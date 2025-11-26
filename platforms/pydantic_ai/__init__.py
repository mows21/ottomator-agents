"""
Pydantic AI Platform
====================

Type-safe AI agents built with Pydantic AI framework.

Features:
- Full type safety with Pydantic models
- Tool decorators for agent capabilities
- Dependency injection
- Streaming support
- Multi-model support

This platform wraps all Pydantic AI agents with our core infrastructure:
- Structured logging
- Quality management
- ML context engineering
- Langfuse observability
"""

from platforms.pydantic_ai.agent import PydanticAIAgent, PydanticAIConfig
from platforms.pydantic_ai.tools import ToolRegistry, tool
from platforms.pydantic_ai.dependencies import Dependencies

__all__ = [
    "PydanticAIAgent",
    "PydanticAIConfig",
    "ToolRegistry",
    "tool",
    "Dependencies",
]
