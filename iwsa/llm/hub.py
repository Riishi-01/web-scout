"""
LLM Hub - Simplified single-purpose LLM system
Purpose: HTML analysis → scraping strategy generation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .strategy_generator import LLMStrategyGenerator, ScrapingStrategy
from ..config import Settings
from ..utils.logger import ComponentLogger


class LLMHub:
    """
    Simplified LLM Hub - Single purpose: HTML → scraping strategy
    Multiple providers for reliability: TinyLlama (primary) → Cloud fallbacks
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = ComponentLogger("llm_hub")
        
        # Single-purpose strategy generator
        self.strategy_generator = LLMStrategyGenerator(settings)
        
        self.logger.info("LLM Hub initialized with single-purpose strategy generator")
    
    async def generate_scraping_strategy(self,
                                        html_content: str,
                                        url: str,
                                        user_intent: str,
                                        extraction_fields: List[str] = None) -> ScrapingStrategy:
        """
        Single LLM purpose: Analyze HTML and generate complete scraping strategy
        Uses multiple providers for reliability: TinyLlama → OpenAI → Claude → HuggingFace
        
        Args:
            html_content: HTML content to analyze
            url: Source URL
            user_intent: What the user wants to extract
            extraction_fields: Specific fields to extract
            
        Returns:
            Complete scraping strategy with selectors, pagination, filters, etc.
        """
        return await self.strategy_generator.generate_scraping_strategy(
            html_content=html_content,
            url=url,
            user_intent=user_intent,
            extraction_fields=extraction_fields
        )
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers from strategy generator"""
        return self.strategy_generator.get_provider_status()
    
    def estimate_cost(self, html_content: str, user_intent: str) -> float:
        """Estimate cost for strategy generation"""
        return self.strategy_generator.estimate_cost(html_content, user_intent)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on strategy generator"""
        return await self.strategy_generator.health_check()