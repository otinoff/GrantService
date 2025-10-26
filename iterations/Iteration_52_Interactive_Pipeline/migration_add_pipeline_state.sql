-- Migration: Add pipeline_state to users table
-- Iteration 52: Interactive Step-by-Step Grant Pipeline
-- Created: 2025-10-26

-- Add pipeline_state column
ALTER TABLE users
ADD COLUMN pipeline_state VARCHAR(50) DEFAULT 'idle';

-- Add comment
COMMENT ON COLUMN users.pipeline_state IS 'Current state in grant pipeline: idle, anketa_in_progress, anketa_completed, audit_completed, grant_completed, pipeline_complete';

-- Create index for faster state queries
CREATE INDEX idx_users_pipeline_state ON users(pipeline_state);

-- Add anketa_id_in_progress column (track which anketa is being processed)
ALTER TABLE users
ADD COLUMN anketa_id_in_progress INTEGER DEFAULT NULL;

-- Add foreign key constraint
ALTER TABLE users
ADD CONSTRAINT fk_users_anketa_in_progress
FOREIGN KEY (anketa_id_in_progress)
REFERENCES grants(id)
ON DELETE SET NULL;

-- Add comment
COMMENT ON COLUMN users.anketa_id_in_progress IS 'ID of anketa currently in pipeline (NULL if pipeline idle)';

-- Create index
CREATE INDEX idx_users_anketa_in_progress ON users(anketa_id_in_progress);

-- Add pipeline_started_at timestamp
ALTER TABLE users
ADD COLUMN pipeline_started_at TIMESTAMP DEFAULT NULL;

-- Add comment
COMMENT ON COLUMN users.pipeline_started_at IS 'When user started current pipeline (NULL if idle)';

-- Verify migration
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('pipeline_state', 'anketa_id_in_progress', 'pipeline_started_at');

-- Rollback script (uncomment to rollback):
/*
ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_anketa_in_progress;
DROP INDEX IF EXISTS idx_users_pipeline_state;
DROP INDEX IF EXISTS idx_users_anketa_in_progress;
ALTER TABLE users DROP COLUMN IF EXISTS pipeline_state;
ALTER TABLE users DROP COLUMN IF EXISTS anketa_id_in_progress;
ALTER TABLE users DROP COLUMN IF EXISTS pipeline_started_at;
*/
