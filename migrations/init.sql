CREATE TABLE tools (
    id SERIAL PRIMARY KEY,
    tool_id VARCHAR(64) UNIQUE NOT NULL, -- 工具唯一标识
    description TEXT,
    input_type VARCHAR(32),
    output_type VARCHAR(32),
    params JSONB, -- 参数schema
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);