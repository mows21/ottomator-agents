"""Example: Create a project with AI-generated plan."""

import asyncio
import httpx


async def main():
    """Create a project and generate AI plan."""
    api_url = "http://localhost:8000"

    # Create project
    project_data = {
        "name": "E-commerce Platform",
        "description": """
Build a full-stack e-commerce platform with:
- Product catalog with search and filtering
- Shopping cart and checkout
- User authentication and profiles
- Payment integration (Stripe)
- Order management
- Admin dashboard

Tech stack:
- Frontend: React + TypeScript + Tailwind CSS
- Backend: FastAPI + PostgreSQL
- Deployment: Docker + AWS

Timeline: 12 weeks
        """.strip(),
        "auto_generate_plan": True,
    }

    async with httpx.AsyncClient() as client:
        print("Creating project...")
        response = await client.post(
            f"{api_url}/api/projects",
            json=project_data,
            timeout=60.0
        )

        if response.status_code == 200:
            project = response.json()
            project_id = project["id"]

            print(f"\n✓ Project created successfully!")
            print(f"  ID: {project_id}")
            print(f"  Name: {project['name']}")
            print(f"  Status: {project['status']}")

            # Generate detailed plan
            print(f"\nGenerating AI plan...")
            plan_response = await client.post(
                f"{api_url}/api/projects/{project_id}/generate-plan",
                timeout=120.0
            )

            if plan_response.status_code == 200:
                plan = plan_response.json()
                print(f"\n✓ Plan generated!")
                print(f"\nPlan details:")
                print(plan)

                # Get optimized schedule
                print(f"\nGenerating optimized schedule...")
                schedule_response = await client.get(
                    f"{api_url}/api/tasks/schedule",
                    params={"project_id": project_id},
                    timeout=60.0
                )

                if schedule_response.status_code == 200:
                    schedule = schedule_response.json()
                    print(f"\n✓ Schedule optimized!")
                    print(f"\nSchedule overview:")
                    print(f"  Total duration: {schedule.get('total_duration_days', 0)} days")
                    print(f"  Total tasks: {len(schedule.get('tasks', []))}")
                    print(f"  Critical path: {schedule.get('critical_path', [])}")

        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    print("Archon Motion AI - Project Creation Example\n")
    print("Make sure the backend is running: docker-compose up -d\n")

    asyncio.run(main())
