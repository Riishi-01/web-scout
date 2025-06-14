"""
Data storage implementations for MongoDB and other backends
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass
from abc import ABC, abstractmethod
import motor.motor_asyncio
from pymongo import IndexModel
from pymongo.errors import DuplicateKeyError, ConnectionFailure

from ..config import Settings
from ..utils.logger import ComponentLogger
from ..utils.helpers import retry_with_backoff


@dataclass
class StorageStats:
    """Storage operation statistics"""
    total_documents: int = 0
    inserted_count: int = 0
    updated_count: int = 0
    failed_count: int = 0
    avg_operation_time: float = 0.0


class BaseStorage(ABC):
    """Base class for storage implementations"""
    
    @abstractmethod
    async def connect(self):
        """Establish connection to storage backend"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close connection to storage backend"""
        pass
    
    @abstractmethod
    async def store_data(self, data: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> StorageStats:
        """Store extracted data"""
        pass
    
    @abstractmethod
    async def retrieve_data(self, query: Dict[str, Any] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Retrieve stored data"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        pass


class MongoDBStorage(BaseStorage):
    """
    MongoDB storage implementation with async support
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = ComponentLogger("mongodb_storage")
        
        # MongoDB configuration
        self.uri = settings.storage.mongodb_uri
        self.database_name = settings.storage.database_name
        self.collection_name = settings.storage.collection_name
        
        # Connection objects
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.database = None
        self.collection = None
        
        # Performance tracking
        self.operation_times: List[float] = []
        
        self.logger.info("MongoDB storage initialized", 
                        database=self.database_name,
                        collection=self.collection_name)
    
    async def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=10
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            # Create indexes for better performance
            await self._create_indexes()
            
            self.logger.info("MongoDB connection established")
            
        except Exception as e:
            self.logger.error("MongoDB connection failed", error=str(e))
            raise
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")
    
    async def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            indexes = [
                IndexModel([("_source_url", 1)]),
                IndexModel([("_extracted_at", -1)]),
                IndexModel([("_job_id", 1)]),
                IndexModel([("_source_url", 1), ("_extracted_at", -1)]),
                # Add text index for search
                IndexModel([("$**", "text")])
            ]
            
            await self.collection.create_indexes(indexes)
            self.logger.debug("Database indexes created")
            
        except Exception as e:
            self.logger.warning("Index creation failed", error=str(e))
    
    @retry_with_backoff(max_attempts=3, retry_exceptions=(ConnectionFailure,))
    async def store_data(self, 
                        data: List[Dict[str, Any]], 
                        metadata: Dict[str, Any] = None) -> StorageStats:
        """
        Store extracted data in MongoDB
        
        Args:
            data: List of extracted data items
            metadata: Additional metadata for the batch
            
        Returns:
            StorageStats with operation results
        """
        if not data:
            return StorageStats()
        
        start_time = time.time()
        stats = StorageStats(total_documents=len(data))
        
        try:
            # Prepare documents
            documents = []
            current_time = time.time()
            
            for item in data:
                doc = item.copy()
                
                # Add metadata
                if metadata:
                    doc.update({f"_meta_{k}": v for k, v in metadata.items()})
                
                # Add processing timestamp if not exists
                if "_processed_at" not in doc:
                    doc["_processed_at"] = current_time
                
                # Generate unique ID based on content to avoid duplicates
                doc["_content_hash"] = self._generate_content_hash(doc)
                
                documents.append(doc)
            
            # Bulk insert with ordered=False to continue on duplicates
            try:
                result = await self.collection.insert_many(documents, ordered=False)
                stats.inserted_count = len(result.inserted_ids)
                
            except DuplicateKeyError as e:
                # Handle partial success in bulk insert
                stats.inserted_count = e.details.get('nInserted', 0)
                stats.failed_count = len(documents) - stats.inserted_count
                
                self.logger.warning("Some documents were duplicates",
                                  inserted=stats.inserted_count,
                                  failed=stats.failed_count)
            
            # Track operation time
            operation_time = time.time() - start_time
            self.operation_times.append(operation_time)
            
            # Keep only recent operation times
            if len(self.operation_times) > 100:
                self.operation_times = self.operation_times[-100:]
            
            stats.avg_operation_time = operation_time
            
            self.logger.info("Data stored successfully",
                           total=stats.total_documents,
                           inserted=stats.inserted_count,
                           failed=stats.failed_count,
                           operation_time=operation_time)
            
        except Exception as e:
            stats.failed_count = len(data)
            self.logger.error("Data storage failed", error=str(e))
            raise
        
        return stats
    
    def _generate_content_hash(self, document: Dict[str, Any]) -> str:
        """Generate hash for content deduplication"""
        import hashlib
        import json
        
        # Create a copy without metadata fields for hashing
        content_doc = {k: v for k, v in document.items() 
                      if not k.startswith('_')}
        
        # Sort keys for consistent hashing
        content_str = json.dumps(content_doc, sort_keys=True, default=str)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    async def retrieve_data(self, 
                           query: Dict[str, Any] = None, 
                           limit: int = None,
                           sort_field: str = "_extracted_at",
                           sort_order: int = -1) -> List[Dict[str, Any]]:
        """
        Retrieve data from MongoDB
        
        Args:
            query: MongoDB query filter
            limit: Maximum number of documents to return
            sort_field: Field to sort by
            sort_order: Sort order (1 for ascending, -1 for descending)
            
        Returns:
            List of documents
        """
        try:
            cursor = self.collection.find(query or {})
            
            if sort_field:
                cursor = cursor.sort(sort_field, sort_order)
            
            if limit:
                cursor = cursor.limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            self.logger.debug("Data retrieved",
                            query=query,
                            count=len(documents),
                            limit=limit)
            
            return documents
            
        except Exception as e:
            self.logger.error("Data retrieval failed", error=str(e))
            return []
    
    async def stream_data(self, 
                         query: Dict[str, Any] = None,
                         batch_size: int = 1000) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Stream data in batches for large datasets
        
        Args:
            query: MongoDB query filter
            batch_size: Number of documents per batch
            
        Yields:
            Batches of documents
        """
        try:
            cursor = self.collection.find(query or {})
            
            batch = []
            async for document in cursor:
                batch.append(document)
                
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            
            # Yield remaining documents
            if batch:
                yield batch
                
        except Exception as e:
            self.logger.error("Data streaming failed", error=str(e))
    
    async def update_data(self, 
                         query: Dict[str, Any],
                         update: Dict[str, Any],
                         upsert: bool = False) -> int:
        """
        Update existing documents
        
        Args:
            query: Query to match documents
            update: Update operations
            upsert: Whether to insert if no match found
            
        Returns:
            Number of documents modified
        """
        try:
            result = await self.collection.update_many(query, update, upsert=upsert)
            
            self.logger.debug("Data updated",
                            matched=result.matched_count,
                            modified=result.modified_count,
                            upserted=result.upserted_id is not None)
            
            return result.modified_count
            
        except Exception as e:
            self.logger.error("Data update failed", error=str(e))
            return 0
    
    async def delete_data(self, query: Dict[str, Any]) -> int:
        """
        Delete documents matching query
        
        Args:
            query: Query to match documents for deletion
            
        Returns:
            Number of documents deleted
        """
        try:
            result = await self.collection.delete_many(query)
            
            self.logger.info("Data deleted", count=result.deleted_count)
            return result.deleted_count
            
        except Exception as e:
            self.logger.error("Data deletion failed", error=str(e))
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics and health info"""
        try:
            # Collection stats
            collection_stats = await self.database.command("collStats", self.collection_name)
            
            # Server info
            server_info = await self.client.server_info()
            
            # Calculate average operation time
            avg_op_time = (sum(self.operation_times) / len(self.operation_times) 
                          if self.operation_times else 0.0)
            
            stats = {
                "connected": True,
                "server_version": server_info.get("version", "unknown"),
                "database": self.database_name,
                "collection": self.collection_name,
                "document_count": collection_stats.get("count", 0),
                "storage_size_bytes": collection_stats.get("storageSize", 0),
                "index_count": collection_stats.get("nindexes", 0),
                "avg_operation_time": avg_op_time,
                "recent_operations": len(self.operation_times)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get storage stats", error=str(e))
            return {
                "connected": False,
                "error": str(e)
            }
    
    async def create_export_view(self, 
                                view_name: str, 
                                pipeline: List[Dict[str, Any]]) -> bool:
        """
        Create a MongoDB view for data export
        
        Args:
            view_name: Name of the view
            pipeline: Aggregation pipeline for the view
            
        Returns:
            True if view created successfully
        """
        try:
            await self.database.create_collection(
                view_name, 
                viewOn=self.collection_name,
                pipeline=pipeline
            )
            
            self.logger.info("Export view created", view_name=view_name)
            return True
            
        except Exception as e:
            self.logger.error("Failed to create export view", 
                            view_name=view_name,
                            error=str(e))
            return False
    
    async def aggregate_data(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform aggregation query
        
        Args:
            pipeline: MongoDB aggregation pipeline
            
        Returns:
            Aggregation results
        """
        try:
            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            self.logger.debug("Aggregation completed", results_count=len(results))
            return results
            
        except Exception as e:
            self.logger.error("Aggregation failed", error=str(e))
            return []
    
    async def get_data_summary(self, 
                              source_url: Optional[str] = None,
                              time_range: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Get summary statistics for stored data
        
        Args:
            source_url: Filter by source URL
            time_range: Tuple of (start_time, end_time) timestamps
            
        Returns:
            Summary statistics
        """
        try:
            match_stage = {}
            
            if source_url:
                match_stage["_source_url"] = source_url
            
            if time_range:
                match_stage["_extracted_at"] = {
                    "$gte": time_range[0],
                    "$lte": time_range[1]
                }
            
            pipeline = []
            
            if match_stage:
                pipeline.append({"$match": match_stage})
            
            pipeline.extend([
                {
                    "$group": {
                        "_id": "$_source_url",
                        "count": {"$sum": 1},
                        "first_extracted": {"$min": "$_extracted_at"},
                        "last_extracted": {"$max": "$_extracted_at"}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_documents": {"$sum": "$count"},
                        "unique_sources": {"$sum": 1},
                        "sources": {"$push": {
                            "url": "$_id",
                            "count": "$count",
                            "first_extracted": "$first_extracted",
                            "last_extracted": "$last_extracted"
                        }}
                    }
                }
            ])
            
            results = await self.aggregate_data(pipeline)
            
            if results:
                summary = results[0]
                summary.pop("_id", None)
                return summary
            else:
                return {
                    "total_documents": 0,
                    "unique_sources": 0,
                    "sources": []
                }
                
        except Exception as e:
            self.logger.error("Failed to get data summary", error=str(e))
            return {"error": str(e)}