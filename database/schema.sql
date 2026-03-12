-- Claude Analytics Platform Database Schema
-- PostgreSQL 16+
-- This schema defines normalized tables for storing Claude Code telemetry data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Employees/Users dimension
CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    practice VARCHAR(100) NOT NULL,
    level VARCHAR(10) NOT NULL,
    location VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User accounts (from telemetry resource data)
CREATE TABLE IF NOT EXISTS user_accounts (
    user_id VARCHAR(64) PRIMARY KEY,
    account_uuid UUID NOT NULL,
    organization_id UUID NOT NULL,
    employee_id INTEGER REFERENCES employees(employee_id),
    hostname VARCHAR(255),
    user_profile VARCHAR(100),
    serial_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Claude models dimension
CREATE TABLE IF NOT EXISTS models (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) UNIQUE NOT NULL,
    model_family VARCHAR(50),  -- opus, sonnet, haiku
    version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tools dimension
CREATE TABLE IF NOT EXISTS tools (
    tool_id SERIAL PRIMARY KEY,
    tool_name VARCHAR(100) UNIQUE NOT NULL,
    tool_category VARCHAR(50),  -- file_ops, search, execution, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions dimension
CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY,
    user_id VARCHAR(64) REFERENCES user_accounts(user_id),
    terminal_type VARCHAR(50),
    os_type VARCHAR(50),
    os_version VARCHAR(50),
    architecture VARCHAR(20),
    claude_code_version VARCHAR(20),
    session_start TIMESTAMP NOT NULL,
    session_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FACT TABLES (Event Data)
-- ============================================================================

-- API Request events
CREATE TABLE IF NOT EXISTS api_requests (
    request_id BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMP NOT NULL,
    session_id UUID REFERENCES sessions(session_id),
    user_id VARCHAR(64) REFERENCES user_accounts(user_id),
    model_id INTEGER REFERENCES models(model_id),
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_creation_tokens INTEGER DEFAULT 0,
    cost_usd NUMERIC(10, 6) NOT NULL,
    duration_ms INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tool Decision events
CREATE TABLE IF NOT EXISTS tool_decisions (
    decision_id BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMP NOT NULL,
    session_id UUID REFERENCES sessions(session_id),
    user_id VARCHAR(64) REFERENCES user_accounts(user_id),
    tool_id INTEGER REFERENCES tools(tool_id),
    decision VARCHAR(20) NOT NULL,  -- accept, reject
    source VARCHAR(50) NOT NULL,    -- config, user_temporary, user_permanent, user_reject
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tool Result events
CREATE TABLE IF NOT EXISTS tool_results (
    result_id BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMP NOT NULL,
    session_id UUID REFERENCES sessions(session_id),
    user_id VARCHAR(64) REFERENCES user_accounts(user_id),
    tool_id INTEGER REFERENCES tools(tool_id),
    decision_type VARCHAR(20) NOT NULL,
    decision_source VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL,
    duration_ms INTEGER NOT NULL,
    result_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Prompt events
CREATE TABLE IF NOT EXISTS user_prompts (
    prompt_id BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMP NOT NULL,
    session_id UUID REFERENCES sessions(session_id),
    user_id VARCHAR(64) REFERENCES user_accounts(user_id),
    prompt_length INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Error events
CREATE TABLE IF NOT EXISTS api_errors (
    error_id BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMP NOT NULL,
    session_id UUID REFERENCES sessions(session_id),
    user_id VARCHAR(64) REFERENCES user_accounts(user_id),
    model_id INTEGER REFERENCES models(model_id),
    error_message TEXT NOT NULL,
    status_code VARCHAR(10),
    attempt INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR QUERY OPTIMIZATION
-- ============================================================================

-- Time-based queries
CREATE INDEX idx_api_requests_timestamp ON api_requests(event_timestamp);
CREATE INDEX idx_tool_decisions_timestamp ON tool_decisions(event_timestamp);
CREATE INDEX idx_tool_results_timestamp ON tool_results(event_timestamp);
CREATE INDEX idx_user_prompts_timestamp ON user_prompts(event_timestamp);
CREATE INDEX idx_api_errors_timestamp ON api_errors(event_timestamp);

-- User-based queries
CREATE INDEX idx_api_requests_user ON api_requests(user_id);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_tool_results_user ON tool_results(user_id);

-- Session-based queries
CREATE INDEX idx_api_requests_session ON api_requests(session_id);
CREATE INDEX idx_tool_results_session ON tool_results(session_id);

-- Model and tool queries
CREATE INDEX idx_api_requests_model ON api_requests(model_id);
CREATE INDEX idx_tool_results_tool ON tool_results(tool_id);

-- Composite indexes for common queries
CREATE INDEX idx_api_requests_user_timestamp ON api_requests(user_id, event_timestamp);
CREATE INDEX idx_api_requests_model_timestamp ON api_requests(model_id, event_timestamp);

-- ============================================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ============================================================================

-- Daily usage summary by user
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_user_usage AS
SELECT
    DATE(ar.event_timestamp) as usage_date,
    ar.user_id,
    e.email,
    e.practice,
    e.level,
    COUNT(*) as request_count,
    SUM(ar.input_tokens) as total_input_tokens,
    SUM(ar.output_tokens) as total_output_tokens,
    SUM(ar.cache_read_tokens) as total_cache_read_tokens,
    SUM(ar.cost_usd) as total_cost,
    AVG(ar.duration_ms) as avg_duration_ms
FROM api_requests ar
JOIN user_accounts ua ON ar.user_id = ua.user_id
JOIN employees e ON ua.employee_id = e.employee_id
GROUP BY DATE(ar.event_timestamp), ar.user_id, e.email, e.practice, e.level;

CREATE UNIQUE INDEX idx_daily_user_usage ON daily_user_usage(usage_date, user_id);

-- Tool usage statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS tool_usage_stats AS
SELECT
    t.tool_name,
    t.tool_category,
    COUNT(*) as usage_count,
    SUM(CASE WHEN tr.success THEN 1 ELSE 0 END) as success_count,
    AVG(tr.duration_ms) as avg_duration_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tr.duration_ms) as median_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY tr.duration_ms) as p95_duration_ms
FROM tool_results tr
JOIN tools t ON tr.tool_id = t.tool_id
GROUP BY t.tool_name, t.tool_category;

CREATE UNIQUE INDEX idx_tool_usage_stats ON tool_usage_stats(tool_name);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for employees table
CREATE TRIGGER update_employees_updated_at BEFORE UPDATE ON employees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Seed common tools
INSERT INTO tools (tool_name, tool_category) VALUES
    ('Read', 'file_ops'),
    ('Write', 'file_ops'),
    ('Edit', 'file_ops'),
    ('Bash', 'execution'),
    ('Grep', 'search'),
    ('Glob', 'search'),
    ('Task', 'workflow'),
    ('TaskCreate', 'workflow'),
    ('TaskUpdate', 'workflow'),
    ('AskUserQuestion', 'interaction'),
    ('WebFetch', 'web'),
    ('WebSearch', 'web'),
    ('mcp_tool', 'integration'),
    ('NotebookEdit', 'file_ops'),
    ('ExitPlanMode', 'workflow'),
    ('TodoWrite', 'workflow'),
    ('ToolSearch', 'search')
ON CONFLICT (tool_name) DO NOTHING;

-- Seed common models
INSERT INTO models (model_name, model_family, version) VALUES
    ('claude-haiku-4-5-20251001', 'haiku', '4.5'),
    ('claude-opus-4-6', 'opus', '4.6'),
    ('claude-opus-4-5-20251101', 'opus', '4.5'),
    ('claude-sonnet-4-5-20250929', 'sonnet', '4.5'),
    ('claude-sonnet-4-6', 'sonnet', '4.6')
ON CONFLICT (model_name) DO NOTHING;

-- Grant permissions (optional, for additional users)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO claude;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO claude;
