# Archon Motion AI - Quick Start Guide

Get Archon Motion AI running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Anthropic API key (get from [console.anthropic.com](https://console.anthropic.com))
- 4GB RAM minimum

## Installation

### 1. Clone Repository

```bash
cd archon-motion-ai
```

### 2. Set Up Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit with your API keys
nano backend/.env
```

Add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

### 3. Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
docker-compose ps
```

You should see:
- ✅ archon-postgres (healthy)
- ✅ archon-redis (running)
- ✅ archon-chromadb (running)
- ✅ archon-backend (running)

### 4. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","version":"1.0.0",...}
```

## Your First Project

### Via API

**Create a Project:**
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Project",
    "description": "Build a task management web application with React and FastAPI",
    "auto_generate_plan": true
  }'
```

**Get AI-Generated Plan:**
```bash
# Use the project_id from previous response
curl -X POST http://localhost:8000/api/projects/{project_id}/generate-plan
```

**Create a Task:**
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "your-project-id",
    "title": "Design database schema",
    "description": "Create PostgreSQL schema for user and task tables",
    "priority": "high",
    "estimated_duration": 240
  }'
```

**Get Optimized Schedule:**
```bash
curl http://localhost:8000/api/tasks/schedule?project_id=your-project-id
```

### Via Chat Interface

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a project to build a chat application with real-time features"
  }'
```

## Using MCP with Claude Desktop

### 1. Configure Claude Desktop

Edit your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "archon-motion": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/archon-motion-ai/mcp-server",
      "env": {
        "API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### 2. Use with Claude

```
You: Create a project called "Mobile App Development"

Claude: I'll create that project for you using the Archon Motion system.
[Uses create_project tool]

Project created successfully!
- Name: Mobile App Development
- ID: proj_abc123
- AI-generated plan with 45 tasks

Would you like me to show you the schedule?

You: Yes, show me the schedule for this week

Claude: [Uses get_schedule tool]
Here's your optimized schedule for this week:

Monday:
  - Set up development environment (4h)
  - Design app architecture (3h)

Tuesday:
  - Implement authentication (6h)
  ...
```

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

## Next Steps

1. **Explore Agents**: Try different agent workflows
   ```bash
   curl -X POST http://localhost:8000/api/agents/workflow \
     -H "Content-Type: application/json" \
     -d '{"task": "Break down authentication system into tasks"}'
   ```

2. **Check Logs**:
   ```bash
   docker-compose logs -f backend
   ```

3. **Customize Agents**: Edit `backend/app/agents/planning.py` to customize planning logic

4. **Add Frontend**: See `frontend/` directory for React app (optional)

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Verify database connection
docker-compose exec backend python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### Can't Connect to API

```bash
# Check if backend is running
docker-compose ps

# Test connection
curl http://localhost:8000/
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

## Development Mode

For development with hot-reloading:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Stopping Services

```bash
# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove all data (reset)
docker-compose down -v
```

## Getting Help

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **GitHub Issues**: Report bugs and request features
- **Wiki**: See full documentation in `docs/WIKI.md`

---

You're all set! Start building intelligent project management systems with AI! 🚀
