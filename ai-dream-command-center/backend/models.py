"""Data models for AI Dream Command Center."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    USING_TOOL = "using_tool"
    COMPLETED = "completed"
    ERROR = "error"


class AgentType(str, Enum):
    """Types of agents available."""

    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"
    WEB_SEARCHER = "web_searcher"
    RAG_AGENT = "rag_agent"
    ORCHESTRATOR = "orchestrator"
    CUSTOM = "custom"


class ToolCall(BaseModel):
    """Represents a tool call by an agent."""

    tool_name: str
    arguments: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentEvent(BaseModel):
    """Real-time event emitted by agents."""

    event_type: Literal["status_change", "tool_call", "message", "result", "error"]
    agent_id: str
    agent_type: AgentType
    status: Optional[AgentStatus] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    """Current state of an agent."""

    agent_id: str
    agent_type: AgentType
    status: AgentStatus
    current_task: Optional[str] = None
    progress: float = 0.0  # 0-100
    tools_used: List[str] = []
    tokens_used: int = 0
    start_time: datetime = Field(default_factory=datetime.utcnow)
    last_update: datetime = Field(default_factory=datetime.utcnow)


class WorkflowStep(BaseModel):
    """A step in a workflow."""

    step_id: str
    agent_type: AgentType
    prompt: str
    tools: List[str] = []
    depends_on: List[str] = []  # Step IDs this depends on


class Workflow(BaseModel):
    """Defines a multi-agent workflow."""

    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    parallel_execution: bool = False


class TaskRequest(BaseModel):
    """Request to execute a task."""

    task_id: Optional[str] = None
    prompt: str
    agent_type: Optional[AgentType] = None
    workflow_id: Optional[str] = None
    tools: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


class TaskResult(BaseModel):
    """Result of task execution."""

    task_id: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    agents_used: List[str] = []
    total_tokens: int = 0
    execution_time: float = 0.0
    events: List[AgentEvent] = []


class AgentMetrics(BaseModel):
    """Metrics for monitoring."""

    agent_id: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_tokens: int = 0
    average_response_time: float = 0.0
    tools_usage: Dict[str, int] = {}


class SystemStatus(BaseModel):
    """Overall system status."""

    active_agents: int
    total_tasks: int
    tasks_in_progress: int
    tasks_completed: int
    uptime: float
    agents: List[AgentState] = []
