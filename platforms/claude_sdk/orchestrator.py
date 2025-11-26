"""
Multi-Agent Orchestrator
========================

Orchestration system for coordinating multiple Claude agents
working together on complex tasks.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
from uuid import uuid4

from platforms.core.logging import StructuredLogger, MetricsCollector
from platforms.core.quality import QualityManagementSystem
from platforms.claude_sdk.agent import ClaudeSDKAgent, ClaudeSDKConfig


class AgentRole(str, Enum):
    """Predefined agent roles for common use cases."""
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    WRITER = "writer"
    ANALYST = "analyst"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"
    PLANNER = "planner"
    CRITIC = "critic"


@dataclass
class ExecutiveAgent:
    """
    An executive-level agent in a multi-agent system.

    Similar to the AI CEO system pattern.
    """
    agent_id: str = field(default_factory=lambda: str(uuid4())[:8])
    role: str = ""
    name: str = ""
    description: str = ""
    system_prompt: str = ""
    model: str = "claude-sonnet-4-5-20250929"
    priorities: List[str] = field(default_factory=list)
    kpis: List[str] = field(default_factory=list)

    # Internal agent instance
    _agent: Optional[ClaudeSDKAgent] = field(default=None, repr=False)

    async def initialize(self) -> None:
        """Initialize the underlying Claude agent."""
        config = ClaudeSDKConfig(
            name=self.name,
            system_prompt=self._build_system_prompt(),
            model=self.model,
        )
        self._agent = ClaudeSDKAgent(config)
        await self._agent.initialize()

    def _build_system_prompt(self) -> str:
        """Build the full system prompt for this executive."""
        prompt = f"""You are {self.name}, the {self.role}.

{self.description}

Your Key Priorities:
{chr(10).join(f"- {p}" for p in self.priorities)}

Your KPIs:
{chr(10).join(f"- {k}" for k in self.kpis)}

{self.system_prompt}

Always respond with actionable insights and specific recommendations.
Structure your analysis clearly with sections for:
1. Current Assessment
2. Key Insights
3. Recommendations
4. Risk Factors
5. Next Steps
"""
        return prompt

    async def execute(self, task: str, context: Optional[str] = None) -> str:
        """Execute a task and return the result."""
        if not self._agent:
            await self.initialize()

        message = task
        if context:
            message = f"Context:\n{context}\n\nTask:\n{task}"

        response = await self._agent.process(message)
        return response.content if response.success else f"Error: {response.error}"

    async def analyze(self, situation: str) -> Dict[str, Any]:
        """Analyze a situation and provide structured insights."""
        prompt = f"""Analyze the following situation and provide insights:

{situation}

Respond in JSON format with:
{{
    "assessment": "current situation assessment",
    "key_insights": ["insight1", "insight2"],
    "recommendations": ["rec1", "rec2"],
    "risks": ["risk1", "risk2"],
    "confidence": 0.0-1.0
}}"""

        response = await self._agent.process(prompt)

        try:
            import json
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "assessment": response.content,
                "key_insights": [],
                "recommendations": [],
                "risks": [],
                "confidence": 0.5,
            }


@dataclass
class OrchestrationResult:
    """Result from multi-agent orchestration."""
    task_id: str
    success: bool
    final_output: str
    agent_outputs: Dict[str, str] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "final_output": self.final_output[:500] + "..." if len(self.final_output) > 500 else self.final_output,
            "agents_used": len(self.agent_outputs),
            "execution_order": self.execution_order,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
        }


class MultiAgentOrchestrator:
    """
    Orchestrator for coordinating multiple Claude agents.

    Supports various orchestration patterns:
    - Sequential: Agents run one after another
    - Parallel: Agents run concurrently
    - Hierarchical: Coordinator delegates to specialists
    - Consensus: Multiple agents vote/agree

    Example:
        orchestrator = MultiAgentOrchestrator()

        # Add agents
        orchestrator.add_agent("researcher", researcher_agent)
        orchestrator.add_agent("writer", writer_agent)
        orchestrator.add_agent("reviewer", reviewer_agent)

        # Run sequential workflow
        result = await orchestrator.run_sequential(
            "Write an article about AI",
            agent_order=["researcher", "writer", "reviewer"],
        )
    """

    def __init__(
        self,
        name: str = "orchestrator",
        logger: Optional[StructuredLogger] = None,
        metrics: Optional[MetricsCollector] = None,
    ):
        self.name = name
        self.logger = logger or StructuredLogger(name=f"orchestrator-{name}")
        self.metrics = metrics or MetricsCollector(name=f"orchestrator-{name}")

        self._agents: Dict[str, ClaudeSDKAgent] = {}
        self._executives: Dict[str, ExecutiveAgent] = {}
        self._coordinator: Optional[ClaudeSDKAgent] = None

    def add_agent(self, name: str, agent: ClaudeSDKAgent) -> None:
        """Add an agent to the orchestrator."""
        self._agents[name] = agent
        self.logger.info(f"Added agent: {name}")

    def add_executive(self, executive: ExecutiveAgent) -> None:
        """Add an executive agent."""
        self._executives[executive.role] = executive
        self.logger.info(f"Added executive: {executive.role} ({executive.name})")

    async def set_coordinator(
        self,
        system_prompt: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
    ) -> None:
        """Set up a coordinator agent for hierarchical orchestration."""
        default_prompt = """You are a coordination agent responsible for orchestrating multiple AI agents.

