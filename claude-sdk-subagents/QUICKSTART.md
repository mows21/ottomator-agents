# Quick Start Guide

Get started with Claude SDK Sub-Agents in 5 minutes!

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Basic Usage

### Example 1: Simple Task

```python
import asyncio
from agents.orchestrator import OrchestratorAgent

async def main():
    # Create orchestrator
    orchestrator = OrchestratorAgent()

    # Execute task (auto-delegates to appropriate agent)
    result = await orchestrator.execute(
        "Research the benefits of Python async programming"
    )

    print(result.content)

asyncio.run(main())
```

### Example 2: Complex Workflow

```python
async def main():
    orchestrator = OrchestratorAgent()

    # Multi-step task
    result = await orchestrator.execute("""
    1. Research REST API best practices
    2. Write Python code for a sample API
    3. Analyze the code for improvements
    """)

    # View which agents were used
    for sub_result in result.sub_results:
        print(f"{sub_result.agent_name}: {sub_result.execution_time:.2f}s")

    # View final result
    print(result.content)

asyncio.run(main())
```

### Example 3: With Context

```python
async def main():
    orchestrator = OrchestratorAgent()

    context = {
        "project": "E-commerce Platform",
        "tech_stack": ["Python", "FastAPI", "React"],
        "deadline": "3 months"
    }

    result = await orchestrator.execute(
        "Plan and implement user authentication",
        context=context
    )

    print(result.content)

asyncio.run(main())
```

## Running Examples

```bash
# Basic delegation example
python examples/basic_delegation.py

# Complex workflows
python examples/complex_workflow.py

# Parallel execution
python examples/parallel_execution.py
```

## Available Agents

The orchestrator automatically delegates to:

- **Research Agent**: Information gathering and research
- **Code Agent**: Writing and reviewing code
- **Analysis Agent**: Data analysis and insights
- **Writing Agent**: Content creation
- **Planning Agent**: Task breakdown and planning

## How It Works

1. **Task Analysis**: Orchestrator analyzes your task
2. **Agent Selection**: Automatically selects appropriate sub-agents
3. **Delegation**: Routes subtasks to specialized agents
4. **Execution**: Agents work sequentially or in parallel
5. **Aggregation**: Results are synthesized into final response

## Advanced Features

### Parallel Execution

```python
# Force parallel execution
result = await orchestrator.execute(
    task="Research X and analyze Y",
    mode="parallel"
)
```

### Custom Agents

```python
from agents.base import BaseSubAgent

class MyAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="My Custom Agent",
            description="Does custom things",
            capabilities=["custom", "specialized"]
        )

orchestrator = OrchestratorAgent()
orchestrator.register_agent("custom", MyAgent())
```

### Monitoring

```python
result = await orchestrator.execute(task)

# View execution trace
print(result.execution_trace)

# View token usage
print(f"Tokens used: {result.total_tokens}")

# View timing
print(f"Total time: {result.execution_time:.2f}s")
```

## Next Steps

- Read the [Full Documentation](./README.md)
- Explore [Example Workflows](./examples/)
- See [Architecture Guide](./docs/ARCHITECTURE.md)
- Check out [API Reference](./docs/API_REFERENCE.md)

## Troubleshooting

### API Key Issues

```bash
# Check if API key is set
echo $ANTHROPIC_API_KEY

# Set it if missing
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
```

### Import Errors

```bash
# Make sure you're in the right directory
cd claude-sdk-subagents

# Install dependencies
pip install -r requirements.txt
```

### No Output

If examples run but produce no output, check:
- API key is valid
- Internet connection is active
- No firewall blocking Anthropic API

## Support

- GitHub Issues: Report bugs
- Examples: See `examples/` directory
- Documentation: See `README.md`

---

**Happy orchestrating!** 🚀
