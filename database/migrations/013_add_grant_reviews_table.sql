-- Migration 013: Add grant_reviews table
-- Date: 2025-10-13
-- Description: Создание таблицы grant_reviews для хранения независимых экспертных оценок грантов
-- Review - это отдельная оценочная запись с review_id, которая НЕ изменяет грант

-- ==========================================
-- CREATE TABLE grant_reviews
-- ==========================================

CREATE TABLE IF NOT EXISTS grant_reviews (
    id SERIAL PRIMARY KEY,
    review_id VARCHAR(100) UNIQUE NOT NULL,
    grant_id VARCHAR(100) NOT NULL,
    anketa_id VARCHAR(50) NOT NULL,

    -- Основные метрики оценки
    readiness_score DECIMAL(4,2),          -- Общая оценка готовности (0-10)
    approval_probability DECIMAL(5,2),      -- Вероятность одобрения (0-100%)
    can_submit BOOLEAN DEFAULT FALSE,       -- Готовность к подаче
    quality_tier VARCHAR(30),               -- Уровень качества (Excellent/Good/Acceptable/etc)

    -- Критерии оценки (4 критерия с весами)
    evidence_score DECIMAL(4,2),           -- Доказательная база (40%)
    structure_score DECIMAL(4,2),          -- Структура и полнота (30%)
    matching_score DECIMAL(4,2),           -- Индикаторный матчинг (20%)
    economics_score DECIMAL(4,2),          -- Экономическое обоснование (10%)

    -- Детальная оценка (JSON)
    criteria_scores JSONB,                  -- Детальные результаты по каждому критерию

    -- Сильные и слабые стороны
    strengths TEXT[],                       -- Массив сильных сторон
    weaknesses TEXT[],                      -- Массив слабых сторон
    recommendations TEXT[],                 -- Массив рекомендаций по улучшению

    -- Отчеты
    review_content TEXT,                    -- Полный текст review отчета
    review_md_path VARCHAR(255),            -- Путь к MD файлу
    review_pdf_path VARCHAR(255),           -- Путь к PDF файлу

    -- Метаданные
    llm_provider VARCHAR(50) DEFAULT 'claude_code',
    model VARCHAR(100),
    processing_time DECIMAL(8,2),
    tokens_used INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Keys
    FOREIGN KEY (grant_id) REFERENCES grants(grant_id) ON DELETE CASCADE,
    FOREIGN KEY (anketa_id) REFERENCES sessions(anketa_id) ON DELETE RESTRICT
);

-- ==========================================
-- CREATE INDEXES
-- ==========================================

-- Индекс для быстрого поиска по review_id
CREATE INDEX IF NOT EXISTS idx_grant_reviews_review_id ON grant_reviews(review_id);

-- Индекс для поиска reviews по grant_id
CREATE INDEX IF NOT EXISTS idx_grant_reviews_grant_id ON grant_reviews(grant_id);

-- Индекс для поиска всех reviews по anketa_id
CREATE INDEX IF NOT EXISTS idx_grant_reviews_anketa_id ON grant_reviews(anketa_id);

-- Индекс для сортировки по дате
CREATE INDEX IF NOT EXISTS idx_grant_reviews_created_at ON grant_reviews(created_at);

-- Индекс для фильтрации по готовности к подаче
CREATE INDEX IF NOT EXISTS idx_grant_reviews_can_submit ON grant_reviews(can_submit);

-- Индекс для поиска по уровню качества
CREATE INDEX IF NOT EXISTS idx_grant_reviews_quality_tier ON grant_reviews(quality_tier);

-- Индекс для GIN поиска по JSONB
CREATE INDEX IF NOT EXISTS idx_grant_reviews_criteria_gin ON grant_reviews USING gin(criteria_scores);

-- ==========================================
-- ADD COMMENTS
-- ==========================================

COMMENT ON TABLE grant_reviews IS 'Независимые экспертные оценки грантов. Review НЕ изменяет грант, а создает отдельную оценочную запись.';
COMMENT ON COLUMN grant_reviews.review_id IS 'Уникальный ID review в формате #AN-YYYYMMDD-username-NNN-RV-NNN';
COMMENT ON COLUMN grant_reviews.grant_id IS 'ID гранта, который оценивается';
COMMENT ON COLUMN grant_reviews.readiness_score IS 'Общая оценка готовности гранта к подаче (0-10)';
COMMENT ON COLUMN grant_reviews.approval_probability IS 'Вероятность одобрения заявки экспертной комиссией (0-100%)';
COMMENT ON COLUMN grant_reviews.evidence_score IS 'Оценка доказательной базы (0-10, вес 40%)';
COMMENT ON COLUMN grant_reviews.structure_score IS 'Оценка структуры и полноты (0-10, вес 30%)';
COMMENT ON COLUMN grant_reviews.matching_score IS 'Оценка индикаторного матчинга (0-10, вес 20%)';
COMMENT ON COLUMN grant_reviews.economics_score IS 'Оценка экономического обоснования (0-10, вес 10%)';
COMMENT ON COLUMN grant_reviews.strengths IS 'Массив сильных сторон заявки';
COMMENT ON COLUMN grant_reviews.weaknesses IS 'Массив слабых сторон заявки';
COMMENT ON COLUMN grant_reviews.recommendations IS 'Массив рекомендаций по улучшению';
COMMENT ON COLUMN grant_reviews.can_submit IS 'Флаг готовности к подаче (readiness_score >= 7.0)';

-- ==========================================
-- MIGRATION DATA (optional)
-- ==========================================

-- Если в таблице grants есть review_score и review_feedback,
-- можно мигрировать эти данные в grant_reviews (опционально)

-- INSERT INTO grant_reviews (
--     review_id,
--     grant_id,
--     anketa_id,
--     review_feedback,
--     created_at
-- )
-- SELECT
--     grant_id || '-RV-001',
--     grant_id,
--     anketa_id,
--     review_feedback,
--     updated_at
-- FROM grants
-- WHERE review_feedback IS NOT NULL AND review_feedback != '';

-- ==========================================
-- VERIFICATION
-- ==========================================

-- Проверка создания таблицы
SELECT
    'Table created' as status,
    COUNT(*) as column_count
FROM information_schema.columns
WHERE table_name = 'grant_reviews';

-- Проверка индексов
SELECT
    'Indexes created' as status,
    COUNT(*) as index_count
FROM pg_indexes
WHERE tablename = 'grant_reviews';
