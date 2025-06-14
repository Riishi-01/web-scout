"""
Job Board Template System

Pre-built templates and configurations for major job boards with
optimized scraping strategies and selectors.
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from .job_intelligence import JobBoardType, JobCriteria
from ..utils.logger import ComponentLogger


@dataclass
class JobBoardTemplate:
    """Template configuration for a specific job board"""
    name: str
    job_board_type: JobBoardType
    base_url: str
    search_url_pattern: str
    
    # Search form configuration
    search_form_selector: str
    job_title_input: str
    location_input: str
    search_button: str
    
    # Job listing selectors
    job_cards_selector: str
    title_selector: str
    company_selector: str
    location_selector: str
    salary_selector: str
    description_selector: Optional[str] = None
    posted_date_selector: Optional[str] = None
    application_url_selector: Optional[str] = None
    
    # Pagination
    pagination_selector: str
    next_button_selector: str
    
    # Anti-detection settings
    rate_limit_delay: float = 2.0
    user_agent_rotation: bool = True
    proxy_rotation: bool = False
    
    # Job board specific features
    remote_filter_selector: Optional[str] = None
    salary_filter_selector: Optional[str] = None
    experience_filter_selector: Optional[str] = None
    employment_type_filter: Optional[str] = None
    
    # Additional metadata
    requires_login: bool = False
    captcha_likely: bool = False
    javascript_heavy: bool = False


@dataclass
class JobSearchTemplate:
    """Template for specific job search scenarios"""
    name: str
    description: str
    job_criteria: JobCriteria
    recommended_boards: List[JobBoardType]
    search_strategy: str
    expected_results: int
    difficulty_level: str  # easy, medium, hard


class JobBoardTemplateManager:
    """
    Manages pre-built templates for major job boards and common search scenarios
    """
    
    def __init__(self):
        self.logger = ComponentLogger("job_templates")
        self.job_board_templates: Dict[JobBoardType, JobBoardTemplate] = {}
        self.search_templates: Dict[str, JobSearchTemplate] = {}
        
        # Initialize built-in templates
        self._initialize_job_board_templates()
        self._initialize_search_templates()
    
    def _initialize_job_board_templates(self):
        """Initialize built-in job board templates"""
        
        # Indeed Template
        self.job_board_templates[JobBoardType.INDEED] = JobBoardTemplate(
            name="Indeed",
            job_board_type=JobBoardType.INDEED,
            base_url="https://www.indeed.com",
            search_url_pattern="https://www.indeed.com/jobs?q={job_title}&l={location}",
            
            search_form_selector="#searchform",
            job_title_input="input[name='q']",
            location_input="input[name='l']", 
            search_button="button[type='submit']",
            
            job_cards_selector=".jobsearch-SerpJobCard, .job_seen_beacon",
            title_selector="h2.jobTitle a span[title], .jobTitle a",
            company_selector=".companyName, [data-testid='company-name']",
            location_selector=".companyLocation, [data-testid='job-location']",
            salary_selector=".salaryText, [data-testid='job-salary']",
            description_selector=".summary, [data-testid='job-snippet']",
            posted_date_selector=".date, [data-testid='job-posted-date']",
            application_url_selector="h2.jobTitle a",
            
            pagination_selector=".np",
            next_button_selector=".np[aria-label='Next Page']:last-child",
            
            rate_limit_delay=2.0,
            user_agent_rotation=True,
            
            remote_filter_selector="input[name='remotejob']",
            salary_filter_selector="select[name='salary']",
            captcha_likely=True,
            javascript_heavy=False
        )
        
        # LinkedIn Template  
        self.job_board_templates[JobBoardType.LINKEDIN] = JobBoardTemplate(
            name="LinkedIn Jobs",
            job_board_type=JobBoardType.LINKEDIN,
            base_url="https://www.linkedin.com",
            search_url_pattern="https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}",
            
            search_form_selector=".jobs-search-box",
            job_title_input="input[aria-label*='Search jobs']",
            location_input="input[aria-label*='City']",
            search_button=".jobs-search-box__submit-button",
            
            job_cards_selector=".job-search-card, .jobs-search-results__list-item",
            title_selector=".base-search-card__title, .job-search-card__title",
            company_selector=".base-search-card__subtitle, .job-search-card__subtitle",
            location_selector=".job-search-card__location",
            salary_selector=".job-search-card__salary-info",
            description_selector=".job-search-card__snippet",
            application_url_selector=".base-card__full-link",
            
            pagination_selector=".artdeco-pagination",
            next_button_selector=".artdeco-pagination__button--next",
            
            rate_limit_delay=3.0,
            user_agent_rotation=True,
            
            requires_login=True,
            javascript_heavy=True,
            captcha_likely=False
        )
        
        # Glassdoor Template
        self.job_board_templates[JobBoardType.GLASSDOOR] = JobBoardTemplate(
            name="Glassdoor",
            job_board_type=JobBoardType.GLASSDOOR,
            base_url="https://www.glassdoor.com",
            search_url_pattern="https://www.glassdoor.com/Job/jobs.htm?sc.keyword={job_title}&locT=C&locId={location}",
            
            search_form_selector="#search-form",
            job_title_input="input[name='sc.keyword']",
            location_input="input[name='locKeyword']",
            search_button="button[type='submit']",
            
            job_cards_selector=".react-job-listing, [data-test='jobListing']",
            title_selector="[data-test='job-title'], .jobTitle",
            company_selector="[data-test='employer-name'], .employerName",
            location_selector="[data-test='job-location'], .location",
            salary_selector="[data-test='detailSalary'], .salaryText",
            description_selector="[data-test='job-desc'], .jobDescription",
            posted_date_selector=".posted, [data-test='posted-age']",
            application_url_selector="[data-test='job-title'], .jobTitle",
            
            pagination_selector=".pagination",
            next_button_selector=".pagination .next",
            
            rate_limit_delay=2.5,
            user_agent_rotation=True,
            
            javascript_heavy=True,
            captcha_likely=True
        )
        
        # Monster Template
        self.job_board_templates[JobBoardType.MONSTER] = JobBoardTemplate(
            name="Monster",
            job_board_type=JobBoardType.MONSTER,
            base_url="https://www.monster.com",
            search_url_pattern="https://www.monster.com/jobs/search?q={job_title}&where={location}",
            
            search_form_selector=".job-search",
            job_title_input="input[name='q']",
            location_input="input[name='where']",
            search_button=".btn-search",
            
            job_cards_selector=".job-openings-card",
            title_selector=".job-title",
            company_selector=".company-name",
            location_selector=".job-location",
            salary_selector=".job-salary",
            description_selector=".job-summary",
            application_url_selector=".job-title a",
            
            pagination_selector=".pagination",
            next_button_selector=".pagination .next",
            
            rate_limit_delay=2.0,
            javascript_heavy=False
        )
        
        # Dice Template (Tech-focused)
        self.job_board_templates[JobBoardType.DICE] = JobBoardTemplate(
            name="Dice",
            job_board_type=JobBoardType.DICE,
            base_url="https://www.dice.com",
            search_url_pattern="https://www.dice.com/jobs?q={job_title}&location={location}",
            
            search_form_selector=".search-form",
            job_title_input="input[data-cy='typeahead-input']",
            location_input="input[data-cy='location-typeahead-input']",
            search_button="button[data-cy='submit-search-button']",
            
            job_cards_selector="[data-cy='search-result-card']",
            title_selector="[data-cy='card-title-link']",
            company_selector="[data-cy='search-result-company-name']",
            location_selector="[data-cy='search-result-location']",
            salary_selector="[data-cy='search-result-salary']",
            description_selector=".card-description",
            application_url_selector="[data-cy='card-title-link']",
            
            pagination_selector=".pagination",
            next_button_selector=".pagination-next",
            
            rate_limit_delay=2.0,
            javascript_heavy=True
        )
        
        # Stack Overflow Jobs Template
        self.job_board_templates[JobBoardType.STACKOVERFLOW] = JobBoardTemplate(
            name="Stack Overflow Jobs",
            job_board_type=JobBoardType.STACKOVERFLOW,
            base_url="https://stackoverflow.com",
            search_url_pattern="https://stackoverflow.com/jobs?q={job_title}&l={location}",
            
            search_form_selector=".job-search-form",
            job_title_input="input[name='q']",
            location_input="input[name='l']",
            search_button=".btn-search",
            
            job_cards_selector=".listResults .job",
            title_selector=".job-title",
            company_selector=".employer",
            location_selector=".location",
            salary_selector=".salary",
            description_selector=".summary",
            application_url_selector=".job-title a",
            
            pagination_selector=".pagination",
            next_button_selector=".pagination .next",
            
            rate_limit_delay=1.5,
            javascript_heavy=False
        )
        
        # Remote.co Template
        self.job_board_templates[JobBoardType.REMOTE_CO] = JobBoardTemplate(
            name="Remote.co",
            job_board_type=JobBoardType.REMOTE_CO,
            base_url="https://remote.co",
            search_url_pattern="https://remote.co/remote-jobs/search/?search_keywords={job_title}",
            
            search_form_selector=".job_search_form",
            job_title_input="input[name='search_keywords']",
            location_input="",  # Remote-only, no location
            search_button="input[type='submit']",
            
            job_cards_selector=".job_board_job",
            title_selector=".job_title",
            company_selector=".company_name",
            location_selector=".job_location",
            salary_selector=".job_salary",
            description_selector=".job_description",
            application_url_selector=".job_title a",
            
            pagination_selector=".pagination",
            next_button_selector=".pagination .next",
            
            rate_limit_delay=1.5,
            javascript_heavy=False
        )
    
    def _initialize_search_templates(self):
        """Initialize common job search scenario templates"""
        
        # Software Engineer searches
        self.search_templates["software_engineer_entry"] = JobSearchTemplate(
            name="Entry Level Software Engineer",
            description="Entry-level software engineering positions",
            job_criteria=JobCriteria(
                job_title="Software Engineer",
                experience_level="entry",
                employment_type="full-time",
                skills_required=["Python", "JavaScript", "Git"]
            ),
            recommended_boards=[
                JobBoardType.INDEED,
                JobBoardType.LINKEDIN, 
                JobBoardType.STACKOVERFLOW,
                JobBoardType.DICE
            ],
            search_strategy="Focus on 'junior', 'entry-level', 'new grad' keywords",
            expected_results=500,
            difficulty_level="medium"
        )
        
        self.search_templates["senior_python_developer"] = JobSearchTemplate(
            name="Senior Python Developer",
            description="Senior-level Python development roles",
            job_criteria=JobCriteria(
                job_title="Senior Python Developer",
                experience_level="senior",
                employment_type="full-time",
                salary_min=100000,
                skills_required=["Python", "Django", "PostgreSQL", "AWS"]
            ),
            recommended_boards=[
                JobBoardType.LINKEDIN,
                JobBoardType.STACKOVERFLOW,
                JobBoardType.DICE,
                JobBoardType.ANGELLIST
            ],
            search_strategy="Target 'senior', '5+ years', 'lead' positions",
            expected_results=200,
            difficulty_level="easy"
        )
        
        # Remote work searches
        self.search_templates["remote_full_stack"] = JobSearchTemplate(
            name="Remote Full Stack Developer",
            description="Remote full-stack development positions",
            job_criteria=JobCriteria(
                job_title="Full Stack Developer",
                remote_ok=True,
                employment_type="full-time",
                skills_required=["React", "Node.js", "MongoDB"]
            ),
            recommended_boards=[
                JobBoardType.REMOTE_CO,
                JobBoardType.WEWORKREMOTELY,
                JobBoardType.ANGELLIST,
                JobBoardType.LINKEDIN
            ],
            search_strategy="Focus on remote-first companies and distributed teams",
            expected_results=300,
            difficulty_level="medium"
        )
        
        # Data Science searches
        self.search_templates["data_scientist"] = JobSearchTemplate(
            name="Data Scientist",
            description="Data science and analytics positions",
            job_criteria=JobCriteria(
                job_title="Data Scientist",
                experience_level="mid",
                employment_type="full-time",
                salary_min=90000,
                skills_required=["Python", "Machine Learning", "SQL", "Statistics"]
            ),
            recommended_boards=[
                JobBoardType.LINKEDIN,
                JobBoardType.INDEED,
                JobBoardType.GLASSDOOR,
                JobBoardType.ANGELLIST
            ],
            search_strategy="Look for ML, AI, analytics keywords",
            expected_results=250,
            difficulty_level="medium"
        )
        
        # DevOps searches
        self.search_templates["devops_engineer"] = JobSearchTemplate(
            name="DevOps Engineer", 
            description="DevOps and infrastructure positions",
            job_criteria=JobCriteria(
                job_title="DevOps Engineer",
                experience_level="mid",
                employment_type="full-time",
                salary_min=95000,
                skills_required=["Docker", "Kubernetes", "AWS", "CI/CD"]
            ),
            recommended_boards=[
                JobBoardType.LINKEDIN,
                JobBoardType.STACKOVERFLOW,
                JobBoardType.DICE,
                JobBoardType.INDEED
            ],
            search_strategy="Target 'infrastructure', 'automation', 'cloud' roles",
            expected_results=180,
            difficulty_level="medium"
        )
    
    def get_job_board_template(self, job_board_type: JobBoardType) -> Optional[JobBoardTemplate]:
        """Get template for specific job board"""
        return self.job_board_templates.get(job_board_type)
    
    def get_search_template(self, template_name: str) -> Optional[JobSearchTemplate]:
        """Get search scenario template by name"""
        return self.search_templates.get(template_name)
    
    def list_job_board_templates(self) -> List[JobBoardTemplate]:
        """List all available job board templates"""
        return list(self.job_board_templates.values())
    
    def list_search_templates(self) -> List[JobSearchTemplate]:
        """List all available search scenario templates"""
        return list(self.search_templates.values())
    
    def find_templates_for_criteria(self, job_criteria: JobCriteria) -> List[JobSearchTemplate]:
        """Find search templates matching given criteria"""
        matching_templates = []
        
        for template in self.search_templates.values():
            if self._criteria_match(job_criteria, template.job_criteria):
                matching_templates.append(template)
        
        return matching_templates
    
    def _criteria_match(self, search_criteria: JobCriteria, template_criteria: JobCriteria) -> bool:
        """Check if search criteria matches template criteria"""
        # Check job title similarity
        if search_criteria.job_title.lower() in template_criteria.job_title.lower():
            return True
        
        # Check experience level match
        if (search_criteria.experience_level and 
            search_criteria.experience_level == template_criteria.experience_level):
            return True
        
        # Check remote work preference
        if search_criteria.remote_ok and template_criteria.remote_ok:
            return True
        
        # Check skill overlap
        if (search_criteria.skills_required and template_criteria.skills_required):
            search_skills = set(skill.lower() for skill in search_criteria.skills_required)
            template_skills = set(skill.lower() for skill in template_criteria.skills_required)
            if search_skills.intersection(template_skills):
                return True
        
        return False
    
    def recommend_job_boards(self, job_criteria: JobCriteria) -> List[JobBoardType]:
        """Recommend job boards based on search criteria"""
        recommendations = []
        
        # Tech roles - prioritize tech-focused boards
        tech_keywords = ['engineer', 'developer', 'programmer', 'devops', 'data scientist']
        if any(keyword in job_criteria.job_title.lower() for keyword in tech_keywords):
            recommendations.extend([
                JobBoardType.STACKOVERFLOW,
                JobBoardType.DICE,
                JobBoardType.LINKEDIN,
                JobBoardType.ANGELLIST
            ])
        
        # Remote work - prioritize remote-focused boards
        if job_criteria.remote_ok:
            recommendations.extend([
                JobBoardType.REMOTE_CO,
                JobBoardType.WEWORKREMOTELY,
                JobBoardType.ANGELLIST
            ])
        
        # Entry level - prioritize general boards
        if job_criteria.experience_level in ['entry', 'junior']:
            recommendations.extend([
                JobBoardType.INDEED,
                JobBoardType.LINKEDIN,
                JobBoardType.GLASSDOOR
            ])
        
        # Senior level - prioritize professional networks
        if job_criteria.experience_level in ['senior', 'lead', 'principal']:
            recommendations.extend([
                JobBoardType.LINKEDIN,
                JobBoardType.ANGELLIST,
                JobBoardType.STACKOVERFLOW
            ])
        
        # Always include major general boards
        recommendations.extend([
            JobBoardType.INDEED,
            JobBoardType.LINKEDIN,
            JobBoardType.GLASSDOOR
        ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for board in recommendations:
            if board not in seen:
                seen.add(board)
                unique_recommendations.append(board)
        
        return unique_recommendations[:5]  # Return top 5 recommendations
    
    def export_template(self, job_board_type: JobBoardType, file_path: str):
        """Export job board template to JSON file"""
        template = self.get_job_board_template(job_board_type)
        if template:
            with open(file_path, 'w') as f:
                json.dump(asdict(template), f, indent=2, default=str)
            self.logger.info("Template exported", job_board=job_board_type.value, file=file_path)
    
    def import_template(self, file_path: str) -> JobBoardTemplate:
        """Import job board template from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert job_board_type string back to enum
        data['job_board_type'] = JobBoardType(data['job_board_type'])
        
        template = JobBoardTemplate(**data)
        self.job_board_templates[template.job_board_type] = template
        
        self.logger.info("Template imported", job_board=template.job_board_type.value, file=file_path)
        return template
    
    def create_custom_template(
        self,
        name: str,
        base_url: str,
        selectors: Dict[str, str],
        **kwargs
    ) -> JobBoardTemplate:
        """Create custom job board template"""
        template = JobBoardTemplate(
            name=name,
            job_board_type=JobBoardType.GENERIC,
            base_url=base_url,
            search_url_pattern=kwargs.get('search_url_pattern', base_url),
            search_form_selector=selectors.get('search_form', ''),
            job_title_input=selectors.get('job_title_input', ''),
            location_input=selectors.get('location_input', ''),
            search_button=selectors.get('search_button', ''),
            job_cards_selector=selectors.get('job_cards', ''),
            title_selector=selectors.get('title', ''),
            company_selector=selectors.get('company', ''),
            location_selector=selectors.get('location', ''),
            salary_selector=selectors.get('salary', ''),
            pagination_selector=selectors.get('pagination', ''),
            next_button_selector=selectors.get('next_button', ''),
            **kwargs
        )
        
        self.job_board_templates[JobBoardType.GENERIC] = template
        self.logger.info("Custom template created", name=name)
        return template