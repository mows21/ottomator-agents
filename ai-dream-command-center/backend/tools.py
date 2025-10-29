"""Tools that agents can use."""

import httpx
import asyncio
from typing import Any, Dict, Optional
from datetime import datetime


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self):
        self.tools: Dict[str, callable] = {}
        self.register_default_tools()

    def register(self, name: str, func: callable):
        """Register a new tool."""
        self.tools[name] = func

    def get_tool(self, name: str) -> Optional[callable]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> list:
        """List all available tools."""
        return list(self.tools.keys())

    def register_default_tools(self):
        """Register default tools."""
        self.register("web_search", web_search)
        self.register("calculate", calculate)
        self.register("get_current_time", get_current_time)
        self.register("analyze_data", analyze_data)
        self.register("code_executor", code_executor)


# Tool implementations

async def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search the web for information.

    Args:
        query: Search query
        max_results: Maximum number of results to return

    Returns:
        Search results with titles, URLs, and snippets
    """
    # This is a mock implementation
    # In production, integrate with Brave API, Google, etc.
    return {
        "query": query,
        "results": [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is a snippet for result {i+1} about {query}",
            }
            for i in range(min(max_results, 3))
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


async def calculate(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        Calculation result
    """
    try:
        # Whitelist safe operations
        allowed_chars = set("0123456789+-*/().% ")
        if not all(c in allowed_chars for c in expression):
            return {"error": "Invalid characters in expression"}

        result = eval(expression, {"__builtins__": {}}, {})
        return {"expression": expression, "result": result, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


async def get_current_time(timezone: str = "UTC") -> Dict[str, Any]:
    """
    Get current time in specified timezone.

    Args:
        timezone: Timezone name (default: UTC)

    Returns:
        Current time information
    """
    now = datetime.utcnow()
    return {
        "timezone": timezone,
        "datetime": now.isoformat(),
        "timestamp": now.timestamp(),
        "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
    }


async def analyze_data(data: list, analysis_type: str = "summary") -> Dict[str, Any]:
    """
    Analyze a dataset.

    Args:
        data: List of numbers or data points
        analysis_type: Type of analysis (summary, statistics, etc.)

    Returns:
        Analysis results
    """
    if not data:
        return {"error": "No data provided"}

    try:
        numeric_data = [float(x) for x in data]

        if analysis_type == "summary":
            return {
                "count": len(numeric_data),
                "sum": sum(numeric_data),
                "average": sum(numeric_data) / len(numeric_data),
                "min": min(numeric_data),
                "max": max(numeric_data),
            }
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}
    except Exception as e:
        return {"error": str(e)}


async def code_executor(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Execute code in a sandboxed environment (MOCK).

    Args:
        code: Code to execute
        language: Programming language

    Returns:
        Execution results

    Note: This is a mock. In production, use proper sandboxing.
    """
    return {
        "language": language,
        "code": code,
        "output": "[MOCK] Code execution disabled for safety",
        "success": False,
        "note": "This is a mock implementation. Use proper sandboxing in production.",
    }


# Global registry instance
tool_registry = ToolRegistry()
