"""
Scraping profiles for different use cases and risk levels
"""

from typing import Dict, Any
from enum import Enum


class ProfileType(Enum):
    """Available scraping profile types"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"  
    AGGRESSIVE = "aggressive"
    STEALTH = "stealth"


class ScrapingProfiles:
    """Predefined scraping profiles for different scenarios"""
    
    PROFILES = {
        ProfileType.CONSERVATIVE.value: {
            "name": "Conservative",
            "description": "Slow and respectful scraping with maximum anti-detection",
            "rate_limit": 5.0,  # seconds between requests
            "retry_attempts": 5,
            "timeout": 60,
            "anti_detection": "high",
            "concurrent_browsers": 1,
            "proxy_rotation": True,
            "user_agent_rotation": True,
            "fingerprint_randomization": True,
            "request_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            "behavioral_patterns": {
                "mouse_movements": True,
                "scroll_simulation": True,
                "typing_delays": True,
                "random_pauses": True
            },
            "memory_optimization": "high",
            "error_threshold": 0.001,  # 0.1% error rate threshold
            "success_rate_target": 0.99
        },
        
        ProfileType.BALANCED.value: {
            "name": "Balanced",
            "description": "Moderate speed with good anti-detection measures",
            "rate_limit": 2.0,
            "retry_attempts": 3,
            "timeout": 30,
            "anti_detection": "medium",
            "concurrent_browsers": 2,
            "proxy_rotation": True,
            "user_agent_rotation": True,
            "fingerprint_randomization": True,
            "request_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            },
            "behavioral_patterns": {
                "mouse_movements": False,
                "scroll_simulation": True,
                "typing_delays": False,
                "random_pauses": True
            },
            "memory_optimization": "medium",
            "error_threshold": 0.005,  # 0.5% error rate threshold
            "success_rate_target": 0.95
        },
        
        ProfileType.AGGRESSIVE.value: {
            "name": "Aggressive",
            "description": "Fast scraping with minimal anti-detection",
            "rate_limit": 1.0,
            "retry_attempts": 2,
            "timeout": 15,
            "anti_detection": "low",
            "concurrent_browsers": 3,
            "proxy_rotation": False,
            "user_agent_rotation": False,
            "fingerprint_randomization": False,
            "request_headers": {
                "Accept": "*/*",
                "Connection": "keep-alive"
            },
            "behavioral_patterns": {
                "mouse_movements": False,
                "scroll_simulation": False,
                "typing_delays": False,
                "random_pauses": False
            },
            "memory_optimization": "low",
            "error_threshold": 0.02,  # 2% error rate threshold
            "success_rate_target": 0.90
        },
        
        ProfileType.STEALTH.value: {
            "name": "Stealth",
            "description": "Maximum stealth with residential proxies and advanced evasion",
            "rate_limit": 8.0,
            "retry_attempts": 7,
            "timeout": 90,
            "anti_detection": "maximum",
            "concurrent_browsers": 1,
            "proxy_rotation": True,
            "user_agent_rotation": True,
            "fingerprint_randomization": True,
            "residential_proxies": True,
            "request_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            },
            "behavioral_patterns": {
                "mouse_movements": True,
                "scroll_simulation": True,
                "typing_delays": True,
                "random_pauses": True,
                "page_view_time": (10, 30),  # Random page view time range
                "session_duration": (300, 1800)  # 5-30 minutes session duration
            },
            "memory_optimization": "maximum",
            "error_threshold": 0.0001,  # 0.01% error rate threshold
            "success_rate_target": 0.999,
            "captcha_solving": True,
            "js_execution": "full"
        }
    }
    
    @classmethod
    def get_profile(cls, profile_name: str) -> Dict[str, Any]:
        """Get a scraping profile by name"""
        if profile_name not in cls.PROFILES:
            available = list(cls.PROFILES.keys())
            raise ValueError(f"Profile '{profile_name}' not found. Available: {available}")
        
        return cls.PROFILES[profile_name].copy()
    
    @classmethod
    def get_all_profiles(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available profiles"""
        return cls.PROFILES.copy()
    
    @classmethod
    def create_custom_profile(cls, base_profile: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom profile based on an existing one with overrides"""
        if base_profile not in cls.PROFILES:
            raise ValueError(f"Base profile '{base_profile}' not found")
        
        profile = cls.get_profile(base_profile)
        
        # Apply overrides recursively
        def deep_update(base_dict: Dict, update_dict: Dict) -> Dict:
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    base_dict[key] = deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict
        
        return deep_update(profile, overrides)
    
    @classmethod
    def get_profile_for_site_type(cls, site_type: str) -> str:
        """Recommend a profile based on site type"""
        site_recommendations = {
            "e-commerce": ProfileType.BALANCED.value,
            "job_boards": ProfileType.CONSERVATIVE.value,
            "social_media": ProfileType.STEALTH.value,
            "news": ProfileType.BALANCED.value,
            "directories": ProfileType.AGGRESSIVE.value,
            "apis": ProfileType.AGGRESSIVE.value,
            "government": ProfileType.STEALTH.value,
            "financial": ProfileType.STEALTH.value,
            "academic": ProfileType.CONSERVATIVE.value,
            "real_estate": ProfileType.BALANCED.value
        }
        
        return site_recommendations.get(site_type.lower(), ProfileType.BALANCED.value)
    
    @classmethod 
    def validate_profile(cls, profile: Dict[str, Any]) -> bool:
        """Validate a profile configuration"""
        required_fields = [
            "rate_limit", "retry_attempts", "timeout", 
            "anti_detection", "concurrent_browsers"
        ]
        
        for field in required_fields:
            if field not in profile:
                return False
        
        # Validate value ranges
        if profile["rate_limit"] <= 0:
            return False
        if profile["retry_attempts"] < 1:
            return False
        if profile["timeout"] <= 0:
            return False
        if profile["concurrent_browsers"] < 1:
            return False
        
        return True