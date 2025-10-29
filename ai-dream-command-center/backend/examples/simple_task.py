"""Simple example of creating a task via API."""

import asyncio
import httpx


async def create_task():
    """Create a simple task and get the result."""

    api_url = "http://localhost:8000"

    # Task request
    task_data = {
        "prompt": "Write a Python function to calculate the factorial of a number",
        "agent_type": "coder",
    }

    async with httpx.AsyncClient() as client:
        print("Creating task...")
        response = await client.post(f"{api_url}/tasks", json=task_data, timeout=60.0)

        if response.status_code == 200:
            result = response.json()
            print("\n✓ Task completed successfully!")
            print(f"\nTask ID: {result['task_id']}")
            print(f"Success: {result['success']}")
            print(f"Agents used: {result['agents_used']}")
            print(f"Tokens used: {result['total_tokens']}")
            print(f"Execution time: {result['execution_time']:.2f}s")
            print(f"\nResult:\n{result['result']}")
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    print("AI Dream Command Center - Simple Task Example\n")
    asyncio.run(create_task())
