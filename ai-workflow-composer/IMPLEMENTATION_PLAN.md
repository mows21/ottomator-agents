# AI Workflow Composer - Simplified POC Implementation Plan

## Project Overview

A **proof-of-concept agent** that generates n8n workflows from natural language descriptions. This is agent #69 in the ottomator-agents repository, demonstrating advanced multi-agent coordination and workflow automation.

**Timeline:** 4-6 weeks
**Team Size:** 2-3 developers
**Budget:** ~$50K (MVP/POC)
**Focus:** Educational platform with practical value

---

## Core Philosophy: Start Simple, Add AI Incrementally

```
Phase 1: Template-Based (Week 1-2) → Validate basic concept
Phase 2: AI-Enhanced (Week 3-4)     → Add intelligent generation
Phase 3: Learning System (Week 5-6) → Enable self-improvement
```

---

## Phase 1: Template-Based Generation (Weeks 1-2)

### Goal: Prove we can programmatically create and execute n8n workflows

### Week 1: Foundation

**Day 1-2: Project Setup**
```bash
# Create structure
ai-workflow-composer/
├── templates/           # Hand-crafted n8n workflows
├── generator/          # Template matching logic
├── api/               # FastAPI MCP server
├── ui/                # Streamlit interface
├── tests/             # Validation tests
├── docs/              # Documentation
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

**Day 3-4: Template Library**
Create 10 validated n8n workflow templates:
1. `email_notification.json` - Send email via Gmail/Outlook
2. `database_query.json` - Query PostgreSQL database
3. `api_call.json` - HTTP request to REST API
4. `file_processing.json` - Read/process CSV files
5. `web_scraper.json` - Scrape website content
6. `slack_notification.json` - Post to Slack channel
7. `data_transformation.json` - Transform JSON data
8. `scheduled_task.json` - Run workflow on schedule
9. `webhook_receiver.json` - Receive webhook data
10. `multi_step_pipeline.json` - Combine multiple operations

Each template includes:
- Valid n8n JSON structure
- Parameterized placeholders ({{email}}, {{url}}, etc.)
- Metadata (description, use case, parameters)
- Test data for validation

**Day 5: Template Generator**
```python
# generator/template_matcher.py
class TemplateGenerator:
    """Match task descriptions to templates using keyword matching"""

    def match_template(self, task_description: str) -> dict:
        # Simple keyword matching
        if "email" in task_description.lower():
            return self.load_template("email_notification")
        elif "database" in task_description.lower():
            return self.load_template("database_query")
        # ... more rules

    def fill_parameters(self, template: dict, params: dict) -> dict:
        # Replace {{placeholders}} with actual values
        pass
```

### Week 2: Integration & Testing

**Day 1-2: n8n Client**
```python
# api/n8n_client.py
class N8nClient:
    """Wrapper for n8n API"""

    async def create_workflow(self, workflow_json: dict) -> str:
        """Create workflow in n8n, return workflow_id"""

    async def execute_workflow(self, workflow_id: str, input_data: dict) -> dict:
        """Execute workflow, return results"""

    async def validate_workflow(self, workflow_json: dict) -> dict:
        """Validate workflow structure"""
```

**Day 3-4: FastAPI MCP Server**
```python
# api/mcp_server.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI(title="AI Workflow Composer POC")

class WorkflowRequest(BaseModel):
    task_description: str
    parameters: dict = {}

class WorkflowResponse(BaseModel):
    workflow_id: str
    workflow_json: dict
    status: str

@app.post("/api/generate-workflow")
async def generate_workflow(request: WorkflowRequest) -> WorkflowResponse:
    # 1. Match template
    generator = TemplateGenerator()
    template = generator.match_template(request.task_description)

    # 2. Fill parameters
    workflow_json = generator.fill_parameters(template, request.parameters)

    # 3. Validate
    n8n = N8nClient()
    validation = await n8n.validate_workflow(workflow_json)

    # 4. Create in n8n
    workflow_id = await n8n.create_workflow(workflow_json)

    return WorkflowResponse(
        workflow_id=workflow_id,
        workflow_json=workflow_json,
        status="created"
    )
