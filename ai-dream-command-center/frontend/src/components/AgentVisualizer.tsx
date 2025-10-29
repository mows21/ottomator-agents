"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useWebSocketStore } from "@/store/websocket";
import { AgentBubble } from "./AgentBubble";

export function AgentVisualizer() {
  const agents = useWebSocketStore((state) => state.agents);

  return (
    <div className="relative w-full h-[500px] bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg overflow-hidden">
      {/* Grid background */}
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]" />

      {/* Central hub */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
        <motion.div
          animate={{
            rotate: 360,
          }}
          transition={{
            duration: 60,
            repeat: Infinity,
            ease: "linear",
          }}
          className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 shadow-2xl flex items-center justify-center"
        >
          <div className="w-20 h-20 rounded-full bg-gray-900 flex items-center justify-center text-white font-bold">
            AI
          </div>
        </motion.div>

        {/* Agents orbiting the center */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <AnimatePresence>
            {agents.map((agent, index) => (
              <AgentBubble key={agent.agent_id} agent={agent} index={index} />
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Agent count */}
      <div className="absolute top-4 right-4 bg-black/50 backdrop-blur-sm rounded-lg px-4 py-2 text-white">
        <div className="text-sm text-gray-400">Active Agents</div>
        <div className="text-2xl font-bold">{agents.length}</div>
      </div>

      {/* No agents message */}
      {agents.length === 0 && (
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 translate-y-12 text-center text-gray-500">
          <p>No active agents</p>
          <p className="text-sm">Create a task to spawn agents</p>
        </div>
      )}
    </div>
  );
}
