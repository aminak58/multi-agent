-- =====================================================
-- Multi-Agent Trading Bot - Database Initialization
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- Orders Table
-- =====================================================

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID UNIQUE NOT NULL,
    agent VARCHAR(50) NOT NULL,
    pair VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    qty NUMERIC(20, 8) NOT NULL CHECK (qty > 0),
    type VARCHAR(10) NOT NULL CHECK (type IN ('market', 'limit')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'submitted', 'filled', 'cancelled', 'rejected')),
    price NUMERIC(20, 8),
    filled_qty NUMERIC(20, 8) DEFAULT 0,
    avg_price NUMERIC(20, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta JSONB
);

-- Indexes for orders
CREATE INDEX IF NOT EXISTS idx_orders_request_id ON orders(request_id);
CREATE INDEX IF NOT EXISTS idx_orders_agent ON orders(agent);
CREATE INDEX IF NOT EXISTS idx_orders_pair ON orders(pair);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);

-- =====================================================
-- Decisions Table
-- =====================================================

CREATE TABLE IF NOT EXISTS decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    agent VARCHAR(50) NOT NULL,
    pair VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('buy', 'sell', 'hold')),
    confidence NUMERIC(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT,
    llm_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta JSONB
);

-- Indexes for decisions
CREATE INDEX IF NOT EXISTS idx_decisions_request_id ON decisions(request_id);
CREATE INDEX IF NOT EXISTS idx_decisions_agent ON decisions(agent);
CREATE INDEX IF NOT EXISTS idx_decisions_pair ON decisions(pair);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_llm_used ON decisions(llm_used);

-- =====================================================
-- LLM Logs Table
-- =====================================================

CREATE TABLE IF NOT EXISTS llm_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    input_hash VARCHAR(64) NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT,
    model VARCHAR(50) NOT NULL,
    temperature NUMERIC(3, 2),
    tokens_in INTEGER,
    tokens_out INTEGER,
    latency_ms INTEGER,
    status VARCHAR(20) NOT NULL CHECK (status IN ('ok', 'error', 'timeout')),
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta JSONB
);

-- Indexes for llm_logs
CREATE INDEX IF NOT EXISTS idx_llm_logs_request_id ON llm_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_llm_logs_input_hash ON llm_logs(input_hash);
CREATE INDEX IF NOT EXISTS idx_llm_logs_created_at ON llm_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_logs_status ON llm_logs(status);

-- =====================================================
-- Trigger for updated_at
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Views
-- =====================================================

-- Recent orders view
CREATE OR REPLACE VIEW recent_orders AS
SELECT
    id,
    request_id,
    agent,
    pair,
    side,
    qty,
    status,
    created_at
FROM orders
ORDER BY created_at DESC
LIMIT 100;

-- LLM usage statistics view
CREATE OR REPLACE VIEW llm_stats AS
SELECT
    DATE(created_at) as date,
    model,
    status,
    COUNT(*) as call_count,
    AVG(latency_ms) as avg_latency_ms,
    SUM(tokens_in) as total_tokens_in,
    SUM(tokens_out) as total_tokens_out
FROM llm_logs
GROUP BY DATE(created_at), model, status
ORDER BY date DESC;

-- Agent performance view
CREATE OR REPLACE VIEW agent_performance AS
SELECT
    d.agent,
    d.pair,
    COUNT(*) as decision_count,
    AVG(d.confidence) as avg_confidence,
    SUM(CASE WHEN d.llm_used THEN 1 ELSE 0 END) as llm_decisions,
    COUNT(o.id) as orders_placed,
    SUM(CASE WHEN o.status = 'filled' THEN 1 ELSE 0 END) as orders_filled
FROM decisions d
LEFT JOIN orders o ON d.request_id = o.request_id
GROUP BY d.agent, d.pair;

-- =====================================================
-- Grant Permissions
-- =====================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bot_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO bot_user;
GRANT SELECT ON recent_orders, llm_stats, agent_performance TO bot_user;

-- =====================================================
-- Sample Data (for testing)
-- =====================================================

-- Uncomment for dev/test environments
-- INSERT INTO decisions (request_id, agent, pair, action, confidence, reasoning, llm_used) VALUES
-- (gen_random_uuid(), 'signal-agent', 'BTC/USDT', 'buy', 0.85, 'Strong bullish signal', true),
-- (gen_random_uuid(), 'signal-agent', 'ETH/USDT', 'hold', 0.60, 'Neutral market', false);
