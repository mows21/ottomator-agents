"""
n8n Workflow Templates
======================

Templates and utilities for creating n8n AI agent workflows.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4
import json


@dataclass
class WorkflowNode:
    """A node in an n8n workflow."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    type: str = ""
    position: List[int] = field(default_factory=lambda: [0, 0])
    parameters: Dict[str, Any] = field(default_factory=dict)
    credentials: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        node = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "position": self.position,
            "parameters": self.parameters,
        }
        if self.credentials:
            node["credentials"] = self.credentials
        return node


@dataclass
class WorkflowConfig:
    """Configuration for an n8n workflow."""
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)

    # Agent configuration
    model: str = "gpt-4o-mini"
    system_prompt: str = "You are a helpful AI assistant."
    temperature: float = 0.7
    max_tokens: int = 4096

    # RAG configuration
    enable_rag: bool = False
    vector_store: str = "supabase"
    embedding_model: str = "text-embedding-3-small"

    # Webhook configuration
    enable_webhook: bool = True
    webhook_path: str = "/webhook"


class N8NWorkflow:
    """
    Builder for n8n AI agent workflows.

    Example:
        workflow = N8NWorkflow(WorkflowConfig(
            name="my-agent",
            system_prompt="You are an expert...",
        ))

        workflow.add_webhook_trigger()
        workflow.add_ai_agent()
        workflow.add_respond()

        json_output = workflow.to_json()
    """

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.nodes: List[WorkflowNode] = []
        self.connections: Dict[str, Any] = {}
        self._x_position = 0

    def _next_position(self) -> List[int]:
        """Get next node position."""
        pos = [self._x_position, 200]
        self._x_position += 300
        return pos

    def add_webhook_trigger(self, path: Optional[str] = None) -> "N8NWorkflow":
        """Add a webhook trigger node."""
        node = WorkflowNode(
            name="Webhook",
            type="n8n-nodes-base.webhook",
            position=self._next_position(),
            parameters={
                "path": path or self.config.webhook_path,
                "httpMethod": "POST",
                "responseMode": "responseNode",
            },
        )
        self.nodes.append(node)
        return self

    def add_ai_agent(
        self,
        name: str = "AI Agent",
        tools: Optional[List[str]] = None,
    ) -> "N8NWorkflow":
        """Add an AI agent node."""
        node = WorkflowNode(
            name=name,
            type="@n8n/n8n-nodes-langchain.agent",
            position=self._next_position(),
            parameters={
                "agent": "conversationalAgent",
                "text": "={{ $json.body.message }}",
                "options": {
                    "systemMessage": self.config.system_prompt,
                },
            },
        )
        self.nodes.append(node)
        return self

    def add_openai_chat(
        self,
        name: str = "OpenAI Chat",
    ) -> "N8NWorkflow":
        """Add an OpenAI chat model node."""
        node = WorkflowNode(
            name=name,
            type="@n8n/n8n-nodes-langchain.lmChatOpenAi",
            position=self._next_position(),
            parameters={
                "model": self.config.model,
                "options": {
                    "temperature": self.config.temperature,
                    "maxTokens": self.config.max_tokens,
                },
            },
            credentials={
                "openAiApi": {"id": "openai", "name": "OpenAI"},
            },
        )
        self.nodes.append(node)
        return self

    def add_claude_chat(
        self,
        name: str = "Claude Chat",
        model: str = "claude-sonnet-4-5-20250929",
    ) -> "N8NWorkflow":
        """Add a Claude chat model node."""
        node = WorkflowNode(
            name=name,
            type="@n8n/n8n-nodes-langchain.lmChatAnthropic",
            position=self._next_position(),
            parameters={
                "model": model,
                "options": {
                    "temperature": self.config.temperature,
                    "maxTokensToSample": self.config.max_tokens,
                },
            },
            credentials={
                "anthropicApi": {"id": "anthropic", "name": "Anthropic"},
            },
        )
        self.nodes.append(node)
        return self

    def add_vector_store_retriever(
        self,
        name: str = "Vector Store Retriever",
        top_k: int = 5,
    ) -> "N8NWorkflow":
        """Add a vector store retriever for RAG."""
        node = WorkflowNode(
            name=name,
            type="@n8n/n8n-nodes-langchain.retrieverVectorStore",
            position=self._next_position(),
            parameters={
                "topK": top_k,
            },
        )
        self.nodes.append(node)
        return self

    def add_supabase_vector_store(
        self,
        name: str = "Supabase Vector Store",
        table_name: str = "documents",
    ) -> "N8NWorkflow":
        """Add Supabase vector store."""
        node = WorkflowNode(
            name=name,
            type="@n8n/n8n-nodes-langchain.vectorStoreSupabase",
            position=self._next_position(),
            parameters={
                "tableName": table_name,
                "queryName": "match_documents",
            },
            credentials={
                "supabaseApi": {"id": "supabase", "name": "Supabase"},
            },
        )
        self.nodes.append(node)
        return self

    def add_embedding(
        self,
        name: str = "Embeddings",
        model: str = "text-embedding-3-small",
    ) -> "N8NWorkflow":
        """Add an embeddings node."""
        node = WorkflowNode(
            name=name,
            type="@n8n/n8n-nodes-langchain.embeddingsOpenAi",
            position=self._next_position(),
            parameters={
                "model": model,
            },
            credentials={
                "openAiApi": {"id": "openai", "name": "OpenAI"},
            },
        )
        self.nodes.append(node)
        return self

    def add_memory(
        self,
        name: str = "Memory",
        memory_type: str = "buffer",
        window_size: int = 10,
    ) -> "N8NWorkflow":
        """Add a memory node for conversation history."""
        node = WorkflowNode(
            name=name,
            type="@n8n/n8n-nodes-langchain.memoryBufferWindow",
            position=self._next_position(),
            parameters={
                "contextWindowLength": window_size,
                "sessionKey": "={{ $json.body.session_id }}",
            },
        )
        self.nodes.append(node)
        return self

    def add_tool(
        self,
        name: str,
        tool_type: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> "N8NWorkflow":
        """Add a tool node."""
        node = WorkflowNode(
            name=name,
            type=tool_type,
            position=self._next_position(),
            parameters=parameters or {},
        )
        self.nodes.append(node)
        return self

    def add_http_request_tool(
        self,
        name: str = "HTTP Request",
        url: str = "",
        method: str = "GET",
    ) -> "N8NWorkflow":
        """Add an HTTP request tool."""
        return self.add_tool(
            name=name,
            tool_type="@n8n/n8n-nodes-langchain.toolHttpRequest",
            parameters={
                "url": url,
                "method": method,
                "description": f"Make {method} request to {url}",
            },
        )

    def add_respond(
        self,
        name: str = "Respond to Webhook",
    ) -> "N8NWorkflow":
        """Add a respond to webhook node."""
        node = WorkflowNode(
            name=name,
            type="n8n-nodes-base.respondToWebhook",
            position=self._next_position(),
            parameters={
                "options": {
                    "responseCode": 200,
                },
                "respondWith": "json",
                "responseBody": "={{ { response: $json.output } }}",
            },
        )
        self.nodes.append(node)
        return self

    def _build_connections(self) -> Dict[str, Any]:
        """Build connections between nodes (sequential by default)."""
        connections = {}
        for i in range(len(self.nodes) - 1):
            current = self.nodes[i]
            next_node = self.nodes[i + 1]
            connections[current.name] = {
                "main": [[{"node": next_node.name, "type": "main", "index": 0}]]
            }
        return connections

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary format."""
        return {
            "name": self.config.name,
            "nodes": [node.to_dict() for node in self.nodes],
            "connections": self._build_connections(),
            "settings": {
                "executionOrder": "v1",
                **self.config.settings,
            },
            "meta": {
                "description": self.config.description,
                "tags": self.config.tags,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """Export workflow as JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str) -> None:
        """Save workflow to a JSON file."""
        with open(path, "w") as f:
            f.write(self.to_json())


