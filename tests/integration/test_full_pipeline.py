"""
Integration tests for the full IWSA pipeline
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from iwsa.core.engine import ScrapingEngine
from iwsa.config import Settings


class TestFullPipeline:
    """Integration tests for complete scraping pipeline"""
    
    @pytest.mark.asyncio
    async def test_basic_scraping_flow(self, test_settings, sample_user_prompt, mock_llm_response, sample_extracted_data):
        """Test basic end-to-end scraping flow"""
        
        # Mock the LLM responses
        mock_llm_hub = MagicMock()
        mock_llm_hub.analyze_html.return_value = AsyncMock()
        mock_llm_hub.analyze_html.return_value.success = True
        mock_llm_hub.analyze_html.return_value.data = mock_llm_response
        
        mock_llm_hub.generate_strategy.return_value = AsyncMock()
        mock_llm_hub.generate_strategy.return_value.success = True
        mock_llm_hub.generate_strategy.return_value.data = {
            "scraping_plan": {"approach": "test", "steps": ["step1"]},
            "timing_strategy": {"request_delay": 2.0},
            "risk_assessment": {"detection_probability": "low"}
        }
        
        mock_llm_hub.assess_quality.return_value = AsyncMock()
        mock_llm_hub.assess_quality.return_value.success = True
        mock_llm_hub.assess_quality.return_value.data = {"quality_score": 0.9}
        
        # Mock the scraper components
        with patch('iwsa.core.engine.LLMHub') as mock_hub_class:
            mock_hub_class.return_value = mock_llm_hub
            
            with patch('iwsa.core.engine.DynamicScraper') as mock_scraper_class:
                # Mock scraper context manager
                mock_scraper = AsyncMock()
                mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
                mock_scraper.__aexit__ = AsyncMock(return_value=None)
                
                # Mock scraping result
                from iwsa.scraper.dynamic_scraper import ExtractionResult
                mock_extraction_result = ExtractionResult(
                    success=True,
                    data=sample_extracted_data,
                    total_items=len(sample_extracted_data),
                    pages_processed=1
                )
                mock_scraper.scrape_site.return_value = mock_extraction_result
                mock_scraper_class.return_value = mock_scraper
                
                with patch('iwsa.data.pipeline.DataPipeline') as mock_pipeline_class:
                    # Mock pipeline context manager
                    mock_pipeline = AsyncMock()
                    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
                    mock_pipeline.__aexit__ = AsyncMock(return_value=None)
                    
                    # Mock pipeline result
                    from iwsa.data.pipeline import PipelineResult
                    from iwsa.data.exporters import ExportResult
                    
                    mock_export_result = ExportResult(
                        success=True,
                        export_url="https://docs.google.com/spreadsheets/d/test123",
                        records_exported=len(sample_extracted_data)
                    )
                    
                    mock_pipeline_result = PipelineResult(
                        success=True,
                        total_output_records=len(sample_extracted_data),
                        export_results=[mock_export_result]
                    )
                    mock_pipeline.process_and_export.return_value = mock_pipeline_result
                    mock_pipeline_class.return_value = mock_pipeline
                    
                    # Test the engine
                    engine = ScrapingEngine(test_settings)
                    response = await engine.process_request(sample_user_prompt["simple"])
                    
                    # Verify response
                    assert response.success == True
                    assert response.total_records == len(sample_extracted_data)
                    assert response.pages_processed == 1
                    assert response.export_url == "https://docs.google.com/spreadsheets/d/test123"
    
    @pytest.mark.asyncio
    async def test_error_handling_in_pipeline(self, test_settings, sample_user_prompt):
        """Test error handling throughout the pipeline"""
        
        # Test with invalid prompt (no URLs)
        engine = ScrapingEngine(test_settings)
        response = await engine.process_request("Invalid prompt with no URLs")
        
        assert response.success == False
        assert "No valid URLs found" in response.error
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self, test_settings, sample_user_prompt):
        """Test cost estimation functionality"""
        
        with patch('iwsa.core.engine.LLMHub') as mock_hub_class:
            mock_llm_hub = MagicMock()
            mock_llm_hub.estimate_cost.return_value = 0.05
            mock_hub_class.return_value = mock_llm_hub
            
            engine = ScrapingEngine(test_settings)
            
            cost_estimate = await engine.estimate_request_cost(sample_user_prompt["detailed"])
            
            assert "estimated_cost_usd" in cost_estimate
            assert "estimated_pages" in cost_estimate
            assert "target_urls" in cost_estimate
            assert cost_estimate["estimated_cost_usd"] > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, test_settings):
        """Test system health check"""
        
        with patch('iwsa.core.engine.LLMHub') as mock_hub_class:
            mock_llm_hub = MagicMock()
            mock_llm_hub.health_check.return_value = AsyncMock()
            mock_llm_hub.health_check.return_value = {
                "overall_health": "healthy",
                "components": {"llm_hub": {"status": "healthy"}}
            }
            mock_hub_class.return_value = mock_llm_hub
            
            with patch('iwsa.data.pipeline.DataPipeline') as mock_pipeline_class:
                mock_pipeline = AsyncMock()
                mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
                mock_pipeline.__aexit__ = AsyncMock(return_value=None)
                mock_pipeline.validate_pipeline_health.return_value = {
                    "overall_health": "healthy"
                }
                mock_pipeline_class.return_value = mock_pipeline
                
                engine = ScrapingEngine(test_settings)
                health = await engine.health_check()
                
                assert health["overall_health"] in ["healthy", "degraded", "unhealthy"]
                assert "components" in health
                assert "timestamp" in health
    
    @pytest.mark.asyncio
    async def test_request_tracking(self, test_settings, sample_user_prompt):
        """Test request tracking functionality"""
        
        engine = ScrapingEngine(test_settings)
        
        # Initially no active requests
        assert len(engine.get_active_requests()) == 0
        
        # Start a request (mock it to not complete)
        with patch.object(engine, 'process_request') as mock_process:
            async def slow_process(prompt):
                # Simulate a request being tracked
                from iwsa.core.engine import ScrapingRequest
                from iwsa.core.prompt_processor import ExtractedIntent, ValidationResult
                
                intent = ExtractedIntent(target_urls=["https://example.com"])
                validation = ValidationResult(valid=True)
                
                request = ScrapingRequest(
                    request_id="test_req_1",
                    prompt=prompt,
                    intent=intent,
                    validation_result=validation
                )
                
                engine.active_requests["test_req_1"] = request
                
                # Return mock response
                from iwsa.core.engine import ScrapingResponse
                return ScrapingResponse(success=True, request_id="test_req_1")
            
            mock_process.side_effect = slow_process
            
            # Process request
            response = await engine.process_request(sample_user_prompt["simple"])
            
            # Check request was tracked
            assert response.request_id == "test_req_1"
            
            # Check active requests
            active = engine.get_active_requests()
            assert len(active) == 1
            assert active[0]["request_id"] == "test_req_1"
            
            # Test request status
            status = await engine.get_request_status("test_req_1")
            assert status is not None
            assert status["request_id"] == "test_req_1"
            
            # Test request cancellation
            cancelled = await engine.cancel_request("test_req_1")
            assert cancelled == True
            assert len(engine.get_active_requests()) == 0
    
    @pytest.mark.asyncio
    async def test_system_stats(self, test_settings):
        """Test system statistics retrieval"""
        
        with patch('iwsa.core.engine.LLMHub') as mock_hub_class:
            mock_llm_hub = MagicMock()
            mock_llm_hub.get_provider_status.return_value = {
                "openai": {"available": True, "status": "healthy"}
            }
            mock_hub_class.return_value = mock_llm_hub
            
            with patch('iwsa.data.pipeline.DataPipeline') as mock_pipeline_class:
                mock_pipeline = AsyncMock()
                mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
                mock_pipeline.__aexit__ = AsyncMock(return_value=None)
                mock_pipeline.get_pipeline_stats.return_value = {
                    "storage": {"connected": True}
                }
                mock_pipeline_class.return_value = mock_pipeline
                
                engine = ScrapingEngine(test_settings)
                stats = await engine.get_system_stats()
                
                assert "engine" in stats
                assert "llm_providers" in stats
                assert "data_pipeline" in stats
                assert "timestamp" in stats
                
                # Check engine stats
                assert "active_requests" in stats["engine"]
                assert "uptime_seconds" in stats["engine"]


class TestPipelineComponents:
    """Test integration between pipeline components"""
    
    @pytest.mark.asyncio
    async def test_data_flow_through_processors(self, sample_extracted_data):
        """Test data flow through cleaning, validation, and enrichment"""
        
        from iwsa.data.processors import DataCleaner, DataValidator, DataEnricher
        
        # Start with sample data
        data = sample_extracted_data.copy()
        
        # Add some dirty data to test cleaning
        data[0]["title"] = "  Dirty Title  \n"
        data[0]["email"] = "test@example.com"
        data[1]["price"] = "$1,299.99"
        
        # Process through cleaning
        cleaner = DataCleaner()
        cleaned_data, clean_stats = await cleaner.process(data)
        
        assert clean_stats.processed_items == len(data)
        assert cleaned_data[0]["title"] == "Dirty Title"
        
        # Process through validation
        validator = DataValidator()
        validated_data, valid_stats = await validator.process(cleaned_data)
        
        assert valid_stats.processed_items == len(cleaned_data)
        assert "_validation_score" in validated_data[0]
        
        # Process through enrichment
        enricher = DataEnricher()
        enriched_data, enrich_stats = await enricher.process(validated_data)
        
        assert enrich_stats.processed_items == len(validated_data)
        assert "_enriched_at" in enriched_data[0]
        assert "_field_count" in enriched_data[0]
        
        # Verify data integrity throughout pipeline
        assert len(enriched_data) == len(data)
        assert enriched_data[0]["title"] == "Dirty Title"  # Original data preserved
        assert enriched_data[0]["_source_url"] == data[0]["_source_url"]