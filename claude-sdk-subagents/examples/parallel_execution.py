"""Parallel execution example."""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import OrchestratorAgent


async def compare_sequential_vs_parallel():
    """Compare sequential vs parallel execution."""
    print("=" * 60)
    print("Sequential vs Parallel Execution Comparison")
    print("=" * 60)

    orchestrator = OrchestratorAgent()

    # Independent tasks that can run in parallel
    task = """
Please complete these independent tasks:
1. Research Python async programming best practices
2. Analyze the pros and cons of microservices architecture
3. Write a Python function for making HTTP requests
"""

    # Sequential execution
    print("\n[1] Running SEQUENTIALLY...")
    start_time = time.time()
    sequential_result = await orchestrator.execute(task, mode="sequential")
    sequential_time = time.time() - start_time

    print(f"Sequential Time: {sequential_time:.2f}s")
    print(f"Agents: {[r.agent_name for r in sequential_result.sub_results]}")

    # Parallel execution
    print("\n[2] Running IN PARALLEL...")
    start_time = time.time()
    parallel_result = await orchestrator.execute(task, mode="parallel")
    parallel_time = time.time() - start_time

    print(f"Parallel Time: {parallel_time:.2f}s")
    print(f"Agents: {[r.agent_name for r in parallel_result.sub_results]}")

    # Compare
    print(f"\n{'=' * 60}")
    print("Comparison")
    print("=" * 60)
    print(f"Sequential Time: {sequential_time:.2f}s")
    print(f"Parallel Time:   {parallel_time:.2f}s")
    print(f"Speedup:         {sequential_time / parallel_time:.2f}x")

    print(f"\n{'=' * 60}")
    print("Parallel Result")
    print("=" * 60)
    print(parallel_result.content)


async def parallel_research_tasks():
    """Multiple research tasks in parallel."""
    print("\n" + "=" * 60)
    print("Parallel Research Example")
    print("=" * 60)

    orchestrator = OrchestratorAgent()

    task = """
Research the following topics independently:
1. Latest trends in AI and machine learning
2. Best practices for API design
3. Modern frontend frameworks comparison
"""

    print("\nExecuting multiple research tasks in parallel...\n")

    result = await orchestrator.execute(task, mode="parallel")

    print(f"Execution Time: {result.execution_time:.2f}s")
    print(f"Agents Used: {len(result.sub_results)}")

    print(f"\nExecution Log:")
    print(result.execution_trace)

    print(f"\nCombined Research Results:")
    print(result.content)


async def main():
    """Run parallel execution examples."""
    print("Claude Agent SDK - Parallel Execution Examples\n")

    await compare_sequential_vs_parallel()
    await parallel_research_tasks()

    print("\n" + "=" * 60)
    print("Parallel execution examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    asyncio.run(main())