def create_agent_workflow(
    name: str,
    system_prompt: str,
    model: str = "gpt-4o-mini",
    enable_rag: bool = False,
    enable_memory: bool = True,
) -> N8NWorkflow:
    """
    Create a standard AI agent workflow.

    Example:
        workflow = create_agent_workflow(
            name="my-agent",
            system_prompt="You are an expert...",
            enable_rag=True,
        )
        workflow.save("my-agent.json")
    """
    config = WorkflowConfig(
        name=name,
        system_prompt=system_prompt,
        model=model,
        enable_rag=enable_rag,
    )

    workflow = N8NWorkflow(config)

    # Webhook trigger
    workflow.add_webhook_trigger()

    # Memory if enabled
    if enable_memory:
        workflow.add_memory()

    # RAG components if enabled
    if enable_rag:
        workflow.add_embedding()
        workflow.add_supabase_vector_store()
        workflow.add_vector_store_retriever()

    # Chat model
    if "claude" in model.lower():
        workflow.add_claude_chat(model=model)
    else:
        workflow.add_openai_chat()

    # AI Agent
    workflow.add_ai_agent()

    # Response
    workflow.add_respond()

    return workflow


def create_rag_workflow(
    name: str,
    system_prompt: str,
    vector_store: str = "supabase",
    top_k: int = 5,
) -> N8NWorkflow:
    """Create a RAG-enabled workflow."""
    return create_agent_workflow(
        name=name,
        system_prompt=system_prompt,
        enable_rag=True,
        enable_memory=True,
    )


def create_mcp_workflow(
    name: str,
    system_prompt: str,
    mcp_servers: List[str],
) -> N8NWorkflow:
    """Create a workflow with MCP server integration."""
    config = WorkflowConfig(
        name=name,
        system_prompt=system_prompt,
    )

    workflow = N8NWorkflow(config)
    workflow.add_webhook_trigger()
    workflow.add_memory()
    workflow.add_openai_chat()

    # Add MCP-style tools
    for server in mcp_servers:
        workflow.add_tool(
            name=f"MCP: {server}",
            tool_type="@n8n/n8n-nodes-langchain.toolMcp",
            parameters={"server": server},
        )

    workflow.add_ai_agent()
    workflow.add_respond()

    return workflow
