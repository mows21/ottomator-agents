"""
Pydantic AI Agent Implementation
================================

Full-featured Pydantic AI agent with integrated observability,
quality management, and ML context engineering.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Generic
import os

from platforms.core.base import BaseAgent, AgentConfig, AgentResponse, AgentCapability
from platforms.core.logging import StructuredLogger, LangfuseObserver, MetricsCollector
from platforms.core.quality import QualityManagementSystem
from platforms.core.ml_context import MLContextEngine, ContextType

try:
    from pydantic import BaseModel
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.models.openai import OpenAIModel
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.models.gemini import GeminiModel
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False
    BaseModel = object
    Agent = None
    RunContext = None


T = TypeVar("T")


@dataclass
class PydanticAIConfig(AgentConfig):
    """Extended configuration for Pydantic AI agents."""

    # Model configuration
    model_provider: str = "openai"  # openai, anthropic, gemini
    model: str = "gpt-4o-mini"

    # API keys (loaded from env if not provided)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Agent behavior
    retries: int = 3
    result_retries: int = 1

    # Tool configuration
    enable_tools: bool = True
    parallel_tool_calls: bool = True

    # Response configuration
    result_type: Optional[Type] = None

    def __post_init__(self):
        self.platform = "pydantic_ai"
        self.capabilities = [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
        ]


@dataclass
class PydanticDependencies:
    """
    Dependencies for Pydantic AI agent tools.

    This is passed to all tool functions via RunContext.
    """
    session_id: str = ""
    user_id: Optional[str] = None
    request_id: str = ""
    logger: Optional[StructuredLogger] = None
    metrics: Optional[MetricsCollector] = None
    observer: Optional[LangfuseObserver] = None
    context_engine: Optional[MLContextEngine] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def log(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a message from a tool."""
        if self.logger:
            self.logger.debug(f"[Tool] {message}", data)

    def record_tool_call(
        self,
        tool_name: str,
        success: bool,
        latency_ms: float,
    ) -> None:
        """Record a tool call in metrics."""
        if self.metrics:
            self.metrics.record_tool_call(tool_name, success, latency_ms)
        if self.observer:
            self.observer.log_tool_call(
                tool_name=tool_name,
                input_data={},
                output_data={},
                duration_ms=latency_ms,
                success=success,
            )


