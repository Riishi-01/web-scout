"""
Job Board Intelligence Engine

Specialized LLM processing for job board scraping with job-specific 
strategies, salary parsing, and career intelligence.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..llm.hub import LLMHub
from ..utils.logger import ComponentLogger
from ..config.settings import Settings


class JobBoardType(Enum):
    """Job board platform types"""
    INDEED = "indeed"
    LINKEDIN = "linkedin" 
    GLASSDOOR = "glassdoor"
    MONSTER = "monster"
    DICE = "dice"
    STACKOVERFLOW = "stackoverflow"
    ANGELLIST = "angellist"
    REMOTE_CO = "remote_co"
    WEWORKREMOTELY = "weworkremotely"
    GENERIC = "generic"


@dataclass
class JobCriteria:
    """Structured job search criteria"""
    job_title: str
    location: Optional[str] = None
    remote_ok: bool = False
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_level: Optional[str] = None  # entry, mid, senior, executive
    employment_type: Optional[str] = None  # full-time, part-time, contract
    skills_required: List[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    
    def __post_init__(self):
        if self.skills_required is None:
            self.skills_required = []


@dataclass 
class JobPosting:
    """Structured job posting data"""
    title: str
    company: str
    location: str
    salary_range: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_required: Optional[str] = None
    employment_type: Optional[str] = None
    remote_friendly: bool = False
    description: Optional[str] = None
    skills: List[str] = None
    posted_date: Optional[str] = None
    application_url: Optional[str] = None
    quality_score: float = 0.0
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []


class JobIntelligenceEngine:
    """
    Specialized intelligence engine for job board analysis and processing
    """
    
    JOB_PROMPTS = {
        "criteria_extraction": """
You are a job search specialist. Parse this natural language job search request and extract structured criteria.

Request: {user_request}

Extract the following information:
1. Job title/role (required)
2. Location (if specified, or "remote" if remote work mentioned)
3. Salary range (convert to USD annually if possible)
4. Experience level (entry/junior, mid/intermediate, senior, lead/principal, executive)
5. Employment type (full-time, part-time, contract, internship)
6. Required skills/technologies
7. Company preferences (size, industry, culture)
8. Remote work preference

Respond in this JSON format:
{{
    "job_title": "extracted title",
    "location": "location or null",
    "remote_ok": true/false,
    "salary_min": number or null,
    "salary_max": number or null,
    "experience_level": "level or null",
    "employment_type": "type or null", 
    "skills_required": ["skill1", "skill2"],
    "company_size": "startup/small/medium/large or null",
    "industry": "industry or null"
}}
""",
        
        "job_board_strategy": """
You are a web scraping expert specializing in job boards. Generate an optimal scraping strategy for this job board.

Job Board: {job_board}
URL: {target_url}
Search Criteria: {job_criteria}
HTML Sample: {html_sample}

Analyze the job board structure and generate:
1. Search form interaction strategy
2. Job listing selectors (title, company, location, salary)
3. Pagination handling approach
4. Anti-detection measures specific to this platform
5. Data extraction and normalization rules

Focus on:
- Job-specific data fields (salary, benefits, remote status)
- Company information extraction
- Skills and requirements parsing
- Application process detection

Respond in JSON format with detailed selectors and strategy.
""",

        "salary_normalization": """
You are a compensation analyst. Normalize this salary information to a consistent format.

Raw Salary Data: {salary_text}
Location: {location}
Job Level: {experience_level}

Tasks:
1. Extract numeric salary range
2. Convert to annual USD equivalent
3. Account for location cost-of-living if possible
4. Classify salary competitiveness for role level
5. Extract benefits information

Return JSON:
{{
    "salary_min": number,
    "salary_max": number,
    "currency": "USD",
    "period": "annual",
    "benefits": ["benefit1", "benefit2"],
    "competitiveness": "below_market/market_rate/above_market",
    "confidence": 0.0-1.0
}}
""",

        "skills_extraction": """
