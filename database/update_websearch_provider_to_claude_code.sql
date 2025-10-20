-- Update WebSearch provider settings to Claude Code CLI ONLY
-- Date: 2025-10-13
-- Policy: Claude Code CLI as primary and ONLY provider, NO fallback

-- Update researcher agent settings
UPDATE ai_agent_settings
SET config = jsonb_set(
    jsonb_set(
        config,
        '{websearch_provider}',
        '"claude_code"'
    ),
    '{websearch_fallback}',
    'null'
)
WHERE agent_name = 'researcher';

-- Verify update
SELECT
    agent_name,
    config->>'websearch_provider' as websearch_provider,
    config->>'websearch_fallback' as websearch_fallback
FROM ai_agent_settings
WHERE agent_name = 'researcher';
