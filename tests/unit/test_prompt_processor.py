"""
Unit tests for prompt processor
"""

import pytest
from unittest.mock import patch, AsyncMock

from iwsa.core.prompt_processor import PromptProcessor, ExtractedIntent


class TestPromptProcessor:
    """Test cases for PromptProcessor"""
    
    @pytest.mark.asyncio
    async def test_process_simple_prompt(self, mock_prompt_processor, sample_user_prompt):
        """Test processing a simple prompt"""
        processor = mock_prompt_processor
        prompt = sample_user_prompt["simple"]
        
        intent = await processor.process_prompt(prompt)
        
        assert isinstance(intent, ExtractedIntent)
        assert len(intent.target_urls) > 0
        assert "example.com" in intent.target_urls[0]
        assert intent.scraping_type in ["general", "products"]
    
    @pytest.mark.asyncio
    async def test_extract_urls_from_prompt(self, mock_prompt_processor):
        """Test URL extraction from prompts"""
        processor = mock_prompt_processor
        
        test_cases = [
            ("Scrape https://example.com for products", ["https://example.com"]),
            ("Get data from example.com and test.org", ["https://example.com", "https://test.org"]),
            ("Extract from www.test.com", ["https://www.test.com"]),
            ("No URLs here", [])
        ]
        
        for prompt, expected_urls in test_cases:
            urls = processor._extract_urls(prompt)
            if expected_urls:
                assert len(urls) == len(expected_urls)
                for expected_url in expected_urls:
                    assert any(expected_url in url for url in urls)
            else:
                assert len(urls) == 0
    
    def test_classify_intent(self, mock_prompt_processor):
        """Test intent classification"""
        processor = mock_prompt_processor
        
        test_cases = [
            ("Scrape job listings from careers.com", "job_listings"),
            ("Get product data from store.com", "products"),
            ("Extract contact information", "contacts"),
            ("Scrape news articles", "news"),
            ("Random text with no clear intent", "general")
        ]
        
        for prompt, expected_type in test_cases:
            intent_type = processor._classify_intent(prompt)
            assert intent_type == expected_type
    
    def test_extract_data_fields(self, mock_prompt_processor):
        """Test data field extraction"""
        processor = mock_prompt_processor
        
        test_cases = [
            ("Get title, price, and description", ["title", "price", "description"]),
            ("Extract name, email, and phone number", ["name", "email", "phone"]),
            ("Scrape job title, company, location", ["job", "title", "company", "location"]),
            ("No specific fields mentioned", [])
        ]
        
        for prompt, expected_fields in test_cases:
            fields = processor._extract_data_fields(prompt)
            
            if expected_fields:
                # Check that at least some expected fields are found
                found_fields = [field for field in expected_fields if any(field in f for f in fields)]
                assert len(found_fields) > 0
    
    def test_extract_filters(self, mock_prompt_processor):
        """Test filter extraction"""
        processor = mock_prompt_processor
        
        test_cases = [
            ("Products under $100", {"max_price": 100.0}),
            ("Jobs in San Francisco", {"location": "san francisco"}),
            ("Posted in the last 7 days", {"date_range": "last_7_day"}),
            ("No filters here", {})
        ]
        
        for prompt, expected_filters in test_cases:
            filters = processor._extract_filters(prompt)
            
            for key, value in expected_filters.items():
                if key in filters:
                    if isinstance(value, str):
                        assert value.lower() in str(filters[key]).lower()
                    else:
                        assert filters[key] == value
    
    def test_determine_urgency(self, mock_prompt_processor):
        """Test urgency determination"""
        processor = mock_prompt_processor
        
        test_cases = [
            ("I need this urgently", "high"),
            ("Please do this quickly", "high"),
            ("When you have time", "low"),
            ("No rush on this", "low"),
            ("Regular request", "normal")
        ]
        
        for prompt, expected_urgency in test_cases:
            urgency = processor._determine_urgency(prompt)
            assert urgency == expected_urgency
    
    def test_estimate_volume(self, mock_prompt_processor):
        """Test volume estimation"""
        processor = mock_prompt_processor
        
        test_cases = [
            ("Get all products", 10000),
            ("Extract 50 records", 50),
            ("First 100 results", 100),
            ("Just a few items", 100),
            ("Regular scraping", 1000)
        ]
        
        for prompt, expected_range in test_cases:
            volume = processor._estimate_volume(prompt)
            
            # Allow some variance in estimation
            if expected_range < 200:
                assert abs(volume - expected_range) <= 50
            else:
                assert volume >= expected_range * 0.5
    
    @pytest.mark.asyncio
    async def test_validate_parameters(self, mock_prompt_processor):
        """Test parameter validation"""
        processor = mock_prompt_processor
        
        # Create test intent
        intent = ExtractedIntent(
            target_urls=["https://example.com"],
            data_fields=["title", "price"],
            scraping_type="products",
            volume_estimate=100
        )
        
        with patch.object(processor, '_validate_url_accessibility') as mock_validate:
            mock_validate.return_value = {"accessible": True, "robots_restricted": False}
            
            with patch.object(processor, '_check_legal_compliance') as mock_legal:
                mock_legal.return_value = "allowed"
                
                result = await processor.validate_parameters(intent)
                
                assert result.valid == True
                assert len(result.issues) == 0
    
    @pytest.mark.asyncio
    async def test_validate_parameters_with_issues(self, mock_prompt_processor):
        """Test parameter validation with issues"""
        processor = mock_prompt_processor
        
        # Create intent with no URLs
        intent = ExtractedIntent(
            target_urls=[],
            data_fields=["title"],
            scraping_type="general"
        )
        
        result = await processor.validate_parameters(intent)
        
        assert result.valid == False
        assert len(result.issues) > 0
        assert "No valid URLs found" in result.issues[0]
    
    def test_extract_pagination_limit(self, mock_prompt_processor):
        """Test pagination limit extraction"""
        processor = mock_prompt_processor
        
        test_cases = [
            ("First 5 pages only", 5),
            ("Maximum 10 pages", 10),
            ("Page limit: 3", 3),
            ("No pagination limit", None)
        ]
        
        for prompt, expected_limit in test_cases:
            limit = processor._extract_pagination_limit(prompt)
            assert limit == expected_limit
    
    def test_extract_output_format(self, mock_prompt_processor):
        """Test output format extraction"""
        processor = mock_prompt_processor
        
        test_cases = [
            ("Export to CSV", "csv"),
            ("Save as JSON", "json"),
            ("Google Sheets export", "sheets"),
            ("Excel file", "excel"),
            ("No format specified", "sheets")  # Default
        ]
        
        for prompt, expected_format in test_cases:
            format_type = processor._extract_output_format(prompt)
            assert format_type == expected_format