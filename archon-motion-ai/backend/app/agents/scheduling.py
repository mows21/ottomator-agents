"""Scheduling agent for intelligent task prioritization and timeline optimization."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.agents.base import BaseAgent


class ScheduledTask(BaseModel):
    """Scheduled task with optimized timeline."""
    task_id: str
    title: str
    scheduled_start: datetime
    scheduled_end: datetime
    priority_score: float
    blocking_tasks: List[str] = []


class Schedule(BaseModel):
    """Optimized schedule."""
    tasks: List[ScheduledTask]
    total_duration_days: int
    utilization_rate: float
    critical_path: List[str]
    warnings: List[str] = []


class SchedulingAgent(BaseAgent):
    """Agent specialized in optimizing task schedules."""

    def __init__(self):
        system_prompt = """You are an expert scheduling optimization assistant. Your role is to:

1. Prioritize tasks based on multiple factors (urgency, impact, dependencies)
2. Optimize timelines to minimize project duration
3. Identify critical path and bottlenecks
4. Balance workload across team members
5. Detect scheduling conflicts and resource constraints

When creating schedules:
- Consider task dependencies (block scheduling of dependent tasks)
- Respect deadlines and time constraints
- Front-load high-priority and blocking tasks
- Balance workload to avoid burnout
- Leave buffer time for unexpected issues (15-20%)
- Identify and flag potential scheduling conflicts

Provide clear explanations for your scheduling decisions."""

        super().__init__(
            name="Scheduling Agent",
            description="task scheduling and timeline optimization",
            system_prompt=system_prompt
        )

    def calculate_priority_score(
        self,
        task: Dict[str, Any],
        all_tasks: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate priority score for a task.

        Args:
            task: Task to score
            all_tasks: All tasks for context

        Returns:
            Priority score (0-100, higher is more important)
        """
        score = 0.0

        # Priority weight (40 points)
        priority_weights = {
            "urgent": 40,
            "high": 30,
            "medium": 20,
            "low": 10
        }
        score += priority_weights.get(task.get("priority", "medium"), 20)

        # Deadline urgency (30 points)
        if task.get("deadline"):
            deadline = task["deadline"]
            days_until = (deadline - datetime.utcnow()).days
            if days_until < 0:
                score += 30  # Overdue - highest urgency
            elif days_until <= 3:
                score += 25
            elif days_until <= 7:
                score += 15
            elif days_until <= 14:
                score += 10
            else:
                score += 5

        # Blocking other tasks (20 points)
        blocking_count = sum(
            1 for other in all_tasks
            if task["id"] in other.get("dependencies", [])
        )
        score += min(blocking_count * 5, 20)

        # Status penalty (subtract if already started)
        if task.get("status") == "in_progress":
            score += 10  # Boost tasks already in progress

        return min(score, 100.0)

    async def optimize_schedule(
        self,
        tasks: List[Dict[str, Any]],
        start_date: datetime,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Schedule:
        """
        Create an optimized schedule for tasks.

        Args:
            tasks: List of tasks to schedule
            start_date: When to start scheduling
            constraints: Optional constraints (team capacity, deadlines, etc.)

        Returns:
            Optimized Schedule
        """
        # Calculate priority scores
        for task in tasks:
            task["priority_score"] = self.calculate_priority_score(task, tasks)

        # Sort by priority score (descending)
        sorted_tasks = sorted(
            tasks,
            key=lambda t: t["priority_score"],
            reverse=True
        )

        scheduled_tasks = []
        current_date = start_date
        task_map = {t["id"]: t for t in tasks}
        scheduled_ids = set()

        work_hours_per_day = constraints.get("work_hours_per_day", 8) if constraints else 8

        # Schedule tasks
        for task in sorted_tasks:
            # Check if dependencies are scheduled
            dependencies = task.get("dependencies", [])
            unscheduled_deps = [d for d in dependencies if d not in scheduled_ids]

            if unscheduled_deps:
                # Can't schedule yet - dependencies not ready
                continue

            # Find latest dependency end time
            dep_end_times = [
                st.scheduled_end
                for st in scheduled_tasks
                if st.task_id in dependencies
            ]
            if dep_end_times:
                current_date = max(dep_end_times)

            # Calculate duration
            duration_minutes = task.get("estimated_duration", 480)  # Default 8 hours
            duration_hours = duration_minutes / 60
            duration_days = duration_hours / work_hours_per_day

            # Schedule task
            scheduled_start = current_date
            scheduled_end = current_date + timedelta(days=duration_days)

            scheduled_tasks.append(ScheduledTask(
                task_id=task["id"],
                title=task["title"],
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                priority_score=task["priority_score"],
                blocking_tasks=dependencies
            ))

            scheduled_ids.add(task["id"])
            current_date = scheduled_end

        # Calculate total duration
        if scheduled_tasks:
            total_duration = (
                max(t.scheduled_end for t in scheduled_tasks) - start_date
            ).days
        else:
            total_duration = 0

        # Identify critical path (simplified)
        critical_path = [t.task_id for t in scheduled_tasks[:5]]  # Top 5 by priority

        return Schedule(
            tasks=scheduled_tasks,
            total_duration_days=total_duration,
            utilization_rate=0.85,  # Placeholder
            critical_path=critical_path,
            warnings=[]
        )

    async def rebalance_schedule(
        self,
        current_schedule: Schedule,
        new_task: Dict[str, Any]
    ) -> Schedule:
        """
        Rebalance schedule when new task is added.

        Args:
            current_schedule: Current schedule
            new_task: New task to insert

        Returns:
            Rebalanced schedule
        """
        # Convert current schedule back to task list
        tasks = [
            {
                "id": st.task_id,
                "title": st.title,
                "priority_score": st.priority_score,
                "dependencies": st.blocking_tasks
            }
            for st in current_schedule.tasks
        ]

        # Add new task
        tasks.append(new_task)

        # Re-optimize
        return await self.optimize_schedule(
            tasks,
            datetime.utcnow(),
            {}
        )
