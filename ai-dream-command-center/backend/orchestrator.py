"""Agent orchestrator for managing multiple agents and workflows."""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from agents import DreamAgent, ResearchAgent, CoderAgent, AnalystAgent, WebSearchAgent
from models import (
    AgentType,
    AgentStatus,
    AgentState,
    AgentEvent,
    TaskRequest,
    TaskResult,
    Workflow,
    WorkflowStep,
)
from websocket_manager import manager as ws_manager


class AgentOrchestrator:
    """Orchestrates multiple AI agents and workflows."""

    def __init__(self):
        self.agents: Dict[str, DreamAgent] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, TaskResult] = {}

    def create_agent(self, agent_type: AgentType) -> DreamAgent:
        """Create a new agent instance."""
        agent_id = f"{agent_type.value}_{uuid.uuid4().hex[:8]}"

        agent_classes = {
            AgentType.RESEARCHER: ResearchAgent,
            AgentType.CODER: CoderAgent,
            AgentType.ANALYST: AnalystAgent,
            AgentType.WEB_SEARCHER: WebSearchAgent,
        }

        agent_class = agent_classes.get(agent_type, DreamAgent)
        agent = agent_class(agent_id)

        self.agents[agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[DreamAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[AgentState]:
        """List all active agents."""
        states = []
        for agent in self.agents.values():
            state = AgentState(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type,
                status=agent.status,
                tokens_used=agent.tokens_used,
            )
            states.append(state)
        return states

    async def execute_task(self, task_request: TaskRequest) -> TaskResult:
        """Execute a task with an agent."""
        task_id = task_request.task_id or f"task_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()

        try:
            # Determine agent type
            agent_type = task_request.agent_type or AgentType.RESEARCHER

            # Create or get agent
            agent = self.create_agent(agent_type)

            # Broadcast agent creation
            await ws_manager.broadcast_agent_event(
                {
                    "event_type": "agent_created",
                    "agent_id": agent.agent_id,
                    "agent_type": agent_type.value,
                    "task_id": task_id,
                }
            )

            # Execute task
            result_text = await agent.run(task_request.prompt, task_request.context)

            # Get all events
            events = agent.get_events()

            # Broadcast events
            for event in events:
                await ws_manager.broadcast_agent_event(event.model_dump())

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            task_result = TaskResult(
                task_id=task_id,
                success=True,
                result=result_text,
                agents_used=[agent.agent_id],
                total_tokens=agent.tokens_used,
                execution_time=execution_time,
                events=events,
            )

            self.task_results[task_id] = task_result
            return task_result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            task_result = TaskResult(
                task_id=task_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
            )

            self.task_results[task_id] = task_result

            # Broadcast error
            await ws_manager.broadcast_agent_event(
                {
                    "event_type": "error",
                    "task_id": task_id,
                    "error": str(e),
                }
            )

            return task_result

    async def execute_workflow(self, workflow: Workflow) -> TaskResult:
        """Execute a multi-step workflow."""
        task_id = f"workflow_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()
        agents_used = []
        all_events = []
        results = {}

        try:
            if workflow.parallel_execution:
                # Execute steps in parallel
                tasks = []
                for step in workflow.steps:
                    task = self._execute_workflow_step(step, results)
                    tasks.append(task)

                step_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, step_result in enumerate(step_results):
                    if isinstance(step_result, Exception):
                        raise step_result
                    results[workflow.steps[i].step_id] = step_result

            else:
                # Execute steps sequentially
                for step in workflow.steps:
                    # Wait for dependencies
                    if step.depends_on:
                        for dep_id in step.depends_on:
                            if dep_id not in results:
                                raise ValueError(f"Dependency {dep_id} not completed")

                    step_result = await self._execute_workflow_step(step, results)
                    results[step.step_id] = step_result

            # Combine results
            final_result = "\n\n".join(
                f"Step {step_id}: {result}" for step_id, result in results.items()
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return TaskResult(
                task_id=task_id,
                success=True,
                result=final_result,
                agents_used=agents_used,
                execution_time=execution_time,
                events=all_events,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return TaskResult(
                task_id=task_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
            )

    async def _execute_workflow_step(
        self, step: WorkflowStep, previous_results: Dict[str, str]
    ) -> str:
        """Execute a single workflow step."""
        # Create agent for this step
        agent = self.create_agent(step.agent_type)

        # Build context from previous steps
        context = {
            "previous_results": previous_results,
            "step_id": step.step_id,
        }

        # Execute
        result = await agent.run(step.prompt, context)

        # Broadcast events
        for event in agent.get_events():
            await ws_manager.broadcast_agent_event(event.model_dump())

        return result

    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result of a completed task."""
        return self.task_results.get(task_id)

    async def shutdown(self):
        """Shutdown all agents and cleanup."""
        # Cancel active tasks
        for task in self.active_tasks.values():
            task.cancel()

        # Clear agents
        self.agents.clear()


# Global orchestrator instance
orchestrator = AgentOrchestrator()
