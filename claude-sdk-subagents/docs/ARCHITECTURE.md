# Architecture Documentation

## System Overview

The Claude SDK Sub-Agents system implements a **hierarchical multi-agent architecture** where a main orchestrator coordinates specialized sub-agents to accomplish complex tasks.

## Core Components

### 1. Base Agent (`agents/base.py`)

The foundation for all agents:

```python
class BaseSubAgent:
    - name: Agent identifier
    - description: What the agent does
    - capabilities: List of keywords/capabilities
    - can_handle(task): Scoring function (0-1)
    - execute(task, context): Main execution method
```

**Key Features:**
- Capability matching via keywords
- Confidence scoring for task assignment
- Context passing between agents
- Standardized result format

### 2. Specialized Sub-Agents (`agents/research_agent.py`)

Five specialized agents:

#### Research Agent
- **Capabilities**: research, investigate, find information, gather data
- **Tools**: Information synthesis, source evaluation
- **Output**: Structured research findings

#### Code Agent
- **Capabilities**: code, programming, implement, develop, debug
- **Tools**: Code generation, best practices, testing
- **Output**: Working code with documentation

#### Analysis Agent
- **Capabilities**: analyze, evaluate, assess, compare, patterns
- **Tools**: Data analysis, statistical methods, insights
- **Output**: Analysis reports with recommendations

#### Writing Agent
- **Capabilities**: write, compose, content, blog, documentation
- **Tools**: Content creation, editing, formatting
- **Output**: Polished written content

#### Planning Agent
- **Capabilities**: plan, organize, structure, breakdown, roadmap
- **Tools**: Task decomposition, timeline estimation
- **Output**: Structured plans with timelines

### 3. Orchestrator (`agents/orchestrator.py`)

The main coordinator:

```python
class OrchestratorAgent:
    - agents: Dict of specialized sub-agents
    - execute(task): Main entry point
    - _analyze_and_plan(): Task analysis
    - _execute_sequential(): Serial execution
    - _execute_parallel(): Parallel execution
    - _aggregate_results(): Result synthesis
```

**Execution Flow:**

```
User Task
    │
    ▼
[Task Analysis]
    │
    ├──> Score each agent's capability match
    └──> Create delegation plan
    │
    ▼
[Execution Mode Decision]
    │
    ├──> Sequential (dependent tasks)
    └──> Parallel (independent tasks)
    │
    ▼
[Agent Delegation]
    │
    ├──> Research Agent
    ├──> Code Agent
    ├──> Analysis Agent
    ├──> Writing Agent
    └──> Planning Agent
    │
    ▼
[Result Aggregation]
    │
    └──> Synthesize outputs using Claude
    │
    ▼
[Final Result]
```

## Task Routing Algorithm

### 1. Capability Scoring

Each agent scores a task based on keyword matching:

```python
def can_handle(task: str) -> float:
    score = 0.0
    for capability in self.capabilities:
        if capability in task.lower():
            score += 0.3
    return min(score, 1.0)
```

**Example:**
- Task: "Research Python async and write code"
- Research Agent: 0.3 (matches "research")
- Code Agent: 0.3 (matches "write code")
- Both selected for delegation

### 2. Delegation Planning

```python
def _analyze_and_plan(task):
    # Score all agents
    agent_scores = {
        name: agent.can_handle(task)
        for name, agent in agents.items()
    }

    # Select agents with score >= 0.3
    plan = [
        {"agent": name, "score": score, "task": task}
        for name, score in agent_scores.items()
        if score >= 0.3
    ]

    return plan
```

### 3. Execution Mode

**Sequential Mode:**
- Used when tasks have dependencies
- Agents execute one after another
- Context passed between agents

**Parallel Mode:**
- Used for independent tasks
- All agents execute simultaneously
- Results combined at the end

```python
def _can_parallelize(plan):
    # Simple heuristic: multiple agents = can parallelize
    # unless explicit dependencies detected
    return len(plan) > 1
```

## Result Aggregation

When multiple agents contribute:

```
Agent 1 Result + Agent 2 Result + ... + Agent N Result
                          │
                          ▼
              [Claude Synthesis]
                          │
            Uses meta-prompt to combine:
            - Remove redundancy
            - Maintain logical flow
            - Create coherent response
                          │
                          ▼
                   Final Result
```

**Synthesis Prompt Template:**

```
Original task: {task}

Multiple agents have contributed:

### Agent 1
{result_1}

### Agent 2
{result_2}

...

Please synthesize into a coherent response that:
1. Combines all information
2. Removes redundancy
3. Maintains logical flow
4. Answers the original task completely
```

## Data Flow

### 1. Simple Task (Single Agent)

```
User: "Research Python async"
    │
    ▼
Orchestrator analyzes → Research Agent selected (score: 0.6)
    │
    ▼
Research Agent executes
    │
    ▼
Result returned directly
```

