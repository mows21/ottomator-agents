"""
Pydantic AI Dependencies
========================

Dependency injection for Pydantic AI agents.
Provides typed dependencies with full observability integration.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar
import os

from platforms.core.logging import StructuredLogger, LangfuseObserver, MetricsCollector
from platforms.core.quality import QualityManagementSystem, ValidationEngine
from platforms.core.ml_context import MLContextEngine, EmbeddingManager

try:
    from supabase import Client as SupabaseClient, create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    SupabaseClient = Any

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


T = TypeVar("T")


@dataclass
class Dependencies:
    """
    Base dependencies class for Pydantic AI agents.

    Provides access to core infrastructure from within tools.

    Example:
        @agent.tool
        async def my_tool(ctx: RunContext[Dependencies], query: str) -> str:
            ctx.deps.logger.info("Processing query", {"query": query})
            result = await ctx.deps.http.get(f"https://api.example.com/{query}")
            return result.text
    """
    # Session context
    session_id: str = ""
    user_id: Optional[str] = None
    request_id: str = ""

    # Core infrastructure
    logger: Optional[StructuredLogger] = None
    metrics: Optional[MetricsCollector] = None
    observer: Optional[LangfuseObserver] = None
    context_engine: Optional[MLContextEngine] = None
    qms: Optional[QualityManagementSystem] = None
    validation: Optional[ValidationEngine] = None

    # Data access
    supabase: Optional[SupabaseClient] = None
    embeddings: Optional[EmbeddingManager] = None

    # HTTP client
    http: Optional[Any] = None  # httpx.AsyncClient

    # Custom data
    extra: Dict[str, Any] = field(default_factory=dict)

    def log(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a message."""
        if self.logger:
            self.logger.info(message, data)

    def log_debug(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message."""
        if self.logger:
            self.logger.debug(message, data)

    def log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log an error."""
        if self.logger:
            self.logger.error(message, error)

    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a metric."""
        if self.metrics:
            self.metrics.histogram(name, value, labels)

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter."""
        if self.metrics:
            self.metrics.increment(name, value, labels)

    def record_tool_call(
        self,
        tool_name: str,
        success: bool,
        latency_ms: float,
    ) -> None:
        """Record a tool call."""
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

    def add_context(self, content: str, context_type: str = "document") -> None:
        """Add content to the context engine."""
        if self.context_engine:
            from platforms.core.ml_context.context_engine import ContextType
            ct = ContextType(context_type) if context_type in [e.value for e in ContextType] else ContextType.DOCUMENT
            self.context_engine.add_context(content, ct)

    async def embed(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        if self.embeddings:
            result = self.embeddings.embed_single(text)
            return result.embedding if result else None
        return None


@dataclass
class StudioDependencies(Dependencies):
    """
    Extended dependencies for Live Agent Studio integration.

    Includes Supabase for session management and history.
    """
    # Studio-specific
    api_token: Optional[str] = None
    studio_url: str = "https://studio.ottomator.ai"

    async def get_session_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history from Supabase."""
        if not self.supabase or not self.session_id:
            return []

        try:
            response = self.supabase.table("messages").select("*").eq(
                "session_id", self.session_id
            ).order("created_at", desc=True).limit(limit).execute()

            return list(reversed(response.data)) if response.data else []
        except Exception as e:
            self.log_error("Failed to get session history", e)
            return []

    async def save_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save a message to Supabase."""
        if not self.supabase or not self.session_id:
            return

        try:
            self.supabase.table("messages").insert({
                "session_id": self.session_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as e:
            self.log_error("Failed to save message", e)


class DependencyBuilder:
    """
    Builder for creating dependency instances.

    Example:
        deps = (
            DependencyBuilder()
            .with_logging("my-agent")
            .with_metrics()
            .with_supabase()
            .with_http()
            .build()
        )
    """

    def __init__(self, deps_class: type = Dependencies):
        self._deps_class = deps_class
        self._config: Dict[str, Any] = {}

    def with_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> "DependencyBuilder":
        """Add session context."""
        self._config["session_id"] = session_id
        self._config["user_id"] = user_id
        self._config["request_id"] = request_id
        return self

    def with_logging(
        self,
        name: str = "agent",
        platform: str = "pydantic_ai",
    ) -> "DependencyBuilder":
        """Add structured logging."""
        self._config["logger"] = StructuredLogger(name=name, platform=platform)
        return self

    def with_metrics(self, name: str = "agent") -> "DependencyBuilder":
        """Add metrics collection."""
        self._config["metrics"] = MetricsCollector(name=name)
        return self

    def with_langfuse(self) -> "DependencyBuilder":
        """Add Langfuse observability."""
        self._config["observer"] = LangfuseObserver.from_env(
            logger=self._config.get("logger")
        )
        return self

    def with_context_engine(
        self,
        max_tokens: int = 8000,
    ) -> "DependencyBuilder":
        """Add ML context engine."""
        self._config["context_engine"] = MLContextEngine(
            max_tokens=max_tokens,
            logger=self._config.get("logger"),
        )
        return self

    def with_qms(
        self,
        agent_id: str,
        platform: str = "pydantic_ai",
    ) -> "DependencyBuilder":
        """Add quality management."""
        self._config["qms"] = QualityManagementSystem(
            agent_id=agent_id,
            platform=platform,
            logger=self._config.get("logger"),
            metrics=self._config.get("metrics"),
        )
        return self

    def with_validation(self) -> "DependencyBuilder":
        """Add validation engine."""
        self._config["validation"] = ValidationEngine()
        return self

    def with_supabase(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
    ) -> "DependencyBuilder":
        """Add Supabase client."""
        if not SUPABASE_AVAILABLE:
            return self

        url = url or os.getenv("SUPABASE_URL")
        key = key or os.getenv("SUPABASE_KEY")

        if url and key:
            self._config["supabase"] = create_client(url, key)
        return self

    def with_embeddings(
        self,
        provider: str = "openai",
    ) -> "DependencyBuilder":
        """Add embedding manager."""
        self._config["embeddings"] = EmbeddingManager(
            provider=provider,
            logger=self._config.get("logger"),
        )
        return self

    def with_http(self) -> "DependencyBuilder":
        """Add HTTP client."""
        if HTTPX_AVAILABLE:
            self._config["http"] = httpx.AsyncClient()
        return self

    def with_extra(self, **kwargs: Any) -> "DependencyBuilder":
        """Add extra data."""
        if "extra" not in self._config:
            self._config["extra"] = {}
        self._config["extra"].update(kwargs)
        return self

    def build(self) -> Dependencies:
        """Build the dependencies instance."""
        return self._deps_class(**self._config)


def create_dependencies(
    session_id: str = "",
    user_id: Optional[str] = None,
    enable_logging: bool = True,
    enable_metrics: bool = True,
    enable_langfuse: bool = True,
    enable_supabase: bool = False,
    agent_name: str = "agent",
) -> Dependencies:
    """
    Factory function to create standard dependencies.

    Example:
        deps = create_dependencies(
            session_id="sess_123",
            user_id="user_456",
            enable_langfuse=True,
        )
    """
    builder = DependencyBuilder()
    builder.with_session(session_id, user_id)

    if enable_logging:
        builder.with_logging(agent_name)

    if enable_metrics:
        builder.with_metrics(agent_name)

    if enable_langfuse:
        builder.with_langfuse()

    if enable_supabase:
        builder.with_supabase()

    return builder.build()


def create_studio_dependencies(
    session_id: str,
    user_id: Optional[str] = None,
    api_token: Optional[str] = None,
    agent_name: str = "agent",
) -> StudioDependencies:
    """
    Create dependencies for Live Agent Studio integration.

    Example:
        deps = create_studio_dependencies(
            session_id="sess_123",
            api_token=os.getenv("API_BEARER_TOKEN"),
        )
    """
    builder = DependencyBuilder(StudioDependencies)
    builder.with_session(session_id, user_id)
    builder.with_logging(agent_name)
    builder.with_metrics(agent_name)
    builder.with_langfuse()
    builder.with_supabase()
    builder.with_context_engine()
    builder.with_extra(api_token=api_token)

    return builder.build()
