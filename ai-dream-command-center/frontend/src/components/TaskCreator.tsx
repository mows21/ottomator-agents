"use client";

import { useState } from "react";
import { AgentType, TaskRequest } from "@/types";
import { Send, Loader2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function TaskCreator() {
  const [prompt, setPrompt] = useState("");
  const [agentType, setAgentType] = useState<AgentType | "auto">("auto");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!prompt.trim()) {
      setError("Please enter a task");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const taskRequest: TaskRequest = {
        prompt: prompt.trim(),
        agent_type: agentType === "auto" ? undefined : agentType,
      };

      const response = await fetch(`${API_URL}/tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(taskRequest),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        setResult(data.result);
        setPrompt(""); // Clear input on success
      } else {
        setError(data.error || "Task failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-4">Create Task</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Agent type selector */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Agent Type
          </label>
          <select
            value={agentType}
            onChange={(e) => setAgentType(e.target.value as AgentType | "auto")}
            className="w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          >
            <option value="auto">Auto-select</option>
            <option value={AgentType.RESEARCHER}>Researcher</option>
            <option value={AgentType.CODER}>Coder</option>
            <option value={AgentType.ANALYST}>Analyst</option>
            <option value={AgentType.WEB_SEARCHER}>Web Searcher</option>
            <option value={AgentType.RAG_AGENT}>RAG Agent</option>
          </select>
        </div>

        {/* Prompt input */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Task Description
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe your task... (e.g., 'Research the latest AI developments' or 'Write a Python function to sort a list')"
            className="w-full px-4 py-3 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none"
            rows={4}
          />
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={loading || !prompt.trim()}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              Create Task
            </>
          )}
        </button>
      </form>

      {/* Error display */}
      {error && (
        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Result display */}
      {result && (
        <div className="mt-4 p-4 bg-green-500/10 border border-green-500/50 rounded-lg">
          <p className="text-sm font-medium text-green-400 mb-2">Result:</p>
          <p className="text-gray-300 text-sm whitespace-pre-wrap">{result}</p>
        </div>
      )}
    </div>
  );
}
