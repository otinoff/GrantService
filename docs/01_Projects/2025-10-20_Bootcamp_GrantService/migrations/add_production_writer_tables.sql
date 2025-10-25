-- =====================================================
-- PRODUCTION WRITER DATABASE MIGRATION
-- Server: 5.35.88.251 (Beget VPS)
-- Database: grantservice (PostgreSQL 18, port 5434)
-- Date: 2025-10-24
-- =====================================================

-- =====================================================
-- 1. ТАБЛИЦА АНКЕТ
-- =====================================================

CREATE TABLE IF NOT EXISTS anketas (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    telegram_id BIGINT,
    anketa_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Комментарии для документации
COMMENT ON TABLE anketas IS 'Анкеты пользователей для грантовых заявок';
COMMENT ON COLUMN anketas.user_id IS 'ID пользователя в системе';
COMMENT ON COLUMN anketas.telegram_id IS 'Telegram ID пользователя';
COMMENT ON COLUMN anketas.anketa_data IS 'JSON данные анкеты (все поля)';
COMMENT ON COLUMN anketas.status IS 'Статус: draft, in_progress, completed';
COMMENT ON COLUMN anketas.completed_at IS 'Дата завершения анкеты';

-- =====================================================
-- 2. ТАБЛИЦА ГРАНТОВЫХ ЗАЯВОК
-- =====================================================

CREATE TABLE IF NOT EXISTS grant_applications (
    id SERIAL PRIMARY KEY,
    anketa_id INTEGER REFERENCES anketas(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    character_count INTEGER NOT NULL,
    word_count INTEGER,
    sections_generated INTEGER DEFAULT 10,
    duration_seconds FLOAT,
    qdrant_queries INTEGER DEFAULT 0,
    llm_provider VARCHAR(50) DEFAULT 'gigachat',
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    sent_to_user_at TIMESTAMP,
    user_approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP,
    admin_notified_at TIMESTAMP
);

-- Комментарии для документации
COMMENT ON TABLE grant_applications IS 'Сгенерированные грантовые заявки (ProductionWriter)';
COMMENT ON COLUMN grant_applications.anketa_id IS 'Ссылка на анкету';
COMMENT ON COLUMN grant_applications.content IS 'Полный текст грантовой заявки (Markdown)';
COMMENT ON COLUMN grant_applications.character_count IS 'Длина заявки в символах (target: 44K+)';
COMMENT ON COLUMN grant_applications.word_count IS 'Количество слов';
COMMENT ON COLUMN grant_applications.sections_generated IS 'Количество сгенерированных секций (обычно 10)';
COMMENT ON COLUMN grant_applications.duration_seconds IS 'Время генерации в секундах (target: <180s)';
COMMENT ON COLUMN grant_applications.qdrant_queries IS 'Количество запросов к Qdrant (обычно 5-10)';
COMMENT ON COLUMN grant_applications.llm_provider IS 'LLM провайдер (gigachat, claude, etc)';
COMMENT ON COLUMN grant_applications.status IS 'Статус: pending, sent_to_user, approved';

-- =====================================================
-- 3. ИНДЕКСЫ ДЛЯ PERFORMANCE
-- =====================================================

-- Индексы для anketas
CREATE INDEX IF NOT EXISTS idx_anketas_user_id ON anketas(user_id);
CREATE INDEX IF NOT EXISTS idx_anketas_telegram_id ON anketas(telegram_id);
CREATE INDEX IF NOT EXISTS idx_anketas_status ON anketas(status);
CREATE INDEX IF NOT EXISTS idx_anketas_created ON anketas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_anketas_completed ON anketas(completed_at DESC)
    WHERE completed_at IS NOT NULL;

-- Индексы для grant_applications
CREATE INDEX IF NOT EXISTS idx_grants_anketa_id ON grant_applications(anketa_id);
CREATE INDEX IF NOT EXISTS idx_grants_status ON grant_applications(status);
CREATE INDEX IF NOT EXISTS idx_grants_created ON grant_applications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_grants_provider ON grant_applications(llm_provider);

-- Composite index для частых запросов
CREATE INDEX IF NOT EXISTS idx_grants_status_created ON grant_applications(status, created_at DESC);

-- =====================================================
-- 4. ПРОВЕРКА СОЗДАНИЯ ТАБЛИЦ
-- =====================================================

-- Вывести информацию о созданных таблицах
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
    AND table_name IN ('anketas', 'grant_applications')
ORDER BY table_name;

-- Вывести информацию об индексах
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('anketas', 'grant_applications')
ORDER BY tablename, indexname;

-- =====================================================
-- MIGRATION COMPLETED
-- =====================================================

-- Проверка успешности миграции:
-- SELECT COUNT(*) FROM anketas; -- Должно быть 0
-- SELECT COUNT(*) FROM grant_applications; -- Должно быть 0
