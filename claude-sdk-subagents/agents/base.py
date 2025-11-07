"""Base agent class for sub-agents."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from claude_agent_sdk import ClaudeSDKClient, query as claude_query


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    content: str
    agent_name: str
    execution_time: float
    tokens_used: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseSubAgent:
    """Base class for all sub-agents."""

    def __init__(
        self,
        name: str,
        description: str,
        capabilities: List[str],
        model: str = "claude-3-5-sonnet-20241022"
    ):
        """
        Initialize base sub-agent.

        Args:
            name: Agent name
            description: What this agent does
            capabilities: List of capabilities/keywords
            model: Claude model to use
        """
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.model = model
        self.client = ClaudeSDKClient(model=model)

    def can_handle(self, task: str) -> float:
        """
        Determine if this agent can handle the task.

        Args:
            task: Task description

        Returns:
            Confidence score (0-1)
        """
        task_lower = task.lower()
        score = 0.0

        for capability in self.capabilities:
            if capability.lower() in task_lower:
                score += 0.3

        return min(score, 1.0)

    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Execute a task.

        Args:
            task: Task description
            context: Additional context

        Returns:
            AgentResult with execution details
        """
        start_time = datetime.utcnow()

        try:
            # Build prompt with context
            prompt = self._build_prompt(task, context)

            # Execute using Claude SDK
            result = await self._execute_with_sdk(prompt)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return AgentResult(
                success=True,
                content=result["content"],
                agent_name=self.name,
                execution_time=execution_time,
                tokens_used=result.get("tokens_used", 0),
                metadata=result.get("metadata", {})
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return AgentResult(
                success=False,
                content=f"Error: {str(e)}",
                agent_name=self.name,
                execution_time=execution_time,
                metadata={"error": str(e)}
            )

    def _build_prompt(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build prompt for Claude.

        Args:
            task: Task description
            context: Additional context

        Returns:
            Formatted prompt
        """
        prompt = f"{self._get_system_prompt()}\n\n"

        if context:
            prompt += "Context:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"
            prompt += "\n"

        prompt += f"Task: {task}"

        return prompt

    def _get_system_prompt(self) -> str:
        """
        Get system prompt for this agent.

        Returns:
            System prompt string
        """
        return f"""You are {self.name}, a specialized AI assistant.

Your role: {self.description}

Your capabilities: {', '.join(self.capabilities)}

Provide clear, concise, and accurate responses focused on your specialty.
If a task is outside your expertise, clearly state that."""

    async def _execute_with_sdk(self, prompt: str) -> Dict[str, Any]:
        """
        Execute using Claude SDK.

        Args:
            prompt: Prompt to execute

        Returns:
            Result dictionary
        """
        # Using stateless query
        result = await claude_query(prompt, model=self.model)

        return {
            "content": result,
            "tokens_used": 0,  # SDK doesn't expose this currently
            "metadata": {}
        }

    def __repr__(self) -> str:
        return f"<{self.name}: {', '.join(self.capabilities)}>"