class PydanticAIAgent(BaseAgent[PydanticDependencies]):
    """
    Pydantic AI agent with full infrastructure integration.

    Features:
    - Type-safe tool definitions
    - Automatic observability
    - Quality management
    - ML context optimization
    - Multi-model support

    Example:
        config = PydanticAIConfig(
            name="my-agent",
            system_prompt="You are a helpful assistant.",
            model="gpt-4o",
        )

        agent = PydanticAIAgent(config)
        await agent.initialize()

        # Add tools
        @agent.tool
        async def search(ctx: RunContext[PydanticDependencies], query: str) -> str:
            '''Search the web for information.'''
            ctx.deps.log("Searching", {"query": query})
            return f"Results for: {query}"

        response = await agent.process("Search for AI news")
    """

    def __init__(self, config: Optional[PydanticAIConfig] = None):
        if not PYDANTIC_AI_AVAILABLE:
            raise ImportError(
                "pydantic-ai package is required. Install with: pip install pydantic-ai"
            )

        super().__init__(config or PydanticAIConfig())
        self.config: PydanticAIConfig = self.config
        self._agent: Optional[Agent] = None
        self._tools: Dict[str, Callable] = {}
        self._result_validators: List[Callable] = []

    def _get_model(self):
        """Get the appropriate model based on configuration."""
        provider = self.config.model_provider.lower()

        if provider == "openai":
            api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
            return OpenAIModel(self.config.model, api_key=api_key)

        elif provider == "anthropic":
            api_key = self.config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
            return AnthropicModel(self.config.model, api_key=api_key)

        elif provider == "gemini" or provider == "google":
            api_key = self.config.google_api_key or os.getenv("GOOGLE_API_KEY")
            return GeminiModel(self.config.model, api_key=api_key)

        else:
            raise ValueError(f"Unknown model provider: {provider}")

    async def _initialize(self) -> None:
        """Initialize the Pydantic AI agent."""
        model = self._get_model()

        # Create agent with or without result type
        if self.config.result_type:
            self._agent = Agent(
                model=model,
                system_prompt=self.config.system_prompt,
                result_type=self.config.result_type,
                deps_type=PydanticDependencies,
                retries=self.config.retries,
                result_retries=self.config.result_retries,
            )
        else:
            self._agent = Agent(
                model=model,
                system_prompt=self.config.system_prompt,
                deps_type=PydanticDependencies,
                retries=self.config.retries,
            )

        # Register any pre-defined tools
        for name, tool_fn in self._tools.items():
            self._agent.tool(tool_fn)

        # Register result validators
        for validator in self._result_validators:
            self._agent.result_validator(validator)

        if self.logger:
            self.logger.info("Pydantic AI agent initialized", {
                "model": self.config.model,
                "provider": self.config.model_provider,
                "tools": list(self._tools.keys()),
            })

    async def _process(self, message: str, **kwargs: Any) -> AgentResponse:
        """Process a message using Pydantic AI."""
        if not self._agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        # Create dependencies
        deps = PydanticDependencies(
            session_id=self._session_id or "",
            user_id=kwargs.get("user_id"),
            request_id=kwargs.get("request_id", ""),
            logger=self.logger,
            metrics=self.metrics,
            observer=self.observer,
            context_engine=self.context_engine,
            extra=kwargs,
        )

        # Get optimized context
        context_window = self.context_engine.optimize(query=message)

        # Build message history
        message_history = kwargs.get("message_history")
        if message_history is None and self._message_history:
            message_history = [
                {"role": m["role"], "content": m["content"]}
                for m in self._message_history[-self.config.max_history_messages:]
            ]

        try:
            start_time = time.perf_counter()

            # Run the agent
            result = await self._agent.run(
                message,
                deps=deps,
                message_history=message_history,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Extract response content
            if hasattr(result.data, "model_dump"):
                content = str(result.data.model_dump())
            else:
                content = str(result.data)

            # Calculate tokens
            usage = result.usage() if hasattr(result, "usage") else None
            prompt_tokens = usage.request_tokens if usage else 0
            completion_tokens = usage.response_tokens if usage else 0

            # Extract tool calls
            tools_used = []
            tool_results = []
            for msg in result.all_messages():
                if hasattr(msg, "parts"):
                    for part in msg.parts:
                        if hasattr(part, "tool_name"):
                            tools_used.append(part.tool_name)
                            tool_results.append({
                                "tool": part.tool_name,
                                "args": getattr(part, "args", {}),
                            })

            return AgentResponse(
                content=content,
                success=True,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                tools_used=tools_used,
                tool_results=tool_results,
                metadata={
                    "model": self.config.model,
                    "provider": self.config.model_provider,
                    "message_count": len(result.all_messages()),
                },
            )

        except Exception as e:
            if self.logger:
                self.logger.error("Pydantic AI processing failed", e)
            raise

    async def _cleanup(self) -> None:
        """Cleanup Pydantic AI agent."""
        self._agent = None

    def tool(
        self,
        func: Optional[Callable] = None,
        *,
        retries: int = 1,
    ):
        """
        Decorator to register a tool with the agent.

        Example:
            @agent.tool
            async def my_tool(ctx: RunContext[PydanticDependencies], arg: str) -> str:
                '''Tool description.'''
                return f"Result: {arg}"
        """
        def decorator(fn: Callable) -> Callable:
            # Store tool for registration during initialization
            self._tools[fn.__name__] = fn

            # If agent already initialized, register immediately
            if self._agent:
                self._agent.tool(fn, retries=retries)

            return fn

        if func is not None:
            return decorator(func)
        return decorator

    def result_validator(self, func: Callable) -> Callable:
        """
        Decorator to register a result validator.

        Example:
            @agent.result_validator
            async def validate(ctx: RunContext[PydanticDependencies], result: str) -> str:
                if len(result) < 10:
                    raise ValueError("Response too short")
                return result
        """
        self._result_validators.append(func)

        if self._agent:
            self._agent.result_validator(func)

        return func

    async def run_sync(self, message: str, **kwargs: Any) -> AgentResponse:
        """
        Synchronous wrapper for process().

        Useful for non-async contexts.
        """
        return await self.process(message, **kwargs)

    async def stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Stream responses from the agent.

        Yields partial responses as they are generated.

        Example:
            async for chunk in agent.stream("Tell me a story"):
                print(chunk, end="", flush=True)
        """
        if not self._agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        self._session_id = session_id or self._session_id

        deps = PydanticDependencies(
            session_id=self._session_id or "",
            user_id=kwargs.get("user_id"),
            logger=self.logger,
            metrics=self.metrics,
            observer=self.observer,
            context_engine=self.context_engine,
        )

        async with self._agent.run_stream(message, deps=deps) as result:
            async for chunk in result.stream_text():
                yield chunk


def create_pydantic_agent(
    name: str = "pydantic-agent",
    system_prompt: str = "You are a helpful AI assistant.",
    model: str = "gpt-4o-mini",
    model_provider: str = "openai",
    **kwargs: Any,
) -> PydanticAIAgent:
    """
    Factory function to create a Pydantic AI agent.

    Example:
        agent = create_pydantic_agent(
            name="search-agent",
            system_prompt="You help users search for information.",
            model="gpt-4o",
        )
        await agent.initialize()
    """
    config = PydanticAIConfig(
        name=name,
        system_prompt=system_prompt,
        model=model,
        model_provider=model_provider,
        **kwargs,
    )
    return PydanticAIAgent(config)


# Pre-built agent templates
async def create_research_agent() -> PydanticAIAgent:
    """Create a research-focused agent with web search capabilities."""
    config = PydanticAIConfig(
        name="research-agent",
        system_prompt="""You are an expert research assistant. You help users find accurate information and provide well-sourced answers.

When researching:
1. Use the search tool to find relevant information
2. Synthesize information from multiple sources
3. Cite your sources
4. Acknowledge uncertainty when appropriate""",
        model="gpt-4o",
        capabilities=[
            AgentCapability.TEXT_GENERATION,
            AgentCapability.TOOL_USE,
            AgentCapability.WEB_SEARCH,
        ],
    )

    agent = PydanticAIAgent(config)
    await agent.initialize()

    return agent


async def create_code_agent() -> PydanticAIAgent:
    """Create a coding-focused agent."""
    config = PydanticAIConfig(
        name="code-agent",
        system_prompt="""You are an expert programmer. You help users write, debug, and understand code.

Guidelines:
1. Write clean, well-documented code
2. Follow best practices for the language
3. Explain your code clearly
4. Consider edge cases and error handling""",
        model="gpt-4o",
        temperature=0.2,  # Lower temperature for more consistent code
        capabilities=[
            AgentCapability.TEXT_GENERATION,
            AgentCapability.TOOL_USE,
            AgentCapability.CODE_EXECUTION,
        ],
    )

    agent = PydanticAIAgent(config)
    await agent.initialize()

    return agent
