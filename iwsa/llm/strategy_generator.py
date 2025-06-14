"""
Unified LLM Strategy Generator
Single Purpose: HTML analysis → scraping strategy generation
Multiple Providers: TinyLlama (primary) → OpenAI/Claude/HuggingFace (fallback)
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

from .providers import TinyLlamaProvider, OpenAIProvider, ClaudeProvider, HuggingFaceProvider, LLMRequest, LLMResponse
from ..config import Settings
from ..utils.logger import ComponentLogger
from ..utils.helpers import CircuitBreaker


@dataclass
class ScrapingStrategy:
    """Unified scraping strategy response"""
    success: bool
    selectors: List[str] = None
    extraction_logic: str = ""
    pagination_strategy: Dict[str, Any] = None
    filters: List[Dict[str, Any]] = None
    error_handling: List[str] = None
    confidence_score: float = 0.0
    reasoning: str = ""
    provider_used: str = ""
    response_time: float = 0.0
    cost: float = 0.0
    
    def __post_init__(self):
        if self.selectors is None:
            self.selectors = []
        if self.pagination_strategy is None:
            self.pagination_strategy = {}
        if self.filters is None:
            self.filters = []
        if self.error_handling is None:
            self.error_handling = []


class LLMStrategyGenerator:
    """
    Single-purpose LLM system: HTML analysis → scraping strategy generation
    Multiple providers for reliability: Local TinyLlama → Cloud fallbacks
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = ComponentLogger("llm_strategy_generator")
        
        # Initialize providers in priority order
        self.providers = {}
        self._initialize_providers()
        
        # Circuit breakers for reliability
        self.circuit_breakers = {
            name: CircuitBreaker(
                failure_threshold=3,
                recovery_timeout=300.0,  # 5 minutes
                expected_exception=Exception
            ) for name in self.providers.keys()
        }
        
        # Provider priority: Local first, then cloud fallbacks
        self.provider_priority = self._get_provider_priority()
        
        self.logger.info("LLM Strategy Generator initialized",
                        providers=list(self.providers.keys()),
                        primary_provider=self.provider_priority[0] if self.provider_priority else None)
    
    def _initialize_providers(self):
        """Initialize providers in priority order"""
        # 1. Local TinyLlama (Primary - fast, offline)
        tinyllama = TinyLlamaProvider(self.settings)
        if tinyllama.is_available:
            self.providers["tinyllama"] = tinyllama
            self.logger.info("TinyLlama provider initialized (primary)")
        
        # 2. OpenAI (First cloud fallback)
        openai = OpenAIProvider(self.settings)
        if openai.is_available:
            self.providers["openai"] = openai
            self.logger.info("OpenAI provider initialized (fallback)")
        
        # 3. Claude (Second cloud fallback)
        claude = ClaudeProvider(self.settings)
        if claude.is_available:
            self.providers["claude"] = claude
            self.logger.info("Claude provider initialized (fallback)")
        
        # 4. HuggingFace (Final fallback)
        huggingface = HuggingFaceProvider(self.settings)
        self.providers["huggingface"] = huggingface
        self.logger.info("HuggingFace provider initialized (final fallback)")
        
        if not self.providers:
            raise RuntimeError("No LLM providers available for strategy generation")
    
    def _get_provider_priority(self) -> List[str]:
        """Get provider priority order: Local first, then cloud"""
        priority = []
        
        # Always prefer local if available
        if "tinyllama" in self.providers:
            priority.append("tinyllama")
        
        # Then cloud providers based on configuration
        cloud_order = ["openai", "claude", "huggingface"]
        for provider in cloud_order:
            if provider in self.providers and provider not in priority:
                priority.append(provider)
        
        return priority
    
    async def generate_scraping_strategy(self,
                                       html_content: str,
                                       url: str,
                                       user_intent: str,
                                       extraction_fields: List[str] = None) -> ScrapingStrategy:
        """
        Single LLM purpose: Analyze HTML and generate complete scraping strategy
        
        Args:
            html_content: HTML content to analyze
            url: Source URL
            user_intent: What the user wants to extract
            extraction_fields: Specific fields to extract
            
        Returns:
            Complete scraping strategy
        """
        start_time = time.time()
        
        self.logger.info("Generating scraping strategy",
                        url=url,
                        html_length=len(html_content),
                        user_intent=user_intent[:100])
        
        # Prepare unified prompt
        request = self._prepare_strategy_request(html_content, url, user_intent, extraction_fields)
        
        # Try providers in priority order (local first)
        for provider_name in self.provider_priority:
            provider = self.providers[provider_name]
            circuit_breaker = self.circuit_breakers[provider_name]
            
            try:
                # Check circuit breaker
                if circuit_breaker.state == "OPEN":
                    self.logger.warning("Provider circuit breaker open, trying next",
                                      provider=provider_name)
                    continue
                
                # Execute with circuit breaker protection
                response = await circuit_breaker.call(provider.generate_response, request)
                
                if response.success:
                    # Parse strategy from response
                    strategy = self._parse_strategy_response(response, provider_name)
                    
                    if strategy.success:
                        strategy.response_time = time.time() - start_time
                        
                        self.logger.info("Strategy generated successfully",
                                       provider=provider_name,
                                       confidence=strategy.confidence_score,
                                       selectors_count=len(strategy.selectors),
                                       response_time=strategy.response_time,
                                       cost=strategy.cost)
                        
                        return strategy
                    else:
                        self.logger.warning("Strategy parsing failed, trying next provider",
                                          provider=provider_name,
                                          reasoning=strategy.reasoning)
                        continue
                else:
                    self.logger.warning("Provider request failed, trying next",
                                      provider=provider_name,
                                      error=response.error)
                    continue
            
            except Exception as e:
                self.logger.error("Provider execution error, trying next",
                                provider=provider_name,
                                error=str(e))
                continue
        
        # All providers failed
        return ScrapingStrategy(
            success=False,
            reasoning="All LLM providers failed to generate strategy",
            response_time=time.time() - start_time
        )
    
    def _prepare_strategy_request(self,
                                html_content: str,
                                url: str,
                                user_intent: str,
                                extraction_fields: List[str] = None) -> LLMRequest:
        """Prepare unified strategy generation request"""
        
        # Truncate HTML if too long
        if len(html_content) > 50000:
            html_content = html_content[:50000] + "... [truncated]"
        
        system_prompt = """You are an expert web scraping strategist. Analyze the HTML and generate a complete scraping strategy.

Return your response as a JSON object with this exact structure:
{
    "selectors": ["css_selector1", "css_selector2"],
    "extraction_logic": "detailed explanation of extraction approach",
    "pagination_strategy": {
        "type": "numbered|infinite_scroll|load_more|none",
        "selectors": ["pagination_selectors"],
        "logic": "pagination handling approach"
    },
    "filters": [
        {
            "name": "filter_name",
            "selector": "filter_selector",
            "type": "dropdown|input|checkbox",
            "default_value": "default"
        }
    ],
    "error_handling": ["strategy1", "strategy2"],
    "confidence_score": 0.85,
    "reasoning": "detailed explanation of analysis and choices"
}

Focus on:
1. Robust, reliable selectors
2. Complete extraction strategy
3. Pagination and filtering
4. Error handling approaches
5. Confidence in the strategy"""
        
        fields_text = ""
        if extraction_fields:
            fields_text = f"\nSpecific fields to extract: {', '.join(extraction_fields)}"
        
        user_message = f"""Analyze this HTML content and generate a complete scraping strategy:

URL: {url}
User Intent: {user_intent}{fields_text}

HTML Content:
{html_content}

Generate a comprehensive scraping strategy that handles all aspects of data extraction from this page."""
        
        return LLMRequest(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.1
        )
    
    def _parse_strategy_response(self, response: LLMResponse, provider_name: str) -> ScrapingStrategy:
        """Parse LLM response into scraping strategy"""
        try:
            # Extract JSON from response
            content = response.content.strip()
            
            # Find JSON in response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1 or end_idx <= start_idx:
                return ScrapingStrategy(
                    success=False,
                    reasoning="No JSON found in response"
                )
            
            json_str = content[start_idx:end_idx]
            strategy_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["selectors", "extraction_logic", "confidence_score"]
            for field in required_fields:
                if field not in strategy_data:
                    return ScrapingStrategy(
                        success=False,
                        reasoning=f"Missing required field: {field}"
                    )
            
            # Create strategy object
            return ScrapingStrategy(
                success=True,
                selectors=strategy_data.get("selectors", []),
                extraction_logic=strategy_data.get("extraction_logic", ""),
                pagination_strategy=strategy_data.get("pagination_strategy", {}),
                filters=strategy_data.get("filters", []),
                error_handling=strategy_data.get("error_handling", []),
                confidence_score=strategy_data.get("confidence_score", 0.0),
                reasoning=strategy_data.get("reasoning", ""),
                provider_used=provider_name,
                cost=response.cost or 0.0
            )
        
        except json.JSONDecodeError as e:
            return ScrapingStrategy(
                success=False,
                reasoning=f"JSON parsing error: {str(e)}"
            )
        except Exception as e:
            return ScrapingStrategy(
                success=False,
                reasoning=f"Strategy parsing error: {str(e)}"
            )
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        
        for provider_name, provider in self.providers.items():
            circuit_breaker = self.circuit_breakers[provider_name]
            
            status[provider_name] = {
                "available": provider.is_available,
                "circuit_breaker_state": circuit_breaker.state,
                "failure_count": circuit_breaker.failure_count,
                "provider_type": provider.provider_name,
                "priority": self.provider_priority.index(provider_name) if provider_name in self.provider_priority else -1
            }
        
        return status
    
    def estimate_cost(self, html_content: str, user_intent: str) -> float:
        """Estimate cost for strategy generation"""
        # Use primary provider for estimation
        if self.provider_priority:
            primary_provider = self.providers[self.provider_priority[0]]
            dummy_request = self._prepare_strategy_request(html_content, "", user_intent)
            return primary_provider.estimate_cost(dummy_request)
        return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        self.logger.info("Performing strategy generator health check")
        
        health_status = {
            "overall_health": "healthy",
            "providers": {},
            "primary_provider": self.provider_priority[0] if self.provider_priority else None,
            "timestamp": time.time()
        }
        
        # Test each provider
        test_request = LLMRequest(
            messages=[{"role": "user", "content": "Generate a simple test response"}],
            max_tokens=50
        )
        
        healthy_providers = 0
        
        for provider_name, provider in self.providers.items():
            try:
                if provider.is_available:
                    response = await asyncio.wait_for(
                        provider.generate_response(test_request),
                        timeout=10.0
                    )
                    
                    provider_health = {
                        "status": "healthy" if response.success else "degraded",
                        "response_time": response.response_time,
                        "error": response.error
                    }
                    
                    if response.success:
                        healthy_providers += 1
                else:
                    provider_health = {
                        "status": "unavailable",
                        "error": "Provider not configured"
                    }
            
            except asyncio.TimeoutError:
                provider_health = {
                    "status": "timeout",
                    "error": "Health check timeout"
                }
            except Exception as e:
                provider_health = {
                    "status": "error",
                    "error": str(e)
                }
            
            health_status["providers"][provider_name] = provider_health
        
        # Determine overall health
        if healthy_providers == 0:
            health_status["overall_health"] = "critical"
        elif healthy_providers < len(self.providers):
            health_status["overall_health"] = "degraded"
        
        self.logger.info("Health check completed",
                        overall_health=health_status["overall_health"],
                        healthy_providers=healthy_providers,
                        total_providers=len(self.providers))
        
        return health_status