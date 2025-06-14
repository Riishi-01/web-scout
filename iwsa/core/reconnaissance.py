"""
Reconnaissance Engine - Website structure discovery and analysis
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup, Tag
import aiohttp
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from ..config import Settings
from ..utils.logger import ComponentLogger
from ..utils.helpers import retry_with_backoff, measure_time


@dataclass
class FilterInfo:
    """Information about a detected filter"""
    type: str  # dropdown, checkbox, radio, text_input, slider
    selector: str
    label: str
    options: List[str] = field(default_factory=list)
    default_value: Optional[str] = None
    required: bool = False
    dependencies: List[str] = field(default_factory=list)  # Other filters this depends on


@dataclass
class PaginationInfo:
    """Information about pagination mechanisms"""
    type: str  # numbered, next_prev, infinite_scroll, load_more
    selectors: Dict[str, str] = field(default_factory=dict)
    current_page_selector: Optional[str] = None
    total_pages_selector: Optional[str] = None
    items_per_page: Optional[int] = None
    estimated_total_items: Optional[int] = None


@dataclass
class ContentPattern:
    """Information about repeating content patterns"""
    container_selector: str
    item_selector: str
    field_selectors: Dict[str, str] = field(default_factory=dict)
    confidence_score: float = 0.0
    sample_data: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class AntiDetectionInfo:
    """Information about anti-bot measures"""
    captcha_detected: bool = False
    rate_limiting: bool = False
    js_protection: bool = False
    cloudflare_detected: bool = False
    bot_detection_signals: List[str] = field(default_factory=list)
    recommended_profile: str = "balanced"


@dataclass
class SiteMetadata:
    """Complete site reconnaissance data"""
    url: str
    title: str = ""
    description: str = ""
    
    # Structure analysis
    filters: List[FilterInfo] = field(default_factory=list)
    pagination: Optional[PaginationInfo] = None
    content_patterns: List[ContentPattern] = field(default_factory=list)
    
    # Technical analysis
    load_time: float = 0.0
    js_heavy: bool = False
    mobile_responsive: bool = True
    
    # Security analysis
    anti_detection: AntiDetectionInfo = field(default_factory=AntiDetectionInfo)
    
    # Authentication
    requires_login: bool = False
    login_form_selector: Optional[str] = None
    
    # Additional metadata
    language: str = "en"
    geo_restricted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "filters": [
                {
                    "type": f.type,
                    "selector": f.selector, 
                    "label": f.label,
                    "options": f.options,
                    "default_value": f.default_value,
                    "required": f.required,
                    "dependencies": f.dependencies
                } for f in self.filters
            ],
            "pagination": {
                "type": self.pagination.type,
                "selectors": self.pagination.selectors,
                "current_page_selector": self.pagination.current_page_selector,
                "total_pages_selector": self.pagination.total_pages_selector,
                "items_per_page": self.pagination.items_per_page,
                "estimated_total_items": self.pagination.estimated_total_items
            } if self.pagination else None,
            "content_patterns": [
                {
                    "container_selector": p.container_selector,
                    "item_selector": p.item_selector,
                    "field_selectors": p.field_selectors,
                    "confidence_score": p.confidence_score,
                    "sample_data": p.sample_data
                } for p in self.content_patterns
            ],
            "load_time": self.load_time,
            "js_heavy": self.js_heavy,
            "mobile_responsive": self.mobile_responsive,
            "anti_detection": {
                "captcha_detected": self.anti_detection.captcha_detected,
                "rate_limiting": self.anti_detection.rate_limiting,
                "js_protection": self.anti_detection.js_protection,
                "cloudflare_detected": self.anti_detection.cloudflare_detected,
                "bot_detection_signals": self.anti_detection.bot_detection_signals,
                "recommended_profile": self.anti_detection.recommended_profile
            },
            "requires_login": self.requires_login,
            "login_form_selector": self.login_form_selector,
            "language": self.language,
            "geo_restricted": self.geo_restricted
        }


class ReconnaissanceEngine:
    """
    Website reconnaissance and structure analysis engine
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = ComponentLogger("reconnaissance")
        
        # Filter detection patterns
        self.filter_patterns = {
            "dropdown": [
                "select", 
                "[role='combobox']",
                ".dropdown",
                ".select-box"
            ],
            "checkbox": [
                "input[type='checkbox']",
                "[role='checkbox']",
                ".checkbox"
            ],
            "radio": [
                "input[type='radio']",
                "[role='radio']",
                ".radio"
            ],
            "text_input": [
                "input[type='text']",
                "input[type='search']",
                ".search-input",
                ".filter-input"
            ],
            "slider": [
                "input[type='range']",
                "[role='slider']",
                ".slider",
                ".range-slider"
            ]
        }
        
        # Content pattern indicators
        self.content_indicators = [
            ".item", ".card", ".product", ".listing", ".entry",
            ".result", ".post", ".article", ".job", ".property",
            "[data-item]", "[data-product]", "[data-listing]"
        ]
        
        # Pagination patterns
        self.pagination_patterns = {
            "numbered": [
                ".pagination", ".page-numbers", ".pager",
                "[role='navigation'] a[href*='page']"
            ],
            "next_prev": [
                ".next", ".previous", ".prev",
                "a[href*='next']", "a[href*='prev']",
                "button:contains('Next')", "button:contains('Previous')"
            ],
            "infinite_scroll": [
                "[data-infinite-scroll]", ".infinite-scroll",
                ".load-more-trigger"
            ],
            "load_more": [
                ".load-more", ".show-more", 
                "button:contains('Load')", "button:contains('Show more')"
            ]
        }
    
    @measure_time
    async def analyze_site(self, url: str) -> SiteMetadata:
        """
        Perform comprehensive site reconnaissance
        
        Args:
            url: URL to analyze
            
        Returns:
            SiteMetadata with complete analysis
        """
        self.logger.info("Starting site reconnaissance", url=url)
        
        metadata = SiteMetadata(url=url)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.settings.scraping.headless
            )
            
            try:
                context = await self._create_stealth_context(browser)
                page = await context.new_page()
                
                # Load the page and measure performance
                await self._load_page_with_timing(page, url, metadata)
                
                # Basic metadata extraction
                await self._extract_basic_metadata(page, metadata)
                
                # Structure analysis
                await self._analyze_filters(page, metadata)
                await self._analyze_pagination(page, metadata)
                await self._analyze_content_patterns(page, metadata)
                
                # Technical analysis
                await self._analyze_performance(page, metadata)
                await self._analyze_mobile_responsiveness(page, metadata)
                
                # Security analysis
                await self._analyze_anti_detection(page, metadata)
                
                # Authentication analysis
                await self._analyze_authentication(page, metadata)
                
                self.logger.info("Site reconnaissance completed", 
                               url=url,
                               filters_found=len(metadata.filters),
                               patterns_found=len(metadata.content_patterns),
                               load_time=metadata.load_time)
                
            finally:
                await browser.close()
        
        return metadata
    
    async def _create_stealth_context(self, browser: Browser) -> BrowserContext:
        """Create a browser context with stealth configuration"""
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Add stealth scripts
        await context.add_init_script("""
            // Hide webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
        return context
    
    async def _load_page_with_timing(self, page: Page, url: str, metadata: SiteMetadata):
        """Load page and measure timing metrics"""
        import time
        start_time = time.time()
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            metadata.load_time = time.time() - start_time
            
            # Wait for any dynamic content
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            self.logger.warning("Page load issues", url=url, error=str(e))
            metadata.load_time = time.time() - start_time
    
    async def _extract_basic_metadata(self, page: Page, metadata: SiteMetadata):
        """Extract basic page metadata"""
        try:
            metadata.title = await page.title()
            
            # Try to get description from meta tag
            desc_element = await page.query_selector('meta[name="description"]')
            if desc_element:
                metadata.description = await desc_element.get_attribute('content') or ""
            
            # Detect language
            lang_element = await page.query_selector('html[lang]')
            if lang_element:
                metadata.language = await lang_element.get_attribute('lang') or "en"
                
        except Exception as e:
            self.logger.warning("Failed to extract basic metadata", error=str(e))
    
    async def _analyze_filters(self, page: Page, metadata: SiteMetadata):
        """Analyze filter systems on the page"""
        self.logger.info("Analyzing filters")
        
        for filter_type, selectors in self.filter_patterns.items():
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        filter_info = await self._extract_filter_info(element, filter_type)
                        if filter_info:
                            metadata.filters.append(filter_info)
                            
                except Exception as e:
                    self.logger.debug("Filter analysis error", 
                                    filter_type=filter_type, 
                                    selector=selector, 
                                    error=str(e))
        
        self.logger.info("Filter analysis completed", count=len(metadata.filters))
    
    async def _extract_filter_info(self, element, filter_type: str) -> Optional[FilterInfo]:
        """Extract information about a specific filter element"""
        try:
            # Get selector for the element
            selector = await self._generate_selector(element)
            
            # Get label
            label = await self._find_filter_label(element)
            
            # Get options for select/checkbox/radio
            options = []
            if filter_type in ['dropdown', 'checkbox', 'radio']:
                options = await self._extract_filter_options(element, filter_type)
            
            # Get default value
            default_value = None
            if filter_type == 'dropdown':
                default_value = await element.input_value() if await element.input_value() else None
            elif filter_type in ['checkbox', 'radio']:
                is_checked = await element.is_checked()
                if is_checked:
                    default_value = await element.get_attribute('value')
            
            return FilterInfo(
                type=filter_type,
                selector=selector,
                label=label,
                options=options,
                default_value=default_value,
                required=await self._is_filter_required(element)
            )
            
        except Exception as e:
            self.logger.debug("Failed to extract filter info", error=str(e))
            return None
    
    async def _find_filter_label(self, element) -> str:
        """Find the label associated with a filter element"""
        try:
            # Try direct label association
            label_id = await element.get_attribute('id')
            if label_id:
                label_element = await element.page.query_selector(f'label[for="{label_id}"]')
                if label_element:
                    return await label_element.text_content() or ""
            
            # Try parent/sibling label
            parent = await element.query_selector('xpath=..')
            if parent:
                label_element = await parent.query_selector('label')
                if label_element:
                    return await label_element.text_content() or ""
            
            # Try placeholder or aria-label
            placeholder = await element.get_attribute('placeholder')
            if placeholder:
                return placeholder
            
            aria_label = await element.get_attribute('aria-label')
            if aria_label:
                return aria_label
            
            return "Unknown Filter"
            
        except:
            return "Unknown Filter"
    
    async def _extract_filter_options(self, element, filter_type: str) -> List[str]:
        """Extract options from select/checkbox/radio elements"""
        options = []
        
        try:
            if filter_type == 'dropdown':
                option_elements = await element.query_selector_all('option')
                for option in option_elements:
                    text = await option.text_content()
                    if text and text.strip():
                        options.append(text.strip())
            
            elif filter_type in ['checkbox', 'radio']:
                # For checkbox/radio groups, find siblings with same name
                name = await element.get_attribute('name')
                if name:
                    group_elements = await element.page.query_selector_all(f'input[name="{name}"]')
                    for group_element in group_elements:
                        value = await group_element.get_attribute('value')
                        if value:
                            options.append(value)
        
        except Exception as e:
            self.logger.debug("Failed to extract filter options", error=str(e))
        
        return options
    
    async def _is_filter_required(self, element) -> bool:
        """Check if filter is required"""
        try:
            required = await element.get_attribute('required')
            return required is not None
        except:
            return False
    
    async def _analyze_pagination(self, page: Page, metadata: SiteMetadata):
        """Analyze pagination mechanisms"""
        self.logger.info("Analyzing pagination")
        
        for pagination_type, selectors in self.pagination_patterns.items():
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        pagination_info = await self._extract_pagination_info(page, pagination_type, selector)
                        if pagination_info:
                            metadata.pagination = pagination_info
                            self.logger.info("Pagination detected", type=pagination_type)
                            return
                            
                except Exception as e:
                    self.logger.debug("Pagination analysis error", 
                                    type=pagination_type, 
                                    selector=selector, 
                                    error=str(e))
    
    async def _extract_pagination_info(self, page: Page, pagination_type: str, base_selector: str) -> Optional[PaginationInfo]:
        """Extract detailed pagination information"""
        try:
            selectors = {}
            
            if pagination_type == "numbered":
                selectors = {
                    "container": base_selector,
                    "page_links": f"{base_selector} a",
                    "current_page": f"{base_selector} .current, {base_selector} .active",
                    "next": f"{base_selector} .next, {base_selector} a:contains('Next')",
                    "previous": f"{base_selector} .prev, {base_selector} a:contains('Prev')"
                }
                
                # Try to estimate total pages
                page_links = await page.query_selector_all(selectors["page_links"])
                page_numbers = []
                for link in page_links:
                    text = await link.text_content()
                    if text and text.strip().isdigit():
                        page_numbers.append(int(text.strip()))
                
                total_pages = max(page_numbers) if page_numbers else None
                
            elif pagination_type == "next_prev":
                selectors = {
                    "next": base_selector,
                    "previous": "a:contains('Previous'), a:contains('Prev'), .prev"
                }
                
            elif pagination_type in ["infinite_scroll", "load_more"]:
                selectors = {
                    "trigger": base_selector
                }
            
            # Estimate items per page by counting current items
            items_per_page = await self._count_current_page_items(page)
            
            return PaginationInfo(
                type=pagination_type,
                selectors=selectors,
                items_per_page=items_per_page
            )
            
        except Exception as e:
            self.logger.debug("Failed to extract pagination info", error=str(e))
            return None
    
    async def _count_current_page_items(self, page: Page) -> Optional[int]:
        """Count items on current page"""
        try:
            # Try common item selectors
            for selector in self.content_indicators:
                elements = await page.query_selector_all(selector)
                if len(elements) > 5:  # Reasonable number of items
                    return len(elements)
            
            return None
            
        except:
            return None
    
    async def _analyze_content_patterns(self, page: Page, metadata: SiteMetadata):
        """Analyze repeating content patterns"""
        self.logger.info("Analyzing content patterns")
        
        for container_selector in self.content_indicators:
            try:
                containers = await page.query_selector_all(container_selector)
                
                if len(containers) >= 3:  # Need multiple items to establish pattern
                    pattern = await self._extract_content_pattern(page, container_selector, containers)
                    if pattern and pattern.confidence_score > 0.5:
                        metadata.content_patterns.append(pattern)
                        
            except Exception as e:
                self.logger.debug("Content pattern analysis error", 
                                selector=container_selector, 
                                error=str(e))
        
        # Sort patterns by confidence score
        metadata.content_patterns.sort(key=lambda p: p.confidence_score, reverse=True)
        
        self.logger.info("Content pattern analysis completed", 
                        patterns_found=len(metadata.content_patterns))
    
    async def _extract_content_pattern(self, page: Page, container_selector: str, containers) -> Optional[ContentPattern]:
        """Extract content pattern from multiple containers"""
        try:
            # Analyze structure of first few containers
            sample_containers = containers[:5]
            field_candidates = {}
            
            for container in sample_containers:
                # Find common child elements
                children = await container.query_selector_all('*')
                
                for child in children:
                    tag_name = await child.evaluate('el => el.tagName.toLowerCase()')
                    class_name = await child.get_attribute('class') or ""
                    text_content = await child.text_content()
                    
                    if text_content and len(text_content.strip()) > 0:
                        # Generate potential field name based on content/class
                        field_name = await self._guess_field_name(tag_name, class_name, text_content)
                        
                        if field_name not in field_candidates:
                            field_candidates[field_name] = []
                        
                        selector = await self._generate_relative_selector(child, container)
                        field_candidates[field_name].append({
                            'selector': selector,
                            'sample_content': text_content.strip()[:100]
                        })
            
            # Build field selectors from most common patterns
            field_selectors = {}
            sample_data = []
            
            for field_name, candidates in field_candidates.items():
                if len(candidates) >= len(sample_containers) * 0.6:  # Present in 60%+ of samples
                    # Use most common selector
                    selector_counts = {}
                    for candidate in candidates:
                        selector = candidate['selector']
                        selector_counts[selector] = selector_counts.get(selector, 0) + 1
                    
                    best_selector = max(selector_counts, key=selector_counts.get)
                    field_selectors[field_name] = best_selector
            
            # Extract sample data
            for i, container in enumerate(sample_containers[:3]):
                sample_item = {}
                for field_name, selector in field_selectors.items():
                    try:
                        element = await container.query_selector(selector)
                        if element:
                            content = await element.text_content()
                            if content:
                                sample_item[field_name] = content.strip()
                    except:
                        pass
                
                if sample_item:
                    sample_data.append(sample_item)
            
            # Calculate confidence score
            confidence_score = len(field_selectors) * 0.2  # Base score
            if len(sample_data) >= 3:
                confidence_score += 0.3
            if len(field_selectors) >= 3:
                confidence_score += 0.3
            
            return ContentPattern(
                container_selector=container_selector,
                item_selector=container_selector,
                field_selectors=field_selectors,
                confidence_score=min(confidence_score, 1.0),
                sample_data=sample_data
            )
            
        except Exception as e:
            self.logger.debug("Failed to extract content pattern", error=str(e))
            return None
    
    async def _guess_field_name(self, tag_name: str, class_name: str, text_content: str) -> str:
        """Guess field name based on element properties"""
        # Common field indicators
        field_indicators = {
            'title': ['title', 'name', 'heading', 'h1', 'h2', 'h3'],
            'price': ['price', 'cost', 'amount', '$', 'dollar'],
            'description': ['description', 'desc', 'summary', 'content'],
            'date': ['date', 'time', 'posted', 'published'],
            'location': ['location', 'address', 'city', 'place'],
            'rating': ['rating', 'star', 'score', 'review'],
            'image': ['img', 'image', 'photo', 'picture'],
            'link': ['link', 'url', 'href']
        }
        
        # Check class names and content
        combined_text = f"{class_name} {text_content[:50]}".lower()
        
        for field_name, indicators in field_indicators.items():
            if any(indicator in combined_text for indicator in indicators):
                return field_name
        
        # Fallback to tag name or generic
        if tag_name in ['h1', 'h2', 'h3']:
            return 'title'
        elif tag_name == 'img':
            return 'image'
        elif tag_name == 'a':
            return 'link'
        else:
            return f'field_{tag_name}'
    
    async def _generate_selector(self, element) -> str:
        """Generate CSS selector for element"""
        try:
            # Try ID first
            element_id = await element.get_attribute('id')
            if element_id:
                return f"#{element_id}"
            
            # Try class combination
            class_name = await element.get_attribute('class')
            if class_name:
                classes = class_name.strip().split()
                if classes:
                    return f".{'.'.join(classes[:2])}"  # Use first 2 classes
            
            # Fallback to tag name
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            return tag_name
            
        except:
            return "unknown"
    
    async def _generate_relative_selector(self, element, container) -> str:
        """Generate selector relative to container"""
        try:
            # Get element position relative to container
            element_tag = await element.evaluate('el => el.tagName.toLowerCase()')
            element_class = await element.get_attribute('class') or ""
            
            if element_class:
                classes = element_class.strip().split()[:2]  # First 2 classes
                return f"{element_tag}.{'.'.join(classes)}"
            else:
                return element_tag
                
        except:
            return "unknown"
    
    async def _analyze_performance(self, page: Page, metadata: SiteMetadata):
        """Analyze page performance characteristics"""
        try:
            # Check for heavy JavaScript usage
            script_elements = await page.query_selector_all('script')
            external_scripts = 0
            
            for script in script_elements:
                src = await script.get_attribute('src')
                if src:
                    external_scripts += 1
            
            metadata.js_heavy = external_scripts > 5 or metadata.load_time > 5
            
            self.logger.info("Performance analysis completed", 
                           load_time=metadata.load_time,
                           js_heavy=metadata.js_heavy,
                           external_scripts=external_scripts)
            
        except Exception as e:
            self.logger.warning("Performance analysis failed", error=str(e))
    
    async def _analyze_mobile_responsiveness(self, page: Page, metadata: SiteMetadata):
        """Check mobile responsiveness"""
        try:
            # Set mobile viewport
            await page.set_viewport_size({"width": 375, "height": 667})
            await page.wait_for_timeout(1000)
            
            # Check if layout adapts
            body_width = await page.evaluate('document.body.scrollWidth')
            viewport_width = await page.evaluate('window.innerWidth')
            
            metadata.mobile_responsive = body_width <= viewport_width * 1.1
            
            # Reset to desktop viewport
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            self.logger.info("Mobile responsiveness analysis completed", 
                           responsive=metadata.mobile_responsive)
            
        except Exception as e:
            self.logger.warning("Mobile analysis failed", error=str(e))
            metadata.mobile_responsive = True  # Assume responsive on error
    
    async def _analyze_anti_detection(self, page: Page, metadata: SiteMetadata):
        """Analyze anti-bot measures"""
        try:
            anti_detection = AntiDetectionInfo()
            
            # Check for common anti-bot indicators
            page_content = await page.content()
            
            # CAPTCHA detection
            captcha_indicators = [
                'recaptcha', 'captcha', 'cloudflare', 'hcaptcha',
                'challenge', 'verify', 'robot'
            ]
            
            for indicator in captcha_indicators:
                if indicator.lower() in page_content.lower():
                    anti_detection.captcha_detected = True
                    anti_detection.bot_detection_signals.append(f"CAPTCHA indicator: {indicator}")
                    break
            
            # Cloudflare detection
            if 'cloudflare' in page_content.lower() or 'cf-ray' in page_content.lower():
                anti_detection.cloudflare_detected = True
                anti_detection.bot_detection_signals.append("Cloudflare protection detected")
            
            # JavaScript protection
            noscript_elements = await page.query_selector_all('noscript')
            if len(noscript_elements) > 2:
                anti_detection.js_protection = True
                anti_detection.bot_detection_signals.append("Heavy JavaScript dependency")
            
            # Rate limiting indicators
            rate_limit_indicators = ['rate limit', 'too many requests', '429', 'slow down']
            for indicator in rate_limit_indicators:
                if indicator.lower() in page_content.lower():
                    anti_detection.rate_limiting = True
                    anti_detection.bot_detection_signals.append(f"Rate limiting: {indicator}")
                    break
            
            # Recommend profile based on detection level
            if anti_detection.captcha_detected or anti_detection.cloudflare_detected:
                anti_detection.recommended_profile = "stealth"
            elif len(anti_detection.bot_detection_signals) > 2:
                anti_detection.recommended_profile = "conservative"
            elif anti_detection.js_protection or anti_detection.rate_limiting:
                anti_detection.recommended_profile = "balanced"
            else:
                anti_detection.recommended_profile = "balanced"
            
            metadata.anti_detection = anti_detection
            
            self.logger.info("Anti-detection analysis completed",
                           signals_detected=len(anti_detection.bot_detection_signals),
                           recommended_profile=anti_detection.recommended_profile)
            
        except Exception as e:
            self.logger.warning("Anti-detection analysis failed", error=str(e))
    
    async def _analyze_authentication(self, page: Page, metadata: SiteMetadata):
        """Analyze authentication requirements"""
        try:
            # Look for login forms
            login_selectors = [
                'form[action*="login"]',
                'form[action*="signin"]', 
                'form[action*="auth"]',
                '.login-form',
                '.signin-form',
                '#login',
                '#signin'
            ]
            
            for selector in login_selectors:
                element = await page.query_selector(selector)
                if element:
                    metadata.requires_login = True
                    metadata.login_form_selector = selector
                    break
            
            # Check for login-only content indicators
            login_indicators = [
                'please login', 'sign in required', 'members only',
                'login to view', 'authentication required'
            ]
            
            page_text = await page.text_content('body')
            if page_text:
                for indicator in login_indicators:
                    if indicator.lower() in page_text.lower():
                        metadata.requires_login = True
                        break
            
            self.logger.info("Authentication analysis completed",
                           requires_login=metadata.requires_login,
                           login_form_found=metadata.login_form_selector is not None)
            
        except Exception as e:
            self.logger.warning("Authentication analysis failed", error=str(e))