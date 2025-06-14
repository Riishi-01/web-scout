"""
Specialized LLM communication channels for different analysis tasks
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .providers import LLMRequest, LLMResponse
from ..utils.logger import ComponentLogger


@dataclass
class ChannelResponse:
    """Response from a specialized channel"""
    success: bool
    data: Dict[str, Any]
    confidence: float = 0.0
    reasoning: str = ""
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class BaseChannel(ABC):
    """Base class for specialized LLM channels"""
    
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        self.logger = ComponentLogger(f"llm_channel_{channel_id}")
    
    @abstractmethod
    def prepare_request(self, input_data: Dict[str, Any]) -> LLMRequest:
        """Prepare LLM request for this channel"""
        pass
    
    @abstractmethod
    def parse_response(self, response: LLMResponse) -> ChannelResponse:
        """Parse LLM response into structured format"""
        pass
    
    def _extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response content"""
        try:
            # Try to find JSON in the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
            
            # If no JSON found, try parsing entire content
            return json.loads(content)
            
        except json.JSONDecodeError:
            self.logger.warning("Failed to extract JSON from response", content=content[:200])
            return None


class HTMLAnalysisChannel(BaseChannel):
    """Channel for HTML structure analysis and selector generation"""
    
    def __init__(self):
        super().__init__("html_analysis")
    
    def prepare_request(self, input_data: Dict[str, Any]) -> LLMRequest:
        """Prepare HTML analysis request"""
        html_content = input_data.get("html_content", "")
        url = input_data.get("url", "")
        user_intent = input_data.get("user_intent", "")
        site_metadata = input_data.get("site_metadata", {})
        
        # Truncate HTML if too long
        if len(html_content) > 50000:
            html_content = html_content[:50000] + "... [truncated]"
        
        system_prompt = """You are an expert web scraping analyst. Your task is to analyze HTML content and generate optimal CSS selectors for data extraction.

Return your analysis as a JSON object with the following structure:
{
    "selectors": ["css_selector1", "css_selector2"],
    "extraction_logic": "description of how to extract data",
    "confidence_score": 0.95,
    "alternative_strategies": ["alternative approach 1", "alternative approach 2"],
    "reasoning": "explanation of your analysis"
}

Focus on:
1. Robust selectors that won't break easily
2. Efficient extraction patterns
3. Handling of dynamic content
4. Alternative strategies for reliability"""

        user_message = f"""Analyze this HTML content and generate optimal selectors for data extraction:

URL: {url}
User Intent: {user_intent}

Site Metadata: {json.dumps(site_metadata, indent=2)}

HTML Content:
{html_content}

Please provide CSS selectors and extraction logic for the user's intended data extraction."""

        return LLMRequest(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            max_tokens=3000,
            temperature=0.1
        )
    
    def parse_response(self, response: LLMResponse) -> ChannelResponse:
        """Parse HTML analysis response"""
        if not response.success:
            return ChannelResponse(
                success=False,
                data={},
                reasoning=f"LLM request failed: {response.error}"
            )
        
        # Extract JSON from response
        data = self._extract_json_from_response(response.content)
        
        if not data:
            return ChannelResponse(
                success=False,
                data={},
                reasoning="Failed to parse JSON response"
            )
        
        # Validate required fields
        required_fields = ["selectors", "extraction_logic", "confidence_score"]
        if not all(field in data for field in required_fields):
            return ChannelResponse(
                success=False,
                data={},
                reasoning="Missing required fields in response"
            )
        
        return ChannelResponse(
            success=True,
            data=data,
            confidence=data.get("confidence_score", 0.0),
            reasoning=data.get("reasoning", ""),
            suggestions=data.get("alternative_strategies", [])
        )


