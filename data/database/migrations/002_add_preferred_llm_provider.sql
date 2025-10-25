-- Migration: Add preferred_llm_provider to users table
-- Date: 2025-10-21
-- Purpose: Allow users to choose between Claude Code and GigaChat for interviewer

-- Add column for preferred LLM provider
ALTER TABLE users
ADD COLUMN IF NOT EXISTS preferred_llm_provider VARCHAR(50) DEFAULT 'claude_code';

-- Add comment
COMMENT ON COLUMN users.preferred_llm_provider IS 'Предпочитаемый LLM провайдер для интервью: claude_code или gigachat';

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_preferred_llm ON users(preferred_llm_provider);

-- Update existing users to claude_code (default)
UPDATE users
SET preferred_llm_provider = 'claude_code'
WHERE preferred_llm_provider IS NULL;
