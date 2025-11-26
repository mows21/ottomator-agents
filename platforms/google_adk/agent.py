"""
Google ADK Agent Implementation
===============================

Agent implementation using Google's Agent Development Kit
with Gemini models.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import os

from platforms.core.base import BaseAgent, AgentConfig, AgentResponse, AgentCapability
from platforms.core.logging import StructuredLogger, LangfuseObserver, MetricsCollector

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    genai = None


# Cost per 1M tokens for Gemini models (as of 2025)
GEMINI_COSTS = {
    "gemini-2.0-flash-exp": {"input": 0.075, "output": 0.3},
    "gemini-2.0-flash": {"input": 0.075, "output": 0.3},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.0},
    "gemini-1.5-pro-002": {"input": 1.25, "output": 5.0},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
    "gemini-1.5-flash-002": {"input": 0.075, "output": 0.3},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for token usage."""
    costs = GEMINI_COSTS.get(model, {"input": 0.1, "output": 0.3})
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return round(input_cost + output_cost, 6)


@dataclass
class GoogleADKConfig(AgentConfig):
    """Configuration for Google ADK agents."""

    # Model configuration
    model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_tokens: int = 8192

    # API configuration
    api_key: Optional[str] = None

    # Safety settings
    safety_threshold: str = "BLOCK_ONLY_HIGH"

    # Tool configuration
    enable_tools: bool = True
    enable_code_execution: bool = False
    enable_google_search: bool = False

    def __post_init__(self):
        self.platform = "google_adk"
        self.model_provider = "google"
        self.capabilities = [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.TOOL_USE,
            AgentCapability.IMAGE_ANALYSIS,
            AgentCapability.STREAMING,
        ]
        if self.enable_code_execution:
            self.capabilities.append(AgentCapability.CODE_EXECUTION)
        if self.enable_google_search:
            self.capabilities.append(AgentCapability.WEB_SEARCH)


