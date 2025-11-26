"""
Structured Logger
=================

Full-featured structured logging with JSON output, context propagation,
and integration with observability platforms.
"""

import json
import logging
import sys
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4
import asyncio
from functools import wraps


class LogLevel(str, Enum):
    """Log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Context for structured log entries."""
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid4()))
    parent_span_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    platform: Optional[str] = None
    environment: str = "development"
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "platform": self.platform,
            "environment": self.environment,
            **self.extra,
        }


@dataclass
class LogEntry:
    """A structured log entry."""
    timestamp: datetime
    level: LogLevel
    message: str
    context: LogContext
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        entry = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "context": self.context.to_dict(),
        }
        if self.data:
            entry["data"] = self.data
        if self.error:
            entry["error"] = self.error
        if self.duration_ms is not None:
            entry["duration_ms"] = self.duration_ms
        return entry

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class StructuredLogger:
    """
    Full-featured structured logger with context propagation.

    Features:
    - JSON structured output
    - Context propagation (trace_id, span_id, etc.)
    - Automatic error formatting with stack traces
    - Duration tracking for operations
    - Multiple output handlers (stdout, file, external)
    - Async-safe logging

    Example:
        logger = StructuredLogger(
            name="my-agent",
            platform="pydantic_ai",
            environment="production"
        )

        with logger.span("process_request") as span:
            span.info("Processing started", {"request_id": "123"})
            result = process()
            span.info("Processing complete", {"result": result})
    """

    def __init__(
        self,
        name: str,
        platform: Optional[str] = None,
        environment: str = "development",
        level: LogLevel = LogLevel.INFO,
        handlers: Optional[List[Callable[[LogEntry], None]]] = None,
        enable_console: bool = True,
        log_file: Optional[str] = None,
    ):
        self.name = name
        self.platform = platform
        self.environment = environment
        self.level = level
        self._handlers: List[Callable[[LogEntry], None]] = handlers or []
        self._context_stack: List[LogContext] = []
        self._log_buffer: List[LogEntry] = []
        self._buffer_size = 100

        # Setup console handler
        if enable_console:
            self._handlers.append(self._console_handler)

        # Setup file handler
        if log_file:
            self._log_file = log_file
            self._handlers.append(self._file_handler)
        else:
            self._log_file = None

    @property
    def current_context(self) -> LogContext:
        """Get the current logging context."""
        if self._context_stack:
            return self._context_stack[-1]
        return LogContext(
            agent_id=self.name,
            platform=self.platform,
            environment=self.environment,
        )

    def _should_log(self, level: LogLevel) -> bool:
        """Check if the log level should be logged."""
        levels = list(LogLevel)
        return levels.index(level) >= levels.index(self.level)

    def _create_entry(
        self,
        level: LogLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        duration_ms: Optional[float] = None,
    ) -> LogEntry:
        """Create a structured log entry."""
        error_dict = None
        if error:
            error_dict = {
                "type": type(error).__name__,
                "message": str(error),
                "stack_trace": traceback.format_exc(),
            }

        return LogEntry(
            timestamp=datetime.now(timezone.utc),
            level=level,
            message=message,
            context=self.current_context,
            data=data or {},
            error=error_dict,
            duration_ms=duration_ms,
        )

    def _emit(self, entry: LogEntry) -> None:
        """Emit a log entry to all handlers."""
        if not self._should_log(entry.level):
            return

        # Buffer the entry
        self._log_buffer.append(entry)
        if len(self._log_buffer) > self._buffer_size:
            self._log_buffer.pop(0)

        # Send to all handlers
        for handler in self._handlers:
            try:
                handler(entry)
            except Exception as e:
                # Fallback to stderr if handler fails
                print(f"Logger handler error: {e}", file=sys.stderr)

    def _console_handler(self, entry: LogEntry) -> None:
        """Handler for console output."""
        # Color codes for log levels
        colors = {
            LogLevel.DEBUG: "\033[36m",    # Cyan
            LogLevel.INFO: "\033[32m",     # Green
            LogLevel.WARNING: "\033[33m",  # Yellow
            LogLevel.ERROR: "\033[31m",    # Red
            LogLevel.CRITICAL: "\033[35m", # Magenta
        }
        reset = "\033[0m"

        color = colors.get(entry.level, "")
        level_str = f"{color}[{entry.level.value}]{reset}"

        output = f"{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')} {level_str} [{entry.context.trace_id[:8]}] {entry.message}"

        if entry.data:
            output += f" | data={json.dumps(entry.data, default=str)}"

        if entry.duration_ms is not None:
            output += f" | duration={entry.duration_ms:.2f}ms"

        if entry.error:
            output += f"\n  Error: {entry.error['type']}: {entry.error['message']}"

        print(output, file=sys.stderr if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL] else sys.stdout)

    def _file_handler(self, entry: LogEntry) -> None:
        """Handler for file output."""
        if self._log_file:
            with open(self._log_file, "a") as f:
                f.write(entry.to_json() + "\n")

    # Core logging methods
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message."""
        self._emit(self._create_entry(LogLevel.DEBUG, message, data))

    def info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message."""
        self._emit(self._create_entry(LogLevel.INFO, message, data))

    def warning(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message."""
        self._emit(self._create_entry(LogLevel.WARNING, message, data))

    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an error message with optional exception."""
        self._emit(self._create_entry(LogLevel.ERROR, message, data, error))

    def critical(
        self,
        message: str,
        error: Optional[Exception] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a critical message."""
        self._emit(self._create_entry(LogLevel.CRITICAL, message, data, error))

    @contextmanager
    def span(
        self,
        name: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a new span context for tracing operations.

        Example:
            with logger.span("process_user", {"user_id": "123"}) as span:
                span.info("Starting processing")
                result = process_user()
                span.info("Completed", {"result": result})
        """
        parent = self.current_context

        new_context = LogContext(
            trace_id=parent.trace_id,
            span_id=str(uuid4()),
            parent_span_id=parent.span_id,
            session_id=parent.session_id,
            user_id=parent.user_id,
            agent_id=parent.agent_id,
            platform=parent.platform,
            environment=parent.environment,
            extra={**parent.extra, **(data or {})},
        )

        self._context_stack.append(new_context)
        start_time = datetime.now(timezone.utc)

        span_logger = SpanLogger(self, name)
        span_logger.debug(f"Span started: {name}", data)

        try:
            yield span_logger
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            span_logger.error(f"Span failed: {name}", e, {"duration_ms": duration})
            raise
        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            span_logger.debug(f"Span completed: {name}", {"duration_ms": duration})
            self._context_stack.pop()

    def with_context(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **extra: Any,
    ) -> "StructuredLogger":
        """
        Create a new logger instance with additional context.

        Example:
            request_logger = logger.with_context(
                session_id="sess_123",
                user_id="user_456",
                request_id="req_789"
            )
        """
        new_logger = StructuredLogger(
            name=self.name,
            platform=self.platform,
            environment=self.environment,
            level=self.level,
            handlers=self._handlers.copy(),
            enable_console=False,
        )

        new_context = LogContext(
            trace_id=self.current_context.trace_id,
            span_id=str(uuid4()),
            parent_span_id=self.current_context.span_id,
            session_id=session_id or self.current_context.session_id,
            user_id=user_id or self.current_context.user_id,
            agent_id=agent_id or self.current_context.agent_id,
            platform=self.current_context.platform,
            environment=self.current_context.environment,
            extra={**self.current_context.extra, **extra},
        )
        new_logger._context_stack.append(new_context)

        return new_logger

    def get_logs(self, level: Optional[LogLevel] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent logs from the buffer."""
        logs = self._log_buffer[-limit:]
        if level:
            logs = [log for log in logs if log.level == level]
        return [log.to_dict() for log in logs]

    def add_handler(self, handler: Callable[[LogEntry], None]) -> None:
        """Add a custom log handler."""
        self._handlers.append(handler)


class SpanLogger:
    """A logger scoped to a specific span."""

    def __init__(self, parent: StructuredLogger, name: str):
        self._parent = parent
        self.name = name

    def debug(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self._parent.debug(f"[{self.name}] {message}", data)

    def info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self._parent.info(f"[{self.name}] {message}", data)

    def warning(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self._parent.warning(f"[{self.name}] {message}", data)

    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._parent.error(f"[{self.name}] {message}", error, data)


def log_operation(logger: StructuredLogger, operation_name: str):
    """
    Decorator to log function execution with timing.

    Example:
        @log_operation(logger, "process_request")
        async def process_request(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with logger.span(operation_name) as span:
                span.info("Starting operation", {"args_count": len(args)})
                try:
                    result = await func(*args, **kwargs)
                    span.info("Operation completed successfully")
                    return result
                except Exception as e:
                    span.error("Operation failed", e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with logger.span(operation_name) as span:
                span.info("Starting operation", {"args_count": len(args)})
                try:
                    result = func(*args, **kwargs)
                    span.info("Operation completed successfully")
                    return result
                except Exception as e:
                    span.error("Operation failed", e)
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