### 2. Complex Task (Multiple Agents)

```
User: "Research async, write code, analyze it"
    │
    ▼
Orchestrator analyzes
    ├──> Research Agent (score: 0.3)
    ├──> Code Agent (score: 0.3)
    └──> Analysis Agent (score: 0.3)
    │
    ▼
Sequential Execution
    ├──> Research Agent → findings
    ├──> Code Agent → code
    └──> Analysis Agent → analysis
    │
    ▼
Aggregation (Claude synthesis)
    │
    ▼
Combined result
```

### 3. Parallel Execution

```
User: "Research X and analyze Y"
    │
    ▼
Orchestrator detects independent tasks
    │
    ├──────────┬──────────┐
    │          │          │
Research  Analysis  (Parallel)
    │          │          │
    └──────────┴──────────┘
              │
              ▼
        Aggregation
              │
              ▼
       Combined result
```

## Error Handling

### Agent-Level Errors

```python
try:
    result = await agent.execute(task)
except Exception as e:
    return AgentResult(
        success=False,
        content=f"Error: {str(e)}",
        agent_name=agent.name,
        ...
    )
```

### Orchestrator-Level Errors

```python
try:
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            # Handle exception
            create_error_result(result)
except Exception as e:
    return OrchestratorResult(
        success=False,
        content=f"Orchestration failed: {str(e)}",
        ...
    )
```

## Context Sharing

Context flows through the system:

```python
context = {
    "project": "E-commerce",
    "language": "Python",
    "deadline": "3 months"
}

# Context available to all agents
result = await orchestrator.execute(task, context=context)
```

Each agent receives:
```python
def execute(task, context):
    prompt = f"{task}\n\nContext: {context}"
    # Use context in decision making
```

## Performance Considerations

### Token Usage

- **Single Agent**: ~500-2000 tokens
- **Multiple Agents**: ~1000-5000 tokens (with synthesis)
- **Parallel Execution**: Same token count, faster wall time

### Execution Time

- **Sequential**: Sum of individual agent times
- **Parallel**: Max of individual agent times (significant speedup)
- **Synthesis**: Additional ~2-5 seconds

### Optimization Strategies

1. **Task Decomposition**: Break large tasks into subtasks
2. **Parallel When Possible**: Use parallel mode for independent tasks
3. **Context Pruning**: Only include relevant context
4. **Agent Selection**: Use capability scores to filter agents

## Extension Points

### Adding Custom Agents

```python
class CustomAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="Custom Agent",
            description="Custom functionality",
            capabilities=["custom", "specialized"]
        )

    def _get_system_prompt(self):
        return "Custom system prompt..."

# Register with orchestrator
orchestrator.register_agent("custom", CustomAgent())
```

### Adding Tools

```python
class ToolEnabledAgent(BaseSubAgent):
    async def _execute_with_sdk(self, prompt):
        # Add tools here
        result = await self.client.query(
            prompt,
            tools=[...]  # Claude SDK tools
        )
        return result
```

### Custom Aggregation

```python
async def _aggregate_results(self, task, results):
    # Custom aggregation logic
    if len(results) == 1:
        return results[0].content

    # Custom synthesis
    return custom_synthesis(results)
```

## Monitoring

### Execution Logging

```python
delegation_log = [
    "[00:00:01] Orchestrator: Analyzing task...",
    "[00:00:02] Delegating to Research Agent...",
    "[00:00:05] Research Agent: Completed",
    "[00:00:06] Delegating to Code Agent...",
    "[00:00:12] Code Agent: Completed",
    "[00:00:13] Aggregating results...",
    "[00:00:14] Complete"
]
```

### Metrics Tracking

```python
class OrchestratorResult:
    success: bool
    execution_time: float
    total_tokens: int
    sub_results: List[AgentResult]

    # Per-agent metrics
    for sub_result in sub_results:
        agent_name = sub_result.agent_name
        time = sub_result.execution_time
        tokens = sub_result.tokens_used
```

## Best Practices

1. **Clear Task Descriptions**: Be specific about what you want
2. **Appropriate Context**: Include relevant but not excessive context
3. **Let Auto-Delegation Work**: Trust the capability scoring
4. **Use Parallel Mode**: For independent subtasks
5. **Monitor Performance**: Track execution times and token usage

## Future Enhancements

- **Tool Integration**: Add specialized tools per agent
- **Memory/State**: Maintain conversation history
- **Dynamic Agent Creation**: Create agents on-the-fly
- **Learning**: Improve routing based on past performance
- **Streaming**: Stream results as agents complete
- **Feedback Loop**: Agents can critique each other's work

---

This architecture enables flexible, scalable multi-agent coordination using the Claude Agent SDK.
