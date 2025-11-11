"""
FastAPI MCP Server for AI Workflow Composer.
Main API endpoint integrating template generation, AI agents, and n8n execution.
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

from generator.workflow_agent import HybridWorkflowGenerator
from api.n8n_client import N8nClient, N8nValidationError, N8nExecutionError

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Workflow Composer",
    description="Generate and execute n8n workflows from natural language",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
API_BEARER_TOKEN = os.getenv("API_BEARER_TOKEN", "your-secure-token-here")


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify bearer token"""
    if credentials.credentials != API_BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials


# Request/Response Models
class WorkflowGenerationRequest(BaseModel):
    """Request to generate a workflow"""
    task_description: str = Field(description="Natural language description of workflow")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Optional parameters for workflow")
    user_id: Optional[str] = Field(default=None, description="User ID for tracking")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")
    force_ai: bool = Field(default=False, description="Force AI generation instead of templates")


class WorkflowGenerationResponse(BaseModel):
    """Response from workflow generation"""
    workflow_id: str = Field(description="Unique workflow identifier")
    workflow_json: Dict[str, Any] = Field(description="Generated n8n workflow JSON")
    n8n_workflow_id: Optional[str] = Field(default=None, description="ID in n8n (if created)")
    generation_method: str = Field(description="template_matching or ai_generation")
    confidence_score: float = Field(description="Confidence in generation quality")
    reasoning: str = Field(description="Explanation of generation approach")
    status: str = Field(description="generated, validated, or created")
    created_at: str = Field(description="ISO timestamp of creation")


class WorkflowExecutionRequest(BaseModel):
    """Request to execute a workflow"""
    workflow_id: str = Field(description="Workflow ID to execute")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Input data for workflow")
    monitor: bool = Field(default=True, description="Monitor execution until completion")


