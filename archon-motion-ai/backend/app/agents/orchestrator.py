"""Agent orchestrator for coordinating multiple agents."""

from typing import Optional, Dict, Any, List
from enum import Enum

from app.agents.planning import PlanningAgent, ProjectPlan
from app.agents.scheduling import SchedulingAgent, Schedule
from app.agents.base import AgentResult, AgentContext


class AgentType(str, Enum):
    """Available agent types."""
    PLANNING = "planning"
    SCHEDULING = "scheduling"
    CODE = "code"
    RESEARCH = "research"
    RISK = "risk"


class AgentOrchestrator:
    """Orchestrates multiple AI agents to accomplish complex tasks."""

    def __init__(self):
        self.agents = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all available agents."""
        self.agents[AgentType.PLANNING] = PlanningAgent()
        self.agents[AgentType.SCHEDULING] = SchedulingAgent()
        # Add more agents as they're implemented

    def get_agent(self, agent_type: AgentType):
        """Get a specific agent instance."""
        return self.agents.get(agent_type)

    async def execute_workflow(
        self,
        task: str,
        context: Optional[AgentContext] = None,
        agents_to_use: Optional[List[AgentType]] = None
    ) -> Dict[str, Any]:
        """
        Execute a multi-agent workflow.

        Args:
            task: The task description
            context: Context for execution
            agents_to_use: Specific agents to use (auto-detect if None)

        Returns:
            Dictionary with results from each agent
        """
        results = {}

        # Auto-detect which agents to use if not specified
        if not agents_to_use:
            agents_to_use = self._detect_required_agents(task)

        # Execute agents in sequence
        for agent_type in agents_to_use:
            agent = self.agents.get(agent_type)
            if agent:
                result = await agent.run(task, context)
                results[agent_type.value] = result

        return results

    def _detect_required_agents(self, task: str) -> List[AgentType]:
        """
        Detect which agents are needed for a task.

        Args:
            task: Task description

        Returns:
            List of required agent types
        """
        task_lower = task.lower()
        agents = []

        # Planning keywords
        if any(word in task_lower for word in ["create project", "break down", "plan", "roadmap"]):
            agents.append(AgentType.PLANNING)

        # Scheduling keywords
        if any(word in task_lower for word in ["schedule", "timeline", "when", "prioritize"]):
            agents.append(AgentType.SCHEDULING)

        # Code keywords
        if any(word in task_lower for word in ["code", "implement", "build", "develop"]):
            agents.append(AgentType.CODE)

        # Research keywords
        if any(word in task_lower for word in ["research", "find", "search", "learn"]):
            agents.append(AgentType.RESEARCH)

        # Risk keywords
        if any(word in task_lower for word in ["risk", "deadline", "analyze", "health"]):
            agents.append(AgentType.RISK)

        # Default to planning if nothing detected
        if not agents:
            agents.append(AgentType.PLANNING)

        return agents

    async def create_project_with_agents(
        self,
        project_description: str,
        auto_schedule: bool = True,
        context: Optional[AgentContext] = None
    ) -> Dict[str, Any]:
        """
        Create a complete project using multiple agents.

        Args:
            project_description: What to build
            auto_schedule: Whether to auto-schedule tasks
            context: Additional context

        Returns:
            Dictionary with project plan and schedule
        """
        results = {}

        # 1. Use planning agent to break down project
        planning_agent = self.agents[AgentType.PLANNING]
        plan_result = await planning_agent.generate_project_plan(
            project_description
        )
        results["plan"] = plan_result

        # 2. If auto_schedule, use scheduling agent
        if auto_schedule and isinstance(plan_result, ProjectPlan):
            # Extract tasks from plan
            all_tasks = []
            for phase in plan_result.phases:
                for task in phase.tasks:
                    all_tasks.append({
                        "id": f"task_{len(all_tasks)}",
                        "title": task.title,
                        "description": task.description,
                        "estimated_duration": task.estimated_duration,
                        "priority": task.priority,
                        "dependencies": task.dependencies
                    })

            scheduling_agent = self.agents[AgentType.SCHEDULING]
            schedule = await scheduling_agent.optimize_schedule(
                all_tasks,
                context.metadata.get("start_date") if context else None
            )
            results["schedule"] = schedule

        return results


# Global instance
orchestrator = AgentOrchestrator()
