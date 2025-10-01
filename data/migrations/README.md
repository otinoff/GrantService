# Database Migrations

This directory contains SQL migration scripts for GrantService database schema updates.

## Migration Files

### 003_add_auditor_results.sql
**Date:** 2025-10-01
**Priority:** CRITICAL
**Description:** Creates `auditor_results` table for structured quality assessment storage

**What it does:**
- Creates table with 5 quality scores (completeness, clarity, feasibility, innovation, quality)
- Adds calculated average_score field
- Implements approval_status logic (approved/needs_revision/rejected)
- Creates indexes for performance
- Adds triggers for data integrity
- Creates views for analytics

**Why it's needed:**
Fills critical gap in pipeline between Interview and Planner stages. Previously, audit results were stored as unstructured JSON in sessions table, making analytics impossible.

**How to apply:**
```bash
sqlite3 data/grantservice.db < data/migrations/003_add_auditor_results.sql
```

**Rollback:**
See bottom of migration file for rollback commands.

---

### 004_add_planner_structures.sql
**Date:** 2025-10-01
**Priority:** CRITICAL
**Description:** Creates `planner_structures` table for grant application structure storage

**What it does:**
- Creates table to store grant section plans (MVP: 7 standard sections)
- Stores structure as JSON with word count targets
- Tracks data mapping from interview questions to sections
- Links to auditor_results (only approved audits get planned)
- Creates indexes and views for analytics

**Why it's needed:**
Planner Agent was completely missing from the system. This creates the bridge between Auditor (quality check) and Researcher (data gathering).

**How to apply:**
```bash
sqlite3 data/grantservice.db < data/migrations/004_add_planner_structures.sql
```

**Rollback:**
See bottom of migration file for rollback commands.

---

## Complete Pipeline After Migrations

```
sessions (Interview)
    ↓
auditor_results (NEW - Quality Assessment)
    ↓
planner_structures (NEW - Structure Generation)
    ↓
researcher_research (Data Enrichment)
    ↓
grants (Final Document)
    ↓
sent_documents (Delivery)
```

## How to Apply All Migrations

### Windows (PowerShell):
```powershell
Get-ChildItem data\migrations\*.sql | ForEach-Object {
    Write-Host "Applying migration: $($_.Name)"
    Get-Content $_.FullName | sqlite3 data\grantservice.db
}
```

### Linux/Mac (Bash):
```bash
for file in data/migrations/*.sql; do
    echo "Applying migration: $file"
    sqlite3 data/grantservice.db < "$file"
done
```

### One by one:
```bash
sqlite3 data/grantservice.db < data/migrations/003_add_auditor_results.sql
sqlite3 data/grantservice.db < data/migrations/004_add_planner_structures.sql
```

## Verify Migrations

Check that new tables exist:
```bash
sqlite3 data/grantservice.db ".tables"
```

Expected output should include:
- auditor_results
- planner_structures
- v_auditor_stats (view)
- v_recent_audits (view)
- v_planner_stats (view)
- v_recent_plans (view)
- v_plans_incomplete_data (view)

## Testing Migrations

Sample test queries:

### Test auditor_results:
```sql
-- Should return 0 rows (table is empty but valid)
SELECT COUNT(*) FROM auditor_results;

-- Check constraints work
INSERT INTO auditor_results (session_id, completeness_score, clarity_score, feasibility_score, innovation_score, quality_score, average_score, auditor_llm_provider)
VALUES (1, 8, 7, 9, 6, 8, 7.6, 'gigachat');

-- Should return 1 row
SELECT * FROM auditor_results;
```

### Test planner_structures:
```sql
-- Should return 0 rows (table is empty but valid)
SELECT COUNT(*) FROM planner_structures;

-- Check JSON validation works (this should succeed)
INSERT INTO planner_structures (session_id, audit_id, structure_json, sections_count)
VALUES (1, 1, '{"sections": [{"id": 1, "title": "Test"}]}', 1);

-- Should return 1 row
SELECT * FROM planner_structures;
```

## Migration History

| Version | Date       | Description                      | Status   |
|---------|------------|----------------------------------|----------|
| 003     | 2025-10-01 | Add auditor_results table        | Applied  |
| 004     | 2025-10-01 | Add planner_structures table     | Applied  |

## Future Migrations

Planned migrations (not yet created):

- 005_add_pipeline_status_tracking.sql
  - Add pipeline_stage field to sessions
  - Add processing timestamps for each stage

- 006_add_grant_templates.sql
  - Templates for different grant types
  - Support for multiple foundations

- 007_add_user_feedback.sql
  - NPS scoring
  - Grant quality feedback from users

---

**Maintained by:** Grant Architect Agent
**Last updated:** 2025-10-01
