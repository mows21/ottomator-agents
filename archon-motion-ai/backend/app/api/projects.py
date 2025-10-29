"""Project API endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import Project, ProjectStatus, ProjectPriority
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.agents.orchestrator import orchestrator


router = APIRouter()


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new project.

    Optionally uses AI to generate project plan.
    """
    # Create project
    project = Project(
        name=project_in.name,
        description=project_in.description,
        status=ProjectStatus.PLANNING,
        priority=project_in.priority or ProjectPriority.MEDIUM,
        deadline=project_in.deadline,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    # If auto_generate_plan, use planning agent
    if project_in.auto_generate_plan and project_in.description:
        try:
            planning_result = await orchestrator.create_project_with_agents(
                project_description=project_in.description,
                auto_schedule=True
            )
            # Store results in metadata
            project.metadata = {
                "ai_generated_plan": True,
                "plan_summary": str(planning_result.get("plan", ""))[:500]
            }
            await db.commit()
        except Exception as e:
            print(f"Error generating plan: {e}")

    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ProjectStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all projects."""
    query = select(Project).offset(skip).limit(limit)

    if status:
        query = query.where(Project.status == status)

    result = await db.execute(query)
    projects = result.scalars().all()

    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get project by ID."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()

    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/generate-plan")
async def generate_project_plan(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Generate AI-powered project plan."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.description:
        raise HTTPException(
            status_code=400,
            detail="Project must have a description to generate plan"
        )

    # Use orchestrator to generate plan
    try:
        planning_result = await orchestrator.create_project_with_agents(
            project_description=project.description
        )

        return {
            "project_id": str(project_id),
            "plan": planning_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
