-- Migration: Add AI agent settings table
-- Author: Database Manager Agent
-- Date: 2025-10-05
-- Description: Creates ai_agent_settings table for storing configuration of AI agents
--              (interviewer, writer, auditor, planner, researcher)

BEGIN;

-- Create table
CREATE TABLE IF NOT EXISTS ai_agent_settings (
    agent_name VARCHAR(50) PRIMARY KEY,
    mode VARCHAR(20) NOT NULL,
    provider VARCHAR(20),
    config JSONB,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100)
);

-- Create index for faster mode lookups
CREATE INDEX IF NOT EXISTS idx_ai_agent_settings_mode ON ai_agent_settings(mode);

-- Add comments
COMMENT ON TABLE ai_agent_settings IS 'Настройки режимов работы AI-агентов';
COMMENT ON COLUMN ai_agent_settings.agent_name IS 'Имя агента: interviewer, writer, auditor, planner, researcher';
COMMENT ON COLUMN ai_agent_settings.mode IS 'Режим работы (для interviewer: structured/ai_powered, для остальных: используется provider)';
COMMENT ON COLUMN ai_agent_settings.provider IS 'LLM провайдер: gigachat, claude_code';
COMMENT ON COLUMN ai_agent_settings.config IS 'Дополнительные параметры в JSON';
COMMENT ON COLUMN ai_agent_settings.updated_at IS 'Время последнего обновления настроек';
COMMENT ON COLUMN ai_agent_settings.updated_by IS 'Кто обновил настройки (telegram_id или username)';

-- Insert default values
INSERT INTO ai_agent_settings (agent_name, mode, provider, config)
VALUES
    ('interviewer', 'structured', NULL, '{"questions_count": 24}'::jsonb),
    ('writer', 'active', 'gigachat', '{"temperature": 0.7}'::jsonb),
    ('auditor', 'active', 'gigachat', '{"temperature": 0.3}'::jsonb),
    ('planner', 'active', 'gigachat', '{"temperature": 0.5}'::jsonb),
    ('researcher', 'active', 'gigachat', '{"temperature": 0.7}'::jsonb)
ON CONFLICT (agent_name) DO NOTHING;

COMMIT;
