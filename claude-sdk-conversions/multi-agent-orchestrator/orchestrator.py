"""
Multi-Agent Orchestrator - Claude SDK Version

Converted from: mcp-agent-army
Framework: Claude Agent SDK

This orchestrator manages multiple specialized agents and delegates
tasks based on user requests. Uses parallel processing for efficiency.
"""

import asyncio
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.base_agent import BaseClaudeAgent, AgentConfig, parallel_queries

load_dotenv()

console = Console()


class SpecialistAgent:
    """A specialist agent with a specific domain expertise."""

    def __init__(self, name: str, system_prompt: str, description: str):
        self.name = name
        self.description = description

        config = AgentConfig(
            system_prompt=system_prompt,
            model="sonnet",  # Can use "haiku" for faster/cheaper responses
        )

        self.agent = BaseClaudeAgent(config)

    async def execute_task(self, task: str) -> str:
        """Execute a task and return the result."""
        console.print(f"  [cyan]→ {self.name}[/cyan] processing...")
        result = await self.agent.query(task)
        return result


class MultiAgentOrchestrator:
    """
    Orchestrates multiple specialized agents using Claude SDK.

    Similar to mcp-agent-army but leverages Claude's native capabilities
    for tool use and reasoning without requiring MCP servers.
    """

    def __init__(self):
        self.specialists: Dict[str, SpecialistAgent] = {}
        self._initialize_specialists()

        # Primary orchestrator agent
        orchestrator_prompt = self._build_orchestrator_prompt()

        config = AgentConfig(
            system_prompt=orchestrator_prompt,
            model="sonnet",
        )

        self.orchestrator = BaseClaudeAgent(config)

    def _initialize_specialists(self):
        """Initialize all specialist agents."""

        # 1. Web Research Specialist
        self.specialists["web_researcher"] = SpecialistAgent(
            name="Web Researcher",
            system_prompt="""You are a web research specialist.
            Analyze questions and provide structured research guidance.
            Focus on: search strategy, source evaluation, information synthesis.""",
            description="Expert at researching information and analyzing web content"
        )

        # 2. Code Analysis Specialist
        self.specialists["code_analyst"] = SpecialistAgent(
            name="Code Analyst",
            system_prompt="""You are a code analysis specialist.
            Analyze code, suggest improvements, find bugs, and explain implementations.
            Focus on: code quality, best practices, performance optimization.""",
            description="Expert at analyzing, reviewing, and improving code"
        )

        # 3. Document Processing Specialist
        self.specialists["doc_processor"] = SpecialistAgent(
            name="Document Processor",
            system_prompt="""You are a document processing specialist.
            Extract information, summarize documents, and structure content.
            Focus on: document analysis, information extraction, summarization.""",
            description="Expert at processing and analyzing documents"
        )

        # 4. Data Analysis Specialist
        self.specialists["data_analyst"] = SpecialistAgent(
            name="Data Analyst",
            system_prompt="""You are a data analysis specialist.
            Analyze data patterns, generate insights, and create visualizations.
            Focus on: statistical analysis, pattern recognition, data visualization.""",
            description="Expert at analyzing data and generating insights"
        )

        # 5. API Integration Specialist
        self.specialists["api_expert"] = SpecialistAgent(
            name="API Expert",
            system_prompt="""You are an API integration specialist.
            Design, implement, and debug API integrations.
            Focus on: REST APIs, authentication, error handling, best practices.""",
            description="Expert at working with APIs and integrations"
        )

        # 6. System Architecture Specialist
        self.specialists["architect"] = SpecialistAgent(
            name="System Architect",
            system_prompt="""You are a system architecture specialist.
            Design scalable systems, choose technologies, and plan implementations.
            Focus on: system design, scalability, technology selection.""",
            description="Expert at system architecture and design"
        )

    def _build_orchestrator_prompt(self) -> str:
        """Build the system prompt for the orchestrator."""

        specialists_info = "\n".join([
            f"  - **{name}**: {agent.description}"
            for name, agent in self.specialists.items()
        ])

        return f"""You are an intelligent task orchestrator managing specialized agents.

Available Specialists:
{specialists_info}

Your Role:
1. Analyze user requests to understand requirements
2. Determine which specialist(s) can best handle the task
3. Break down complex tasks into sub-tasks for specialists
4. Coordinate parallel execution when possible
5. Synthesize results into a comprehensive answer

Instructions:
- When you identify tasks for specialists, format them as:
  DELEGATE: <specialist_name> | <task_description>

- For parallel tasks, list multiple DELEGATE commands
- After delegation, wait for results and synthesize them
- Always explain your reasoning and coordination strategy

Example:
User: "Analyze this Python API code and suggest improvements"
You would output:
DELEGATE: code_analyst | Review the code for quality and bugs
DELEGATE: api_expert | Evaluate API design and best practices

Then synthesize the results into actionable recommendations.
"""

    def parse_delegations(self, orchestrator_response: str) -> List[tuple[str, str]]:
        """
        Parse delegation commands from orchestrator response.

        Returns:
            List of (specialist_name, task) tuples
        """
        delegations = []

        for line in orchestrator_response.split("\n"):
            if line.strip().startswith("DELEGATE:"):
                try:
                    content = line.split("DELEGATE:")[1]
                    parts = content.split("|", 1)

                    if len(parts) == 2:
                        specialist_name = parts[0].strip()
                        task = parts[1].strip()

                        if specialist_name in self.specialists:
                            delegations.append((specialist_name, task))

                except Exception as e:
                    console.print(f"[yellow]Warning: Could not parse delegation: {line}[/yellow]")

        return delegations

    async def execute_delegations(
        self,
        delegations: List[tuple[str, str]]
    ) -> Dict[str, str]:
        """
        Execute delegations in parallel.

        Args:
            delegations: List of (specialist_name, task) tuples

        Returns:
            Dictionary mapping specialist names to results
        """
        if not delegations:
            return {}

        console.print(f"\n[bold cyan]Executing {len(delegations)} specialist task(s) in parallel...[/bold cyan]")

        # Execute all tasks in parallel
        tasks = [
            self.specialists[name].execute_task(task)
            for name, task in delegations
        ]

        results = await asyncio.gather(*tasks)

        # Map results back to specialist names
        result_dict = {
            delegations[i][0]: results[i]
            for i in range(len(delegations))
        }

        return result_dict

    async def process_request(self, user_request: str) -> str:
        """
        Process a user request through the orchestration system.

        Args:
            user_request: The user's request

        Returns:
            The final orchestrated response
        """
        console.print("\n[bold magenta]Orchestrator:[/bold magenta] Analyzing request...")

        # Step 1: Get orchestration plan
        orchestration_response = await self.orchestrator.query(
            f"User Request: {user_request}\n\nAnalyze this request and delegate to appropriate specialists."
        )

        # Display orchestration plan
        console.print(Panel(
            Markdown(orchestration_response),
            title="[bold]Orchestration Plan[/bold]",
            border_style="magenta"
        ))

        # Step 2: Parse delegations
        delegations = self.parse_delegations(orchestration_response)

        if not delegations:
            console.print("\n[yellow]No specialist delegation needed. Providing direct answer.[/yellow]\n")
            return orchestration_response

        # Step 3: Execute delegations in parallel
        specialist_results = await self.execute_delegations(delegations)

        # Step 4: Format results for synthesis
        results_text = "\n\n".join([
            f"**{name} Result:**\n{result}"
            for name, result in specialist_results.items()
        ])

        console.print("\n[bold magenta]Orchestrator:[/bold magenta] Synthesizing results...")

        # Step 5: Synthesize final answer
        synthesis_prompt = f"""
Original User Request: {user_request}

Specialist Results:
{results_text}

Based on these specialist results, provide a comprehensive, synthesized answer to the user's request.
Integrate insights from all specialists coherently.
"""

        final_answer = await self.orchestrator.query(synthesis_prompt)

        return final_answer

    async def interactive_mode(self):
        """Run the orchestrator in interactive CLI mode."""
        console.print("\n[bold green]" + "=" * 70 + "[/bold green]")
        console.print("[bold green]Multi-Agent Orchestrator - Claude SDK[/bold green]")
        console.print("[bold green]" + "=" * 70 + "[/bold green]")

        console.print("\n[bold cyan]Available Specialists:[/bold cyan]")
        for name, agent in self.specialists.items():
            console.print(f"  • [cyan]{agent.name}[/cyan]: {agent.description}")

        console.print("\n[dim]Type your requests. Complex tasks will be delegated to specialists.[/dim]")
        console.print("[dim]Type 'exit' to quit.[/dim]\n")

        while True:
            try:
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ")

                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print("\n[bold green]Goodbye![/bold green]\n")
                    break

                if not user_input.strip():
                    continue

                # Process request
                answer = await self.process_request(user_input)

                # Display final answer
                console.print("\n[bold green]Final Answer:[/bold green]\n")
                console.print(Markdown(answer))

            except KeyboardInterrupt:
                console.print("\n\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
                continue
            except Exception as e:
                console.print(f"\n[bold red]Error:[/bold red] {e}\n")
                import traceback
                traceback.print_exc()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Agent Orchestrator")
    parser.add_argument(
        "request",
        nargs="*",
        help="Task request (if not provided, enters interactive mode)"
    )

    args = parser.parse_args()

    orchestrator = MultiAgentOrchestrator()

    if args.request:
        # Single request mode
        request_text = " ".join(args.request)
        console.print(f"\n[bold cyan]Processing:[/bold cyan] {request_text}\n")

        answer = await orchestrator.process_request(request_text)

        console.print("\n[bold green]Final Answer:[/bold green]\n")
        console.print(Markdown(answer))
        console.print()
    else:
        # Interactive mode
        await orchestrator.interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
