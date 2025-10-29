"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useWebSocketStore } from "@/store/websocket";
import { formatTime } from "@/lib/utils";
import { Brain, Wrench, CheckCircle2, XCircle, Info } from "lucide-react";
import { AgentEvent } from "@/types";

const eventIcons = {
  status_change: Brain,
  tool_call: Wrench,
  result: CheckCircle2,
  error: XCircle,
  message: Info,
};

function EventItem({ event }: { event: AgentEvent }) {
  const Icon = eventIcons[event.event_type] || Info;
  const timestamp = new Date(event.timestamp).toLocaleTimeString();

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="flex items-start gap-3 p-3 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors"
    >
      <div className={`
        p-2 rounded-lg
        ${event.event_type === "error" ? "bg-red-500/20 text-red-400" :
          event.event_type === "result" ? "bg-green-500/20 text-green-400" :
          event.event_type === "tool_call" ? "bg-purple-500/20 text-purple-400" :
          "bg-blue-500/20 text-blue-400"}
      `}>
        <Icon className="w-4 h-4" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm font-medium text-white">
            {event.agent_type.replace("_", " ").toUpperCase()}
          </span>
          <span className="text-xs text-gray-500">{timestamp}</span>
        </div>

        {event.message && (
          <p className="text-sm text-gray-300 mt-1 line-clamp-2">
            {event.message}
          </p>
        )}

        {event.status && (
          <div className="mt-1">
            <span className="text-xs px-2 py-1 rounded-full bg-gray-700 text-gray-300">
              {event.status}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export function ActivityFeed() {
  const events = useWebSocketStore((state) => state.events);
  const clearEvents = useWebSocketStore((state) => state.clearEvents);

  return (
    <div className="bg-gray-900 rounded-lg p-4 h-[500px] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">Activity Feed</h2>
        <button
          onClick={clearEvents}
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Clear
        </button>
      </div>

      {/* Events list */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-2">
        <AnimatePresence mode="popLayout">
          {events.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p>No activity yet</p>
              <p className="text-sm mt-2">Events will appear here in real-time</p>
            </div>
          ) : (
            events.map((event, index) => (
              <EventItem key={`${event.agent_id}-${event.timestamp}-${index}`} event={event} />
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
