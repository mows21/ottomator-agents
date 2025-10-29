"""Base agent class and common utilities."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel

from app.core.config import settings


class AgentContext(BaseModel):
    """Context passed to agents."""
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AgentResult(BaseModel):
    """Result from agent execution."""
    success: bool
    data: Any
    message: Optional[str] = None
    error: Optional[str] = None
    tokens_used: int = 0
    execution_time: float = 0.0
    timestamp: datetime = datetime.utcnow()


class BaseAgent:
    """Base class for all AI agents."""

    def __init__(
        self,
        name: str,
        description: str,
        model_name: str = None,
        system_prompt: str = None
    ):
        self.name = name
        self.description = description
        self.model_name = model_name or settings.default_model

        # Initialize Pydantic AI agent
        self.model = AnthropicModel(
            self.model_name,
            api_key=settings.anthropic_api_key
        )

        self.agent = Agent(
            self.model,
            system_prompt=system_prompt or self._get_default_prompt(),
            retries=2
        )

    def _get_default_prompt(self) -> str:
        """Get default system prompt for this agent."""
        return f"""You are {self.name}, an AI assistant specialized in {self.description}.

Be concise, accurate, and helpful. Always structure your responses in a clear format.
When making recommendations, explain your reasoning."""

    async def run(
        self,
        prompt: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """
        Execute the agent with given prompt and context.

        Args:
            prompt: The task or question for the agent
            context: Additional context for the agent

        Returns:
            AgentResult with the execution result
        """
        start_time = datetime.utcnow()

        try:
            # Prepare context
            ctx = context or AgentContext()

            # Run agent
            result = await self.agent.run(prompt)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Get token usage
            tokens_used = 0
            if hasattr(result, "usage"):
                usage = result.usage()
                tokens_used = getattr(usage, "total_tokens", 0)

            return AgentResult(
                success=True,
                data=result.data,
                tokens_used=tokens_used,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=execution_time
            )
