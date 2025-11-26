"""
Claude Code Agent Templates
===========================

Pre-built templates for common agent configurations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from platforms.claude_code.config import (
    ClaudeCodeConfig,
    MCPServer,
    Hook,
    create_brave_search_server,
    create_github_server,
    create_filesystem_server,
    create_memory_server,
)


@dataclass
class AgentTemplate:
    """Template for a Claude Code agent configuration."""
    name: str
    description: str
    config: ClaudeCodeConfig

    def generate_files(self, base_path: str = ".") -> None:
        """Generate all configuration files."""
        self.config.save(base_path)


def create_research_agent_config(
    project_name: str = "Research Agent",
    output_dir: str = "./research_output",
) -> ClaudeCodeConfig:
    """
    Create configuration for a research-focused agent.

    Features:
    - Web search via Brave
    - GitHub integration for code research
    - Memory for long-term context
    - File system access for saving results
    """
    return ClaudeCodeConfig(
        project_name=project_name,
        description="AI-powered research assistant with web search and document synthesis capabilities.",
        system_context="""You are an expert research assistant. Your job is to:
1. Search for relevant information using web search
2. Analyze and synthesize findings
3. Provide well-sourced, accurate answers
4. Save important research to files when requested

Always cite your sources and acknowledge uncertainty when appropriate.""",
        tech_stack=[
            "Web Search (Brave)",
            "GitHub Integration",
            "Memory for context",
            "File system for output",
        ],
        conventions=[
            "Always cite sources for claims",
            "Use structured markdown for output",
            "Save research summaries to files",
            "Maintain conversation context with memory",
        ],
        mcp_servers=[
            create_brave_search_server(),
            create_github_server(),
            create_memory_server(),
            create_filesystem_server([output_dir]),
        ],
        slash_commands={
            "research": """Research a topic thoroughly.

Search for information on the given topic, synthesize findings, and provide a comprehensive summary with sources.

$ARGUMENTS""",
            "summarize": """Summarize the current research.

Provide a concise summary of all research conducted in this session.

$ARGUMENTS""",
            "save": """Save research to a file.

Save the current research summary to a markdown file in the output directory.

$ARGUMENTS""",
        },
        default_model="sonnet",
    )


def create_coding_agent_config(
    project_name: str = "Coding Agent",
    project_path: str = ".",
) -> ClaudeCodeConfig:
    """
    Create configuration for a coding-focused agent.

    Features:
    - Full file system access
    - GitHub integration
    - Code execution hooks
    - Testing integration
    """
    return ClaudeCodeConfig(
        project_name=project_name,
        description="AI-powered coding assistant with full project access and GitHub integration.",
        system_context="""You are an expert software engineer. Your job is to:
1. Understand the codebase structure
2. Write clean, well-documented code
3. Follow project conventions
4. Write and run tests
5. Create pull requests when requested

Always follow best practices and maintain code quality.""",
        tech_stack=[
            "Full codebase access",
            "GitHub integration",
            "Terminal access",
        ],
        conventions=[
            "Follow existing code style",
            "Write unit tests for new code",
            "Document public APIs",
            "Use meaningful commit messages",
            "Create focused, atomic commits",
        ],
        important_files=[
            "README.md",
            "pyproject.toml",
            "package.json",
            ".env.example",
        ],
        mcp_servers=[
            create_github_server(),
            create_filesystem_server([project_path]),
        ],
        hooks=[
            Hook(
                name="test_before_commit",
                event="PreToolUse",
                matcher="Bash",
                command="./scripts/pre-commit-check.sh",
                timeout_ms=120000,
            ),
        ],
        slash_commands={
            "review": """Review the current changes.

Analyze the current git diff and provide a code review with suggestions for improvement.

$ARGUMENTS""",
            "test": """Run tests for the project.

Execute the test suite and report results.

$ARGUMENTS""",
            "pr": """Create a pull request.

Create a well-documented pull request with the current changes.

