-- ============================================================
-- Migration 006: Add Stage Tracking System
-- Description: Adds current_stage and agents_passed tracking
--              to track application progress through agent funnel
-- Created: 2025-10-07
-- ============================================================

-- Add stage tracking to sessions table
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS current_stage VARCHAR(50) DEFAULT 'interviewer',
ADD COLUMN IF NOT EXISTS agents_passed TEXT[] DEFAULT ARRAY[]::TEXT[],
ADD COLUMN IF NOT EXISTS stage_history JSONB DEFAULT '[]'::JSONB,
ADD COLUMN IF NOT EXISTS stage_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create index for stage queries
CREATE INDEX IF NOT EXISTS idx_sessions_current_stage ON sessions(current_stage);
CREATE INDEX IF NOT EXISTS idx_sessions_stage_updated ON sessions(stage_updated_at);

-- Add comments
COMMENT ON COLUMN sessions.current_stage IS 'Current agent stage: interviewer, auditor, researcher, writer, reviewer';
COMMENT ON COLUMN sessions.agents_passed IS 'Array of completed agent stages';
COMMENT ON COLUMN sessions.stage_history IS 'JSON array of stage transitions with timestamps';
COMMENT ON COLUMN sessions.stage_updated_at IS 'Last time stage was updated';

-- Add stage tracking to grant_applications table
ALTER TABLE grant_applications
ADD COLUMN IF NOT EXISTS anketa_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS current_stage VARCHAR(50) DEFAULT 'auditor',
ADD COLUMN IF NOT EXISTS agents_passed TEXT[] DEFAULT ARRAY['interviewer']::TEXT[];

-- Create FK constraint to sessions.anketa_id
ALTER TABLE grant_applications
ADD CONSTRAINT fk_grant_applications_anketa
FOREIGN KEY (anketa_id) REFERENCES sessions(anketa_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_grant_applications_anketa ON grant_applications(anketa_id);
CREATE INDEX IF NOT EXISTS idx_grant_applications_current_stage ON grant_applications(current_stage);

-- Add stage tracking to grants table (for reviewer stage)
ALTER TABLE grants
ADD COLUMN IF NOT EXISTS current_stage VARCHAR(50) DEFAULT 'reviewer',
ADD COLUMN IF NOT EXISTS agents_passed TEXT[] DEFAULT ARRAY['interviewer', 'auditor', 'researcher', 'writer']::TEXT[],
ADD COLUMN IF NOT EXISTS review_score INTEGER,
ADD COLUMN IF NOT EXISTS review_feedback TEXT,
ADD COLUMN IF NOT EXISTS final_status VARCHAR(30) DEFAULT 'pending';

CREATE INDEX IF NOT EXISTS idx_grants_current_stage ON grants(current_stage);
CREATE INDEX IF NOT EXISTS idx_grants_final_status ON grants(final_status);

COMMENT ON COLUMN grants.current_stage IS 'Current stage: reviewer or completed';
COMMENT ON COLUMN grants.agents_passed IS 'Array of all completed agent stages';
COMMENT ON COLUMN grants.review_score IS 'Reviewer agent score (1-10)';
COMMENT ON COLUMN grants.review_feedback IS 'Final review feedback from reviewer agent';
COMMENT ON COLUMN grants.final_status IS 'Final status after review: approved, needs_revision, rejected';

-- Add stage tracking helper function
CREATE OR REPLACE FUNCTION update_session_stage(
    p_anketa_id VARCHAR(50),
    p_new_stage VARCHAR(50)
)
RETURNS BOOLEAN AS $$
DECLARE
    v_current_stage VARCHAR(50);
    v_agents_passed TEXT[];
    v_stage_history JSONB;
BEGIN
    -- Get current stage
    SELECT current_stage, agents_passed, stage_history
    INTO v_current_stage, v_agents_passed, v_stage_history
    FROM sessions
    WHERE anketa_id = p_anketa_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Add current stage to agents_passed if not already there
    IF v_current_stage IS NOT NULL AND NOT (v_current_stage = ANY(v_agents_passed)) THEN
        v_agents_passed := array_append(v_agents_passed, v_current_stage);
    END IF;

    -- Add transition to stage_history
    v_stage_history := v_stage_history || jsonb_build_object(
        'from_stage', v_current_stage,
        'to_stage', p_new_stage,
        'timestamp', NOW()
    );

    -- Update session
    UPDATE sessions
    SET
        current_stage = p_new_stage,
        agents_passed = v_agents_passed,
        stage_history = v_stage_history,
        stage_updated_at = NOW()
    WHERE anketa_id = p_anketa_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_session_stage IS 'Update session stage and track history';

-- Add helper function to get stage progress
CREATE OR REPLACE FUNCTION get_stage_progress(p_anketa_id VARCHAR(50))
RETURNS TABLE (
    anketa_id VARCHAR(50),
    current_stage VARCHAR(50),
    agents_passed TEXT[],
    progress_percentage INTEGER,
    stage_emoji TEXT
) AS $$
DECLARE
    v_total_stages INTEGER := 5; -- interviewer, auditor, researcher, writer, reviewer
    v_completed_stages INTEGER;
BEGIN
    SELECT
        s.anketa_id,
        s.current_stage,
        s.agents_passed,
        (array_length(s.agents_passed, 1) * 100 / v_total_stages)::INTEGER,
        CASE s.current_stage
            WHEN 'interviewer' THEN '📝'
            WHEN 'auditor' THEN '✅'
            WHEN 'researcher' THEN '🔍'
            WHEN 'writer' THEN '✍️'
            WHEN 'reviewer' THEN '🔎'
            ELSE '❓'
        END
    INTO
        anketa_id,
        current_stage,
        agents_passed,
        progress_percentage,
        stage_emoji
    FROM sessions s
    WHERE s.anketa_id = p_anketa_id;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_stage_progress IS 'Get detailed stage progress for an anketa';

-- Update existing sessions to have initial stage
UPDATE sessions
SET current_stage = 'interviewer'
WHERE current_stage IS NULL;

-- Update existing grant_applications
UPDATE grant_applications ga
SET
    anketa_id = s.anketa_id,
    current_stage = 'auditor',
    agents_passed = ARRAY['interviewer']
FROM sessions s
WHERE ga.session_id = s.id
  AND ga.anketa_id IS NULL
  AND s.anketa_id IS NOT NULL;

-- Update existing grants
UPDATE grants
SET
    current_stage = CASE
        WHEN status = 'completed' THEN 'completed'
        ELSE 'reviewer'
    END,
    agents_passed = ARRAY['interviewer', 'auditor', 'researcher', 'writer']
WHERE agents_passed IS NULL OR array_length(agents_passed, 1) IS NULL;

-- Verification queries (commented out, uncomment to test)
-- SELECT anketa_id, current_stage, agents_passed, stage_updated_at FROM sessions ORDER BY created_at DESC LIMIT 10;
-- SELECT * FROM get_stage_progress('AN-20251004-theperipherals-014');
-- SELECT update_session_stage('AN-20251004-theperipherals-014', 'researcher');

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 006 completed: Stage tracking system added';
    RAISE NOTICE '   - Added current_stage, agents_passed, stage_history to sessions';
    RAISE NOTICE '   - Added anketa_id, stage tracking to grant_applications';
    RAISE NOTICE '   - Added review fields to grants table';
    RAISE NOTICE '   - Created helper functions: update_session_stage(), get_stage_progress()';
END $$;
