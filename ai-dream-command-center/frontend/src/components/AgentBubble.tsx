"use client";

import { motion } from "framer-motion";
import { AgentState, AgentStatus } from "@/types";
import { getStatusColor, getAgentTypeColor } from "@/lib/utils";
import { Brain, Code, BarChart3, Search, Database, Network } from "lucide-react";

interface AgentBubbleProps {
  agent: AgentState;
  index: number;
}

const iconMap: Record<string, any> = {
  researcher: Brain,
  coder: Code,
  analyst: BarChart3,
  web_searcher: Search,
  rag_agent: Database,
  orchestrator: Network,
};

export function AgentBubble({ agent, index }: AgentBubbleProps) {
  const Icon = iconMap[agent.agent_type] || Brain;
  const isActive = agent.status === AgentStatus.WORKING ||
                   agent.status === AgentStatus.THINKING ||
                   agent.status === AgentStatus.USING_TOOL;

  // Calculate size based on activity
  const baseSize = 80;
  const activityBonus = isActive ? 20 : 0;
  const size = baseSize + activityBonus;

  // Position in a circular pattern
  const angle = (index / 6) * 2 * Math.PI;
  const radius = 150;
  const x = Math.cos(angle) * radius;
  const y = Math.sin(angle) * radius;

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{
        scale: 1,
        opacity: 1,
        x,
        y,
      }}
      exit={{ scale: 0, opacity: 0 }}
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 20,
      }}
      className="absolute"
      style={{
        width: size,
        height: size,
      }}
    >
      <motion.div
        animate={{
          scale: isActive ? [1, 1.1, 1] : 1,
        }}
        transition={{
          duration: 2,
          repeat: isActive ? Infinity : 0,
          ease: "easeInOut",
        }}
        className={`
          relative w-full h-full rounded-full
          ${getAgentTypeColor(agent.agent_type)}
          shadow-lg cursor-pointer
          flex items-center justify-center
          text-white
        `}
      >
        {/* Pulsing ring for active agents */}
        {isActive && (
          <motion.div
            className={`absolute inset-0 rounded-full ${getAgentTypeColor(agent.agent_type)} opacity-50`}
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.5, 0, 0.5],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeOut",
            }}
          />
        )}

        {/* Icon */}
        <Icon className="w-8 h-8 relative z-10" />

        {/* Status indicator */}
        <div
          className={`
            absolute bottom-0 right-0 w-4 h-4 rounded-full
            ${getStatusColor(agent.status)}
            border-2 border-white
            z-20
          `}
        />
      </motion.div>

      {/* Agent info tooltip */}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 hover:opacity-100 transition-opacity pointer-events-none">
        <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
          <div className="font-semibold">{agent.agent_type.replace("_", " ").toUpperCase()}</div>
          <div className="text-gray-300">{agent.status}</div>
          <div className="text-gray-400">{agent.tokens_used} tokens</div>
        </div>
      </div>
    </motion.div>
  );
}
