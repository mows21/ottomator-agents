"""
Base Agent
==========

Abstract base class for all agent implementations across platforms.
Provides common interface, configuration, and lifecycle management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from uuid import uuid4

from platforms.core.logging.structured_logger import StructuredLogger
from platforms.core.logging.langfuse_integration import LangfuseObserver
from platforms.core.logging.metrics import MetricsCollector
from platforms.core.quality.qms import QualityManagementSystem
from platforms.core.ml_context.context_engine import MLContextEngine, ContextType


class AgentCapability(str, Enum):
    """Capabilities that agents can have."""
    TEXT_GENERATION = "text_generation"
    TOOL_USE = "tool_use"
    CODE_EXECUTION = "code_execution"
    WEB_SEARCH = "web_search"
    FILE_ACCESS = "file_access"
    DATABASE_ACCESS = "database_access"
    IMAGE_GENERATION = "image_generation"
    IMAGE_ANALYSIS = "image_analysis"
    AUDIO_PROCESSING = "audio_processing"
    MEMORY = "memory"
    MULTI_AGENT = "multi_agent"
    STREAMING = "streaming"
    RAG = "rag"


class AgentState(str, Enum):
    """Agent lifecycle states."""
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentConfig:
    """
    Configuration for an agent.

    Provides standardized configuration across all platforms.
    """
    # Identity
    agent_id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "agent"
    description: str = ""
    version: str = "1.0.0"

    # Platform
    platform: str = "base"
    model: str = "gpt-4o-mini"
    model_provider: str = "openai"

    # Prompts
    system_prompt: str = "You are a helpful AI assistant."
    temperature: float = 0.7
    max_tokens: int = 4096

    # Context
    max_context_tokens: int = 8000
    context_strategy: str = "hybrid"

    # Capabilities
    capabilities: List[AgentCapability] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)

    # Quality
    enable_qms: bool = True
    enable_validation: bool = True

    # Observability
    enable_logging: bool = True
    enable_metrics: bool = True
    enable_langfuse: bool = True
    log_level: str = "INFO"

    # Session
    session_timeout_seconds: int = 3600
    max_history_messages: int = 50

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "platform": self.platform,
            "model": self.model,
            "capabilities": [c.value for c in self.capabilities],
            "tools": self.tools,
            "metadata": self.metadata,
            "tags": self.tags,
        }


@dataclass
class AgentResponse:
    """
    Standardized response from an agent.

    All platforms return this common response format.
    """
    # Core response
    content: str
    success: bool = True
    error: Optional[str] = None

    # Metadata
    response_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    session_id: str = ""
    request_id: str = ""

    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: float = 0.0

    # Token usage
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0

    # Tool usage
    tools_used: List[str] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)

    # Quality
    quality_score: Optional[float] = None
    quality_issues: List[str] = field(default_factory=list)

    # Streaming
    is_streaming: bool = False
    is_complete: bool = True

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "success": self.success,
            "error": self.error,
            "response_id": self.response_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "latency_ms": round(self.latency_ms, 2),
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "tools_used": self.tools_used,
            "quality_score": self.quality_score,
            "is_complete": self.is_complete,
            "created_at": self.created_at.isoformat(),
        }


T = TypeVar("T")


class BaseAgent(ABC, Generic[T]):
    """
    Abstract base class for all agent implementations.

    Provides:
    - Common initialization
    - Logging and metrics
    - Quality management
    - Context management
    - Lifecycle hooks

    Subclasses must implement:
    - _initialize(): Platform-specific initialization
    - _process(): Core processing logic
    - _cleanup(): Cleanup on shutdown

    Example:
        class MyAgent(BaseAgent):
            async def _initialize(self):
                self.client = MyLLMClient()

            async def _process(self, message: str, **kwargs) -> AgentResponse:
                result = await self.client.complete(message)
                return AgentResponse(content=result)

            async def _cleanup(self):
                await self.client.close()
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.state = AgentState.INITIALIZING

        # Initialize infrastructure
        self._setup_infrastructure()

        # Agent state
        self._session_id: Optional[str] = None
        self._message_history: List[Dict[str, Any]] = []
        self._created_at = datetime.now(timezone.utc)

    def _setup_infrastructure(self) -> None:
        """Set up logging, metrics, QMS, and context engine."""
        # Logging
        if self.config.enable_logging:
            self.logger = StructuredLogger(
                name=f"agent-{self.config.name}",
                platform=self.config.platform,
            )
        else:
            self.logger = None

        # Metrics
        if self.config.enable_metrics:
            self.metrics = MetricsCollector(name=f"agent-{self.config.name}")
        else:
            self.metrics = None

        # Langfuse
        if self.config.enable_langfuse:
            self.observer = LangfuseObserver.from_env(logger=self.logger)
        else:
            self.observer = None

        # Quality Management
        if self.config.enable_qms:
            self.qms = QualityManagementSystem(
                agent_id=self.config.agent_id,
                platform=self.config.platform,
                logger=self.logger,
                metrics=self.metrics,
            )
        else:
            self.qms = None

        # Context Engine
        self.context_engine = MLContextEngine(
            max_tokens=self.config.max_context_tokens,
            logger=self.logger,
        )

        # Add system prompt as reserved context
        self.context_engine.add_context(
            self.config.system_prompt,
            ContextType.SYSTEM,
            reserved=True,
        )

    async def initialize(self) -> None:
        """Initialize the agent."""
        if self.logger:
            self.logger.info("Initializing agent", self.config.to_dict())

        try:
            await self._initialize()
            self.state = AgentState.READY

            if self.logger:
                self.logger.info("Agent initialized successfully")

        except Exception as e:
            self.state = AgentState.ERROR
            if self.logger:
                self.logger.error("Agent initialization failed", e)
            raise

    @abstractmethod
    async def _initialize(self) -> None:
        """Platform-specific initialization. Override in subclass."""
        pass

    async def process(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Process a message and return a response.

        This is the main entry point for agent interactions.
        """
        import time
        start_time = time.perf_counter()

        # Set session context
        self._session_id = session_id or str(uuid4())
        request_id = request_id or str(uuid4())

        # Create logger context
        if self.logger:
            context_logger = self.logger.with_context(
                session_id=self._session_id,
                user_id=user_id,
                request_id=request_id,
            )
        else:
            context_logger = None

        # Start trace
        if self.observer:
            self.observer.start_trace(
                name=f"{self.config.name}:process",
                session_id=self._session_id,
                user_id=user_id,
            )

        self.state = AgentState.PROCESSING

        try:
            if context_logger:
                context_logger.info("Processing message", {"message_length": len(message)})

            # Add message to context
            self.context_engine.add_context(message, ContextType.USER)

            # Add to history
            self._message_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Trim history if needed
            if len(self._message_history) > self.config.max_history_messages:
                self._message_history = self._message_history[-self.config.max_history_messages:]

            # Process with platform-specific logic
            response = await self._process(message, **kwargs)

            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000
            response.latency_ms = latency_ms
            response.agent_id = self.config.agent_id
            response.session_id = self._session_id
            response.request_id = request_id

            # Add response to history
            self._message_history.append({
                "role": "assistant",
                "content": response.content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Add response to context
            self.context_engine.add_context(response.content, ContextType.ASSISTANT)

            # Quality evaluation
            if self.qms and response.success:
                quality_report = self.qms.evaluate_response(
                    response=response.content,
                    latency_ms=latency_ms,
                    tokens_used=response.total_tokens,
                    model=self.config.model,
                )
                response.quality_score = quality_report.overall_score
                response.quality_issues = [
                    issue.title for issue in quality_report.issues
                ]

            # Record metrics
            if self.metrics:
                self.metrics.record_request(
                    platform=self.config.platform,
                    agent_id=self.config.agent_id,
                    success=response.success,
                    latency_ms=latency_ms,
                )
                self.metrics.record_tokens(
                    model=self.config.model,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                    cost_usd=response.cost_usd,
                )

            # Log completion
            if context_logger:
                context_logger.info("Message processed", {
                    "latency_ms": latency_ms,
                    "tokens": response.total_tokens,
                    "success": response.success,
                    "quality_score": response.quality_score,
                })

            # End trace
            if self.observer:
                self.observer.log_generation(
                    name="completion",
                    model=self.config.model,
                    prompt=message,
                    completion=response.content,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                )
                self.observer.end_trace(output=response.content)

            self.state = AgentState.READY
            return response

        except Exception as e:
            self.state = AgentState.ERROR

            if context_logger:
                context_logger.error("Processing failed", e)

            if self.observer:
                self.observer.end_trace(status="error")

            latency_ms = (time.perf_counter() - start_time) * 1000

            return AgentResponse(
                content="",
                success=False,
                error=str(e),
                agent_id=self.config.agent_id,
                session_id=self._session_id,
                request_id=request_id,
                latency_ms=latency_ms,
            )

    @abstractmethod
    async def _process(self, message: str, **kwargs: Any) -> AgentResponse:
        """Platform-specific processing. Override in subclass."""
        pass

    async def shutdown(self) -> None:
        """Shutdown the agent and cleanup resources."""
        if self.logger:
            self.logger.info("Shutting down agent")

        self.state = AgentState.SHUTDOWN

        try:
            await self._cleanup()

            if self.observer:
                self.observer.shutdown()

            if self.logger:
                self.logger.info("Agent shutdown complete")

        except Exception as e:
            if self.logger:
                self.logger.error("Error during shutdown", e)

    @abstractmethod
    async def _cleanup(self) -> None:
        """Platform-specific cleanup. Override in subclass."""
        pass

    def get_history(self) -> List[Dict[str, Any]]:
        """Get message history."""
        return self._message_history.copy()

    def clear_history(self) -> None:
        """Clear message history."""
        self._message_history.clear()
        self.context_engine.clear(keep_reserved=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        stats = {
            "agent_id": self.config.agent_id,
            "name": self.config.name,
            "platform": self.config.platform,
            "state": self.state.value,
            "created_at": self._created_at.isoformat(),
            "session_id": self._session_id,
            "history_length": len(self._message_history),
            "config": self.config.to_dict(),
        }

        if self.metrics:
            stats["metrics"] = self.metrics.get_summary()

        if self.context_engine:
            stats["context"] = self.context_engine.get_stats()

        return stats


class SimpleAgent(BaseAgent):
    """
    A simple agent implementation for testing and examples.

    This agent echoes back messages with some transformation.
    """

    async def _initialize(self) -> None:
        """No special initialization needed."""
        pass

    async def _process(self, message: str, **kwargs: Any) -> AgentResponse:
        """Echo back the message."""
        response_content = f"I received your message: {message}"

        return AgentResponse(
            content=response_content,
            success=True,
            prompt_tokens=len(message) // 4,
            completion_tokens=len(response_content) // 4,
            total_tokens=(len(message) + len(response_content)) // 4,
        )

    async def _cleanup(self) -> None:
        """No special cleanup needed."""
        pass
