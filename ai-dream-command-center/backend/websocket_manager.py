"""WebSocket manager for real-time communication."""

import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.client_info: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.client_info[websocket] = {
            "client_id": client_id or f"client_{id(websocket)}",
            "connected_at": datetime.utcnow(),
        }
        print(f"✓ Client connected: {self.client_info[websocket]['client_id']}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            client_info = self.client_info.get(websocket, {})
            print(f"✗ Client disconnected: {client_info.get('client_id', 'unknown')}")
            self.active_connections.remove(websocket)
            del self.client_info[websocket]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_agent_event(self, event: dict):
        """Broadcast an agent event to all clients."""
        await self.broadcast({"type": "agent_event", "data": event})

    async def broadcast_system_status(self, status: dict):
        """Broadcast system status update."""
        await self.broadcast({"type": "system_status", "data": status})

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global instance
manager = ConnectionManager()
