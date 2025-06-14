"""
Data processing utilities for cleaning, validation, and enrichment
"""

import re
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime

from ..utils.logger import ComponentLogger


@dataclass
class ProcessingStats:
    """Statistics from data processing operations"""
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    modifications_made: int = 0
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    quality_score: float = 0.0


class BaseProcessor(ABC):
    """Base class for data processors"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = ComponentLogger(f"processor_{name}")
    
    @abstractmethod
    async def process(self, data: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], ProcessingStats]:
        """Process data and return results with stats"""
        pass


class DataCleaner(BaseProcessor):
    """
    Data cleaning processor for normalizing and cleaning extracted data
    """
    
    def __init__(self):
        super().__init__("data_cleaner")
        
        # Cleaning rules
        self.text_cleaning_rules = [
            (r'\s+', ' '),  # Multiple whitespace to single space
            (r'^\s+|\s+$', ''),  # Strip leading/trailing whitespace
            (r'[\x00-\x1f\x7f-\x9f]', ''),  # Remove control characters
            (r'&nbsp;|&amp;|&lt;|&gt;|&quot;|&#39;', self._decode_html_entities),
        ]
        
        # Price cleaning patterns
        self.price_patterns = [
            (r'[^\d.,]', ''),  # Remove non-numeric except decimal separators
            (r'^,+|,+$', ''),  # Remove leading/trailing commas
            (r'\.(?=.*\.)', ''),  # Remove all but last decimal point
        ]
        
        # URL normalization
        self.url_patterns = [
            (r'^//', 'https://'),  # Protocol-relative URLs
            (r'(?<!:)//+', '/'),  # Multiple slashes to single
        ]
    
    async def process(self, data: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], ProcessingStats]:
        """Clean and normalize data"""
        start_time = time.time()
        stats = ProcessingStats(total_items=len(data))
        
        cleaned_data = []
        
        for item in data:
            try:
                cleaned_item = await self._clean_item(item)
                cleaned_data.append(cleaned_item)
                stats.processed_items += 1
                
                # Count modifications
                if cleaned_item != item:
                    stats.modifications_made += 1
                    
            except Exception as e:
                stats.failed_items += 1
                stats.errors.append(f"Failed to clean item: {str(e)}")
                self.logger.warning("Item cleaning failed", error=str(e))
                
                # Include original item if cleaning fails
                cleaned_data.append(item)
        
        stats.processing_time = time.time() - start_time
        
        self.logger.info("Data cleaning completed",
                        total=stats.total_items,
                        processed=stats.processed_items,
                        failed=stats.failed_items,
                        modifications=stats.modifications_made,
                        time=stats.processing_time)
        
        return cleaned_data, stats
    
    async def _clean_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a single data item"""
        cleaned_item = {}
        
        for key, value in item.items():
            if key.startswith('_'):
                # Preserve metadata fields as-is
                cleaned_item[key] = value
                continue
            
            # Clean based on field type/name
            if isinstance(value, str):
                if 'price' in key.lower() or 'cost' in key.lower() or '$' in str(value):
                    cleaned_item[key] = self._clean_price(value)
                elif 'url' in key.lower() or 'link' in key.lower():
                    cleaned_item[key] = self._clean_url(value)
                elif 'email' in key.lower():
                    cleaned_item[key] = self._clean_email(value)
                elif 'phone' in key.lower():
                    cleaned_item[key] = self._clean_phone(value)
                else:
                    cleaned_item[key] = self._clean_text(value)
            else:
                cleaned_item[key] = value
        
        return cleaned_item
    
    def _clean_text(self, text: str) -> str:
        """Clean general text content"""
        if not text:
            return ""
        
        cleaned = str(text)
        
        # Apply cleaning rules
        for pattern, replacement in self.text_cleaning_rules:
            if callable(replacement):
                cleaned = re.sub(pattern, replacement, cleaned)
            else:
                cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned.strip()
    
    def _clean_price(self, price_str: str) -> str:
        """Clean and normalize price strings"""
        if not price_str:
            return ""
        
        cleaned = str(price_str)
        
        # Apply price-specific cleaning
        for pattern, replacement in self.price_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        # Try to format as proper decimal
        try:
            # Handle comma as thousand separator
            if ',' in cleaned and '.' in cleaned:
                # Assume comma is thousand separator if it comes before period
                if cleaned.rindex(',') < cleaned.rindex('.'):
                    cleaned = cleaned.replace(',', '')
            elif cleaned.count(',') == 1 and '.' not in cleaned:
                # Single comma might be decimal separator
                if len(cleaned.split(',')[1]) <= 2:  # Max 2 decimal places
                    cleaned = cleaned.replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            
            # Validate numeric format
            float(cleaned)
            return cleaned
            
        except ValueError:
            # Return original if we can't parse it
            return price_str
    
    def _clean_url(self, url: str) -> str:
        """Clean and normalize URLs"""
        if not url:
            return ""
        
        cleaned = str(url).strip()
        
        # Apply URL-specific cleaning
        for pattern, replacement in self.url_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        # Ensure proper protocol
        if cleaned and not cleaned.startswith(('http://', 'https://', '//')):
            if cleaned.startswith('/'):
                pass  # Relative URL, leave as-is
            else:
                cleaned = 'https://' + cleaned
        
        return cleaned
    
    def _clean_email(self, email: str) -> str:
        """Clean email addresses"""
        if not email:
            return ""
        
        cleaned = self._clean_text(email).lower()
        
        # Basic email validation and cleaning
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, cleaned)
        
        return match.group() if match else cleaned
    
    def _clean_phone(self, phone: str) -> str:
        """Clean phone numbers"""
        if not phone:
            return ""
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', str(phone))
        
        # Basic phone number formatting
        if cleaned.startswith('+'):
            return cleaned
        elif len(cleaned) == 10:  # US format
            return f"+1{cleaned}"
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            return f"+{cleaned}"
        else:
            return cleaned
    
    def _decode_html_entities(self, match):
        """Decode common HTML entities"""
        entity_map = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'"
        }
        return entity_map.get(match.group(), match.group())


