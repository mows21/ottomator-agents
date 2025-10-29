"""MCP Server for Archon Motion AI.

Exposes project management capabilities as MCP tools that can be used with Claude Desktop.
"""

import asyncio
import json
from typing import Any
import httpx


# Configuration
API_URL = "http://localhost:8000"


async def create_project(name: str, description: str, auto_generate_plan: bool = True) -> dict:
    """
    Create a new project.

    Args:
        name: Project name
        description: Project description
        auto_generate_plan: Whether to generate AI plan automatically

    Returns:
        Created project data
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/projects",
            json={
                "name": name,
                "description": description,
                "auto_generate_plan": auto_generate_plan
            }
        )
        response.raise_for_status()
        return response.json()


async def create_task(
    project_id: str,
    title: str,
    description: str = "",
    priority: str = "medium",
    estimated_duration: int = 480
) -> dict:
    """
    Create a new task.

    Args:
        project_id: ID of the project
        title: Task title
        description: Task description
        priority: Priority (low, medium, high, urgent)
        estimated_duration: Estimated duration in minutes

    Returns:
        Created task data
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/tasks",
            json={
                "project_id": project_id,
                "title": title,
                "description": description,
                "priority": priority,
                "estimated_duration": estimated_duration
            }
        )
        response.raise_for_status()
        return response.json()


async def get_schedule(project_id: str = None, timeframe: str = "week") -> dict:
    """
    Get AI-optimized task schedule.

    Args:
        project_id: Optional project ID to filter
        timeframe: Timeframe (day, week, month)

    Returns:
        Optimized schedule
    """
    async with httpx.AsyncClient() as client:
        params = {"timeframe": timeframe}
        if project_id:
            params["project_id"] = project_id

        response = await client.get(
            f"{API_URL}/api/tasks/schedule",
            params=params
        )
        response.raise_for_status()
        return response.json()


async def generate_project_plan(project_id: str) -> dict:
    """
    Generate AI-powered project plan.

    Args:
        project_id: Project ID

    Returns:
        Generated plan
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/projects/{project_id}/generate-plan"
        )
        response.raise_for_status()
        return response.json()


async def execute_agent_workflow(task: str, context: dict = None) -> dict:
    """
    Execute multi-agent workflow.

    Args:
        task: Task description
        context: Optional context data

    Returns:
        Workflow results
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/agents/workflow",
            json={
                "task": task,
                "context": context or {}
            }
        )
        response.raise_for_status()
        return response.json()


# MCP Tool Definitions
MCP_TOOLS = [
    {
        "name": "create_project",
        "description": "Create a new project with optional AI-generated plan",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "description": {"type": "string", "description": "Project description"},
                "auto_generate_plan": {
                    "type": "boolean",
                    "description": "Generate AI plan automatically",
                    "default": True
                }
            },
            "required": ["name", "description"]
        }
    },
    {
        "name": "create_task",
        "description": "Create a new task in a project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"},
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "default": "medium"
                },
                "estimated_duration": {
                    "type": "integer",
                    "description": "Estimated duration in minutes",
                    "default": 480
                }
            },
            "required": ["project_id", "title"]
        }
    },
    {
        "name": "get_schedule",
        "description": "Get AI-optimized task schedule",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Optional project ID"},
                "timeframe": {
                    "type": "string",
                    "enum": ["day", "week", "month"],
                    "default": "week"
                }
            }
        }
    },
    {
        "name": "generate_plan",
        "description": "Generate comprehensive AI project plan",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"}
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "execute_workflow",
        "description": "Execute multi-agent workflow for complex tasks",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task description"},
                "context": {"type": "object", "description": "Optional context data"}
            },
            "required": ["task"]
        }
    }
]


# Tool dispatcher
TOOL_FUNCTIONS = {
    "create_project": create_project,
    "create_task": create_task,
    "get_schedule": get_schedule,
    "generate_plan": generate_project_plan,
    "execute_workflow": execute_agent_workflow,
}


async def handle_tool_call(tool_name: str, arguments: dict) -> Any:
    """
    Handle MCP tool call.

    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments

    Returns:
        Tool execution result
    """
    if tool_name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {tool_name}")

    func = TOOL_FUNCTIONS[tool_name]
    return await func(**arguments)


if __name__ == "__main__":
    print("Archon Motion AI - MCP Server")
    print("Tools available:", list(TOOL_FUNCTIONS.keys()))
