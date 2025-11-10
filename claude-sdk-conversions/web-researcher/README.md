# Web Research Agent - Claude SDK

Advanced web research agent using Claude Agent SDK and Brave Search.

**Converted from**: `pydantic-ai-advanced-researcher`
**Framework**: Claude Agent SDK

## Features

- **Brave Search Integration**: Real-time web search capabilities
- **Multi-Query Research**: Automatically generates multiple search queries for comprehensive coverage
- **Source Synthesis**: Combines information from multiple sources
- **Interactive CLI**: Chat-based interface for research
- **Citation**: Proper source attribution with URLs

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Authentication

**Option A: Claude CLI (Recommended)**
```bash
claude auth login
```

**Option B: API Key**
```bash
export ANTHROPIC_API_KEY=your_key_here
```

### 3. Brave Search API Key

Get a free API key from [Brave Search API](https://brave.com/search/api/)

```bash
export BRAVE_API_KEY=your_brave_key_here
```

Or create a `.env` file:
```env
ANTHROPIC_API_KEY=your_anthropic_key
BRAVE_API_KEY=your_brave_key
```

## Usage

### Interactive Mode

```bash
python agent.py
```

This starts an interactive session where you can ask research questions:

```
===============================================================
Web Research Agent - Claude SDK Version
===============================================================

Type your research questions. Type 'exit' to quit.

You: What are the latest developments in quantum computing in 2025?

Performing 3 web searches...
  1. Searching: quantum computing developments 2025
  2. Searching: quantum computing breakthroughs 2025
  3. Searching: quantum computing applications 2025

Synthesizing answer...