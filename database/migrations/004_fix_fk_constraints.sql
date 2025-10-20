-- Migration 004: Fix Foreign Key Constraints
-- Description: Fix FK constraints that incorrectly reference users.telegram_id instead of users.id
-- Date: 2025-10-06
-- Author: Claude Code (AI Agents Settings Integration)

-- ================================================
-- ISSUE: FK constraints pointing to wrong columns
-- ================================================
-- researcher_research.user_id -> users.telegram_id (WRONG)
-- grants.user_id -> users.telegram_id (WRONG)
-- sent_documents.user_id -> users.telegram_id (WRONG)
--
-- SHOULD BE:
-- researcher_research.user_id -> users.id (CORRECT)
-- grants.user_id -> users.id (CORRECT)
-- sent_documents.user_id -> users.id (CORRECT)

BEGIN;

-- ================================================
-- Step 1: Clean orphaned records
-- ================================================

-- Delete orphaned researcher_research records
DELETE FROM researcher_research
WHERE user_id NOT IN (SELECT id FROM users);

-- Delete orphaned grants records
DELETE FROM grants
WHERE user_id NOT IN (SELECT id FROM users);

-- Delete orphaned sent_documents records
DELETE FROM sent_documents
WHERE user_id NOT IN (SELECT id FROM users);

-- ================================================
-- Step 2: Fix researcher_research FK constraint
-- ================================================

ALTER TABLE researcher_research
DROP CONSTRAINT IF EXISTS researcher_research_user_id_fkey;

ALTER TABLE researcher_research
ADD CONSTRAINT researcher_research_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- ================================================
-- Step 3: Fix grants FK constraint
-- ================================================

ALTER TABLE grants
DROP CONSTRAINT IF EXISTS grants_user_id_fkey;

ALTER TABLE grants
ADD CONSTRAINT grants_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- ================================================
-- Step 4: Fix sent_documents FK constraint
-- ================================================

ALTER TABLE sent_documents
DROP CONSTRAINT IF EXISTS sent_documents_user_id_fkey;

ALTER TABLE sent_documents
ADD CONSTRAINT sent_documents_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- ================================================
-- Step 5: Make user_answers.question_id nullable
-- ================================================
-- ISSUE: AI-powered interviews generate dynamic questions
--        that don't exist in interview_questions table.
--        question_id=NULL is needed for AI-generated answers.

ALTER TABLE user_answers
ALTER COLUMN question_id DROP NOT NULL;

-- ================================================
-- Verification queries
-- ================================================

-- Check all FK constraints on users table
-- SELECT
--     tc.table_name,
--     tc.constraint_name,
--     kcu.column_name,
--     ccu.table_name AS foreign_table,
--     ccu.column_name AS foreign_column
-- FROM information_schema.table_constraints AS tc
-- JOIN information_schema.key_column_usage AS kcu
--   ON tc.constraint_name = kcu.constraint_name
-- JOIN information_schema.constraint_column_usage AS ccu
--   ON ccu.constraint_name = tc.constraint_name
-- WHERE ccu.table_name='users' AND tc.constraint_type = 'FOREIGN KEY';

-- Expected results:
-- researcher_research.user_id -> users.id (CORRECT)
-- grants.user_id -> users.id (CORRECT)
-- sent_documents.user_id -> users.id (CORRECT)
-- sessions.telegram_id -> users.telegram_id (CORRECT - this one is intentional)

COMMIT;

-- ================================================
-- Rollback (if needed)
-- ================================================
-- BEGIN;
--
-- ALTER TABLE researcher_research DROP CONSTRAINT researcher_research_user_id_fkey;
-- ALTER TABLE researcher_research ADD CONSTRAINT researcher_research_user_id_fkey
--   FOREIGN KEY (user_id) REFERENCES users(telegram_id);
--
-- ALTER TABLE grants DROP CONSTRAINT grants_user_id_fkey;
-- ALTER TABLE grants ADD CONSTRAINT grants_user_id_fkey
--   FOREIGN KEY (user_id) REFERENCES users(telegram_id);
--
-- ALTER TABLE sent_documents DROP CONSTRAINT sent_documents_user_id_fkey;
-- ALTER TABLE sent_documents ADD CONSTRAINT sent_documents_user_id_fkey
--   FOREIGN KEY (user_id) REFERENCES users(telegram_id);
--
-- ALTER TABLE user_answers ALTER COLUMN question_id SET NOT NULL;
--
-- COMMIT;
