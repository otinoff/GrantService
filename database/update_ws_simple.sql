-- Update WebSearch provider to Claude Code ONLY
UPDATE ai_agent_settings
SET config = config || '{"websearch_provider": "claude_code", "websearch_fallback": null}'::jsonb
WHERE agent_name = 'researcher';

-- Verify
SELECT agent_name,
       config->>'websearch_provider' as provider,
       config->>'websearch_fallback' as fallback
FROM ai_agent_settings
WHERE agent_name = 'researcher';
