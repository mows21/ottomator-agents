"""
Claude SDK Tools
================

Tool definitions and utilities for Claude Agent SDK.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
import json
import asyncio
from functools import wraps


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    content: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        """Convert to string for Claude."""
        if self.success:
            return self.content
        return f"Error: {self.error}"


@dataclass
class ClaudeTool:
    """
    Tool definition for Claude API.

    Example:
        tool = ClaudeTool(
            name="search",
            description="Search the web for information",
            parameters={
                "query": {"type": "string", "description": "Search query"},
            },
            required=["query"],
            handler=search_function,
        )
    """
    name: str
    description: str
    parameters: Dict[str, Dict[str, Any]]
    required: List[str] = field(default_factory=list)
    handler: Optional[Callable] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to Claude API tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required,
            },
        }

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        if not self.handler:
            return ToolResult(
                success=False,
                content="",
                error="No handler defined for this tool",
            )

        try:
            if asyncio.iscoroutinefunction(self.handler):
                result = await self.handler(**kwargs)
            else:
                result = self.handler(**kwargs)

            if isinstance(result, ToolResult):
                return result
            return ToolResult(success=True, content=str(result))

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e),
            )


class ToolRegistry:
    """
    Registry for Claude tools.

    Example:
        registry = ToolRegistry()

        @registry.tool(
            description="Search the web",
            parameters={"query": {"type": "string"}},
        )
        async def search(query: str) -> str:
            return f"Results for: {query}"

        # Get all tools for API
        tools = registry.to_api_format()
    """

    def __init__(self):
        self._tools: Dict[str, ClaudeTool] = {}

    def add(self, tool: ClaudeTool) -> None:
        """Add a tool to the registry."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ClaudeTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def tool(
        self,
        name: Optional[str] = None,
        description: str = "",
        parameters: Optional[Dict[str, Dict[str, Any]]] = None,
        required: Optional[List[str]] = None,
    ):
        """Decorator to register a tool."""
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or ""

            # Auto-generate parameters if not provided
            if parameters is None:
                import inspect
                sig = inspect.signature(func)
                auto_params = {}
                auto_required = []

                for param_name, param in sig.parameters.items():
                    param_type = "string"
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == float:
                            param_type = "number"
                        elif param.annotation == bool:
                            param_type = "boolean"
                        elif param.annotation == list:
                            param_type = "array"
                        elif param.annotation == dict:
                            param_type = "object"

                    auto_params[param_name] = {"type": param_type}
                    if param.default == inspect.Parameter.empty:
                        auto_required.append(param_name)

                final_params = auto_params
                final_required = required or auto_required
            else:
                final_params = parameters
                final_required = required or []

            tool = ClaudeTool(
                name=tool_name,
                description=tool_desc,
                parameters=final_params,
                required=final_required,
                handler=func,
            )
            self.add(tool)

            return func

        return decorator

    def to_api_format(self) -> List[Dict[str, Any]]:
        """Get all tools in Claude API format."""
        return [tool.to_api_format() for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                content="",
                error=f"Unknown tool: {name}",
            )
        return await tool.execute(**kwargs)

    def list_tools(self) -> List[str]:
        """List all tool names."""
        return list(self._tools.keys())


# Pre-built tools
def create_web_search_tool(
    search_function: Callable[[str], str],
) -> ClaudeTool:
    """Create a web search tool."""
    return ClaudeTool(
        name="web_search",
        description="Search the web for information. Use this when you need current information or facts.",
        parameters={
            "query": {
                "type": "string",
                "description": "The search query",
            },
        },
        required=["query"],
        handler=search_function,
    )


def create_calculator_tool() -> ClaudeTool:
    """Create a calculator tool."""
    def calculate(expression: str) -> str:
        try:
            # Safe eval for basic math
            allowed_names = {"abs": abs, "round": round, "min": min, "max": max}
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

    return ClaudeTool(
        name="calculator",
        description="Perform mathematical calculations. Supports basic operations (+, -, *, /, **) and functions (abs, round, min, max).",
        parameters={
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate",
            },
        },
        required=["expression"],
        handler=calculate,
    )


def create_datetime_tool() -> ClaudeTool:
    """Create a datetime tool."""
    from datetime import datetime, timezone

    def get_datetime(timezone_name: str = "UTC") -> str:
        import pytz
        try:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            return now.strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception:
            now = datetime.now(timezone.utc)
            return now.strftime("%Y-%m-%d %H:%M:%S UTC")

    return ClaudeTool(
        name="get_datetime",
        description="Get the current date and time in a specific timezone.",
        parameters={
            "timezone_name": {
                "type": "string",
                "description": "Timezone name (e.g., 'America/New_York', 'Europe/London'). Defaults to UTC.",
            },
        },
        required=[],
        handler=get_datetime,
    )


def create_json_tool() -> ClaudeTool:
    """Create a JSON parsing/formatting tool."""
    def json_tool(action: str, data: str) -> str:
        try:
            if action == "parse":
                parsed = json.loads(data)
                return json.dumps(parsed, indent=2)
            elif action == "validate":
                json.loads(data)
                return "Valid JSON"
            elif action == "minify":
                parsed = json.loads(data)
                return json.dumps(parsed, separators=(",", ":"))
            else:
                return f"Unknown action: {action}"
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {str(e)}"

    return ClaudeTool(
        name="json_tool",
        description="Parse, validate, or format JSON data.",
        parameters={
            "action": {
                "type": "string",
                "enum": ["parse", "validate", "minify"],
                "description": "The action to perform",
            },
            "data": {
                "type": "string",
                "description": "The JSON data to process",
            },
        },
        required=["action", "data"],
        handler=json_tool,
    )


# MCP-style tool wrapper
class MCPToolWrapper:
    """
    Wrapper to use MCP tools with Claude SDK.

    Example:
        mcp = MCPToolWrapper(mcp_client)
        tools = mcp.list_tools()
        result = await mcp.call_tool("brave_search", {"query": "AI news"})
    """

    def __init__(self, mcp_client: Any):
        self.client = mcp_client
        self._tools: Dict[str, Dict] = {}

    async def initialize(self) -> None:
        """Initialize and list available tools."""
        if hasattr(self.client, "list_tools"):
            tools = await self.client.list_tools()
            for tool in tools:
                self._tools[tool.name] = {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }

    def to_api_format(self) -> List[Dict[str, Any]]:
        """Get tools in Claude API format."""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"],
            }
            for tool in self._tools.values()
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Call an MCP tool."""
        try:
            result = await self.client.call_tool(name, arguments)
            return ToolResult(
                success=True,
                content=str(result.content) if hasattr(result, "content") else str(result),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e),
            )


# Global registry
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(
    name: Optional[str] = None,
    description: str = "",
    **kwargs,
):
    """Decorator to register a tool globally."""
    return get_global_registry().tool(name=name, description=description, **kwargs)
