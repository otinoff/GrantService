-- Fix VARCHAR(500) limit blocking realistic interview saves
-- Issue: grant_applications.title is VARCHAR(500) but realistic answers are 800-1500+ chars
-- Date: 2025-10-25
-- Iteration: 41

BEGIN;

-- Alter grant_applications.title from VARCHAR(500) to TEXT
ALTER TABLE grant_applications
ALTER COLUMN title TYPE TEXT;

-- Verify change
\d grant_applications

COMMIT;

-- Success message
SELECT 'grant_applications.title changed from VARCHAR(500) to TEXT' AS status;
