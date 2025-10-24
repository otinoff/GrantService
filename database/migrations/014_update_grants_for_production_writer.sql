-- ============================================================
-- MIGRATION 014: Update grants table for ProductionWriter
-- Server: 5.35.88.251 (Beget VPS)
-- Database: grantservice (PostgreSQL 18, port 5434)
-- Date: 2025-10-24
-- Description: Make research_id nullable and add ProductionWriter metrics
-- ============================================================

-- ============================================================
-- STEP 1: Make research_id NULLABLE
-- ============================================================

-- This allows ProductionWriter to work WITHOUT Researcher phase
ALTER TABLE grants
ALTER COLUMN research_id DROP NOT NULL;

COMMENT ON COLUMN grants.research_id IS 'Research ID (nullable for ProductionWriter workflow without research phase)';

-- ============================================================
-- STEP 2: Add ProductionWriter-specific columns
-- ============================================================

-- Character count (target: 44,000+)
ALTER TABLE grants
ADD COLUMN IF NOT EXISTS character_count INTEGER;

COMMENT ON COLUMN grants.character_count IS 'Grant content length in characters (target: 44K+ for ProductionWriter)';

-- Word count
ALTER TABLE grants
ADD COLUMN IF NOT EXISTS word_count INTEGER;

COMMENT ON COLUMN grants.word_count IS 'Grant content length in words (target: 5K+ words)';

-- Sections generated (usually 10 for ProductionWriter)
ALTER TABLE grants
ADD COLUMN IF NOT EXISTS sections_generated INTEGER DEFAULT 10;

COMMENT ON COLUMN grants.sections_generated IS 'Number of sections generated (ProductionWriter generates 10 sections)';

-- Generation duration in seconds
ALTER TABLE grants
ADD COLUMN IF NOT EXISTS duration_seconds FLOAT;

COMMENT ON COLUMN grants.duration_seconds IS 'Generation time in seconds (target: <180s for ProductionWriter)';

-- Qdrant queries count
ALTER TABLE grants
ADD COLUMN IF NOT EXISTS qdrant_queries INTEGER DEFAULT 0;

COMMENT ON COLUMN grants.qdrant_queries IS 'Number of Qdrant vector DB queries made during generation (usually 5-10)';

-- Sent to user timestamp
ALTER TABLE grants
ADD COLUMN IF NOT EXISTS sent_to_user_at TIMESTAMP;

COMMENT ON COLUMN grants.sent_to_user_at IS 'When the grant was sent to user (for fluent workflow)';

-- Admin notified timestamp
ALTER TABLE grants
ADD COLUMN IF NOT EXISTS admin_notified_at TIMESTAMP;

COMMENT ON COLUMN grants.admin_notified_at IS 'When admins were notified about grant generation';

-- User approval flag
ALTER TABLE grants
ADD COLUMN IF NOT EXISTS user_approved BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN grants.user_approved IS 'Whether user approved the grant (for quality tracking)';

-- Approval timestamp
ALTER TABLE grants
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;

COMMENT ON COLUMN grants.approved_at IS 'When user approved the grant';

-- ============================================================
-- STEP 3: Add indexes for new columns
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_grants_character_count ON grants(character_count) WHERE character_count IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_grants_duration ON grants(duration_seconds) WHERE duration_seconds IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_grants_sent_to_user ON grants(sent_to_user_at) WHERE sent_to_user_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_grants_user_approved ON grants(user_approved) WHERE user_approved = TRUE;

-- ============================================================
-- STEP 4: Update check constraint for status
-- ============================================================

-- Drop old constraint
ALTER TABLE grants DROP CONSTRAINT IF EXISTS grants_status_check;

-- Add new constraint with 'pending' and 'sent_to_user' statuses
ALTER TABLE grants
ADD CONSTRAINT grants_status_check
CHECK (status IN ('draft', 'pending', 'completed', 'sent_to_user', 'submitted', 'approved', 'rejected'));

-- ============================================================
-- STEP 5: Verification queries
-- ============================================================

-- Check that research_id is now nullable
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'grants' AND column_name = 'research_id';

-- Check new columns exist
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'grants'
    AND column_name IN (
        'character_count',
        'word_count',
        'sections_generated',
        'duration_seconds',
        'qdrant_queries',
        'sent_to_user_at',
        'admin_notified_at',
        'user_approved',
        'approved_at'
    )
ORDER BY column_name;

-- Check indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'grants'
    AND indexname LIKE '%character_count%'
    OR indexname LIKE '%duration%'
    OR indexname LIKE '%sent_to_user%'
    OR indexname LIKE '%approved%'
ORDER BY indexname;

-- ============================================================
-- MIGRATION COMPLETED
-- ============================================================

-- Expected result:
-- ✅ research_id is nullable (YES)
-- ✅ 9 new columns added
-- ✅ 4 new indexes created
-- ✅ status constraint updated with 'pending' and 'sent_to_user'

-- Test query: Check grants table structure
\d grants;
