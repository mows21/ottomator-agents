"""
Template-based workflow generator using keyword matching.
This is the foundation before adding AI - simple, fast, and reliable.
"""

import json
import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TemplateMatch:
    """Represents a matched template with confidence score"""
    template_name: str
    template_json: Dict[str, Any]
    metadata: Dict[str, Any]
    confidence: float
    matched_keywords: List[str]


class TemplateLibrary:
    """Manages the library of n8n workflow templates"""

    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "templates"
        self.templates_dir = Path(templates_dir)
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict]:
        """Load all template JSON files from the templates directory"""
        templates = {}

        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                    template_name = template_file.stem
                    templates[template_name] = template_data
            except Exception as e:
                print(f"Error loading template {template_file}: {e}")

        return templates

    def get_template(self, template_name: str) -> Optional[Dict]:
        """Get a specific template by name"""
        return self.templates.get(template_name)

    def list_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.templates.keys())

    def get_template_metadata(self, template_name: str) -> Optional[Dict]:
        """Get metadata for a specific template"""
        template = self.get_template(template_name)
        if template:
            return template.get("metadata", {})
        return None


class TemplateGenerator:
    """
    Generate n8n workflows using template matching.
    Uses keyword matching and scoring to find the best template.
    """

    def __init__(self, templates_dir: str = None):
        self.library = TemplateLibrary(templates_dir)

        # Define keyword patterns for each template
        self.template_keywords = {
            "email_notification": {
                "primary": ["email", "mail", "send email", "notify via email"],
                "secondary": ["smtp", "gmail", "outlook", "message"],
                "category": "communication"
            },
            "database_query": {
                "primary": ["database", "sql", "query", "postgres", "select"],
                "secondary": ["table", "fetch data", "retrieve", "db"],
                "category": "database"
            },
            "api_call": {
                "primary": ["api", "http", "rest", "endpoint", "request"],
                "secondary": ["get", "post", "fetch", "call api"],
                "category": "integration"
            },
            "web_scraper": {
                "primary": ["scrape", "web scraping", "extract from website", "crawl"],
                "secondary": ["html", "website", "web page", "parse"],
                "category": "data"
            },
            "file_processing": {
                "primary": ["file", "csv", "process file", "read file"],
                "secondary": ["spreadsheet", "excel", "data file", "import"],
                "category": "data"
            },
            "slack_notification": {
                "primary": ["slack", "send to slack", "slack message"],
                "secondary": ["channel", "team notification", "slack bot"],
                "category": "communication"
            },
            "data_transformation": {
                "primary": ["transform", "convert", "map data", "etl"],
                "secondary": ["json", "format", "reshape", "modify"],
                "category": "data"
            },
            "scheduled_task": {
                "primary": ["schedule", "cron", "daily", "periodic", "recurring"],
                "secondary": ["every day", "every hour", "automated", "timer"],
                "category": "automation"
            },
            "webhook_receiver": {
                "primary": ["webhook", "receive webhook", "incoming webhook"],
                "secondary": ["callback", "http post", "listener"],
                "category": "integration"
            },
            "multi_step_pipeline": {
                "primary": ["pipeline", "multi-step", "workflow", "process"],
                "secondary": ["multiple steps", "chain", "sequence"],
                "category": "pipeline"
            }
        }

    def match_template(self, task_description: str) -> TemplateMatch:
        """
        Find the best matching template for a task description.
        Returns TemplateMatch with confidence score.
        """
        task_lower = task_description.lower()
        scores = {}
        matched_keywords = {}

        # Calculate scores for each template
        for template_name, keywords in self.template_keywords.items():
            score = 0.0
            matches = []

            # Primary keywords worth more (2 points each)
            for keyword in keywords["primary"]:
                if keyword in task_lower:
                    score += 2.0
                    matches.append(keyword)

            # Secondary keywords worth less (1 point each)
            for keyword in keywords["secondary"]:
                if keyword in task_lower:
                    score += 1.0
                    matches.append(keyword)

            scores[template_name] = score
            matched_keywords[template_name] = matches

        # Find template with highest score
        if not scores or max(scores.values()) == 0:
            # Default to multi_step_pipeline if no matches
            best_template = "multi_step_pipeline"
            confidence = 0.3
        else:
            best_template = max(scores, key=scores.get)
            max_score = scores[best_template]
            # Normalize confidence to 0-1 range
            confidence = min(max_score / 10.0, 1.0)

        # Load the template
        template_json = self.library.get_template(best_template)
        metadata = self.library.get_template_metadata(best_template)

        return TemplateMatch(
            template_name=best_template,
            template_json=template_json,
            metadata=metadata or {},
            confidence=confidence,
            matched_keywords=matched_keywords.get(best_template, [])
        )

    def fill_parameters(self, template: Dict, parameters: Dict[str, Any]) -> Dict:
        """
        Fill template placeholders with actual parameter values.
        Replaces {{parameter_name}} with actual values.
        """
        # Convert template to JSON string
        template_str = json.dumps(template)

        # Replace all placeholders
        for param_name, param_value in parameters.items():
            placeholder = f"{{{{{param_name}}}}}"
            # Convert value to string for replacement
            if isinstance(param_value, (dict, list)):
                value_str = json.dumps(param_value)
            else:
                value_str = str(param_value)
            template_str = template_str.replace(placeholder, value_str)

        # Remove metadata before returning (n8n doesn't need it)
        filled_template = json.loads(template_str)
        if "metadata" in filled_template:
            del filled_template["metadata"]

        return filled_template

    def extract_parameters(self, task_description: str, template_match: TemplateMatch) -> Dict[str, Any]:
        """
        Extract parameter values from task description based on template requirements.
        This is a simple heuristic - AI will do better later.
        """
        parameters = {}
        metadata = template_match.metadata

        if not metadata or "parameters" not in metadata:
            return parameters

        required_params = metadata["parameters"]
        task_lower = task_description.lower()

        # Simple extraction heuristics
        for param_name, param_info in required_params.items():
            param_type = param_info.get("type", "string")

            # Email extraction
            if "email" in param_name:
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, task_description)
                if emails:
                    parameters[param_name] = emails[0]

            # URL extraction
            elif "url" in param_name:
                url_pattern = r'https?://[^\s]+'
                urls = re.findall(url_pattern, task_description)
                if urls:
                    parameters[param_name] = urls[0]

            # Use defaults if specified
            if param_name not in parameters and "default" in param_info:
                parameters[param_name] = param_info["default"]

        return parameters

    def generate_workflow(self, task_description: str,
                         custom_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main method: Generate a complete workflow from task description.

        Args:
            task_description: Natural language description of desired workflow
            custom_parameters: Optional dict of parameter values to override extraction

        Returns:
            Dict containing workflow_json, metadata, and generation info
        """
        # 1. Find best matching template
        template_match = self.match_template(task_description)

        # 2. Extract parameters from description
        extracted_params = self.extract_parameters(task_description, template_match)

        # 3. Merge with custom parameters (custom takes precedence)
        if custom_parameters:
            extracted_params.update(custom_parameters)

        # 4. Fill template with parameters
        workflow_json = self.fill_parameters(
            template_match.template_json.copy(),
            extracted_params
        )

        # 5. Return complete result
        return {
            "workflow_json": workflow_json,
            "template_name": template_match.template_name,
            "confidence": template_match.confidence,
            "matched_keywords": template_match.matched_keywords,
            "parameters_used": extracted_params,
            "generation_method": "template_matching"
        }


# Example usage
if __name__ == "__main__":
    generator = TemplateGenerator()

    # Test cases
    test_tasks = [
        "Send an email notification to team@example.com about the daily report",
        "Query the users table in the database and get all active users",
        "Call the weather API at https://api.weather.com/current",
        "Scrape product prices from https://example.com/products",
        "Process the sales CSV file and transform the data"
    ]

    for task in test_tasks:
        print(f"\nTask: {task}")
        result = generator.generate_workflow(task)
        print(f"Template: {result['template_name']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Matched keywords: {result['matched_keywords']}")
        print(f"Parameters: {result['parameters_used']}")
        print("-" * 80)
