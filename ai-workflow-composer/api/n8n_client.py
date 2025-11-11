"""
n8n API client for workflow creation and execution.
Handles all communication with n8n server.
"""

import httpx
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class N8nValidationError(Exception):
    """Raised when workflow validation fails"""
    pass


class N8nExecutionError(Exception):
    """Raised when workflow execution fails"""
    pass


class N8nClient:
    """
    Async client for n8n API operations.
    Supports workflow creation, execution, and monitoring.
    """

    def __init__(self,
                 base_url: str = None,
                 api_key: str = None,
                 username: str = None,
                 password: str = None):
        """
        Initialize n8n client.

        Args:
            base_url: n8n server URL (default: from env)
            api_key: API key for authentication (default: from env)
            username: Basic auth username (fallback auth method)
            password: Basic auth password (fallback auth method)
        """
        self.base_url = base_url or os.getenv("N8N_BASE_URL", "http://localhost:5678")
        self.api_key = api_key or os.getenv("N8N_API_KEY")
        self.username = username or os.getenv("N8N_USERNAME", "admin")
        self.password = password or os.getenv("N8N_PASSWORD", "admin123")

        # Set up authentication
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["X-N8N-API-KEY"] = self.api_key

        # Create async HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            auth=(self.username, self.password) if not self.api_key else None,
            timeout=30.0,
            follow_redirects=True
        )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def health_check(self) -> bool:
        """
        Check if n8n server is accessible.

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = await self.client.get("/healthz")
            return response.status_code == 200
        except Exception as e:
            print(f"n8n health check failed: {e}")
            return False

    async def validate_workflow(self, workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate workflow structure before creation.

        Args:
            workflow_json: Workflow definition to validate

        Returns:
            Dict with validation results:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        errors = []
        warnings = []

        # Required fields
        required_fields = ["nodes", "connections"]
        for field in required_fields:
            if field not in workflow_json:
                errors.append(f"Missing required field: {field}")

        # Validate nodes
        if "nodes" in workflow_json:
            nodes = workflow_json["nodes"]
            if not isinstance(nodes, list):
                errors.append("'nodes' must be a list")
            elif len(nodes) == 0:
                errors.append("Workflow must contain at least one node")
            else:
                # Validate each node
                node_ids = set()
                for i, node in enumerate(nodes):
                    if not isinstance(node, dict):
                        errors.append(f"Node {i} is not a dictionary")
                        continue

                    # Check required node fields
                    if "type" not in node:
                        errors.append(f"Node {i} missing 'type' field")
                    if "name" not in node:
                        warnings.append(f"Node {i} missing 'name' field")
                    if "id" in node:
                        if node["id"] in node_ids:
                            errors.append(f"Duplicate node ID: {node['id']}")
                        node_ids.add(node["id"])

        # Validate connections
        if "connections" in workflow_json:
            connections = workflow_json["connections"]
            if not isinstance(connections, dict):
                errors.append("'connections' must be a dictionary")

        # Check for credentials
        if "nodes" in workflow_json:
            for node in workflow_json["nodes"]:
                if "credentials" in node:
                    warnings.append(
                        f"Node '{node.get('name')}' requires credentials to be configured"
                    )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def create_workflow(self, workflow_json: Dict[str, Any],
                            workflow_name: str = None) -> Dict[str, Any]:
        """
        Create a new workflow in n8n.

        Args:
            workflow_json: Workflow definition
            workflow_name: Optional name override

        Returns:
            Created workflow data including ID

        Raises:
            N8nValidationError: If workflow validation fails
            N8nExecutionError: If creation fails
        """
        # Validate first
        validation = await self.validate_workflow(workflow_json)
        if not validation["valid"]:
            raise N8nValidationError(f"Validation failed: {validation['errors']}")

        # Set workflow name
        if workflow_name:
            workflow_json["name"] = workflow_name
        elif "name" not in workflow_json:
            workflow_json["name"] = f"Generated Workflow {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Add required fields
        workflow_json.setdefault("active", False)  # Start inactive by default
        workflow_json.setdefault("settings", {})

        try:
            response = await self.client.post(
                "/api/v1/workflows",
                json=workflow_json
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise N8nExecutionError(f"Failed to create workflow: {error_detail}")
        except Exception as e:
            raise N8nExecutionError(f"Failed to create workflow: {str(e)}")

    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow details by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow data
        """
        try:
            response = await self.client.get(f"/api/v1/workflows/{workflow_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise N8nExecutionError(f"Failed to get workflow: {str(e)}")

    async def execute_workflow(self, workflow_id: str,
                              input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow_id: ID of workflow to execute
            input_data: Optional input data for workflow

        Returns:
            Execution result with execution ID
        """
        payload = {}
        if input_data:
            payload["workflowData"] = input_data

        try:
            response = await self.client.post(
                f"/api/v1/workflows/{workflow_id}/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise N8nExecutionError(f"Failed to execute workflow: {error_detail}")
        except Exception as e:
            raise N8nExecutionError(f"Failed to execute workflow: {str(e)}")

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get execution status and results.

        Args:
            execution_id: Execution ID

        Returns:
            Execution details including status and data
        """
        try:
            response = await self.client.get(f"/api/v1/executions/{execution_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise N8nExecutionError(f"Failed to get execution status: {str(e)}")

    async def monitor_execution(self, execution_id: str,
                               timeout: int = 300,
                               poll_interval: int = 2) -> Dict[str, Any]:
        """
        Monitor execution until completion or timeout.

        Args:
            execution_id: Execution ID to monitor
            timeout: Maximum wait time in seconds
            poll_interval: How often to check status (seconds)

        Returns:
            Final execution status
        """
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < timeout:
            status = await self.get_execution_status(execution_id)

            # Check if finished
            if status.get("finished"):
                return {
                    "status": "completed" if not status.get("stoppedAt") else "stopped",
                    "success": status.get("finished") and not status.get("stoppedAt"),
                    "data": status.get("data"),
                    "error": status.get("error"),
                    "execution_time": status.get("executionTime")
                }

            # Check if failed
            if status.get("stoppedAt"):
                return {
                    "status": "failed",
                    "success": False,
                    "data": status.get("data"),
                    "error": status.get("error")
                }

            await asyncio.sleep(poll_interval)

        return {
            "status": "timeout",
            "success": False,
            "error": f"Execution timeout after {timeout} seconds"
        }

    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow.

        Args:
            workflow_id: Workflow ID to delete

        Returns:
            True if successful
        """
        try:
            response = await self.client.delete(f"/api/v1/workflows/{workflow_id}")
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to delete workflow: {e}")
            return False

    async def list_workflows(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all workflows.

        Args:
            limit: Maximum number of workflows to return

        Returns:
            List of workflow summaries
        """
        try:
            response = await self.client.get(
                "/api/v1/workflows",
                params={"limit": limit}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            print(f"Failed to list workflows: {e}")
            return []


# Example usage
async def main():
    """Test the n8n client"""
    async with N8nClient() as client:
        # Health check
        healthy = await client.health_check()
        print(f"n8n server healthy: {healthy}")

        if not healthy:
            print("Cannot connect to n8n server. Please check configuration.")
            return

        # Create a simple test workflow
        test_workflow = {
            "name": "Test Workflow",
            "nodes": [
                {
                    "parameters": {},
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [250, 300]
                }
            ],
            "connections": {},
            "settings": {}
        }

        # Validate
        validation = await client.validate_workflow(test_workflow)
        print(f"Validation: {validation}")

        # Create
        if validation["valid"]:
            created = await client.create_workflow(test_workflow)
            print(f"Created workflow: {created['id']}")

            # Execute
            execution = await client.execute_workflow(created['id'])
            print(f"Execution started: {execution}")

            # Monitor
            result = await client.monitor_execution(execution['data']['executionId'])
            print(f"Execution result: {result}")

            # Clean up
            await client.delete_workflow(created['id'])
            print("Workflow deleted")


if __name__ == "__main__":
    asyncio.run(main())
