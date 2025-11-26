"""
Langfuse Observability Integration
==================================

Deep integration with Langfuse for LLM observability:
- Automatic trace creation
- Token usage tracking
- Cost calculation
- Prompt/completion logging
- Latency metrics
- Custom spans and events
"""

import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, TypeVar
from functools import wraps
import asyncio
from uuid import uuid4

try:
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None

from platforms.core.logging.structured_logger import StructuredLogger, LogEntry


@dataclass
class LangfuseConfig:
    """Configuration for Langfuse integration."""
    public_key: Optional[str] = None
    secret_key: Optional[str] = None
    host: str = "https://cloud.langfuse.com"
    enabled: bool = True
    debug: bool = False
    flush_at: int = 10
    flush_interval: float = 1.0
    sample_rate: float = 1.0  # 1.0 = 100% sampling

    @classmethod
    def from_env(cls) -> "LangfuseConfig":
        """Load configuration from environment variables."""
        return cls(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            enabled=os.getenv("LANGFUSE_ENABLED", "true").lower() == "true",
            debug=os.getenv("LANGFUSE_DEBUG", "false").lower() == "true",
            sample_rate=float(os.getenv("LANGFUSE_SAMPLE_RATE", "1.0")),
        )


@dataclass
class TraceMetrics:
    """Metrics collected during a trace."""
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost_usd: float = 0.0
    model: Optional[str] = None
    latency_ms: float = 0.0
    tool_calls: int = 0
    errors: int = 0
    success: bool = True

    def finalize(self) -> None:
        """Calculate final metrics."""
        self.end_time = datetime.now(timezone.utc)
        if self.start_time:
            self.latency_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_cost_usd": self.total_cost_usd,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "tool_calls": self.tool_calls,
            "errors": self.errors,
            "success": self.success,
        }


