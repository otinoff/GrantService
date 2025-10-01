-- Migration: 004_add_planner_structures.sql
-- Description: Creates planner_structures table for grant application structure storage
-- Author: Grant Architect Agent
-- Date: 2025-10-01
-- Status: CRITICAL - Fills the gap between Auditor and Researcher in pipeline

-- =============================================================================
-- TABLE: planner_structures
-- Purpose: Stores the structured plan for grant application sections
-- Pipeline: Auditor → Planner → Researcher → Writer
-- =============================================================================

CREATE TABLE IF NOT EXISTS planner_structures (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign Keys
    session_id INTEGER NOT NULL,
    audit_id INTEGER NOT NULL,

    -- Structure Data (JSON format)
    -- Example structure in BUSINESS_LOGIC.md Section 2.3
    structure_json TEXT NOT NULL,

    -- Metadata
    sections_count INTEGER DEFAULT 7,
    total_word_count_target INTEGER DEFAULT 1900,
    estimated_pages INTEGER DEFAULT 8,

    -- Data Mapping Status
    data_mapping_complete BOOLEAN DEFAULT FALSE,
    missing_data_sections TEXT,  -- JSON array of section IDs with incomplete data

    -- Template Information
    template_name VARCHAR(100) DEFAULT 'standard_grant_v1',
    template_version VARCHAR(20) DEFAULT '1.0',

    -- LLM Metadata (for future AI-powered planning)
    planner_llm_provider VARCHAR(50),
    model VARCHAR(50),

    -- Processing Metadata (JSON format)
    -- Example: {"tokens": 800, "cost": 0.008, "duration_sec": 2.1}
    metadata TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (audit_id) REFERENCES auditor_results(id) ON DELETE RESTRICT,

    -- Business Rules
    CHECK(sections_count > 0),
    CHECK(total_word_count_target > 0)
);

-- =============================================================================
-- INDEXES for Performance
-- =============================================================================

-- Index for session lookup
CREATE INDEX IF NOT EXISTS idx_planner_session_id
    ON planner_structures(session_id);

-- Index for audit lookup
CREATE INDEX IF NOT EXISTS idx_planner_audit_id
    ON planner_structures(audit_id);

-- Index for template-based queries
CREATE INDEX IF NOT EXISTS idx_planner_template
    ON planner_structures(template_name);

-- Index for data mapping status
CREATE INDEX IF NOT EXISTS idx_planner_data_mapping
    ON planner_structures(data_mapping_complete);

-- Index for date-based analytics
CREATE INDEX IF NOT EXISTS idx_planner_created_at
    ON planner_structures(created_at);

-- Composite index for common queries (session + mapping status)
CREATE INDEX IF NOT EXISTS idx_planner_session_mapping
    ON planner_structures(session_id, data_mapping_complete);

-- =============================================================================
-- TRIGGERS for Data Integrity
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_planner_timestamp
    AFTER UPDATE ON planner_structures
    FOR EACH ROW
BEGIN
    UPDATE planner_structures
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Validate structure_json is valid JSON
CREATE TRIGGER IF NOT EXISTS validate_planner_structure_json
    BEFORE INSERT ON planner_structures
    FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN json_valid(NEW.structure_json) = 0
        THEN RAISE(ABORT, 'structure_json must be valid JSON')
    END;
END;

-- Auto-update sections_count from structure_json
CREATE TRIGGER IF NOT EXISTS auto_update_sections_count
    BEFORE INSERT ON planner_structures
    FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.sections_count != json_array_length(json_extract(NEW.structure_json, '$.sections'))
        THEN RAISE(ABORT, 'sections_count must match actual sections in JSON')
    END;
END;

-- =============================================================================
-- VIEWS for Common Queries
-- =============================================================================

-- View: Recent plans with session and audit info
CREATE VIEW IF NOT EXISTS v_recent_plans AS
SELECT
    ps.id,
    ps.session_id,
    s.anketa_id,
    s.telegram_id,
    u.username,
    u.first_name,
    u.last_name,
    ar.average_score as audit_score,
    ar.approval_status as audit_status,
    ps.sections_count,
    ps.total_word_count_target,
    ps.data_mapping_complete,
    ps.template_name,
    ps.created_at
FROM planner_structures ps
JOIN sessions s ON ps.session_id = s.id
JOIN auditor_results ar ON ps.audit_id = ar.id
LEFT JOIN users u ON s.telegram_id = u.telegram_id
ORDER BY ps.created_at DESC;

-- View: Planner statistics
CREATE VIEW IF NOT EXISTS v_planner_stats AS
SELECT
    COUNT(*) as total_plans,
    COUNT(CASE WHEN data_mapping_complete = 1 THEN 1 END) as complete_mappings,
    ROUND(AVG(sections_count), 1) as avg_sections,
    ROUND(AVG(total_word_count_target), 0) as avg_word_target,
    template_name,
    COUNT(*) as template_usage_count
FROM planner_structures
WHERE created_at >= DATE('now', '-30 days')
GROUP BY template_name;

