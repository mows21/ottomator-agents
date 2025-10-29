"""Project Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.project import ProjectStatus, ProjectPriority


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str
    description: Optional[str] = None
    priority: Optional[ProjectPriority] = ProjectPriority.MEDIUM
    deadline: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    auto_generate_plan: bool = False


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    deadline: Optional[datetime] = None


class ProjectResponse(ProjectBase):
    """Schema for project responses."""
    id: UUID
    status: ProjectStatus
    start_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
