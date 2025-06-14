"""
Unit tests for configuration management
"""

import pytest
import os
from unittest.mock import patch

from iwsa.config import Settings, ScrapingProfiles
from iwsa.config.settings import LLMConfig, StorageConfig, ScrapingConfig


class TestSettings:
    """Test cases for Settings configuration"""
    
    def test_settings_initialization(self):
        """Test basic settings initialization"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key',
            'MONGODB_URI': 'mongodb://localhost:27017',
            'ENVIRONMENT': 'test'
        }):
            settings = Settings()
            
            assert settings.environment == 'test'
            assert settings.llm.openai_api_key == 'test_key'
            assert settings.storage.mongodb_uri == 'mongodb://localhost:27017'
    
    def test_llm_config(self):
        """Test LLM configuration"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123',
            'CLAUDE_API_KEY': 'claude-test456',
            'PRIMARY_LLM_PROVIDER': 'claude'
        }):
            config = LLMConfig()
            
            assert config.openai_api_key == 'sk-test123'
            assert config.claude_api_key == 'claude-test456'
            assert config.primary_provider == 'claude'
            assert config.timeout == 30
            assert config.rate_limiting == True
    
    def test_storage_config(self):
        """Test storage configuration"""
        with patch.dict(os.environ, {
            'MONGODB_URI': 'mongodb://test:27017',
            'MONGODB_DATABASE': 'test_db',
            'MONGODB_COLLECTION': 'test_collection'
        }):
            config = StorageConfig()
            
            assert config.mongodb_uri == 'mongodb://test:27017'
            assert config.database_name == 'test_db'
            assert config.collection_name == 'test_collection'
    
    def test_scraping_config(self):
        """Test scraping configuration"""
        with patch.dict(os.environ, {
            'MAX_CONCURRENT_BROWSERS': '5',
            'DEFAULT_TIMEOUT': '45',
            'RATE_LIMIT_DELAY': '3.0'
        }):
            config = ScrapingConfig()
            
            assert config.max_concurrent_browsers == 5
            assert config.default_timeout == 45
            assert config.rate_limit_delay == 3.0
    
    def test_environment_validation(self):
        """Test environment validation"""
        with pytest.raises(ValueError):
            with patch.dict(os.environ, {'ENVIRONMENT': 'invalid_env'}):
                Settings()
    
    def test_has_llm_provider(self):
        """Test LLM provider availability check"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            settings = Settings()
            assert settings.has_llm_provider() == True
        
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.has_llm_provider() == False
    
    def test_get_active_llm_provider(self):
        """Test active LLM provider detection"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key',
            'PRIMARY_LLM_PROVIDER': 'openai'
        }):
            settings = Settings()
            assert settings.get_active_llm_provider() == 'openai'
        
        with patch.dict(os.environ, {
            'CLAUDE_API_KEY': 'test_key',
            'PRIMARY_LLM_PROVIDER': 'claude'
        }):
            settings = Settings()
            assert settings.get_active_llm_provider() == 'claude'
    
    def test_settings_dict_masking(self):
        """Test that sensitive data is masked in dict output"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'secret_key',
            'MONGODB_URI': 'mongodb://user:pass@host:27017/db'
        }):
            settings = Settings()
            settings_dict = settings.dict()
            
            assert settings_dict['llm']['openai_api_key'] == '***MASKED***'
            assert settings_dict['storage']['mongodb_uri'] == '***MASKED***'
    
    def test_is_production(self):
        """Test production environment detection"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            settings = Settings()
            assert settings.is_production() == True
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            settings = Settings()
            assert settings.is_production() == False


class TestScrapingProfiles:
    """Test cases for ScrapingProfiles"""
    
    def test_get_profile(self):
        """Test profile retrieval"""
        profile = ScrapingProfiles.get_profile("balanced")
        
        assert profile["name"] == "Balanced"
        assert "rate_limit" in profile
        assert "retry_attempts" in profile
        assert "anti_detection" in profile
    
    def test_get_all_profiles(self):
        """Test getting all profiles"""
        profiles = ScrapingProfiles.get_all_profiles()
        
        expected_profiles = ["conservative", "balanced", "aggressive", "stealth"]
        for profile_name in expected_profiles:
            assert profile_name in profiles
            assert "name" in profiles[profile_name]
            assert "rate_limit" in profiles[profile_name]
    
    def test_invalid_profile(self):
        """Test invalid profile handling"""
        with pytest.raises(ValueError):
            ScrapingProfiles.get_profile("invalid_profile")
    
    def test_create_custom_profile(self):
        """Test custom profile creation"""
        custom_profile = ScrapingProfiles.create_custom_profile(
            "balanced",
            {"rate_limit": 5.0, "retry_attempts": 10}
        )
        
        assert custom_profile["rate_limit"] == 5.0
        assert custom_profile["retry_attempts"] == 10
        assert custom_profile["name"] == "Balanced"  # Inherited from base
    
    def test_get_profile_for_site_type(self):
        """Test site type profile recommendations"""
        test_cases = [
            ("e-commerce", "balanced"),
            ("social_media", "stealth"),
            ("job_boards", "conservative"),
            ("news", "balanced"),
            ("unknown_type", "balanced")
        ]
        
        for site_type, expected_profile in test_cases:
            recommended = ScrapingProfiles.get_profile_for_site_type(site_type)
            assert recommended == expected_profile
    
    def test_validate_profile(self):
        """Test profile validation"""
        valid_profile = {
            "rate_limit": 2.0,
            "retry_attempts": 3,
            "timeout": 30,
            "anti_detection": "medium",
            "concurrent_browsers": 2
        }
        
        assert ScrapingProfiles.validate_profile(valid_profile) == True
        
        invalid_profile = {
            "rate_limit": -1,  # Invalid negative rate
            "retry_attempts": 0,  # Invalid zero retries
        }
        
        assert ScrapingProfiles.validate_profile(invalid_profile) == False
    
    def test_profile_structure(self):
        """Test that all profiles have required structure"""
        required_fields = [
            "name", "description", "rate_limit", "retry_attempts", 
            "timeout", "anti_detection", "concurrent_browsers"
        ]
        
        for profile_name in ["conservative", "balanced", "aggressive", "stealth"]:
            profile = ScrapingProfiles.get_profile(profile_name)
            
            for field in required_fields:
                assert field in profile, f"Missing field '{field}' in profile '{profile_name}'"
            
            # Validate data types
            assert isinstance(profile["rate_limit"], (int, float))
            assert isinstance(profile["retry_attempts"], int)
            assert isinstance(profile["timeout"], int)
            assert isinstance(profile["concurrent_browsers"], int)
            assert profile["anti_detection"] in ["low", "medium", "high", "maximum"]