Your job is to:
1. Analyze incoming tasks and break them down
2. Delegate sub-tasks to appropriate specialist agents
3. Synthesize results into a coherent final output
4. Ensure quality and consistency across agent outputs

Available agents: {agents}

For each task, respond with a JSON plan:
{{
    "analysis": "your analysis of the task",
    "subtasks": [
        {{"agent": "agent_name", "task": "specific task"}},
        ...
    ],
    "synthesis_strategy": "how to combine results"
}}"""

        prompt = system_prompt or default_prompt.format(
            agents=", ".join(self._agents.keys())
        )

        config = ClaudeSDKConfig(
            name="coordinator",
            system_prompt=prompt,
            model=model,
        )
        self._coordinator = ClaudeSDKAgent(config)
        await self._coordinator.initialize()

    async def run_sequential(
        self,
        task: str,
        agent_order: List[str],
        pass_context: bool = True,
    ) -> OrchestrationResult:
        """
        Run agents sequentially, each building on the previous output.

        Example:
            result = await orchestrator.run_sequential(
                "Write a blog post",
                ["researcher", "writer", "editor"],
            )
        """
        import time
        start_time = time.perf_counter()

        task_id = str(uuid4())[:8]
        agent_outputs = {}
        execution_order = []
        total_tokens = 0
        total_cost = 0.0

        current_context = task

        self.logger.info("Starting sequential orchestration", {
            "task_id": task_id,
            "agents": agent_order,
        })

        try:
            for agent_name in agent_order:
                agent = self._agents.get(agent_name)
                if not agent:
                    self.logger.warning(f"Agent not found: {agent_name}")
                    continue

                # Build message with context
                if pass_context and agent_outputs:
                    message = f"Previous work:\n{current_context}\n\nContinue with: {task}"
                else:
                    message = task

                response = await agent.process(message)

                agent_outputs[agent_name] = response.content
                execution_order.append(agent_name)
                total_tokens += response.total_tokens
                total_cost += response.cost_usd

                if pass_context:
                    current_context = response.content

                self.logger.info(f"Agent {agent_name} completed", {
                    "tokens": response.total_tokens,
                    "success": response.success,
                })

            total_latency = (time.perf_counter() - start_time) * 1000

            return OrchestrationResult(
                task_id=task_id,
                success=True,
                final_output=current_context,
                agent_outputs=agent_outputs,
                execution_order=execution_order,
                total_latency_ms=total_latency,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
            )

        except Exception as e:
            self.logger.error("Sequential orchestration failed", e)
            return OrchestrationResult(
                task_id=task_id,
                success=False,
                final_output=str(e),
                agent_outputs=agent_outputs,
                execution_order=execution_order,
            )

    async def run_parallel(
        self,
        task: str,
        agents: Optional[List[str]] = None,
        synthesize: bool = True,
    ) -> OrchestrationResult:
        """
        Run multiple agents in parallel on the same task.

        Optionally synthesize results using the coordinator.

        Example:
            result = await orchestrator.run_parallel(
                "Analyze this market data",
                ["analyst_1", "analyst_2", "analyst_3"],
                synthesize=True,
            )
        """
        import time
        start_time = time.perf_counter()

        task_id = str(uuid4())[:8]
        agent_names = agents or list(self._agents.keys())

        self.logger.info("Starting parallel orchestration", {
            "task_id": task_id,
            "agents": agent_names,
        })

        try:
            # Run all agents in parallel
            tasks = [
                self._agents[name].process(task)
                for name in agent_names
                if name in self._agents
            ]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            agent_outputs = {}
            total_tokens = 0
            total_cost = 0.0

            for name, response in zip(agent_names, responses):
                if isinstance(response, Exception):
                    agent_outputs[name] = f"Error: {str(response)}"
                else:
                    agent_outputs[name] = response.content
                    total_tokens += response.total_tokens
                    total_cost += response.cost_usd

            # Synthesize if requested and coordinator is available
            final_output = ""
            if synthesize and self._coordinator:
                synthesis_prompt = f"""Synthesize the following agent outputs into a coherent response:

