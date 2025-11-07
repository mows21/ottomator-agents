"""Orchestrator Agent - Coordinates and delegates to sub-agents."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from claude_agent_sdk import ClaudeSDKClient

from agents.base import BaseSubAgent, AgentResult
from agents.research_agent import (
    ResearchAgent,
    CodeAgent,
    AnalysisAgent,
    WritingAgent,
    PlanningAgent
)


@dataclass
class OrchestratorResult:
    """Result from orchestrator execution."""
    success: bool
    content: str
    sub_results: List[AgentResult] = field(default_factory=list)
    delegation_log: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    total_tokens: int = 0

    @property
    def execution_trace(self) -> str:
        """Get formatted execution trace."""
        trace = []
        for entry in self.delegation_log:
            trace.append(entry)
        return "\n".join(trace)


class OrchestratorAgent:
    """Main orchestrator that delegates tasks to specialized sub-agents."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        log_level: str = "INFO"
    ):
        """
        Initialize orchestrator.

        Args:
            model: Claude model to use
            log_level: Logging level (INFO, DEBUG)
        """
        self.model = model
        self.log_level = log_level
        self.client = ClaudeSDKClient(model=model)

        # Initialize sub-agents
        self.agents: Dict[str, BaseSubAgent] = {
            "research": ResearchAgent(),
            "code": CodeAgent(),
            "analysis": AnalysisAgent(),
            "writing": WritingAgent(),
            "planning": PlanningAgent()
        }

    def register_agent(self, name: str, agent: BaseSubAgent):
        """
        Register a custom sub-agent.

        Args:
            name: Agent identifier
            agent: Agent instance
        """
        self.agents[name] = agent

    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        mode: str = "auto"
    ) -> OrchestratorResult:
        """
        Execute a task with automatic delegation.

        Args:
            task: Task description
            context: Additional context
            mode: Execution mode (auto, sequential, parallel)

        Returns:
            OrchestratorResult with all details
        """
        start_time = datetime.utcnow()
        delegation_log = []
        sub_results = []

        try:
            # Log start
            delegation_log.append(f"[{self._timestamp()}] Orchestrator: Analyzing task...")

            # Analyze task and determine delegation strategy
            delegation_plan = await self._analyze_and_plan(task)
            delegation_log.append(
                f"[{self._timestamp()}] Orchestrator: Planning to use {len(delegation_plan)} agent(s)"
            )

            # Execute delegations
            if mode == "parallel" or (mode == "auto" and self._can_parallelize(delegation_plan)):
                sub_results = await self._execute_parallel(delegation_plan, context, delegation_log)
            else:
                sub_results = await self._execute_sequential(delegation_plan, context, delegation_log)

            # Aggregate results
            delegation_log.append(f"[{self._timestamp()}] Orchestrator: Aggregating results...")
            final_result = await self._aggregate_results(task, sub_results)

            # Calculate totals
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            total_tokens = sum(r.tokens_used for r in sub_results)

            delegation_log.append(f"[{self._timestamp()}] Orchestrator: Complete")

            return OrchestratorResult(
                success=True,
                content=final_result,
                sub_results=sub_results,
                delegation_log=delegation_log,
                execution_time=execution_time,
                total_tokens=total_tokens
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            delegation_log.append(f"[{self._timestamp()}] Orchestrator: Error - {str(e)}")

            return OrchestratorResult(
                success=False,
                content=f"Orchestration failed: {str(e)}",
                delegation_log=delegation_log,
                execution_time=execution_time
            )

    async def _analyze_and_plan(self, task: str) -> List[Dict[str, Any]]:
        """
        Analyze task and create delegation plan.

        Args:
            task: Task description

        Returns:
            List of delegation steps
        """
        # Score each agent for this task
        agent_scores = {}
        for name, agent in self.agents.items():
            score = agent.can_handle(task)
            if score > 0:
                agent_scores[name] = score

        # Create delegation plan
        plan = []

        # If multiple agents score high, delegate to all
        if len(agent_scores) > 1:
            # Sort by score
            sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)

            for agent_name, score in sorted_agents:
                if score >= 0.3:  # Threshold for inclusion
                    plan.append({
                        "agent": agent_name,
                        "score": score,
                        "task": task  # Could be refined per agent
                    })
        elif len(agent_scores) == 1:
            # Single agent delegation
            agent_name = list(agent_scores.keys())[0]
            plan.append({
                "agent": agent_name,
                "score": agent_scores[agent_name],
                "task": task
            })
        else:
            # No specific agent - use research as default
            plan.append({
                "agent": "research",
                "score": 0.5,
                "task": task
            })

        return plan

    async def _execute_sequential(
        self,
        plan: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
        log: List[str]
    ) -> List[AgentResult]:
        """Execute delegation plan sequentially."""
        results = []

        for step in plan:
            agent_name = step["agent"]
            agent = self.agents[agent_name]

            log.append(f"[{self._timestamp()}] Delegating to {agent.name}...")

            result = await agent.execute(step["task"], context)
            results.append(result)

            log.append(
                f"[{self._timestamp()}] {agent.name}: {'Completed' if result.success else 'Failed'}"
            )

        return results

    async def _execute_parallel(
        self,
        plan: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
        log: List[str]
    ) -> List[AgentResult]:
        """Execute delegation plan in parallel."""
        log.append(f"[{self._timestamp()}] Executing {len(plan)} agents in parallel...")

        # Create tasks
        tasks = []
        for step in plan:
            agent = self.agents[step["agent"]]
            tasks.append(agent.execute(step["task"], context))

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_name = plan[i]["agent"]
                final_results.append(AgentResult(
                    success=False,
                    content=f"Error: {str(result)}",
                    agent_name=agent_name,
                    execution_time=0.0
                ))
            else:
                final_results.append(result)

        return final_results

    def _can_parallelize(self, plan: List[Dict[str, Any]]) -> bool:
        """
        Determine if plan can be parallelized.

        Args:
            plan: Delegation plan

        Returns:
            True if can run in parallel
        """
        # Simple heuristic: if multiple agents, can parallelize
        # unless there are explicit dependencies
        return len(plan) > 1

    async def _aggregate_results(
        self,
        original_task: str,
        results: List[AgentResult]
    ) -> str:
        """
        Aggregate results from sub-agents.

        Args:
            original_task: Original task description
            results: Results from sub-agents

        Returns:
            Aggregated response
        """
        if len(results) == 1:
            # Single result - return directly
            return results[0].content

        # Multiple results - synthesize
        synthesis_prompt = f"""Original task: {original_task}

Multiple specialized agents have worked on this task. Synthesize their outputs into a coherent, comprehensive response.

Agent Results:

"""

        for result in results:
            synthesis_prompt += f"\n### {result.agent_name}\n"
            synthesis_prompt += result.content
            synthesis_prompt += "\n\n"

        synthesis_prompt += """
Please synthesize the above results into a single, well-organized response that:
1. Combines all relevant information
2. Removes redundancy
3. Maintains logical flow
4. Provides a complete answer to the original task
"""

        # Use Claude to synthesize
        from claude_agent_sdk import query
        synthesized = await query(synthesis_prompt, model=self.model)

        return synthesized

    def _timestamp(self) -> str:
        """Get formatted timestamp."""
        return datetime.utcnow().strftime("%H:%M:%S")

    def list_agents(self) -> Dict[str, str]:
        """
        List all available agents.

        Returns:
            Dictionary of agent names and descriptions
        """
        return {
            name: agent.description
            for name, agent in self.agents.items()
        }
