"""
Web Research Agent - Claude SDK Version

Converted from: pydantic-ai-advanced-researcher
Framework: Claude Agent SDK

This agent performs advanced web research using Brave Search API
and leverages Claude's reasoning to synthesize information.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.base_agent import BaseClaudeAgent, AgentConfig

load_dotenv()

console = Console()


class WebResearchAgent:
    """
    Advanced web research agent using Claude SDK.

    Features:
    - Brave Search integration
    - Multi-query research
    - Source synthesis
    - Interactive CLI
    """

    def __init__(self, brave_api_key: Optional[str] = None):
        self.brave_api_key = brave_api_key or os.getenv('BRAVE_API_KEY')

        system_prompt = f"""You are an expert web researcher with access to current information.

Current date: {datetime.now().strftime("%Y-%m-%d")}

Your capabilities:
1. Search the web for current information
2. Analyze multiple sources
3. Synthesize comprehensive answers
4. Cite sources accurately

When researching:
- Use multiple search queries to get comprehensive coverage
- Evaluate source credibility
- Provide balanced, well-sourced answers
- Always cite your sources with URLs

To search the web, simply ask me to search for specific information.
I have access to web search through Brave Search API.
"""

        config = AgentConfig(
            system_prompt=system_prompt,
            model="sonnet",
        )

        self.agent = BaseClaudeAgent(config)
        self.httpx_client: Optional[httpx.AsyncClient] = None

    async def search_brave(self, query: str) -> Dict[str, Any]:
        """
        Search using Brave Search API.

        Args:
            query: Search query

        Returns:
            Dictionary with search results
        """
        if not self.brave_api_key:
            return {
                "error": "No Brave API key provided",
                "results": []
            }

        if not self.httpx_client:
            self.httpx_client = httpx.AsyncClient()

        try:
            headers = {
                'X-Subscription-Token': self.brave_api_key,
                'Accept': 'application/json',
            }

            response = await self.httpx_client.get(
                'https://api.search.brave.com/res/v1/web/search',
                params={
                    'q': query,
                    'count': 5,
                    'text_decorations': True,
                    'search_lang': 'en'
                },
                headers=headers
            )

            response.raise_for_status()
            data = response.json()

            # Format results
            results = []
            web_results = data.get('web', {}).get('results', [])

            for item in web_results[:5]:
                results.append({
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'url': item.get('url', ''),
                })

            return {
                "results": results,
                "query": query
            }

        except Exception as e:
            return {
                "error": str(e),
                "results": []
            }

    def format_search_results(self, search_data: Dict[str, Any]) -> str:
        """Format search results for Claude."""
        if "error" in search_data:
            return f"Search Error: {search_data['error']}"

        results = search_data.get("results", [])
        if not results:
            return "No results found."

        formatted = f"Search results for: {search_data.get('query', 'N/A')}\n\n"

        for i, result in enumerate(results, 1):
            formatted += f"{i}. **{result['title']}**\n"
            formatted += f"   {result['description']}\n"
            formatted += f"   Source: {result['url']}\n\n"

        return formatted

    async def research_with_context(self, user_query: str, max_searches: int = 3) -> str:
        """
        Research a topic with automatic web search integration.

        Args:
            user_query: The user's research question
            max_searches: Maximum number of web searches to perform

        Returns:
            Comprehensive research answer
        """
        # Initial query to understand what needs to be searched
        planning_prompt = f"""
User Question: {user_query}

To answer this question comprehensively:
1. What search queries would be most helpful? List 1-{max_searches} specific queries.
2. Format as: SEARCH_QUERY: <your query here>

Then, I'll provide you with the search results to synthesize an answer.
"""

        planning_response = await self.agent.query(planning_prompt)

        # Extract search queries
        search_queries = []
        for line in planning_response.split("\n"):
            if "SEARCH_QUERY:" in line:
                query = line.split("SEARCH_QUERY:")[1].strip()
                search_queries.append(query)

        if not search_queries:
            # Fallback: use the original query
            search_queries = [user_query]

        # Perform searches
        console.print(f"\n[bold cyan]Performing {len(search_queries)} web searches...[/bold cyan]")

        search_results_text = ""
        for i, query in enumerate(search_queries[:max_searches], 1):
            console.print(f"  {i}. Searching: [italic]{query}[/italic]")
            search_data = await self.search_brave(query)
            search_results_text += f"\n\n--- Search {i}: {query} ---\n"
            search_results_text += self.format_search_results(search_data)

        # Synthesize answer with search results
        synthesis_prompt = f"""
User Question: {user_query}

Web Search Results:
{search_results_text}

Based on these search results, provide a comprehensive answer to the user's question.

Requirements:
- Synthesize information from multiple sources
- Cite sources with [Source: URL] notation
- Provide a balanced, well-reasoned answer
- If conflicting information exists, note it
- Be clear about confidence level
"""

        console.print("\n[bold cyan]Synthesizing answer...[/bold cyan]\n")

        final_answer = await self.agent.query(synthesis_prompt)
        return final_answer

    async def interactive_mode(self):
        """Run the agent in interactive CLI mode."""
        console.print("\n[bold green]" + "=" * 70 + "[/bold green]")
        console.print("[bold green]Web Research Agent - Claude SDK Version[/bold green]")
        console.print("[bold green]" + "=" * 70 + "[/bold green]")
        console.print("\nType your research questions. Type 'exit' to quit.\n")

        await self.agent.start_session()

        while True:
            try:
                # Get user input
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ")

                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print("\n[bold green]Goodbye![/bold green]\n")
                    break

                if not user_input.strip():
                    continue

                # Research the query
                console.print()
                answer = await self.research_with_context(user_input)

                # Display answer
                console.print("\n[bold magenta]Assistant:[/bold magenta]\n")
                console.print(Markdown(answer))

            except KeyboardInterrupt:
                console.print("\n\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
                continue
            except Exception as e:
                console.print(f"\n[bold red]Error:[/bold red] {e}\n")

    async def cleanup(self):
        """Cleanup resources."""
        if self.httpx_client:
            await self.httpx_client.aclose()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Web Research Agent")
    parser.add_argument(
        "query",
        nargs="*",
        help="Research query (if not provided, enters interactive mode)"
    )
    parser.add_argument(
        "--brave-api-key",
        help="Brave Search API key (or set BRAVE_API_KEY env var)"
    )

    args = parser.parse_args()

    agent = WebResearchAgent(brave_api_key=args.brave_api_key)

    try:
        if args.query:
            # Single query mode
            query_text = " ".join(args.query)
            console.print(f"\n[bold cyan]Researching:[/bold cyan] {query_text}\n")

            answer = await agent.research_with_context(query_text)

            console.print("\n[bold magenta]Answer:[/bold magenta]\n")
            console.print(Markdown(answer))
            console.print()
        else:
            # Interactive mode
            await agent.interactive_mode()

    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
