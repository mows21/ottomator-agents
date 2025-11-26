"""
Claude Agent SDK Agent Implementation
=====================================

Full-featured Claude Agent SDK agent with integrated observability,
quality management, and ML context engineering.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Type, Union
import os
import json

from platforms.core.base import BaseAgent, AgentConfig, AgentResponse, AgentCapability
from platforms.core.logging import StructuredLogger, LangfuseObserver, MetricsCollector
from platforms.core.quality import QualityManagementSystem
from platforms.core.ml_context import MLContextEngine, ContextType

try:
    import anthropic
    from anthropic import Anthropic, AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None
    AsyncAnthropic = None


# Cost per 1M tokens for Claude models (as of 2025)
CLAUDE_COSTS = {
    "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for token usage."""
    costs = CLAUDE_COSTS.get(model, {"input": 3.0, "output": 15.0})
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return round(input_cost + output_cost, 6)


@dataclass
class ClaudeSDKConfig(AgentConfig):
    """Configuration for Claude Agent SDK agents."""

    # Model configuration
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: Optional[int] = None

    # API configuration
    api_key: Optional[str] = None
    timeout: float = 300.0
    max_retries: int = 3

    # Extended thinking (for complex reasoning)
    enable_extended_thinking: bool = False
    thinking_budget: int = 10000

    # Tool configuration
    enable_tools: bool = True
    parallel_tool_use: bool = True

    # Streaming
    enable_streaming: bool = False

    def __post_init__(self):
        self.platform = "claude_sdk"
        self.model_provider = "anthropic"
        self.capabilities = [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
            AgentCapability.IMAGE_ANALYSIS,
        ]


@dataclass
class ToolDefinition:
    """Definition of a tool for Claude."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable


class ClaudeSDKAgent(BaseAgent):
    """
    Claude Agent SDK agent with full infrastructure integration.

    Features:
    - Direct Claude API integration
    - Tool use with function calling
    - Extended thinking for complex tasks
    - Streaming support
    - Cost tracking
    - Full observability

    Example:
        config = ClaudeSDKConfig(
            name="claude-agent",
            system_prompt="You are a helpful assistant.",
            model="claude-sonnet-4-5-20250929",
        )

        agent = ClaudeSDKAgent(config)
        await agent.initialize()

        # Add tools
        agent.add_tool(
            name="search",
            description="Search the web",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
            handler=search_handler,
        )

        response = await agent.process("Search for AI news")
    """

    def __init__(self, config: Optional[ClaudeSDKConfig] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package is required. Install with: pip install anthropic"
            )

        super().__init__(config or ClaudeSDKConfig())
        self.config: ClaudeSDKConfig = self.config
        self._client: Optional[AsyncAnthropic] = None
        self._sync_client: Optional[Anthropic] = None
        self._tools: Dict[str, ToolDefinition] = {}

    async def _initialize(self) -> None:
        """Initialize the Claude client."""
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided")

        self._client = AsyncAnthropic(
            api_key=api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

        self._sync_client = Anthropic(
            api_key=api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

        if self.logger:
            self.logger.info("Claude SDK agent initialized", {
                "model": self.config.model,
                "tools": list(self._tools.keys()),
            })

    async def _process(self, message: str, **kwargs: Any) -> AgentResponse:
        """Process a message using Claude API."""
        if not self._client:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        # Build messages
        messages = self._build_messages(message, kwargs.get("message_history"))

        # Build tools list
        tools = self._build_tools() if self.config.enable_tools and self._tools else None

        # Create API request parameters
        params = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "system": self.config.system_prompt,
            "messages": messages,
            "temperature": self.config.temperature,
        }

        if tools:
            params["tools"] = tools

        if self.config.top_k:
            params["top_k"] = self.config.top_k

        # Add extended thinking if enabled
        if self.config.enable_extended_thinking:
            params["metadata"] = {
                "extended_thinking": {
                    "enabled": True,
                    "budget_tokens": self.config.thinking_budget,
                }
            }

        try:
            start_time = time.perf_counter()

            # Make API call
            response = await self._client.messages.create(**params)

            # Process tool calls if any
            tools_used = []
            tool_results_list = []

            while response.stop_reason == "tool_use":
                # Extract tool calls
                tool_calls = [
                    block for block in response.content
                    if block.type == "tool_use"
                ]

                tool_results = []
                for tool_call in tool_calls:
                    tool_name = tool_call.name
                    tool_input = tool_call.input
                    tools_used.append(tool_name)

                    # Execute tool
                    result = await self._execute_tool(tool_name, tool_input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": str(result),
                    })
                    tool_results_list.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "output": result,
                    })

                # Continue conversation with tool results
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

                response = await self._client.messages.create(**{**params, "messages": messages})

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Extract text content
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = calculate_cost(self.config.model, input_tokens, output_tokens)

            return AgentResponse(
                content=content,
                success=True,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=cost,
                tools_used=tools_used,
                tool_results=tool_results_list,
                metadata={
                    "model": self.config.model,
                    "stop_reason": response.stop_reason,
                    "message_id": response.id,
                },
            )

        except anthropic.APIError as e:
            if self.logger:
                self.logger.error("Claude API error", e)
            raise

    def _build_messages(
        self,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Build messages list for API call."""
        messages = []

        # Add history
        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # Add current message
        messages.append({"role": "user", "content": message})

        return messages

    def _build_tools(self) -> List[Dict[str, Any]]:
        """Build tools list for API call."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    async def _execute_tool(self, name: str, input_data: Dict[str, Any]) -> Any:
        """Execute a tool and return the result."""
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Unknown tool '{name}'"

        start_time = time.perf_counter()
        try:
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**input_data)
            else:
                result = tool.handler(**input_data)

            latency_ms = (time.perf_counter() - start_time) * 1000

            if self.metrics:
                self.metrics.record_tool_call(name, True, latency_ms)

            if self.observer:
                self.observer.log_tool_call(
                    tool_name=name,
                    input_data=input_data,
                    output_data=result,
                    duration_ms=latency_ms,
                    success=True,
                )

            return result

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000

            if self.metrics:
                self.metrics.record_tool_call(name, False, latency_ms)

            if self.logger:
                self.logger.error(f"Tool execution failed: {name}", e)

            return f"Error executing tool: {str(e)}"

    async def _cleanup(self) -> None:
        """Cleanup Claude client."""
        self._client = None
        self._sync_client = None

    def add_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable,
    ) -> None:
        """
        Add a tool to the agent.

        Example:
            def search(query: str) -> str:
                return f"Results for: {query}"

            agent.add_tool(
                name="search",
                description="Search the web for information",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                },
                handler=search,
            )
        """
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )

        if self.logger:
            self.logger.debug(f"Added tool: {name}")

    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Decorator to add a tool to the agent.

        Example:
            @agent.tool(description="Search the web")
            def search(query: str) -> str:
                '''Search for information.'''
                return f"Results for: {query}"
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or ""

            # Auto-generate input schema from function signature
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

            input_schema = {
                "type": "object",
                "properties": properties,
                "required": required,
            }

            self.add_tool(tool_name, tool_desc, input_schema, func)
            return func

        return decorator

    async def stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Stream responses from Claude.

        Example:
            async for chunk in agent.stream("Tell me a story"):
                print(chunk, end="", flush=True)
        """
        if not self._client:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        messages = self._build_messages(message, kwargs.get("message_history"))

        async with self._client.messages.stream(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=self.config.system_prompt,
            messages=messages,
            temperature=self.config.temperature,
        ) as stream:
            async for text in stream.text_stream:
                yield text


