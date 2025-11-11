# Quick Start Guide

Get started with Claude SDK agent conversions in 5 minutes.

## Prerequisites

```bash
# Python 3.10+
python --version

# Install Claude SDK
pip install claude-agent-sdk anthropic

# Authenticate
claude auth login
```

## Try the Agents

### 1. Web Researcher (Simplest)

Search the web and get synthesized answers:

```bash
cd web-researcher
pip install -r requirements.txt

# Set your Brave API key (get free key at https://brave.com/search/api/)
export BRAVE_API_KEY=your_key_here

# Run it
python agent.py "What are the latest AI developments in 2025?"
```

### 2. Multi-Agent Orchestrator (Most Impressive)

Multiple specialists working in parallel:

```bash
cd multi-agent-orchestrator
pip install -r requirements.txt

# Run interactive mode
python orchestrator.py

# Try: "Analyze this Python API code and suggest architectural improvements"
```

### 3. Document Analyzer (Most Practical)

Analyze PDFs, DOCX, and more:

```bash
cd document-analyzer
pip install -r requirements.txt

# Create documents folder and add a PDF
mkdir documents
cp ~/Downloads/sample.pdf documents/

# Run it
python agent.py

# Commands:
# list
# analyze sample.pdf What are the key points?
```

## Key Concepts

### 1. Simple Query (Stateless)

For one-off questions:

```python
from claude_agent_sdk import query

result = await query("What is 2+2?")
print(result)
```

### 2. Session (Stateful)

For conversations with context:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

client = ClaudeSDKClient()

# First message
await client.send_message("My name is Alice")
result = await client.receive_response()
session_id = result.session_id

# Continue conversation (remembers context)
options = ClaudeAgentOptions(resume=session_id)
await client.send_message("What's my name?", options=options)
result = await client.receive_response()
print(result.text)  # "Your name is Alice"
```

### 3. System Prompts

Control agent behavior:

```python
options = ClaudeAgentOptions(
    system_prompt="You are a Python expert. Provide concise code examples."
)

result = await query("How do I read a file?", options=options)
```

### 4. Parallel Processing

Run multiple agents simultaneously:

```python
import asyncio
from claude_agent_sdk import query

tasks = [
    query("Research quantum computing"),
    query("Research AI developments"),
    query("Research renewable energy")
]

results = await asyncio.gather(*tasks)
```

## Common Patterns

### Pattern 1: Custom Tools

```python
import httpx

async def search_web(query: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/search?q={query}")
        return response.text

# Use in prompt
search_results = await search_web("AI news")

result = await query(f"""
Search results: {search_results}

Summarize the latest AI news.
""")
```

### Pattern 2: Document Processing

```python
from docling.document_converter import DocumentConverter

def load_pdf(file_path: str) -> str:
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()

# Analyze document
content = load_pdf("report.pdf")
result = await query(f"""
Document content:
{content}

What are the key findings?
""")
```

### Pattern 3: Multi-Agent Delegation

```python
class Specialist:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    async def execute(self, task: str) -> str:
        options = ClaudeAgentOptions(system_prompt=self.system_prompt)
        return await query(task, options=options)

# Create specialists
code_expert = Specialist("You are a code review expert...")
security_expert = Specialist("You are a security expert...")

# Run in parallel
results = await asyncio.gather(
    code_expert.execute("Review this code"),
    security_expert.execute("Check for vulnerabilities")
)
```

## Next Steps

1. **Read the full README**: [README.md](README.md)
2. **Learn conversion patterns**: [CONVERSION_GUIDE.md](CONVERSION_GUIDE.md)
3. **Explore examples**: Check out each agent directory
4. **Build your own**: Use the shared base classes in `shared/`

## Troubleshooting

### Authentication Issues

```bash
# Re-authenticate
claude auth logout
claude auth login

# Or use API key
export ANTHROPIC_API_KEY=your_key_here
```

### Import Errors

```bash
# Make sure you're in the right directory
cd /path/to/claude-sdk-conversions/web-researcher

# Install dependencies
pip install -r requirements.txt
```

### Slow Responses

```python
# Use faster model
options = ClaudeAgentOptions(
    system_prompt="...",
    model="haiku"  # Instead of "sonnet"
)
```

## Tips

- **Start simple**: Try the web researcher first
- **Use haiku for speed**: Switch to `haiku` model for faster responses
- **Leverage built-in tools**: Claude has Read, Write, Bash, Edit tools
- **System prompts matter**: Clear, specific prompts get better results
- **Parallel when possible**: Use `asyncio.gather()` for concurrent tasks

## Help & Resources

- **Documentation**: https://docs.claude.com/en/api/agent-sdk/python
- **Examples**: See each agent directory for full implementations
- **Community**: [oTTomator Think Tank](https://thinktank.ottomator.ai)

---

Happy building! 🚀
