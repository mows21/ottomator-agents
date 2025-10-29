# Getting Started with AI Dream Command Center

Welcome! This guide will help you get the AI Dream Command Center up and running in minutes.

## Prerequisites

Before you begin, make sure you have:

- **Python 3.9+** installed ([Download](https://www.python.org/downloads/))
- **Node.js 18+** and npm ([Download](https://nodejs.org/))
- **API Keys**:
  - Anthropic API key (get from [console.anthropic.com](https://console.anthropic.com))
  - OpenAI API key (optional, for OpenAI models)

## Quick Start (5 minutes)

### Step 1: Clone or Navigate to the Directory

```bash
cd ai-dream-command-center
```

### Step 2: Set Up the Backend

```bash
# Navigate to backend
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and add your API keys
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here (optional)
```

**Edit `.env` file:**
```bash
nano .env  # or use your preferred editor
```

Add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

### Step 3: Start the Backend Server

```bash
# From the backend directory
python main.py
```

You should see:
```
🚀 Starting AI Dream Command Center on 0.0.0.0:8000
📚 API Documentation: http://localhost:8000/docs
🔌 WebSocket: ws://localhost:8000/ws
```

Keep this terminal running!

### Step 4: Set Up the Frontend

Open a **new terminal window**:

```bash
# Navigate to frontend
cd ai-dream-command-center/frontend

# Install dependencies
npm install

# Create environment file (optional, has good defaults)
cp .env.example .env.local

# Start the development server
npm run dev
```

You should see:
```
✓ Ready on http://localhost:3000
```

### Step 5: Open the Command Center

Open your browser and go to:
```
http://localhost:3000
```

You should see the AI Dream Command Center interface!

## Your First Task

1. **Look at the Interface**:
   - Top: Status bar showing connection status
   - Left: Agent visualizer (the central hub with orbiting bubbles)
   - Right: Activity feed
   - Bottom left: Task creator

2. **Create a Task**:
   - Scroll to the "Create Task" section
   - Select an agent type (or use "Auto-select")
   - Enter a prompt, for example:
     ```
     Write a Python function to check if a number is prime
     ```
   - Click "Create Task"

3. **Watch the Magic**:
   - A new agent bubble will appear and orbit the central hub
   - The bubble will pulse and change colors as the agent works
   - Events will appear in the Activity Feed in real-time
   - When complete, you'll see the result below the task form

## Example Tasks to Try

### For Coder Agent
```
Write a Python function to calculate fibonacci numbers recursively and iteratively
```

### For Researcher Agent
```
Research the latest developments in large language models in 2024
```

### For Analyst Agent
```
Analyze this dataset and find patterns: [10, 15, 20, 25, 30, 35, 40]
```

### For Web Searcher Agent
```
Find information about the latest AI frameworks for building agents
```

## Troubleshooting

### Backend won't start

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Make sure you installed requirements:
```bash
pip install -r requirements.txt
```

---

**Problem**: `Error: ANTHROPIC_API_KEY not found`

**Solution**: Check your `.env` file has the API key:
```bash
cat .env
# Should show: ANTHROPIC_API_KEY=sk-ant-xxxxx
```

---

### Frontend won't connect

**Problem**: Frontend shows "Disconnected"

**Solution**: Make sure backend is running on port 8000:
```bash
# Check if backend is running
curl http://localhost:8000/health
```

---

**Problem**: `npm install` fails

**Solution**: Update npm:
```bash
npm install -g npm@latest
```

---

### Agent not working

**Problem**: Task fails with API error

**Solution**: Verify your API key is valid:
```bash
# Test the key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY_HERE" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":100,"messages":[{"role":"user","content":"Hi"}]}'
```

## Next Steps

### Explore the API Documentation

Visit: `http://localhost:8000/docs`

This interactive API documentation lets you:
- See all available endpoints
- Test API calls directly
- View request/response schemas

### Try Advanced Features

1. **Create a Workflow** (multi-step task):
```bash
cd backend
python examples/workflow_example.py
```

2. **Monitor with WebSocket**:
```bash
python examples/websocket_client.py
```

3. **Check System Status**:
```bash
curl http://localhost:8000/status | python -m json.tool
```

### Customize Agents

Edit `backend/agents.py` to:
- Modify agent prompts
- Add new agent types
- Register custom tools

### Add New Tools

Edit `backend/tools.py` to:
- Create custom tools
- Integrate external APIs
- Add specialized functions

## Docker Deployment (Optional)

If you prefer using Docker:

```bash
# Make sure Docker is installed
docker --version

# Start everything with docker-compose
docker-compose up
```

This will:
- Build both backend and frontend
- Start on the same ports (8000, 3000)
- Handle networking automatically

## What's Next?

- Read the [Architecture Documentation](docs/ARCHITECTURE.md)
- Explore [Advanced Examples](backend/examples/)
- Set up [Supabase Integration](backend/database/supabase_schema.sql)
- Configure [MCP Servers](backend/integrations/mcp_client.py)
- Add [LangFuse Monitoring](https://langfuse.com/)

## Getting Help

- Check the main [README.md](README.md)
- Review example code in `/backend/examples/`
- Open an issue on GitHub
- Check the FAQ section

## Common Questions

**Q: Can I use OpenAI instead of Anthropic?**

A: Yes! Set `use_openai=True` when creating agents in `agents.py`.

**Q: How do I add more agents?**

A: Create new agent classes in `backend/agents.py` following the `DreamAgent` pattern.

**Q: Can I run this in production?**

A: Yes! Use Docker, set proper environment variables, and configure HTTPS.

**Q: Is there a cost?**

A: The platform is free and open-source. You only pay for API usage (Anthropic/OpenAI).

---

Happy orchestrating! 🚀

If you build something cool, share it with the community!
