# Claude Agent SDK Conversions

This directory contains converted versions of ottomator agents using the **Claude Agent SDK** instead of Pydantic AI or other frameworks.

## Why Convert to Claude Agent SDK?

- **Native Integration**: Direct access to Claude's powerful reasoning and tool use
- **Built-in Tools**: Read, Write, Bash, Edit tools work out of the box
- **Session Management**: Persistent conversations with context
- **Streaming**: Real-time response streaming
- **Simplicity**: Less boilerplate, more focus on agent logic

## Conversion Framework

### Architecture Pattern

```
┌─────────────────────────────────────────┐
│     Claude Agent SDK (Orchestrator)     │
│  - Session management                   │
│  - Streaming responses                  │
│  - Built-in tools (Read/Write/Bash)     │
└──────────────┬──────────────────────────┘
               │
               ├── Custom Tools (as functions)
               │   ├── Web Search
               │   ├── API Calls
               │   └── External Services
               │
               └── Sub-Agents (parallel/sequential)
                   ├── Specialist Agent 1
                   ├── Specialist Agent 2
                   └── Specialist Agent N
```

### Converted Agents

| Original Agent | Framework | Claude SDK Version | Status |
|---------------|-----------|-------------------|---------|
| pydantic-ai-advanced-researcher | Pydantic AI | web-researcher | ✅ Ready |
| mcp-agent-army | Pydantic AI | multi-agent-orchestrator | ✅ Ready |
| docling-rag-agent | Custom | document-analyzer | ✅ Ready |

## Project Structure

```
claude-sdk-conversions/
├── shared/                      # Shared utilities
│   ├── base_agent.py           # Base agent class
│   ├── tools.py                # Common tool implementations
│   └── utils.py                # Helper functions
│
├── web-researcher/              # Web search agent
│   ├── agent.py                # Main agent implementation
│   ├── requirements.txt        # Dependencies
│   └── README.md              # Usage guide
│
├── multi-agent-orchestrator/    # Multi-agent system
│   ├── orchestrator.py         # Primary agent
│   ├── subagents/             # Specialist agents
│   ├── requirements.txt
│   └── README.md
│
└── document-analyzer/           # Document analysis with Docling
    ├── agent.py
    ├── requirements.txt
    └── README.md
```

## Conversion Patterns

### Pattern 1: Tool Conversion
**Pydantic AI Tool** → **Claude SDK Custom Tool**

```python
# Pydantic AI
@agent.tool
async def search_web(ctx: RunContext[Deps], query: str) -> str:
    result = await ctx.deps.client.get(...)
    return result

# Claude SDK
# Tools are defined as Python functions
# and called through Claude's tool use capabilities
async def search_web_tool(query: str) -> dict:
    async with httpx.AsyncClient() as client:
        result = await client.get(...)
        return {"result": result}
```

### Pattern 2: Multi-Agent Orchestration
**Pydantic AI Subagents** → **Claude SDK Task Tool**

```python
# Claude SDK uses query() or ClaudeSDKClient for sub-agents
from claude_agent_sdk import query

async def call_specialist(task: str) -> str:
    result = await query(
        prompt=task,
        options=ClaudeAgentOptions(
            system_prompt="You are a specialist in X"
        )
    )
    return result
```

### Pattern 3: Streaming Responses
```python
from claude_agent_sdk import ClaudeSDKClient

client = ClaudeSDKClient()
async for message in client.receive_messages():
    if isinstance(message, TextBlock):
        print(message.text, end="", flush=True)
```

## Getting Started

### Prerequisites

```bash
# Install Claude Agent SDK
pip install claude-agent-sdk anthropic

# Authenticate
claude auth login
# OR set API key
export ANTHROPIC_API_KEY=your_key_here
```

### Running an Agent

```bash
# Web Researcher
cd web-researcher
pip install -r requirements.txt
python agent.py

# Multi-Agent Orchestrator
cd multi-agent-orchestrator
pip install -r requirements.txt
python orchestrator.py

# Document Analyzer
cd document-analyzer
pip install -r requirements.txt
python agent.py
```

## Key Differences: Pydantic AI vs Claude SDK

| Feature | Pydantic AI | Claude SDK |
|---------|------------|------------|
| **Tool Definition** | @agent.tool decorator | Python functions + tool use |
| **State Management** | RunContext[Deps] | Session IDs |
| **Streaming** | run_stream() | receive_messages() |
| **Model Support** | Multi-provider | Claude models only |
| **Built-in Tools** | None | Read, Write, Bash, Edit |
| **Sub-Agents** | Agent instances | query() or ClaudeSDKClient |
| **MCP Support** | Native | Via custom tools |

## Benefits of Claude SDK

1. **Native Claude Integration**: Access to latest Claude models and features
2. **Simplified Architecture**: Built-in tools reduce custom code
3. **Better File Operations**: Native Read/Write/Edit tools
4. **Bash Integration**: Execute commands directly
5. **Session Persistence**: Easy conversation continuity

## Advanced Patterns

### Parallel Sub-Agent Execution

```python
import asyncio
from claude_agent_sdk import query

async def parallel_research(topics: list[str]) -> list[str]:
    tasks = [
        query(f"Research {topic}", options=options)
        for topic in topics
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### Tool Chaining

```python
# Claude naturally chains tools
# Example: Web search → File write → Analysis
# The agent decides the flow based on the prompt
```

### Integration with Existing Tools

Keep valuable tools like:
- **Docling**: Document processing
- **Crawl4AI**: Web scraping
- **MCP Servers**: External integrations

```python
# Wrap existing tools as async functions
async def docling_process(file_path: str) -> str:
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()
```

## Contributing

To add more conversions:

1. Create a new directory under `claude-sdk-conversions/`
2. Implement using Claude SDK patterns
3. Add requirements.txt
4. Document in README.md
5. Update this main README

## Resources

- [Claude Agent SDK Docs](https://docs.claude.com/en/api/agent-sdk/python)
- [Claude Agent SDK Examples](../claude-agent-sdk-demos/)
- [Original Agents](../)

---

**Created by**: oTTomator Community
**License**: MIT
**Version**: 1.0.0