@dataclass
class ToolDeclaration:
    """Declaration for a Gemini tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable


class GoogleADKAgent(BaseAgent):
    """
    Google ADK agent with full infrastructure integration.

    Features:
    - Gemini model integration
    - Google Search grounding
    - Code execution
    - Multi-modal support
    - Function calling

    Example:
        config = GoogleADKConfig(
            name="gemini-agent",
            system_prompt="You are a helpful assistant.",
            model="gemini-2.0-flash-exp",
            enable_google_search=True,
        )

        agent = GoogleADKAgent(config)
        await agent.initialize()

        response = await agent.process("What's the latest news?")
    """

    def __init__(self, config: Optional[GoogleADKConfig] = None):
        if not GOOGLE_AI_AVAILABLE:
            raise ImportError(
                "google-generativeai package is required. "
                "Install with: pip install google-generativeai"
            )

        super().__init__(config or GoogleADKConfig())
        self.config: GoogleADKConfig = self.config
        self._model = None
        self._chat = None
        self._tools: Dict[str, ToolDeclaration] = {}

    async def _initialize(self) -> None:
        """Initialize the Gemini model."""
        api_key = self.config.api_key or os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not provided")

        genai.configure(api_key=api_key)

        # Build tools list
        tools = self._build_tools()

        # Create model
        generation_config = GenerationConfig(
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            max_output_tokens=self.config.max_tokens,
        )

        self._model = genai.GenerativeModel(
            model_name=self.config.model,
            generation_config=generation_config,
            system_instruction=self.config.system_prompt,
            tools=tools if tools else None,
        )

        # Start chat session
        self._chat = self._model.start_chat(history=[])

        if self.logger:
            self.logger.info("Google ADK agent initialized", {
                "model": self.config.model,
                "tools": list(self._tools.keys()),
                "google_search": self.config.enable_google_search,
                "code_execution": self.config.enable_code_execution,
            })

    def _build_tools(self) -> Optional[List]:
        """Build tools for the model."""
        if not self.config.enable_tools:
            return None

        tools = []

        # Add Google Search if enabled
        if self.config.enable_google_search:
            tools.append(genai.Tool(google_search_retrieval=genai.GoogleSearchRetrieval()))

        # Add code execution if enabled
        if self.config.enable_code_execution:
            tools.append(genai.Tool(code_execution=genai.CodeExecution()))

        # Add custom function declarations
        if self._tools:
            function_declarations = []
            for tool in self._tools.values():
                function_declarations.append(
                    genai.FunctionDeclaration(
                        name=tool.name,
                        description=tool.description,
                        parameters=tool.parameters,
                    )
                )
            if function_declarations:
                tools.append(genai.Tool(function_declarations=function_declarations))

        return tools if tools else None

    async def _process(self, message: str, **kwargs: Any) -> AgentResponse:
        """Process a message using Gemini."""
        if not self._chat:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        try:
            start_time = time.perf_counter()

            # Send message
            response = await asyncio.to_thread(
                self._chat.send_message,
                message,
            )

            # Process function calls if any
            tools_used = []
            tool_results = []

            while response.candidates[0].finish_reason.name == "TOOL_CALL":
                function_calls = []
                for part in response.parts:
                    if hasattr(part, "function_call"):
                        fc = part.function_call
                        function_calls.append({
                            "name": fc.name,
                            "args": dict(fc.args),
                        })

                # Execute function calls
                function_responses = []
                for fc in function_calls:
                    result = await self._execute_function(fc["name"], fc["args"])
                    tools_used.append(fc["name"])
                    tool_results.append({
                        "function": fc["name"],
                        "args": fc["args"],
                        "result": result,
                    })
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fc["name"],
                                response={"result": str(result)},
                            )
                        )
                    )

                # Continue conversation with function results
                response = await asyncio.to_thread(
                    self._chat.send_message,
                    function_responses,
                )

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Extract text content
            content = response.text if hasattr(response, "text") else ""

            # Get token usage
            usage_metadata = getattr(response, "usage_metadata", None)
            prompt_tokens = getattr(usage_metadata, "prompt_token_count", 0) if usage_metadata else 0
            completion_tokens = getattr(usage_metadata, "candidates_token_count", 0) if usage_metadata else 0

            # Calculate cost
            cost = calculate_cost(self.config.model, prompt_tokens, completion_tokens)

            return AgentResponse(
                content=content,
                success=True,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost_usd=cost,
                tools_used=tools_used,
                tool_results=tool_results,
                metadata={
                    "model": self.config.model,
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                },
            )

        except Exception as e:
            if self.logger:
                self.logger.error("Gemini processing failed", e)
            raise

    async def _execute_function(self, name: str, args: Dict[str, Any]) -> Any:
        """Execute a function call."""
        tool = self._tools.get(name)
        if not tool:
            return f"Unknown function: {name}"

        start_time = time.perf_counter()
        try:
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**args)
            else:
                result = tool.handler(**args)

            latency_ms = (time.perf_counter() - start_time) * 1000

            if self.metrics:
                self.metrics.record_tool_call(name, True, latency_ms)

            return result

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000

            if self.metrics:
                self.metrics.record_tool_call(name, False, latency_ms)

            if self.logger:
                self.logger.error(f"Function execution failed: {name}", e)

            return f"Error: {str(e)}"

    async def _cleanup(self) -> None:
        """Cleanup resources."""
        self._model = None
        self._chat = None

    def add_function(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
    ) -> None:
        """
        Add a function (tool) to the agent.

        Example:
            agent.add_function(
                name="get_weather",
                description="Get current weather for a location",
                parameters={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name"
                        }
                    },
                    "required": ["location"]
                },
                handler=get_weather_handler,
            )
        """
        self._tools[name] = ToolDeclaration(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )

        if self.logger:
            self.logger.debug(f"Added function: {name}")

    def function(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Decorator to add a function to the agent.

        Example:
            @agent.function(description="Search the web")
            def search(query: str) -> str:
                return f"Results for: {query}"
        """
        def decorator(func: Callable) -> Callable:
            func_name = name or func.__name__
            func_desc = description or func.__doc__ or ""

            # Auto-generate parameters from signature
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

            parameters = {
                "type": "object",
                "properties": properties,
                "required": required,
            }

            self.add_function(func_name, func_desc, parameters, func)
            return func

        return decorator

    async def stream(
        self,
        message: str,
        **kwargs: Any,
    ):
        """
        Stream responses from Gemini.

        Example:
            async for chunk in agent.stream("Tell me a story"):
                print(chunk, end="", flush=True)
        """
        if not self._model:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        response = await asyncio.to_thread(
            self._model.generate_content,
            message,
            stream=True,
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text


def create_google_agent(
    name: str = "gemini-agent",
    system_prompt: str = "You are a helpful AI assistant.",
    model: str = "gemini-2.0-flash-exp",
    enable_google_search: bool = False,
    enable_code_execution: bool = False,
    **kwargs: Any,
) -> GoogleADKAgent:
    """
    Factory function to create a Google ADK agent.

    Example:
        agent = create_google_agent(
            name="search-agent",
            system_prompt="You help users search for information.",
            enable_google_search=True,
        )
        await agent.initialize()
    """
    config = GoogleADKConfig(
        name=name,
        system_prompt=system_prompt,
        model=model,
        enable_google_search=enable_google_search,
        enable_code_execution=enable_code_execution,
        **kwargs,
    )
    return GoogleADKAgent(config)


async def create_flash_agent(
    name: str = "flash-agent",
    system_prompt: str = "You are a fast and efficient AI assistant.",
) -> GoogleADKAgent:
    """Create a fast Gemini Flash agent."""
    config = GoogleADKConfig(
        name=name,
        system_prompt=system_prompt,
        model="gemini-2.0-flash-exp",
    )
    agent = GoogleADKAgent(config)
    await agent.initialize()
    return agent


async def create_pro_agent(
    name: str = "pro-agent",
    system_prompt: str = "You are an expert AI assistant with advanced capabilities.",
) -> GoogleADKAgent:
    """Create a Gemini Pro agent for complex tasks."""
    config = GoogleADKConfig(
        name=name,
        system_prompt=system_prompt,
        model="gemini-1.5-pro-002",
        enable_google_search=True,
        enable_code_execution=True,
    )
    agent = GoogleADKAgent(config)
    await agent.initialize()
    return agent
