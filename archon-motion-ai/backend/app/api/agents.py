"""Agent API endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.orchestrator import orchestrator, AgentType, AgentContext


router = APIRouter()


class AgentExecuteRequest(BaseModel):
    """Request to execute an agent."""
    agent_type: str
    task: str
    context: Optional[dict] = None


class WorkflowRequest(BaseModel):
    """Request to execute a workflow."""
    task: str
    context: Optional[dict] = None
    agents: Optional[list[str]] = None


@router.post("/execute")
async def execute_agent(request: AgentExecuteRequest):
    """Execute a specific agent with a task."""
    try:
        agent_type = AgentType(request.agent_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent type: {request.agent_type}"
        )

    agent = orchestrator.get_agent(agent_type)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent {request.agent_type} not found"
        )

    # Build context
    context = AgentContext(**(request.context or {}))

    # Execute agent
    try:
        result = await agent.run(request.task, context)
        return {
            "agent_type": request.agent_type,
            "task": request.task,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflow")
async def execute_workflow(request: WorkflowRequest):
    """Execute a multi-agent workflow."""
    # Build context
    context = AgentContext(**(request.context or {}))

    # Parse agent types
    agents_to_use = None
    if request.agents:
        try:
            agents_to_use = [AgentType(a) for a in request.agents]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Execute workflow
    try:
        results = await orchestrator.execute_workflow(
            task=request.task,
            context=context,
            agents_to_use=agents_to_use
        )

        return {
            "task": request.task,
            "agents_used": list(results.keys()),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def list_agent_types():
    """List available agent types."""
    return {
        "agent_types": [
            {
                "type": agent_type.value,
                "name": agent_type.value.replace("_", " ").title(),
                "available": agent_type in orchestrator.agents
            }
            for agent_type in AgentType
        ]
    }