class DataValidator(BaseProcessor):
    """
    Data validation processor for checking data quality and completeness
    """
    
    def __init__(self):
        super().__init__("data_validator")
        
        # Validation rules
        self.field_validators = {
            'email': self._validate_email,
            'url': self._validate_url,
            'phone': self._validate_phone,
            'price': self._validate_price,
            'date': self._validate_date
        }
    
    async def process(self, data: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], ProcessingStats]:
        """Validate data and add quality scores"""
        start_time = time.time()
        stats = ProcessingStats(total_items=len(data))
        
        validated_data = []
        
        for item in data:
            try:
                validation_result = await self._validate_item(item)
                
                # Add validation metadata
                validated_item = item.copy()
                validated_item['_validation_score'] = validation_result.quality_score
                validated_item['_validation_errors'] = validation_result.errors
                validated_item['_validation_warnings'] = validation_result.warnings
                validated_item['_is_valid'] = validation_result.is_valid
                
                validated_data.append(validated_item)
                stats.processed_items += 1
                
                if not validation_result.is_valid:
                    stats.failed_items += 1
                    
            except Exception as e:
                stats.failed_items += 1
                stats.errors.append(f"Failed to validate item: {str(e)}")
                validated_data.append(item)
        
        stats.processing_time = time.time() - start_time
        
        self.logger.info("Data validation completed",
                        total=stats.total_items,
                        valid=stats.processed_items - stats.failed_items,
                        invalid=stats.failed_items,
                        time=stats.processing_time)
        
        return validated_data, stats
    
    async def _validate_item(self, item: Dict[str, Any]) -> ValidationResult:
        """Validate a single data item"""
        result = ValidationResult(is_valid=True)
        
        # Check for required fields (non-empty values)
        required_fields = [k for k, v in item.items() 
                          if not k.startswith('_') and v]
        
        if len(required_fields) == 0:
            result.is_valid = False
            result.errors.append("No valid data fields found")
            result.quality_score = 0.0
            return result
        
        # Validate specific field types
        for field_name, value in item.items():
            if field_name.startswith('_') or not value:
                continue
            
            # Determine field type and validate
            field_type = self._detect_field_type(field_name, value)
            
            if field_type in self.field_validators:
                is_valid, error_msg = self.field_validators[field_type](value)
                
                if not is_valid:
                    result.warnings.append(f"{field_name}: {error_msg}")
        
        # Calculate quality score
        result.quality_score = self._calculate_quality_score(item, result)
        
        # Determine overall validity
        result.is_valid = len(result.errors) == 0 and result.quality_score >= 0.5
        
        return result
    
    def _detect_field_type(self, field_name: str, value: Any) -> str:
        """Detect the type of field based on name and content"""
        field_name_lower = field_name.lower()
        value_str = str(value).lower()
        
        if 'email' in field_name_lower:
            return 'email'
        elif any(url_indicator in field_name_lower for url_indicator in ['url', 'link', 'href']):
            return 'url'
        elif any(phone_indicator in field_name_lower for phone_indicator in ['phone', 'tel', 'mobile']):
            return 'phone'
        elif any(price_indicator in field_name_lower for price_indicator in ['price', 'cost', 'amount']):
            return 'price'
        elif any(date_indicator in field_name_lower for date_indicator in ['date', 'time', 'posted', 'created']):
            return 'date'
        elif '@' in value_str:
            return 'email'
        elif value_str.startswith(('http://', 'https://', 'www.')):
            return 'url'
        elif re.match(r'[\d\s\-\+\(\)]+', value_str) and len(value_str) >= 10:
            return 'phone'
        elif re.search(r'[\$£€¥]|\d+\.\d{2}', value_str):
            return 'price'
        else:
            return 'text'
    
    def _validate_email(self, email: str) -> tuple[bool, str]:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if re.match(email_pattern, str(email).strip()):
            return True, ""
        else:
            return False, "Invalid email format"
    
    def _validate_url(self, url: str) -> tuple[bool, str]:
        """Validate URL format"""
        url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
        
        if re.match(url_pattern, str(url).strip()):
            return True, ""
        else:
            return False, "Invalid URL format"
    
    def _validate_phone(self, phone: str) -> tuple[bool, str]:
        """Validate phone number"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', str(phone))
        
        if len(digits_only) >= 10:
            return True, ""
        else:
            return False, "Phone number too short"
    
    def _validate_price(self, price: str) -> tuple[bool, str]:
        """Validate price format"""
        try:
            # Remove currency symbols and formatting
            price_clean = re.sub(r'[^\d.,]', '', str(price))
            price_clean = price_clean.replace(',', '')
            
            price_value = float(price_clean)
            
            if price_value >= 0:
                return True, ""
            else:
                return False, "Negative price value"
                
        except ValueError:
            return False, "Invalid price format"
    
    def _validate_date(self, date_str: str) -> tuple[bool, str]:
        """Validate date format"""
        # Common date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, str(date_str)):
                return True, ""
        
        return False, "Unrecognized date format"
    
    def _calculate_quality_score(self, item: Dict[str, Any], validation_result: ValidationResult) -> float:
        """Calculate overall quality score for item"""
        # Base score from field completeness
        non_meta_fields = {k: v for k, v in item.items() if not k.startswith('_')}
        non_empty_fields = {k: v for k, v in non_meta_fields.items() if v and str(v).strip()}
        
        completeness_score = len(non_empty_fields) / max(len(non_meta_fields), 1)
        
        # Penalty for validation warnings
        warning_penalty = min(len(validation_result.warnings) * 0.1, 0.5)
        
        # Penalty for validation errors
        error_penalty = min(len(validation_result.errors) * 0.2, 0.8)
        
        # Final score
        quality_score = completeness_score - warning_penalty - error_penalty
        
        return max(0.0, min(1.0, quality_score))


class DataEnricher(BaseProcessor):
    """
    Data enrichment processor for adding derived fields and metadata
    """
    
    def __init__(self):
        super().__init__("data_enricher")
    
    async def process(self, data: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], ProcessingStats]:
        """Enrich data with derived fields and metadata"""
        start_time = time.time()
        stats = ProcessingStats(total_items=len(data))
        
        enriched_data = []
        
        for item in data:
            try:
                enriched_item = await self._enrich_item(item)
                enriched_data.append(enriched_item)
                stats.processed_items += 1
                
                if enriched_item != item:
                    stats.modifications_made += 1
                    
            except Exception as e:
                stats.failed_items += 1
                stats.errors.append(f"Failed to enrich item: {str(e)}")
                enriched_data.append(item)
        
        stats.processing_time = time.time() - start_time
        
        self.logger.info("Data enrichment completed",
                        total=stats.total_items,
                        processed=stats.processed_items,
                        failed=stats.failed_items,
                        modifications=stats.modifications_made,
                        time=stats.processing_time)
        
        return enriched_data, stats
    
    async def _enrich_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single data item"""
        enriched_item = item.copy()
        
        # Add timestamp if not present
        if '_enriched_at' not in enriched_item:
            enriched_item['_enriched_at'] = time.time()
        
        # Add field count
        non_meta_fields = [k for k in item.keys() if not k.startswith('_')]
        enriched_item['_field_count'] = len(non_meta_fields)
        
        # Extract domain from URLs
        for field_name, value in item.items():
            if isinstance(value, str) and ('url' in field_name.lower() or value.startswith('http')):
                domain = self._extract_domain(value)
                if domain:
                    enriched_item[f'{field_name}_domain'] = domain
        
        # Price normalization
        for field_name, value in item.items():
            if 'price' in field_name.lower() and isinstance(value, str):
                normalized_price = self._normalize_price(value)
                if normalized_price is not None:
                    enriched_item[f'{field_name}_numeric'] = normalized_price
        
        # Text statistics
        text_fields = {k: v for k, v in item.items() 
                      if isinstance(v, str) and not k.startswith('_') and len(str(v)) > 20}
        
        if text_fields:
            total_chars = sum(len(str(v)) for v in text_fields.values())
            total_words = sum(len(str(v).split()) for v in text_fields.values())
            
            enriched_item['_total_text_length'] = total_chars
            enriched_item['_total_word_count'] = total_words
        
        # Data freshness indicator
        extracted_at = item.get('_extracted_at', time.time())
        age_hours = (time.time() - extracted_at) / 3600
        enriched_item['_data_age_hours'] = round(age_hours, 2)
        
        # Content hash for deduplication
        content_hash = self._generate_content_hash(item)
        enriched_item['_content_hash'] = content_hash
        
        return enriched_item
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower() if parsed.netloc else None
        except:
            return None
    
    def _normalize_price(self, price_str: str) -> Optional[float]:
        """Normalize price string to numeric value"""
        try:
            # Remove currency symbols and formatting
            cleaned = re.sub(r'[^\d.,]', '', str(price_str))
            cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
        except:
            return None
    
    def _generate_content_hash(self, item: Dict[str, Any]) -> str:
        """Generate hash of content fields for deduplication"""
        import hashlib
        import json
        
        # Get content fields (non-metadata)
        content_fields = {k: v for k, v in item.items() if not k.startswith('_')}
        
        # Create consistent string representation
        content_str = json.dumps(content_fields, sort_keys=True, default=str)
        
        return hashlib.md5(content_str.encode()).hexdigest()