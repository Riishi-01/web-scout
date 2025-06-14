"""
Main scraping engine that orchestrates all IWSA components
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlparse

from .prompt_processor import PromptProcessor, ExtractedIntent, ValidationResult
from .reconnaissance import ReconnaissanceEngine, SiteMetadata
from ..llm.hub import LLMHub
from ..scraper.dynamic_scraper import DynamicScraper, ExtractionResult
from ..data.pipeline import DataPipeline, PipelineResult
from ..config import Settings
from ..utils.logger import ComponentLogger
from ..utils.helpers import generate_id, measure_time


@dataclass
class ScrapingRequest:
    """Complete scraping request with all parameters"""
    request_id: str
    prompt: str
    intent: ExtractedIntent
    validation_result: ValidationResult
    scraping_profile: str = "balanced"
    export_formats: List[str] = None
    
    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = ["sheets"]


@dataclass 
class ScrapingResponse:
    """Complete response from scraping operation"""
    success: bool
    request_id: str
    total_records: int = 0
    pages_processed: int = 0
    export_url: Optional[str] = None
    file_paths: List[str] = None
    processing_time: float = 0.0
    error: Optional[str] = None
    
    # Detailed results
    extraction_result: Optional[ExtractionResult] = None
    pipeline_result: Optional[PipelineResult] = None
    site_metadata: Optional[SiteMetadata] = None
    
    def __post_init__(self):
        if self.file_paths is None:
            self.file_paths = []


class ScrapingEngine:
    """
    Main orchestrating engine for the Intelligent Web Scraping Agent
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = ComponentLogger("scraping_engine")
        
        # Core components
        self.prompt_processor = PromptProcessor(settings)
        self.reconnaissance = ReconnaissanceEngine(settings)
        self.llm_hub = LLMHub(settings)
        
        # Active requests tracking
        self.active_requests: Dict[str, ScrapingRequest] = {}
        
        self.logger.info("Scraping engine initialized")
    
    @measure_time
    async def process_request(self, prompt: str) -> ScrapingResponse:
        """
        Main entry point for processing scraping requests
        
        Args:
            prompt: Natural language scraping request
            
        Returns:
            ScrapingResponse with complete results
        """
        request_id = generate_id("req")
        start_time = time.time()
        
        self.logger.info("Processing scraping request", 
                        request_id=request_id,
                        prompt=prompt[:100] + "..." if len(prompt) > 100 else prompt)
        
        response = ScrapingResponse(
            success=False,
            request_id=request_id
        )
        
        try:
            # Step 1: Process user prompt
            intent = await self.prompt_processor.process_prompt(prompt)
            
            if not intent.target_urls:
                response.error = "No valid URLs found in prompt"
                return response
            
            # Step 2: Validate parameters
            validation_result = await self.prompt_processor.validate_parameters(intent)
            
            if not validation_result.valid:
                response.error = f"Parameter validation failed: {'; '.join(validation_result.issues)}"
                return response
            
            # Create scraping request
            scraping_request = ScrapingRequest(
                request_id=request_id,
                prompt=prompt,
                intent=intent,
                validation_result=validation_result,
                scraping_profile=self._determine_scraping_profile(intent),
                export_formats=[intent.output_format]
            )
            
            self.active_requests[request_id] = scraping_request
            
            # Step 3: Perform reconnaissance on target URLs
            site_metadata_list = []
            for url in intent.target_urls:
                site_metadata = await self.reconnaissance.analyze_site(url)
                site_metadata_list.append(site_metadata)
            
            # Use the first site's metadata for now (could be enhanced for multi-site)
            primary_site_metadata = site_metadata_list[0]
            response.site_metadata = primary_site_metadata
            
            # Step 4: Generate scraping strategy using simplified LLM system
            strategy = await self.llm_hub.generate_scraping_strategy(
                html_content=primary_site_metadata.sample_html or "",
                url=primary_site_metadata.url,
                user_intent=intent.intent_description,
                extraction_fields=intent.data_fields
            )
            
            if not strategy.success:
                response.error = f"Strategy generation failed: {strategy.reasoning}"
                return response
            
            self.logger.info("Scraping strategy generated successfully",
                           provider=strategy.provider_used,
                           confidence=strategy.confidence_score,
                           selectors_count=len(strategy.selectors),
                           cost=strategy.cost)
            
            # Step 5: Execute scraping with dynamic scraper using generated strategy
            async with DynamicScraper(self.settings, self.llm_hub) as scraper:
                extraction_result = await scraper.scrape_with_strategy(
                    site_metadata=primary_site_metadata,
                    strategy=strategy,
                    user_requirements=self._build_user_requirements(intent),
                    scraping_profile=scraping_request.scraping_profile
                )
                
                response.extraction_result = extraction_result
                response.pages_processed = extraction_result.pages_processed
                response.total_records = extraction_result.total_items
            
            if not extraction_result.success:
                response.error = f"Data extraction failed: {'; '.join(extraction_result.errors)}"
                return response
            
            # Step 6: Process and export data
            async with DataPipeline(self.settings) as pipeline:
                pipeline_result = await pipeline.process_and_export(
                    data=extraction_result.data,
                    export_formats=scraping_request.export_formats,
                    metadata=self._build_export_metadata(intent, primary_site_metadata)
                )
                
                response.pipeline_result = pipeline_result
            
            if not pipeline_result.success:
                response.error = f"Data processing/export failed: {'; '.join(pipeline_result.errors)}"
                return response
            
            # Set response details
            response.success = True
            response.processing_time = time.time() - start_time
            
            # Extract export URLs and file paths
            for export_result in pipeline_result.export_results:
                if export_result.success:
                    if export_result.export_url:
                        response.export_url = export_result.export_url
                    if export_result.file_path:
                        response.file_paths.append(export_result.file_path)
            
            self.logger.info("Scraping request completed successfully",
                           request_id=request_id,
                           records=response.total_records,
                           pages=response.pages_processed,
                           time=response.processing_time,
                           exports=len(pipeline_result.export_results))
            
        except Exception as e:
            response.error = f"Request processing failed: {str(e)}"
            response.processing_time = time.time() - start_time
            self.logger.error("Scraping request failed", 
                            request_id=request_id,
                            error=str(e),
                            exc_info=True)
        
        finally:
            # Clean up active request
            if request_id in self.active_requests:
                del self.active_requests[request_id]
        
        return response
    
    def _determine_scraping_profile(self, intent: ExtractedIntent) -> str:
        """Determine appropriate scraping profile based on intent"""
        
        # High detection scenarios
        if intent.detection_level == "maximum":
            return "stealth"
        elif intent.detection_level == "high":
            return "conservative"
        
        # Volume-based decisions
        if intent.volume_estimate > 10000:
            return "conservative"  # Large volumes need to be careful
        elif intent.volume_estimate < 100:
            return "aggressive"  # Small volumes can be fast
        
        # Urgency-based decisions
        if intent.urgency == "high":
            return "aggressive"
        elif intent.urgency == "low":
            return "conservative"
        
        # Default
        return "balanced"
    
    def _build_user_requirements(self, intent: ExtractedIntent) -> Dict[str, Any]:
        """Build user requirements dictionary for scraping"""
        return {
            "data_fields": intent.data_fields,
            "filters": intent.filters,
            "volume_estimate": intent.volume_estimate,
            "pagination_limit": intent.pagination_limit,
            "date_range": intent.date_range,
            "geographic_filter": intent.geographic_filter,
            "data_quality": intent.data_quality,
            "expected_patterns": {
                "min_fields_per_item": len(intent.data_fields) // 2,
                "required_fields": intent.data_fields[:3] if intent.data_fields else []
            }
        }
    
    def _build_export_metadata(self, intent: ExtractedIntent, site_metadata: SiteMetadata) -> Dict[str, Any]:
        """Build metadata for export operations"""
        domain = urlparse(site_metadata.url).netloc
        
        return {
            "source_url": site_metadata.url,
            "source_domain": domain,
            "scraping_type": intent.scraping_type,
            "data_fields": intent.data_fields,
            "filters_applied": intent.filters,
            "extraction_timestamp": time.time(),
            "iwsa_version": "1.0.0",
            "spreadsheet_name": f"IWSA_{domain}_{int(time.time())}",
            "worksheet_name": f"{intent.scraping_type.title()} Data"
        }
    
    async def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of active scraping request"""
        if request_id not in self.active_requests:
            return None
        
        request = self.active_requests[request_id]
        return {
            "request_id": request_id,
            "status": "processing",
            "target_urls": request.intent.target_urls,
            "scraping_type": request.intent.scraping_type,
            "estimated_volume": request.intent.volume_estimate,
            "profile": request.scraping_profile,
            "export_formats": request.export_formats
        }
    
    async def cancel_request(self, request_id: str) -> bool:
        """Cancel active scraping request"""
        if request_id in self.active_requests:
            del self.active_requests[request_id]
            self.logger.info("Scraping request cancelled", request_id=request_id)
            return True
        return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all components"""
        health_status = {
            "overall_health": "healthy",
            "components": {},
            "active_requests": len(self.active_requests),
            "timestamp": time.time()
        }
        
        issues = []
        
        try:
            # Check LLM Hub health
            llm_health = await self.llm_hub.health_check()
            health_status["components"]["llm_hub"] = llm_health
            
            if llm_health["overall_health"] != "healthy":
                issues.append("LLM Hub issues detected")
        
        except Exception as e:
            health_status["components"]["llm_hub"] = {"status": "error", "error": str(e)}
            issues.append(f"LLM Hub error: {str(e)}")
        
        try:
            # Check data pipeline health (requires initialization)
            async with DataPipeline(self.settings) as pipeline:
                pipeline_health = await pipeline.validate_pipeline_health()
                health_status["components"]["data_pipeline"] = pipeline_health
                
                if pipeline_health["overall_health"] != "healthy":
                    issues.append("Data Pipeline issues detected")
        
        except Exception as e:
            health_status["components"]["data_pipeline"] = {"status": "error", "error": str(e)}
            issues.append(f"Data Pipeline error: {str(e)}")
        
        # Check prompt processor
        try:
            health_status["components"]["prompt_processor"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["prompt_processor"] = {"status": "error", "error": str(e)}
            issues.append(f"Prompt Processor error: {str(e)}")
        
        # Check reconnaissance engine
        try:
            health_status["components"]["reconnaissance"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["reconnaissance"] = {"status": "error", "error": str(e)}
            issues.append(f"Reconnaissance error: {str(e)}")
        
        # Determine overall health
        if issues:
            health_status["overall_health"] = "degraded" if len(issues) < 3 else "unhealthy"
            health_status["issues"] = issues
        
        return health_status
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            "engine": {
                "active_requests": len(self.active_requests),
                "uptime_seconds": time.time() - getattr(self, '_start_time', time.time())
            },
            "timestamp": time.time()
        }
        
        try:
            # Get LLM provider status
            stats["llm_providers"] = self.llm_hub.get_provider_status()
        except Exception as e:
            stats["llm_providers"] = {"error": str(e)}
        
        try:
            # Get pipeline stats
            async with DataPipeline(self.settings) as pipeline:
                stats["data_pipeline"] = await pipeline.get_pipeline_stats()
        except Exception as e:
            stats["data_pipeline"] = {"error": str(e)}
        
        return stats
    
    async def estimate_request_cost(self, prompt: str) -> Dict[str, Any]:
        """Estimate cost and resources for a scraping request"""
        try:
            # Process prompt to get intent
            intent = await self.prompt_processor.process_prompt(prompt)
            
            if not intent.target_urls:
                return {"error": "No valid URLs found"}
            
            # Validate parameters
            validation_result = await self.prompt_processor.validate_parameters(intent)
            
            # Estimate LLM costs
            estimated_llm_cost = 0.0
            
            # HTML analysis cost (per URL)
            for url in intent.target_urls:
                html_analysis_cost = self.llm_hub.estimate_cost(
                    "html_analysis", 
                    {"html_content": "x" * 10000, "url": url, "user_intent": prompt}
                )
                estimated_llm_cost += html_analysis_cost
            
            # Strategy generation cost
            strategy_cost = self.llm_hub.estimate_cost(
                "strategy_generation",
                {"site_structure": {}, "user_requirements": {}}
            )
            estimated_llm_cost += strategy_cost
            
            # Quality assessment cost
            quality_cost = self.llm_hub.estimate_cost(
                "quality_assessment",
                {"extracted_data": [{}] * 10}
            )
            estimated_llm_cost += quality_cost
            
            return {
                "estimated_cost_usd": estimated_llm_cost,
                "estimated_pages": validation_result.resource_estimate.get("total_pages", 0),
                "estimated_duration_minutes": validation_result.resource_estimate.get("estimated_duration_minutes", 0),
                "estimated_memory_mb": validation_result.resource_estimate.get("estimated_memory_mb", 0),
                "target_urls": intent.target_urls,
                "scraping_type": intent.scraping_type,
                "volume_estimate": intent.volume_estimate,
                "validation_issues": validation_result.issues,
                "validation_warnings": validation_result.warnings
            }
        
        except Exception as e:
            return {"error": str(e)}
    
    def get_active_requests(self) -> List[Dict[str, Any]]:
        """Get list of currently active requests"""
        return [
            {
                "request_id": req_id,
                "target_urls": request.intent.target_urls,
                "scraping_type": request.intent.scraping_type,
                "profile": request.scraping_profile,
                "estimated_volume": request.intent.volume_estimate
            }
            for req_id, request in self.active_requests.items()
        ]