"""
Core Infrastructure Module
==========================

Provides shared infrastructure for all platform agents:
- Logging: Structured logging with full observability
- Quality: Quality Management System (QMS)
- ML Context: Machine learning for prompt context engineering
- Base: Base agent classes and interfaces
"""

from platforms.core.logging import StructuredLogger, LangfuseObserver, MetricsCollector
from platforms.core.quality import QualityManagementSystem, ValidationEngine, QualityStandards
from platforms.core.ml_context import MLContextEngine, PromptOptimizer, EmbeddingManager
from platforms.core.base import BaseAgent, AgentConfig, AgentResponse

__all__ = [
    # Logging
    "StructuredLogger",
    "LangfuseObserver",
    "MetricsCollector",
    # Quality
    "QualityManagementSystem",
    "ValidationEngine",
    "QualityStandards",
    # ML Context
    "MLContextEngine",
    "PromptOptimizer",
    "EmbeddingManager",
    # Base
    "BaseAgent",
    "AgentConfig",
    "AgentResponse",
]