# Cost per 1M tokens for common models (as of 2025)
MODEL_COSTS = {
    # Claude models
    "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
    # OpenAI models
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    # Google models
    "gemini-2.0-flash": {"input": 0.075, "output": 0.3},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.0},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate cost in USD for token usage."""
    costs = MODEL_COSTS.get(model, {"input": 0.0, "output": 0.0})
    input_cost = (prompt_tokens / 1_000_000) * costs["input"]
    output_cost = (completion_tokens / 1_000_000) * costs["output"]
    return round(input_cost + output_cost, 6)


class LangfuseObserver:
    """
    Langfuse observability integration for comprehensive LLM monitoring.

    Features:
    - Automatic trace creation and management
    - Token usage and cost tracking
    - Prompt/completion logging
    - Latency metrics
    - Custom spans and events
    - Integration with StructuredLogger

    Example:
        observer = LangfuseObserver.from_env()

        @observer.trace("chat_completion")
        async def chat(message: str) -> str:
            observer.log_prompt(message)
            result = await llm.complete(message)
            observer.log_completion(result, tokens=100)
            return result
    """

    def __init__(
        self,
        config: Optional[LangfuseConfig] = None,
        logger: Optional[StructuredLogger] = None,
    ):
        self.config = config or LangfuseConfig.from_env()
        self.logger = logger or StructuredLogger(name="langfuse-observer")
        self._client: Optional[Langfuse] = None
        self._traces: Dict[str, Any] = {}
        self._current_trace_id: Optional[str] = None
        self._metrics: Dict[str, TraceMetrics] = {}

        if self.config.enabled and LANGFUSE_AVAILABLE:
            self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Langfuse client."""
        if not self.config.public_key or not self.config.secret_key:
            self.logger.warning("Langfuse credentials not configured, observability disabled")
            return

        try:
            self._client = Langfuse(
                public_key=self.config.public_key,
                secret_key=self.config.secret_key,
                host=self.config.host,
                debug=self.config.debug,
            )
            self.logger.info("Langfuse client initialized", {
                "host": self.config.host,
                "sample_rate": self.config.sample_rate,
            })
        except Exception as e:
            self.logger.error("Failed to initialize Langfuse client", e)

    @classmethod
    def from_env(cls, logger: Optional[StructuredLogger] = None) -> "LangfuseObserver":
        """Create observer from environment variables."""
        return cls(config=LangfuseConfig.from_env(), logger=logger)

    @property
    def is_enabled(self) -> bool:
        """Check if Langfuse observability is enabled."""
        return self._client is not None and self.config.enabled

    def start_trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Start a new trace.

        Returns the trace ID for reference.
        """
        trace_id = str(uuid4())
        self._metrics[trace_id] = TraceMetrics()

        if self.is_enabled:
            try:
                trace = self._client.trace(
                    id=trace_id,
                    name=name,
                    user_id=user_id,
                    session_id=session_id,
                    metadata=metadata or {},
                    tags=tags or [],
                )
                self._traces[trace_id] = trace
            except Exception as e:
                self.logger.error("Failed to create Langfuse trace", e)

        self._current_trace_id = trace_id
        self.logger.info("Trace started", {
            "trace_id": trace_id,
            "name": name,
            "user_id": user_id,
        })

        return trace_id

    def end_trace(
        self,
        trace_id: Optional[str] = None,
        output: Optional[Any] = None,
        status: str = "success",
    ) -> TraceMetrics:
        """End a trace and return metrics."""
        trace_id = trace_id or self._current_trace_id
        if not trace_id:
            return TraceMetrics()

        metrics = self._metrics.get(trace_id, TraceMetrics())
        metrics.success = status == "success"
        metrics.finalize()

        if self.is_enabled and trace_id in self._traces:
            try:
                trace = self._traces[trace_id]
                trace.update(
                    output=output,
                    metadata={
                        "metrics": metrics.to_dict(),
                        "status": status,
                    },
                )
            except Exception as e:
                self.logger.error("Failed to update Langfuse trace", e)

        self.logger.info("Trace ended", {
            "trace_id": trace_id,
            "status": status,
            "latency_ms": metrics.latency_ms,
            "total_tokens": metrics.total_tokens,
            "cost_usd": metrics.total_cost_usd,
        })

        return metrics

    @contextmanager
    def trace_context(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Context manager for traces.

        Example:
            with observer.trace_context("chat", user_id="123") as trace_id:
                result = await process_chat()
        """
        trace_id = self.start_trace(name, user_id, session_id, metadata)
        try:
            yield trace_id
            self.end_trace(trace_id, status="success")
        except Exception as e:
            self.end_trace(trace_id, status="error")
            raise

    def log_generation(
        self,
        name: str,
        model: str,
        prompt: Any,
        completion: Any,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an LLM generation with full details."""
        trace_id = trace_id or self._current_trace_id

        # Update metrics
        if trace_id and trace_id in self._metrics:
            metrics = self._metrics[trace_id]
            metrics.prompt_tokens += prompt_tokens
            metrics.completion_tokens += completion_tokens
            metrics.total_tokens += prompt_tokens + completion_tokens
            metrics.model = model
            metrics.total_cost_usd += calculate_cost(model, prompt_tokens, completion_tokens)

        if self.is_enabled and trace_id in self._traces:
            try:
                trace = self._traces[trace_id]
                trace.generation(
                    name=name,
                    model=model,
                    input=prompt,
                    output=completion,
                    usage={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                    },
                    metadata=metadata or {},
                )
            except Exception as e:
                self.logger.error("Failed to log generation to Langfuse", e)

        self.logger.debug("Generation logged", {
            "name": name,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        })

    def log_span(
        self,
        name: str,
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """Log a span within a trace."""
        trace_id = trace_id or self._current_trace_id

        if self.is_enabled and trace_id in self._traces:
            try:
                trace = self._traces[trace_id]
                trace.span(
                    name=name,
                    input=input_data,
                    output=output_data,
                    metadata=metadata or {},
                )
            except Exception as e:
                self.logger.error("Failed to log span to Langfuse", e)

    def log_tool_call(
        self,
        tool_name: str,
        input_data: Any,
        output_data: Any,
        duration_ms: float,
        success: bool = True,
        trace_id: Optional[str] = None,
    ) -> None:
        """Log a tool call within a trace."""
        trace_id = trace_id or self._current_trace_id

        if trace_id and trace_id in self._metrics:
            self._metrics[trace_id].tool_calls += 1
            if not success:
                self._metrics[trace_id].errors += 1

        self.log_span(
            name=f"tool:{tool_name}",
            input_data=input_data,
            output_data=output_data,
            metadata={
                "duration_ms": duration_ms,
                "success": success,
                "type": "tool_call",
            },
            trace_id=trace_id,
        )

    def log_event(
        self,
        name: str,
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """Log a custom event."""
        trace_id = trace_id or self._current_trace_id

        if self.is_enabled and trace_id in self._traces:
            try:
                trace = self._traces[trace_id]
                trace.event(name=name, metadata=data or {})
            except Exception as e:
                self.logger.error("Failed to log event to Langfuse", e)

    def trace(
        self,
        name: str,
        user_id_param: Optional[str] = None,
        session_id_param: Optional[str] = None,
    ):
        """
        Decorator to trace a function.

        Example:
            @observer.trace("chat_completion")
            async def chat(message: str) -> str:
                return await llm.complete(message)
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                user_id = kwargs.get("user_id", user_id_param)
                session_id = kwargs.get("session_id", session_id_param)

                with self.trace_context(name, user_id, session_id):
                    return await func(*args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                user_id = kwargs.get("user_id", user_id_param)
                session_id = kwargs.get("session_id", session_id_param)

                with self.trace_context(name, user_id, session_id):
                    return func(*args, **kwargs)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    def flush(self) -> None:
        """Flush all pending traces to Langfuse."""
        if self._client:
            try:
                self._client.flush()
                self.logger.debug("Flushed traces to Langfuse")
            except Exception as e:
                self.logger.error("Failed to flush Langfuse traces", e)

    def shutdown(self) -> None:
        """Shutdown the Langfuse client."""
        self.flush()
        if self._client:
            try:
                self._client.shutdown()
                self.logger.info("Langfuse client shutdown complete")
            except Exception as e:
                self.logger.error("Error during Langfuse shutdown", e)

    def get_metrics(self, trace_id: Optional[str] = None) -> Optional[TraceMetrics]:
        """Get metrics for a specific trace or current trace."""
        trace_id = trace_id or self._current_trace_id
        return self._metrics.get(trace_id) if trace_id else None

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all collected metrics."""
        return {
            trace_id: metrics.to_dict()
            for trace_id, metrics in self._metrics.items()
        }


def create_langfuse_handler(observer: LangfuseObserver) -> Callable[[LogEntry], None]:
    """
    Create a log handler that sends logs to Langfuse as events.

    Example:
        logger = StructuredLogger("my-agent")
        observer = LangfuseObserver.from_env()
        logger.add_handler(create_langfuse_handler(observer))
    """
    def handler(entry: LogEntry) -> None:
        if observer.is_enabled and observer._current_trace_id:
            observer.log_event(
                name=f"log:{entry.level.value.lower()}",
                data={
                    "message": entry.message,
                    "level": entry.level.value,
                    "timestamp": entry.timestamp.isoformat(),
                    **entry.data,
                },
            )

    return handler
