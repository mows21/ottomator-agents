"""Basic example of orchestrator delegating to sub-agents."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import OrchestratorAgent


async def example_1_single_agent():
    """Example 1: Simple delegation to single agent."""
    print("=" * 60)
    print("Example 1: Single Agent Delegation")
    print("=" * 60)

    orchestrator = OrchestratorAgent()

    # Research task
    result = await orchestrator.execute(
        "Research the benefits of using async programming in Python"
    )

    print(f"\nSuccess: {result.success}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    print(f"\nDelegation Log:")
    print(result.execution_trace)
    print(f"\nResult:")
    print(result.content)


async def example_2_multi_agent():
    """Example 2: Task requiring multiple agents."""
    print("\n" + "=" * 60)
    print("Example 2: Multi-Agent Workflow")
    print("=" * 60)

    orchestrator = OrchestratorAgent()

    # Complex task needing research + code
    result = await orchestrator.execute("""
Research Python async best practices, then write example code demonstrating
async/await with proper error handling.
""")

    print(f"\nSuccess: {result.success}")
    print(f"Agents Used: {len(result.sub_results)}")
    print(f"Execution Time: {result.execution_time:.2f}s")

    print(f"\nDelegation Log:")
    print(result.execution_trace)

    print(f"\nSub-Agent Results:")
    for sub_result in result.sub_results:
        print(f"\n[{sub_result.agent_name}]")
        print(f"Status: {'Success' if sub_result.success else 'Failed'}")
        print(f"Time: {sub_result.execution_time:.2f}s")

    print(f"\nFinal Synthesized Result:")
    print(result.content)


async def example_3_context_sharing():
    """Example 3: Sharing context across agents."""
    print("\n" + "=" * 60)
    print("Example 3: Context Sharing")
    print("=" * 60)

    orchestrator = OrchestratorAgent()

    # Task with shared context
    context = {
        "project": "E-commerce Platform",
        "language": "Python",
        "framework": "FastAPI",
        "timeline": "3 months"
    }

    result = await orchestrator.execute(
        "Plan the authentication system implementation and write sample code",
        context=context
    )

    print(f"\nContext: {context}")
    print(f"\nSuccess: {result.success}")
    print(f"Agents Used: {len(result.sub_results)}")

    print(f"\nDelegation Log:")
    print(result.execution_trace)

    print(f"\nResult:")
    print(result.content)


async def example_4_list_agents():
    """Example 4: List available agents."""
    print("\n" + "=" * 60)
    print("Example 4: Available Agents")
    print("=" * 60)

    orchestrator = OrchestratorAgent()

    agents = orchestrator.list_agents()

    print("\nAvailable Sub-Agents:")
    for name, description in agents.items():
        print(f"\n{name.upper()}")
        print(f"  {description}")


async def main():
    """Run all examples."""
    print("Claude Agent SDK - Sub-Agents Examples")
    print("=" * 60)

    # Run examples
    await example_1_single_agent()
    await example_2_multi_agent()
    await example_3_context_sharing()
    await example_4_list_agents()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    asyncio.run(main())
