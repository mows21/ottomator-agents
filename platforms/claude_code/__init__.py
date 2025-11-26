"""
Claude Code Configuration Platform
===================================

Configuration templates and utilities for Claude Code agents.

Features:
- CLAUDE.md templates
- Slash command definitions
- Hook configurations
- MCP server setup

This platform provides tools for configuring Claude Code environments.
"""

from platforms.claude_code.config import (
    ClaudeCodeConfig,
    create_claude_md,
    create_slash_command,
    create_hook,
)
from platforms.claude_code.templates import (
    AgentTemplate,
    create_research_agent_config,
    create_coding_agent_config,
    create_data_agent_config,
)

__all__ = [
    "ClaudeCodeConfig",
    "create_claude_md",
    "create_slash_command",
    "create_hook",
    "AgentTemplate",
    "create_research_agent_config",
    "create_coding_agent_config",
    "create_data_agent_config",
]
