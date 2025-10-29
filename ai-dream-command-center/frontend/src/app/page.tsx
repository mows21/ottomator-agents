"use client";

import { useEffect } from "react";
import { useWebSocketStore } from "@/store/websocket";
import { StatusBar } from "@/components/StatusBar";
import { AgentVisualizer } from "@/components/AgentVisualizer";
import { ActivityFeed } from "@/components/ActivityFeed";
import { TaskCreator } from "@/components/TaskCreator";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export default function Home() {
  const connect = useWebSocketStore((state) => state.connect);
  const connected = useWebSocketStore((state) => state.connected);

  useEffect(() => {
    // Connect to WebSocket on mount
    if (!connected) {
      connect(WS_URL);
    }

    // Heartbeat to keep connection alive
    const heartbeat = setInterval(() => {
      const { connected, sendMessage } = useWebSocketStore.getState();
      if (connected) {
        sendMessage({ type: "ping" });
      }
    }, 30000); // Every 30 seconds

    return () => {
      clearInterval(heartbeat);
    };
  }, [connect, connected]);

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Status Bar */}
      <StatusBar />

      {/* Main Content */}
      <div className="container mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Agent Visualizer */}
          <div className="lg:col-span-2 space-y-6">
            <AgentVisualizer />
            <TaskCreator />
          </div>

          {/* Right Column - Activity Feed */}
          <div className="lg:col-span-1">
            <ActivityFeed />
          </div>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
          <div className="bg-gray-900 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-2">
              Multi-Agent System
            </h3>
            <p className="text-sm text-gray-400">
              Orchestrate multiple AI agents with different specializations
              working together seamlessly.
            </p>
          </div>

          <div className="bg-gray-900 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-2">
              Real-time Visualization
            </h3>
            <p className="text-sm text-gray-400">
              Watch agents work in real-time with visual feedback on status,
              tools, and progress.
            </p>
          </div>

          <div className="bg-gray-900 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-2">
              Powered by AI
            </h3>
            <p className="text-sm text-gray-400">
              Built with Pydantic AI, LangGraph, Claude SDK, and modern web
              technologies.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