Task: {task}

Agent Outputs:
{chr(10).join(f"[{name}]: {output}" for name, output in agent_outputs.items())}

Provide a synthesized response that combines the best insights from all agents."""

                synthesis_response = await self._coordinator.process(synthesis_prompt)
                final_output = synthesis_response.content
                total_tokens += synthesis_response.total_tokens
                total_cost += synthesis_response.cost_usd
            else:
                # Just concatenate outputs
                final_output = "\n\n".join(
                    f"[{name}]:\n{output}"
                    for name, output in agent_outputs.items()
                )

            total_latency = (time.perf_counter() - start_time) * 1000

            return OrchestrationResult(
                task_id=task_id,
                success=True,
                final_output=final_output,
                agent_outputs=agent_outputs,
                execution_order=agent_names,
                total_latency_ms=total_latency,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
            )

        except Exception as e:
            self.logger.error("Parallel orchestration failed", e)
            return OrchestrationResult(
                task_id=task_id,
                success=False,
                final_output=str(e),
            )

    async def run_hierarchical(
        self,
        task: str,
    ) -> OrchestrationResult:
        """
        Run hierarchical orchestration with coordinator delegation.

        The coordinator analyzes the task and delegates to specialists.
        """
        if not self._coordinator:
            raise ValueError("Coordinator not set. Call set_coordinator() first.")

        import time
        import json
        start_time = time.perf_counter()
        task_id = str(uuid4())[:8]

        self.logger.info("Starting hierarchical orchestration", {"task_id": task_id})

        try:
            # Get coordination plan
            plan_response = await self._coordinator.process(task)
            plan = json.loads(plan_response.content)

            agent_outputs = {"coordinator_plan": plan_response.content}
            execution_order = ["coordinator"]
            total_tokens = plan_response.total_tokens
            total_cost = plan_response.cost_usd

            # Execute subtasks
            for subtask in plan.get("subtasks", []):
                agent_name = subtask.get("agent")
                subtask_text = subtask.get("task")

                if agent_name not in self._agents:
                    continue

                response = await self._agents[agent_name].process(subtask_text)
                agent_outputs[agent_name] = response.content
                execution_order.append(agent_name)
                total_tokens += response.total_tokens
                total_cost += response.cost_usd

            # Final synthesis
            synthesis_prompt = f"""Original task: {task}

Subtask results:
{json.dumps(agent_outputs, indent=2)}

Provide a final synthesized response."""

            final_response = await self._coordinator.process(synthesis_prompt)
            total_tokens += final_response.total_tokens
            total_cost += final_response.cost_usd

            total_latency = (time.perf_counter() - start_time) * 1000

            return OrchestrationResult(
                task_id=task_id,
                success=True,
                final_output=final_response.content,
                agent_outputs=agent_outputs,
                execution_order=execution_order,
                total_latency_ms=total_latency,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
            )

        except Exception as e:
            self.logger.error("Hierarchical orchestration failed", e)
            return OrchestrationResult(
                task_id=task_id,
                success=False,
                final_output=str(e),
            )

    async def run_executive_cycle(
        self,
        situation: str,
    ) -> OrchestrationResult:
        """
        Run an executive decision cycle like the AI CEO system.

        All executives analyze the situation and provide recommendations.
        """
        import time
        start_time = time.perf_counter()
        task_id = str(uuid4())[:8]

        self.logger.info("Starting executive cycle", {
            "task_id": task_id,
            "executives": list(self._executives.keys()),
        })

        try:
            # Run all executives in parallel
            tasks = [
                exec.analyze(situation)
                for exec in self._executives.values()
            ]

            analyses = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            agent_outputs = {}
            for exec, analysis in zip(self._executives.values(), analyses):
                if isinstance(analysis, Exception):
                    agent_outputs[exec.role] = {"error": str(analysis)}
                else:
                    agent_outputs[exec.role] = analysis

            # Synthesize recommendations
            all_recommendations = []
            all_risks = []
            confidence_scores = []

            for role, analysis in agent_outputs.items():
                if isinstance(analysis, dict) and "recommendations" in analysis:
                    all_recommendations.extend(analysis.get("recommendations", []))
                    all_risks.extend(analysis.get("risks", []))
                    confidence_scores.append(analysis.get("confidence", 0.5))

            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5

            final_output = f"""Executive Analysis Summary

