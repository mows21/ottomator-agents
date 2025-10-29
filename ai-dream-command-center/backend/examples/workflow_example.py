"""Example of creating and executing a workflow."""

import asyncio
import httpx


async def execute_workflow():
    """Execute a multi-step workflow."""

    api_url = "http://localhost:8000"

    # Define a workflow
    workflow_data = {
        "workflow_id": "research_and_code_example",
        "name": "Research and Code Example",
        "description": "Research a topic and write code based on findings",
        "parallel_execution": False,
        "steps": [
            {
                "step_id": "research",
                "agent_type": "researcher",
                "prompt": "Research best practices for Python async programming",
                "tools": ["web_search"],
                "depends_on": [],
            },
            {
                "step_id": "analyze",
                "agent_type": "analyst",
                "prompt": "Analyze the research findings and identify key patterns",
                "tools": [],
                "depends_on": ["research"],
            },
            {
                "step_id": "code",
                "agent_type": "coder",
                "prompt": "Write a Python async example based on the research",
                "tools": [],
                "depends_on": ["research", "analyze"],
            },
        ],
    }

    async with httpx.AsyncClient() as client:
        print("Executing workflow...")
        response = await client.post(
            f"{api_url}/workflows", json=workflow_data, timeout=120.0
        )

        if response.status_code == 200:
            result = response.json()
            print("\n✓ Workflow completed successfully!")
            print(f"\nTask ID: {result['task_id']}")
            print(f"Success: {result['success']}")
            print(f"Total tokens: {result['total_tokens']}")
            print(f"Execution time: {result['execution_time']:.2f}s")
            print(f"\nResult:\n{result['result']}")
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    print("AI Dream Command Center - Workflow Example\n")
    asyncio.run(execute_workflow())
