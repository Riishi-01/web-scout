"""
Dynamic scraper core with LLM-powered adaptation and anti-detection
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from playwright.async_api import Page

from .browser_manager import BrowserManager, BrowserConfig
from .anti_detection import AntiDetectionManager, BehavioralPattern
from .session_manager import SessionManager, SessionState
from ..core.reconnaissance import SiteMetadata, FilterInfo, PaginationInfo, ContentPattern
from ..llm.hub import LLMHub
from ..config import Settings
from ..utils.logger import ComponentLogger
from ..utils.helpers import retry_with_backoff, measure_time


@dataclass
class ExtractionResult:
    """Result of data extraction operation"""
    success: bool
    data: List[Dict[str, Any]] = field(default_factory=list)
    total_items: int = 0
    pages_processed: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_data(self, items: List[Dict[str, Any]]):
        """Add extracted items to result"""
        self.data.extend(items)
        self.total_items = len(self.data)
    
    def add_error(self, error: str):
        """Add error to result"""
        self.errors.append(error)
        if len(self.errors) > 10:  # Limit error count
            self.errors = self.errors[-10:]


@dataclass 
class ScrapingStrategy:
    """Complete scraping strategy from LLM"""
    approach: str
    steps: List[str]
    selectors: Dict[str, str]
    filter_sequence: List[Dict[str, Any]] = field(default_factory=list)
    timing_strategy: Dict[str, float] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_llm_response(cls, llm_data: Dict[str, Any]) -> 'ScrapingStrategy':
        """Create strategy from LLM response"""
        return cls(
            approach=llm_data.get("scraping_plan", {}).get("approach", ""),
            steps=llm_data.get("scraping_plan", {}).get("steps", []),
            selectors=llm_data.get("selectors", {}),
            filter_sequence=llm_data.get("filter_sequence", []),
            timing_strategy=llm_data.get("timing_strategy", {}),
            risk_assessment=llm_data.get("risk_assessment", {})
        )


class DynamicScraper:
    """
    Dynamic scraper with LLM-powered adaptation and intelligent error handling
    """
    
    def __init__(self, settings: Settings, llm_hub: LLMHub):
        self.settings = settings
        self.llm_hub = llm_hub
        self.logger = ComponentLogger("dynamic_scraper")
        
        # Component managers
        self.browser_manager = None  # Initialized in context manager
        self.anti_detection = AntiDetectionManager(settings)
        self.session_manager = SessionManager(settings)
        
        # Scraping state
        self.current_strategy: Optional[ScrapingStrategy] = None
        self.extraction_cache: Dict[str, Any] = {}
        
        # Performance tracking
        self.pages_processed = 0
        self.total_items_extracted = 0
        self.start_time = 0
        
        self.logger.info("Dynamic scraper initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.browser_manager = BrowserManager(self.settings)
        await self.browser_manager.__aenter__()
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.browser_manager:
            await self.browser_manager.__aexit__(exc_type, exc_val, exc_tb)
        
        # Log final statistics
        duration = time.time() - self.start_time
        self.logger.info("Scraping session completed",
                        duration=duration,
                        pages_processed=self.pages_processed,
                        items_extracted=self.total_items_extracted,
                        items_per_minute=(self.total_items_extracted / duration * 60) if duration > 0 else 0)
    
    @measure_time
    async def scrape_site(self, 
                         site_metadata: SiteMetadata,
                         user_requirements: Dict[str, Any],
                         scraping_profile: str = "balanced") -> ExtractionResult:
        """
        Main scraping method with LLM-powered strategy generation
        
        Args:
            site_metadata: Site analysis from reconnaissance
            user_requirements: User's extraction requirements
            scraping_profile: Scraping profile to use
            
        Returns:
            ExtractionResult with extracted data
        """
        self.logger.info("Starting site scraping", 
                        url=site_metadata.url,
                        profile=scraping_profile)
        
        result = ExtractionResult(success=False)
        session = None
        browser_instance = None
        
        try:
            # Generate scraping strategy using LLM
            strategy_response = await self.llm_hub.generate_strategy(
                site_structure=site_metadata.to_dict(),
                user_requirements=user_requirements,
                detected_filters=site_metadata.filters,
                performance_constraints=self._get_performance_constraints()
            )
            
            if not strategy_response.success:
                result.add_error(f"Strategy generation failed: {strategy_response.reasoning}")
                return result
            
            self.current_strategy = ScrapingStrategy.from_llm_response(strategy_response.data)
            
            # Create session
            session = await self.session_manager.create_session(site_metadata.url)
            
            # Get browser instance
            browser_config = self._create_browser_config(scraping_profile, site_metadata)
            browser_instance = await self.browser_manager.get_browser_instance(browser_config)
            
            # Apply anti-detection measures
            domain = urlparse(site_metadata.url).netloc
            await self.anti_detection.apply_rate_limiting(domain, scraping_profile)
            
            # Navigate to site
            await self._navigate_to_site(browser_instance.page, session, site_metadata.url)
            
            # Apply filters if needed
            if site_metadata.filters:
                await self._apply_filters(browser_instance.page, site_metadata.filters, user_requirements)
            
            # Extract data with pagination handling
            if site_metadata.pagination:
                result = await self._extract_with_pagination(
                    browser_instance.page, 
                    site_metadata.pagination,
                    site_metadata.content_patterns,
                    session
                )
            else:
                # Single page extraction
                extracted_data = await self._extract_page_data(
                    browser_instance.page,
                    site_metadata.content_patterns
                )
                result.add_data(extracted_data)
                result.pages_processed = 1
            
            result.success = len(result.data) > 0
            
            # Quality assessment
            if result.data:
                quality_response = await self.llm_hub.assess_quality(
                    extracted_data=result.data[:10],  # Sample for analysis
                    expected_patterns=user_requirements.get("expected_patterns", {}),
                    extraction_metadata={"pages_processed": result.pages_processed}
                )
                
                if quality_response.success:
                    result.metadata["quality_assessment"] = quality_response.data
            
            self.total_items_extracted += result.total_items
            self.pages_processed += result.pages_processed
            
            self.logger.info("Site scraping completed",
                           success=result.success,
                           items_extracted=result.total_items,
                           pages_processed=result.pages_processed)
            
        except Exception as e:
            error_msg = f"Scraping failed: {str(e)}"
            result.add_error(error_msg)
            self.logger.error("Site scraping failed", error=str(e), exc_info=True)
            
            # Try to recover using LLM
            if browser_instance:
                await self._attempt_error_recovery(browser_instance.page, str(e), result)
        
        finally:
            # Clean up resources
            if browser_instance:
                await self.browser_manager.release_instance(browser_instance)
            if session:
                await self.session_manager.cleanup_session(session.session_id)
        
        return result
    
    def _create_browser_config(self, profile: str, site_metadata: SiteMetadata) -> BrowserConfig:
        """Create browser configuration based on profile and site analysis"""
        config = BrowserConfig(
            headless=self.settings.scraping.headless,
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        
        # Adjust based on anti-detection requirements
        if site_metadata.anti_detection.recommended_profile == "stealth":
            config.extra_headers = {
                "sec-ch-ua": '"Google Chrome";v="120", "Chromium";v="120", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            }
        
        # Apply proxy if available and needed
        if (site_metadata.anti_detection.cloudflare_detected or 
            site_metadata.anti_detection.captcha_detected):
            proxy = self.anti_detection.get_next_proxy()
            if proxy:
                config.proxy = proxy.server
        
        return config
    
    async def _navigate_to_site(self, page: Page, session: SessionState, url: str):
        """Navigate to site with session restoration"""
        try:
            # Check if we have existing session state
            if session.cookies or session.current_page:
                await self.session_manager.restore_session_state(
                    session.session_id, page, page.context
                )
            else:
                # Fresh navigation
                await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Save current state
            await self.session_manager.save_session_state(
                session.session_id, page, page.context
            )
            
            # Handle any CAPTCHA/challenges
            await self.anti_detection.handle_captcha_detection(page)
            
            # Simulate human behavior
            await self.anti_detection.simulate_human_behavior(page)
            
        except Exception as e:
            self.logger.error("Navigation failed", url=url, error=str(e))
            raise
    
    async def _apply_filters(self, 
                           page: Page, 
                           filters: List[FilterInfo], 
                           user_requirements: Dict[str, Any]):
        """Apply filters based on user requirements"""
        if not self.current_strategy or not self.current_strategy.filter_sequence:
            return
        
        self.logger.info("Applying filters", count=len(self.current_strategy.filter_sequence))
        
        for filter_action in self.current_strategy.filter_sequence:
            try:
                filter_selector = filter_action.get("filter")
                action = filter_action.get("action")
                value = filter_action.get("value")
                wait_time = filter_action.get("wait_time", 2)
                
                if not filter_selector or not action:
                    continue
                
                # Apply filter based on action type
                if action == "select":
                    await page.select_option(filter_selector, value)
                elif action == "click":
                    await self.anti_detection.human_like_click(page, filter_selector)
                elif action == "type":
                    await self.anti_detection.human_like_type(page, filter_selector, value)
                elif action == "check":
                    await page.check(filter_selector)
                elif action == "uncheck":
                    await page.uncheck(filter_selector)
                
                # Wait for filter to apply
                await asyncio.sleep(wait_time)
                await self.anti_detection.wait_for_page_load(page)
                
                self.logger.debug("Filter applied", 
                                selector=filter_selector,
                                action=action,
                                value=value)
                
            except Exception as e:
                self.logger.warning("Filter application failed", 
                                  filter=filter_action,
                                  error=str(e))
                continue
    
    async def _extract_with_pagination(self, 
                                     page: Page,
                                     pagination_info: PaginationInfo,
                                     content_patterns: List[ContentPattern],
                                     session: SessionState) -> ExtractionResult:
        """Extract data across multiple pages"""
        result = ExtractionResult(success=False)
        current_page = 1
        max_pages = self.settings.scraping.max_pages_per_session or 100
        
        self.logger.info("Starting paginated extraction", 
                        pagination_type=pagination_info.type,
                        max_pages=max_pages)
        
        try:
            while current_page <= max_pages:
                # Extract data from current page
                page_data = await self._extract_page_data(page, content_patterns)
                
                if page_data:
                    result.add_data(page_data)
                    result.pages_processed += 1
                    
                    self.logger.debug("Page extracted", 
                                    page=current_page,
                                    items=len(page_data))
                else:
                    self.logger.warning("No data extracted from page", page=current_page)
                
                # Try to navigate to next page
                next_page_found = await self._navigate_to_next_page(page, pagination_info)
                
                if not next_page_found:
                    self.logger.info("No more pages found, stopping pagination")
                    break
                
                # Save session state after each page
                await self.session_manager.save_session_state(
                    session.session_id, page, page.context
                )
                
                # Apply rate limiting
                domain = urlparse(page.url).netloc
                await self.anti_detection.apply_rate_limiting(domain)
                
                current_page += 1
            
            result.success = result.total_items > 0
            
        except Exception as e:
            result.add_error(f"Pagination extraction failed: {str(e)}")
            self.logger.error("Pagination extraction failed", error=str(e))
        
        return result
    
    async def _navigate_to_next_page(self, page: Page, pagination_info: PaginationInfo) -> bool:
        """Navigate to next page based on pagination type"""
        try:
            if pagination_info.type == "numbered":
                # Look for next page link
                next_selectors = [
                    pagination_info.selectors.get("next"),
                    ".next",
                    "a:contains('Next')",
                    "a:contains('>')",
                    "[aria-label*='next']"
                ]
                
                for selector in next_selectors:
                    if not selector:
                        continue
                    
                    element = await page.query_selector(selector)
                    if element and await element.is_enabled():
                        await self.anti_detection.human_like_click(page, selector)
                        await self.anti_detection.wait_for_page_load(page)
                        return True
            
            elif pagination_info.type == "load_more":
                # Look for load more button
                load_more_selector = pagination_info.selectors.get("trigger", ".load-more")
                element = await page.query_selector(load_more_selector)
                
                if element and await element.is_visible():
                    await self.anti_detection.human_like_click(page, load_more_selector)
                    await asyncio.sleep(3)  # Wait for content to load
                    return True
            
            elif pagination_info.type == "infinite_scroll":
                # Simulate scrolling to trigger infinite scroll
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                
                # Check if new content loaded
                return True  # In real implementation, would check for new content
            
            return False
            
        except Exception as e:
            self.logger.warning("Next page navigation failed", error=str(e))
            return False
    
    async def _extract_page_data(self, 
                                page: Page, 
                                content_patterns: List[ContentPattern]) -> List[Dict[str, Any]]:
        """Extract data from current page using content patterns"""
        if not content_patterns:
            return []
        
        # Use the highest confidence pattern
        best_pattern = max(content_patterns, key=lambda p: p.confidence_score)
        
        try:
            # Get all item containers
            items = await page.query_selector_all(best_pattern.item_selector)
            
            if not items:
                self.logger.warning("No items found with selector", 
                                  selector=best_pattern.item_selector)
                return []
            
            extracted_data = []
            
            for item in items:
                item_data = {}
                
                # Extract each field
                for field_name, field_selector in best_pattern.field_selectors.items():
                    try:
                        field_element = await item.query_selector(field_selector)
                        if field_element:
                            # Get text content, handling different element types
                            if await field_element.get_attribute("href"):
                                # Link element
                                value = await field_element.get_attribute("href")
                                # Convert relative URLs to absolute
                                if value and not value.startswith("http"):
                                    value = urljoin(page.url, value)
                            elif await field_element.get_attribute("src"):
                                # Image element
                                value = await field_element.get_attribute("src")
                                if value and not value.startswith("http"):
                                    value = urljoin(page.url, value)
                            else:
                                # Text content
                                value = await field_element.text_content()
                                if value:
                                    value = value.strip()
                            
                            if value:
                                item_data[field_name] = value
                    
                    except Exception as e:
                        self.logger.debug("Field extraction failed", 
                                        field=field_name,
                                        selector=field_selector,
                                        error=str(e))
                        continue
                
                if item_data:
                    # Add metadata
                    item_data["_source_url"] = page.url
                    item_data["_extracted_at"] = time.time()
                    extracted_data.append(item_data)
            
            self.logger.debug("Data extracted from page", 
                            items_found=len(items),
                            items_extracted=len(extracted_data))
            
            return extracted_data
            
        except Exception as e:
            self.logger.error("Page data extraction failed", error=str(e))
            return []
    
    async def _attempt_error_recovery(self, page: Page, error_msg: str, result: ExtractionResult):
        """Attempt to recover from extraction errors using LLM"""
        try:
            self.logger.info("Attempting error recovery with LLM")
            
            # Get current page state
            page_state = {
                "url": page.url,
                "title": await page.title(),
                "has_content": bool(await page.query_selector("body")),
                "page_size": len(await page.content())
            }
            
            # Get current selectors that failed
            failed_selectors = []
            if self.current_strategy and self.current_strategy.selectors:
                failed_selectors = list(self.current_strategy.selectors.values())
            
            # Ask LLM for resolution
            resolution_response = await self.llm_hub.resolve_error(
                error_context=error_msg,
                failed_selectors=failed_selectors,
                page_state=page_state,
                previous_attempts=result.errors[-3:] if len(result.errors) > 3 else result.errors
            )
            
            if resolution_response.success:
                resolution_data = resolution_response.data
                
                # Try updated selectors
                updated_selectors = resolution_data.get("updated_selectors", [])
                if updated_selectors:
                    self.logger.info("Trying updated selectors from LLM")
                    
                    # Create temporary content pattern with new selectors
                    temp_pattern = ContentPattern(
                        container_selector="body",
                        item_selector=updated_selectors[0] if updated_selectors else ".item",
                        field_selectors={f"field_{i}": selector for i, selector in enumerate(updated_selectors)},
                        confidence_score=0.8
                    )
                    
                    # Attempt extraction with new selectors
                    recovery_data = await self._extract_page_data(page, [temp_pattern])
                    
                    if recovery_data:
                        result.add_data(recovery_data)
                        result.success = True
                        self.logger.info("Error recovery successful", 
                                       items_recovered=len(recovery_data))
                    else:
                        result.add_error("LLM recovery attempt failed - no data extracted")
                else:
                    result.add_error("LLM recovery provided no updated selectors")
            else:
                result.add_error(f"LLM error resolution failed: {resolution_response.reasoning}")
                
        except Exception as e:
            result.add_error(f"Error recovery attempt failed: {str(e)}")
            self.logger.error("Error recovery failed", error=str(e))
    
    def _get_performance_constraints(self) -> Dict[str, Any]:
        """Get current performance constraints"""
        return {
            "max_memory_mb": 512,
            "max_concurrent_browsers": self.settings.scraping.max_concurrent_browsers,
            "max_pages_per_session": getattr(self.settings.scraping, 'max_pages_per_session', 100),
            "target_extraction_rate": 30,  # items per minute
            "max_session_duration": 3600   # 1 hour
        }
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get current scraping statistics"""
        duration = time.time() - self.start_time if self.start_time else 0
        
        return {
            "pages_processed": self.pages_processed,
            "items_extracted": self.total_items_extracted,
            "duration_seconds": duration,
            "pages_per_minute": (self.pages_processed / duration * 60) if duration > 0 else 0,
            "items_per_minute": (self.total_items_extracted / duration * 60) if duration > 0 else 0,
            "browser_pool_status": self.browser_manager.get_pool_status() if self.browser_manager else {},
            "session_stats": self.session_manager.get_session_stats(),
            "anti_detection_status": self.anti_detection.get_detection_status()
        }