"""
Job Criteria Parser

Advanced parsing of natural language job search requests with
intelligent extraction of criteria, filters, and preferences.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from .job_intelligence import JobCriteria, JobBoardType
from ..utils.logger import ComponentLogger


@dataclass
class ParsedJobRequest:
    """Result of parsing a job search request"""
    job_criteria: JobCriteria
    confidence: float
    extracted_entities: Dict[str, Any]
    ambiguous_terms: List[str]
    suggestions: List[str]
    original_request: str


class JobCriteriaParser:
    """
    Intelligent parser for natural language job search requests
    """
    
    # Predefined patterns for common job search terms
    JOB_TITLE_PATTERNS = [
        r"(?:looking for|seeking|want|need|find|search for)\s+(?:a\s+)?(.+?)(?:\s+(?:job|position|role|work))",
        r"(.+?)\s+(?:job|position|role|opening|opportunity)",
        r"(?:hire|hiring)\s+(.+?)(?:\s|$)",
        r"(.+?)\s+(?:developer|engineer|manager|analyst|designer|specialist)"
    ]
    
    LOCATION_PATTERNS = [
        r"(?:in|at|near|around)\s+([A-Za-z\s,]+?)(?:\s+(?:area|region|city|state))?",
        r"location[:\s]+([A-Za-z\s,]+)",
        r"([A-Za-z\s,]+)\s+(?:area|region|city|state)"
    ]
    
    SALARY_PATTERNS = [
        r"\$(\d+)k?(?:\s*-\s*\$?(\d+)k?)?\s*(?:per\s+)?(?:year|annually|yearly|k|thousand)?",
        r"(\d+)k?\s*-\s*(\d+)k?\s*(?:per\s+)?(?:year|annually|yearly|k|thousand)",
        r"salary[:\s]+\$?(\d+)k?(?:\s*-\s*\$?(\d+)k?)?",
        r"(?:pay|compensation)[:\s]+\$?(\d+)k?(?:\s*-\s*\$?(\d+)k?)?"
    ]
    
    EXPERIENCE_PATTERNS = [
        r"(?:(\d+)[\+\-\s]*(?:years?|yrs?)\s+(?:of\s+)?experience)",
        r"(?:experience[:\s]+(\d+)[\+\-\s]*(?:years?|yrs?))",
        r"\b(entry[-\s]?level|junior|mid[-\s]?level|senior|lead|principal|executive)\b",
        r"\b(intern|internship|graduate|new grad)\b"
    ]
    
    EMPLOYMENT_TYPE_PATTERNS = [
        r"\b(full[-\s]?time|part[-\s]?time|contract|freelance|temporary|permanent)\b",
        r"\b(hourly|salaried)\b",
        r"\b(w2|1099|corp[-\s]?to[-\s]?corp|c2c)\b"
    ]
    
    REMOTE_PATTERNS = [
        r"\b(remote|work from home|wfh|distributed|virtual)\b",
        r"\b(hybrid|flexible|on[-\s]?site|office)\b",
        r"(?:work\s+)?(?:from\s+)?(?:home|anywhere)"
    ]
    
    SKILL_PATTERNS = [
        # Programming languages
        r"\b(python|java|javascript|typescript|c\+\+|c#|go|rust|swift|kotlin|scala|ruby|php|r|matlab)\b",
        # Frameworks and libraries
        r"\b(react|angular|vue|node\.?js|django|flask|spring|laravel|rails|express)\b",
        # Databases
        r"\b(sql|mysql|postgresql|postgres|mongodb|redis|elasticsearch|oracle|sqlite)\b",
        # Cloud platforms
        r"\b(aws|azure|gcp|google cloud|amazon web services|microsoft azure)\b",
        # Tools and technologies
        r"\b(docker|kubernetes|jenkins|git|gitlab|github|jira|confluence|slack)\b",
        # Methodologies
        r"\b(agile|scrum|devops|ci/cd|tdd|microservices|api)\b"
    ]
    
    COMPANY_SIZE_PATTERNS = [
        r"\b(startup|small company|large company|enterprise|fortune 500)\b",
        r"(?:company with\s+)?(?:(\d+)[\+\-\s]*(?:employees?|people))",
        r"\b(early[-\s]?stage|growth[-\s]?stage|mature|established)\b"
    ]
    
    INDUSTRY_PATTERNS = [
        r"\b(fintech|healthcare|edtech|e[-\s]?commerce|saas|gaming|social media)\b",
        r"\b(finance|technology|tech|healthcare|education|retail|manufacturing)\b",
        r"\b(banking|insurance|consulting|media|entertainment|government)\b"
    ]
    
    def __init__(self):
        self.logger = ComponentLogger("job_parser")
        
        # Pre-compiled regex patterns for better performance
        self._compile_patterns()
        
        # Common job titles and variations
        self.job_title_synonyms = {
            'software engineer': ['developer', 'programmer', 'software dev', 'swe'],
            'data scientist': ['data analyst', 'ml engineer', 'data engineer'],
            'product manager': ['pm', 'product owner', 'product lead'],
            'devops engineer': ['site reliability engineer', 'sre', 'platform engineer'],
            'frontend developer': ['front-end developer', 'ui developer', 'frontend engineer'],
            'backend developer': ['back-end developer', 'backend engineer', 'api developer'],
            'full stack developer': ['fullstack developer', 'full-stack engineer']
        }
        
        # Experience level mappings
        self.experience_mappings = {
            'intern': 'entry',
            'internship': 'entry', 
            'graduate': 'entry',
            'new grad': 'entry',
            'entry-level': 'entry',
            'entry level': 'entry',
            'junior': 'entry',
            'mid-level': 'mid',
            'mid level': 'mid',
            'intermediate': 'mid',
            'senior': 'senior',
            'lead': 'senior',
            'principal': 'senior',
            'staff': 'senior',
            'executive': 'executive',
            'director': 'executive',
            'vp': 'executive'
        }
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        self.compiled_patterns = {
            'job_title': [re.compile(pattern, re.IGNORECASE) for pattern in self.JOB_TITLE_PATTERNS],
            'location': [re.compile(pattern, re.IGNORECASE) for pattern in self.LOCATION_PATTERNS],
            'salary': [re.compile(pattern, re.IGNORECASE) for pattern in self.SALARY_PATTERNS],
            'experience': [re.compile(pattern, re.IGNORECASE) for pattern in self.EXPERIENCE_PATTERNS],
            'employment': [re.compile(pattern, re.IGNORECASE) for pattern in self.EMPLOYMENT_TYPE_PATTERNS],
            'remote': [re.compile(pattern, re.IGNORECASE) for pattern in self.REMOTE_PATTERNS],
            'skills': [re.compile(pattern, re.IGNORECASE) for pattern in self.SKILL_PATTERNS],
            'company_size': [re.compile(pattern, re.IGNORECASE) for pattern in self.COMPANY_SIZE_PATTERNS],
            'industry': [re.compile(pattern, re.IGNORECASE) for pattern in self.INDUSTRY_PATTERNS]
        }
    
    def parse_job_request(self, request: str) -> ParsedJobRequest:
        """
        Parse natural language job search request into structured criteria
        """
        self.logger.info("Parsing job search request", request=request[:100])
        
        request_clean = self._clean_request(request)
        
        # Extract all entities
        extracted_entities = {}
        
        # Extract job title
        job_title, title_confidence = self._extract_job_title(request_clean)
        extracted_entities['job_title'] = {'value': job_title, 'confidence': title_confidence}
        
        # Extract location
        location, location_confidence = self._extract_location(request_clean)
        extracted_entities['location'] = {'value': location, 'confidence': location_confidence}
        
        # Extract salary information
        salary_min, salary_max, salary_confidence = self._extract_salary(request_clean)
        extracted_entities['salary'] = {
            'min': salary_min, 
            'max': salary_max, 
            'confidence': salary_confidence
        }
        
        # Extract experience level
        experience_level, exp_confidence = self._extract_experience(request_clean)
        extracted_entities['experience'] = {'value': experience_level, 'confidence': exp_confidence}
        
        # Extract employment type
        employment_type, emp_confidence = self._extract_employment_type(request_clean)
        extracted_entities['employment_type'] = {'value': employment_type, 'confidence': emp_confidence}
        
        # Extract remote preference
        remote_ok, remote_confidence = self._extract_remote_preference(request_clean)
        extracted_entities['remote'] = {'value': remote_ok, 'confidence': remote_confidence}
        
        # Extract skills
        skills, skills_confidence = self._extract_skills(request_clean)
        extracted_entities['skills'] = {'value': skills, 'confidence': skills_confidence}
        
        # Extract company preferences
        company_size, industry, company_confidence = self._extract_company_preferences(request_clean)
        extracted_entities['company'] = {
            'size': company_size,
            'industry': industry,
            'confidence': company_confidence
        }
        
        # Create job criteria
        job_criteria = JobCriteria(
            job_title=job_title,
            location=location,
            remote_ok=remote_ok,
            salary_min=salary_min,
            salary_max=salary_max,
            experience_level=experience_level,
            employment_type=employment_type,
            skills_required=skills,
            company_size=company_size,
            industry=industry
        )
        
        # Calculate overall confidence
        confidences = [
            title_confidence,
            location_confidence if location else 0.8,  # Don't penalize for no location
            salary_confidence if salary_min else 0.7,   # Don't penalize for no salary
            exp_confidence,
            remote_confidence,
            skills_confidence
        ]
        overall_confidence = sum(confidences) / len(confidences)
        
        # Identify ambiguous terms and suggestions
        ambiguous_terms = self._identify_ambiguous_terms(request_clean, extracted_entities)
        suggestions = self._generate_suggestions(job_criteria, extracted_entities)
        
        result = ParsedJobRequest(
            job_criteria=job_criteria,
            confidence=overall_confidence,
            extracted_entities=extracted_entities,
            ambiguous_terms=ambiguous_terms,
            suggestions=suggestions,
            original_request=request
        )
        
        self.logger.info("Job request parsed", 
                        job_title=job_title,
                        confidence=overall_confidence,
                        ambiguous_count=len(ambiguous_terms))
        
        return result
    
    def _clean_request(self, request: str) -> str:
        """Clean and normalize the request text"""
        # Remove extra whitespace
        request = re.sub(r'\s+', ' ', request.strip())
        
        # Normalize common abbreviations
        replacements = {
            r'\bswe\b': 'software engineer',
            r'\bpm\b': 'product manager', 
            r'\bsre\b': 'site reliability engineer',
            r'\bml\b': 'machine learning',
            r'\bai\b': 'artificial intelligence',
            r'\bui\b': 'user interface',
            r'\bux\b': 'user experience',
            r'\bapi\b': 'application programming interface'
        }
        
        for pattern, replacement in replacements.items():
            request = re.sub(pattern, replacement, request, flags=re.IGNORECASE)
        
        return request
    
    def _extract_job_title(self, request: str) -> Tuple[str, float]:
        """Extract job title from request"""
        for pattern in self.compiled_patterns['job_title']:
            match = pattern.search(request)
            if match:
                title = match.group(1).strip()
                title = self._normalize_job_title(title)
                return title, 0.9
        
        # Fallback: look for common job titles anywhere in text
        for main_title, synonyms in self.job_title_synonyms.items():
            if main_title in request.lower():
                return main_title.title(), 0.8
            for synonym in synonyms:
                if synonym in request.lower():
                    return main_title.title(), 0.7
        
        # Last resort: extract first meaningful noun phrase
        words = request.split()
        for i, word in enumerate(words):
            if word.lower() in ['engineer', 'developer', 'manager', 'analyst', 'designer']:
                if i > 0:
                    return f"{words[i-1].title()} {word.title()}", 0.5
                return word.title(), 0.4
        
        return "Software Developer", 0.3  # Default fallback
    
    def _normalize_job_title(self, title: str) -> str:
        """Normalize job title to standard format"""
        title = title.lower().strip()
        
        # Check against known synonyms
        for main_title, synonyms in self.job_title_synonyms.items():
            if title == main_title or title in synonyms:
                return main_title.title()
        
        # Basic normalization
        title = re.sub(r'\b(dev|eng)\b', lambda m: 'developer' if m.group(1) == 'dev' else 'engineer', title)
        title = re.sub(r'\bjr\b', 'junior', title)
        title = re.sub(r'\bsr\b', 'senior', title)
        
        return title.title()
    
    def _extract_location(self, request: str) -> Tuple[Optional[str], float]:
        """Extract location from request"""
        for pattern in self.compiled_patterns['location']:
            match = pattern.search(request)
            if match:
                location = match.group(1).strip()
                location = self._normalize_location(location)
                return location, 0.8
        
        return None, 0.8  # No location specified is often intentional
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location string"""
        # Remove common words
        location = re.sub(r'\b(area|region|city|state)\b', '', location, flags=re.IGNORECASE)
        return location.strip().title()
    
    def _extract_salary(self, request: str) -> Tuple[Optional[int], Optional[int], float]:
        """Extract salary range from request"""
        for pattern in self.compiled_patterns['salary']:
            match = pattern.search(request)
            if match:
                min_salary = int(match.group(1))
                max_salary = int(match.group(2)) if match.group(2) else None
                
                # Convert k notation to thousands
                if 'k' in match.group(0).lower() or min_salary < 1000:
                    min_salary *= 1000
                    if max_salary:
                        max_salary *= 1000
                
                return min_salary, max_salary, 0.8
        
        return None, None, 0.7  # No salary often acceptable
    
    def _extract_experience(self, request: str) -> Tuple[Optional[str], float]:
        """Extract experience level from request"""
        # Check for specific year requirements
        for pattern in self.compiled_patterns['experience']:
            match = pattern.search(request)
            if match:
                if match.group(1) and match.group(1).isdigit():
                    years = int(match.group(1))
                    if years <= 2:
                        return 'entry', 0.9
                    elif years <= 5:
                        return 'mid', 0.9
                    else:
                        return 'senior', 0.9
                else:
                    # Look for level keywords
                    level_text = match.group(0).lower()
                    for keyword, level in self.experience_mappings.items():
                        if keyword in level_text:
                            return level, 0.8
        
        return None, 0.6  # No experience level often acceptable
    
    def _extract_employment_type(self, request: str) -> Tuple[Optional[str], float]:
        """Extract employment type from request"""
        for pattern in self.compiled_patterns['employment']:
            match = pattern.search(request)
            if match:
                emp_type = match.group(1).lower().replace('-', '').replace(' ', '')
                
                type_mappings = {
                    'fulltime': 'full-time',
                    'parttime': 'part-time',
                    'contract': 'contract',
                    'freelance': 'freelance',
                    'temporary': 'temporary',
                    'permanent': 'full-time'
                }
                
                return type_mappings.get(emp_type, emp_type), 0.8
        
        return 'full-time', 0.6  # Default to full-time
    
    def _extract_remote_preference(self, request: str) -> Tuple[bool, float]:
        """Extract remote work preference"""
        remote_score = 0
        total_matches = 0
        
        for pattern in self.compiled_patterns['remote']:
            matches = pattern.findall(request)
            for match in matches:
                total_matches += 1
                if match.lower() in ['remote', 'work from home', 'wfh', 'distributed', 'virtual']:
                    remote_score += 1
                elif match.lower() in ['hybrid', 'flexible']:
                    remote_score += 0.5
                elif match.lower() in ['on-site', 'onsite', 'office']:
                    remote_score -= 1
        
        if total_matches == 0:
            return False, 0.7  # No preference stated
        
        remote_preference = remote_score > 0
        confidence = min(0.9, 0.5 + abs(remote_score) * 0.2)
        
        return remote_preference, confidence
    
    def _extract_skills(self, request: str) -> Tuple[List[str], float]:
        """Extract technical skills from request"""
        found_skills = []
        
        for pattern in self.compiled_patterns['skills']:
            matches = pattern.findall(request)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # Normalize skill name
                skill = match.lower()
                skill_normalized = self._normalize_skill(skill)
                
                if skill_normalized not in found_skills:
                    found_skills.append(skill_normalized)
        
        confidence = 0.8 if found_skills else 0.6
        return found_skills, confidence
    
    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill name"""
        normalizations = {
            'javascript': 'JavaScript',
            'typescript': 'TypeScript', 
            'nodejs': 'Node.js',
            'node.js': 'Node.js',
            'reactjs': 'React',
            'vuejs': 'Vue.js',
            'angularjs': 'Angular',
            'postgresql': 'PostgreSQL',
            'postgres': 'PostgreSQL',
            'mongodb': 'MongoDB',
            'mysql': 'MySQL',
            'c++': 'C++',
            'c#': 'C#'
        }
        
        return normalizations.get(skill.lower(), skill.title())
    
    def _extract_company_preferences(self, request: str) -> Tuple[Optional[str], Optional[str], float]:
        """Extract company size and industry preferences"""
        company_size = None
        industry = None
        confidence = 0.6
        
        # Extract company size
        for pattern in self.compiled_patterns['company_size']:
            match = pattern.search(request)
            if match:
                size_text = match.group(0).lower()
                if 'startup' in size_text or 'early' in size_text:
                    company_size = 'startup'
                elif 'small' in size_text:
                    company_size = 'small'
                elif 'large' in size_text or 'enterprise' in size_text or 'fortune' in size_text:
                    company_size = 'large'
                else:
                    company_size = 'medium'
                confidence = 0.8
                break
        
        # Extract industry
        for pattern in self.compiled_patterns['industry']:
            match = pattern.search(request)
            if match:
                industry = match.group(1).lower()
                confidence = max(confidence, 0.7)
                break
        
        return company_size, industry, confidence
    
    def _identify_ambiguous_terms(self, request: str, extracted_entities: Dict) -> List[str]:
        """Identify terms that could be interpreted multiple ways"""
        ambiguous = []
        
        # Check for vague job titles
        if extracted_entities['job_title']['confidence'] < 0.6:
            ambiguous.append("job title unclear")
        
        # Check for ambiguous experience levels
        if 'mid' in request.lower() and 'senior' in request.lower():
            ambiguous.append("experience level ambiguous")
        
        # Check for conflicting remote preferences
        if 'remote' in request.lower() and 'office' in request.lower():
            ambiguous.append("work location preference unclear")
        
        return ambiguous
    
    def _generate_suggestions(self, criteria: JobCriteria, entities: Dict) -> List[str]:
        """Generate suggestions to improve the search"""
        suggestions = []
        
        # Suggest adding location if missing
        if not criteria.location and not criteria.remote_ok:
            suggestions.append("Consider specifying a location or indicating remote work preference")
        
        # Suggest adding salary range if missing
        if not criteria.salary_min:
            suggestions.append("Consider adding salary expectations for better matching")
        
        # Suggest adding experience level if missing
        if not criteria.experience_level:
            suggestions.append("Specify experience level (entry, mid, senior) for more targeted results")
        
        # Suggest adding skills if few found
        if len(criteria.skills_required) < 2:
            suggestions.append("Add specific technical skills or technologies you want to work with")
        
        # Suggest job board recommendations
        if criteria.remote_ok:
            suggestions.append("Consider searching on remote-focused job boards like Remote.co")
        
        if any(skill.lower() in ['python', 'javascript', 'java'] for skill in criteria.skills_required):
            suggestions.append("Tech-focused boards like Stack Overflow Jobs or Dice might have good matches")
        
        return suggestions
    
    def enhance_criteria_with_synonyms(self, criteria: JobCriteria) -> JobCriteria:
        """Enhance job criteria with synonyms and related terms"""
        enhanced_criteria = JobCriteria(
            job_title=criteria.job_title,
            location=criteria.location,
            remote_ok=criteria.remote_ok,
            salary_min=criteria.salary_min,
            salary_max=criteria.salary_max,
            experience_level=criteria.experience_level,
            employment_type=criteria.employment_type,
            skills_required=criteria.skills_required.copy(),
            company_size=criteria.company_size,
            industry=criteria.industry
        )
        
        # Add skill synonyms
        skill_synonyms = {
            'JavaScript': ['JS', 'ECMAScript'],
            'Python': ['Python3'],
            'React': ['ReactJS', 'React.js'],
            'Node.js': ['NodeJS', 'Node'],
            'Machine Learning': ['ML', 'AI', 'Artificial Intelligence'],
            'DevOps': ['CI/CD', 'Continuous Integration'],
            'PostgreSQL': ['Postgres', 'PostGIS']
        }
        
        for skill in criteria.skills_required:
            if skill in skill_synonyms:
                for synonym in skill_synonyms[skill]:
                    if synonym not in enhanced_criteria.skills_required:
                        enhanced_criteria.skills_required.append(synonym)
        
        return enhanced_criteria