```

**Day 5: Testing**
- Test all 10 templates create valid workflows
- Test parameter substitution
- Test n8n execution
- Measure success rate (target: 80%+)

---

## Phase 2: AI-Enhanced Generation (Weeks 3-4)

### Goal: Add intelligent workflow generation using Pydantic AI

### Week 3: Pydantic AI Agent

**Day 1-2: Workflow Generator Agent**
```python
# generator/workflow_agent.py
from pydantic_ai import Agent
from pydantic import BaseModel

class GeneratedWorkflow(BaseModel):
    workflow_json: dict
    confidence_score: float
    reasoning: str

workflow_agent = Agent(
    'openai:gpt-4o',
    result_type=GeneratedWorkflow,
    system_prompt="""
    You are an n8n workflow generation expert.

    Given a task description, generate a valid n8n workflow JSON.
    Use the following templates as examples:
    {template_examples}

    Ensure:
    1. Valid JSON structure with "nodes" and "connections"
    2. Proper node types and parameters
    3. Correct connection mappings
    4. Error handling nodes

    Provide a confidence score (0-1) based on task complexity.
    """
)

@workflow_agent.tool
async def search_similar_workflows(ctx, task: str) -> list[dict]:
    """Search vector DB for similar workflows"""
    # RAG over template library + successful generations
    pass

@workflow_agent.tool
async def validate_node_types(ctx, nodes: list) -> dict:
    """Validate node types against n8n schema"""
    pass
```

**Day 3-4: Vector Database Integration**
```python
# Use pgvector (already in many ottomator agents)
# Store embeddings of:
# - Template workflows
# - Successfully generated workflows
# - Task descriptions

# generator/knowledge_base.py
class WorkflowKnowledgeBase:
    """RAG over workflow examples"""

    async def add_workflow(self, description: str, workflow_json: dict, success: bool):
        """Store workflow with embedding"""
        embedding = await get_embedding(description)
        await db.store(description, workflow_json, embedding, success)

    async def search_similar(self, task_description: str, limit: int = 5) -> list:
        """Find similar successful workflows"""
        embedding = await get_embedding(task_description)
        return await db.vector_search(embedding, limit)
```

**Day 5: Hybrid Approach**
```python
# generator/hybrid_generator.py
class HybridWorkflowGenerator:
    """Combine template matching + AI generation"""

    async def generate(self, task_description: str) -> dict:
        # 1. Try template matching first (fast, reliable)
        template_match = self.template_generator.match_template(task_description)

        if template_match and template_match.confidence > 0.8:
            return template_match

        # 2. Use AI for complex/novel tasks
        similar_workflows = await self.kb.search_similar(task_description)
        workflow = await self.ai_agent.run(task_description, similar_workflows)

        # 3. Validate before returning
        validation = await self.n8n.validate_workflow(workflow.workflow_json)

        if not validation.valid:
            # Fallback to template or error
            pass

        return workflow
```

### Week 4: Evaluation & Feedback

**Day 1-2: Evaluation System**
```python
# evaluation/evaluator.py
class WorkflowEvaluator:
    """Evaluate generated workflows"""

    async def evaluate(self, workflow_json: dict, execution_result: dict) -> dict:
        scores = {
            "json_validity": self._check_json_structure(workflow_json),
            "execution_success": 1.0 if execution_result.get("success") else 0.0,
            "performance": self._calculate_performance(execution_result),
            "error_rate": self._calculate_error_rate(execution_result)
        }

        overall_score = sum(scores.values()) / len(scores)

        return {
            "scores": scores,
            "overall_score": overall_score,
            "feedback": self._generate_feedback(scores)
        }
```

**Day 3-4: Feedback Loop**
```python
# Store evaluation results
# Use for:
# 1. Improving prompt templates
# 2. Filtering out failed patterns
# 3. Prioritizing successful patterns in RAG

# evaluation/feedback_loop.py
class FeedbackLoop:
    async def process_execution_result(
        self,
        task: str,
        workflow: dict,
        result: dict
    ):
        # 1. Evaluate
        evaluation = await self.evaluator.evaluate(workflow, result)

        # 2. Store in knowledge base (only if successful)
        if evaluation["overall_score"] > 0.7:
            await self.kb.add_workflow(task, workflow, success=True)

        # 3. Update metrics
        await self.metrics.record(task, evaluation)

        # 4. Generate improvement suggestions
        if evaluation["overall_score"] < 0.7:
            suggestions = await self.generate_improvements(workflow, result)
            return suggestions
