-- ============================================================================
-- Expert Agent Knowledge Base Schema
-- ============================================================================
-- Database: grantservice_kb
-- PostgreSQL Version: 14+
-- Extension: pgvector 0.5+
-- Created: 2025-10-17
-- Purpose: Centralized knowledge base for grant application agents
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

-- Vector extension for embeddings and semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- UUID generation (optional, for future use)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE 1: knowledge_sources
-- Purpose: Store information about knowledge sources (articles, documents)
-- ============================================================================

CREATE TABLE knowledge_sources (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Source identification
    fund_name VARCHAR(100) NOT NULL,           -- 'fpg', 'kultura', 'rosmolodjezh', etc.
    source_type VARCHAR(50) NOT NULL,          -- 'official_article', 'example', 'methodical', 'faq'
    title TEXT NOT NULL,                       -- "Статья 84. Раздел О проекте"
    url TEXT,                                   -- https://президентскиегранты.рф/...

    -- Version and status
    version VARCHAR(20),                        -- '2025', '2024', '2023'
    is_active BOOLEAN DEFAULT true,             -- Актуальность источника
    priority INTEGER DEFAULT 5,                 -- 1-10, важность источника

    -- Metadata
    metadata JSONB,                             -- Flexible JSON data

    -- Timestamps
    downloaded_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX idx_sources_fund ON knowledge_sources(fund_name);
CREATE INDEX idx_sources_active ON knowledge_sources(is_active);
CREATE INDEX idx_sources_type ON knowledge_sources(source_type);
CREATE INDEX idx_sources_version ON knowledge_sources(version);
CREATE INDEX idx_sources_priority ON knowledge_sources(priority DESC);

-- Unique constraint: same URL should not be duplicated
CREATE UNIQUE INDEX idx_sources_url_unique ON knowledge_sources(url) WHERE url IS NOT NULL;

-- Comments
COMMENT ON TABLE knowledge_sources IS 'Источники знаний: официальные статьи, примеры, методички';
COMMENT ON COLUMN knowledge_sources.fund_name IS 'Название фонда: fpg, kultura, etc.';
COMMENT ON COLUMN knowledge_sources.source_type IS 'Тип источника: official_article, example, methodical';
COMMENT ON COLUMN knowledge_sources.is_active IS 'Актуальность: false для устаревших источников';

-- ============================================================================
-- TABLE 2: knowledge_sections
-- Purpose: Store individual sections of knowledge (requirements, examples, tips)
-- ============================================================================

CREATE TABLE knowledge_sections (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Foreign key to source
    source_id INTEGER NOT NULL REFERENCES knowledge_sources(id) ON DELETE CASCADE,

    -- Section classification
    section_type VARCHAR(50) NOT NULL,         -- 'requirement', 'example', 'tip', 'criterion', 'faq'
    section_name TEXT NOT NULL,                -- "Цель проекта", "Бюджет", "Команда"

    -- Content
    content TEXT NOT NULL,                     -- Полный текст раздела
    char_limit INTEGER,                        -- Ограничение символов (300, 5000, etc.)

    -- Priority and tags
    priority INTEGER DEFAULT 5,                -- 1-10, важность раздела
    tags TEXT[],                               -- ['smart', 'goals', 'planning']

    -- Metadata
    metadata JSONB,                            -- Flexible JSON data

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_sections_source ON knowledge_sections(source_id);
CREATE INDEX idx_sections_type ON knowledge_sections(section_type);
CREATE INDEX idx_sections_name ON knowledge_sections(section_name);
CREATE INDEX idx_sections_priority ON knowledge_sections(priority DESC);
CREATE INDEX idx_sections_tags ON knowledge_sections USING GIN(tags);

-- Full-text search index (for non-vector fallback)
CREATE INDEX idx_sections_content_fts ON knowledge_sections USING GIN(to_tsvector('russian', content));

-- Comments
COMMENT ON TABLE knowledge_sections IS 'Разделы документов: требования, примеры, советы';
COMMENT ON COLUMN knowledge_sections.section_type IS 'Тип раздела: requirement, example, tip';
COMMENT ON COLUMN knowledge_sections.char_limit IS 'Ограничение символов для этого раздела';
COMMENT ON COLUMN knowledge_sections.tags IS 'Теги для категоризации';

-- ============================================================================
-- TABLE 3: successful_examples
-- Purpose: Store examples of successful grant applications
-- ============================================================================

CREATE TABLE successful_examples (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Application identification
    fund_name VARCHAR(100) NOT NULL,
    application_number VARCHAR(50),            -- Номер заявки (если публичный)
    year INTEGER NOT NULL,                     -- Год победы

    -- Application details
    direction VARCHAR(200),                    -- Направление конкурса
    organization_name VARCHAR(200),            -- Название организации (опционально)
    region VARCHAR(100),                       -- Регион

    -- Financial information
    requested_amount DECIMAL(12, 2),           -- Запрошенная сумма
    awarded_amount DECIMAL(12, 2),             -- Выделенная сумма
    cofinancing_amount DECIMAL(12, 2),         -- Софинансирование

    -- Status
    status VARCHAR(50) DEFAULT 'winner',       -- 'winner', 'finalist', 'recommended'

    -- Content
    full_text TEXT,                            -- Полный текст заявки
    extracted_parts JSONB,                     -- Извлеченные разделы (JSON)

    -- Metadata
    metadata JSONB,                            -- Additional data

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_examples_fund ON successful_examples(fund_name);
CREATE INDEX idx_examples_year ON successful_examples(year);
CREATE INDEX idx_examples_direction ON successful_examples(direction);
CREATE INDEX idx_examples_region ON successful_examples(region);
CREATE INDEX idx_examples_status ON successful_examples(status);
CREATE INDEX idx_examples_amount ON successful_examples(requested_amount);

-- JSONB indexes for extracted_parts
CREATE INDEX idx_examples_parts_gin ON successful_examples USING GIN(extracted_parts);

-- Comments
COMMENT ON TABLE successful_examples IS 'Примеры успешных грантовых заявок';
COMMENT ON COLUMN successful_examples.extracted_parts IS 'JSONB с разделами: project_name, goals, tasks, budget, etc.';

-- Example of extracted_parts structure:
-- {
--   "project_name": "Образовательная робототехника для школьников",
--   "goals": "Организовать дополнительное обучение...",
--   "tasks": ["Разработать программу", "Провести набор", ...],
--   "target_group": "Старшеклассники 10-11 классов",
--   "budget": {"total": 500000, "by_category": {...}},
--   "team": [...]
-- }

-- ============================================================================
-- TABLE 4: evaluation_criteria
-- Purpose: Store evaluation criteria used by expert reviewers
-- ============================================================================

CREATE TABLE evaluation_criteria (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Identification
    fund_name VARCHAR(100) NOT NULL,
    criterion_number INTEGER,                  -- 1-10 для ФПГ
    criterion_name VARCHAR(200) NOT NULL,

    -- Scoring
    max_score INTEGER NOT NULL DEFAULT 10,     -- Максимальный балл (обычно 10)
    weight DECIMAL(3, 2) DEFAULT 1.0,          -- Вес критерия (если применимо)

    -- Content
    description TEXT NOT NULL,                 -- Что оценивается
    examples TEXT,                             -- Примеры хороших практик
    tips TEXT,                                 -- Советы для заявителей
    common_mistakes TEXT,                      -- Частые ошибки

    -- Metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_criteria_fund ON evaluation_criteria(fund_name);
CREATE INDEX idx_criteria_number ON evaluation_criteria(criterion_number);

-- Unique constraint: fund + criterion_number should be unique
CREATE UNIQUE INDEX idx_criteria_fund_number ON evaluation_criteria(fund_name, criterion_number);

-- Comments
COMMENT ON TABLE evaluation_criteria IS 'Критерии оценки заявок экспертами (10 критериев для ФПГ)';
COMMENT ON COLUMN evaluation_criteria.max_score IS 'Максимальный балл (обычно 10)';
COMMENT ON COLUMN evaluation_criteria.weight IS 'Вес критерия (если какие-то важнее)';

-- ============================================================================
-- TABLE 5: knowledge_embeddings
-- Purpose: Store vector embeddings for semantic search
-- ============================================================================

CREATE TABLE knowledge_embeddings (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Foreign key to section
    section_id INTEGER NOT NULL REFERENCES knowledge_sections(id) ON DELETE CASCADE,

    -- Embedding vector
    embedding vector(1536),                    -- 1536 dimensions (ruBERT, OpenAI, etc.)

    -- Model information
    model_name VARCHAR(50) DEFAULT 'rubert',   -- 'rubert', 'sbergpt', 'openai-ada-002'
    model_version VARCHAR(20),                 -- Version of embedding model

    -- Metadata
    metadata JSONB,

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW index for fast vector similarity search
-- m: number of connections (16 is good default)
-- ef_construction: quality of index (64 is good default)
CREATE INDEX idx_embeddings_hnsw ON knowledge_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Index for section lookup
CREATE INDEX idx_embeddings_section ON knowledge_embeddings(section_id);
CREATE INDEX idx_embeddings_model ON knowledge_embeddings(model_name);

-- Unique constraint: one embedding per section per model
CREATE UNIQUE INDEX idx_embeddings_section_model ON knowledge_embeddings(section_id, model_name);

-- Comments
COMMENT ON TABLE knowledge_embeddings IS 'Векторные embeddings для семантического поиска';
COMMENT ON COLUMN knowledge_embeddings.embedding IS 'Вектор 1536 измерений для cosine similarity';
COMMENT ON COLUMN knowledge_embeddings.model_name IS 'Модель: rubert, sbergpt, openai';

-- ============================================================================
-- TABLE 6: knowledge_updates
-- Purpose: Track all updates to the knowledge base (audit log)
-- ============================================================================

CREATE TABLE knowledge_updates (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Who made the update
    updated_by VARCHAR(50) NOT NULL,           -- 'expert_agent', 'researcher', 'admin', 'user:123'

    -- What type of update
    update_type VARCHAR(50) NOT NULL,          -- 'new', 'modified', 'deleted', 'bulk_import', 'rollback'

    -- Description
    description TEXT,                          -- Human-readable description

    -- Affected records
    affected_tables TEXT[],                    -- ['knowledge_sections', 'successful_examples']
    record_ids INTEGER[],                      -- IDs of affected records

    -- Change details (optional)
    old_values JSONB,                          -- Old values (for rollback)
    new_values JSONB,                          -- New values

    -- Metadata
    metadata JSONB,                            -- Additional context

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_updates_by ON knowledge_updates(updated_by);
CREATE INDEX idx_updates_type ON knowledge_updates(update_type);
CREATE INDEX idx_updates_date ON knowledge_updates(created_at DESC);
CREATE INDEX idx_updates_tables ON knowledge_updates USING GIN(affected_tables);

-- Comments
COMMENT ON TABLE knowledge_updates IS 'История обновлений базы знаний (audit log)';
COMMENT ON COLUMN knowledge_updates.updated_by IS 'Кто обновил: expert_agent, researcher, admin';
COMMENT ON COLUMN knowledge_updates.old_values IS 'Старые значения (для отката)';

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View 1: Active knowledge with embeddings
CREATE VIEW v_active_knowledge AS
SELECT
    ks.id,
    ks.fund_name,
    ks.section_type,
    ks.section_name,
    ks.content,
    ks.char_limit,
    ks.priority,
    ks.tags,
    ke.embedding,
    ke.model_name,
    src.title AS source_title,
    src.url AS source_url,
    src.version AS source_version
FROM knowledge_sections ks
JOIN knowledge_sources src ON src.id = ks.source_id
LEFT JOIN knowledge_embeddings ke ON ke.section_id = ks.id
WHERE src.is_active = true;

COMMENT ON VIEW v_active_knowledge IS 'Актуальные знания с embeddings';

-- View 2: Knowledge statistics by fund
CREATE VIEW v_knowledge_stats AS
SELECT
    fund_name,
    COUNT(DISTINCT id) AS total_sources,
    COUNT(DISTINCT CASE WHEN is_active THEN id END) AS active_sources,
    MAX(updated_at) AS last_update,
    MIN(created_at) AS first_created
FROM knowledge_sources
GROUP BY fund_name;

COMMENT ON VIEW v_knowledge_stats IS 'Статистика по фондам';

-- View 3: Recent updates (last 30 days)
CREATE VIEW v_recent_updates AS
SELECT
    id,
    updated_by,
    update_type,
    description,
    array_length(record_ids, 1) AS affected_count,
    created_at
FROM knowledge_updates
WHERE created_at >= NOW() - INTERVAL '30 days'
ORDER BY created_at DESC;

COMMENT ON VIEW v_recent_updates IS 'Обновления за последние 30 дней';

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function 1: Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for auto-updating updated_at
CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON knowledge_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sections_updated_at BEFORE UPDATE ON knowledge_sections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_examples_updated_at BEFORE UPDATE ON successful_examples
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function 2: Search similar sections by vector
CREATE OR REPLACE FUNCTION search_similar_sections(
    query_embedding vector(1536),
    fund_filter VARCHAR(100) DEFAULT NULL,
    top_k INTEGER DEFAULT 5,
    min_similarity FLOAT DEFAULT 0.75
)
RETURNS TABLE (
    section_id INTEGER,
    section_name TEXT,
    content TEXT,
    similarity FLOAT,
    source_title TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ks.id,
        ks.section_name,
        ks.content,
        1 - (ke.embedding <=> query_embedding) AS similarity,
        src.title
    FROM knowledge_sections ks
    JOIN knowledge_sources src ON src.id = ks.source_id
    JOIN knowledge_embeddings ke ON ke.section_id = ks.id
    WHERE
        (fund_filter IS NULL OR src.fund_name = fund_filter)
        AND src.is_active = true
        AND (1 - (ke.embedding <=> query_embedding)) >= min_similarity
    ORDER BY ke.embedding <=> query_embedding
    LIMIT top_k;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION search_similar_sections IS 'Поиск похожих разделов по векторному embedding';

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Insert sample knowledge source
INSERT INTO knowledge_sources (fund_name, source_type, title, url, version, is_active)
VALUES
    ('fpg', 'official_article', 'Статья 84. Раздел О проекте', 'https://президентскиегранты.рф/public/application/item?id=84', '2025', true),
    ('fpg', 'official_article', 'Статья 86. Раздел Команда проекта', 'https://президентскиегранты.рф/public/application/item?id=86', '2025', true),
    ('fpg', 'official_article', 'Статья 87. Раздел Бюджет проекта', 'https://президентскиегранты.рф/public/application/item?id=87', '2025', true);

-- Insert sample knowledge sections
INSERT INTO knowledge_sections (source_id, section_type, section_name, content, char_limit, priority)
VALUES
    (1, 'requirement', 'Название проекта', 'Название проекта должно быть кратким, понятным и отражать суть проекта. Избегайте длинных формулировок.', 300, 10),
    (1, 'requirement', 'Обоснование социальной значимости', 'Необходимо описать проблему, которую решает проект, с указанием статистики и конкретных данных.', 5000, 10),
    (2, 'requirement', 'Руководитель проекта', 'Руководитель проекта должен иметь опыт в реализации подобных проектов.', NULL, 8);

-- Insert sample evaluation criteria
INSERT INTO evaluation_criteria (fund_name, criterion_number, criterion_name, max_score, description, tips)
VALUES
    ('fpg', 1, 'Информационная открытость организации', 10, 'Оценивается наличие сайта, социальных сетей, публикация отчетов.', 'Создайте сайт, ведите соцсети, публикуйте годовые отчеты.'),
    ('fpg', 2, 'Опыт организации по успешной реализации программ', 10, 'Опыт реализации похожих проектов с конкретными результатами.', 'Укажите конкретные цифры и достижения прошлых проектов.'),
    ('fpg', 4, 'Актуальность проблемы и социальная значимость', 10, 'Обоснованность проблемы со статистикой и данными.', 'Используйте официальную статистику, результаты опросов.');

-- Insert sample successful example
INSERT INTO successful_examples (fund_name, year, direction, requested_amount, cofinancing_amount, status, extracted_parts)
VALUES
    ('fpg', 2021, 'Поддержка молодежных проектов', 500000.00, 150000.00, 'winner',
     '{
        "project_name": "Образовательная робототехника для школьников",
        "goals": "Организовать дополнительное обучение робототехнике для 50 старшеклассников города Сарапул",
        "target_group": "Старшеклассники 10-11 классов города Сарапул (450 человек)",
        "tasks": ["Разработать программу обучения", "Провести набор учащихся", "Организовать 36 занятий"],
        "budget": {"total": 500000, "cofinancing": 150000}
     }'::jsonb);

-- ============================================================================
-- GRANTS AND PERMISSIONS (optional, adjust as needed)
-- ============================================================================

-- Create a dedicated user for Expert Agent
-- CREATE USER expert_agent WITH PASSWORD 'secure_password_here';

-- Grant permissions
-- GRANT CONNECT ON DATABASE grantservice_kb TO expert_agent;
-- GRANT USAGE ON SCHEMA public TO expert_agent;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO expert_agent;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO expert_agent;

-- ============================================================================
-- MAINTENANCE
-- ============================================================================

-- Vacuum and analyze for optimal performance
-- Run periodically:
-- VACUUM ANALYZE knowledge_sources;
-- VACUUM ANALYZE knowledge_sections;
-- VACUUM ANALYZE knowledge_embeddings;

-- ============================================================================
-- BACKUP RECOMMENDATIONS
-- ============================================================================

-- Daily backup:
-- pg_dump -U postgres -d grantservice_kb -F c -b -v -f backup_$(date +%Y%m%d).backup

-- Restore:
-- pg_restore -U postgres -d grantservice_kb -v backup_YYYYMMDD.backup

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