class StrategyGenerationChannel(BaseChannel):
    """Channel for generating comprehensive scraping strategies"""
    
    def __init__(self):
        super().__init__("strategy_generation")
    
    def prepare_request(self, input_data: Dict[str, Any]) -> LLMRequest:
        """Prepare strategy generation request"""
        site_structure = input_data.get("site_structure", {})
        user_requirements = input_data.get("user_requirements", {})
        detected_filters = input_data.get("detected_filters", [])
        performance_constraints = input_data.get("performance_constraints", {})
        
        system_prompt = """You are an expert web scraping strategist. Generate comprehensive scraping strategies based on site analysis and user requirements.

Return your strategy as a JSON object:
{
    "scraping_plan": {
        "approach": "strategy description",
        "steps": ["step1", "step2", "step3"],
        "estimated_duration": "time estimate",
        "resource_requirements": "resource needs"
    },
    "filter_sequence": [
        {
            "filter": "filter_name",
            "action": "action_to_take",
            "value": "value_to_set",
            "wait_time": 2
        }
    ],
    "timing_strategy": {
        "request_delay": 2.0,
        "page_load_wait": 3.0,
        "retry_delay": 5.0,
        "total_timeout": 30.0
    },
    "risk_assessment": {
        "detection_probability": "low/medium/high",
        "mitigation_strategies": ["strategy1", "strategy2"],
        "fallback_plans": ["plan1", "plan2"]
    },
    "reasoning": "detailed explanation"
}"""

        user_message = f"""Generate a comprehensive scraping strategy based on this analysis:

Site Structure:
{json.dumps(site_structure, indent=2)}

User Requirements:
{json.dumps(user_requirements, indent=2)}

Detected Filters:
{json.dumps(detected_filters, indent=2)}

Performance Constraints:
{json.dumps(performance_constraints, indent=2)}

Please provide a detailed, actionable scraping strategy that addresses all requirements while minimizing detection risk."""

        return LLMRequest(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            max_tokens=4000,
            temperature=0.2
        )
    
    def parse_response(self, response: LLMResponse) -> ChannelResponse:
        """Parse strategy generation response"""
        if not response.success:
            return ChannelResponse(
                success=False,
                data={},
                reasoning=f"LLM request failed: {response.error}"
            )
        
        data = self._extract_json_from_response(response.content)
        
        if not data:
            return ChannelResponse(
                success=False,
                data={},
                reasoning="Failed to parse JSON response"
            )
        
        # Validate strategy structure
        required_sections = ["scraping_plan", "timing_strategy", "risk_assessment"]
        if not all(section in data for section in required_sections):
            return ChannelResponse(
                success=False,
                data={},
                reasoning="Missing required strategy sections"
            )
        
        # Calculate confidence based on completeness
        confidence = 0.5  # Base confidence
        if "filter_sequence" in data:
            confidence += 0.2
        if data.get("risk_assessment", {}).get("detection_probability"):
            confidence += 0.2
        if len(data.get("scraping_plan", {}).get("steps", [])) > 2:
            confidence += 0.1
        
        return ChannelResponse(
            success=True,
            data=data,
            confidence=min(confidence, 1.0),
            reasoning=data.get("reasoning", ""),
            suggestions=data.get("risk_assessment", {}).get("mitigation_strategies", [])
        )


class ErrorResolutionChannel(BaseChannel):
    """Channel for analyzing errors and generating resolution strategies"""
    
    def __init__(self):
        super().__init__("error_resolution")
    
    def prepare_request(self, input_data: Dict[str, Any]) -> LLMRequest:
        """Prepare error resolution request"""
        error_context = input_data.get("error_context", "")
        failed_selectors = input_data.get("failed_selectors", [])
        page_state = input_data.get("page_state", {})
        previous_attempts = input_data.get("previous_attempts", [])
        
        system_prompt = """You are an expert web scraping troubleshooter. Analyze errors and provide practical resolution strategies.

Return your analysis as a JSON object:
{
    "resolution_strategy": "primary approach to resolve the issue",
    "updated_selectors": ["new_selector1", "new_selector2"],
    "retry_logic": {
        "max_attempts": 3,
        "delay_between_attempts": 5.0,
        "escalation_strategy": "what to do if retries fail"
    },
    "success_probability": 0.85,
    "reasoning": "detailed analysis of the problem and solution",
    "preventive_measures": ["measure1", "measure2"]
}

Focus on:
1. Root cause analysis
2. Practical, implementable solutions
3. Prevention of similar issues
4. Fallback strategies"""

        user_message = f"""Analyze this scraping error and provide a resolution strategy:

Error Context:
{error_context}

Failed Selectors:
{json.dumps(failed_selectors, indent=2)}

Page State:
{json.dumps(page_state, indent=2)}

Previous Attempts:
{json.dumps(previous_attempts, indent=2)}

Please provide a comprehensive resolution strategy with updated selectors and retry logic."""

        return LLMRequest(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.1
        )
    
    def parse_response(self, response: LLMResponse) -> ChannelResponse:
        """Parse error resolution response"""
        if not response.success:
            return ChannelResponse(
                success=False,
                data={},
                reasoning=f"LLM request failed: {response.error}"
            )
        
        data = self._extract_json_from_response(response.content)
        
        if not data:
            return ChannelResponse(
                success=False,
                data={},
                reasoning="Failed to parse JSON response"
            )
        
        # Validate resolution structure
        required_fields = ["resolution_strategy", "success_probability"]
        if not all(field in data for field in required_fields):
            return ChannelResponse(
                success=False,
                data={},
                reasoning="Missing required resolution fields"
            )
        
        success_probability = data.get("success_probability", 0.0)
        
        return ChannelResponse(
            success=True,
            data=data,
            confidence=success_probability,
            reasoning=data.get("reasoning", ""),
            suggestions=data.get("preventive_measures", [])
        )


