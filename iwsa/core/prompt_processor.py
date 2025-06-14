"""
Prompt Processing Layer - Natural language understanding for scraping requests
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin
from pydantic import BaseModel, Field, validator
import aiohttp
from bs4 import BeautifulSoup

from ..config import Settings
from ..utils.logger import ComponentLogger
from ..utils.validators import validate_url


@dataclass
class ExtractedIntent:
    """Represents extracted intent from user prompt"""
    
    # Core extraction parameters
    target_urls: List[str] = field(default_factory=list)
    data_fields: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    
    # Scraping context
    scraping_type: str = "general"  # job_listings, products, contacts, etc.
    urgency: str = "normal"  # low, normal, high
    volume_estimate: int = 0
    
    # Anti-detection requirements
    detection_level: str = "medium"  # low, medium, high, maximum
    
    # Data requirements
    output_format: str = "sheets"  # sheets, json, csv
    data_quality: str = "standard"  # basic, standard, high
    
    # Additional parameters
    pagination_limit: Optional[int] = None
    date_range: Optional[Dict[str, str]] = None
    geographic_filter: Optional[str] = None
    language: str = "en"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "target_urls": self.target_urls,
            "data_fields": self.data_fields,
            "filters": self.filters,
            "scraping_type": self.scraping_type,
            "urgency": self.urgency,
            "volume_estimate": self.volume_estimate,
            "detection_level": self.detection_level,
            "output_format": self.output_format,
            "data_quality": self.data_quality,
            "pagination_limit": self.pagination_limit,
            "date_range": self.date_range,
            "geographic_filter": self.geographic_filter,
            "language": self.language
        }


class ValidationResult(BaseModel):
    """Result of parameter validation"""
    
    valid: bool
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    legal_status: str = "unknown"  # allowed, restricted, prohibited, unknown
    resource_estimate: Dict[str, Any] = Field(default_factory=dict)


class PromptProcessor:
    """
    Natural language prompt processor for extracting scraping parameters
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = ComponentLogger("prompt_processor")
        
        # Intent classification patterns
        self.intent_patterns = {
            "job_listings": [
                r"job[s]?\s+listing[s]?", r"job[s]?\s+posting[s]?", r"career[s]?",
                r"employment", r"hiring", r"position[s]?", r"vacancy", r"vacancies"
            ],
            "products": [
                r"product[s]?", r"item[s]?", r"catalog", r"inventory", 
                r"shop", r"store", r"merchandise", r"goods"
            ],
            "contacts": [
                r"contact[s]?", r"email[s]?", r"phone[s]?", r"address",
                r"directory", r"profile[s]?", r"people", r"person"
            ],
            "news": [
                r"news", r"article[s]?", r"story", r"stories", 
                r"press", r"media", r"publication[s]?"
            ],
            "real_estate": [
                r"property", r"properties", r"real\s+estate", r"house[s]?",
                r"apartment[s]?", r"rental[s]?", r"listing[s]?"
            ],
            "reviews": [
                r"review[s]?", r"rating[s]?", r"feedback", r"comment[s]?",
                r"testimonial[s]?", r"opinion[s]?"
            ]
        }
        
        # Urgency indicators
        self.urgency_patterns = {
            "high": [r"urgent", r"asap", r"quickly", r"fast", r"immediately"],
            "low": [r"when\s+possible", r"eventually", r"no\s+rush"]
        }
        
        # Data field extraction patterns
        self.field_patterns = {
            "title": [r"title[s]?", r"name[s]?", r"heading[s]?"],
            "price": [r"price[s]?", r"cost[s]?", r"amount[s]?", r"\$", r"dollar[s]?"],
            "description": [r"description[s]?", r"detail[s]?", r"info"],
            "location": [r"location[s]?", r"address", r"city", r"state"],
            "date": [r"date[s]?", r"time", r"when", r"posted"],
            "contact": [r"contact", r"email", r"phone", r"tel"],
            "company": [r"company", r"organization", r"employer"],
            "rating": [r"rating[s]?", r"star[s]?", r"score[s]?"]
        }
    
    async def process_prompt(self, prompt: str) -> ExtractedIntent:
        """
        Process natural language prompt and extract scraping parameters
        
        Args:
            prompt: User's natural language scraping request
            
        Returns:
            ExtractedIntent with extracted parameters
        """
        self.logger.info("Processing user prompt", prompt_length=len(prompt))
        
        # Initialize intent object
        intent = ExtractedIntent()
        
        # Extract URLs
        intent.target_urls = self._extract_urls(prompt)
        self.logger.info("Extracted URLs", count=len(intent.target_urls), urls=intent.target_urls)
        
        # Classify scraping type
        intent.scraping_type = self._classify_intent(prompt)
        self.logger.info("Classified intent", type=intent.scraping_type)
        
        # Extract data fields
        intent.data_fields = self._extract_data_fields(prompt)
        self.logger.info("Extracted data fields", fields=intent.data_fields)
        
        # Extract filters
        intent.filters = self._extract_filters(prompt)
        self.logger.info("Extracted filters", filters=intent.filters)
        
        # Determine urgency
        intent.urgency = self._determine_urgency(prompt)
        
        # Estimate volume
        intent.volume_estimate = self._estimate_volume(prompt)
        
        # Determine anti-detection level
        intent.detection_level = self._determine_detection_level(prompt, intent.scraping_type)
        
        # Extract additional parameters
        intent.pagination_limit = self._extract_pagination_limit(prompt)
        intent.date_range = self._extract_date_range(prompt)
        intent.geographic_filter = self._extract_geographic_filter(prompt)
        intent.output_format = self._extract_output_format(prompt)
        
        self.logger.info("Prompt processing completed", intent=intent.to_dict())
        return intent
    
    def _extract_urls(self, prompt: str) -> List[str]:
        """Extract URLs from the prompt"""
        # URL pattern matching
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, prompt)
        
        # Validate and clean URLs
        valid_urls = []
        for url in urls:
            if validate_url(url):
                valid_urls.append(url.strip())
        
        # If no direct URLs found, look for domain mentions
        if not valid_urls:
            domain_pattern = r'(?:from\s+|on\s+|scrape\s+)?([a-zA-Z0-9.-]+\.(?:com|org|net|edu|gov|io|co|uk|de|fr|jp|cn|au|in|br|ca|mx|nl|se|ch|dk|no|fi|pl|ru|za))'
            domains = re.findall(domain_pattern, prompt.lower())
            
            for domain in domains:
                if not domain.startswith(('http://', 'https://')):
                    url = f"https://{domain}"
                    if validate_url(url):
                        valid_urls.append(url)
        
        return valid_urls
    
    def _classify_intent(self, prompt: str) -> str:
        """Classify the scraping intent based on prompt content"""
        prompt_lower = prompt.lower()
        
        # Score each intent type
        intent_scores = {}
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, prompt_lower))
                score += matches
            intent_scores[intent_type] = score
        
        # Return highest scoring intent, default to 'general'
        if intent_scores and max(intent_scores.values()) > 0:
            return max(intent_scores, key=intent_scores.get)
        
        return "general"
    
    def _extract_data_fields(self, prompt: str) -> List[str]:
        """Extract required data fields from the prompt"""
        prompt_lower = prompt.lower()
        extracted_fields = []
        
        # Check for explicit field mentions
        for field, patterns in self.field_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    extracted_fields.append(field)
                    break
        
        # Look for quoted field names
        quoted_fields = re.findall(r'"([^"]+)"', prompt)
        for field in quoted_fields:
            if field.lower() not in [f.lower() for f in extracted_fields]:
                extracted_fields.append(field.lower())
        
        # Look for list patterns
        list_patterns = [
            r'(?:get|extract|scrape|collect)\s+(?:the\s+)?([^.!?]+?)(?:\s+from|\s+data)',
            r'(?:need|want|require)\s+(?:the\s+)?([^.!?]+?)(?:\s+from|\s+data)'
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, prompt_lower)
            for match in matches:
                # Split on commas and 'and'
                items = re.split(r',|\s+and\s+', match.strip())
                for item in items:
                    item = item.strip()
                    if item and len(item.split()) <= 3:  # Reasonable field name length
                        if item not in extracted_fields:
                            extracted_fields.append(item)
        
        # Default fields based on intent type
        if not extracted_fields:
            default_fields = {
                "job_listings": ["title", "company", "location", "salary", "description"],
                "products": ["name", "price", "description", "rating", "availability"],
                "contacts": ["name", "email", "phone", "company", "position"],
                "news": ["title", "author", "date", "content", "url"],
                "real_estate": ["address", "price", "bedrooms", "bathrooms", "sqft"],
                "reviews": ["rating", "review_text", "reviewer", "date"]
            }
            
            intent_type = self._classify_intent(prompt)
            extracted_fields = default_fields.get(intent_type, ["title", "description", "url"])
        
        return list(set(extracted_fields))  # Remove duplicates
    
    def _extract_filters(self, prompt: str) -> Dict[str, Any]:
        """Extract filtering criteria from the prompt"""
        filters = {}
        prompt_lower = prompt.lower()
        
        # Price filters
        price_patterns = [
            r'under\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'less\s+than\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'below\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'max\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'maximum\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                filters['max_price'] = float(match.group(1).replace(',', ''))
                break
        
        # Location filters
        location_patterns = [
            r'in\s+([A-Za-z\s]+?)(?:\s+(?:area|city|state|country))',
            r'from\s+([A-Za-z\s]+?)(?:\s+(?:area|city|state|country))',
            r'located\s+in\s+([A-Za-z\s]+)',
            r'(?:city|location|area):\s*([A-Za-z\s]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                filters['location'] = match.group(1).strip()
                break
        
        # Date filters
        date_patterns = [
            r'posted\s+(?:in\s+)?(?:the\s+)?last\s+(\d+)\s+(day[s]?|week[s]?|month[s]?)',
            r'within\s+(?:the\s+)?last\s+(\d+)\s+(day[s]?|week[s]?|month[s]?)',
            r'from\s+(\d{4}|\d{1,2}/\d{1,2}/\d{4})',
            r'since\s+(\d{4}|\d{1,2}/\d{1,2}/\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                if len(match.groups()) == 2:  # Relative date
                    number, unit = match.groups()
                    filters['date_range'] = f'last_{number}_{unit.rstrip("s")}'
                else:  # Absolute date
                    filters['start_date'] = match.group(1)
                break
        
        # Keyword filters
        keyword_patterns = [
            r'(?:containing|with|including)\s+(?:the\s+)?(?:word[s]?|term[s]?)\s+["\']([^"\']+)["\']',
            r'(?:containing|with|including)\s+["\']([^"\']+)["\']',
            r'keyword[s]?\s*:\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in keyword_patterns:
            matches = re.findall(pattern, prompt_lower)
            if matches:
                filters['keywords'] = matches
                break
        
        # Category filters
        category_patterns = [
            r'category\s*:\s*([A-Za-z\s]+)',
            r'in\s+the\s+([A-Za-z\s]+)\s+category',
            r'(?:type|kind)\s+of\s+([A-Za-z\s]+)'
        ]
        
        for pattern in category_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                filters['category'] = match.group(1).strip()
                break
        
        return filters
    
    def _determine_urgency(self, prompt: str) -> str:
        """Determine urgency level from prompt"""
        prompt_lower = prompt.lower()
        
        for urgency, patterns in self.urgency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    return urgency
        
        return "normal"
    
    def _estimate_volume(self, prompt: str) -> int:
        """Estimate the volume of data to be scraped"""
        # Look for explicit numbers
        volume_patterns = [
            r'(\d+(?:,\d{3})*)\s+(?:records|items|entries|results)',
            r'up\s+to\s+(\d+(?:,\d{3})*)',
            r'maximum\s+of\s+(\d+(?:,\d{3})*)',
            r'limit\s+(?:to\s+)?(\d+(?:,\d{3})*)'
        ]
        
        for pattern in volume_patterns:
            match = re.search(pattern, prompt.lower())
            if match:
                return int(match.group(1).replace(',', ''))
        
        # Estimate based on keywords
        if any(word in prompt.lower() for word in ['all', 'everything', 'complete']):
            return 10000  # Large estimate
        elif any(word in prompt.lower() for word in ['few', 'some', 'sample']):
            return 100   # Small estimate
        
        return 1000  # Default moderate estimate
    
    def _determine_detection_level(self, prompt: str, scraping_type: str) -> str:
        """Determine required anti-detection level"""
        prompt_lower = prompt.lower()
        
        # Explicit mentions
        if any(word in prompt_lower for word in ['stealth', 'undetected', 'careful']):
            return "maximum"
        elif any(word in prompt_lower for word in ['fast', 'quick', 'speed']):
            return "low"
        
        # Based on scraping type
        high_detection_types = ['social_media', 'government', 'financial']
        if scraping_type in high_detection_types:
            return "high"
        
        return "medium"
    
    def _extract_pagination_limit(self, prompt: str) -> Optional[int]:
        """Extract pagination limit if specified"""
        patterns = [
            r'(?:first|only)\s+(\d+)\s+page[s]?',
            r'page[s]?\s+limit\s*:\s*(\d+)',
            r'max\s+(\d+)\s+page[s]?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt.lower())
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_date_range(self, prompt: str) -> Optional[Dict[str, str]]:
        """Extract date range if specified"""
        # This is a simplified implementation
        # In production, would use more sophisticated date parsing
        date_range_pattern = r'from\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})'
        match = re.search(date_range_pattern, prompt)
        
        if match:
            return {
                "start_date": match.group(1),
                "end_date": match.group(2)
            }
        
        return None
    
    def _extract_geographic_filter(self, prompt: str) -> Optional[str]:
        """Extract geographic filtering criteria"""
        geo_patterns = [
            r'in\s+([A-Za-z\s]+?)\s+(?:only|area|region)',
            r'(?:country|region|state)\s*:\s*([A-Za-z\s]+)',
            r'limited\s+to\s+([A-Za-z\s]+)'
        ]
        
        for pattern in geo_patterns:
            match = re.search(pattern, prompt.lower())
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_output_format(self, prompt: str) -> str:
        """Extract desired output format"""
        format_patterns = {
            'csv': [r'csv', r'comma.*separated'],
            'json': [r'json', r'javascript.*object'],
            'excel': [r'excel', r'xls', r'xlsx'],
            'sheets': [r'sheets', r'google.*sheets', r'spreadsheet']
        }
        
        prompt_lower = prompt.lower()
        for format_type, patterns in format_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    return format_type
        
        return "sheets"  # Default to Google Sheets
    
    async def validate_parameters(self, intent: ExtractedIntent) -> ValidationResult:
        """
        Validate extracted parameters for feasibility and compliance
        
        Args:
            intent: Extracted intent parameters
            
        Returns:
            ValidationResult with validation status and recommendations
        """
        self.logger.info("Validating extracted parameters")
        
        result = ValidationResult(valid=True)
        
        # Validate URLs
        if not intent.target_urls:
            result.valid = False
            result.issues.append("No valid URLs found in prompt")
        else:
            for url in intent.target_urls:
                url_validation = await self._validate_url_accessibility(url)
                if not url_validation['accessible']:
                    result.issues.append(f"URL not accessible: {url}")
                
                if url_validation['robots_restricted']:
                    result.warnings.append(f"robots.txt restrictions found for: {url}")
                
                # Legal compliance check
                legal_status = await self._check_legal_compliance(url)
                if legal_status == "prohibited":
                    result.valid = False
                    result.issues.append(f"Scraping prohibited for: {url}")
                elif legal_status == "restricted":
                    result.warnings.append(f"Scraping restricted for: {url}")
        
        # Resource estimation
        result.resource_estimate = self._estimate_resources(intent)
        
        # Check if within free tier limits
        if result.resource_estimate['estimated_duration_minutes'] > 60:
            result.warnings.append("Estimated duration exceeds GitHub Actions free tier limits")
        
        if result.resource_estimate['estimated_memory_mb'] > 512:
            result.warnings.append("Estimated memory usage may exceed limits")
        
        # Suggestions for optimization
        if intent.volume_estimate > 1000:
            result.suggestions.append("Consider using conservative scraping profile for large volumes")
        
        if intent.detection_level == "low" and intent.scraping_type in ['social_media', 'financial']:
            result.suggestions.append("Consider higher anti-detection level for this site type")
        
        self.logger.info("Parameter validation completed", 
                        valid=result.valid, 
                        issues_count=len(result.issues),
                        warnings_count=len(result.warnings))
        
        return result
    
    async def _validate_url_accessibility(self, url: str) -> Dict[str, Any]:
        """Check if URL is accessible and get robots.txt status"""
        try:
            async with aiohttp.ClientSession() as session:
                # Check main URL
                async with session.head(url, timeout=10) as response:
                    accessible = response.status < 400
                
                # Check robots.txt
                robots_url = urljoin(url, '/robots.txt')
                robots_restricted = False
                
                try:
                    async with session.get(robots_url, timeout=5) as robots_response:
                        if robots_response.status == 200:
                            robots_content = await robots_response.text()
                            # Simple robots.txt parsing
                            if 'disallow: /' in robots_content.lower():
                                robots_restricted = True
                except:
                    pass  # robots.txt not found or inaccessible
                
                return {
                    'accessible': accessible,
                    'robots_restricted': robots_restricted,
                    'status_code': response.status
                }
        
        except Exception as e:
            self.logger.warning("URL validation failed", url=url, error=str(e))
            return {
                'accessible': False,
                'robots_restricted': False,
                'error': str(e)
            }
    
    async def _check_legal_compliance(self, url: str) -> str:
        """Basic legal compliance check"""
        domain = urlparse(url).netloc.lower()
        
        # Known problematic domains (this would be expanded in production)
        prohibited_domains = [
            'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com'
        ]
        
        restricted_domains = [
            'amazon.com', 'ebay.com', 'google.com'
        ]
        
        if any(domain.endswith(d) for d in prohibited_domains):
            return "prohibited"
        elif any(domain.endswith(d) for d in restricted_domains):
            return "restricted"
        
        return "allowed"
    
    def _estimate_resources(self, intent: ExtractedIntent) -> Dict[str, Any]:
        """Estimate resource requirements for the scraping task"""
        
        # Base estimates
        pages_per_url = max(1, intent.volume_estimate // len(intent.target_urls)) if intent.target_urls else intent.volume_estimate
        
        # Time estimation (pages per minute based on detection level)
        speed_mapping = {
            "low": 60,      # 60 pages/minute
            "medium": 30,   # 30 pages/minute  
            "high": 15,     # 15 pages/minute
            "maximum": 8    # 8 pages/minute
        }
        
        pages_per_minute = speed_mapping.get(intent.detection_level, 30)
        total_pages = len(intent.target_urls) * pages_per_url
        estimated_duration = total_pages / pages_per_minute
        
        # Memory estimation
        base_memory = 100  # Base browser memory
        per_page_memory = 0.5  # MB per page in memory
        concurrent_pages = min(total_pages, 10)  # Max concurrent pages
        estimated_memory = base_memory + (concurrent_pages * per_page_memory)
        
        return {
            "total_pages": total_pages,
            "estimated_duration_minutes": estimated_duration,
            "estimated_memory_mb": estimated_memory,
            "pages_per_minute": pages_per_minute,
            "concurrent_browsers": min(3, len(intent.target_urls))
        }