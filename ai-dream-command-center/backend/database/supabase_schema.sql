-- AI Dream Command Center - Supabase Schema
-- This schema supports task tracking, agent history, and RAG capabilities

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    agent_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    result TEXT,
    error TEXT,
    total_tokens INTEGER DEFAULT 0,
    execution_time FLOAT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent sessions table
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    task_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'idle',
    tokens_used INTEGER DEFAULT 0,
    tools_used TEXT[],
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- Events table for activity tracking
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    task_id VARCHAR(255),
    message TEXT,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- Documents table for RAG
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),  -- OpenAI embeddings dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL,
    parallel_execution BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow executions
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'running',
    results JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent_id ON agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_events_agent_id ON events(agent_id);
CREATE INDEX IF NOT EXISTS idx_events_task_id ON events(task_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at DESC);

-- Vector similarity search index
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Functions for vector search
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float,
    match_count int
)
RETURNS TABLE (
    id uuid,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.content,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) as similarity
    FROM documents
    WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data (optional)
INSERT INTO workflows (workflow_id, name, description, steps) VALUES
(
    'research_and_summarize',
    'Research and Summarize',
    'Research a topic and provide a summary',
    '[
        {
            "step_id": "research",
            "agent_type": "researcher",
            "prompt": "Research the topic: {topic}",
            "tools": ["web_search"],
            "depends_on": []
        },
        {
            "step_id": "summarize",
            "agent_type": "analyst",
            "prompt": "Summarize the research findings",
            "tools": [],
            "depends_on": ["research"]
        }
    ]'::jsonb
)
ON CONFLICT (workflow_id) DO NOTHING;