You are a technical recruiter. Extract and categorize skills from this job posting.

Job Description: {job_description}
Job Title: {job_title}

Extract:
1. Required technical skills
2. Preferred/nice-to-have skills  
3. Soft skills and competencies
4. Years of experience per skill (if mentioned)
5. Skill categories (programming, frameworks, tools, etc.)

Return structured JSON with categorized skills and experience requirements.
""",

        "company_analysis": """
You are a company research analyst. Analyze this company information for job seekers.

Company: {company_name}
Job Posting Context: {job_context}
Additional Info: {company_info}

Provide:
1. Company size estimate
2. Industry and business model
3. Company culture indicators
4. Growth stage (startup, growth, mature, enterprise)
5. Remote work policies
6. Notable benefits or perquisites
7. Reputation indicators

Format as JSON with confidence scores for each assessment.
"""
    }
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm_hub = LLMHub(settings)
        self.logger = ComponentLogger("job_intelligence")
        
        # Job board specific configurations
        self.job_board_configs = self._load_job_board_configs()
        
    def _load_job_board_configs(self) -> Dict[JobBoardType, Dict]:
        """Load job board specific configurations"""
        return {
            JobBoardType.INDEED: {
                "search_form": "#searchform",
                "job_cards": ".jobsearch-SerpJobCard",
                "title_selector": "[data-jk] h2 a span",
                "company_selector": ".companyName",
                "location_selector": ".companyLocation",
                "salary_selector": ".salaryText",
                "pagination": ".np:last-child",
                "base_url": "https://www.indeed.com"
            },
            JobBoardType.LINKEDIN: {
                "search_form": ".jobs-search-box",
                "job_cards": ".job-search-card",
                "title_selector": ".base-search-card__title",
                "company_selector": ".base-search-card__subtitle",
                "location_selector": ".job-search-card__location",
                "salary_selector": ".job-search-card__salary-info",
                "pagination": "[aria-label='Pagination']",
                "base_url": "https://www.linkedin.com"
            },
            JobBoardType.GLASSDOOR: {
                "search_form": "#search-form",
                "job_cards": ".react-job-listing",
                "title_selector": "[data-test='job-title']",
                "company_selector": "[data-test='employer-name']", 
                "location_selector": "[data-test='job-location']",
                "salary_selector": "[data-test='detailSalary']",
                "pagination": ".pagination",
                "base_url": "https://www.glassdoor.com"
            }
        }
    
    async def parse_job_criteria(self, user_request: str) -> JobCriteria:
        """Parse natural language job search request into structured criteria"""
        self.logger.info("Parsing job search criteria", request=user_request[:100])
        
        try:
            prompt = self.JOB_PROMPTS["criteria_extraction"].format(
                user_request=user_request
            )
            
            response = await self.llm_hub.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.1,
                channel="job_intelligence"
            )
            
            # Parse JSON response
            criteria_data = json.loads(response.content)
            
            criteria = JobCriteria(
                job_title=criteria_data.get("job_title", ""),
                location=criteria_data.get("location"),
                remote_ok=criteria_data.get("remote_ok", False),
                salary_min=criteria_data.get("salary_min"),
                salary_max=criteria_data.get("salary_max"),
                experience_level=criteria_data.get("experience_level"),
                employment_type=criteria_data.get("employment_type"),
                skills_required=criteria_data.get("skills_required", []),
                company_size=criteria_data.get("company_size"),
                industry=criteria_data.get("industry")
            )
            
            self.logger.info("Job criteria parsed successfully", criteria=criteria)
            return criteria
            
        except Exception as e:
            self.logger.error("Failed to parse job criteria", error=str(e))
            # Fallback to basic parsing
            return self._fallback_criteria_parsing(user_request)
    
    def _fallback_criteria_parsing(self, user_request: str) -> JobCriteria:
        """Fallback criteria parsing using regex patterns"""
        # Basic regex patterns for common job search terms
        title_patterns = [
            r"(?:looking for|seeking|want|need)\s+(?:a\s+)?(.+?)(?:\s+(?:job|position|role))",
            r"(.+?)\s+(?:job|position|role|developer|engineer|manager)"
        ]
        
        # Extract job title
        job_title = "Software Developer"  # Default
        for pattern in title_patterns:
            match = re.search(pattern, user_request, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
                break
        
        # Check for remote work
        remote_ok = bool(re.search(r"\b(?:remote|work from home|wfh)\b", user_request, re.IGNORECASE))
        
        # Extract salary if mentioned
        salary_pattern = r"\$?(\d+)k?(?:\s*-\s*\$?(\d+)k?)?"
        salary_match = re.search(salary_pattern, user_request)
        salary_min = salary_max = None
        if salary_match:
            salary_min = int(salary_match.group(1)) * 1000
            if salary_match.group(2):
                salary_max = int(salary_match.group(2)) * 1000
        
        return JobCriteria(
            job_title=job_title,
            remote_ok=remote_ok,
            salary_min=salary_min,
            salary_max=salary_max
        )
    
    async def generate_job_board_strategy(
        self, 
        job_board: JobBoardType,
        target_url: str,
        job_criteria: JobCriteria,
        html_sample: str
    ) -> Dict[str, Any]:
        """Generate optimized scraping strategy for specific job board"""
        self.logger.info("Generating job board strategy", 
                        job_board=job_board.value, 
                        url=target_url)
        
        try:
            prompt = self.JOB_PROMPTS["job_board_strategy"].format(
                job_board=job_board.value,
                target_url=target_url,
                job_criteria=json.dumps({
                    "title": job_criteria.job_title,
                    "location": job_criteria.location,
                    "remote": job_criteria.remote_ok,
                    "salary_range": f"${job_criteria.salary_min}-{job_criteria.salary_max}" if job_criteria.salary_min else None
                }),
                html_sample=html_sample[:3000]  # Truncate for token limits
            )
            
            response = await self.llm_hub.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1,
                channel="job_strategy"
            )
            
            strategy = json.loads(response.content)
            
            # Merge with predefined job board config
            if job_board in self.job_board_configs:
                base_config = self.job_board_configs[job_board]
                strategy.update(base_config)
            
            return strategy
            
        except Exception as e:
            self.logger.error("Failed to generate job board strategy", error=str(e))
            return self._get_default_strategy(job_board)
    
    def _get_default_strategy(self, job_board: JobBoardType) -> Dict[str, Any]:
        """Get default strategy for job board"""
        if job_board in self.job_board_configs:
            return self.job_board_configs[job_board]
        
        return {
            "job_cards": ".job",
            "title_selector": ".job-title",
            "company_selector": ".company",
            "location_selector": ".location",
            "salary_selector": ".salary",
            "pagination": ".next"
        }
    
    async def normalize_salary(
        self, 
        salary_text: str,
        location: Optional[str] = None,
        experience_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Normalize salary information to consistent format"""
        self.logger.info("Normalizing salary data", salary=salary_text)
        
        try:
            prompt = self.JOB_PROMPTS["salary_normalization"].format(
                salary_text=salary_text,
                location=location or "Unknown",
                experience_level=experience_level or "Unknown"
            )
            
            response = await self.llm_hub.generate(
                prompt=prompt,
                max_tokens=300,
                temperature=0.1,
                channel="salary_analysis"
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error("Failed to normalize salary", error=str(e))
            return self._fallback_salary_parsing(salary_text)
    
    def _fallback_salary_parsing(self, salary_text: str) -> Dict[str, Any]:
        """Fallback salary parsing using regex"""
        # Extract numbers from salary text
        numbers = re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', salary_text.replace(',', ''))
        
        if not numbers:
            return {"salary_min": None, "salary_max": None, "confidence": 0.0}
        
        # Convert to integers
        nums = [int(float(n.replace(',', ''))) for n in numbers]
        
        # Determine if hourly, monthly, or annual
        if 'hour' in salary_text.lower():
            # Convert hourly to annual (40 hours/week * 52 weeks)
            nums = [n * 40 * 52 for n in nums]
        elif 'month' in salary_text.lower():
            # Convert monthly to annual
            nums = [n * 12 for n in nums]
        
        # Handle ranges
        if len(nums) >= 2:
            return {
                "salary_min": min(nums),
                "salary_max": max(nums),
                "currency": "USD",
                "period": "annual",
                "confidence": 0.7
            }
        elif len(nums) == 1:
            return {
                "salary_min": nums[0],
                "salary_max": nums[0],
                "currency": "USD", 
                "period": "annual",
                "confidence": 0.6
            }
        
        return {"salary_min": None, "salary_max": None, "confidence": 0.0}
    
    async def extract_skills(self, job_description: str, job_title: str) -> Dict[str, List[str]]:
        """Extract and categorize skills from job description"""
        self.logger.info("Extracting skills from job posting")
        
        try:
            prompt = self.JOB_PROMPTS["skills_extraction"].format(
                job_description=job_description[:2000],  # Truncate for token limits
                job_title=job_title
            )
            
            response = await self.llm_hub.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.1,
                channel="skills_analysis"
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error("Failed to extract skills", error=str(e))
            return self._fallback_skills_extraction(job_description)
    
    def _fallback_skills_extraction(self, job_description: str) -> Dict[str, List[str]]:
        """Fallback skills extraction using predefined patterns"""
        # Common technical skills patterns
        tech_skills = [
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'Swift',
            'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'Spring',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'SQL', 'MongoDB',
            'Git', 'CI/CD', 'DevOps', 'Machine Learning', 'AI', 'TensorFlow'
        ]
        
        found_skills = []
        description_lower = job_description.lower()
        
        for skill in tech_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)
        
        return {
            "required_skills": found_skills[:10],  # Limit results
            "preferred_skills": [],
            "soft_skills": [],
            "confidence": 0.5
        }
    
    async def analyze_company(
        self, 
        company_name: str,
        job_context: str,
        company_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze company information for job seekers"""
        self.logger.info("Analyzing company information", company=company_name)
        
        try:
            prompt = self.JOB_PROMPTS["company_analysis"].format(
                company_name=company_name,
                job_context=job_context,
                company_info=company_info or "No additional information"
            )
            
            response = await self.llm_hub.generate(
                prompt=prompt,
                max_tokens=400,
                temperature=0.1,
                channel="company_analysis"
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error("Failed to analyze company", error=str(e))
            return {
                "company_size": "Unknown",
                "industry": "Unknown",
                "growth_stage": "Unknown",
                "confidence": 0.0
            }
    
    def detect_job_board_type(self, url: str) -> JobBoardType:
        """Detect job board type from URL"""
        url_lower = url.lower()
        
        if 'indeed.com' in url_lower:
            return JobBoardType.INDEED
        elif 'linkedin.com' in url_lower:
            return JobBoardType.LINKEDIN
        elif 'glassdoor.com' in url_lower:
            return JobBoardType.GLASSDOOR
        elif 'monster.com' in url_lower:
            return JobBoardType.MONSTER
        elif 'dice.com' in url_lower:
            return JobBoardType.DICE
        elif 'stackoverflow.com' in url_lower:
            return JobBoardType.STACKOVERFLOW
        elif 'angel.co' in url_lower or 'wellfound.com' in url_lower:
            return JobBoardType.ANGELLIST
        elif 'remote.co' in url_lower:
            return JobBoardType.REMOTE_CO
        elif 'weworkremotely.com' in url_lower:
            return JobBoardType.WEWORKREMOTELY
        else:
            return JobBoardType.GENERIC