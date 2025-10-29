"use client";

import { useWebSocketStore } from "@/store/websocket";
import { formatTime, formatNumber } from "@/lib/utils";
import { Wifi, WifiOff, Activity } from "lucide-react";

export function StatusBar() {
  const connected = useWebSocketStore((state) => state.connected);
  const systemStatus = useWebSocketStore((state) => state.systemStatus);

  const totalTokens = systemStatus?.agents.reduce(
    (sum, agent) => sum + agent.tokens_used,
    0
  ) || 0;

  return (
    <div className="bg-gray-900 border-b border-gray-800 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">
              AI Dream Command Center
            </h1>
            <p className="text-xs text-gray-400">
              Real-time Agent Orchestration Platform
            </p>
          </div>
        </div>

        {/* Status indicators */}
        <div className="flex items-center gap-6">
          {/* Connection status */}
          <div className="flex items-center gap-2">
            {connected ? (
              <>
                <Wifi className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-red-400" />
                <span className="text-sm text-red-400">Disconnected</span>
              </>
            )}
          </div>

          {/* Stats */}
          {systemStatus && (
            <>
              <div className="text-sm">
                <span className="text-gray-400">Tasks:</span>{" "}
                <span className="text-white font-medium">
                  {systemStatus.tasks_completed}/{systemStatus.total_tasks}
                </span>
              </div>

              <div className="text-sm">
                <span className="text-gray-400">Tokens:</span>{" "}
                <span className="text-white font-medium">
                  {formatNumber(totalTokens)}
                </span>
              </div>

              <div className="text-sm">
                <span className="text-gray-400">Uptime:</span>{" "}
                <span className="text-white font-medium">
                  {formatTime(systemStatus.uptime)}
                </span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
