-- ============================================================================
-- Migration: Add Expert Agent Knowledge Base Tables
-- ============================================================================
-- Migration Number: 012
-- Author: grant-architect agent
-- Date: 2025-10-17
-- Purpose: Add tables for Expert Agent (knowledge base, embeddings, etc.)
-- Database: grantservice (existing)
-- Dependencies: Extension pgvector (will be installed if not exists)
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Install pgvector extension
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

COMMENT ON EXTENSION vector IS 'Vector similarity search for pgvector (Expert Agent embeddings)';

-- ============================================================================
-- STEP 2: Create knowledge_sources table
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_sources (
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_sources_fund ON knowledge_sources(fund_name);
CREATE INDEX IF NOT EXISTS idx_knowledge_sources_active ON knowledge_sources(is_active);
CREATE INDEX IF NOT EXISTS idx_knowledge_sources_type ON knowledge_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_sources_version ON knowledge_sources(version);
CREATE INDEX IF NOT EXISTS idx_knowledge_sources_priority ON knowledge_sources(priority DESC);

-- Unique constraint
CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_sources_url_unique
ON knowledge_sources(url) WHERE url IS NOT NULL;

-- Comments
COMMENT ON TABLE knowledge_sources IS 'Expert Agent: Источники знаний (статьи, примеры, методички)';
COMMENT ON COLUMN knowledge_sources.fund_name IS 'Название фонда: fpg, kultura, etc.';
COMMENT ON COLUMN knowledge_sources.source_type IS 'Тип источника: official_article, example, methodical';
COMMENT ON COLUMN knowledge_sources.is_active IS 'Актуальность: false для устаревших источников';

-- ============================================================================
-- STEP 3: Create knowledge_sections table
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_sections (
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
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_sections_source ON knowledge_sections(source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_sections_type ON knowledge_sections(section_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_sections_name ON knowledge_sections(section_name);
CREATE INDEX IF NOT EXISTS idx_knowledge_sections_priority ON knowledge_sections(priority DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_sections_tags ON knowledge_sections USING GIN(tags);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_knowledge_sections_content_fts
ON knowledge_sections USING GIN(to_tsvector('russian', content));

-- Comments
COMMENT ON TABLE knowledge_sections IS 'Expert Agent: Разделы документов (требования, примеры, советы)';
COMMENT ON COLUMN knowledge_sections.section_type IS 'Тип раздела: requirement, example, tip';
COMMENT ON COLUMN knowledge_sections.char_limit IS 'Ограничение символов для этого раздела';

-- ============================================================================
-- STEP 4: Create successful_grant_examples table
-- ============================================================================

CREATE TABLE IF NOT EXISTS successful_grant_examples (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Application identification
    fund_name VARCHAR(100) NOT NULL,
    application_number VARCHAR(50),            -- Номер заявки (если публичный)
    year INTEGER NOT NULL,                     -- Год победы

    -- Application details
    direction VARCHAR(200),                    -- Направление конкурса
    organization_name VARCHAR(200),            -- Название организации
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
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_successful_examples_fund ON successful_grant_examples(fund_name);
CREATE INDEX IF NOT EXISTS idx_successful_examples_year ON successful_grant_examples(year);
CREATE INDEX IF NOT EXISTS idx_successful_examples_direction ON successful_grant_examples(direction);
CREATE INDEX IF NOT EXISTS idx_successful_examples_region ON successful_grant_examples(region);
CREATE INDEX IF NOT EXISTS idx_successful_examples_status ON successful_grant_examples(status);
CREATE INDEX IF NOT EXISTS idx_successful_examples_amount ON successful_grant_examples(requested_amount);

-- JSONB indexes
CREATE INDEX IF NOT EXISTS idx_successful_examples_parts_gin
ON successful_grant_examples USING GIN(extracted_parts);

-- Comments
COMMENT ON TABLE successful_grant_examples IS 'Expert Agent: Примеры успешных грантовых заявок';
COMMENT ON COLUMN successful_grant_examples.extracted_parts IS 'JSONB: project_name, goals, tasks, budget, etc.';

-- ============================================================================
-- STEP 5: Create evaluation_criteria table
-- ============================================================================

CREATE TABLE IF NOT EXISTS evaluation_criteria (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Identification
    fund_name VARCHAR(100) NOT NULL,
    criterion_number INTEGER,                  -- 1-10 для ФПГ
    criterion_name VARCHAR(200) NOT NULL,

    -- Scoring
    max_score INTEGER NOT NULL DEFAULT 10,     -- Макс. баллов (обычно 10)
    weight DECIMAL(3, 2) DEFAULT 1.0,          -- Вес критерия

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
CREATE INDEX IF NOT EXISTS idx_evaluation_criteria_fund ON evaluation_criteria(fund_name);
CREATE INDEX IF NOT EXISTS idx_evaluation_criteria_number ON evaluation_criteria(criterion_number);

-- Unique constraint
CREATE UNIQUE INDEX IF NOT EXISTS idx_evaluation_criteria_fund_number
ON evaluation_criteria(fund_name, criterion_number);

-- Comments
COMMENT ON TABLE evaluation_criteria IS 'Expert Agent: Критерии оценки заявок экспертами';
COMMENT ON COLUMN evaluation_criteria.max_score IS 'Максимальный балл (обычно 10)';

-- ============================================================================
-- STEP 6: Create knowledge_embeddings table (VECTOR!)
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Foreign key to section
    section_id INTEGER NOT NULL REFERENCES knowledge_sections(id) ON DELETE CASCADE,

    -- Embedding vector (1536 dimensions for ruBERT/OpenAI)
    embedding vector(1536),

    -- Model information
    model_name VARCHAR(50) DEFAULT 'rubert',   -- 'rubert', 'sbergpt', 'openai-ada-002'
    model_version VARCHAR(20),

    -- Metadata
    metadata JSONB,

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW index for fast vector similarity search
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_hnsw
ON knowledge_embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Regular indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_section ON knowledge_embeddings(section_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_model ON knowledge_embeddings(model_name);

-- Unique constraint
CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_embeddings_section_model
ON knowledge_embeddings(section_id, model_name);

-- Comments
COMMENT ON TABLE knowledge_embeddings IS 'Expert Agent: Векторные embeddings для семантического поиска';
COMMENT ON COLUMN knowledge_embeddings.embedding IS 'Вектор 1536 измерений для cosine similarity';
COMMENT ON COLUMN knowledge_embeddings.model_name IS 'Модель: rubert, sbergpt, openai';

-- ============================================================================
-- STEP 7: Create knowledge_updates table (audit log)
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_updates (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Who made the update
    updated_by VARCHAR(50) NOT NULL,           -- 'expert_agent', 'researcher', 'admin', 'user:123'

    -- What type of update
    update_type VARCHAR(50) NOT NULL,          -- 'new', 'modified', 'deleted', 'bulk_import', 'rollback'

    -- Description
    description TEXT,

    -- Affected records
    affected_tables TEXT[],                    -- ['knowledge_sections', 'successful_grant_examples']
    record_ids INTEGER[],                      -- IDs of affected records

    -- Change details
    old_values JSONB,                          -- Old values (for rollback)
    new_values JSONB,                          -- New values

    -- Metadata
    metadata JSONB,

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_updates_by ON knowledge_updates(updated_by);
CREATE INDEX IF NOT EXISTS idx_knowledge_updates_type ON knowledge_updates(update_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_updates_date ON knowledge_updates(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_updates_tables ON knowledge_updates USING GIN(affected_tables);

-- Comments
COMMENT ON TABLE knowledge_updates IS 'Expert Agent: История обновлений базы знаний (audit log)';
COMMENT ON COLUMN knowledge_updates.updated_by IS 'Кто обновил: expert_agent, researcher, admin';

-- ============================================================================
-- STEP 8: Create views for convenience
-- ============================================================================

-- View: Active knowledge with embeddings
CREATE OR REPLACE VIEW v_expert_active_knowledge AS
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

COMMENT ON VIEW v_expert_active_knowledge IS 'Expert Agent: Актуальные знания с embeddings';

-- View: Knowledge statistics by fund
CREATE OR REPLACE VIEW v_expert_knowledge_stats AS
SELECT
    fund_name,
    COUNT(DISTINCT id) AS total_sources,
    COUNT(DISTINCT CASE WHEN is_active THEN id END) AS active_sources,
    MAX(updated_at) AS last_update,
    MIN(created_at) AS first_created
FROM knowledge_sources
GROUP BY fund_name;

COMMENT ON VIEW v_expert_knowledge_stats IS 'Expert Agent: Статистика по фондам';

-- View: Recent updates (last 30 days)
CREATE OR REPLACE VIEW v_expert_recent_updates AS
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

COMMENT ON VIEW v_expert_recent_updates IS 'Expert Agent: Обновления за последние 30 дней';

-- ============================================================================
-- STEP 9: Create trigger for auto-updating updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_expert_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER trg_knowledge_sources_updated_at
BEFORE UPDATE ON knowledge_sources
FOR EACH ROW EXECUTE FUNCTION update_expert_updated_at_column();

CREATE TRIGGER trg_knowledge_sections_updated_at
BEFORE UPDATE ON knowledge_sections
FOR EACH ROW EXECUTE FUNCTION update_expert_updated_at_column();

CREATE TRIGGER trg_successful_examples_updated_at
BEFORE UPDATE ON successful_grant_examples
FOR EACH ROW EXECUTE FUNCTION update_expert_updated_at_column();

CREATE TRIGGER trg_evaluation_criteria_updated_at
BEFORE UPDATE ON evaluation_criteria
FOR EACH ROW EXECUTE FUNCTION update_expert_updated_at_column();

-- ============================================================================
-- STEP 10: Create search function for semantic search
-- ============================================================================

CREATE OR REPLACE FUNCTION expert_search_similar_sections(
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

COMMENT ON FUNCTION expert_search_similar_sections IS 'Expert Agent: Поиск похожих разделов по векторному embedding';

-- ============================================================================
-- STEP 11: Add Expert Agent to ai_agent_settings (if table exists)
-- ============================================================================

-- Check if ai_agent_settings exists and add expert agent
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_agent_settings') THEN
        -- Add expert agent settings
        INSERT INTO ai_agent_settings (agent_name, mode, provider, config)
        VALUES ('expert', 'active', 'claude_code',
                '{"temperature": 0.5, "embedding_model": "rubert", "vector_search_threshold": 0.75}'::jsonb)
        ON CONFLICT (agent_name) DO NOTHING;

        RAISE NOTICE 'Expert agent added to ai_agent_settings';
    ELSE
        RAISE NOTICE 'Table ai_agent_settings does not exist, skipping agent registration';
    END IF;
END $$;

-- ============================================================================
-- STEP 12: Insert sample data for testing
-- ============================================================================

-- Sample knowledge sources
INSERT INTO knowledge_sources (fund_name, source_type, title, url, version, is_active)
VALUES
    ('fpg', 'official_article', 'Статья 84. Раздел О проекте',
     'https://президентскиегранты.рф/public/application/item?id=84', '2025', true),
    ('fpg', 'official_article', 'Статья 86. Раздел Команда проекта',
     'https://президентскиегранты.рф/public/application/item?id=86', '2025', true),
    ('fpg', 'official_article', 'Статья 87. Раздел Бюджет проекта',
     'https://президентскиегранты.рф/public/application/item?id=87', '2025', true)
ON CONFLICT DO NOTHING;

-- Sample knowledge sections
INSERT INTO knowledge_sections (source_id, section_type, section_name, content, char_limit, priority)
SELECT
    src.id,
    'requirement',
    'Название проекта',
    'Название проекта должно быть кратким, понятным и отражать суть проекта. Избегайте длинных формулировок.',
    300,
    10
FROM knowledge_sources src
WHERE src.title = 'Статья 84. Раздел О проекте' AND src.version = '2025'
LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_sections (source_id, section_type, section_name, content, char_limit, priority)
SELECT
    src.id,
    'requirement',
    'Обоснование социальной значимости',
    'Необходимо описать проблему, которую решает проект, с указанием статистики и конкретных данных.',
    5000,
    10
FROM knowledge_sources src
WHERE src.title = 'Статья 84. Раздел О проекте' AND src.version = '2025'
LIMIT 1
ON CONFLICT DO NOTHING;

-- Sample evaluation criteria
INSERT INTO evaluation_criteria (fund_name, criterion_number, criterion_name, max_score, description, tips)
VALUES
    ('fpg', 1, 'Информационная открытость организации', 10,
     'Оценивается наличие сайта, социальных сетей, публикация отчетов.',
     'Создайте сайт, ведите соцсети, публикуйте годовые отчеты.'),
    ('fpg', 2, 'Опыт организации по успешной реализации программ', 10,
     'Опыт реализации похожих проектов с конкретными результатами.',
     'Укажите конкретные цифры и достижения прошлых проектов.'),
    ('fpg', 4, 'Актуальность проблемы и социальная значимость', 10,
     'Обоснованность проблемы со статистикой и данными.',
     'Используйте официальную статистику, результаты опросов.')
ON CONFLICT DO NOTHING;

-- Sample successful example
INSERT INTO successful_grant_examples (fund_name, year, direction, requested_amount, cofinancing_amount, status, extracted_parts)
VALUES
    ('fpg', 2021, 'Поддержка молодежных проектов', 500000.00, 150000.00, 'winner',
     '{
        "project_name": "Образовательная робототехника для школьников",
        "goals": "Организовать дополнительное обучение робототехнике для 50 старшеклассников города Сарапул",
        "target_group": "Старшеклассники 10-11 классов города Сарапул (450 человек)",
        "tasks": ["Разработать программу обучения", "Провести набор учащихся", "Организовать 36 занятий"],
        "budget": {"total": 500000, "cofinancing": 150000}
     }'::jsonb)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- STEP 13: Verify installation
-- ============================================================================

DO $$
DECLARE
    sources_count INTEGER;
    sections_count INTEGER;
    criteria_count INTEGER;
    examples_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO sources_count FROM knowledge_sources;
    SELECT COUNT(*) INTO sections_count FROM knowledge_sections;
    SELECT COUNT(*) INTO evaluation_criteria FROM evaluation_criteria;
    SELECT COUNT(*) INTO examples_count FROM successful_grant_examples;

    RAISE NOTICE '============================================';
    RAISE NOTICE 'Expert Agent Migration 012 Complete!';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - knowledge_sources: % records', sources_count;
    RAISE NOTICE '  - knowledge_sections: % records', sections_count;
    RAISE NOTICE '  - evaluation_criteria: % records', criteria_count;
    RAISE NOTICE '  - successful_grant_examples: % records', examples_count;
    RAISE NOTICE '  - knowledge_embeddings: ready for data';
    RAISE NOTICE '  - knowledge_updates: ready for logging';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'pgvector extension: INSTALLED';
    RAISE NOTICE 'Vector dimension: 1536';
    RAISE NOTICE 'Search function: expert_search_similar_sections()';
    RAISE NOTICE '============================================';
END $$;

COMMIT;

-- ============================================================================
-- END OF MIGRATION 012
-- ============================================================================
