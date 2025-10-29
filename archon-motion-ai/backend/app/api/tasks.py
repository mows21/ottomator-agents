"""Task API endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.agents.orchestrator import orchestrator, AgentType


router = APIRouter()


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new task."""
    task = Task(
        project_id=task_in.project_id,
        title=task_in.title,
        description=task_in.description,
        status=TaskStatus.TODO,
        priority=task_in.priority or TaskPriority.MEDIUM,
        estimated_duration=task_in.estimated_duration,
        deadline=task_in.deadline,
        assigned_to=task_in.assigned_to,
        tags=task_in.tags or [],
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    return task


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[UUID] = None,
    status: Optional[TaskStatus] = None,
    assigned_to: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """List tasks with optional filters."""
    query = select(Task).offset(skip).limit(limit)

    if project_id:
        query = query.where(Task.project_id == project_id)
    if status:
        query = query.where(Task.status == status)
    if assigned_to:
        query = query.where(Task.assigned_to == assigned_to)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get task by ID."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update fields
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Track status changes
    if task_in.status == TaskStatus.IN_PROGRESS and not task.started_at:
        task.started_at = datetime.utcnow()
    elif task_in.status == TaskStatus.COMPLETED and not task.completed_at:
        task.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)

    return task


@router.get("/schedule")
async def get_optimized_schedule(
    project_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    timeframe: str = "week",
    db: AsyncSession = Depends(get_db)
):
    """Get AI-optimized task schedule."""
    # Build query
    query = select(Task)

    if project_id:
        query = query.where(Task.project_id == project_id)
    if user_id:
        query = query.where(Task.assigned_to == user_id)

    # Exclude completed tasks
    query = query.where(Task.status != TaskStatus.COMPLETED)

    result = await db.execute(query)
    tasks = result.scalars().all()

    # Convert to dict format for scheduling agent
    task_dicts = [
        {
            "id": str(task.id),
            "title": task.title,
            "priority": task.priority.value,
            "estimated_duration": task.estimated_duration or 480,
            "deadline": task.deadline,
            "dependencies": [],  # Would need to fetch dependencies
            "status": task.status.value,
        }
        for task in tasks
    ]

    # Use scheduling agent
    try:
        scheduling_agent = orchestrator.get_agent(AgentType.SCHEDULING)
        schedule = await scheduling_agent.optimize_schedule(
            task_dicts,
            datetime.utcnow(),
            {"work_hours_per_day": 8}
        )

        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
