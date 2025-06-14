"""
Pytest configuration and fixtures for IWSA tests
"""

import pytest
import asyncio
from unittest.mock import MagicMock
from typing import Dict, Any

from iwsa.config import Settings
from iwsa.core.prompt_processor import PromptProcessor
from iwsa.core.reconnaissance import ReconnaissanceEngine
from iwsa.llm.hub import LLMHub
from iwsa.data.pipeline import DataPipeline


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Create test settings with mock values"""
    import os
    
    # Set test environment variables
    os.environ.update({
        'ENVIRONMENT': 'test',
        'MONGODB_URI': 'mongodb://localhost:27017',
        'MONGODB_DATABASE': 'iwsa_test',
        'OPENAI_API_KEY': 'test_key',
        'DEBUG': 'true'
    })
    
    return Settings()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response data"""
    return {
        "selectors": [".product-card", ".item"],
        "extraction_logic": "Find product cards and extract data from each",
        "confidence_score": 0.85,
        "alternative_strategies": ["Use grid layout", "Try list view"],
        "reasoning": "Product cards are consistently structured"
    }


@pytest.fixture
def sample_extracted_data():
    """Sample extracted data for testing"""
    return [
        {
            "title": "Product 1",
            "price": "$29.99",
            "description": "Great product description",
            "_source_url": "https://example.com/products",
            "_extracted_at": 1640995200.0
        },
        {
            "title": "Product 2", 
            "price": "$49.99",
            "description": "Another product description",
            "_source_url": "https://example.com/products",
            "_extracted_at": 1640995260.0
        }
    ]


@pytest.fixture
def sample_site_metadata():
    """Sample site metadata for testing"""
    from iwsa.core.reconnaissance import SiteMetadata, FilterInfo, PaginationInfo, ContentPattern, AntiDetectionInfo
    
    return SiteMetadata(
        url="https://example.com",
        title="Example Store",
        description="Example e-commerce site",
        filters=[
            FilterInfo(
                type="dropdown",
                selector="#category-filter",
                label="Category",
                options=["Electronics", "Books", "Clothing"]
            )
        ],
        pagination=PaginationInfo(
            type="numbered",
            selectors={"next": ".next-page", "prev": ".prev-page"}
        ),
        content_patterns=[
            ContentPattern(
                container_selector=".products",
                item_selector=".product-card",
                field_selectors={
                    "title": ".product-title",
                    "price": ".product-price",
                    "description": ".product-desc"
                },
                confidence_score=0.9
            )
        ],
        anti_detection=AntiDetectionInfo(
            recommended_profile="balanced"
        )
    )


@pytest.fixture
def mock_prompt_processor(test_settings):
    """Mock prompt processor for testing"""
    processor = PromptProcessor(test_settings)
    return processor


@pytest.fixture
def mock_reconnaissance(test_settings):
    """Mock reconnaissance engine for testing"""
    return ReconnaissanceEngine(test_settings)


@pytest.fixture
def mock_llm_hub(test_settings):
    """Mock LLM hub for testing"""
    hub = LLMHub(test_settings)
    
    # Mock the providers to avoid actual API calls
    for provider_name in hub.providers:
        hub.providers[provider_name] = MagicMock()
    
    return hub


@pytest.fixture
async def mock_data_pipeline(test_settings):
    """Mock data pipeline for testing"""
    pipeline = DataPipeline(test_settings)
    
    # Mock storage to avoid database calls
    pipeline.storage = MagicMock()
    
    return pipeline


@pytest.fixture
def sample_user_prompt():
    """Sample user prompts for testing"""
    return {
        "simple": "Scrape products from example.com",
        "detailed": "Extract job listings from careers.example.com showing title, company, location, and salary for remote Python developer positions",
        "with_filters": "Get product listings from store.com under $100 in the Electronics category",
        "with_pagination": "Scrape the first 5 pages of search results from example.com"
    }


@pytest.fixture
def mock_browser_page():
    """Mock Playwright page object"""
    mock_page = MagicMock()
    mock_page.url = "https://example.com"
    mock_page.title.return_value = "Example Site"
    mock_page.content.return_value = "<html><body>Mock content</body></html>"
    mock_page.query_selector_all.return_value = []
    return mock_page


@pytest.fixture
def mock_export_result():
    """Mock export result for testing"""
    from iwsa.data.exporters import ExportResult
    
    return ExportResult(
        success=True,
        export_url="https://docs.google.com/spreadsheets/d/test123",
        records_exported=10,
        export_time=2.5,
        metadata={"spreadsheet_id": "test123"}
    )


@pytest.mark.asyncio
class AsyncTestCase:
    """Base class for async test cases"""
    pass