class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution"""
    execution_id: str = Field(description="n8n execution ID")
    workflow_id: str = Field(description="Workflow ID")
    status: str = Field(description="running, completed, failed, or timeout")
    success: bool = Field(description="Whether execution succeeded")
    execution_time_ms: Optional[int] = Field(default=None, description="Execution time in milliseconds")
    output_data: Optional[Dict[str, Any]] = Field(default=None, description="Execution output")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class WorkflowValidationResponse(BaseModel):
    """Response from workflow validation"""
    valid: bool = Field(description="Whether workflow is valid")
    errors: List[str] = Field(description="List of validation errors")
    warnings: List[str] = Field(description="List of warnings")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    n8n_connected: bool
    timestamp: str


# Global state
workflow_generator: HybridWorkflowGenerator = None
n8n_client: N8nClient = None
workflow_cache: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize agents and clients on startup"""
    global workflow_generator, n8n_client

    print("Initializing AI Workflow Composer...")

    # Initialize workflow generator
    model = os.getenv("OPENAI_MODEL", "openai:gpt-4o")
    workflow_generator = HybridWorkflowGenerator(model=model)
    print(f"✓ Workflow generator initialized with model: {model}")

    # Initialize n8n client
    n8n_client = N8nClient()
    n8n_healthy = await n8n_client.health_check()
    if n8n_healthy:
        print("✓ n8n client connected")
    else:
        print("⚠ Warning: n8n server not accessible")

    print("AI Workflow Composer ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global n8n_client
    if n8n_client:
        await n8n_client.close()
    print("AI Workflow Composer shutdown complete")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    n8n_connected = False
    if n8n_client:
        n8n_connected = await n8n_client.health_check()

    return HealthResponse(
        status="healthy" if n8n_connected else "degraded",
        n8n_connected=n8n_connected,
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/generate-workflow", response_model=WorkflowGenerationResponse)
async def generate_workflow(
    request: WorkflowGenerationRequest,
    token: str = Depends(verify_token)
):
    """
    Generate an n8n workflow from natural language description.

    This endpoint:
    1. Analyzes the task description
    2. Uses template matching or AI generation
    3. Validates the generated workflow
    4. Optionally creates it in n8n
    """
    try:
        # Generate workflow using hybrid approach
        result = await workflow_generator.generate(
            task_description=request.task_description,
            parameters=request.parameters,
            force_ai=request.force_ai
        )

        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())

        # Validate workflow
        validation = await n8n_client.validate_workflow(result["workflow_json"])
        if not validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Generated workflow validation failed: {validation['errors']}"
            )

        # Store in cache
        workflow_cache[workflow_id] = {
            "workflow_json": result["workflow_json"],
            "generation_method": result["method"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "task_description": request.task_description,
            "parameters": request.parameters,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "created_at": datetime.now().isoformat()
        }

        return WorkflowGenerationResponse(
            workflow_id=workflow_id,
            workflow_json=result["workflow_json"],
            generation_method=result["method"],
            confidence_score=result["confidence"],
            reasoning=result["reasoning"],
            status="validated",
            created_at=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow generation failed: {str(e)}")


@app.post("/api/create-workflow", response_model=WorkflowGenerationResponse)
async def create_workflow_in_n8n(
    request: WorkflowGenerationRequest,
    token: str = Depends(verify_token)
):
    """
    Generate workflow and create it directly in n8n.

    This endpoint:
    1. Generates the workflow
    2. Validates it
    3. Creates it in n8n
    4. Returns the n8n workflow ID
    """
    try:
        # Generate workflow
        gen_response = await generate_workflow(request, token)

        # Create in n8n
        workflow_json = gen_response.workflow_json
        created = await n8n_client.create_workflow(
            workflow_json,
            workflow_name=workflow_json.get("name", f"Generated: {request.task_description[:50]}")
        )

        # Update cache with n8n ID
        workflow_cache[gen_response.workflow_id]["n8n_workflow_id"] = created["id"]

        gen_response.n8n_workflow_id = created["id"]
        gen_response.status = "created"

        return gen_response

    except N8nValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except N8nExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@app.post("/api/execute-workflow", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: WorkflowExecutionRequest,
    token: str = Depends(verify_token)
):
    """
    Execute a generated workflow.

    The workflow must have been created in n8n first.
    Optionally monitors execution until completion.
    """
    try:
        # Get workflow from cache
        if request.workflow_id not in workflow_cache:
            raise HTTPException(status_code=404, detail="Workflow not found")

        workflow_data = workflow_cache[request.workflow_id]
        n8n_workflow_id = workflow_data.get("n8n_workflow_id")

        if not n8n_workflow_id:
            raise HTTPException(
                status_code=400,
                detail="Workflow not created in n8n. Use /api/create-workflow first."
            )

        # Execute workflow
        execution = await n8n_client.execute_workflow(
            n8n_workflow_id,
            request.input_data
        )

        execution_id = execution.get("data", {}).get("executionId")
        if not execution_id:
            raise HTTPException(status_code=500, detail="Failed to get execution ID")

        # Monitor if requested
        if request.monitor:
            result = await n8n_client.monitor_execution(execution_id)

            return WorkflowExecutionResponse(
                execution_id=execution_id,
                workflow_id=request.workflow_id,
                status=result["status"],
                success=result.get("success", False),
                execution_time_ms=result.get("execution_time"),
                output_data=result.get("data"),
                error=result.get("error")
            )
        else:
            return WorkflowExecutionResponse(
                execution_id=execution_id,
                workflow_id=request.workflow_id,
                status="running",
                success=False
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@app.get("/api/workflow/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    token: str = Depends(verify_token)
):
    """Get workflow details by ID"""
    if workflow_id not in workflow_cache:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow_cache[workflow_id]


@app.get("/api/workflows", response_model=List[Dict[str, Any]])
async def list_workflows(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    token: str = Depends(verify_token)
):
    """List all workflows, optionally filtered by user or session"""
    workflows = []

    for wf_id, wf_data in workflow_cache.items():
        if user_id and wf_data.get("user_id") != user_id:
            continue
        if session_id and wf_data.get("session_id") != session_id:
            continue

        workflows.append({
            "workflow_id": wf_id,
            "task_description": wf_data.get("task_description"),
            "generation_method": wf_data.get("generation_method"),
            "confidence": wf_data.get("confidence"),
            "created_at": wf_data.get("created_at"),
            "n8n_workflow_id": wf_data.get("n8n_workflow_id")
        })

    return workflows


@app.post("/api/validate-workflow", response_model=WorkflowValidationResponse)
async def validate_workflow(
    workflow_json: Dict[str, Any],
    token: str = Depends(verify_token)
):
    """Validate a workflow JSON structure"""
    validation = await n8n_client.validate_workflow(workflow_json)

    return WorkflowValidationResponse(
        valid=validation["valid"],
        errors=validation["errors"],
        warnings=validation["warnings"]
    )


@app.get("/api/templates")
async def list_templates(token: str = Depends(verify_token)):
    """List available workflow templates"""
    templates = workflow_generator.template_generator.library.list_templates()

    template_info = []
    for template_name in templates:
        metadata = workflow_generator.template_generator.library.get_template_metadata(template_name)
        template_info.append({
            "name": template_name,
            "description": metadata.get("description", ""),
            "category": metadata.get("category", ""),
            "tags": metadata.get("tags", []),
            "use_cases": metadata.get("use_cases", [])
        })

    return template_info


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Workflow Composer",
        "version": "1.0.0",
        "description": "Generate and execute n8n workflows from natural language",
        "endpoints": {
            "health": "/health",
            "generate": "/api/generate-workflow",
            "create": "/api/create-workflow",
            "execute": "/api/execute-workflow",
            "validate": "/api/validate-workflow",
            "templates": "/api/templates"
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
