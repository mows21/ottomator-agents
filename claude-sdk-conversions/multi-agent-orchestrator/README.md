# Multi-Agent Orchestrator - Claude SDK

Intelligent multi-agent system with specialized agents for different domains.

**Converted from**: `mcp-agent-army`
**Framework**: Claude Agent SDK

## Features

- **6 Specialized Agents**: Web research, code analysis, document processing, data analysis, API integration, system architecture
- **Intelligent Delegation**: Automatically routes tasks to appropriate specialists
- **Parallel Execution**: Runs multiple specialists concurrently for efficiency
- **Result Synthesis**: Combines specialist outputs into coherent answers
- **Interactive CLI**: Chat-based interface for complex tasks

## Architecture

```
┌─────────────────────────────────┐
│   Primary Orchestrator Agent    │
│   (Analyzes & Delegates)        │
└────────────┬────────────────────┘
             │
      ┌──────┴──────┬─────────────┐
      ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│   Web    │  │   Code   │  │Document  │
│Researcher│  │ Analyst  │  │Processor │
└──────────┘  └──────────┘  └──────────┘
      │             │             │
      └──────┬──────┴─────────────┘
             ▼
    ┌─────────────────┐
    │ Synthesize Results │
    └─────────────────┘
```

## Specialists

| Specialist | Expertise |
|------------|-----------|
| **Web Researcher** | Research information, analyze web content, evaluate sources |
| **Code Analyst** | Code review, bug finding, performance optimization |
| **Document Processor** | Extract information, summarize, structure content |
| **Data Analyst** | Statistical analysis, pattern recognition, insights |
| **API Expert** | API design, integration, authentication, debugging |
| **System Architect** | System design, scalability, technology selection |

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Authentication

**Option A: Claude CLI (Recommended)**
```bash
claude auth login
```

**Option B: API Key**
```bash
export ANTHROPIC_API_KEY=your_key_here
```

Or create a `.env` file:
```env
ANTHROPIC_API_KEY=your_anthropic_key
```

## Usage

### Interactive Mode

```bash
python orchestrator.py
```

Example session:

```
======================================================================
Multi-Agent Orchestrator - Claude SDK
======================================================================

Available Specialists:
  • Web Researcher: Expert at researching information and analyzing web content
  • Code Analyst: Expert at analyzing, reviewing, and improving code
  • Document Processor: Expert at processing and analyzing documents
  • Data Analyst: Expert at analyzing data and generating insights
  • API Expert: Expert at working with APIs and integrations
  • System Architect: Expert at system architecture and design

Type your requests. Complex tasks will be delegated to specialists.
Type 'exit' to quit.

You: I need to build a REST API for a document processing service. Help me design it and review this code...

Orchestrator: Analyzing request...

╭─ Orchestration Plan ─────────────────────────────────────╮
│ This requires multiple specialists:                       │
│ 1. System Architect - Design the overall API architecture│
│ 2. API Expert - Review REST API best practices          │
│ 3. Code Analyst - Review the implementation code        │
│                                                          │
│ DELEGATE: architect | Design a scalable REST API...     │
│ DELEGATE: api_expert | Review API design patterns...    │
│ DELEGATE: code_analyst | Review the code for quality... │
╰──────────────────────────────────────────────────────────╯

Executing 3 specialist task(s) in parallel...
  → System Architect processing...
  → API Expert processing...
  → Code Analyst processing...

Orchestrator: Synthesizing results...

Final Answer:

Based on analysis from multiple specialists, here's a comprehensive plan...
```

### Single Request Mode

```bash
python orchestrator.py "Analyze this Python code for performance issues"
```

## How It Works

1. **Request Analysis**: Primary orchestrator analyzes the user's request
2. **Task Delegation**: Identifies which specialists are needed
3. **Parallel Execution**: Runs specialist tasks concurrently
4. **Result Synthesis**: Combines all specialist outputs into a coherent answer

## Advantages Over MCP-Agent-Army

| Feature | MCP-Agent-Army | Claude SDK Orchestrator |
|---------|----------------|-------------------------|
| **Setup Complexity** | Requires MCP servers (npx) | Pure Python, no external servers |
| **Dependencies** | Multiple npm packages | Just Claude SDK |
| **Performance** | Network overhead | Direct API calls |
| **Error Handling** | MCP server failures | Native error handling |
| **Customization** | Limited to MCP tools | Full Python flexibility |

## Extending the System

### Adding New Specialists

```python
# In orchestrator.py, add to _initialize_specialists():

self.specialists["your_specialist"] = SpecialistAgent(
    name="Your Specialist",
    system_prompt="""You are a specialist in X.
    Focus on: task1, task2, task3.""",
    description="Expert at doing X"
)
```

### Custom Tool Integration

```python
# Specialists can use any Python library
# Example: Adding web scraping to Web Researcher

from crawl4ai import AsyncWebCrawler

async def enhanced_research(query: str) -> str:
    # Use crawl4ai or any other tool
    crawler = AsyncWebCrawler()
    result = await crawler.crawl(query)
    return result
```

## Performance Notes

- **Model Selection**: Uses `sonnet` by default. Switch to `haiku` for faster/cheaper responses
- **Parallel Execution**: All specialists run concurrently using `asyncio.gather()`
- **Token Efficiency**: Only relevant specialists are invoked

## Examples

### Example 1: Code Review

```
You: Review this FastAPI code for security issues and performance

Result:
- Code Analyst: Identifies SQL injection risk, suggests async optimization
- API Expert: Recommends authentication middleware, rate limiting
- Synthesized: Comprehensive security and performance recommendations
```

### Example 2: System Design

```
You: Design a scalable document processing pipeline

Result:
- System Architect: Proposes microservices architecture
- Document Processor: Recommends Docling for parsing
- Data Analyst: Suggests analytics pipeline
- Synthesized: Complete system design with implementation plan
```

### Example 3: Research + Implementation

```
You: Research latest RAG techniques and implement a basic version

Result:
- Web Researcher: Summarizes latest RAG papers and techniques
- Code Analyst: Reviews implementation patterns
- Synthesized: Research findings + implementation guide
```

## Troubleshooting

**Issue**: Orchestrator not delegating tasks
- **Solution**: Check that your request is clear and specific. The orchestrator needs sufficient context to determine which specialists to use.

**Issue**: Slow response times
- **Solution**: Switch specialists to `haiku` model or reduce the number of specialists for simpler tasks.

**Issue**: Authentication errors
- **Solution**: Ensure `claude auth login` was successful or `ANTHROPIC_API_KEY` is set correctly.

## Future Enhancements

- [ ] Add more specialists (Security, DevOps, ML, etc.)
- [ ] Implement specialist memory/context sharing
- [ ] Add tool use for specialists (file operations, API calls)
- [ ] Web UI for orchestration
- [ ] Metrics and cost tracking

## Resources

- [Claude Agent SDK Docs](https://docs.claude.com/en/api/agent-sdk/python)
- [Original MCP Agent Army](../../mcp-agent-army/)
- [Shared Base Classes](../shared/)

---

**Created by**: oTTomator Community
**License**: MIT
**Version**: 1.0.0
