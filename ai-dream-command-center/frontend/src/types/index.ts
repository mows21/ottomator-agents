// Type definitions for AI Dream Command Center

export enum AgentStatus {
  IDLE = "idle",
  THINKING = "thinking",
  WORKING = "working",
  USING_TOOL = "using_tool",
  COMPLETED = "completed",
  ERROR = "error",
}

export enum AgentType {
  RESEARCHER = "researcher",
  CODER = "coder",
  ANALYST = "analyst",
  WEB_SEARCHER = "web_searcher",
  RAG_AGENT = "rag_agent",
  ORCHESTRATOR = "orchestrator",
  CUSTOM = "custom",
}

export interface AgentState {
  agent_id: string;
  agent_type: AgentType;
  status: AgentStatus;
  current_task?: string;
  progress: number;
  tools_used: string[];
  tokens_used: number;
  start_time: string;
  last_update: string;
}

export interface AgentEvent {
  event_type: "status_change" | "tool_call" | "message" | "result" | "error";
  agent_id: string;
  agent_type: AgentType;
  status?: AgentStatus;
  message?: string;
  data?: any;
  timestamp: string;
}

export interface TaskRequest {
  task_id?: string;
  prompt: string;
  agent_type?: AgentType;
  workflow_id?: string;
  tools?: string[];
  context?: Record<string, any>;
}

export interface TaskResult {
  task_id: string;
  success: boolean;
  result?: string;
  error?: string;
  agents_used: string[];
  total_tokens: number;
  execution_time: number;
  events: AgentEvent[];
}

export interface SystemStatus {
  active_agents: number;
  total_tasks: number;
  tasks_in_progress: number;
  tasks_completed: number;
  uptime: number;
  agents: AgentState[];
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  message?: string;
  timestamp?: string;
}