$ARGUMENTS""",
            "refactor": """Refactor code.

Analyze and refactor the specified code for better quality.

$ARGUMENTS""",
        },
        default_model="sonnet",
    )


def create_data_agent_config(
    project_name: str = "Data Agent",
    data_dir: str = "./data",
) -> ClaudeCodeConfig:
    """
    Create configuration for a data analysis agent.

    Features:
    - File system access to data directory
    - Memory for analysis context
    - Python execution for data processing
    """
    return ClaudeCodeConfig(
        project_name=project_name,
        description="AI-powered data analysis assistant with file access and computation capabilities.",
        system_context="""You are an expert data analyst. Your job is to:
1. Explore and understand datasets
2. Perform statistical analysis
3. Create visualizations
4. Generate insights and reports

Use Python for data processing and always explain your findings clearly.""",
        tech_stack=[
            "Python (pandas, numpy, matplotlib)",
            "Data file access",
            "Memory for context",
        ],
        conventions=[
            "Document data transformations",
            "Validate data quality",
            "Create reproducible analysis",
            "Visualize key findings",
        ],
        mcp_servers=[
            create_filesystem_server([data_dir]),
            create_memory_server(),
        ],
        slash_commands={
            "explore": """Explore a dataset.

Load and analyze the structure of the specified dataset.

$ARGUMENTS""",
            "analyze": """Perform statistical analysis.

Run statistical analysis on the specified data.

$ARGUMENTS""",
            "visualize": """Create visualizations.

Generate charts and graphs for the data.

$ARGUMENTS""",
            "report": """Generate analysis report.

Create a comprehensive report of all analyses performed.

$ARGUMENTS""",
        },
        default_model="sonnet",
    )


def create_multi_agent_config(
    project_name: str = "Multi-Agent System",
) -> ClaudeCodeConfig:
    """
    Create configuration for a multi-agent orchestration system.

    Features:
    - All MCP servers enabled
    - Full capabilities
    - Complex hooks for agent coordination
    """
    return ClaudeCodeConfig(
        project_name=project_name,
        description="Multi-agent orchestration system with full capabilities.",
        system_context="""You are a sophisticated AI orchestrator managing multiple specialized agents.

Your capabilities:
1. Web search for current information
2. GitHub access for code repositories
3. File system for local operations
4. Memory for long-term context

Coordinate tasks efficiently and provide comprehensive solutions.""",
        tech_stack=[
            "Multi-agent orchestration",
            "Web search",
            "GitHub integration",
            "File system access",
            "Long-term memory",
        ],
        conventions=[
            "Delegate appropriately",
            "Synthesize information from multiple sources",
            "Maintain context across interactions",
            "Provide structured, actionable outputs",
        ],
        mcp_servers=[
            create_brave_search_server(),
            create_github_server(),
            create_memory_server(),
            create_filesystem_server(["./"]),
        ],
        slash_commands={
            "delegate": """Delegate a task to a specialist.

Analyze the task and delegate to the appropriate agent.

$ARGUMENTS""",
            "synthesize": """Synthesize results from multiple agents.

Combine and summarize outputs from different agents.

$ARGUMENTS""",
            "plan": """Create an execution plan.

Develop a detailed plan for accomplishing the given goal.

$ARGUMENTS""",
        },
        default_model="opus",
    )


# Template registry
TEMPLATES: Dict[str, callable] = {
    "research": create_research_agent_config,
    "coding": create_coding_agent_config,
    "data": create_data_agent_config,
    "multi-agent": create_multi_agent_config,
}


def get_template(name: str, **kwargs) -> ClaudeCodeConfig:
    """Get a template by name."""
    if name not in TEMPLATES:
        raise ValueError(f"Unknown template: {name}. Available: {list(TEMPLATES.keys())}")
    return TEMPLATES[name](**kwargs)


def list_templates() -> List[str]:
    """List all available templates."""
    return list(TEMPLATES.keys())