```

**Day 5: Testing & Metrics**
- Test 50 diverse tasks
- Measure: success rate, execution time, error types
- Compare template-based vs AI-enhanced
- Document failure modes

---

## Phase 3: Learning System (Weeks 5-6)

### Week 5: Self-Improvement

**Day 1-2: Prompt Optimization**
```python
# Instead of genetic algorithms, use simpler proven approach:
# optimization/prompt_optimizer.py

class PromptOptimizer:
    """Optimize system prompts based on execution feedback"""

    async def optimize(self, current_prompt: str, failure_cases: list) -> str:
        # Use LLM to analyze failures and suggest prompt improvements
        analysis = await self.analyze_failures(failure_cases)

        optimization_prompt = f"""
        Current system prompt:
        {current_prompt}

        Recent failures:
        {analysis}

        Suggest 3 specific improvements to the system prompt to address these failures.
        Focus on: clarity, specificity, error handling.
        """

        suggestions = await llm.run(optimization_prompt)

        # A/B test suggestions
        return await self.test_variations(suggestions)
```

**Day 3-4: Pattern Recognition**
```python
# optimization/pattern_recognition.py
class PatternRecognizer:
    """Identify successful patterns in workflows"""

    async def analyze_successful_workflows(self) -> dict:
        # Query workflows with >0.8 success rate
        successful = await db.get_successful_workflows(threshold=0.8)

        patterns = {
            "common_node_sequences": self._find_node_patterns(successful),
            "parameter_patterns": self._find_param_patterns(successful),
            "error_handling_patterns": self._find_error_patterns(successful),
            "connection_patterns": self._find_connection_patterns(successful)
        }

        # Update agent knowledge base with patterns
        await self.kb.update_patterns(patterns)

        return patterns
```

**Day 5: Iterative Refinement**
```python
# optimization/iterative_refiner.py
class IterativeRefiner:
    """Refine failed workflows through iteration"""

    async def refine(self, task: str, failed_workflow: dict, error: dict) -> dict:
        max_attempts = 3

        for attempt in range(max_attempts):
            # Analyze error
            error_analysis = await self.analyze_error(error)

            # Generate fix
            fix_prompt = f"""
            Task: {task}

            Generated workflow failed with:
            {error_analysis}

            Workflow JSON:
            {failed_workflow}

            Suggest specific fixes to make this workflow execute successfully.
            """

            fixed_workflow = await self.agent.run(fix_prompt)

            # Test fix
            result = await self.n8n.execute_workflow(fixed_workflow)

            if result.get("success"):
                return fixed_workflow

            error = result.get("error")

        # After 3 attempts, fall back to template
        return None
```

### Week 6: Polish & Deploy

**Day 1-2: Streamlit UI**
```python
# ui/app.py
import streamlit as st

st.title("🤖 AI Workflow Composer")

tab1, tab2, tab3 = st.tabs(["Generate", "History", "Analytics"])

with tab1:
    st.header("Generate Workflow")

    task = st.text_area("Describe your workflow:", height=150)

    col1, col2 = st.columns(2)
    with col1:
        use_ai = st.checkbox("Use AI Generation", value=True)
    with col2:
        auto_execute = st.checkbox("Auto-execute", value=False)

    if st.button("Generate Workflow", type="primary"):
        with st.spinner("Generating workflow..."):
            result = await generate_workflow(task, use_ai=use_ai)

        st.success(f"Generated workflow (confidence: {result.confidence:.1%})")

        st.json(result.workflow_json)

        if auto_execute:
            with st.spinner("Executing workflow..."):
                exec_result = await execute_workflow(result.workflow_id)

            if exec_result.success:
                st.success("✅ Execution successful!")
            else:
                st.error(f"❌ Execution failed: {exec_result.error}")

with tab2:
    st.header("Generation History")
    # Show past generations with success/failure

with tab3:
    st.header("Analytics")
    # Success rate over time
    # Most common task types
    # Average execution time
```

**Day 3: Docker Setup**
```dockerfile
# Dockerfile
FROM ottomator/base-python:latest

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "api.mcp_server:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Day 4: Documentation**
```markdown
# README.md
- What it does
- How to use it
- Architecture diagram
- Examples
- Contributing guidelines
- Limitations & future work

# ARCHITECTURE.md
- System design
- Component interactions
- Data flow diagrams
- Technology choices

# USAGE_EXAMPLES.md
- 20+ example tasks
- Expected outputs
- Common patterns
```