def create_claude_agent(
    name: str = "claude-agent",
    system_prompt: str = "You are a helpful AI assistant.",
    model: str = "claude-sonnet-4-5-20250929",
    **kwargs: Any,
) -> ClaudeSDKAgent:
    """
    Factory function to create a Claude SDK agent.

    Example:
        agent = create_claude_agent(
            name="research-agent",
            system_prompt="You are a research assistant.",
            model="claude-sonnet-4-5-20250929",
        )
        await agent.initialize()
    """
    config = ClaudeSDKConfig(
        name=name,
        system_prompt=system_prompt,
        model=model,
        **kwargs,
    )
    return ClaudeSDKAgent(config)


async def create_opus_agent(
    name: str = "opus-agent",
    system_prompt: str = "You are an expert AI assistant capable of complex reasoning.",
) -> ClaudeSDKAgent:
    """Create a Claude Opus agent for complex tasks."""
    config = ClaudeSDKConfig(
        name=name,
        system_prompt=system_prompt,
        model="claude-opus-4-5-20251101",
        enable_extended_thinking=True,
        thinking_budget=20000,
    )
    agent = ClaudeSDKAgent(config)
    await agent.initialize()
    return agent


async def create_haiku_agent(
    name: str = "haiku-agent",
    system_prompt: str = "You are a fast and efficient AI assistant.",
) -> ClaudeSDKAgent:
    """Create a Claude Haiku agent for fast responses."""
    config = ClaudeSDKConfig(
        name=name,
        system_prompt=system_prompt,
        model="claude-3-5-haiku-20241022",
        max_tokens=2048,
    )
    agent = ClaudeSDKAgent(config)
    await agent.initialize()
    return agent
