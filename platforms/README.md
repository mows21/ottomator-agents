# Multi-Platform Agent Framework

A comprehensive agent platform supporting multiple frameworks with quality management, ML context engineering, and full logging from the start.

## Supported Platforms

| Platform | Description | Key Features |
|----------|-------------|--------------|
| **pydantic_ai** | Pydantic AI agents | Type-safe tools, dependency injection, streaming |
| **claude_sdk** | Claude Agent SDK | Native Claude API, multi-agent orchestration, tool use |
| **n8n** | n8n Workflows | No-code workflows, webhook triggers, RAG templates |
| **claude_code** | Claude Code Config | CLAUDE.md templates, slash commands, MCP servers |
| **google_adk** | Google ADK | Gemini models, Google Search, code execution |

## Core Infrastructure

All platforms share common infrastructure:

### Logging (`core/logging/`)
- **StructuredLogger**: JSON structured logging with context propagation
- **LangfuseObserver**: LLM observability with token/cost tracking
- **MetricsCollector**: Comprehensive metrics collection

### Quality Management (`core/quality/`)
- **QualityManagementSystem**: Quality gates and automated evaluation
- **ValidationEngine**: Input/output validation with sanitization
- **QualityStandards**: Compliance checking (security, performance, privacy)

### ML Context Engineering (`core/ml_context/`)
- **MLContextEngine**: Dynamic context window optimization
- **PromptOptimizer**: A/B testing and prompt improvement
- **EmbeddingManager**: Multi-provider embedding management

## Quick Start

### Pydantic AI Agent

```python
from platforms.pydantic_ai import PydanticAIAgent, PydanticAIConfig

config = PydanticAIConfig(
    name="my-agent",
    system_prompt="You are a helpful assistant.",
    model="gpt-4o-mini",
)

agent = PydanticAIAgent(config)
await agent.initialize()

@agent.tool
async def search(ctx, query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"

response = await agent.process("Search for AI news")
print(response.content)
```

### Claude SDK Agent

```python
from platforms.claude_sdk import ClaudeSDKAgent, ClaudeSDKConfig

config = ClaudeSDKConfig(
    name="claude-agent",
    system_prompt="You are an expert assistant.",
    model="claude-sonnet-4-5-20250929",
)

agent = ClaudeSDKAgent(config)
await agent.initialize()

@agent.tool(description="Get weather")
def get_weather(location: str) -> str:
    return f"Weather for {location}: Sunny"

response = await agent.process("What's the weather in NYC?")
```

### Google ADK Agent

```python
from platforms.google_adk import GoogleADKAgent, GoogleADKConfig

config = GoogleADKConfig(
    name="gemini-agent",
    system_prompt="You are helpful.",
    model="gemini-2.0-flash-exp",
    enable_google_search=True,
)

agent = GoogleADKAgent(config)
await agent.initialize()

response = await agent.process("What's happening in AI today?")
```

### n8n Workflow

```python
from platforms.n8n import create_agent_workflow

workflow = create_agent_workflow(
    name="my-agent",
    system_prompt="You are helpful.",
    enable_rag=True,
)
workflow.save("my-agent.json")
```

### Claude Code Configuration

```python
from platforms.claude_code import create_research_agent_config

config = create_research_agent_config(
    project_name="Research Agent",
)
config.save("./my-project")
```

## Multi-Agent Orchestration

```python
from platforms.claude_sdk import MultiAgentOrchestrator, create_claude_agent

orchestrator = MultiAgentOrchestrator()

# Add agents
researcher = create_claude_agent("researcher", "Research topics")
writer = create_claude_agent("writer", "Write content")
await researcher.initialize()
await writer.initialize()

orchestrator.add_agent("researcher", researcher)
orchestrator.add_agent("writer", writer)

# Run sequential workflow
result = await orchestrator.run_sequential(
    "Write about AI",
    ["researcher", "writer"],
)
```

## Observability

All agents integrate with Langfuse for observability:

```python
from platforms.core import LangfuseObserver

# Set environment variables
# LANGFUSE_PUBLIC_KEY=...
# LANGFUSE_SECRET_KEY=...

observer = LangfuseObserver.from_env()

with observer.trace_context("my_task", user_id="user123"):
    response = await agent.process(message)

# Automatic tracking of:
# - Token usage and costs
# - Latency metrics
# - Tool calls
# - Errors
```

## Quality Management

```python
from platforms.core import QualityManagementSystem

qms = QualityManagementSystem(
    agent_id="my-agent",
    platform="pydantic_ai",
)

# Evaluate response quality
report = qms.evaluate_response(
    response=response.content,
    latency_ms=response.latency_ms,
    tokens_used=response.total_tokens,
    model="gpt-4o",
)

print(f"Quality Score: {report.overall_score}%")
print(f"Passing: {report.is_passing()}")
```

## ML Context Engineering

```python
from platforms.core import MLContextEngine, ContextType

engine = MLContextEngine(max_tokens=8000)

# Add context items
engine.add_context(system_prompt, ContextType.SYSTEM, reserved=True)
engine.add_context(document, ContextType.DOCUMENT, relevance=0.9)
engine.add_context(user_message, ContextType.USER)

# Optimize context window for query
window = engine.optimize(query=user_message)
messages = window.to_messages()
```

## Environment Variables

```bash
# API Keys
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...

# Langfuse Observability
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com

# Supabase (for n8n and studio integration)
SUPABASE_URL=...
SUPABASE_KEY=...

# n8n
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=...
```

## Installation

```bash
pip install -r platforms/requirements.txt
```

## Architecture

```
platforms/
├── __init__.py              # Main exports
├── requirements.txt         # Dependencies
├── README.md               # This file
├── core/                   # Shared infrastructure
│   ├── logging/           # Structured logging + Langfuse
│   ├── quality/           # QMS + validation + standards
│   ├── ml_context/        # Context engine + prompt optimizer
│   └── base/              # Base agent classes
├── pydantic_ai/           # Pydantic AI platform
├── claude_sdk/            # Claude Agent SDK platform
├── n8n/                   # n8n workflow platform
├── claude_code/           # Claude Code configuration
└── google_adk/            # Google ADK platform
```

## License

MIT License - Part of the ottomator-agents project.