**Day 5: Testing & Validation**
- End-to-end testing with 100 diverse tasks
- Measure final metrics:
  - Template-based success rate: Target 90%+
  - AI-enhanced success rate: Target 70%+
  - Hybrid approach success rate: Target 85%+
  - Average generation time: <5 seconds
  - Average execution time: <30 seconds

---

## Success Criteria

### Must Have (P0)
- ✅ Generate valid n8n workflows from text
- ✅ Execute workflows in n8n successfully
- ✅ 70%+ success rate on common tasks
- ✅ Basic validation and error handling
- ✅ FastAPI MCP server with authentication
- ✅ Simple UI for testing

### Should Have (P1)
- ✅ AI-enhanced generation for complex tasks
- ✅ Vector database for pattern matching
- ✅ Evaluation and feedback system
- ✅ Basic self-improvement capability
- ✅ Comprehensive documentation

### Nice to Have (P2)
- ⚠️ Advanced prompt optimization
- ⚠️ Multi-step workflow refinement
- ⚠️ Analytics dashboard
- ⚠️ Community template contributions

### Future (P3)
- ❌ Commercial SaaS features
- ❌ Billing system
- ❌ Multi-language support
- ❌ Enterprise integrations

---

## Technology Stack

**Simplified from original guide:**

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **AI Framework** | Pydantic AI | Type-safe, used in 14+ ottomator agents |
| **LLM** | OpenAI GPT-4o | Reliable, good at JSON generation |
| **Database** | PostgreSQL + pgvector | Already in 15+ agents, no new infrastructure |
| **Vector Store** | pgvector | Simpler than Qdrant, already deployed |
| **API Framework** | FastAPI | Used in 19+ ottomator agents |
| **UI** | Streamlit | Rapid prototyping (used in 12+ agents) |
| **Workflow Engine** | n8n | Core requirement, local Docker instance |
| **Container** | Docker | Standard deployment (24+ agents) |

**Removed from guide:**
- ❌ Qdrant (use pgvector instead)
- ❌ Redis/Celery (not needed for POC)
- ❌ React dashboard (Streamlit faster)
- ❌ Separate billing service (future)
- ❌ Multiple LLM providers (focus on OpenAI)

---

## Cost Estimate (POC)

```
Development (6 weeks × 2 devs × $10K/week): $120K
Infrastructure (n8n, Supabase, servers):      $2K
LLM API usage (testing):                      $5K
Contingency (20%):                            $25K
─────────────────────────────────────────────
Total:                                        ~$150K

vs Original Guide: $1.2M (92% reduction)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **n8n JSON too complex** | Start with 10 simple templates, expand gradually |
| **AI generation unreliable** | Hybrid approach: templates first, AI as fallback |
| **Execution failures** | Validation before execution, iterative refinement |
| **High API costs** | Cache similar requests, limit retries |
| **Scope creep** | Strict POC boundaries, defer commercial features |

---

## Next Steps

1. ✅ **Week 1:** Build template library + template generator
2. ⏳ **Week 2:** n8n integration + FastAPI server
3. ⏳ **Week 3:** Add Pydantic AI agent
4. ⏳ **Week 4:** Evaluation & feedback loop
5. ⏳ **Week 5:** Self-improvement features
6. ⏳ **Week 6:** UI, docs, testing, deploy

---

## Evaluation Plan

After POC completion:

**If Success Rate >70%:**
- ✅ Open-source to ottomator-agents community
- ✅ Write tutorial blog post / YouTube video
- ✅ Plan Phase 2: Advanced features

**If Success Rate 50-70%:**
- ⚠️ Analyze failure modes
- ⚠️ Improve template library
- ⚠️ Refine AI prompts
- ⚠️ Consider different approach

**If Success Rate <50%:**
- ❌ Re-evaluate core assumptions
- ❌ Consider simpler problem (e.g., workflow validator instead of generator)
- ❌ Research alternative approaches

---

## Community Contribution Plan

Once POC is validated:

1. **Template Library:** Community submits validated n8n workflows
2. **Use Case Gallery:** Real-world examples from users
3. **Prompt Engineering:** Share effective system prompts
4. **Integration Guides:** How to integrate with other tools
5. **Research:** Test alternative AI approaches

This aligns with ottomator-agents mission: educational, practical, community-driven.
