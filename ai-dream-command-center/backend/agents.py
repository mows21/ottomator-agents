"""AI Agents using Pydantic AI."""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel

from models import AgentType, AgentStatus, AgentEvent
from tools import tool_registry
from config import settings


class DreamAgent:
    """Base class for AI Dream Command Center agents."""

    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        model_name: str = "claude-3-5-sonnet-20241022",
        use_openai: bool = False,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = AgentStatus.IDLE
        self.events: List[AgentEvent] = []
        self.tokens_used = 0

        # Initialize model
        if use_openai:
            self.model = OpenAIModel(
                model_name or "gpt-4o", api_key=settings.openai_api_key
            )
        else:
            self.model = AnthropicModel(
                model_name, api_key=settings.anthropic_api_key
            )

        # Create Pydantic AI agent
        self.agent = Agent(
            self.model,
            system_prompt=self._get_system_prompt(),
            retries=2,
        )

        # Register tools
        self._register_tools()

    def _get_system_prompt(self) -> str:
        """Get system prompt based on agent type."""
        prompts = {
            AgentType.RESEARCHER: "You are a research agent. Your job is to gather, analyze, and synthesize information from various sources. Be thorough and cite sources.",
            AgentType.CODER: "You are a coding agent. You write clean, efficient, well-documented code. You follow best practices and explain your solutions.",
            AgentType.ANALYST: "You are a data analyst. You analyze data, find patterns, and provide insights. Present findings clearly with statistics.",
            AgentType.WEB_SEARCHER: "You are a web search agent. You search for information online and provide relevant, up-to-date results.",
            AgentType.RAG_AGENT: "You are a RAG (Retrieval-Augmented Generation) agent. You retrieve relevant documents and generate accurate answers based on them.",
            AgentType.ORCHESTRATOR: "You are an orchestrator agent. You coordinate multiple sub-agents to accomplish complex tasks.",
        }
        return prompts.get(
            self.agent_type,
            "You are a helpful AI agent. Assist users with their tasks efficiently.",
        )

    def _register_tools(self):
        """Register tools with the agent."""
        # Register web search
        @self.agent.tool
        async def search_web(ctx: RunContext[None], query: str) -> str:
            """Search the web for information."""
            self._emit_event("tool_call", message=f"Searching web: {query}")
            result = await tool_registry.get_tool("web_search")(query)
            return str(result)

        # Register calculator
        @self.agent.tool
        async def calculate(ctx: RunContext[None], expression: str) -> str:
            """Calculate a mathematical expression."""
            self._emit_event("tool_call", message=f"Calculating: {expression}")
            result = await tool_registry.get_tool("calculate")(expression)
            return str(result)

        # Register time tool
        @self.agent.tool
        async def get_time(ctx: RunContext[None], timezone: str = "UTC") -> str:
            """Get current time."""
            self._emit_event("tool_call", message=f"Getting time for {timezone}")
            result = await tool_registry.get_tool("get_current_time")(timezone)
            return str(result)

    def _emit_event(
        self,
        event_type: str,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        status: Optional[AgentStatus] = None,
    ):
        """Emit an event."""
        if status:
            self.status = status

        event = AgentEvent(
            event_type=event_type,
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=self.status,
            message=message,
            data=data,
        )
        self.events.append(event)
        return event

    async def run(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Run the agent with a prompt."""
        self._emit_event("status_change", status=AgentStatus.THINKING)

        try:
            # Run the agent
            result = await self.agent.run(prompt)

            self._emit_event(
                "result",
                message="Task completed",
                data={"result": result.data},
                status=AgentStatus.COMPLETED,
            )

            # Track token usage if available
            if hasattr(result, "usage"):
                self.tokens_used += getattr(result.usage(), "total_tokens", 0)

            return str(result.data)

        except Exception as e:
            self._emit_event(
                "error",
                message=f"Error: {str(e)}",
                data={"error": str(e)},
                status=AgentStatus.ERROR,
            )
            raise

    def get_events(self) -> List[AgentEvent]:
        """Get all events from this agent."""
        return self.events

    def clear_events(self):
        """Clear event history."""
        self.events = []


class ResearchAgent(DreamAgent):
    """Specialized research agent."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.RESEARCHER)


class CoderAgent(DreamAgent):
    """Specialized coding agent."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.CODER)


class AnalystAgent(DreamAgent):
    """Specialized data analyst agent."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.ANALYST)


class WebSearchAgent(DreamAgent):
    """Specialized web search agent."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.WEB_SEARCHER)
