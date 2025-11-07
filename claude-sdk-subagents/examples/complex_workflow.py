"""Complex workflow example with multiple agents."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import OrchestratorAgent


async def software_development_workflow():
    """Complete software development workflow."""
    print("=" * 60)
    print("Software Development Workflow Example")
    print("=" * 60)

    orchestrator = OrchestratorAgent()

    task = """
I need to implement a REST API feature for user notifications. Please:

1. Research best practices for notification systems
2. Plan the implementation with phases and tasks
3. Write Python code for the notification API endpoints
4. Analyze the code for potential issues
5. Write API documentation

The system should support:
- Email notifications
- Push notifications
- In-app notifications
- User preferences for notification types
"""

    print("\nExecuting complex workflow...")
    print("This will delegate to multiple specialized agents.\n")

    result = await orchestrator.execute(task)

    print(f"\nWorkflow Complete!")
    print(f"Success: {result.success}")
    print(f"Total Execution Time: {result.execution_time:.2f}s")
    print(f"Agents Involved: {len(result.sub_results)}")

    print(f"\n{'=' * 60}")
    print("Execution Trace")
    print("=" * 60)
    print(result.execution_trace)

    print(f"\n{'=' * 60}")
    print("Individual Agent Results")
    print("=" * 60)

    for i, sub_result in enumerate(result.sub_results, 1):
        print(f"\n[{i}] {sub_result.agent_name}")
        print(f"    Status: {'✓' if sub_result.success else '✗'}")
        print(f"    Time: {sub_result.execution_time:.2f}s")
        print(f"    Output Preview: {sub_result.content[:200]}...")

    print(f"\n{'=' * 60}")
    print("Final Synthesized Output")
    print("=" * 60)
    print(result.content)


async def content_creation_workflow():
    """Content creation workflow example."""
    print("\n" + "=" * 60)
    print("Content Creation Workflow Example")
    print("=" * 60)

    orchestrator = OrchestratorAgent()

    task = """
Create a technical blog post about microservices architecture:

1. Research current trends in microservices
2. Analyze pros and cons of microservices vs monolithic architecture
3. Write a 500-word blog post for developers
4. Include code examples in Python showing service communication

Target audience: Mid-level developers
Tone: Informative but accessible
"""

    print("\nCreating content with multiple agents...\n")

    result = await orchestrator.execute(task)

    print(f"\nContent Creation Complete!")
    print(f"Agents Used: {[r.agent_name for r in result.sub_results]}")
    print(f"Total Time: {result.execution_time:.2f}s")

    print(f"\n{'=' * 60}")
    print("Execution Flow")
    print("=" * 60)
    print(result.execution_trace)

    print(f"\n{'=' * 60}")
    print("Final Blog Post")
    print("=" * 60)
    print(result.content)


async def data_analysis_workflow():
    """Data analysis workflow example."""
    print("\n" + "=" * 60)
    print("Data Analysis Workflow Example")
    print("=" * 60)

    orchestrator = OrchestratorAgent()

    task = """
Analyze user engagement data:

1. Research best practices for engagement analysis
2. Analyze the following metrics:
   - Daily Active Users: [1200, 1350, 1100, 1400, 1500]
   - Session Duration (min): [15, 18, 12, 20, 22]
   - Feature Usage: Login (95%), Search (70%), Export (30%)

3. Write Python code to calculate key metrics (growth rate, averages, trends)
4. Write a summary report with findings and recommendations

Context: SaaS product with 5000 total users, launched 6 months ago
"""

    print("\nAnalyzing data with specialized agents...\n")

    result = await orchestrator.execute(task)

    print(f"\nAnalysis Complete!")
    print(f"Time: {result.execution_time:.2f}s")

    print(f"\n{'=' * 60}")
    print("Analysis Report")
    print("=" * 60)
    print(result.content)


async def main():
    """Run complex workflow examples."""
    print("Claude Agent SDK - Complex Workflow Examples\n")

    await software_development_workflow()
    await content_creation_workflow()
    await data_analysis_workflow()

    print("\n" + "=" * 60)
    print("All workflows completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    asyncio.run(main())
