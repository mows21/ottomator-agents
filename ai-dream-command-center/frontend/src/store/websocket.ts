"use client";

import { create } from "zustand";
import {
  AgentState,
  AgentEvent,
  SystemStatus,
  WebSocketMessage,
} from "@/types";

interface WebSocketStore {
  // Connection state
  connected: boolean;
  connecting: boolean;
  error: string | null;

  // Data
  agents: AgentState[];
  events: AgentEvent[];
  systemStatus: SystemStatus | null;

  // WebSocket instance
  ws: WebSocket | null;

  // Actions
  connect: (url: string) => void;
  disconnect: () => void;
  sendMessage: (message: any) => void;
  clearEvents: () => void;
}

export const useWebSocketStore = create<WebSocketStore>((set, get) => ({
  // Initial state
  connected: false,
  connecting: false,
  error: null,
  agents: [],
  events: [],
  systemStatus: null,
  ws: null,

  // Connect to WebSocket
  connect: (url: string) => {
    const { ws, connected } = get();

    // Don't reconnect if already connected
    if (connected || ws) {
      console.log("Already connected or connecting");
      return;
    }

    set({ connecting: true, error: null });

    try {
      const socket = new WebSocket(url);

      socket.onopen = () => {
        console.log("✓ WebSocket connected");
        set({ connected: true, connecting: false, ws: socket });
      };

      socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          switch (message.type) {
            case "connection":
              console.log("Connection message:", message.message);
              break;

            case "agent_event":
              // Add new event
              const agentEvent = message.data as AgentEvent;
              set((state) => ({
                events: [agentEvent, ...state.events].slice(0, 100), // Keep last 100
              }));
              break;

            case "system_status":
              // Update system status
              const status = message.data as SystemStatus;
              set({
                systemStatus: status,
                agents: status.agents || [],
              });
              break;

            case "pong":
              // Heartbeat response
              break;

            default:
              console.log("Unknown message type:", message.type);
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        set({ error: "WebSocket connection error", connecting: false });
      };

      socket.onclose = () => {
        console.log("✗ WebSocket disconnected");
        set({ connected: false, ws: null, connecting: false });

        // Auto-reconnect after 3 seconds
        setTimeout(() => {
          const { connected } = get();
          if (!connected) {
            console.log("Attempting to reconnect...");
            get().connect(url);
          }
        }, 3000);
      };
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      set({ error: "Failed to create WebSocket connection", connecting: false });
    }
  },

  // Disconnect from WebSocket
  disconnect: () => {
    const { ws } = get();
    if (ws) {
      ws.close();
      set({ ws: null, connected: false });
    }
  },

  // Send message to server
  sendMessage: (message: any) => {
    const { ws, connected } = get();
    if (ws && connected) {
      ws.send(JSON.stringify(message));
    } else {
      console.error("Cannot send message: not connected");
    }
  },

  // Clear events
  clearEvents: () => {
    set({ events: [] });
  },
}));
