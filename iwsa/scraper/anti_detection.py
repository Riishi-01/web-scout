"""
Anti-detection mechanisms for web scraping
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from playwright.async_api import Page

from ..config import Settings
from ..utils.logger import ComponentLogger
from ..utils.helpers import RateLimiter


@dataclass
class ProxyConfig:
    """Proxy configuration"""
    server: str
    username: Optional[str] = None
    password: Optional[str] = None
    type: str = "http"  # http, https, socks4, socks5
    
    def to_playwright_proxy(self) -> Dict[str, str]:
        """Convert to Playwright proxy format"""
        proxy = {"server": self.server}
        if self.username and self.password:
            proxy["username"] = self.username
            proxy["password"] = self.password
        return proxy


@dataclass
class BehavioralPattern:
    """Behavioral patterns for human-like interaction"""
    mouse_movements: bool = True
    scroll_simulation: bool = True
    typing_delays: bool = True
    random_pauses: bool = True
    page_view_time: Tuple[int, int] = (5, 15)  # seconds
    click_delay: Tuple[float, float] = (0.1, 0.5)  # seconds
    scroll_delay: Tuple[float, float] = (0.5, 2.0)  # seconds


class AntiDetectionManager:
    """
    Manages anti-detection mechanisms including proxies, behavioral patterns, and fingerprint randomization
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = ComponentLogger("anti_detection")
        
        # Rate limiters for different domains
        self.domain_rate_limiters: Dict[str, RateLimiter] = {}
        
        # Proxy rotation
        self.proxy_pool: List[ProxyConfig] = []
        self.current_proxy_index = 0
        
        # Request tracking for pattern analysis
        self.request_history: Dict[str, List[float]] = {}
        
        # Behavioral patterns
        self.behavioral_patterns = {
            "conservative": BehavioralPattern(
                mouse_movements=True,
                scroll_simulation=True,
                typing_delays=True,
                random_pauses=True,
                page_view_time=(10, 30),
                click_delay=(0.2, 0.8),
                scroll_delay=(1.0, 3.0)
            ),
            "balanced": BehavioralPattern(
                mouse_movements=False,
                scroll_simulation=True,
                typing_delays=False,
                random_pauses=True,
                page_view_time=(5, 15),
                click_delay=(0.1, 0.5),
                scroll_delay=(0.5, 2.0)
            ),
            "aggressive": BehavioralPattern(
                mouse_movements=False,
                scroll_simulation=False,
                typing_delays=False,
                random_pauses=False,
                page_view_time=(1, 3),
                click_delay=(0.05, 0.2),
                scroll_delay=(0.1, 0.5)
            )
        }
        
        self.logger.info("Anti-detection manager initialized")
    
    def add_proxy(self, proxy_config: ProxyConfig):
        """Add proxy to rotation pool"""
        self.proxy_pool.append(proxy_config)
        self.logger.info("Proxy added to pool", server=proxy_config.server, total_proxies=len(self.proxy_pool))
    
    def get_next_proxy(self) -> Optional[ProxyConfig]:
        """Get next proxy in rotation"""
        if not self.proxy_pool:
            return None
        
        proxy = self.proxy_pool[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_pool)
        
        return proxy
    
    async def apply_rate_limiting(self, domain: str, profile: str = "balanced"):
        """Apply intelligent rate limiting for domain"""
        if domain not in self.domain_rate_limiters:
            # Create rate limiter based on profile
            rate_limits = {
                "conservative": 0.2,  # 1 request per 5 seconds
                "balanced": 0.5,      # 1 request per 2 seconds
                "aggressive": 1.0     # 1 request per second
            }
            
            rate = rate_limits.get(profile, 0.5)
            self.domain_rate_limiters[domain] = RateLimiter(calls_per_second=rate)
        
        # Apply rate limiting
        await self.domain_rate_limiters[domain].acquire()
        
        # Track request timing
        current_time = time.time()
        if domain not in self.request_history:
            self.request_history[domain] = []
        
        self.request_history[domain].append(current_time)
        
        # Keep only recent history (last hour)
        cutoff_time = current_time - 3600
        self.request_history[domain] = [
            timestamp for timestamp in self.request_history[domain] 
            if timestamp > cutoff_time
        ]
    
    async def simulate_human_behavior(self, page: Page, pattern: str = "balanced"):
        """Simulate human-like behavior on page"""
        behavior = self.behavioral_patterns.get(pattern, self.behavioral_patterns["balanced"])
        
        if behavior.mouse_movements:
            await self._simulate_mouse_movements(page)
        
        if behavior.scroll_simulation:
            await self._simulate_scrolling(page, behavior)
        
        if behavior.random_pauses:
            await self._random_pause(behavior.page_view_time)
    
    async def _simulate_mouse_movements(self, page: Page):
        """Simulate random mouse movements"""
        try:
            viewport = page.viewport_size
            if not viewport:
                return
            
            # Generate random mouse path
            num_movements = random.randint(3, 8)
            
            for _ in range(num_movements):
                x = random.randint(0, viewport["width"])
                y = random.randint(0, viewport["height"])
                
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
        except Exception as e:
            self.logger.debug("Mouse simulation failed", error=str(e))
    
    async def _simulate_scrolling(self, page: Page, behavior: BehavioralPattern):
        """Simulate human-like scrolling"""
        try:
            # Get page height
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")
            
            if page_height <= viewport_height:
                return  # No need to scroll
            
            # Scroll in random increments
            scroll_positions = []
            current_position = 0
            
            while current_position < page_height:
                scroll_amount = random.randint(200, 600)
                current_position += scroll_amount
                scroll_positions.append(min(current_position, page_height))
            
            # Execute scrolling
            for position in scroll_positions:
                await page.evaluate(f"window.scrollTo(0, {position})")
                delay = random.uniform(*behavior.scroll_delay)
                await asyncio.sleep(delay)
            
            # Scroll back to top occasionally
            if random.random() < 0.3:
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
        except Exception as e:
            self.logger.debug("Scroll simulation failed", error=str(e))
    
    async def _random_pause(self, time_range: Tuple[int, int]):
        """Random pause to simulate reading time"""
        pause_time = random.uniform(*time_range)
        await asyncio.sleep(pause_time)
    
    async def human_like_click(self, page: Page, selector: str, behavior: str = "balanced"):
        """Perform human-like click with delays and movements"""
        pattern = self.behavioral_patterns.get(behavior, self.behavioral_patterns["balanced"])
        
        try:
            # Wait for element
            element = await page.wait_for_selector(selector, timeout=10000)
            if not element:
                raise Exception(f"Element not found: {selector}")
            
            # Get element position
            box = await element.bounding_box()
            if not box:
                raise Exception(f"Element not visible: {selector}")
            
            # Calculate click position with slight randomization
            x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
            y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
            
            # Move mouse to element
            await page.mouse.move(x, y)
            
            # Small delay before clicking
            click_delay = random.uniform(*pattern.click_delay)
            await asyncio.sleep(click_delay)
            
            # Perform click
            await page.mouse.click(x, y)
            
            self.logger.debug("Human-like click performed", selector=selector)
            
        except Exception as e:
            self.logger.warning("Human-like click failed", selector=selector, error=str(e))
            # Fallback to regular click
            await page.click(selector)
    
    async def human_like_type(self, page: Page, selector: str, text: str, behavior: str = "balanced"):
        """Type text with human-like delays"""
        pattern = self.behavioral_patterns.get(behavior, self.behavioral_patterns["balanced"])
        
        try:
            await page.click(selector)
            await page.fill(selector, "")  # Clear existing text
            
            if pattern.typing_delays:
                # Type character by character with delays
                for char in text:
                    await page.type(selector, char, delay=random.uniform(50, 150))
            else:
                await page.type(selector, text, delay=0)
            
            self.logger.debug("Human-like typing completed", selector=selector, text_length=len(text))
            
        except Exception as e:
            self.logger.warning("Human-like typing failed", selector=selector, error=str(e))
            # Fallback to regular fill
            await page.fill(selector, text)
    
    async def wait_for_page_load(self, page: Page, timeout: int = 30):
        """Wait for page to fully load with anti-detection considerations"""
        try:
            # Wait for basic load
            await page.wait_for_load_state("networkidle", timeout=timeout * 1000)
            
            # Additional wait for dynamic content
            await asyncio.sleep(random.uniform(1, 3))
            
            # Check for common loading indicators
            loading_selectors = [
                ".loading", ".spinner", ".loader", 
                "[data-loading]", ".fa-spinner"
            ]
            
            for selector in loading_selectors:
                try:
                    loader = await page.query_selector(selector)
                    if loader:
                        await page.wait_for_selector(selector, state="detached", timeout=10000)
                except:
                    continue
            
        except Exception as e:
            self.logger.debug("Page load wait completed with timeout", error=str(e))
    
    async def handle_captcha_detection(self, page: Page) -> bool:
        """Detect and handle CAPTCHA challenges"""
        captcha_indicators = [
            "captcha", "recaptcha", "hcaptcha", "cloudflare",
            "challenge", "verify", "robot", "human"
        ]
        
        try:
            page_content = await page.content()
            page_text = page_content.lower()
            
            # Check for CAPTCHA indicators
            for indicator in captcha_indicators:
                if indicator in page_text:
                    self.logger.warning("CAPTCHA detected", indicator=indicator)
                    
                    # Basic CAPTCHA handling strategies
                    if "cloudflare" in page_text:
                        # Wait for Cloudflare challenge to complete
                        await asyncio.sleep(5)
                        try:
                            await page.wait_for_url(lambda url: "challenge" not in url.lower(), timeout=30000)
                            return True
                        except:
                            return False
                    
                    # For other CAPTCHAs, just wait and hope
                    await asyncio.sleep(10)
                    return False
            
            return True  # No CAPTCHA detected
            
        except Exception as e:
            self.logger.warning("CAPTCHA detection failed", error=str(e))
            return True  # Assume no CAPTCHA on error
    
    async def randomize_request_timing(self, base_delay: float, variance: float = 0.5) -> float:
        """Apply randomized timing to requests"""
        # Add random variance to base delay
        min_delay = base_delay * (1 - variance)
        max_delay = base_delay * (1 + variance)
        
        actual_delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(actual_delay)
        
        return actual_delay
    
    def analyze_request_patterns(self, domain: str) -> Dict[str, Any]:
        """Analyze request patterns for a domain"""
        if domain not in self.request_history:
            return {"status": "no_data"}
        
        history = self.request_history[domain]
        if len(history) < 2:
            return {"status": "insufficient_data"}
        
        # Calculate request intervals
        intervals = []
        for i in range(1, len(history)):
            interval = history[i] - history[i-1]
            intervals.append(interval)
        
        # Statistical analysis
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)
        
        # Detect suspicious patterns
        suspicious = False
        warnings = []
        
        if avg_interval < 1.0:  # Too fast
            suspicious = True
            warnings.append("Average request interval too low")
        
        if min_interval < 0.5:  # Individual requests too fast
            suspicious = True
            warnings.append("Some requests too fast")
        
        # Check for too regular patterns
        if len(set(intervals)) < len(intervals) * 0.3:  # Too regular
            suspicious = True
            warnings.append("Request timing too regular")
        
        return {
            "status": "analyzed",
            "total_requests": len(history),
            "avg_interval": avg_interval,
            "min_interval": min_interval,
            "max_interval": max_interval,
            "suspicious": suspicious,
            "warnings": warnings,
            "recommendation": "slow_down" if suspicious else "continue"
        }
    
    def adjust_rate_limiting(self, domain: str, adjustment_factor: float):
        """Dynamically adjust rate limiting based on response patterns"""
        if domain in self.domain_rate_limiters:
            current_rate = self.domain_rate_limiters[domain].min_interval
            new_rate = current_rate * adjustment_factor
            
            # Set reasonable bounds
            new_rate = max(0.5, min(10.0, new_rate))  # Between 0.5s and 10s
            
            self.domain_rate_limiters[domain].set_rate(1.0 / new_rate)
            
            self.logger.info("Rate limiting adjusted", 
                           domain=domain,
                           old_interval=current_rate,
                           new_interval=new_rate,
                           factor=adjustment_factor)
    
    def get_detection_status(self) -> Dict[str, Any]:
        """Get current anti-detection status"""
        status = {
            "proxy_pool_size": len(self.proxy_pool),
            "current_proxy_index": self.current_proxy_index,
            "tracked_domains": len(self.domain_rate_limiters),
            "request_history": {}
        }
        
        # Analyze each tracked domain
        for domain in self.request_history:
            analysis = self.analyze_request_patterns(domain)
            status["request_history"][domain] = analysis
        
        return status