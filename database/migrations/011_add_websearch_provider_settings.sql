-- Migration: Add WebSearch provider settings to Researcher Agent
-- Author: AI Integration Specialist
-- Date: 2025-10-11
-- Purpose: Add websearch_provider and websearch_fallback to researcher config

BEGIN;

-- Update researcher settings to include WebSearch provider configuration
UPDATE ai_agent_settings
SET config = jsonb_set(
    jsonb_set(
        COALESCE(config, '{}'::jsonb),
        '{websearch_provider}',
        '"perplexity"'
    ),
    '{websearch_fallback}',
    '"claude_code"'
),
updated_at = NOW(),
updated_by = 'migration_011'
WHERE agent_name = 'researcher';

-- Verify the migration
DO $$
DECLARE
    websearch_provider TEXT;
    websearch_fallback TEXT;
BEGIN
    -- Check if websearch_provider was set
    SELECT config->>'websearch_provider', config->>'websearch_fallback'
    INTO websearch_provider, websearch_fallback
    FROM ai_agent_settings
    WHERE agent_name = 'researcher';

    IF websearch_provider = 'perplexity' AND websearch_fallback = 'claude_code' THEN
        RAISE NOTICE '[SUCCESS] Migration 011: websearch_provider=% websearch_fallback=%',
            websearch_provider, websearch_fallback;
    ELSE
        RAISE EXCEPTION '[FAILED] Migration 011: Expected websearch_provider=perplexity websearch_fallback=claude_code, got % %',
            websearch_provider, websearch_fallback;
    END IF;
END $$;

-- Display current researcher configuration
SELECT
    agent_name,
    provider as llm_provider,
    config->>'websearch_provider' as websearch_provider,
    config->>'websearch_fallback' as websearch_fallback,
    config->>'temperature' as temperature,
    updated_at,
    updated_by
FROM ai_agent_settings
WHERE agent_name = 'researcher';

COMMIT;

-- Expected output:
-- agent_name | llm_provider | websearch_provider | websearch_fallback | temperature | updated_at | updated_by
-- -----------|--------------|--------------------|--------------------|-------------|------------|------------
-- researcher | claude_code  | perplexity         | claude_code        | 0.7         | NOW()      | migration_011
