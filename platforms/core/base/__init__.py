"""
Base Agent Module
=================

Base classes and interfaces for all agent platforms:
- BaseAgent abstract class
- Common configuration
- Shared response types
"""

from platforms.core.base.base_agent import BaseAgent, AgentConfig, AgentResponse, AgentCapability

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "AgentResponse",
    "AgentCapability",
]
