"""
Pydantic AI agent for intelligent n8n workflow generation.
Combines template-based generation with AI reasoning for complex tasks.
"""

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import os
from dotenv import load_dotenv

from generator.template_matcher import TemplateGenerator, TemplateLibrary

load_dotenv()


class GeneratedWorkflow(BaseModel):
    """Result from workflow generation"""
    workflow_json: Dict[str, Any] = Field(description="Complete n8n workflow JSON")
    confidence_score: float = Field(description="Confidence in generation quality (0-1)")
    reasoning: str = Field(description="Explanation of generation decisions")
    complexity_level: str = Field(description="simple, medium, or complex")
    recommended_testing: List[str] = Field(description="Testing recommendations")


@dataclass
class WorkflowAgentDeps:
    """Dependencies for workflow agent"""
    template_library: TemplateLibrary
    template_generator: TemplateGenerator
    n8n_schema: Dict[str, Any] = None


class WorkflowGeneratorAgent:
    """
    AI-powered workflow generator using Pydantic AI.
    Falls back to template matching for simple tasks.
    """

    def __init__(self, model: str = "openai:gpt-4o"):
        self.template_library = TemplateLibrary()
        self.template_generator = TemplateGenerator()

        self.deps = WorkflowAgentDeps(
            template_library=self.template_library,
            template_generator=self.template_generator,
            n8n_schema=self._load_n8n_schema()
        )

        self.agent = Agent(
            model,
            deps_type=WorkflowAgentDeps,
            result_type=GeneratedWorkflow,
            system_prompt=self._get_system_prompt()
        )

    def _get_system_prompt(self) -> str:
        """Create comprehensive system prompt for workflow generation"""
        available_templates = self.template_library.list_templates()

        return f"""You are an expert n8n workflow generation agent.

Your role is to generate valid, executable n8n workflow JSON from natural language descriptions.

AVAILABLE TEMPLATES:
{', '.join(available_templates)}

WORKFLOW STRUCTURE:
Every n8n workflow must have:
1. "name": string - workflow name
2. "nodes": array - list of workflow nodes
3. "connections": object - how nodes connect
4. "settings": object - workflow settings (optional)

NODE STRUCTURE:
Each node must have:
- "id": unique identifier
- "name": human-readable name
- "type": node type (e.g., "n8n-nodes-base.httpRequest")
- "typeVersion": version number
- "position": [x, y] coordinates
- "parameters": node-specific configuration

CONNECTION STRUCTURE:
{{
  "NodeName": {{
    "main": [
      [
        {{
          "node": "TargetNodeName",
          "type": "main",
          "index": 0
        }}
      ]
    ]
  }}
}}

GENERATION STRATEGY:
1. SIMPLE TASKS: Use template matching when possible (faster, more reliable)
2. COMPLEX TASKS: Generate custom workflows with AI reasoning
3. VALIDATION: Always ensure valid JSON structure
4. CONFIDENCE: Provide honest assessment of generation quality

QUALITY CRITERIA:
- Syntactically correct JSON
- Valid node types and parameters
- Proper node connections
- Error handling where appropriate
- Clear, descriptive node names

Generate workflows that will execute successfully in n8n.
"""

    def _load_n8n_schema(self) -> Dict[str, Any]:
        """Load n8n schema information (simplified for POC)"""
        return {
            "common_node_types": [
                "n8n-nodes-base.httpRequest",
                "n8n-nodes-base.postgres",
                "n8n-nodes-base.emailSend",
                "n8n-nodes-base.slack",
                "n8n-nodes-base.code",
                "n8n-nodes-base.webhook",
                "n8n-nodes-base.scheduleTrigger",
                "n8n-nodes-base.manualTrigger",
                "n8n-nodes-base.filter",
                "n8n-nodes-base.if"
            ],
            "trigger_nodes": [
                "n8n-nodes-base.manualTrigger",
                "n8n-nodes-base.webhook",
                "n8n-nodes-base.scheduleTrigger"
            ]
        }

    @agent.tool
    async def get_template_info(self, ctx: RunContext[WorkflowAgentDeps],
                              template_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific template"""
        template = ctx.deps.template_library.get_template(template_name)
        if template:
            return {
                "template": template,
                "metadata": template.get("metadata", {})
            }
        return {"error": f"Template {template_name} not found"}

    @agent.tool
    async def search_similar_templates(self, ctx: RunContext[WorkflowAgentDeps],
                                      task_description: str) -> List[Dict[str, Any]]:
        """Search for templates similar to the task description"""
        # Use template matcher to find similar templates
        match = ctx.deps.template_generator.match_template(task_description)

        return [
            {
                "template_name": match.template_name,
                "confidence": match.confidence,
                "matched_keywords": match.matched_keywords,
                "metadata": match.metadata
            }
        ]

    @agent.tool
    async def validate_node_types(self, ctx: RunContext[WorkflowAgentDeps],
                                 nodes: List[Dict]) -> Dict[str, Any]:
        """Validate that node types are valid"""
        schema = ctx.deps.n8n_schema
        valid_types = schema.get("common_node_types", [])

        validation = {
            "valid": True,
            "invalid_nodes": [],
            "warnings": []
        }

        for node in nodes:
            node_type = node.get("type")
            if node_type and node_type not in valid_types:
                validation["warnings"].append(
                    f"Node type '{node_type}' not in common types list"
                )

        return validation

    async def generate_workflow(self,
                               task_description: str,
                               use_template: bool = True,
                               custom_parameters: Dict[str, Any] = None) -> GeneratedWorkflow:
        """
        Main generation method with hybrid approach.

        Args:
            task_description: Natural language workflow description
            use_template: Whether to try template matching first
            custom_parameters: Optional parameters to pass to templates

        Returns:
            GeneratedWorkflow with JSON and metadata
        """
        # Try template matching first for simple tasks
        if use_template:
            template_result = self.template_generator.generate_workflow(
                task_description,
                custom_parameters
            )

            # If confidence is high, use template result
            if template_result["confidence"] >= 0.7:
                return GeneratedWorkflow(
                    workflow_json=template_result["workflow_json"],
                    confidence_score=template_result["confidence"],
                    reasoning=f"Used template '{template_result['template_name']}' with high confidence match based on keywords: {', '.join(template_result['matched_keywords'])}",
                    complexity_level="simple",
                    recommended_testing=[
                        "Verify all parameters are correctly set",
                        "Test with sample data",
                        "Check node credentials are configured"
                    ]
                )

        # Use AI for complex tasks or low-confidence template matches
        prompt = f"""Generate an n8n workflow for the following task:

Task Description:
{task_description}

Custom Parameters:
{json.dumps(custom_parameters or {}, indent=2)}

Consider using similar templates as reference, but generate a custom workflow if needed.
Ensure the workflow is complete, valid, and executable.
"""

        result = await self.agent.run(prompt, deps=self.deps)
        return result.data

    async def refine_workflow(self,
                            workflow_json: Dict[str, Any],
                            feedback: str) -> GeneratedWorkflow:
        """
        Refine a workflow based on feedback or errors.

        Args:
            workflow_json: Current workflow JSON
            feedback: Feedback or error message

        Returns:
            Refined workflow
        """
        prompt = f"""Refine this n8n workflow based on the feedback:

Current Workflow:
{json.dumps(workflow_json, indent=2)}

Feedback/Error:
{feedback}

Generate an improved version that addresses the issues.
"""

        result = await self.agent.run(prompt, deps=self.deps)
        return result.data


# Hybrid generator combining templates and AI
class HybridWorkflowGenerator:
    """
    Combines template matching with AI generation.
    Provides the best of both approaches.
    """

    def __init__(self, model: str = "openai:gpt-4o"):
        self.template_generator = TemplateGenerator()
        self.ai_generator = WorkflowGeneratorAgent(model)

    async def generate(self,
                      task_description: str,
                      parameters: Dict[str, Any] = None,
                      force_ai: bool = False) -> Dict[str, Any]:
        """
        Generate workflow using hybrid approach.

        Args:
            task_description: Task description
            parameters: Optional parameters
            force_ai: Force AI generation even for simple tasks

        Returns:
            Generation result with workflow and metadata
        """
        if not force_ai:
            # Try template matching first
            template_result = self.template_generator.generate_workflow(
                task_description,
                parameters
            )

            # Return template result if confidence is high
            if template_result["confidence"] >= 0.7:
                return {
                    "workflow_json": template_result["workflow_json"],
                    "confidence": template_result["confidence"],
                    "method": "template_matching",
                    "template_name": template_result["template_name"],
                    "reasoning": f"High-confidence template match",
                    "parameters_used": template_result["parameters_used"]
                }

        # Use AI for complex or low-confidence cases
        ai_result = await self.ai_generator.generate_workflow(
            task_description,
            use_template=not force_ai,
            custom_parameters=parameters
        )

        return {
            "workflow_json": ai_result.workflow_json,
            "confidence": ai_result.confidence_score,
            "method": "ai_generation",
            "reasoning": ai_result.reasoning,
            "complexity_level": ai_result.complexity_level,
            "recommended_testing": ai_result.recommended_testing
        }


# Example usage
async def main():
    """Test the workflow generator"""
    generator = HybridWorkflowGenerator()

    # Test cases
    test_cases = [
        {
            "description": "Send an email notification when a new user signs up",
            "params": {
                "recipient_email": "team@example.com",
                "email_subject": "New User Signup"
            }
        },
        {
            "description": "Create a complex multi-step pipeline that fetches data from an API, transforms it, stores in database, and sends Slack notification",
            "params": {}
        }
    ]

    for test in test_cases:
        print(f"\n{'=' * 80}")
        print(f"Task: {test['description']}")
        print(f"{'=' * 80}")

        result = await generator.generate(
            test["description"],
            test["params"]
        )

        print(f"Method: {result['method']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Reasoning: {result['reasoning']}")
        print(f"\nWorkflow Preview:")
        print(json.dumps(result["workflow_json"], indent=2)[:500] + "...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
