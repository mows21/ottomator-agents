"""Main FastAPI application for Archon Motion AI."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api import projects, tasks, agents, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("🚀 Archon Motion AI starting...")
    await init_db()
    print(f"✓ Database initialized")
    print(f"✓ CORS origins: {settings.cors_origins_list}")
    yield
    # Shutdown
    print("🛑 Shutting down...")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="Archon Motion AI",
    description="AI-Powered Project Management System with Claude Integration",
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

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Archon Motion AI",
        "version": "1.0.0",
        "description": "AI-Powered Project Management System",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "features": {
            "planning_agent": True,
            "scheduling_agent": True,
            "rag_engine": False,  # To be implemented
            "websockets": settings.enable_websockets,
        }
    }


if __name__ == "__main__":
    import uvicorn

    print(f"🚀 Starting Archon Motion AI on {settings.host}:{settings.port}")
    print(f"📚 API Documentation: http://localhost:{settings.port}/docs")

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
