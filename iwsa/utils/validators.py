"""
Validation utilities for IWSA
"""

import re
import json
import validators
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from email_validator import validate_email as _validate_email, EmailNotValidError


def validate_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted and accessible
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Basic format validation
        if not isinstance(url, str) or not url.strip():
            return False
        
        # Use validators library for comprehensive check
        result = validators.url(url)
        if not result:
            return False
        
        # Additional checks
        parsed = urlparse(url)
        
        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Scheme must be http or https
        if parsed.scheme.lower() not in ['http', 'https']:
            return False
        
        # Domain validation
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, parsed.netloc.split(':')[0]):
            return False
        
        return True
        
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not isinstance(email, str) or not email.strip():
            return False
        
        # Use email-validator library
        _validate_email(email)
        return True
        
    except (EmailNotValidError, Exception):
        return False


def validate_json(json_string: str) -> bool:
    """
    Validate if string is valid JSON
    
    Args:
        json_string: JSON string to validate
        
    Returns:
        True if valid JSON, False otherwise
    """
    try:
        if not isinstance(json_string, str):
            return False
        
        json.loads(json_string)
        return True
        
    except (json.JSONDecodeError, Exception):
        return False


def validate_css_selector(selector: str) -> bool:
    """
    Basic validation for CSS selectors
    
    Args:
        selector: CSS selector string
        
    Returns:
        True if appears to be valid CSS selector, False otherwise
    """
    try:
        if not isinstance(selector, str) or not selector.strip():
            return False
        
        # Basic CSS selector pattern check
        # This is a simplified validation - full CSS selector validation is complex
        invalid_chars = ['<', '>', '{', '}', '"', "'"]
        if any(char in selector for char in invalid_chars):
            return False
        
        # Must not be empty after stripping
        if not selector.strip():
            return False
        
        # Basic structure checks
        selector = selector.strip()
        
        # Can't start or end with combinators
        combinators = ['+', '~', '>']
        if any(selector.startswith(c) or selector.endswith(c) for c in combinators):
            return False
        
        return True
        
    except Exception:
        return False


def validate_xpath(xpath: str) -> bool:
    """
    Basic validation for XPath expressions
    
    Args:
        xpath: XPath expression string
        
    Returns:
        True if appears to be valid XPath, False otherwise
    """
    try:
        if not isinstance(xpath, str) or not xpath.strip():
            return False
        
        xpath = xpath.strip()
        
        # Must start with / or // or contain valid axis
        valid_starts = ['/', './', '../', '(', 'descendant::', 'child::', 'parent::']
        if not any(xpath.startswith(start) for start in valid_starts):
            # Check if it's a relative path or function
            if not re.match(r'^[a-zA-Z_][\w\-]*(\[.*\])?', xpath):
                return False
        
        # Basic bracket balance check
        if xpath.count('[') != xpath.count(']'):
            return False
        if xpath.count('(') != xpath.count(')'):
            return False
        
        return True
        
    except Exception:
        return False


def validate_proxy_url(proxy_url: str) -> bool:
    """
    Validate proxy URL format
    
    Args:
        proxy_url: Proxy URL to validate
        
    Returns:
        True if valid proxy URL, False otherwise
    """
    try:
        if not isinstance(proxy_url, str) or not proxy_url.strip():
            return False
        
        parsed = urlparse(proxy_url)
        
        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Valid proxy schemes
        valid_schemes = ['http', 'https', 'socks4', 'socks5']
        if parsed.scheme.lower() not in valid_schemes:
            return False
        
        # Port must be valid if specified
        if parsed.port:
            if not (1 <= parsed.port <= 65535):
                return False
        
        return True
        
    except Exception:
        return False


def validate_mongodb_uri(uri: str) -> bool:
    """
    Validate MongoDB connection URI
    
    Args:
        uri: MongoDB URI to validate
        
    Returns:
        True if valid MongoDB URI format, False otherwise
    """
    try:
        if not isinstance(uri, str) or not uri.strip():
            return False
        
        # Must start with mongodb:// or mongodb+srv://
        if not uri.startswith(('mongodb://', 'mongodb+srv://')):
            return False
        
        # Basic format validation
        parsed = urlparse(uri)
        if not parsed.netloc:
            return False
        
        return True
        
    except Exception:
        return False


def validate_api_key_format(api_key: str, provider: str) -> bool:
    """
    Validate API key format for different providers
    
    Args:
        api_key: API key to validate
        provider: Provider name (openai, claude, huggingface)
        
    Returns:
        True if format appears valid, False otherwise
    """
    try:
        if not isinstance(api_key, str) or not api_key.strip():
            return False
        
        api_key = api_key.strip()
        
        # Provider-specific format checks
        if provider.lower() == 'openai':
            # OpenAI keys typically start with 'sk-' and are 51 chars long
            return api_key.startswith('sk-') and len(api_key) == 51
        
        elif provider.lower() == 'claude':
            # Claude API keys have a specific format
            return len(api_key) >= 20 and api_key.replace('-', '').replace('_', '').isalnum()
        
        elif provider.lower() == 'huggingface':
            # Hugging Face tokens start with 'hf_'
            return api_key.startswith('hf_') and len(api_key) >= 20
        
        else:
            # Generic validation - must be at least 10 chars, alphanumeric with some special chars
            return len(api_key) >= 10 and re.match(r'^[A-Za-z0-9_\-\.]+$', api_key)
        
    except Exception:
        return False


def validate_scraping_profile(profile: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate scraping profile configuration
    
    Args:
        profile: Profile dictionary to validate
        
    Returns:
        Dictionary with 'errors' and 'warnings' lists
    """
    errors = []
    warnings = []
    
    try:
        # Required fields
        required_fields = [
            'rate_limit', 'retry_attempts', 'timeout', 
            'anti_detection', 'concurrent_browsers'
        ]
        
        for field in required_fields:
            if field not in profile:
                errors.append(f"Missing required field: {field}")
        
        # Validate numeric fields
        numeric_validations = {
            'rate_limit': (0, float('inf')),
            'retry_attempts': (1, 10),
            'timeout': (1, 300),
            'concurrent_browsers': (1, 10)
        }
        
        for field, (min_val, max_val) in numeric_validations.items():
            if field in profile:
                try:
                    value = float(profile[field])
                    if not (min_val <= value <= max_val):
                        errors.append(f"{field} must be between {min_val} and {max_val}")
                except (ValueError, TypeError):
                    errors.append(f"{field} must be a number")
        
        # Validate string enums
        if 'anti_detection' in profile:
            valid_levels = ['low', 'medium', 'high', 'maximum']
            if profile['anti_detection'] not in valid_levels:
                errors.append(f"anti_detection must be one of: {valid_levels}")
        
        # Warnings for potentially problematic configurations
        if profile.get('rate_limit', 0) < 1:
            warnings.append("Very low rate limit may cause detection")
        
        if profile.get('concurrent_browsers', 0) > 5:
            warnings.append("High concurrent browsers may exceed resource limits")
        
        if profile.get('retry_attempts', 0) > 5:
            warnings.append("High retry attempts may slow down scraping significantly")
        
    except Exception as e:
        errors.append(f"Profile validation error: {str(e)}")
    
    return {'errors': errors, 'warnings': warnings}


def validate_data_fields(fields: List[str]) -> Dict[str, List[str]]:
    """
    Validate data field specifications
    
    Args:
        fields: List of field names to validate
        
    Returns:
        Dictionary with 'errors' and 'warnings' lists
    """
    errors = []
    warnings = []
    
    try:
        if not isinstance(fields, list):
            errors.append("Fields must be a list")
            return {'errors': errors, 'warnings': warnings}
        
        if not fields:
            warnings.append("No data fields specified")
            return {'errors': errors, 'warnings': warnings}
        
        for field in fields:
            if not isinstance(field, str):
                errors.append(f"Field name must be string: {field}")
                continue
            
            if not field.strip():
                errors.append("Empty field name found")
                continue
            
            # Field name validation
            field_name = field.strip()
            
            # Must be valid identifier-like
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_\s\-]*$', field_name):
                warnings.append(f"Field name may cause issues: {field_name}")
            
            # Length check
            if len(field_name) > 50:
                warnings.append(f"Very long field name: {field_name}")
        
        # Check for duplicates
        lowercase_fields = [f.lower().strip() for f in fields]
        if len(set(lowercase_fields)) != len(lowercase_fields):
            warnings.append("Duplicate field names found (case-insensitive)")
        
    except Exception as e:
        errors.append(f"Field validation error: {str(e)}")
    
    return {'errors': errors, 'warnings': warnings}