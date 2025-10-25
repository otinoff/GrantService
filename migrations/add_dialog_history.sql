-- Migration: Add dialog_history field to sessions table
-- Iteration: 42
-- Date: 2025-10-25
-- Purpose: Store full conversation history between InteractiveInterviewer and user/simulator

BEGIN;

-- Add dialog_history column
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS dialog_history JSONB DEFAULT '[]'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN sessions.dialog_history IS
'Full conversation history with question-answer pairs. Structure: [{"role": "interviewer"|"user", "text": "...", "timestamp": "...", "field_name": "..."}]';

-- Create index for dialog_history queries
CREATE INDEX IF NOT EXISTS idx_sessions_dialog_history ON sessions USING gin (dialog_history);

COMMIT;

-- Verify the change
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'dialog_history';

-- Success message
SELECT 'sessions.dialog_history JSONB column added successfully' AS status;
