"""
Logging configuration and utilities for IWSA
"""

import os
import sys
import logging
import structlog
from typing import Any, Dict
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_file: str = None) -> structlog.stdlib.BoundLogger:
    """
    Setup structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    
    Returns:
        Configured logger instance
    """
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Create logs directory if logging to file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Setup file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
    
    logger = structlog.get_logger("iwsa")
    logger.info("Logging initialized", level=log_level, file=log_file)
    
    return logger


def get_logger(name: str = "iwsa") -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance for a specific component
    
    Args:
        name: Name of the logger/component
    
    Returns:
        Logger instance
    """
    return structlog.get_logger(name)


class PerformanceLogger:
    """Logger for performance metrics and monitoring"""
    
    def __init__(self, logger: structlog.stdlib.BoundLogger = None):
        self.logger = logger or get_logger("performance")
        self.metrics = {}
    
    def log_extraction_metrics(self, 
                             url: str,
                             pages_scraped: int, 
                             records_extracted: int,
                             duration: float,
                             success_rate: float,
                             error_count: int):
        """Log extraction performance metrics"""
        
        pages_per_minute = (pages_scraped / duration) * 60 if duration > 0 else 0
        records_per_minute = (records_extracted / duration) * 60 if duration > 0 else 0
        
        self.logger.info(
            "extraction_completed",
            url=url,
            pages_scraped=pages_scraped,
            records_extracted=records_extracted,
            duration_seconds=duration,
            pages_per_minute=pages_per_minute,
            records_per_minute=records_per_minute,
            success_rate=success_rate,
            error_count=error_count
        )
        
        # Store metrics for aggregation
        self.metrics[url] = {
            "timestamp": datetime.utcnow().isoformat(),
            "pages_scraped": pages_scraped,
            "records_extracted": records_extracted,
            "duration": duration,
            "pages_per_minute": pages_per_minute,
            "records_per_minute": records_per_minute,
            "success_rate": success_rate,
            "error_count": error_count
        }
    
    def log_llm_metrics(self,
                       provider: str,
                       channel: str,
                       tokens_used: int,
                       response_time: float,
                       success: bool,
                       cost: float = None):
        """Log LLM usage metrics"""
        
        self.logger.info(
            "llm_request_completed",
            provider=provider,
            channel=channel,
            tokens_used=tokens_used,
            response_time_seconds=response_time,
            success=success,
            cost_usd=cost
        )
    
    def log_error_metrics(self,
                         error_type: str,
                         error_message: str,
                         component: str,
                         context: Dict[str, Any] = None):
        """Log error metrics for monitoring"""
        
        self.logger.error(
            "error_occurred",
            error_type=error_type,
            error_message=error_message,
            component=component,
            context=context or {}
        )
    
    def log_resource_usage(self,
                          memory_mb: float,
                          cpu_percent: float,
                          active_browsers: int,
                          concurrent_requests: int):
        """Log resource usage metrics"""
        
        self.logger.info(
            "resource_usage",
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            active_browsers=active_browsers,
            concurrent_requests=concurrent_requests
        )
    
    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics for reporting"""
        
        if not self.metrics:
            return {}
        
        total_pages = sum(m["pages_scraped"] for m in self.metrics.values())
        total_records = sum(m["records_extracted"] for m in self.metrics.values())
        total_duration = sum(m["duration"] for m in self.metrics.values())
        avg_success_rate = sum(m["success_rate"] for m in self.metrics.values()) / len(self.metrics)
        total_errors = sum(m["error_count"] for m in self.metrics.values())
        
        return {
            "total_urls_processed": len(self.metrics),
            "total_pages_scraped": total_pages,
            "total_records_extracted": total_records,
            "total_duration_seconds": total_duration,
            "average_success_rate": avg_success_rate,
            "total_errors": total_errors,
            "overall_pages_per_minute": (total_pages / total_duration) * 60 if total_duration > 0 else 0,
            "overall_records_per_minute": (total_records / total_duration) * 60 if total_duration > 0 else 0
        }


class ComponentLogger:
    """Context-aware logger for different IWSA components"""
    
    def __init__(self, component_name: str):
        self.component = component_name
        self.logger = get_logger(component_name)
    
    def info(self, message: str, **kwargs):
        """Log info message with component context"""
        self.logger.info(message, component=self.component, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with component context"""
        self.logger.debug(message, component=self.component, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with component context"""
        self.logger.warning(message, component=self.component, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with component context"""
        self.logger.error(message, component=self.component, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with component context"""
        self.logger.critical(message, component=self.component, **kwargs)