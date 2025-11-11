"""
Unit tests for AI Workflow Composer.
"""

import pytest
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.template_matcher import TemplateGenerator, TemplateLibrary


class TestTemplateLibrary:
    """Test template library functionality"""

    def test_load_templates(self):
        """Test that templates are loaded correctly"""
        library = TemplateLibrary()
        templates = library.list_templates()

        assert len(templates) == 10, "Should load 10 templates"
        assert "email_notification" in templates
        assert "database_query" in templates
        assert "api_call" in templates

    def test_get_template(self):
        """Test retrieving specific templates"""
        library = TemplateLibrary()

        email_template = library.get_template("email_notification")
        assert email_template is not None
        assert "nodes" in email_template
        assert "connections" in email_template
        assert "metadata" in email_template

    def test_template_metadata(self):
        """Test template metadata structure"""
        library = TemplateLibrary()
        metadata = library.get_template_metadata("email_notification")

        assert metadata is not None
        assert "description" in metadata
        assert "category" in metadata
        assert "parameters" in metadata
        assert "tags" in metadata


class TestTemplateGenerator:
    """Test template-based workflow generation"""

    def test_match_email_template(self):
        """Test matching email notification template"""
        generator = TemplateGenerator()

        match = generator.match_template("Send an email to team@company.com")

        assert match.template_name == "email_notification"
        assert match.confidence > 0.5
        assert "email" in match.matched_keywords

    def test_match_database_template(self):
        """Test matching database query template"""
        generator = TemplateGenerator()

        match = generator.match_template("Query the users table in PostgreSQL")

        assert match.template_name == "database_query"
        assert match.confidence > 0.5
        assert any(kw in ["database", "query", "sql", "postgres"] for kw in match.matched_keywords)

    def test_match_api_template(self):
        """Test matching API call template"""
        generator = TemplateGenerator()

        match = generator.match_template("Call the weather API at https://api.weather.com")

        assert match.template_name == "api_call"
        assert match.confidence > 0.5
        assert "api" in match.matched_keywords

    def test_fill_parameters(self):
        """Test parameter filling in templates"""
        generator = TemplateGenerator()

        template = {
            "name": "Test Workflow",
            "config": {
                "email": "{{recipient_email}}",
                "subject": "{{email_subject}}"
            }
        }

        params = {
            "recipient_email": "test@example.com",
            "email_subject": "Test Subject"
        }

        filled = generator.fill_parameters(template, params)

        assert filled["config"]["email"] == "test@example.com"
        assert filled["config"]["subject"] == "Test Subject"

    def test_extract_parameters(self):
        """Test parameter extraction from task descriptions"""
        generator = TemplateGenerator()

        task = "Send email to john@example.com about the report"
        match = generator.match_template(task)
        params = generator.extract_parameters(task, match)

        # Should extract email
        assert "recipient_email" in params or "sender_email" in params

    def test_generate_workflow_complete(self):
        """Test complete workflow generation"""
        generator = TemplateGenerator()

        result = generator.generate_workflow(
            task_description="Send an email notification to admin@company.com",
            custom_parameters={
                "recipient_email": "admin@company.com",
                "email_subject": "Alert",
                "email_body": "Test message"
            }
        )

        assert "workflow_json" in result
        assert "template_name" in result
        assert "confidence" in result
        assert result["generation_method"] == "template_matching"

        # Workflow should be valid JSON structure
        workflow = result["workflow_json"]
        assert "nodes" in workflow
        assert "connections" in workflow
        assert isinstance(workflow["nodes"], list)
        assert isinstance(workflow["connections"], dict)

    def test_low_confidence_fallback(self):
        """Test behavior with unclear task descriptions"""
        generator = TemplateGenerator()

        # Ambiguous task
        match = generator.match_template("Do something with data")

        # Should still return a template (fallback to multi_step_pipeline)
        assert match.template_name is not None
        assert match.confidence >= 0.0


class TestWorkflowValidation:
    """Test workflow validation"""

    def test_valid_workflow_structure(self):
        """Test that generated workflows have valid structure"""
        generator = TemplateGenerator()

        result = generator.generate_workflow(
            "Send email to test@example.com",
            {"recipient_email": "test@example.com"}
        )

        workflow = result["workflow_json"]

        # Required fields
        assert "nodes" in workflow
        assert "connections" in workflow

        # Nodes structure
        assert isinstance(workflow["nodes"], list)
        assert len(workflow["nodes"]) > 0

        # Each node should have required fields
        for node in workflow["nodes"]:
            assert "type" in node
            assert "name" in node
            # Note: id and position might be optional in some templates

    def test_no_metadata_in_workflow(self):
        """Test that metadata is stripped from final workflow"""
        generator = TemplateGenerator()

        result = generator.generate_workflow(
            "Query database",
            {"sql_query": "SELECT * FROM users"}
        )

        workflow = result["workflow_json"]

        # Metadata should not be in the final workflow JSON
        assert "metadata" not in workflow


def test_all_templates_valid():
    """Test that all templates have valid structure"""
    library = TemplateLibrary()

    for template_name in library.list_templates():
        template = library.get_template(template_name)

        # Basic structure
        assert "nodes" in template, f"{template_name} missing nodes"
        assert "connections" in template, f"{template_name} missing connections"

        # Metadata
        assert "metadata" in template, f"{template_name} missing metadata"
        metadata = template["metadata"]

        assert "description" in metadata
        assert "category" in metadata
        assert "parameters" in metadata
        assert "tags" in metadata
        assert isinstance(metadata["tags"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
