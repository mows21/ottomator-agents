"""
Claude Agent SDK Platform
=========================

Native Claude Agent SDK implementations with full observability.

Features:
- Direct Claude API integration
- Multi-agent orchestration
- Tool use with function calling
- Streaming support
- Cost tracking

This platform wraps Claude Agent SDK with our core infrastructure:
- Structured logging
- Quality management
- ML context engineering
- Langfuse observability
"""

from platforms.claude_sdk.agent import ClaudeSDKAgent, ClaudeSDKConfig
from platforms.claude_sdk.orchestrator import MultiAgentOrchestrator, ExecutiveAgent
from platforms.claude_sdk.tools import ClaudeTool, ToolResult

__all__ = [
    "ClaudeSDKAgent",
    "ClaudeSDKConfig",
    "MultiAgentOrchestrator",
    "ExecutiveAgent",
    "ClaudeTool",
    "ToolResult",
]
