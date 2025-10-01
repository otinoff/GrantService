-- Migration: 003_add_auditor_results.sql
-- Description: Creates auditor_results table for structured quality assessment storage
-- Author: Grant Architect Agent
-- Date: 2025-10-01
-- Status: CRITICAL - Required for pipeline integrity

-- =============================================================================
-- TABLE: auditor_results
-- Purpose: Stores structured quality assessments of grant applications
-- Replaces: JSON field in sessions.audit_result (kept for backward compatibility)
-- =============================================================================

CREATE TABLE IF NOT EXISTS auditor_results (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign Keys
    session_id INTEGER NOT NULL,

    -- Quality Scores (1-10 scale)
    completeness_score INTEGER NOT NULL CHECK(completeness_score >= 1 AND completeness_score <= 10),
    clarity_score INTEGER NOT NULL CHECK(clarity_score >= 1 AND clarity_score <= 10),
    feasibility_score INTEGER NOT NULL CHECK(feasibility_score >= 1 AND feasibility_score <= 10),
    innovation_score INTEGER NOT NULL CHECK(innovation_score >= 1 AND innovation_score <= 10),
    quality_score INTEGER NOT NULL CHECK(quality_score >= 1 AND quality_score <= 10),

    -- Calculated Average
    average_score REAL NOT NULL,

    -- Approval Decision
    approval_status VARCHAR(30) DEFAULT 'pending' CHECK(
        approval_status IN ('pending', 'approved', 'needs_revision', 'rejected')
    ),

    -- Recommendations (JSON format)
    -- Example: {"completeness": {"score": 5, "tips": [...], "examples": [...]}}
    recommendations TEXT,

    -- LLM Metadata
    auditor_llm_provider VARCHAR(50) NOT NULL,
    model VARCHAR(50),

    -- Processing Metadata (JSON format)
    -- Example: {"tokens": 1500, "cost": 0.015, "duration_sec": 3.2}
    metadata TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- =============================================================================
-- INDEXES for Performance
-- =============================================================================

-- Index for session lookup
CREATE INDEX IF NOT EXISTS idx_auditor_session_id
    ON auditor_results(session_id);

-- Index for approval status filtering
CREATE INDEX IF NOT EXISTS idx_auditor_approval_status
    ON auditor_results(approval_status);

-- Index for score-based queries
CREATE INDEX IF NOT EXISTS idx_auditor_average_score
    ON auditor_results(average_score);

-- Index for date-based analytics
CREATE INDEX IF NOT EXISTS idx_auditor_created_at
    ON auditor_results(created_at);

-- Composite index for common queries (status + date)
CREATE INDEX IF NOT EXISTS idx_auditor_status_date
    ON auditor_results(approval_status, created_at);

-- =============================================================================
-- TRIGGERS for Data Integrity
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_auditor_timestamp
    AFTER UPDATE ON auditor_results
    FOR EACH ROW
BEGIN
    UPDATE auditor_results
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Validate average_score calculation
CREATE TRIGGER IF NOT EXISTS validate_auditor_average_score
    BEFORE INSERT ON auditor_results
    FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN ABS(NEW.average_score - (
            (NEW.completeness_score + NEW.clarity_score +
             NEW.feasibility_score + NEW.innovation_score +
             NEW.quality_score) / 5.0
        )) > 0.1
        THEN RAISE(ABORT, 'Average score must equal the mean of all 5 scores')
    END;
END;

-- Auto-set approval_status based on average_score
CREATE TRIGGER IF NOT EXISTS auto_set_approval_status
    BEFORE INSERT ON auditor_results
    FOR EACH ROW
    WHEN NEW.approval_status = 'pending'
BEGIN
    UPDATE auditor_results
    SET approval_status = CASE
        WHEN NEW.average_score >= 6.0 THEN 'approved'
        WHEN NEW.average_score >= 4.0 THEN 'needs_revision'
        ELSE 'rejected'
    END
    WHERE id = NEW.id;
END;

-- =============================================================================
-- VIEWS for Common Queries
-- =============================================================================

-- View: Recent audits with user information
CREATE VIEW IF NOT EXISTS v_recent_audits AS
SELECT
    ar.id,
    ar.session_id,
    s.anketa_id,
    s.telegram_id,
    u.username,
    u.first_name,
    u.last_name,
    ar.completeness_score,
    ar.clarity_score,
    ar.feasibility_score,
    ar.innovation_score,
    ar.quality_score,
    ar.average_score,
    ar.approval_status,
    ar.auditor_llm_provider,
    ar.created_at
FROM auditor_results ar
JOIN sessions s ON ar.session_id = s.id
LEFT JOIN users u ON s.telegram_id = u.telegram_id
ORDER BY ar.created_at DESC;

-- View: Auditor statistics
CREATE VIEW IF NOT EXISTS v_auditor_stats AS
SELECT
    COUNT(*) as total_audits,
    COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved_count,
    COUNT(CASE WHEN approval_status = 'needs_revision' THEN 1 END) as revision_count,
    COUNT(CASE WHEN approval_status = 'rejected' THEN 1 END) as rejected_count,
    ROUND(AVG(average_score), 2) as avg_score,
    ROUND(AVG(completeness_score), 2) as avg_completeness,
    ROUND(AVG(clarity_score), 2) as avg_clarity,
    ROUND(AVG(feasibility_score), 2) as avg_feasibility,
    ROUND(AVG(innovation_score), 2) as avg_innovation,
    ROUND(AVG(quality_score), 2) as avg_quality,
    ROUND(
        COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) * 100.0 / COUNT(*),
        1
    ) as approval_rate_pct
FROM auditor_results
WHERE created_at >= DATE('now', '-30 days');

-- =============================================================================
-- SAMPLE DATA for Testing (commented out - uncomment if needed)
-- =============================================================================

/*
INSERT INTO auditor_results (
    session_id,
    completeness_score,
    clarity_score,
    feasibility_score,
    innovation_score,
    quality_score,
    average_score,
    approval_status,
    recommendations,
    auditor_llm_provider,
    model,
    metadata
) VALUES (
    1,  -- Assuming session with id=1 exists
    8,
    7,
    9,
    6,
    8,
    7.6,
    'approved',
    '{"innovation": {"score": 6, "tips": ["Add more unique value propositions"]}}',
    'gigachat',
    'GigaChat-Pro',
    '{"tokens": 1200, "cost": 0.012, "duration_sec": 2.8}'
);
*/

-- =============================================================================
-- ROLLBACK (if needed)
-- =============================================================================

-- To rollback this migration, run:
-- DROP VIEW IF EXISTS v_auditor_stats;
-- DROP VIEW IF EXISTS v_recent_audits;
-- DROP TRIGGER IF EXISTS auto_set_approval_status;
-- DROP TRIGGER IF EXISTS validate_auditor_average_score;
-- DROP TRIGGER IF EXISTS update_auditor_timestamp;
-- DROP INDEX IF EXISTS idx_auditor_status_date;
-- DROP INDEX IF EXISTS idx_auditor_created_at;
-- DROP INDEX IF EXISTS idx_auditor_average_score;
-- DROP INDEX IF EXISTS idx_auditor_approval_status;
-- DROP INDEX IF EXISTS idx_auditor_session_id;
-- DROP TABLE IF EXISTS auditor_results;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================