class QualityAssessmentChannel(BaseChannel):
    """Channel for assessing data quality and providing improvement suggestions"""
    
    def __init__(self):
        super().__init__("quality_assessment")
    
    def prepare_request(self, input_data: Dict[str, Any]) -> LLMRequest:
        """Prepare quality assessment request"""
        extracted_data = input_data.get("extracted_data", [])
        expected_patterns = input_data.get("expected_patterns", {})
        extraction_metadata = input_data.get("extraction_metadata", {})
        
        # Limit data size for analysis
        sample_data = extracted_data[:10] if len(extracted_data) > 10 else extracted_data
        
        system_prompt = """You are a data quality analyst specializing in web scraping validation. Assess extracted data quality and provide improvement recommendations.

Return your assessment as a JSON object:
{
    "quality_score": 0.85,
    "data_issues": [
        {
            "type": "missing_values",
            "severity": "medium",
            "description": "20% of records missing price information",
            "affected_fields": ["price"]
        }
    ],
    "improvement_suggestions": [
        "Add fallback selectors for price field",
        "Implement data validation rules"
    ],
    "confidence_level": "high",
    "reasoning": "detailed analysis of data quality",
    "metrics": {
        "completeness": 0.95,
        "consistency": 0.80,
        "accuracy": 0.90
    }
}

Evaluate:
1. Data completeness (missing values)
2. Data consistency (format variations)
3. Data accuracy (realistic values)
4. Pattern adherence (matches expectations)"""

        user_message = f"""Assess the quality of this extracted data:

Sample Extracted Data:
{json.dumps(sample_data, indent=2)}

Expected Patterns:
{json.dumps(expected_patterns, indent=2)}

Extraction Metadata:
{json.dumps(extraction_metadata, indent=2)}

Please provide a comprehensive quality assessment with specific improvement recommendations."""

        return LLMRequest(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.1
        )
    
    def parse_response(self, response: LLMResponse) -> ChannelResponse:
        """Parse quality assessment response"""
        if not response.success:
            return ChannelResponse(
                success=False,
                data={},
                reasoning=f"LLM request failed: {response.error}"
            )
        
        data = self._extract_json_from_response(response.content)
        
        if not data:
            return ChannelResponse(
                success=False,
                data={},
                reasoning="Failed to parse JSON response"
            )
        
        # Validate assessment structure
        required_fields = ["quality_score", "data_issues", "improvement_suggestions"]
        if not all(field in data for field in required_fields):
            return ChannelResponse(
                success=False,
                data={},
                reasoning="Missing required assessment fields"
            )
        
        quality_score = data.get("quality_score", 0.0)
        confidence_mapping = {
            "high": 0.9,
            "medium": 0.7,
            "low": 0.5
        }
        
        confidence_level = data.get("confidence_level", "medium")
        confidence = confidence_mapping.get(confidence_level.lower(), 0.7)
        
        return ChannelResponse(
            success=True,
            data=data,
            confidence=confidence,
            reasoning=data.get("reasoning", ""),
            suggestions=data.get("improvement_suggestions", [])
        )