"""Task Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """Base task schema."""
    title: str
    description: Optional[str] = None
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    estimated_duration: Optional[int] = None  # minutes
    deadline: Optional[datetime] = None
    tags: Optional[List[str]] = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    project_id: UUID
    assigned_to: Optional[UUID] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    deadline: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    tags: Optional[List[str]] = None


class TaskResponse(TaskBase):
    """Schema for task responses."""
    id: UUID
    project_id: UUID
    status: TaskStatus
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
