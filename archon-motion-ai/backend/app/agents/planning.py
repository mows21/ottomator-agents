"""Planning agent for project breakdown and task generation."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.base import BaseAgent, AgentContext


class TaskBreakdown(BaseModel):
    """Task breakdown structure."""
    title: str
    description: str
    estimated_duration: int  # minutes
    priority: str
    dependencies: List[str] = []
    tags: List[str] = []


class Phase(BaseModel):
    """Project phase structure."""
    name: str
    description: str
    tasks: List[TaskBreakdown]
    duration_estimate: int  # days


class ProjectPlan(BaseModel):
    """Complete project plan."""
    phases: List[Phase]
    total_tasks: int
    estimated_duration: int  # days
    key_milestones: List[str]
    risks: List[str]
    recommendations: List[str]


class PlanningAgent(BaseAgent):
    """Agent specialized in breaking down projects into actionable plans."""

    def __init__(self):
        system_prompt = """You are an expert project planning assistant. Your role is to:

1. Break down complex projects into clear phases and tasks
2. Identify dependencies between tasks
3. Estimate realistic timelines
4. Spot potential risks and bottlenecks
5. Suggest best practices and optimizations

When creating a project plan:
- Be specific and actionable with task descriptions
- Consider realistic time estimates
- Identify critical path and dependencies
- Flag potential risks early
- Suggest milestones for tracking progress

Always structure your response as a detailed JSON object following the ProjectPlan schema."""

        super().__init__(
            name="Planning Agent",
            description="project planning and task breakdown",
            system_prompt=system_prompt
        )

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register tools for the planning agent."""

        @self.agent.tool
        async def estimate_task_duration(
            ctx: RunContext[AgentContext],
            task_type: str,
            complexity: str
        ) -> str:
            """
            Estimate duration for a task based on type and complexity.

            Args:
                task_type: Type of task (backend, frontend, design, etc.)
                complexity: simple, medium, complex
            """
            # Duration estimates in hours
            base_estimates = {
                "backend": {"simple": 4, "medium": 16, "complex": 40},
                "frontend": {"simple": 4, "medium": 12, "complex": 32},
                "design": {"simple": 3, "medium": 8, "complex": 24},
                "testing": {"simple": 2, "medium": 6, "complex": 16},
                "devops": {"simple": 4, "medium": 12, "complex": 24},
                "research": {"simple": 2, "medium": 8, "complex": 20},
                "documentation": {"simple": 2, "medium": 4, "complex": 12},
            }

            task_type_lower = task_type.lower()
            complexity_lower = complexity.lower()

            # Find matching task type
            for key in base_estimates:
                if key in task_type_lower:
                    hours = base_estimates[key].get(complexity_lower, 8)
                    minutes = hours * 60
                    return f"{minutes} minutes ({hours} hours)"

            # Default estimate
            return "480 minutes (8 hours)"

        @self.agent.tool
        async def identify_dependencies(
            ctx: RunContext[AgentContext],
            task_title: str,
            all_tasks: List[str]
        ) -> List[str]:
            """
            Identify which tasks the given task depends on.

            Args:
                task_title: The task to analyze
                all_tasks: List of all task titles in the project
            """
            # Simple dependency detection based on common patterns
            dependencies = []

            task_lower = task_title.lower()

            # Common dependency patterns
            if "implement" in task_lower or "build" in task_lower:
                for other_task in all_tasks:
                    other_lower = other_task.lower()
                    if "design" in other_lower or "architecture" in other_lower:
                        dependencies.append(other_task)

            if "deploy" in task_lower:
                for other_task in all_tasks:
                    other_lower = other_task.lower()
                    if "test" in other_lower or "implement" in other_lower:
                        dependencies.append(other_task)

            if "test" in task_lower:
                for other_task in all_tasks:
                    other_lower = other_task.lower()
                    if "implement" in other_lower or "build" in other_lower:
                        dependencies.append(other_task)

            return dependencies

    async def generate_project_plan(
        self,
        project_description: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> ProjectPlan:
        """
        Generate a comprehensive project plan.

        Args:
            project_description: Description of what needs to be built
            constraints: Optional constraints (deadline, resources, etc.)

        Returns:
            ProjectPlan with phases, tasks, and recommendations
        """
        # Build prompt with constraints
        prompt = f"""Create a comprehensive project plan for:

{project_description}

"""

        if constraints:
            prompt += f"\nConstraints:\n"
            for key, value in constraints.items():
                prompt += f"- {key}: {value}\n"

        prompt += """
Provide a detailed project plan with:
1. Clear phases with specific tasks
2. Realistic time estimates for each task
3. Task dependencies
4. Key milestones
5. Potential risks
6. Recommendations for success

Format the response as a structured JSON object."""

        result = await self.run(prompt)

        if result.success:
            # Parse the result into ProjectPlan
            try:
                # This would parse the LLM response into ProjectPlan
                # For now, return a sample structure
                return ProjectPlan(
                    phases=[],
                    total_tasks=0,
                    estimated_duration=0,
                    key_milestones=[],
                    risks=[],
                    recommendations=[]
                )
            except Exception:
                # Return the raw data
                return result.data
        else:
            raise Exception(f"Planning failed: {result.error}")

    async def break_down_feature(
        self,
        feature_description: str,
        tech_stack: Optional[List[str]] = None
    ) -> List[TaskBreakdown]:
        """
        Break down a single feature into tasks.

        Args:
            feature_description: What the feature should do
            tech_stack: Technologies being used

        Returns:
            List of TaskBreakdown objects
        """
        prompt = f"""Break down this feature into specific, actionable tasks:

Feature: {feature_description}
"""

        if tech_stack:
            prompt += f"\nTech Stack: {', '.join(tech_stack)}"

        prompt += """

For each task provide:
- Clear title
- Detailed description
- Estimated duration (in minutes)
- Priority (low, medium, high, urgent)
- Any dependencies
- Relevant tags

Format as a JSON list of tasks."""

        result = await self.run(prompt)

        if result.success:
            return result.data
        else:
            raise Exception(f"Feature breakdown failed: {result.error}")
