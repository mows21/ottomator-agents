# AI Dream Command Center

<div align="center">

![AI Dream Command Center](https://img.shields.io/badge/AI-Dream%20Command%20Center-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-teal)
![License](https://img.shields.io/badge/License-MIT-yellow)

**A comprehensive AI agent orchestration platform with real-time visualization**

[Features](#features) •
[Quick Start](#quick-start) •
[Architecture](#architecture) •
[Documentation](#documentation) •
[Demo](#demo)

</div>

---

## Overview

The **AI Dream Command Center** is a cutting-edge platform for orchestrating multiple AI agents with real-time visual feedback. It combines powerful AI frameworks (Pydantic AI, LangGraph, Claude SDK) with a modern, responsive web interface to provide an intuitive command and control experience for AI agents.

### Key Highlights

- **Visual Agent Orchestration**: Watch AI agents work in real-time with animated bubble visualizations
- **Multi-Agent Workflows**: Coordinate multiple specialized agents (researchers, coders, analysts)
- **Real-time Updates**: WebSocket-powered live activity feed and status updates
- **Extensible Architecture**: Easy to add new agent types, tools, and workflows
- **Modern Tech Stack**: Built with FastAPI, Next.js, TypeScript, Tailwind CSS
- **Production Ready**: Includes monitoring, error handling, and deployment configurations

## Features

### Backend

- **FastAPI Server** with WebSocket support for real-time communication
- **Pydantic AI Agents** with type-safe tool integrations
- **Agent Orchestrator** for managing multiple agents and workflows
- **Tool System** with extensible tools (web search, calculator, code execution, etc.)
- **LangGraph Integration** for complex multi-step workflows
- **Supabase Ready** for data persistence and vector search
- **LangFuse Support** for observability and monitoring
- **MCP Server Integration** for extended capabilities

### Frontend

- **Next.js 15** with App Router and TypeScript
- **Real-time Agent Visualization** with animated bubbles showing agent activity
- **Activity Feed** displaying all agent events in real-time
- **Task Creation UI** for spawning new agent tasks
- **WebSocket Client** using Zustand for state management
- **Responsive Design** with Tailwind CSS and shadcn/ui components
- **Dark Mode** optimized interface
- **Framer Motion** for smooth animations

### Agent Types

1. **Researcher**: Gathers and synthesizes information
2. **Coder**: Writes and explains code
3. **Analyst**: Analyzes data and provides insights
4. **Web Searcher**: Searches the web for information
5. **RAG Agent**: Retrieval-augmented generation
6. **Orchestrator**: Coordinates multiple sub-agents

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn
- API keys for Anthropic/OpenAI

### Installation

#### 1. Clone the Repository

```bash
cd ai-dream-command-center
```

#### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# Run the server
python main.py
```

The backend will start at `http://localhost:8000`

API Docs: `http://localhost:8000/docs`

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit if needed (default connects to localhost:8000)

# Run the development server
npm run dev
```

The frontend will start at `http://localhost:3000`

### First Task

1. Open `http://localhost:3000` in your browser
2. You should see the Command Center interface
3. In the "Create Task" section, enter a prompt like:
   - "Research the latest developments in AI"
   - "Write a Python function to calculate fibonacci numbers"
   - "Analyze this data: [1, 2, 3, 4, 5]"
4. Select an agent type or use "Auto-select"
5. Click "Create Task"
6. Watch the agent bubble appear and animate as it works
7. See real-time events in the Activity Feed
8. View the result when complete

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                      │
│  • Agent Visualizer (Bubbles)                           │
│  • Activity Feed                                        │
│  • Task Creator                                         │
│  • Real-time WebSocket Client                           │
└─────────────────────────────────────────────────────────┘
                          │
                   WebSocket/REST API
                          │
┌─────────────────────────────────────────────────────────┐
│              Backend (FastAPI)                           │
│  • WebSocket Server                                     │
│  • REST API Endpoints                                   │
│  • Agent Orchestrator                                   │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│           Agent Frameworks                               │
│  • Pydantic AI Agents                                   │
│  • Claude SDK Integration                               │
│  • LangGraph Workflows                                  │
│  • Tool System (extensible)                             │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│         Data & Services                                  │
│  • Supabase (PostgreSQL + pgvector)                     │
│  • LangFuse (Monitoring)                                │
│  • MCP Servers                                          │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
ai-dream-command-center/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── models.py               # Pydantic models
│   ├── agents.py               # AI agents
│   ├── orchestrator.py         # Agent orchestration
│   ├── tools.py                # Tool system
│   ├── websocket_manager.py    # WebSocket handling
│   ├── requirements.txt        # Python dependencies
│   └── .env.example           # Environment template
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js app router
│   │   ├── components/        # React components
│   │   ├── store/             # Zustand stores
│   │   ├── types/             # TypeScript types
│   │   └── lib/               # Utilities
│   ├── package.json           # Node dependencies
│   └── .env.example           # Environment template
└── docs/
    └── ARCHITECTURE.md        # Detailed architecture
```

## API Endpoints

### REST API

- `GET /` - API information
- `GET /health` - Health check
- `GET /status` - System status
- `GET /agents` - List all agents
- `POST /tasks` - Create a new task
- `GET /tasks/{task_id}` - Get task result
- `POST /workflows` - Execute a workflow
- `GET /agent-types` - List agent types

### WebSocket

- `ws://localhost:8000/ws` - Real-time updates

## Configuration

### Backend Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Optional
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
LANGFUSE_PUBLIC_KEY=your_langfuse_key
LANGFUSE_SECRET_KEY=your_langfuse_secret
```

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## Advanced Features

### Custom Agents

Create custom agents by extending the `DreamAgent` class:

```python
from agents import DreamAgent
from models import AgentType

class MyCustomAgent(DreamAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.CUSTOM)

    def _get_system_prompt(self) -> str:
        return "You are a custom agent with special capabilities..."
```

### Custom Tools

Register new tools in the tool system:

```python
from tools import tool_registry

async def my_custom_tool(param: str) -> dict:
    """Your custom tool implementation."""
    return {"result": "success"}

tool_registry.register("my_tool", my_custom_tool)
```

### Workflows

Define multi-step workflows with LangGraph:

```python
from models import Workflow, WorkflowStep, AgentType

workflow = Workflow(
    workflow_id="research_and_code",
    name="Research and Code",
    description="Research a topic then write code",
    steps=[
        WorkflowStep(
            step_id="research",
            agent_type=AgentType.RESEARCHER,
            prompt="Research {topic}",
        ),
        WorkflowStep(
            step_id="code",
            agent_type=AgentType.CODER,
            prompt="Write code based on research",
            depends_on=["research"],
        ),
    ],
)
```

## Deployment

### Docker (Coming Soon)

```bash
docker-compose up
```

### Production Considerations

- Use environment variables for API keys (never commit them)
- Set up proper CORS origins
- Enable rate limiting
- Use HTTPS for WebSocket connections
- Configure proper logging and monitoring
- Set up database backups (Supabase)
- Use LangFuse for production monitoring

## Monitoring

The platform includes built-in monitoring:

- **LangFuse**: Agent traces, LLM calls, tool usage
- **System Status**: Active agents, task completion rates, token usage
- **Activity Feed**: Real-time event stream
- **WebSocket Health**: Connection status and heartbeat

## Troubleshooting

### Backend won't start

- Check Python version: `python --version` (need 3.9+)
- Verify API keys in `.env`
- Check port 8000 is not in use: `lsof -i :8000`

### Frontend won't connect

- Verify backend is running
- Check WebSocket URL in `.env.local`
- Open browser console for error messages
- Verify CORS settings in backend

### Agents not appearing

- Check browser console for WebSocket errors
- Verify API endpoint is correct
- Check backend logs for errors
- Ensure API keys are valid

## Contributing

Contributions are welcome! This is part of the Open-Source Agent Studio community.

## License

MIT License - See LICENSE file for details

## Credits

Built with:
- [Pydantic AI](https://ai.pydantic.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Framer Motion](https://www.framer.com/motion/)

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/yourrepo/issues)
- Documentation: See `/docs` folder
- Community: Join our Discord

---

<div align="center">

Made with ❤️ by the Open-Source AI Community

[⬆ Back to Top](#ai-dream-command-center)

</div>
