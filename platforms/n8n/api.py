"""
n8n API Client
==============

Client for interacting with n8n API to manage and execute workflows.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from platforms.core.logging import StructuredLogger


@dataclass
class WorkflowExecution:
    """Result of a workflow execution."""
    execution_id: str
    workflow_id: str
    status: str  # running, success, error, waiting
    data: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "data": self.data,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "error": self.error,
        }


class N8NClient:
    """
    Client for n8n API.

    Example:
        client = N8NClient(
            base_url="http://localhost:5678",
            api_key="your-api-key",
        )

        # Execute workflow
        result = await client.execute_workflow(
            workflow_id="workflow-123",
            data={"message": "Hello"},
        )

        # Get execution status
        status = await client.get_execution(result.execution_id)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        logger: Optional[StructuredLogger] = None,
    ):
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx package required. Install with: pip install httpx")

        self.base_url = (base_url or os.getenv("N8N_BASE_URL", "http://localhost:5678")).rstrip("/")
        self.api_key = api_key or os.getenv("N8N_API_KEY")
        self.logger = logger or StructuredLogger(name="n8n-client")

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-N8N-API-KEY": self.api_key} if self.api_key else {},
            timeout=60.0,
        )

    async def execute_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecution:
        """Execute a workflow by ID."""
        self.logger.info("Executing workflow", {"workflow_id": workflow_id})

        try:
            response = await self._client.post(
                f"/api/v1/workflows/{workflow_id}/execute",
                json={"data": data or {}},
            )
            response.raise_for_status()
            result = response.json()

            return WorkflowExecution(
                execution_id=result.get("executionId", ""),
                workflow_id=workflow_id,
                status="running",
                data=result.get("data", {}),
            )

        except Exception as e:
            self.logger.error("Workflow execution failed", e)
            return WorkflowExecution(
                execution_id="",
                workflow_id=workflow_id,
                status="error",
                error=str(e),
            )

    async def execute_webhook(
        self,
        webhook_path: str,
        data: Dict[str, Any],
        method: str = "POST",
    ) -> Dict[str, Any]:
        """Execute a workflow via webhook."""
        self.logger.info("Calling webhook", {"path": webhook_path})

        try:
            url = f"/webhook/{webhook_path.lstrip('/')}"

            if method.upper() == "POST":
                response = await self._client.post(url, json=data)
            else:
                response = await self._client.get(url, params=data)

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error("Webhook execution failed", e)
            return {"error": str(e)}

    async def get_execution(self, execution_id: str) -> WorkflowExecution:
        """Get execution status and result."""
        try:
            response = await self._client.get(f"/api/v1/executions/{execution_id}")
            response.raise_for_status()
            result = response.json()

            return WorkflowExecution(
                execution_id=execution_id,
                workflow_id=result.get("workflowId", ""),
                status=result.get("status", "unknown"),
                data=result.get("data", {}),
                finished_at=datetime.fromisoformat(result["stoppedAt"]) if result.get("stoppedAt") else None,
                error=result.get("error"),
            )

        except Exception as e:
            self.logger.error("Failed to get execution", e)
            return WorkflowExecution(
                execution_id=execution_id,
                workflow_id="",
                status="error",
                error=str(e),
            )

    async def list_workflows(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all workflows."""
        try:
            params = {"active": "true"} if active_only else {}
            response = await self._client.get("/api/v1/workflows", params=params)
            response.raise_for_status()
            return response.json().get("data", [])

        except Exception as e:
            self.logger.error("Failed to list workflows", e)
            return []

    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Optional[str]:
        """Create a new workflow."""
        try:
            response = await self._client.post("/api/v1/workflows", json=workflow_data)
            response.raise_for_status()
            result = response.json()
            return result.get("id")

        except Exception as e:
            self.logger.error("Failed to create workflow", e)
            return None

    async def update_workflow(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any],
    ) -> bool:
        """Update an existing workflow."""
        try:
            response = await self._client.patch(
                f"/api/v1/workflows/{workflow_id}",
                json=workflow_data,
            )
            response.raise_for_status()
            return True

        except Exception as e:
            self.logger.error("Failed to update workflow", e)
            return False

    async def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow."""
        return await self.update_workflow(workflow_id, {"active": True})

    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow."""
        return await self.update_workflow(workflow_id, {"active": False})

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


async def execute_agent_workflow(
    workflow_id: str,
    message: str,
    session_id: str,
    user_id: Optional[str] = None,
    n8n_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute an agent workflow with standard input format.

    This is a convenience function for the common agent pattern.
    """
    client = N8NClient(base_url=n8n_url)

    try:
        result = await client.execute_workflow(
            workflow_id=workflow_id,
            data={
                "message": message,
                "session_id": session_id,
                "user_id": user_id,
            },
        )

        # Wait for completion with timeout
        import asyncio
        for _ in range(60):  # 60 second timeout
            status = await client.get_execution(result.execution_id)
            if status.status in ["success", "error"]:
                return status.to_dict()
            await asyncio.sleep(1)

        return {"error": "Workflow execution timeout"}

    finally:
        await client.close()
