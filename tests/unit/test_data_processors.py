"""
Unit tests for data processors
"""

import pytest
from unittest.mock import patch

from iwsa.data.processors import DataCleaner, DataValidator, DataEnricher, ProcessingStats


class TestDataCleaner:
    """Test cases for DataCleaner"""
    
    @pytest.mark.asyncio
    async def test_clean_text_data(self):
        """Test text cleaning functionality"""
        cleaner = DataCleaner()
        
        # Test data with various cleaning needs
        dirty_data = [
            {
                "title": "  Product Name  \n\n",
                "description": "Great&nbsp;product&amp;description",
                "price": "$29.99",
                "_source_url": "https://example.com"
            }
        ]
        
        cleaned_data, stats = await cleaner.process(dirty_data)
        
        assert stats.total_items == 1
        assert stats.processed_items == 1
        assert stats.failed_items == 0
        
        cleaned_item = cleaned_data[0]
        assert cleaned_item["title"] == "Product Name"
        assert "great product description" in cleaned_item["description"].lower()
        assert cleaned_item["_source_url"] == "https://example.com"  # Metadata preserved
    
    @pytest.mark.asyncio
    async def test_clean_price_data(self):
        """Test price cleaning functionality"""
        cleaner = DataCleaner()
        
        test_data = [
            {"price": "$1,299.99", "cost": "€2.500,00"},
            {"price": "USD 99", "cost": "45.50 EUR"},
            {"price": "Free", "cost": "N/A"}
        ]
        
        cleaned_data, stats = await cleaner.process(test_data)
        
        # Check price cleaning
        assert "1299.99" in cleaned_data[0]["price"]
        assert cleaned_data[1]["price"] == "99"
    
    @pytest.mark.asyncio
    async def test_clean_url_data(self):
        """Test URL cleaning functionality"""
        cleaner = DataCleaner()
        
        test_data = [
            {"url": "//example.com/page", "link": "www.test.com"},
            {"url": "http://example.com//path//", "link": "/relative/path"}
        ]
        
        cleaned_data, stats = await cleaner.process(test_data)
        
        # Check URL cleaning
        assert cleaned_data[0]["url"].startswith("https://")
        assert cleaned_data[0]["link"].startswith("https://")
        assert "//" not in cleaned_data[1]["url"].replace("://", "_")
    
    def test_html_entity_decoding(self):
        """Test HTML entity decoding"""
        cleaner = DataCleaner()
        
        test_text = "Product &amp; Description &lt;with&gt; &quot;quotes&quot;"
        cleaned = cleaner._clean_text(test_text)
        
        assert "&" in cleaned
        assert "<with>" in cleaned
        assert '"quotes"' in cleaned


class TestDataValidator:
    """Test cases for DataValidator"""
    
    @pytest.mark.asyncio
    async def test_validate_valid_data(self):
        """Test validation of valid data"""
        validator = DataValidator()
        
        valid_data = [
            {
                "title": "Product Name",
                "email": "contact@example.com",
                "url": "https://example.com",
                "price": "29.99",
                "phone": "+1-555-123-4567"
            }
        ]
        
        validated_data, stats = await validator.process(valid_data)
        
        assert stats.total_items == 1
        assert stats.processed_items == 1
        
        validated_item = validated_data[0]
        assert validated_item["_is_valid"] == True
        assert validated_item["_validation_score"] > 0.5
        assert len(validated_item["_validation_errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_invalid_data(self):
        """Test validation of invalid data"""
        validator = DataValidator()
        
        invalid_data = [
            {
                "email": "invalid-email",
                "url": "not-a-url",
                "price": "invalid-price",
                "phone": "123"
            }
        ]
        
        validated_data, stats = await validator.process(invalid_data)
        
        validated_item = validated_data[0]
        assert len(validated_item["_validation_warnings"]) > 0
        assert validated_item["_validation_score"] < 1.0
    
    def test_field_type_detection(self):
        """Test field type detection"""
        validator = DataValidator()
        
        test_cases = [
            ("email", "test@example.com", "email"),
            ("contact_email", "user@test.com", "email"),
            ("website", "https://example.com", "url"),
            ("price", "$29.99", "price"),
            ("phone_number", "555-123-4567", "phone"),
            ("random_field", "random value", "text")
        ]
        
        for field_name, value, expected_type in test_cases:
            detected_type = validator._detect_field_type(field_name, value)
            assert detected_type == expected_type
    
    def test_email_validation(self):
        """Test email validation"""
        validator = DataValidator()
        
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "user123@test-domain.org"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com"
        ]
        
        for email in valid_emails:
            is_valid, _ = validator._validate_email(email)
            assert is_valid == True
        
        for email in invalid_emails:
            is_valid, _ = validator._validate_email(email)
            assert is_valid == False
    
    def test_url_validation(self):
        """Test URL validation"""
        validator = DataValidator()
        
        valid_urls = [
            "https://example.com",
            "http://test.org/path?param=value",
            "https://subdomain.example.com:8080/path"
        ]
        
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "https://",
            "http://.com"
        ]
        
        for url in valid_urls:
            is_valid, _ = validator._validate_url(url)
            assert is_valid == True
        
        for url in invalid_urls:
            is_valid, _ = validator._validate_url(url)
            assert is_valid == False
    
    def test_price_validation(self):
        """Test price validation"""
        validator = DataValidator()
        
        valid_prices = ["29.99", "$49.50", "100", "0.99"]
        invalid_prices = ["free", "N/A", "-10.00", "invalid"]
        
        for price in valid_prices:
            is_valid, _ = validator._validate_price(price)
            assert is_valid == True
        
        for price in invalid_prices:
            is_valid, _ = validator._validate_price(price)
            assert is_valid == False


