# Agent Conversion Guide

A practical guide for converting AI agents from other frameworks (Pydantic AI, LangChain, etc.) to Claude Agent SDK.

## Table of Contents

1. [When to Convert](#when-to-convert)
2. [Conversion Patterns](#conversion-patterns)
3. [Step-by-Step Process](#step-by-step-process)
4. [Common Challenges](#common-challenges)
5. [Best Practices](#best-practices)

## When to Convert

### Good Candidates for Conversion

✅ Agents that primarily use LLM reasoning and tool calling
✅ Agents requiring file operations (Read, Write, Edit, Bash)
✅ Multi-turn conversational agents with context
✅ Agents that benefit from Claude's advanced reasoning
✅ Projects wanting to reduce complexity and dependencies

### Keep Original Framework When

❌ Agents tightly integrated with framework-specific features
❌ Production systems requiring multi-provider support
❌ Agents using framework-specific state management patterns
❌ Systems with extensive framework-specific tooling

## Conversion Patterns

### Pattern 1: Tool Function Conversion

**From Pydantic AI:**
```python
from pydantic_ai import Agent, RunContext

@dataclass
class Deps:
    client: httpx.AsyncClient
    api_key: str

agent = Agent('openai:gpt-4', deps_type=Deps)

@agent.tool
async def search_web(ctx: RunContext[Deps], query: str) -> str:
    response = await ctx.deps.client.get(
        'https://api.example.com/search',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
        params={'q': query}
    )
    return response.text
```

**To Claude SDK:**
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import httpx

class SearchAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None

    async def search_web(self, query: str) -> str:
        if not self.client:
            self.client = httpx.AsyncClient()

        response = await self.client.get(
            'https://api.example.com/search',
            headers={'Authorization': f'Bearer {self.api_key}'},
            params={'q': query}
        )
        return response.text

    async def process_query(self, user_query: str) -> str:
        # Claude decides when to search
        # Implement tool calling or provide search results directly
        search_results = await self.search_web(user_query)

        options = ClaudeAgentOptions(
            system_prompt="You are a web search expert. Use the provided search results to answer questions."
        )

        prompt = f"""Search Results for "{user_query}":
{search_results}

Answer the user's question based on these results.
"""

        from claude_agent_sdk import query
        result = await query(prompt, options=options)
        return result
```

**Key Changes:**
- Tools become regular Python methods
- Dependencies managed via `__init__` instead of `deps_type`
- Claude handles reasoning, not explicit tool calling decoration
- Search results provided as context to Claude

### Pattern 2: Multi-Agent Conversion

**From Pydantic AI (Agent Army Pattern):**
```python
# Multiple agents with MCP servers
airtable_agent = Agent(model, mcp_servers=[airtable_server])
brave_agent = Agent(model, mcp_servers=[brave_server])

@primary_agent.tool_plain
async def use_airtable_agent(query: str) -> dict:
    result = await airtable_agent.run(query)
    return {"result": result.data}
```

**To Claude SDK:**
```python
from claude_agent_sdk import query, ClaudeAgentOptions

class SpecialistAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    async def execute(self, task: str) -> str:
        options = ClaudeAgentOptions(system_prompt=self.system_prompt)
        result = await query(task, options=options)
        return result

class Orchestrator:
    def __init__(self):
        self.specialists = {
            'airtable': SpecialistAgent('Airtable', 'You are an Airtable expert...'),
            'brave': SpecialistAgent('Brave', 'You are a web search expert...'),
        }

    async def delegate_task(self, specialist_name: str, task: str) -> str:
        specialist = self.specialists[specialist_name]
        return await specialist.execute(task)

    async def run(self, user_request: str) -> str:
        # Primary agent decides delegation
        options = ClaudeAgentOptions(
            system_prompt=f"""You are an orchestrator with these specialists:
{', '.join(self.specialists.keys())}

Analyze the request and output: DELEGATE: <name> | <task>"""
        )

        plan = await query(user_request, options=options)

        # Parse and execute delegations
        # (see full implementation in multi-agent-orchestrator/)
        ...
```

**Key Changes:**
- MCP servers replaced with specialist agents
- Each specialist is a Claude SDK query with custom system prompt
- Orchestration via Claude's reasoning instead of tool calling
- Parallel execution with `asyncio.gather()`

### Pattern 3: State Management

**From Pydantic AI:**
```python
# Built-in conversation history
messages = []

async with agent.run_stream(user_input, message_history=messages) as result:
    async for message in result.stream_text(delta=True):
        print(message)
    messages.extend(result.all_messages())
```

**To Claude SDK:**
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

client = ClaudeSDKClient()
session_id = None

# First message
await client.send_message(user_input, options=ClaudeAgentOptions(...))
result = await client.receive_response()
session_id = result.session_id

# Continue conversation
options_with_resume = ClaudeAgentOptions(
    system_prompt="...",
    resume=session_id  # Resume previous conversation
)

await client.send_message(next_input, options=options_with_resume)
```

**Key Changes:**
- Use `session_id` for conversation continuity
- Set `resume` in options to continue session
- No explicit message history management needed

## Step-by-Step Process

### Step 1: Analyze Original Agent

1. Identify core functionality
2. List all tools/functions used
3. Note external dependencies (APIs, databases, etc.)
4. Understand state management needs
5. Map conversation flow

### Step 2: Plan Architecture

1. Decide: Single agent or multi-agent?
2. Determine what becomes custom functions vs Claude's built-in tools
3. Plan system prompts for each agent
4. Design delegation strategy (if multi-agent)

### Step 3: Implement Base Structure

```python
# Use shared base classes
from shared.base_agent import BaseClaudeAgent, AgentConfig

config = AgentConfig(
    system_prompt="...",
    model="sonnet",  # or "opus", "haiku"
)

agent = BaseClaudeAgent(config)
```

### Step 4: Convert Tools

1. Extract tool logic into regular Python functions
2. Remove framework-specific decorators
3. Add proper error handling
4. Keep async/await patterns

### Step 5: Implement Agent Logic

```python
class MyAgent:
    def __init__(self):
        self.agent = BaseClaudeAgent(config)
        self.dependencies = self._setup_dependencies()

    async def process_request(self, user_input: str) -> str:
        # Prepare context
        context = await self._prepare_context(user_input)

        # Query Claude
        result = await self.agent.query(
            f"Context: {context}\n\nUser: {user_input}"
        )

        return result
```

### Step 6: Add Interactive Mode

```python
async def interactive_mode(self):
    await self.agent.start_session()

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        response = await self.agent.send_message(user_input)
        print(f"Assistant: {response['response']}")
```

### Step 7: Test & Refine

1. Test with various inputs
2. Verify tool execution
3. Check session persistence
4. Optimize system prompts
5. Add error handling

## Common Challenges

### Challenge 1: Tool Calling Patterns

**Issue**: Pydantic AI's `@agent.tool` pattern doesn't exist in Claude SDK

**Solution**:
- Provide tool results as context to Claude
- Let Claude reason about the information
- Use structured prompts to guide tool usage

```python
# Instead of @agent.tool decorator:
tool_result = await my_tool_function(params)

prompt = f"""Available information:
{tool_result}

User question: {user_question}

Answer using the information provided.
"""
```

### Challenge 2: Dependencies Management

**Issue**: No `RunContext[Deps]` equivalent

**Solution**: Use class attributes or dependency injection

```python
class Agent:
    def __init__(self, db_client, api_key):
        self.db = db_client
        self.api_key = api_key
        # Now accessible throughout the class
```

### Challenge 3: Streaming Responses

**Issue**: Different streaming APIs

**Solution**: Use `receive_messages()` instead of `run_stream()`

```python
# Pydantic AI
async with agent.run_stream(query) as result:
    async for text in result.stream_text(delta=True):
        print(text, end='')

# Claude SDK
await client.send_message(query)
async for message in client.receive_messages():
    if hasattr(message, 'text'):
        print(message.text, end='')
```

### Challenge 4: Model Selection

**Issue**: Pydantic AI supports multiple providers

**Solution**:
- Use Claude SDK for Claude models only
- Keep original agent if multi-provider is required
- Or implement provider abstraction layer

## Best Practices

### 1. System Prompt Design

```python
# Good: Clear, specific, action-oriented
system_prompt = """You are a web research specialist.

Your capabilities:
1. Analyze search queries
2. Evaluate source credibility
3. Synthesize information from multiple sources

When researching:
- Use multiple search queries for comprehensive coverage
- Always cite sources with URLs
- Note conflicting information"""

# Avoid: Vague, overly broad
system_prompt = "You are helpful and answer questions."
```

### 2. Context Management

```python
# Good: Structured context
prompt = f"""Document: {filename}

Content:
{content}

---

Question: {question}

Provide specific citations from the document."""

# Avoid: Dumping raw data
prompt = f"{content} {question}"
```

### 3. Error Handling

```python
# Good: Graceful degradation
try:
    result = await agent.query(prompt)
except Exception as e:
    logger.error(f"Agent error: {e}")
    result = "I encountered an error. Please try again."

# Avoid: Silent failures
result = await agent.query(prompt)  # No error handling
```

### 4. Parallel Execution

```python
# Good: Use asyncio.gather for parallel tasks
results = await asyncio.gather(
    specialist1.execute(task1),
    specialist2.execute(task2),
    specialist3.execute(task3),
)

# Avoid: Sequential execution when parallel is possible
result1 = await specialist1.execute(task1)
result2 = await specialist2.execute(task2)
result3 = await specialist3.execute(task3)
```

### 5. Session Management

```python
# Good: Persistent sessions
await agent.start_session()
# ... multiple interactions ...
# Session automatically maintained via session_id

# Avoid: Creating new sessions unnecessarily
# Every query creates a new session, losing context
for query in queries:
    await query(query)  # No session persistence
```

## Testing Converted Agents

### Unit Tests

```python
import pytest
from your_agent import YourAgent

@pytest.mark.asyncio
async def test_basic_query():
    agent = YourAgent()
    result = await agent.process_query("test query")
    assert result is not None
    assert len(result) > 0

@pytest.mark.asyncio
async def test_tool_execution():
    agent = YourAgent()
    tool_result = await agent.some_tool("param")
    assert tool_result is not None
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_workflow():
    agent = YourAgent()

    # Test multi-turn conversation
    await agent.start_session()
    response1 = await agent.send_message("First question")
    response2 = await agent.send_message("Follow-up question")

    assert response1['session_id'] == response2['session_id']
```

## Resources

- [Claude Agent SDK Documentation](https://docs.claude.com/en/api/agent-sdk/python)
- [Example Conversions](../README.md)
- [Shared Base Classes](../shared/base_agent.py)

## Getting Help

If you encounter issues during conversion:

1. Check the [example conversions](../) in this directory
2. Review the [original agent](../../) to understand patterns
3. Consult Claude SDK documentation
4. Ask in the oTTomator community

---

**Note**: This guide is based on practical conversions in the `claude-sdk-conversions` directory. Refer to actual code for complete implementations.
