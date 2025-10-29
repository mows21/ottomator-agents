"""
AI Dream Command Center - Backend API Server

A comprehensive AI orchestration platform with real-time visualization.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from models import (
    TaskRequest,
    TaskResult,
    AgentState,
    AgentType,
    SystemStatus,
    Workflow,
)
from orchestrator import orchestrator
from websocket_manager import manager as ws_manager


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("🚀 AI Dream Command Center starting...")
    print(f"✓ CORS origins: {settings.cors_origins_list}")
    print(f"✓ WebSocket endpoint: ws://localhost:{settings.port}/ws")
    yield
    # Shutdown
    print("🛑 Shutting down...")
    await orchestrator.shutdown()


# Create FastAPI app
app = FastAPI(
    title="AI Dream Command Center",
    description="Real-time AI agent orchestration platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup time for uptime calculation
startup_time = datetime.utcnow()


# ============================================================================
# HTTP Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Dream Command Center",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "websocket": f"ws://localhost:{settings.port}/ws",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_connections": ws_manager.get_connection_count(),
    }


@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get overall system status."""
    agents = orchestrator.list_agents()
    uptime = (datetime.utcnow() - startup_time).total_seconds()

    return SystemStatus(
        active_agents=len(agents),
        total_tasks=len(orchestrator.task_results),
        tasks_in_progress=len(orchestrator.active_tasks),
        tasks_completed=sum(
            1 for r in orchestrator.task_results.values() if r.success
        ),
        uptime=uptime,
        agents=agents,
    )


@app.get("/agents", response_model=List[AgentState])
async def list_agents():
    """List all active agents."""
    return orchestrator.list_agents()


@app.post("/tasks", response_model=TaskResult)
async def create_task(task_request: TaskRequest):
    """
    Create and execute a new task.

    This endpoint will:
    1. Create an appropriate agent
    2. Execute the task
    3. Broadcast events via WebSocket
    4. Return the result
    """
    try:
        result = await orchestrator.execute_task(task_request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}", response_model=TaskResult)
async def get_task_result(task_id: str):
    """Get the result of a task."""
    result = orchestrator.get_task_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@app.post("/workflows", response_model=TaskResult)
async def execute_workflow(workflow: Workflow):
    """Execute a multi-step workflow."""
    try:
        result = await orchestrator.execute_workflow(workflow)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent-types")
async def get_agent_types():
    """Get list of available agent types."""
    return {
        "agent_types": [
            {
                "type": agent_type.value,
                "name": agent_type.value.replace("_", " ").title(),
            }
            for agent_type in AgentType
        ]
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Clients connect here to receive:
    - Agent status changes
    - Tool calls
    - Task progress
    - System events
    """
    client_id = None

    try:
        # Accept connection
        await ws_manager.connect(websocket)

        # Send welcome message
        await ws_manager.send_personal_message(
            {
                "type": "connection",
                "message": "Connected to AI Dream Command Center",
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

        # Send initial system status
        agents = orchestrator.list_agents()
        await ws_manager.send_personal_message(
            {
                "type": "system_status",
                "data": {
                    "active_agents": len(agents),
                    "agents": [agent.model_dump() for agent in agents],
                },
            },
            websocket,
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "ping":
                await ws_manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket,
                )

            elif data.get("type") == "get_status":
                status = await get_system_status()
                await ws_manager.send_personal_message(
                    {"type": "system_status", "data": status.model_dump()},
                    websocket,
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# ============================================================================
# Development-only endpoints
# ============================================================================


if __name__ == "__main__":
    import uvicorn

    print(f"🚀 Starting AI Dream Command Center on {settings.host}:{settings.port}")
    print(f"📚 API Documentation: http://localhost:{settings.port}/docs")
    print(f"🔌 WebSocket: ws://localhost:{settings.port}/ws")

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )
