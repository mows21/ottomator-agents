-- AI Workflow Composer Database Schema

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Workflow templates table
CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    template_json JSONB NOT NULL,
    parameters JSONB DEFAULT '{}',
    tags TEXT[],
    use_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generated workflows table
CREATE TABLE IF NOT EXISTS generated_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_description TEXT NOT NULL,
    workflow_json JSONB NOT NULL,
    n8n_workflow_id VARCHAR(255),
    generation_method VARCHAR(50), -- 'template', 'ai', 'hybrid'
    confidence_score FLOAT,
    template_id UUID REFERENCES workflow_templates(id),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Execution history table
CREATE TABLE IF NOT EXISTS execution_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES generated_workflows(id),
    n8n_execution_id VARCHAR(255),
    status VARCHAR(50), -- 'success', 'failed', 'running'
    execution_time_ms INTEGER,
    error_message TEXT,
    error_type VARCHAR(100),
    output_data JSONB,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Evaluation metrics table
CREATE TABLE IF NOT EXISTS evaluation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES generated_workflows(id),
    execution_id UUID REFERENCES execution_history(id),
    json_validity_score FLOAT,
    execution_success_score FLOAT,
    performance_score FLOAT,
    overall_score FLOAT,
    feedback JSONB,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow embeddings for vector search
CREATE TABLE IF NOT EXISTS workflow_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES generated_workflows(id),
    template_id UUID REFERENCES workflow_templates(id),
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pattern recognition table
CREATE TABLE IF NOT EXISTS workflow_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(100), -- 'node_sequence', 'parameter', 'connection', 'error_handling'
    pattern_data JSONB NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    success_rate FLOAT DEFAULT 0.0,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent learning history
CREATE TABLE IF NOT EXISTS agent_learning_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(100), -- 'workflow_generator', 'prompt_optimizer', 'evaluator'
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    feedback_score FLOAT,
    learning_context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflow_templates_category ON workflow_templates(category);
CREATE INDEX IF NOT EXISTS idx_workflow_templates_tags ON workflow_templates USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_generated_workflows_user ON generated_workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_workflows_session ON generated_workflows(session_id);
CREATE INDEX IF NOT EXISTS idx_generated_workflows_created ON generated_workflows(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_history_workflow ON execution_history(workflow_id);
CREATE INDEX IF NOT EXISTS idx_execution_history_status ON execution_history(status);
CREATE INDEX IF NOT EXISTS idx_evaluation_metrics_workflow ON evaluation_metrics(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_embeddings_vector ON workflow_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_workflow_patterns_type ON workflow_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_agent_learning_history_type ON agent_learning_history(agent_type);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for updated_at
CREATE TRIGGER update_workflow_templates_updated_at
    BEFORE UPDATE ON workflow_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_patterns_updated_at
    BEFORE UPDATE ON workflow_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert initial template categories
INSERT INTO workflow_templates (name, description, category, template_json, parameters, tags) VALUES
('Email Notification Template', 'Send email notifications via SMTP', 'communication', '{}', '{"to": "", "subject": "", "body": ""}', ARRAY['email', 'notification']),
('Database Query Template', 'Query PostgreSQL database', 'database', '{}', '{"query": "", "connection": ""}', ARRAY['database', 'sql']),
('API Call Template', 'Make HTTP requests to REST APIs', 'integration', '{}', '{"url": "", "method": "GET", "headers": {}}', ARRAY['api', 'http']),
('Web Scraper Template', 'Scrape website content', 'data', '{}', '{"url": "", "selector": ""}', ARRAY['scraping', 'web']),
('File Processing Template', 'Process CSV/JSON files', 'data', '{}', '{"file_path": "", "format": "csv"}', ARRAY['file', 'processing'])
ON CONFLICT DO NOTHING;

-- Comments
COMMENT ON TABLE workflow_templates IS 'Hand-crafted n8n workflow templates';
COMMENT ON TABLE generated_workflows IS 'AI-generated workflows from user descriptions';
COMMENT ON TABLE execution_history IS 'History of workflow executions in n8n';
COMMENT ON TABLE evaluation_metrics IS 'Quality metrics for generated workflows';
COMMENT ON TABLE workflow_embeddings IS 'Vector embeddings for semantic search';
COMMENT ON TABLE workflow_patterns IS 'Recognized patterns in successful workflows';
COMMENT ON TABLE agent_learning_history IS 'Learning data for AI agents';
