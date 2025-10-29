# Archon Motion AI

**AI-Powered Project Management System with Claude Integration**

A comprehensive project management platform that combines Motion.com-style intelligent scheduling with Claude AI integration, RAG capabilities, and multi-agent orchestration.

## 🎯 Overview

Archon Motion AI brings together:
- **Intelligent Scheduling**: Auto-prioritization and smart task scheduling
- **AI Agents**: Specialized agents for planning, coding, research, and risk management
- **RAG Knowledge Base**: Context-aware project management with semantic search
- **MCP Integration**: Extensible tool system via Model Context Protocol
- **Natural Language Interface**: Manage projects through conversation with Claude

## ✨ Key Features

- 🤖 **Multi-Agent System**: Planning, Scheduling, Code, Research, and Risk agents
- 📊 **Smart Scheduling**: AI-powered task prioritization and timeline optimization
- 🧠 **Knowledge Management**: RAG system for context-aware decisions
- 🔌 **MCP Tools**: Integrate with Claude Desktop and Claude Code
- ⚡ **Real-time Updates**: WebSocket-powered live task updates
- 🎨 **Modern UI**: Beautiful React frontend with 21st.dev-style components

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Anthropic API key

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/archon-motion-ai.git
cd archon-motion-ai

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Start with Docker
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📖 Documentation

- [Complete Wiki](./docs/WIKI.md) - Comprehensive system documentation
- [API Reference](./docs/API_REFERENCE.md) - REST API documentation
- [MCP Tools](./docs/MCP_TOOLS.md) - MCP tool integration guide
- [Deployment](./docs/DEPLOYMENT.md) - Production deployment guide
- [Agent Development](./docs/AGENT_GUIDE.md) - Creating custom agents

## 🏗️ Architecture

```
Frontend (React) → API Gateway (FastAPI)
                   ├── Agent Orchestrator
                   ├── RAG Engine (ChromaDB)
                   ├── Scheduling Service
                   └── MCP Gateway

Database: PostgreSQL + Redis + ChromaDB
```

## 💡 Example Usage

**Natural Language Project Creation:**
```
You: Create a project to build an e-commerce platform with React and Python

Archon: I've created "E-commerce Platform" with 45 tasks across 6 phases:
- Architecture & Setup (5 tasks)
- Backend API Development (12 tasks)
- Frontend Development (15 tasks)
- Payment Integration (8 tasks)
- Testing & QA (5 tasks)

Estimated timeline: 12 weeks
First milestone: November 15, 2025

Would you like me to optimize the schedule?
```

**Smart Scheduling:**
```
You: Show me my tasks for this week

Archon: Based on priorities and deadlines, here's your optimized week:

Monday:
  - Design authentication UI (4h) - Blocking 3 other tasks
  - API endpoint implementation (3h)

Tuesday:
  - Database schema updates (5h)
  - Code review: Payment module (2h)

...
```

## 🤖 Agent Types

- **Planning Agent**: Breaks down projects into actionable tasks
- **Scheduling Agent**: Optimizes task timelines based on priorities
- **Code Agent**: Assists with technical implementation
- **Research Agent**: Gathers information from knowledge base
- **Risk Agent**: Monitors project health and deadlines

## 🔌 MCP Integration

Works seamlessly with Claude Desktop:

```json
{
  "mcpServers": {
    "archon-motion": {
      "command": "docker",
      "args": ["exec", "-i", "archon-mcp-server", "python", "-m", "mcp_server"]
    }
  }
}
```

## 🛠️ Tech Stack

**Backend:**
- FastAPI + Python 3.11
- PostgreSQL + ChromaDB + Redis
- Pydantic AI + LangChain
- WebSockets for real-time updates

**Frontend:**
- React 18 + TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query + Zustand
- Vite build system

**Infrastructure:**
- Docker + Docker Compose
- Nginx reverse proxy
- GitHub Actions CI/CD

## 📊 Project Status

✅ Core backend API
✅ Agent orchestration system
✅ RAG knowledge base
✅ MCP server integration
✅ React frontend
✅ WebSocket real-time updates
✅ Docker deployment
🔄 Advanced scheduling algorithms (in progress)
📅 Mobile app (planned)

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](./LICENSE)

## 🙏 Acknowledgments

Inspired by:
- Motion.com for intelligent scheduling
- Archon for knowledge management
- Pydantic AI for agent orchestration
- Claude for AI capabilities

---

Built with ❤️ using Claude Code
