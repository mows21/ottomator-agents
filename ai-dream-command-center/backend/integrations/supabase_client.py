"""Supabase integration for AI Dream Command Center."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import create_client, Client

from config import settings
from models import TaskResult, AgentEvent


class SupabaseManager:
    """Manages Supabase database operations."""

    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize()

    def _initialize(self):
        """Initialize Supabase client."""
        if settings.supabase_url and settings.supabase_key:
            try:
                self.client = create_client(
                    settings.supabase_url, settings.supabase_key
                )
                print("✓ Supabase client initialized")
            except Exception as e:
                print(f"✗ Failed to initialize Supabase: {e}")
                self.client = None
        else:
            print("⚠ Supabase credentials not configured")

    async def save_task(self, task_result: TaskResult) -> bool:
        """Save task result to database."""
        if not self.client:
            return False

        try:
            data = {
                "task_id": task_result.task_id,
                "prompt": "",  # Would need to pass from request
                "status": "completed" if task_result.success else "failed",
                "result": task_result.result,
                "error": task_result.error,
                "total_tokens": task_result.total_tokens,
                "execution_time": task_result.execution_time,
            }

            self.client.table("tasks").insert(data).execute()
            return True
        except Exception as e:
            print(f"Error saving task to Supabase: {e}")
            return False

    async def save_event(self, event: AgentEvent, task_id: Optional[str] = None) -> bool:
        """Save agent event to database."""
        if not self.client:
            return False

        try:
            data = {
                "event_type": event.event_type,
                "agent_id": event.agent_id,
                "agent_type": event.agent_type.value,
                "task_id": task_id,
                "message": event.message,
                "data": event.data,
            }

            self.client.table("events").insert(data).execute()
            return True
        except Exception as e:
            print(f"Error saving event to Supabase: {e}")
            return False

    async def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent task history."""
        if not self.client:
            return []

        try:
            response = (
                self.client.table("tasks")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"Error fetching task history: {e}")
            return []

    async def search_documents(
        self, query_embedding: List[float], threshold: float = 0.7, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search documents using vector similarity."""
        if not self.client:
            return []

        try:
            response = self.client.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": threshold,
                    "match_count": limit,
                },
            ).execute()

            return response.data
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []

    async def save_document(
        self, content: str, embedding: List[float], metadata: Optional[Dict] = None
    ) -> bool:
        """Save a document with embedding."""
        if not self.client:
            return False

        try:
            data = {"content": content, "embedding": embedding, "metadata": metadata or {}}

            self.client.table("documents").insert(data).execute()
            return True
        except Exception as e:
            print(f"Error saving document: {e}")
            return False


# Global instance
supabase_manager = SupabaseManager()
