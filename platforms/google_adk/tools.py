"""
Google ADK Tools
================

Tool utilities for Google ADK agents.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class GoogleTool:
    """Tool definition for Google Gemini."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Optional[Callable] = None

    def to_function_declaration(self) -> Dict[str, Any]:
        """Convert to Gemini function declaration format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


def create_google_search_tool() -> Dict[str, Any]:
    """
    Create Google Search grounding tool configuration.

    This enables the agent to use Google Search for grounding responses.
    """
    return {"google_search_retrieval": {}}


def create_code_execution_tool() -> Dict[str, Any]:
    """
    Create code execution tool configuration.

    This enables the agent to execute Python code.
    """
    return {"code_execution": {}}


def create_calculator_tool() -> GoogleTool:
    """Create a calculator tool."""
    def calculate(expression: str) -> str:
        try:
            allowed_names = {"abs": abs, "round": round, "min": min, "max": max}
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

    return GoogleTool(
        name="calculator",
        description="Perform mathematical calculations",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate",
                }
            },
            "required": ["expression"],
        },
        handler=calculate,
    )


def create_datetime_tool() -> GoogleTool:
    """Create a datetime tool."""
    from datetime import datetime, timezone

    def get_datetime(timezone_name: str = "UTC") -> str:
        try:
            import pytz
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            return now.strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception:
            now = datetime.now(timezone.utc)
            return now.strftime("%Y-%m-%d %H:%M:%S UTC")

    return GoogleTool(
        name="get_datetime",
        description="Get current date and time",
        parameters={
            "type": "object",
            "properties": {
                "timezone_name": {
                    "type": "string",
                    "description": "Timezone (e.g., 'America/New_York')",
                }
            },
        },
        handler=get_datetime,
    )


class ToolRegistry:
    """Registry for Google ADK tools."""

    def __init__(self):
        self._tools: Dict[str, GoogleTool] = {}

    def add(self, tool: GoogleTool) -> None:
        """Add a tool to the registry."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[GoogleTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def to_function_declarations(self) -> List[Dict[str, Any]]:
        """Get all tools as function declarations."""
        return [tool.to_function_declaration() for tool in self._tools.values()]

    def register(
        self,
        name: Optional[str] = None,
        description: str = "",
    ):
        """Decorator to register a tool."""
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or ""

            import inspect
            sig = inspect.signature(func)
            properties = {}
            required = []

            for param_name, param in sig.parameters.items():
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"

                properties[param_name] = {"type": param_type}
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)

            tool = GoogleTool(
                name=tool_name,
                description=tool_desc,
                parameters={
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
                handler=func,
            )
            self.add(tool)
            return func

        return decorator
