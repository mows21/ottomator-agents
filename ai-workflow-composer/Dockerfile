# AI Workflow Composer - Docker Configuration

FROM python:3.11-slim

LABEL maintainer="ottomator-agents"
LABEL description="AI Workflow Composer - Generate n8n workflows from natural language"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose API port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# Run the FastAPI server
CMD ["uvicorn", "api.mcp_server:app", "--host", "0.0.0.0", "--port", "8001"]
