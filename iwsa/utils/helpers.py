"""
Helper utilities for IWSA
"""

import time
import uuid
import asyncio
import functools
from typing import Any, Callable, Optional, Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

logger = structlog.get_logger(__name__)


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique identifier
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique identifier string
    """
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}" if prefix else unique_id


def measure_time(func: Callable) -> Callable:
    """
    Decorator to measure function execution time
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function that logs execution time
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} completed", 
                       execution_time_seconds=execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed", 
                        execution_time_seconds=execution_time,
                        error=str(e))
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} completed", 
                       execution_time_seconds=execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed", 
                        execution_time_seconds=execution_time,
                        error=str(e))
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    exponential_base: float = 2,
    retry_exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries
        max_wait: Maximum wait time between retries
        exponential_base: Base for exponential backoff
        retry_exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=min_wait, max=max_wait, exp_base=exponential_base),
            retry=retry_if_exception_type(retry_exceptions),
            reraise=True
        )
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=min_wait, max=max_wait, exp_base=exponential_base),
            retry=retry_if_exception_type(retry_exceptions),
            reraise=True
        )
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RateLimiter:
    """Simple rate limiter for API calls and requests"""
    
    def __init__(self, calls_per_second: float = 1.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0
    
    async def acquire(self):
        """Wait if necessary to respect rate limit"""
        now = time.time()
        time_since_last = now - self.last_call
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_call = time.time()
    
    def set_rate(self, calls_per_second: float):
        """Update the rate limit"""
        self.min_interval = 1.0 / calls_per_second


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def safe_get(dictionary: Dict[str, Any], keys: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value using dot notation
    
    Args:
        dictionary: Dictionary to search
        keys: Dot-separated key path (e.g., 'user.profile.name')
        default: Default value if key not found
        
    Returns:
        Value at key path or default
    """
    try:
        value = dictionary
        for key in keys.split('.'):
            value = value[key]
        return value
    except (KeyError, TypeError, AttributeError):
        return default


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries, with later dicts taking precedence
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        sanitized = f"{name[:max_name_length]}.{ext}" if ext else name[:255]
    
    return sanitized or 'untitled'


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes value in human readable format
    
    Args:
        bytes_value: Bytes value
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds:.1f}s"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours < 24:
        return f"{hours}h {remaining_minutes}m"
    
    days = hours // 24
    remaining_hours = hours % 24
    
    return f"{days}d {remaining_hours}h"


class AsyncBatch:
    """Utility for batching async operations"""
    
    def __init__(self, batch_size: int = 10, delay: float = 0.1):
        self.batch_size = batch_size
        self.delay = delay
    
    async def process(self, 
                     items: List[Any], 
                     processor: Callable, 
                     *args, **kwargs) -> List[Any]:
        """
        Process items in batches
        
        Args:
            items: Items to process
            processor: Async function to process each item
            *args, **kwargs: Additional arguments for processor
            
        Returns:
            List of results
        """
        results = []
        
        for batch in chunk_list(items, self.batch_size):
            # Process batch concurrently
            batch_tasks = [
                processor(item, *args, **kwargs) 
                for item in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Delay between batches
            if self.delay > 0:
                await asyncio.sleep(self.delay)
        
        return results


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate string similarity using simple ratio
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    if not str1 and not str2:
        return 1.0
    if not str1 or not str2:
        return 0.0
    
    # Simple implementation - in production would use more sophisticated algorithms
    str1_lower = str1.lower()
    str2_lower = str2.lower()
    
    if str1_lower == str2_lower:
        return 1.0
    
    # Character-based similarity
    set1 = set(str1_lower)
    set2 = set(str2_lower)
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0