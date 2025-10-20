-- Migration 009: Unify Research and Grant IDs Nomenclature
-- Author: Database Manager Agent
-- Date: 2025-10-09
-- Description: Update research_id and grant_id to unified format with RS/GR suffixes

BEGIN;

-- Step 1: Temporarily drop FK constraint to allow updates
ALTER TABLE grants DROP CONSTRAINT IF EXISTS grants_research_id_fkey;

-- Step 2: Update researcher_research IDs
-- Format: RES-#AN-... -> #AN-...-RS-001
UPDATE researcher_research
SET research_id = anketa_id || '-RS-001'
WHERE research_id LIKE 'RES-%' AND anketa_id LIKE '#AN-%';

-- Handle old format without #AN- prefix
UPDATE researcher_research
SET research_id = anketa_id || '-RS-001'
WHERE research_id LIKE 'RES_%' AND anketa_id NOT LIKE '#AN-%';

-- Step 3: Update grants.research_id to match new format
UPDATE grants g
SET research_id = (
    SELECT r.research_id
    FROM researcher_research r
    WHERE r.anketa_id = g.anketa_id
    LIMIT 1
)
WHERE g.research_id LIKE 'RES-%' OR g.research_id LIKE 'RES_%';

-- Step 4: Update grants IDs
-- Format: GRANT-#AN-... -> #AN-...-GR-001
UPDATE grants
SET grant_id = anketa_id || '-GR-001'
WHERE grant_id LIKE 'GRANT-%' AND anketa_id LIKE '#AN-%';

-- Step 5: Recreate FK constraint
ALTER TABLE grants
ADD CONSTRAINT grants_research_id_fkey
FOREIGN KEY (research_id)
REFERENCES researcher_research(research_id)
ON DELETE RESTRICT;

-- Step 3: Handle multiple research/grants per anketa (if any)
-- This will be handled automatically by generate_research_id() and generate_grant_id()
-- when new records are created

-- Step 4: Add comments
COMMENT ON COLUMN researcher_research.research_id IS 'Research ID in format: #AN-YYYYMMDD-identifier-NNN-RS-NNN';
COMMENT ON COLUMN grants.grant_id IS 'Grant ID in format: #AN-YYYYMMDD-identifier-NNN-GR-NNN';

-- Step 5: Verify changes
DO $$
DECLARE
    old_format_research_count INT;
    old_format_grant_count INT;
    new_format_research_count INT;
    new_format_grant_count INT;
BEGIN
    -- Count old format
    SELECT COUNT(*) INTO old_format_research_count
    FROM researcher_research
    WHERE research_id LIKE 'RES-%' OR research_id LIKE 'RES_%';

    SELECT COUNT(*) INTO old_format_grant_count
    FROM grants
    WHERE grant_id LIKE 'GRANT-%';

    -- Count new format
    SELECT COUNT(*) INTO new_format_research_count
    FROM researcher_research
    WHERE research_id LIKE '%-RS-%';

    SELECT COUNT(*) INTO new_format_grant_count
    FROM grants
    WHERE grant_id LIKE '%-GR-%';

    -- Report
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Migration 009 Summary:';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Old format research_id remaining: %', old_format_research_count;
    RAISE NOTICE 'New format research_id (-RS-): %', new_format_research_count;
    RAISE NOTICE 'Old format grant_id remaining: %', old_format_grant_count;
    RAISE NOTICE 'New format grant_id (-GR-): %', new_format_grant_count;
    RAISE NOTICE '==============================================';

    -- Fail if old format still exists
    IF old_format_research_count > 0 THEN
        RAISE WARNING 'Warning: % research records still have old format', old_format_research_count;
    END IF;

    IF old_format_grant_count > 0 THEN
        RAISE WARNING 'Warning: % grant records still have old format', old_format_grant_count;
    END IF;
END $$;

COMMIT;
