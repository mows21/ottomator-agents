"""
Multi-Platform Agent Framework
==============================

A comprehensive agent platform supporting multiple frameworks with:
- Quality Management System (QMS) from the start
- ML-powered prompt context engineering
- Full structured logging with Langfuse observability
- Cross-platform agent interoperability

Supported Platforms:
- pydantic_ai: Pydantic AI agents with type-safe tools
- n8n: No-code workflow agents
- claude_sdk: Claude Agent SDK native agents
- claude_code: Claude Code configuration and hooks
- google_adk: Google Agent Development Kit (Gemini 3 Pro)
"""

__version__ = "1.0.0"
__author__ = "ottomator"

from platforms.core import (
    QualityManagementSystem,
    StructuredLogger,
    MLContextEngine,
    LangfuseObserver,
    BaseAgent,
)

__all__ = [
    "QualityManagementSystem",
    "StructuredLogger",
    "MLContextEngine",
    "LangfuseObserver",
    "BaseAgent",
]
