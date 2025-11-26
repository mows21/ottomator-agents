"""
Claude Code Configuration
=========================

Utilities for generating Claude Code configuration files.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import os


@dataclass
class MCPServer:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        config = {
            "command": self.command,
            "args": self.args,
        }
        if self.env:
            config["env"] = self.env
        return config


@dataclass
class Hook:
    """Configuration for a Claude Code hook."""
    name: str
    event: str  # PreToolUse, PostToolUse, Notification, Stop
    matcher: Optional[str] = None  # Tool name pattern to match
    command: str = ""
    timeout_ms: int = 60000
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        hook = {
            "type": "command",
            "command": self.command,
        }
        if self.matcher:
            hook["matcher"] = self.matcher
        if self.timeout_ms != 60000:
            hook["timeout"] = self.timeout_ms
        return hook


@dataclass
class ClaudeCodeConfig:
    """
    Complete Claude Code configuration.

    Example:
        config = ClaudeCodeConfig(
            project_name="my-agent",
            description="AI agent for research",
            mcp_servers=[
                MCPServer(name="brave-search", command="npx", args=[...]),
            ],
        )

        # Generate CLAUDE.md
        claude_md = config.generate_claude_md()

        # Generate settings.json
        settings = config.generate_settings()
    """
    project_name: str
    description: str = ""
    system_context: str = ""

    # Project configuration
    tech_stack: List[str] = field(default_factory=list)
    conventions: List[str] = field(default_factory=list)
    important_files: List[str] = field(default_factory=list)

    # MCP servers
    mcp_servers: List[MCPServer] = field(default_factory=list)

    # Hooks
    hooks: List[Hook] = field(default_factory=list)

    # Slash commands
    slash_commands: Dict[str, str] = field(default_factory=dict)

    # Model preferences
    default_model: str = "sonnet"
    allow_model_override: bool = True

    # Permissions
    allowed_tools: List[str] = field(default_factory=list)
    denied_tools: List[str] = field(default_factory=list)

    def generate_claude_md(self) -> str:
        """Generate CLAUDE.md content."""
        sections = []

        # Header
        sections.append(f"# {self.project_name}\n")
        if self.description:
            sections.append(f"{self.description}\n")

        # System context
        if self.system_context:
            sections.append("## Context\n")
            sections.append(f"{self.system_context}\n")

        # Tech stack
        if self.tech_stack:
            sections.append("## Tech Stack\n")
            for tech in self.tech_stack:
                sections.append(f"- {tech}")
            sections.append("")

        # Conventions
        if self.conventions:
            sections.append("## Conventions\n")
            for convention in self.conventions:
                sections.append(f"- {convention}")
            sections.append("")

        # Important files
        if self.important_files:
            sections.append("## Important Files\n")
            for file in self.important_files:
                sections.append(f"- `{file}`")
            sections.append("")

        # Slash commands
        if self.slash_commands:
            sections.append("## Slash Commands\n")
            for cmd, desc in self.slash_commands.items():
                sections.append(f"- `/{cmd}`: {desc}")
            sections.append("")

        return "\n".join(sections)

    def generate_settings(self) -> Dict[str, Any]:
        """Generate Claude Code settings.json content."""
        settings = {}

        # MCP servers
        if self.mcp_servers:
            settings["mcpServers"] = {
                server.name: server.to_dict()
                for server in self.mcp_servers
                if server.enabled
            }

        # Model
        if self.default_model:
            settings["model"] = self.default_model

        # Permissions
        if self.allowed_tools:
            settings["allowedTools"] = self.allowed_tools
        if self.denied_tools:
            settings["deniedTools"] = self.denied_tools

        return settings

    def generate_hooks_settings(self) -> Dict[str, Any]:
        """Generate hooks configuration."""
        hooks_config = {}

        for hook in self.hooks:
            if not hook.enabled:
                continue

            if hook.event not in hooks_config:
                hooks_config[hook.event] = []

            hooks_config[hook.event].append(hook.to_dict())

        return {"hooks": hooks_config} if hooks_config else {}

    def save(self, base_path: str = ".") -> None:
        """Save all configuration files."""
        # Create .claude directory
        claude_dir = os.path.join(base_path, ".claude")
        os.makedirs(claude_dir, exist_ok=True)

        # Save CLAUDE.md
        claude_md_path = os.path.join(base_path, "CLAUDE.md")
        with open(claude_md_path, "w") as f:
            f.write(self.generate_claude_md())

        # Save settings.json
        settings = self.generate_settings()
        settings.update(self.generate_hooks_settings())
        settings_path = os.path.join(claude_dir, "settings.json")
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)

        # Create commands directory and save slash commands
        if self.slash_commands:
            commands_dir = os.path.join(claude_dir, "commands")
            os.makedirs(commands_dir, exist_ok=True)

            for cmd, content in self.slash_commands.items():
                cmd_path = os.path.join(commands_dir, f"{cmd}.md")
                with open(cmd_path, "w") as f:
                    f.write(content)


def create_claude_md(
    project_name: str,
    description: str,
    system_context: str = "",
    tech_stack: Optional[List[str]] = None,
    conventions: Optional[List[str]] = None,
) -> str:
    """
    Create a CLAUDE.md file content.

    Example:
        claude_md = create_claude_md(
            project_name="AI Research Agent",
            description="An agent for conducting research",
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
        )
    """
    config = ClaudeCodeConfig(
        project_name=project_name,
        description=description,
        system_context=system_context,
        tech_stack=tech_stack or [],
        conventions=conventions or [],
    )
    return config.generate_claude_md()


def create_slash_command(
    name: str,
    prompt: str,
    description: str = "",
) -> Dict[str, str]:
    """
    Create a slash command definition.

    Returns dict with filename and content.
    """
    content = f"""# {name}

