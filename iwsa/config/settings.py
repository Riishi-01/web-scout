"""
Settings and configuration management for IWSA
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from pydantic import BaseSettings, Field, validator
import yaml
from dotenv import load_dotenv


class LLMConfig(BaseSettings):
    """LLM provider configuration"""
    
    # Primary providers (user-provided keys)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    claude_api_key: Optional[str] = Field(None, env="CLAUDE_API_KEY")
    
    # Fallback provider
    hf_api_key: Optional[str] = Field(None, env="HF_API_KEY")
    
    # Local TinyLlama configuration
    tinyllama_model_path: str = Field("./models/tinyllama-1.1b-onnx", env="TINYLLAMA_MODEL_PATH")
    tinyllama_max_memory: str = Field("1.5GB", env="TINYLLAMA_MAX_MEMORY")
    tinyllama_threads: int = Field(4, env="TINYLLAMA_THREADS")
    tinyllama_quantization: str = Field("int8", env="TINYLLAMA_QUANTIZATION")
    tinyllama_batch_size: int = Field(1, env="TINYLLAMA_BATCH_SIZE")
    
    # Configuration
    primary_provider: str = Field("tinyllama", env="PRIMARY_LLM_PROVIDER")
    fallback_provider: str = Field("openai", env="FALLBACK_LLM_PROVIDER")
    timeout: int = Field(30, env="LLM_TIMEOUT")
    retry_attempts: int = Field(3, env="LLM_RETRY_ATTEMPTS")
    rate_limiting: bool = Field(True, env="LLM_RATE_LIMITING")
    
    # Request routing configuration
    local_complexity_threshold: float = Field(0.3, env="LOCAL_COMPLEXITY_THRESHOLD")
    local_token_limit: int = Field(1000, env="LOCAL_TOKEN_LIMIT")
    enable_hybrid_routing: bool = Field(True, env="ENABLE_HYBRID_ROUTING")
    
    # Model specifications
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    claude_model: str = Field("claude-3-sonnet-20240229", env="CLAUDE_MODEL")
    hf_model: str = Field("microsoft/DialoGPT-large", env="HF_MODEL")
    
    # Token limits
    max_tokens: int = Field(4000, env="LLM_MAX_TOKENS")
    temperature: float = Field(0.1, env="LLM_TEMPERATURE")


class StorageConfig(BaseSettings):
    """Storage configuration"""
    
    # MongoDB Atlas
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    database_name: str = Field("iwsa_data", env="MONGODB_DATABASE")
    collection_name: str = Field("scraped_data", env="MONGODB_COLLECTION")
    
    # Google Sheets
    google_credentials: Optional[str] = Field(None, env="GOOGLE_CREDENTIALS")
    sheets_scope: list = Field(
        default=["https://spreadsheets.google.com/feeds", 
                "https://www.googleapis.com/auth/drive"],
        env="SHEETS_SCOPE"
    )


class ScrapingConfig(BaseSettings):
    """Scraping engine configuration"""
    
    # Browser settings
    max_concurrent_browsers: int = Field(3, env="MAX_CONCURRENT_BROWSERS")
    default_timeout: int = Field(30, env="DEFAULT_TIMEOUT")
    headless: bool = Field(True, env="BROWSER_HEADLESS")
    
    # Performance limits
    memory_limit: str = Field("512MB", env="MEMORY_LIMIT")
    cpu_limit: int = Field(2, env="CPU_LIMIT")
    max_pages_per_session: int = Field(1000, env="MAX_PAGES_PER_SESSION")
    
    # Rate limiting
    rate_limit_delay: float = Field(2.0, env="RATE_LIMIT_DELAY")
    min_delay: float = Field(1.0, env="MIN_DELAY")
    max_delay: float = Field(10.0, env="MAX_DELAY")
    
    # Anti-detection
    user_agent_rotation: bool = Field(True, env="USER_AGENT_ROTATION")
    ip_rotation: bool = Field(True, env="IP_ROTATION")
    fingerprint_randomization: bool = Field(True, env="FINGERPRINT_RANDOMIZATION")
    
    # Proxy configuration
    proxy_pool_url: Optional[str] = Field(None, env="PROXY_POOL_URL")
    proxy_rotation_interval: int = Field(10, env="PROXY_ROTATION_INTERVAL")


class MonitoringConfig(BaseSettings):
    """Monitoring and logging configuration"""
    
    enable_monitoring: bool = Field(True, env="ENABLE_MONITORING")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    metrics_enabled: bool = Field(True, env="METRICS_ENABLED")
    
    # Uptime monitoring
    uptime_robot_key: Optional[str] = Field(None, env="UPTIME_ROBOT_KEY")
    
    # Performance thresholds
    max_memory_usage: float = Field(0.8, env="MAX_MEMORY_USAGE")
    max_cpu_usage: float = Field(0.8, env="MAX_CPU_USAGE")
    max_error_rate: float = Field(0.01, env="MAX_ERROR_RATE")


class Settings(BaseSettings):
    """Main settings class combining all configurations"""
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    # Component configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    scraping: ScrapingConfig = Field(default_factory=ScrapingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        # Load environment variables
        load_dotenv()
        super().__init__(**kwargs)
        
        # Load additional configuration from YAML if exists
        self._load_yaml_config()
    
    def _load_yaml_config(self):
        """Load additional configuration from YAML file"""
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                self._merge_yaml_config(yaml_config)
    
    def _merge_yaml_config(self, yaml_config: Dict[str, Any]):
        """Merge YAML configuration with existing settings"""
        for key, value in yaml_config.items():
            if hasattr(self, key):
                if isinstance(value, dict):
                    # Merge nested configuration
                    current_value = getattr(self, key)
                    if hasattr(current_value, 'dict'):
                        merged = {**current_value.dict(), **value}
                        setattr(self, key, type(current_value)(**merged))
                else:
                    setattr(self, key, value)
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting"""
        valid_envs = ['development', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'Environment must be one of: {valid_envs}')
        return v
    
    def get_scraping_profile(self, profile_name: str = "balanced") -> Dict[str, Any]:
        """Get scraping profile configuration"""
        from .profiles import ScrapingProfiles
        return ScrapingProfiles.get_profile(profile_name)
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    def has_llm_provider(self) -> bool:
        """Check if at least one LLM provider is configured"""
        return bool(self.llm.openai_api_key or 
                   self.llm.claude_api_key or 
                   self.llm.hf_api_key or
                   self._has_local_model())
    
    def _has_local_model(self) -> bool:
        """Check if local TinyLlama model is available"""
        import os
        return os.path.exists(self.llm.tinyllama_model_path)
    
    def get_active_llm_provider(self) -> str:
        """Get the currently active LLM provider"""
        if self.llm.primary_provider == "tinyllama" and self._has_local_model():
            return "tinyllama"
        elif self.llm.primary_provider == "openai" and self.llm.openai_api_key:
            return "openai"
        elif self.llm.primary_provider == "claude" and self.llm.claude_api_key:
            return "claude"
        elif self.llm.hf_api_key:
            return "huggingface"
        elif self._has_local_model():
            return "tinyllama"
        else:
            raise ValueError("No LLM provider configured with valid API key or local model")
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Convert settings to dictionary, excluding sensitive data"""
        data = super().dict(**kwargs)
        
        # Mask sensitive information
        if 'llm' in data:
            for key in ['openai_api_key', 'claude_api_key', 'hf_api_key']:
                if key in data['llm'] and data['llm'][key]:
                    data['llm'][key] = "***MASKED***"
        
        if 'storage' in data:
            if 'mongodb_uri' in data['storage'] and data['storage']['mongodb_uri']:
                data['storage']['mongodb_uri'] = "***MASKED***"
            if 'google_credentials' in data['storage'] and data['storage']['google_credentials']:
                data['storage']['google_credentials'] = "***MASKED***"
        
        return data