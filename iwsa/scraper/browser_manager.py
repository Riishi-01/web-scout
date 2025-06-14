"""
Browser instance management with resource optimization and anti-detection
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from fake_useragent import UserAgent

from ..config import Settings
from ..utils.logger import ComponentLogger
from ..utils.helpers import generate_id


@dataclass
class BrowserConfig:
    """Configuration for browser instances"""
    headless: bool = True
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    user_agent: str = ""
    locale: str = "en-US"
    timezone: str = "America/New_York"
    extra_headers: Dict[str, str] = field(default_factory=dict)
    proxy: Optional[str] = None
    
    def to_playwright_args(self) -> Dict[str, Any]:
        """Convert to Playwright launch arguments"""
        args = {
            "headless": self.headless,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows"
            ]
        }
        
        if self.proxy:
            args["proxy"] = {"server": self.proxy}
        
        return args


@dataclass
class BrowserInstance:
    """Managed browser instance"""
    id: str
    browser: Browser
    context: BrowserContext
    page: Page
    config: BrowserConfig
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    requests_count: int = 0
    in_use: bool = False
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception:
            pass  # Ignore cleanup errors


class BrowserManager:
    """
    Manages browser instances with pooling, rotation, and anti-detection
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = ComponentLogger("browser_manager")
        
        # Browser pool
        self.browser_pool: Dict[str, BrowserInstance] = {}
        self.max_instances = settings.scraping.max_concurrent_browsers
        self.max_requests_per_instance = 100  # Rotate after 100 requests
        self.max_instance_age = 3600  # 1 hour max age
        
        # User agent rotation
        self.ua_generator = UserAgent()
        self.user_agents = self._generate_user_agent_pool()
        
        # Playwright instance
        self.playwright: Optional[Playwright] = None
        
        # Instance rotation settings
        self.rotation_enabled = settings.scraping.user_agent_rotation
        self.fingerprint_randomization = settings.scraping.fingerprint_randomization
        
        self.logger.info("Browser manager initialized",
                        max_instances=self.max_instances,
                        rotation_enabled=self.rotation_enabled)
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup_all()
        if self.playwright:
            await self.playwright.stop()
    
    def _generate_user_agent_pool(self) -> List[str]:
        """Generate a pool of diverse user agents"""
        user_agents = []
        
        # Modern Chrome versions
        chrome_versions = [
            "120.0.0.0", "119.0.0.0", "118.0.0.0", "117.0.0.0"
        ]
        
        platforms = [
            "Windows NT 10.0; Win64; x64",
            "Macintosh; Intel Mac OS X 10_15_7",
            "X11; Linux x86_64"
        ]
        
        for version in chrome_versions:
            for platform in platforms:
                ua = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
                user_agents.append(ua)
        
        # Add some Firefox user agents
        firefox_versions = ["120.0", "119.0", "118.0"]
        for version in firefox_versions:
            for platform in platforms:
                if "Windows" in platform:
                    ua = f"Mozilla/5.0 ({platform}; rv:{version}) Gecko/20100101 Firefox/{version}"
                    user_agents.append(ua)
        
        return user_agents
    
    async def get_browser_instance(self, 
                                  config: Optional[BrowserConfig] = None,
                                  force_new: bool = False) -> BrowserInstance:
        """
        Get or create a browser instance
        
        Args:
            config: Browser configuration
            force_new: Force creation of new instance
            
        Returns:
            BrowserInstance
        """
        if config is None:
            config = self._create_default_config()
        
        # Clean up old instances first
        await self._cleanup_old_instances()
        
        # Try to reuse existing instance if not forcing new
        if not force_new:
            available_instance = self._find_available_instance(config)
            if available_instance:
                available_instance.in_use = True
                available_instance.last_used = time.time()
                self.logger.debug("Reusing browser instance", instance_id=available_instance.id)
                return available_instance
        
        # Create new instance if we haven't hit the limit
        if len(self.browser_pool) < self.max_instances:
            return await self._create_new_instance(config)
        
        # Wait for an instance to become available
        self.logger.info("Browser pool full, waiting for available instance")
        for _ in range(30):  # Wait up to 30 seconds
            await asyncio.sleep(1)
            available_instance = self._find_available_instance(config)
            if available_instance:
                available_instance.in_use = True
                available_instance.last_used = time.time()
                return available_instance
        
        # Force create new instance by cleaning up least recently used
        await self._cleanup_lru_instance()
        return await self._create_new_instance(config)
    
    def _create_default_config(self) -> BrowserConfig:
        """Create default browser configuration"""
        config = BrowserConfig(
            headless=self.settings.scraping.headless,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone="America/New_York"
        )
        
        # Randomize user agent if rotation enabled
        if self.rotation_enabled:
            config.user_agent = random.choice(self.user_agents)
        else:
            config.user_agent = self.user_agents[0]  # Use first stable UA
        
        # Add randomized headers if fingerprint randomization enabled
        if self.fingerprint_randomization:
            config.extra_headers = self._generate_random_headers()
        
        return config
    
    def _generate_random_headers(self) -> Dict[str, str]:
        """Generate randomized headers for anti-detection"""
        headers = {
            "Accept": random.choice([
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            ]),
            "Accept-Language": random.choice([
                "en-US,en;q=0.9",
                "en-US,en;q=0.8",
                "en-US,en;q=0.7"
            ]),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
        
        # Randomly include/exclude some headers
        if random.random() < 0.7:
            headers["DNT"] = "1"
        
        if random.random() < 0.5:
            headers["Cache-Control"] = random.choice(["no-cache", "max-age=0"])
        
        return headers
    
    def _find_available_instance(self, config: BrowserConfig) -> Optional[BrowserInstance]:
        """Find an available browser instance that matches config"""
        for instance in self.browser_pool.values():
            if (not instance.in_use and 
                instance.requests_count < self.max_requests_per_instance and
                time.time() - instance.created_at < self.max_instance_age):
                return instance
        return None
    
    async def _create_new_instance(self, config: BrowserConfig) -> BrowserInstance:
        """Create a new browser instance"""
        instance_id = generate_id("browser")
        
        self.logger.info("Creating new browser instance", instance_id=instance_id)
        
        try:
            # Launch browser
            browser_args = config.to_playwright_args()
            browser = await self.playwright.chromium.launch(**browser_args)
            
            # Create context with stealth configuration
            context_options = {
                "viewport": config.viewport,
                "user_agent": config.user_agent,
                "locale": config.locale,
                "timezone_id": config.timezone,
                "extra_http_headers": config.extra_headers,
                "java_script_enabled": True,
                "accept_downloads": False,
                "ignore_https_errors": True
            }
            
            context = await browser.new_context(**context_options)
            
            # Add stealth scripts
            await self._add_stealth_scripts(context)
            
            # Create page
            page = await context.new_page()
            
            # Additional page configuration
            await self._configure_page(page)
            
            # Create instance object
            instance = BrowserInstance(
                id=instance_id,
                browser=browser,
                context=context,
                page=page,
                config=config,
                in_use=True
            )
            
            self.browser_pool[instance_id] = instance
            
            self.logger.info("Browser instance created successfully", 
                           instance_id=instance_id,
                           total_instances=len(self.browser_pool))
            
            return instance
        
        except Exception as e:
            self.logger.error("Failed to create browser instance", 
                            instance_id=instance_id,
                            error=str(e))
            raise
    
    async def _add_stealth_scripts(self, context: BrowserContext):
        """Add stealth scripts to avoid detection"""
        stealth_script = """
        // Hide webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock languages and plugins
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Mock chrome runtime
        window.chrome = {
            runtime: {},
        };
        
        // Override toString methods
        Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
            get: function() {
                return window;
            }
        });
        
        // Randomize canvas fingerprinting
        const getContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type) {
            if (type === '2d') {
                const context = getContext.apply(this, arguments);
                const originalFillText = context.fillText;
                context.fillText = function(text, x, y, maxWidth) {
                    // Add small random noise
                    const noise = Math.random() * 0.01;
                    return originalFillText.apply(this, [text, x + noise, y + noise, maxWidth]);
                };
                return context;
            }
            return getContext.apply(this, arguments);
        };
        """
        
        await context.add_init_script(stealth_script)
    
    async def _configure_page(self, page: Page):
        """Configure page with additional anti-detection measures"""
        # Set extra HTTP headers
        await page.set_extra_http_headers({
            "sec-ch-ua": '"Google Chrome";v="120", "Chromium";v="120", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        })
        
        # Block unnecessary resources for performance
        await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", 
                        lambda route: route.abort())
        
        # Set realistic timeouts
        page.set_default_timeout(self.settings.scraping.default_timeout * 1000)
        page.set_default_navigation_timeout(self.settings.scraping.default_timeout * 1000)
    
    async def release_instance(self, instance: BrowserInstance):
        """Release browser instance back to pool"""
        if instance.id in self.browser_pool:
            instance.in_use = False
            instance.last_used = time.time()
            instance.requests_count += 1
            
            self.logger.debug("Released browser instance", 
                            instance_id=instance.id,
                            requests_count=instance.requests_count)
            
            # Clean up if instance has exceeded limits
            if (instance.requests_count >= self.max_requests_per_instance or
                time.time() - instance.created_at >= self.max_instance_age):
                await self._cleanup_instance(instance.id)
    
    async def _cleanup_old_instances(self):
        """Clean up old or overused instances"""
        current_time = time.time()
        to_cleanup = []
        
        for instance_id, instance in self.browser_pool.items():
            if (not instance.in_use and 
                (current_time - instance.created_at > self.max_instance_age or
                 instance.requests_count >= self.max_requests_per_instance)):
                to_cleanup.append(instance_id)
        
        for instance_id in to_cleanup:
            await self._cleanup_instance(instance_id)
    
    async def _cleanup_lru_instance(self):
        """Clean up least recently used instance"""
        if not self.browser_pool:
            return
        
        # Find LRU instance that's not in use
        lru_instance = None
        lru_time = float('inf')
        
        for instance in self.browser_pool.values():
            if not instance.in_use and instance.last_used < lru_time:
                lru_time = instance.last_used
                lru_instance = instance
        
        if lru_instance:
            await self._cleanup_instance(lru_instance.id)
    
    async def _cleanup_instance(self, instance_id: str):
        """Clean up a specific browser instance"""
        if instance_id in self.browser_pool:
            instance = self.browser_pool[instance_id]
            
            self.logger.info("Cleaning up browser instance", 
                           instance_id=instance_id,
                           requests_count=instance.requests_count,
                           age=time.time() - instance.created_at)
            
            await instance.cleanup()
            del self.browser_pool[instance_id]
    
    async def cleanup_all(self):
        """Clean up all browser instances"""
        self.logger.info("Cleaning up all browser instances", count=len(self.browser_pool))
        
        cleanup_tasks = []
        for instance in self.browser_pool.values():
            cleanup_tasks.append(instance.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self.browser_pool.clear()
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get browser pool status"""
        current_time = time.time()
        
        status = {
            "total_instances": len(self.browser_pool),
            "max_instances": self.max_instances,
            "in_use": sum(1 for instance in self.browser_pool.values() if instance.in_use),
            "available": sum(1 for instance in self.browser_pool.values() if not instance.in_use),
            "instances": []
        }
        
        for instance in self.browser_pool.values():
            instance_info = {
                "id": instance.id,
                "in_use": instance.in_use,
                "requests_count": instance.requests_count,
                "age_seconds": current_time - instance.created_at,
                "last_used_seconds_ago": current_time - instance.last_used
            }
            status["instances"].append(instance_info)
        
        return status