{description}

{prompt}
"""
    return {
        "filename": f"{name}.md",
        "content": content,
    }


def create_hook(
    event: str,
    command: str,
    matcher: Optional[str] = None,
    timeout_ms: int = 60000,
) -> Hook:
    """
    Create a hook configuration.

    Events:
    - PreToolUse: Before a tool is used
    - PostToolUse: After a tool is used
    - Notification: For notifications
    - Stop: When Claude stops

    Example:
        hook = create_hook(
            event="PreToolUse",
            matcher="Bash",
            command="./validate_command.sh",
        )
    """
    return Hook(
        name=f"{event}_{matcher or 'all'}",
        event=event,
        matcher=matcher,
        command=command,
        timeout_ms=timeout_ms,
    )


# Common MCP server configurations
def create_brave_search_server(api_key_env: str = "BRAVE_API_KEY") -> MCPServer:
    """Create Brave Search MCP server configuration."""
    return MCPServer(
        name="brave-search",
        command="npx",
        args=["-y", "@anthropic/mcp-server-brave-search"],
        env={"BRAVE_API_KEY": f"${{{api_key_env}}}"},
    )


def create_github_server(token_env: str = "GITHUB_TOKEN") -> MCPServer:
    """Create GitHub MCP server configuration."""
    return MCPServer(
        name="github",
        command="npx",
        args=["-y", "@anthropic/mcp-server-github"],
        env={"GITHUB_TOKEN": f"${{{token_env}}}"},
    )


def create_filesystem_server(paths: List[str]) -> MCPServer:
    """Create Filesystem MCP server configuration."""
    return MCPServer(
        name="filesystem",
        command="npx",
        args=["-y", "@anthropic/mcp-server-filesystem"] + paths,
    )


def create_memory_server() -> MCPServer:
    """Create Memory MCP server configuration."""
    return MCPServer(
        name="memory",
        command="npx",
        args=["-y", "@anthropic/mcp-server-memory"],
    )