-- View: Plans with missing data
CREATE VIEW IF NOT EXISTS v_plans_incomplete_data AS
SELECT
    ps.id,
    s.anketa_id,
    u.username,
    ps.missing_data_sections,
    ps.sections_count,
    json_array_length(ps.missing_data_sections) as missing_sections_count,
    ps.created_at
FROM planner_structures ps
JOIN sessions s ON ps.session_id = s.id
LEFT JOIN users u ON s.telegram_id = u.telegram_id
WHERE ps.data_mapping_complete = 0
    AND ps.missing_data_sections IS NOT NULL
ORDER BY ps.created_at DESC;

-- =============================================================================
-- HELPER FUNCTIONS (SQLite doesn't support UDFs, but we can use JSON functions)
-- =============================================================================

-- Example: Extract section titles from structure_json
-- Usage: SELECT json_extract(structure_json, '$.sections[*].title') FROM planner_structures;

-- Example: Count sections with missing data
-- Usage: SELECT json_array_length(missing_data_sections) FROM planner_structures;

-- =============================================================================
-- STANDARD TEMPLATES (for MVP)
-- =============================================================================

-- MVP Template: Standard Grant Application (7 sections)
-- This is inserted into structure_json field

/*
STANDARD TEMPLATE STRUCTURE:
{
  "sections": [
    {
      "id": 1,
      "title": "Описание проблемы",
      "description": "Анализ текущей ситуации и обоснование актуальности",
      "word_count_target": 300,
      "data_sources": [1, 2, 3, 6]
    },
    {
      "id": 2,
      "title": "Целевая аудитория и география",
      "description": "Кто получит пользу и где",
      "word_count_target": 200,
      "data_sources": [4, 5]
    },
    {
      "id": 3,
      "title": "Цели и задачи проекта",
      "description": "Что мы хотим достичь и как",
      "word_count_target": 250,
      "data_sources": [7, 8, 9]
    },
    {
      "id": 4,
      "title": "Методы и механизмы реализации",
      "description": "Конкретные шаги и инструменты",
      "word_count_target": 400,
      "data_sources": [10, 11, 12]
    },
    {
      "id": 5,
      "title": "Команда и партнёры",
      "description": "Кто реализует проект",
      "word_count_target": 200,
      "data_sources": [13, 14, 15]
    },
    {
      "id": 6,
      "title": "Бюджет проекта",
      "description": "Финансовый план и обоснование",
      "word_count_target": 300,
      "data_sources": [16, 17, 18]
    },
    {
      "id": 7,
      "title": "Ожидаемые результаты и оценка",
      "description": "Измеримые показатели эффективности",
      "word_count_target": 250,
      "data_sources": [19, 20, 21, 22]
    }
  ],
  "total_estimated_words": 1900,
  "estimated_pages": 8
}
*/

-- =============================================================================
-- SAMPLE DATA for Testing (commented out - uncomment if needed)
-- =============================================================================

/*
INSERT INTO planner_structures (
    session_id,
    audit_id,
    structure_json,
    sections_count,
    total_word_count_target,
    estimated_pages,
    data_mapping_complete,
    template_name,
    template_version
) VALUES (
    1,  -- Assuming session with id=1 exists
    1,  -- Assuming audit with id=1 exists
    '{
      "sections": [
        {"id": 1, "title": "Описание проблемы", "word_count_target": 300, "data_sources": [1, 2, 3]},
        {"id": 2, "title": "Целевая аудитория", "word_count_target": 200, "data_sources": [4, 5]},
        {"id": 3, "title": "Цели и задачи", "word_count_target": 250, "data_sources": [7, 8]},
        {"id": 4, "title": "Методы реализации", "word_count_target": 400, "data_sources": [10, 11]},
        {"id": 5, "title": "Команда", "word_count_target": 200, "data_sources": [13, 14]},
        {"id": 6, "title": "Бюджет", "word_count_target": 300, "data_sources": [16, 17]},
        {"id": 7, "title": "Результаты", "word_count_target": 250, "data_sources": [19, 20]}
      ]
    }',
    7,
    1900,
    8,
    1,
    'standard_grant_v1',
    '1.0'
);
*/

-- =============================================================================
-- ROLLBACK (if needed)
-- =============================================================================

-- To rollback this migration, run:
-- DROP VIEW IF EXISTS v_plans_incomplete_data;
-- DROP VIEW IF EXISTS v_planner_stats;
-- DROP VIEW IF EXISTS v_recent_plans;
-- DROP TRIGGER IF EXISTS auto_update_sections_count;
-- DROP TRIGGER IF EXISTS validate_planner_structure_json;
-- DROP TRIGGER IF EXISTS update_planner_timestamp;
-- DROP INDEX IF EXISTS idx_planner_session_mapping;
-- DROP INDEX IF EXISTS idx_planner_created_at;
-- DROP INDEX IF EXISTS idx_planner_data_mapping;
-- DROP INDEX IF EXISTS idx_planner_template;
-- DROP INDEX IF EXISTS idx_planner_audit_id;
-- DROP INDEX IF EXISTS idx_planner_session_id;
-- DROP TABLE IF EXISTS planner_structures;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================
