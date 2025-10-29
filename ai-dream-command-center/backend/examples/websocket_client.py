"""Example WebSocket client to watch agent activity in real-time."""

import asyncio
import websockets
import json
from datetime import datetime


async def watch_agents():
    """Connect to WebSocket and watch agent activity."""

    ws_url = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✓ Connected to AI Dream Command Center")
            print("Watching for agent activity...\n")

            # Receive messages
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                msg_type = data.get("type")
                timestamp = datetime.now().strftime("%H:%M:%S")

                if msg_type == "connection":
                    print(f"[{timestamp}] {data.get('message')}")

                elif msg_type == "agent_event":
                    event = data.get("data", {})
                    event_type = event.get("event_type")
                    agent_type = event.get("agent_type", "").upper()
                    message = event.get("message", "")

                    print(f"[{timestamp}] {agent_type} - {event_type}")
                    if message:
                        print(f"           {message}")

                elif msg_type == "system_status":
                    status = data.get("data", {})
                    print(f"\n[{timestamp}] System Status:")
                    print(f"  Active agents: {status.get('active_agents', 0)}")
                    print(f"  Total tasks: {status.get('total_tasks', 0)}")
                    print(f"  Completed: {status.get('tasks_completed', 0)}")
                    print()

    except websockets.exceptions.ConnectionClosed:
        print("\n✗ Connection closed")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    print("AI Dream Command Center - WebSocket Monitor\n")
    asyncio.run(watch_agents())
