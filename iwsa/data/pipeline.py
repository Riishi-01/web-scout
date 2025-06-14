"""
Main data processing pipeline coordinating storage, processing, and export
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field

from .storage import MongoDBStorage, StorageStats
from .processors import DataCleaner, DataValidator, DataEnricher, ProcessingStats
from .exporters import (
    GoogleSheetsExporter, CSVExporter, JSONExporter, ExcelExporter, 
    ExportResult, BaseExporter
)
from ..config import Settings
from ..utils.logger import ComponentLogger


@dataclass
class PipelineResult:
    """Result of complete pipeline execution"""
    success: bool
    total_input_records: int = 0
    total_output_records: int = 0
    processing_stats: Dict[str, ProcessingStats] = field(default_factory=dict)
    storage_stats: Optional[StorageStats] = None
    export_results: List[ExportResult] = field(default_factory=list)
    pipeline_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """Add error to pipeline result"""
        self.errors.append(error)


class DataPipeline:
    """
    Main data processing pipeline for IWSA
    Handles cleaning, validation, enrichment, storage, and export
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = ComponentLogger("data_pipeline")
        
        # Initialize components
        self.storage = MongoDBStorage(settings)
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
        self.enricher = DataEnricher()
        
        # Initialize exporters
        self.exporters = {
            'sheets': GoogleSheetsExporter(settings),
            'csv': CSVExporter(settings),
            'json': JSONExporter(settings),
            'excel': ExcelExporter(settings)
        }
        
        # Pipeline configuration
        self.enable_cleaning = True
        self.enable_validation = True
        self.enable_enrichment = True
        self.enable_storage = True
        
        self.logger.info("Data pipeline initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.storage.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.storage.disconnect()
    
    async def process_and_export(self, 
                                data: List[Dict[str, Any]],
                                export_formats: List[str] = None,
                                metadata: Dict[str, Any] = None) -> PipelineResult:
        """
        Complete pipeline: process data and export to specified formats
        
        Args:
            data: Raw extracted data
            export_formats: List of export formats ('sheets', 'csv', 'json', 'excel')
            metadata: Pipeline metadata
            
        Returns:
            PipelineResult with complete execution details
        """
        start_time = time.time()
        result = PipelineResult(success=False, total_input_records=len(data))
        
        if export_formats is None:
            export_formats = ['sheets']  # Default to Google Sheets
        
        self.logger.info("Starting data pipeline",
                        input_records=len(data),
                        export_formats=export_formats)
        
        try:
            # Process data through pipeline stages
            processed_data = await self._process_data(data, result)
            
            if not processed_data:
                result.add_error("No data survived processing pipeline")
                return result
            
            result.total_output_records = len(processed_data)
            
            # Store data if enabled
            if self.enable_storage:
                storage_stats = await self.storage.store_data(processed_data, metadata)
                result.storage_stats = storage_stats
                
                if storage_stats.failed_count > 0:
                    self.logger.warning("Some data failed to store",
                                      failed=storage_stats.failed_count,
                                      total=storage_stats.total_documents)
            
            # Export data in parallel
            if export_formats:
                export_tasks = []
                for format_name in export_formats:
                    if format_name in self.exporters:
                        task = self._export_data(processed_data, format_name, metadata)
                        export_tasks.append(task)
                    else:
                        result.add_error(f"Unknown export format: {format_name}")
                
                if export_tasks:
                    export_results = await asyncio.gather(*export_tasks, return_exceptions=True)
                    
                    for export_result in export_results:
                        if isinstance(export_result, Exception):
                            result.add_error(f"Export failed: {str(export_result)}")
                        else:
                            result.export_results.append(export_result)
            
            # Determine overall success
            result.success = (
                result.total_output_records > 0 and
                len(result.errors) == 0 and
                any(export.success for export in result.export_results)
            )
            
            result.pipeline_time = time.time() - start_time
            
            self.logger.info("Data pipeline completed",
                           success=result.success,
                           input_records=result.total_input_records,
                           output_records=result.total_output_records,
                           exports_successful=sum(1 for exp in result.export_results if exp.success),
                           time=result.pipeline_time)
            
        except Exception as e:
            result.add_error(f"Pipeline execution failed: {str(e)}")
            result.pipeline_time = time.time() - start_time
            self.logger.error("Data pipeline failed", error=str(e), exc_info=True)
        
        return result
    
    async def _process_data(self, data: List[Dict[str, Any]], result: PipelineResult) -> List[Dict[str, Any]]:
        """Process data through cleaning, validation, and enrichment stages"""
        processed_data = data
        
        # Data cleaning stage
        if self.enable_cleaning and processed_data:
            self.logger.info("Starting data cleaning stage")
            processed_data, cleaning_stats = await self.cleaner.process(processed_data)
            result.processing_stats['cleaning'] = cleaning_stats
            
            if cleaning_stats.failed_items > 0:
                self.logger.warning("Some items failed cleaning",
                                  failed=cleaning_stats.failed_items,
                                  total=cleaning_stats.total_items)
        
        # Data validation stage
        if self.enable_validation and processed_data:
            self.logger.info("Starting data validation stage")
            processed_data, validation_stats = await self.validator.process(processed_data)
            result.processing_stats['validation'] = validation_stats
            
            if validation_stats.failed_items > 0:
                self.logger.warning("Some items failed validation",
                                  failed=validation_stats.failed_items,
                                  total=validation_stats.total_items)
        
        # Data enrichment stage
        if self.enable_enrichment and processed_data:
            self.logger.info("Starting data enrichment stage")
            processed_data, enrichment_stats = await self.enricher.process(processed_data)
            result.processing_stats['enrichment'] = enrichment_stats
            
            if enrichment_stats.failed_items > 0:
                self.logger.warning("Some items failed enrichment",
                                  failed=enrichment_stats.failed_items,
                                  total=enrichment_stats.total_items)
        
        return processed_data
    
    async def _export_data(self, 
                          data: List[Dict[str, Any]], 
                          format_name: str, 
                          metadata: Dict[str, Any] = None) -> ExportResult:
        """Export data using specified exporter"""
        try:
            exporter = self.exporters[format_name]
            
            self.logger.info("Starting data export", format=format_name, records=len(data))
            
            export_result = await exporter.export(data, metadata)
            
            if export_result.success:
                self.logger.info("Data export completed",
                               format=format_name,
                               records=export_result.records_exported,
                               time=export_result.export_time,
                               url=export_result.export_url,
                               file=export_result.file_path)
            else:
                self.logger.error("Data export failed",
                                format=format_name,
                                error=export_result.error)
            
            return export_result
            
        except Exception as e:
            return ExportResult(
                success=False,
                error=str(e),
                records_exported=0
            )
    
    async def store_data_only(self, 
                             data: List[Dict[str, Any]], 
                             metadata: Dict[str, Any] = None) -> StorageStats:
        """Store data without export"""
        try:
            processed_data = data
            
            # Run through processing stages if enabled
            if self.enable_cleaning:
                processed_data, _ = await self.cleaner.process(processed_data)
            
            if self.enable_validation:
                processed_data, _ = await self.validator.process(processed_data)
            
            if self.enable_enrichment:
                processed_data, _ = await self.enricher.process(processed_data)
            
            # Store processed data
            return await self.storage.store_data(processed_data, metadata)
            
        except Exception as e:
            self.logger.error("Data storage failed", error=str(e))
            return StorageStats()
    
    async def export_existing_data(self, 
                                  query: Dict[str, Any] = None,
                                  export_formats: List[str] = None,
                                  limit: int = None,
                                  metadata: Dict[str, Any] = None) -> List[ExportResult]:
        """Export existing data from storage"""
        if export_formats is None:
            export_formats = ['sheets']
        
        try:
            # Retrieve data from storage
            data = await self.storage.retrieve_data(query, limit)
            
            if not data:
                self.logger.warning("No data found for export", query=query)
                return []
            
            # Export in parallel
            export_tasks = []
            for format_name in export_formats:
                if format_name in self.exporters:
                    task = self._export_data(data, format_name, metadata)
                    export_tasks.append(task)
            
            if export_tasks:
                export_results = await asyncio.gather(*export_tasks, return_exceptions=True)
                
                # Filter out exceptions
                valid_results = []
                for result in export_results:
                    if isinstance(result, Exception):
                        self.logger.error("Export task failed", error=str(result))
                    else:
                        valid_results.append(result)
                
                return valid_results
            
            return []
            
        except Exception as e:
            self.logger.error("Export of existing data failed", error=str(e))
            return []
    
    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics"""
        try:
            storage_stats = await self.storage.get_stats()
            
            stats = {
                'pipeline_components': {
                    'cleaning_enabled': self.enable_cleaning,
                    'validation_enabled': self.enable_validation,
                    'enrichment_enabled': self.enable_enrichment,
                    'storage_enabled': self.enable_storage
                },
                'storage': storage_stats,
                'available_exporters': list(self.exporters.keys()),
                'timestamp': time.time()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get pipeline stats", error=str(e))
            return {'error': str(e)}
    
    async def cleanup_old_data(self, 
                              age_threshold_hours: int = 24,
                              dry_run: bool = True) -> Dict[str, int]:
        """Clean up old data from storage"""
        try:
            cutoff_time = time.time() - (age_threshold_hours * 3600)
            
            query = {
                '_extracted_at': {'$lt': cutoff_time}
            }
            
            if dry_run:
                # Just count what would be deleted
                old_data = await self.storage.retrieve_data(query)
                count = len(old_data)
                
                self.logger.info("Cleanup dry run completed",
                               would_delete=count,
                               age_threshold_hours=age_threshold_hours)
                
                return {'would_delete': count, 'deleted': 0}
            else:
                # Actually delete old data
                deleted_count = await self.storage.delete_data(query)
                
                self.logger.info("Data cleanup completed",
                               deleted=deleted_count,
                               age_threshold_hours=age_threshold_hours)
                
                return {'would_delete': 0, 'deleted': deleted_count}
                
        except Exception as e:
            self.logger.error("Data cleanup failed", error=str(e))
            return {'error': str(e)}
    
    def configure_processing(self, 
                           enable_cleaning: bool = True,
                           enable_validation: bool = True,
                           enable_enrichment: bool = True,
                           enable_storage: bool = True):
        """Configure which processing stages are enabled"""
        self.enable_cleaning = enable_cleaning
        self.enable_validation = enable_validation
        self.enable_enrichment = enable_enrichment
        self.enable_storage = enable_storage
        
        self.logger.info("Pipeline configuration updated",
                        cleaning=enable_cleaning,
                        validation=enable_validation,
                        enrichment=enable_enrichment,
                        storage=enable_storage)
    
    async def validate_pipeline_health(self) -> Dict[str, Any]:
        """Validate health of all pipeline components"""
        health_status = {
            'overall_health': 'healthy',
            'components': {},
            'timestamp': time.time()
        }
        
        issues = []
        
        try:
            # Check storage health
            storage_stats = await self.storage.get_stats()
            if storage_stats.get('connected', False):
                health_status['components']['storage'] = 'healthy'
            else:
                health_status['components']['storage'] = 'unhealthy'
                issues.append('Storage connection failed')
        
        except Exception as e:
            health_status['components']['storage'] = 'error'
            issues.append(f'Storage error: {str(e)}')
        
        # Check exporters
        for exporter_name in self.exporters:
            try:
                # Basic health check for exporters
                health_status['components'][f'exporter_{exporter_name}'] = 'healthy'
            except Exception as e:
                health_status['components'][f'exporter_{exporter_name}'] = 'error'
                issues.append(f'{exporter_name} exporter error: {str(e)}')
        
        # Determine overall health
        if issues:
            health_status['overall_health'] = 'degraded' if len(issues) < 2 else 'unhealthy'
            health_status['issues'] = issues
        
        return health_status