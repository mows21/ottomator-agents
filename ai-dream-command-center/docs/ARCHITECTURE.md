# AI Dream Command Center - Architecture

## Overview

The AI Dream Command Center is a comprehensive visual orchestration platform that unifies multiple AI frameworks into a single, real-time command and control interface.

## Architecture Layers

### 1. Frontend Layer (Next.js + React + TypeScript)

```
┌─────────────────────────────────────────────────────────┐
│                  Command Center UI                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Agent      │  │   Workflow   │  │  Monitoring  │  │
│  │ Visualizer   │  │   Builder    │  │  Dashboard   │  │
│  │  (Bubbles)   │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Activity   │  │   Tool       │  │    Agent     │  │
│  │    Feed      │  │  Manager     │  │   Library    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                   WebSocket/REST API
                          │
┌─────────────────────────────────────────────────────────┐
│              Backend API Server (FastAPI)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  WebSocket   │  │  REST API    │  │  Auth/CORS   │  │
│  │   Server     │  │  Endpoints   │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│           Agent Orchestration Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  LangGraph   │  │ Pydantic AI  │  │ Claude SDK   │  │
│  │ Orchestrator │  │    Agents    │  │   Agents     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Sub-Agent   │  │   Workflow   │  │     Tool     │  │
│  │   Manager    │  │   Engine     │  │   Registry   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│              Integration & Tools Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ MCP Servers  │  │   LangFuse   │  │   Supabase   │  │
│  │              │  │ (Monitoring) │  │  (Database)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

### Frontend
- **Framework**: Next.js 15+ (App Router)
- **UI Library**: React 18+
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand / React Context
- **Real-time**: WebSocket client
- **Data Viz**: D3.js / Recharts for visualizations
- **Type Safety**: TypeScript 5+

### Backend
- **API Framework**: FastAPI
- **WebSocket**: FastAPI WebSocket support
- **Validation**: Pydantic v2
- **Async Runtime**: asyncio + uvicorn

### Agent Frameworks
- **Orchestration**: LangGraph (workflow graphs)
- **Agent Framework**: Pydantic AI (type-safe agents)
- **Claude Integration**: Claude Agent SDK
- **Voice Agents**: LiveKit (optional integration)

### Data & Monitoring
- **Database**: Supabase (PostgreSQL + pgvector)
- **Observability**: LangFuse
- **Caching**: Redis (optional)
- **MCP**: Model Context Protocol servers

## Core Components

### 1. Agent Orchestrator

The orchestrator manages multiple agents working together:

```python
class AgentOrchestrator:
    - Sub-agents: Research, Code, Analysis, Web Search
    - Workflows: Multi-step processes
    - State management: Shared context
    - Event emission: Real-time updates
```

### 2. Real-time Visualization

Agent activity visualized as:
- **Bubbles**: Each agent is a bubble, size = activity level
- **Feed**: Chronological activity stream
- **Graph**: Agent relationships and data flow
- **Metrics**: Token usage, latency, success rates

### 3. Tool System

Extensible tool architecture:
- File operations (Read, Write, Edit)
- Web search (Brave API)
- Code execution (sandboxed)
- Database queries
- API integrations
- Custom MCP tools

### 4. Workflow Builder

Visual workflow creation:
- Drag-and-drop agent nodes
- Connect agents with data flows
- Conditional branching
- Parallel execution
- Save/load workflow templates

## Data Flow

1. **User Input** → Frontend
2. **WebSocket** → Backend API
3. **Orchestrator** → Select agent/workflow
4. **Agent Execution** → Sub-agents + tools
5. **Events** → WebSocket → Frontend
6. **Visualization** → Real-time updates
7. **Results** → Store in Supabase
8. **Monitoring** → LangFuse traces

## Key Features

### Phase 1 (MVP)
- ✓ FastAPI backend with WebSocket
- ✓ Pydantic AI agent with tools
- ✓ Next.js frontend
- ✓ Real-time agent bubbles visualization
- ✓ Activity feed
- ✓ Basic workflow execution

### Phase 2 (Enhanced)
- LangGraph multi-agent workflows
- Claude SDK integration
- MCP server connections
- Supabase persistence
- LangFuse monitoring

### Phase 3 (Advanced)
- Visual workflow builder
- Agent marketplace
- Custom tool creation
- Voice agent integration
- Advanced analytics

## Performance Targets

- **Response Time**: < 200ms for API calls
- **WebSocket Latency**: < 50ms
- **Agent Startup**: < 1s
- **Concurrent Users**: 100+
- **Bundle Size**: < 500KB (frontend)

## Security

- API key management (environment variables)
- CORS configuration
- Rate limiting
- Input validation (Pydantic)
- Sandboxed code execution

## Deployment

- **Development**: `uvicorn` + `next dev`
- **Production**: Docker containers
- **Database**: Supabase cloud
- **Monitoring**: LangFuse cloud
- **CDN**: Vercel (frontend) / AWS (backend)

## Next Steps

1. Build backend API server
2. Create agent orchestration system
3. Develop frontend with visualizations
4. Integrate all frameworks
5. Add example workflows
6. Documentation and testing