class TestDataEnricher:
    """Test cases for DataEnricher"""
    
    @pytest.mark.asyncio
    async def test_enrich_basic_data(self):
        """Test basic data enrichment"""
        enricher = DataEnricher()
        
        basic_data = [
            {
                "title": "Product Name",
                "price": "$29.99",
                "url": "https://example.com/product",
                "_extracted_at": 1640995200.0
            }
        ]
        
        enriched_data, stats = await enricher.process(basic_data)
        
        assert stats.total_items == 1
        assert stats.processed_items == 1
        
        enriched_item = enriched_data[0]
        
        # Check added metadata
        assert "_enriched_at" in enriched_item
        assert "_field_count" in enriched_item
        assert "_content_hash" in enriched_item
        assert "_data_age_hours" in enriched_item
        
        # Check URL domain extraction
        assert "url_domain" in enriched_item
        assert enriched_item["url_domain"] == "example.com"
        
        # Check price normalization
        assert "price_numeric" in enriched_item
        assert enriched_item["price_numeric"] == 29.99
    
    @pytest.mark.asyncio
    async def test_enrich_text_statistics(self):
        """Test text statistics enrichment"""
        enricher = DataEnricher()
        
        text_data = [
            {
                "title": "Short title",
                "description": "This is a longer description with multiple words and sentences. It should be counted properly for text statistics."
            }
        ]
        
        enriched_data, stats = await enricher.process(text_data)
        
        enriched_item = enriched_data[0]
        
        assert "_total_text_length" in enriched_item
        assert "_total_word_count" in enriched_item
        assert enriched_item["_total_text_length"] > 50
        assert enriched_item["_total_word_count"] > 10
    
    def test_extract_domain(self):
        """Test domain extraction from URLs"""
        enricher = DataEnricher()
        
        test_cases = [
            ("https://example.com/path", "example.com"),
            ("http://subdomain.test.org:8080", "subdomain.test.org"),
            ("//protocol-relative.com", "protocol-relative.com"),
            ("invalid-url", None)
        ]
        
        for url, expected_domain in test_cases:
            domain = enricher._extract_domain(url)
            assert domain == expected_domain
    
    def test_normalize_price(self):
        """Test price normalization"""
        enricher = DataEnricher()
        
        test_cases = [
            ("$29.99", 29.99),
            ("EUR 45.50", 45.50),
            ("1,299.99", 1299.99),
            ("Free", None),
            ("Invalid", None)
        ]
        
        for price_str, expected_value in test_cases:
            normalized = enricher._normalize_price(price_str)
            assert normalized == expected_value
    
    def test_content_hash_generation(self):
        """Test content hash generation"""
        enricher = DataEnricher()
        
        item1 = {"title": "Product", "price": "29.99"}
        item2 = {"title": "Product", "price": "29.99"}
        item3 = {"title": "Different Product", "price": "39.99"}
        
        hash1 = enricher._generate_content_hash(item1)
        hash2 = enricher._generate_content_hash(item2)
        hash3 = enricher._generate_content_hash(item3)
        
        # Same content should have same hash
        assert hash1 == hash2
        
        # Different content should have different hash
        assert hash1 != hash3
        
        # Hash should be a valid MD5 hex string
        assert len(hash1) == 32
        assert all(c in "0123456789abcdef" for c in hash1)


class TestProcessingStats:
    """Test cases for ProcessingStats"""
    
    def test_processing_stats_initialization(self):
        """Test ProcessingStats initialization"""
        stats = ProcessingStats()
        
        assert stats.total_items == 0
        assert stats.processed_items == 0
        assert stats.failed_items == 0
        assert stats.modifications_made == 0
        assert stats.processing_time == 0.0
        assert isinstance(stats.errors, list)
        assert len(stats.errors) == 0
    
    def test_processing_stats_with_values(self):
        """Test ProcessingStats with specific values"""
        stats = ProcessingStats(
            total_items=100,
            processed_items=95,
            failed_items=5,
            modifications_made=80,
            processing_time=2.5
        )
        
        assert stats.total_items == 100
        assert stats.processed_items == 95
        assert stats.failed_items == 5
        assert stats.modifications_made == 80
        assert stats.processing_time == 2.5