"""
n8n Workflow Platform
=====================

Integration with n8n for no-code/low-code AI agent workflows.

Features:
- Workflow templates for common patterns
- API integration for workflow execution
- Webhook handling
- Custom node templates

This platform provides tooling for n8n workflow agents.
"""

from platforms.n8n.workflows import (
    N8NWorkflow,
    WorkflowConfig,
    WorkflowNode,
    create_agent_workflow,
)
from platforms.n8n.api import N8NClient, WorkflowExecution

__all__ = [
    "N8NWorkflow",
    "WorkflowConfig",
    "WorkflowNode",
    "create_agent_workflow",
    "N8NClient",
    "WorkflowExecution",
]
