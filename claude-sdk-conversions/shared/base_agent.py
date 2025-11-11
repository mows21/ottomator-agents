"""
Base agent utilities for Claude SDK conversions.

This module provides common patterns and utilities for building agents
with the Claude Agent SDK.
"""

from dataclasses import dataclass
from typing import Optional, Any, Dict, List, Callable
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, query
import asyncio
import json


@dataclass
class AgentConfig:
    """Configuration for Claude SDK agents."""
    system_prompt: str
    model: str = "sonnet"  # sonnet, opus, or haiku
    cwd: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    max_tokens: int = 4096
    temperature: float = 1.0


class BaseClaudeAgent:
    """
    Base class for Claude SDK agents.

    Provides common functionality like session management,
    streaming, and tool integration.
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.session_id: Optional[str] = None
        self.client: Optional[ClaudeSDKClient] = None

    def get_options(self, resume: bool = False) -> ClaudeAgentOptions:
        """Get Claude agent options from config."""
        options = ClaudeAgentOptions(
            system_prompt=self.config.system_prompt,
            cwd=self.config.cwd,
            allowed_tools=self.config.allowed_tools,
        )

        if resume and self.session_id:
            options.resume = self.session_id

        return options

    async def query(self, prompt: str) -> str:
        """
        Stateless query - for one-off questions.

        Args:
            prompt: The user's question or request

        Returns:
            The agent's response as a string
        """
        result = await query(prompt, options=self.get_options())
        return result

    async def start_session(self) -> ClaudeSDKClient:
        """
        Start a new stateful session.

        Returns:
            A ClaudeSDKClient for multi-turn conversation
        """
        self.client = ClaudeSDKClient()
        return self.client

    async def send_message(self, message: str) -> Dict[str, Any]:
        """
        Send a message in the current session.

        Args:
            message: The message to send

        Returns:
            Dictionary with response data and session info
        """
        if not self.client:
            await self.start_session()

        await self.client.send_message(message, options=self.get_options(resume=True))

        response_text = ""
        tool_uses = []

        async for msg in self.client.receive_messages():
            if hasattr(msg, 'text'):
                response_text += msg.text
            elif hasattr(msg, 'tool_use'):
                tool_uses.append(msg.tool_use)

        # Get the result message for session ID
        result = await self.client.receive_response()
        if result.session_id:
            self.session_id = result.session_id

        return {
            "response": response_text,
            "tool_uses": tool_uses,
            "session_id": self.session_id
        }

    async def stream_response(
        self,
        message: str,
        on_text: Optional[Callable[[str], None]] = None,
        on_tool: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Stream a response with optional callbacks.

        Args:
            message: The message to send
            on_text: Callback for text chunks
            on_tool: Callback for tool use

        Returns:
            Complete response text
        """
        if not self.client:
            await self.start_session()

        await self.client.send_message(message, options=self.get_options(resume=True))

        full_response = ""

        async for msg in self.client.receive_messages():
            if hasattr(msg, 'text'):
                full_response += msg.text
                if on_text:
                    on_text(msg.text)
            elif hasattr(msg, 'tool_use') and on_tool:
                on_tool(msg.tool_use)

        # Update session ID
        result = await self.client.receive_response()
        if result.session_id:
            self.session_id = result.session_id

        return full_response


class MultiAgentOrchestrator:
    """
    Orchestrates multiple specialized agents.

    Similar to mcp-agent-army pattern but using Claude SDK.
    """

    def __init__(self, primary_config: AgentConfig):
        self.primary_agent = BaseClaudeAgent(primary_config)
        self.subagents: Dict[str, BaseClaudeAgent] = {}

    def register_subagent(self, name: str, agent: BaseClaudeAgent):
        """Register a specialized subagent."""
        self.subagents[name] = agent

    async def delegate_task(self, subagent_name: str, task: str) -> str:
        """
        Delegate a task to a specialized subagent.

        Args:
            subagent_name: Name of the subagent to use
            task: The task to perform

        Returns:
            The subagent's response
        """
        if subagent_name not in self.subagents:
            return f"Error: Unknown subagent '{subagent_name}'"

        subagent = self.subagents[subagent_name]
        result = await subagent.query(task)
        return result

    async def parallel_delegate(
        self,
        tasks: List[tuple[str, str]]
    ) -> List[str]:
        """
        Delegate multiple tasks in parallel.

        Args:
            tasks: List of (subagent_name, task) tuples

        Returns:
            List of responses in order
        """
        coroutines = [
            self.delegate_task(name, task)
            for name, task in tasks
        ]
        results = await asyncio.gather(*coroutines)
        return results

    async def run(self, user_request: str) -> str:
        """
        Process a user request through the orchestrator.

        The primary agent decides which subagent(s) to use.

        Args:
            user_request: The user's request

        Returns:
            The orchestrated response
        """
        # Build a system prompt that includes subagent capabilities
        subagent_info = "\n".join([
            f"- {name}: {agent.config.system_prompt}"
            for name, agent in self.subagents.items()
        ])

        orchestration_prompt = f"""
You are an orchestration agent with access to specialized subagents:

{subagent_info}

Analyze the user's request and determine which subagent(s) to use.
You can call subagents by stating: "CALL_SUBAGENT: <name> | <task>"

User Request: {user_request}
"""

        response = await self.primary_agent.query(orchestration_prompt)

        # Simple parsing - in production, use proper tool calling
        if "CALL_SUBAGENT:" in response:
            lines = response.split("\n")
            for line in lines:
                if line.startswith("CALL_SUBAGENT:"):
                    parts = line.replace("CALL_SUBAGENT:", "").split("|")
                    if len(parts) == 2:
                        subagent_name = parts[0].strip()
                        task = parts[1].strip()
                        result = await self.delegate_task(subagent_name, task)
                        response += f"\n\n--- {subagent_name} Result ---\n{result}"

        return response


def create_simple_agent(system_prompt: str, **kwargs) -> BaseClaudeAgent:
    """
    Convenience function to create a simple agent.

    Args:
        system_prompt: The system prompt for the agent
        **kwargs: Additional config options

    Returns:
        A configured BaseClaudeAgent
    """
    config = AgentConfig(system_prompt=system_prompt, **kwargs)
    return BaseClaudeAgent(config)


async def parallel_queries(prompts: List[str], system_prompt: Optional[str] = None) -> List[str]:
    """
    Execute multiple queries in parallel.

    Args:
        prompts: List of prompts to execute
        system_prompt: Optional system prompt for all queries

    Returns:
        List of responses in order
    """
    options = None
    if system_prompt:
        options = ClaudeAgentOptions(system_prompt=system_prompt)

    tasks = [query(prompt, options=options) for prompt in prompts]
    results = await asyncio.gather(*tasks)
    return results
