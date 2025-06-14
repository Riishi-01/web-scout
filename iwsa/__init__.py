"""
Intelligent Web Scraping Agent (IWSA)
AI-powered web scraping with LLM intelligence
"""

__version__ = "1.0.0"
__author__ = "IWSA Team"
__email__ = "team@iwsa.dev"

from .core.engine import ScrapingEngine
from .core.prompt_processor import PromptProcessor
from .core.reconnaissance import ReconnaissanceEngine
from .llm.hub import LLMHub
from .scraper.dynamic_scraper import DynamicScraper
from .data.pipeline import DataPipeline

__all__ = [
    "ScrapingEngine",
    "PromptProcessor", 
    "ReconnaissanceEngine",
    "LLMHub",
    "DynamicScraper",
    "DataPipeline"
]