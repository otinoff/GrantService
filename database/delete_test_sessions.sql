-- Delete test sessions without real interviews
-- Date: 2025-10-09
-- Description: Remove 26 test sessions that have no user_answers (interview data)
-- Keep only: #AN-20251004-Otinoff-001 (has 15 real answers)

BEGIN;

-- Step 1: Delete grants for test sessions
DELETE FROM grants
WHERE anketa_id IN (
    SELECT s.anketa_id FROM sessions s
    WHERE s.anketa_id LIKE '#AN-%'
        AND NOT EXISTS (SELECT 1 FROM user_answers ua WHERE ua.session_id = s.id)
);

-- Step 2: Delete research for test sessions
DELETE FROM researcher_research
WHERE anketa_id IN (
    SELECT s.anketa_id FROM sessions s
    WHERE s.anketa_id LIKE '#AN-%'
        AND NOT EXISTS (SELECT 1 FROM user_answers ua WHERE ua.session_id = s.id)
);

-- Step 3: Delete test sessions themselves
DELETE FROM sessions
WHERE anketa_id LIKE '#AN-%'
    AND NOT EXISTS (SELECT 1 FROM user_answers ua WHERE ua.session_id = sessions.id);

-- Verification
SELECT
    'Remaining sessions' as type,
    COUNT(*) as count
FROM sessions
WHERE anketa_id LIKE '#AN-%'
UNION ALL
SELECT
    'Remaining research' as type,
    COUNT(*) as count
FROM researcher_research
WHERE anketa_id LIKE '#AN-%'
UNION ALL
SELECT
    'Remaining grants' as type,
    COUNT(*) as count
FROM grants
WHERE anketa_id LIKE '#AN-%';

COMMIT;
