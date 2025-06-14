"""
Job Board Specialization Module

This module provides specialized functionality for job board scraping,
including job-specific intelligence, templates, and processing capabilities.
"""

from .job_intelligence import JobIntelligenceEngine
from .job_templates import JobBoardTemplateManager
from .job_parser import JobCriteriaParser
from .job_quality import JobQualityAssessor

__all__ = [
    'JobIntelligenceEngine',
    'JobBoardTemplateManager', 
    'JobCriteriaParser',
    'JobQualityAssessor'
]