Situation: {situation[:200]}...

Collected Recommendations:
{chr(10).join(f"- {r}" for r in all_recommendations[:10])}

Identified Risks:
{chr(10).join(f"- {r}" for r in all_risks[:10])}

Average Confidence: {avg_confidence:.2%}

Individual Analyses:
{json.dumps(agent_outputs, indent=2)}"""

            total_latency = (time.perf_counter() - start_time) * 1000

            return OrchestrationResult(
                task_id=task_id,
                success=True,
                final_output=final_output,
                agent_outputs={k: str(v) for k, v in agent_outputs.items()},
                execution_order=list(self._executives.keys()),
                total_latency_ms=total_latency,
                metadata={"avg_confidence": avg_confidence},
            )

        except Exception as e:
            self.logger.error("Executive cycle failed", e)
            return OrchestrationResult(
                task_id=task_id,
                success=False,
                final_output=str(e),
            )


async def create_ai_ceo_system() -> MultiAgentOrchestrator:
    """
    Create an AI CEO system with executive agents.

    Modeled after the ai-ceo-system pattern.
    """
    orchestrator = MultiAgentOrchestrator(name="ai-ceo")

    # Chief Revenue Officer
    cro = ExecutiveAgent(
        role="CRO",
        name="Chief Revenue Officer",
        description="Responsible for revenue generation and sales strategy",
        priorities=["Revenue growth", "Sales optimization", "Market expansion"],
        kpis=["Monthly revenue", "Customer acquisition cost", "Lifetime value"],
        model="claude-sonnet-4-5-20250929",
    )
    await cro.initialize()
    orchestrator.add_executive(cro)

    # Chief Marketing Officer
    cmo = ExecutiveAgent(
        role="CMO",
        name="Chief Marketing Officer",
        description="Responsible for marketing strategy and brand awareness",
        priorities=["Brand awareness", "Lead generation", "Customer engagement"],
        kpis=["Marketing ROI", "Lead quality", "Brand sentiment"],
        model="claude-sonnet-4-5-20250929",
    )
    await cmo.initialize()
    orchestrator.add_executive(cmo)

    # Chief Product Officer
    cpo = ExecutiveAgent(
        role="CPO",
        name="Chief Product Officer",
        description="Responsible for product strategy and development",
        priorities=["Product-market fit", "User experience", "Innovation"],
        kpis=["User retention", "Feature adoption", "NPS score"],
        model="claude-sonnet-4-5-20250929",
    )
    await cpo.initialize()
    orchestrator.add_executive(cpo)

    # Chief Operating Officer
    coo = ExecutiveAgent(
        role="COO",
        name="Chief Operating Officer",
        description="Responsible for operations and efficiency",
        priorities=["Operational efficiency", "Process optimization", "Scaling"],
        kpis=["Cost efficiency", "Process cycle time", "Quality metrics"],
        model="claude-sonnet-4-5-20250929",
    )
    await coo.initialize()
    orchestrator.add_executive(coo)

    # Chief Financial Officer
    cfo = ExecutiveAgent(
        role="CFO",
        name="Chief Financial Officer",
        description="Responsible for financial strategy and management",
        priorities=["Financial health", "Cash flow", "Investment strategy"],
        kpis=["Burn rate", "Runway", "Unit economics"],
        model="claude-sonnet-4-5-20250929",
    )
    await cfo.initialize()
    orchestrator.add_executive(cfo)

    return orchestrator


# Import json at module level for the executive cycle
import json
