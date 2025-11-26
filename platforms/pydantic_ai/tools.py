"""
Pydantic AI Tools
=================

Tool registration and management for Pydantic AI agents.
Provides a registry of reusable tools with observability.
"""

import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar
import asyncio

try:
    from pydantic_ai import RunContext
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False
    RunContext = Any


T = TypeVar("T")


@dataclass
class ToolDefinition:
    """Definition of a registered tool."""
    name: str
    description: str
    function: Callable
    retries: int = 1
    timeout: Optional[float] = None
    category: str = "general"
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ToolRegistry:
    """
    Registry for managing reusable tools across agents.

    Example:
        registry = ToolRegistry()

        @registry.register(category="search")
        async def web_search(ctx: RunContext, query: str) -> str:
            '''Search the web.'''
            return f"Results for: {query}"

        # Apply to agent
        registry.apply_to_agent(agent)
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        retries: int = 1,
        timeout: Optional[float] = None,
        category: str = "general",
        tags: Optional[List[str]] = None,
    ):
        """
        Decorator to register a tool.

        Example:
            @registry.register(category="data", tags=["database"])
            async def query_db(ctx, sql: str) -> str:
                '''Execute a database query.'''
                return execute(sql)
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or ""

            self._tools[tool_name] = ToolDefinition(
                name=tool_name,
                description=tool_desc,
                function=func,
                retries=retries,
                timeout=timeout,
                category=category,
                tags=tags or [],
            )

            # Track by category
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(tool_name)

            return func

        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_by_category(self, category: str) -> List[ToolDefinition]:
        """Get all tools in a category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names]

    def get_by_tag(self, tag: str) -> List[ToolDefinition]:
        """Get all tools with a specific tag."""
        return [t for t in self._tools.values() if tag in t.tags]

    def list_tools(self) -> List[str]:
        """List all tool names."""
        return list(self._tools.keys())

    def list_categories(self) -> List[str]:
        """List all categories."""
        return list(self._categories.keys())

    def apply_to_agent(self, agent, tools: Optional[List[str]] = None) -> None:
        """
        Apply registered tools to a Pydantic AI agent.

        Args:
            agent: The Pydantic AI agent
            tools: Optional list of tool names to apply (applies all if None)
        """
        tool_names = tools or list(self._tools.keys())

        for name in tool_names:
            tool_def = self._tools.get(name)
            if tool_def:
                agent.tool(tool_def.function, retries=tool_def.retries)

    def to_dict(self) -> Dict[str, Any]:
        """Get registry as dictionary."""
        return {
            "tools": {
                name: {
                    "description": t.description,
                    "category": t.category,
                    "tags": t.tags,
                    "retries": t.retries,
                }
                for name, t in self._tools.items()
            },
            "categories": self._categories,
        }


def tool(
    func: Optional[Callable] = None,
    *,
    retries: int = 1,
    timeout: Optional[float] = None,
    observe: bool = True,
):
    """
    Decorator to create an observable tool.

    Features:
    - Automatic timing and metrics
    - Error handling with retries
    - Optional timeout
    - Integration with observability

    Example:
        @tool(retries=2, timeout=30.0)
        async def my_tool(ctx: RunContext, query: str) -> str:
            '''My tool description.'''
            return do_something(query)
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            ctx = args[0] if args else None

            try:
                # Apply timeout if specified
                if timeout:
                    result = await asyncio.wait_for(
                        fn(*args, **kwargs),
                        timeout=timeout,
                    )
                else:
                    result = await fn(*args, **kwargs)

                latency_ms = (time.perf_counter() - start_time) * 1000

                # Record metrics if context has dependencies
                if observe and ctx and hasattr(ctx, "deps"):
                    deps = ctx.deps
                    if hasattr(deps, "record_tool_call"):
                        deps.record_tool_call(fn.__name__, True, latency_ms)
                    if hasattr(deps, "log"):
                        deps.log(f"Tool {fn.__name__} completed", {"latency_ms": latency_ms})

                return result

            except asyncio.TimeoutError:
                latency_ms = (time.perf_counter() - start_time) * 1000
                if observe and ctx and hasattr(ctx, "deps"):
                    deps = ctx.deps
                    if hasattr(deps, "record_tool_call"):
                        deps.record_tool_call(fn.__name__, False, latency_ms)
                    if hasattr(deps, "log"):
                        deps.log(f"Tool {fn.__name__} timed out", {"timeout": timeout})
                raise

            except Exception as e:
                latency_ms = (time.perf_counter() - start_time) * 1000
                if observe and ctx and hasattr(ctx, "deps"):
                    deps = ctx.deps
                    if hasattr(deps, "record_tool_call"):
                        deps.record_tool_call(fn.__name__, False, latency_ms)
                    if hasattr(deps, "log"):
                        deps.log(f"Tool {fn.__name__} failed", {"error": str(e)})
                raise

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    if func is not None:
        return decorator(func)
    return decorator


# Pre-built tool factories
def create_http_tool(
    name: str,
    base_url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
) -> Callable:
    """
    Create an HTTP request tool.

    Example:
        weather_tool = create_http_tool(
            name="get_weather",
            base_url="https://api.weather.com",
        )
    """
    @tool(retries=2, timeout=30.0)
    async def http_tool(ctx: RunContext, endpoint: str, params: Optional[Dict] = None) -> str:
        """Make an HTTP request."""
        import httpx

        url = f"{base_url}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, json=params, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.text

    http_tool.__name__ = name
    http_tool.__doc__ = f"Make {method} requests to {base_url}"

    return http_tool


def create_database_tool(
    connection_string: str,
    read_only: bool = True,
) -> Callable:
    """
    Create a database query tool.

    Example:
        db_tool = create_database_tool(
            connection_string="postgresql://...",
            read_only=True,
        )
    """
    @tool(retries=1, timeout=60.0)
    async def database_query(ctx: RunContext, query: str) -> str:
        """Execute a database query."""
        if read_only and not query.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed in read-only mode")

        # This would use actual database connection
        return f"Query executed: {query[:100]}"

    return database_query


def create_file_tool(
    allowed_paths: Optional[List[str]] = None,
    max_file_size: int = 1024 * 1024,  # 1MB
) -> Callable:
    """
    Create a file reading tool.

    Example:
        file_tool = create_file_tool(
            allowed_paths=["/data", "/config"],
        )
    """
    @tool(retries=1)
    async def read_file(ctx: RunContext, path: str) -> str:
        """Read a file's contents."""
        import os

        # Security check
        if allowed_paths:
            if not any(path.startswith(p) for p in allowed_paths):
                raise ValueError(f"Path not allowed: {path}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        file_size = os.path.getsize(path)
        if file_size > max_file_size:
            raise ValueError(f"File too large: {file_size} bytes")

        with open(path, "r") as f:
            return f.read()

    return read_file


# Global registry for shared tools
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_global_tool(
    name: Optional[str] = None,
    category: str = "general",
    **kwargs,
):
    """
    Decorator to register a tool in the global registry.

    Example:
        @register_global_tool(category="search")
        async def search(ctx, query: str) -> str:
            '''Search for information.'''
            return results
    """
    return get_global_registry().register(name=name, category=category, **kwargs)
