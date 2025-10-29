"""Chat API for natural language project management."""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.orchestrator import orchestrator, AgentContext


router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message request."""
    message: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Chat response."""
    message: str
    action_taken: Optional[str] = None
    data: Optional[dict] = None


@router.post("/", response_model=ChatResponse)
async def chat(chat_msg: ChatMessage):
    """
    Natural language interface for project management.

    Examples:
    - "Create a project to build a mobile app"
    - "Show me my tasks for this week"
    - "What's blocking the authentication feature?"
    - "Schedule the remaining backend tasks"
    """
    message = chat_msg.message.lower()
    context = AgentContext(**(chat_msg.context or {}))

    # Detect intent and route to appropriate handler
    if any(word in message for word in ["create project", "new project"]):
        # Extract project description (simplified)
        return ChatResponse(
            message="I'll create a new project for you. Use the /api/agents/workflow endpoint with the planning agent for full project generation.",
            action_taken="project_creation_suggested"
        )

    elif any(word in message for word in ["my tasks", "show tasks", "what tasks"]):
        return ChatResponse(
            message="To see your tasks, use GET /api/tasks with your user_id filter.",
            action_taken="task_list_suggested"
        )

    elif any(word in message for word in ["schedule", "when", "timeline"]):
        return ChatResponse(
            message="Use GET /api/tasks/schedule to get an AI-optimized schedule.",
            action_taken="schedule_suggested"
        )

    elif any(word in message for word in ["help", "what can you do"]):
        return ChatResponse(
            message="""I can help you with:

- Creating projects with AI-generated plans
- Scheduling and prioritizing tasks
- Analyzing project timelines
- Identifying blockers and risks
- Breaking down features into tasks

Try asking:
- "Create a project to build [description]"
- "Show me the schedule for [project]"
- "What's blocking [task/project]?"
- "Break down [feature] into tasks"
""",
            action_taken="help"
        )

    else:
        # Use orchestrator to handle general queries
        try:
            results = await orchestrator.execute_workflow(
                task=chat_msg.message,
                context=context
            )

            return ChatResponse(
                message="Executed workflow with available agents",
                data=results
            )
        except Exception as e:
            return ChatResponse(
                message=f"I'm not sure how to help with that. Error: {str(e)}",
                action_taken="error"
            )
