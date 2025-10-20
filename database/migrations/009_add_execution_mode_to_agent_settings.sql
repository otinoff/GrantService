-- Migration: Add execution_mode to ai_agent_settings
-- Author: Database Manager Agent
-- Date: 2025-10-09
-- Description: Adds execution_mode column (automatic/manual) to control agent triggering

BEGIN;

-- Add execution_mode column
ALTER TABLE ai_agent_settings
ADD COLUMN IF NOT EXISTS execution_mode VARCHAR(20) DEFAULT 'manual';

-- Create index for faster execution_mode lookups
CREATE INDEX IF NOT EXISTS idx_ai_agent_settings_execution_mode
ON ai_agent_settings(execution_mode);

-- Add comment
COMMENT ON COLUMN ai_agent_settings.execution_mode IS
'Режим запуска агента: automatic (авто-запуск), manual (ручной запуск)';

-- Update all agents to manual mode by default
UPDATE ai_agent_settings
SET execution_mode = 'manual'
WHERE execution_mode IS NULL;

-- Add constraint to ensure only valid values
ALTER TABLE ai_agent_settings
ADD CONSTRAINT check_execution_mode
CHECK (execution_mode IN ('automatic', 'manual'));

COMMIT;
