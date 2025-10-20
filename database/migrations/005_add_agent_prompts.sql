-- Migration 005: AI Agent Prompts Management System
-- Дата: 2025-10-06
-- Описание: Система управления промптами для AI-агентов
-- Примечание: Таблица называется ai_ai_agent_prompts, т.к. ai_agent_prompts уже существует в migration 001

-- ============================================================================
-- Таблица ai_ai_agent_prompts - хранение промптов для AI-агентов
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_ai_agent_prompts (
    id SERIAL PRIMARY KEY,

    -- Идентификация промпта
    agent_name VARCHAR(50) NOT NULL,          -- 'auditor', 'planner', 'writer', etc.
    prompt_type VARCHAR(100) NOT NULL,        -- 'evaluation', 'quick_score', 'structure', etc.
    prompt_key VARCHAR(150) NOT NULL UNIQUE,  -- 'auditor_evaluation', 'planner_structure' (составной ключ)

    -- Содержимое промпта
    prompt_text TEXT NOT NULL,                -- Текст промпта с плейсхолдерами {variable}
    prompt_description TEXT,                  -- Описание назначения промпта

    -- Переменные промпта (для подстановки)
    variables JSONB,                          -- {'project_data': 'string', 'word_count': 'int', ...}
    example_output JSONB,                     -- Пример ожидаемого результата

    -- Метаданные
    llm_provider VARCHAR(20) DEFAULT 'gigachat',  -- 'gigachat', 'claude_code', 'openai'
    model VARCHAR(50),                            -- 'GigaChat-Pro', 'claude-3-opus', etc.
    temperature DECIMAL(3,2) DEFAULT 0.7,         -- Параметр креативности LLM
    max_tokens INTEGER DEFAULT 4000,              -- Максимум токенов для ответа

    -- Версионирование
    version INTEGER DEFAULT 1,                -- Версия промпта
    is_active BOOLEAN DEFAULT TRUE,           -- Активен ли промпт
    is_default BOOLEAN DEFAULT FALSE,         -- Используется по умолчанию

    -- Статистика использования
    usage_count INTEGER DEFAULT 0,            -- Сколько раз использовался
    last_used_at TIMESTAMP,                   -- Последнее использование
    avg_score DECIMAL(3,2),                   -- Средняя оценка результатов

    -- Аудит
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),                  -- Кто создал
    updated_by VARCHAR(100)                   -- Кто обновил
);

-- Индексы для быстрого поиска
CREATE INDEX idx_ai_agent_prompts_active ON ai_agent_prompts(agent_name, prompt_type, is_active);
CREATE INDEX idx_ai_agent_prompts_key ON ai_agent_prompts(prompt_key);
CREATE INDEX idx_ai_agent_prompts_default ON ai_agent_prompts(agent_name, is_default) WHERE is_default = TRUE;

-- Комментарии к таблице
COMMENT ON TABLE ai_agent_prompts IS 'Система управления промптами для AI-агентов';
COMMENT ON COLUMN ai_agent_prompts.prompt_key IS 'Уникальный ключ промпта (agent_name_prompt_type)';
COMMENT ON COLUMN ai_agent_prompts.variables IS 'JSON с описанием переменных для подстановки в промпт';
COMMENT ON COLUMN ai_agent_prompts.is_default IS 'Промпт используется по умолчанию для данного типа';

-- ============================================================================
-- Начальные данные - промпты из claude_code_prompts.py
-- ============================================================================

-- 1. AUDITOR: Детальная оценка проекта
INSERT INTO ai_agent_prompts (
    agent_name, prompt_type, prompt_key, prompt_text, prompt_description,
    variables, llm_provider, model, temperature, max_tokens, is_default, created_by
) VALUES (
    'auditor',
    'evaluation',
    'auditor_evaluation',
    'Ты эксперт по оценке грантовых заявок с 20-летним опытом работы в ведущих российских и международных грантовых фондах (Фонд президентских грантов, РФФИ, Росмолодежь).

Оцени проект по 10 критериям. Для каждого критерия дай оценку от 1 до 10 баллов и краткое обоснование.

**Критерии оценки:**

1. **Актуальность** (1-10) - насколько проблема важна и своевременна сегодня
2. **Новизна** (1-10) - уникальность подхода, инновационность решения
3. **Методология** (1-10) - обоснованность и реалистичность методов
4. **Бюджет** (1-10) - реалистичность и обоснованность расходов
5. **Команда** (1-10) - компетентность и релевантный опыт
6. **Результаты** (1-10) - конкретность, измеримость, достижимость
7. **Риски** (1-10) - идентификация и план управления рисками
8. **Социальная значимость** (1-10) - влияние на целевую аудиторию
9. **Масштабируемость** (1-10) - потенциал тиражирования опыта
10. **Устойчивость** (1-10) - план продолжения после завершения гранта

**Данные проекта:**
{project_data}

**Требования к ответу:**

Верни ТОЛЬКО валидный JSON (без дополнительного текста)',
    'Детальная оценка проекта по 10 критериям с рекомендациями',
    '{"project_data": "string"}',
    'claude_code',
    'claude-3-opus',
    0.3,
    4000,
    TRUE,
    'system'
);

-- 2. AUDITOR: Быстрая оценка
INSERT INTO ai_agent_prompts (
    agent_name, prompt_type, prompt_key, prompt_text, prompt_description,
    variables, llm_provider, temperature, is_default, created_by
) VALUES (
    'auditor',
    'quick_score',
    'auditor_quick_score',
    'Дай быструю оценку проекту по шкале 1-100.

Проект: {project_description}

Верни ТОЛЬКО JSON:
{
    "score": 75,
    "category": "высокий потенциал",
    "one_line_summary": "Актуальный проект с сильной командой, требует доработки бюджета"
}

Категории: "низкий потенциал" (0-40), "средний потенциал" (41-70), "высокий потенциал" (71-100)',
    'Быстрая оценка проекта по шкале 1-100',
    '{"project_description": "string"}',
    'gigachat',
    0.5,
    FALSE,
    'system'
);

-- 3. PLANNER: Структурирование заявки
INSERT INTO ai_agent_prompts (
    agent_name, prompt_type, prompt_key, prompt_text, prompt_description,
    variables, llm_provider, temperature, max_tokens, is_default, created_by
) VALUES (
    'planner',
    'structure',
    'planner_structure',
    'Ты эксперт по структурированию грантовых заявок для {fund_name}.

Создай детальную структуру заявки на основе данных проекта.

**Данные проекта:**
{project_data}

**Результаты аудита:**
{audit_results}

**Требования к структуре:**
- 6-8 основных разделов
- Для каждого раздела: название, описание, целевой объем (слов)
- Общий объем: {target_word_count} слов

Верни JSON со структурой заявки.',
    'Создание детальной структуры грантовой заявки',
    '{"fund_name": "string", "project_data": "string", "audit_results": "object", "target_word_count": "int"}',
    'claude_code',
    0.6,
    3000,
    TRUE,
    'system'
);

-- 4. RESEARCHER: Анализ аналогов
INSERT INTO ai_agent_prompts (
    agent_name, prompt_type, prompt_key, prompt_text, prompt_description,
    variables, llm_provider, max_tokens, is_default, created_by
) VALUES (
    'researcher',
    'analysis',
    'researcher_analysis',
    'Проанализируй похожие проекты и грантовые заявки.

**Тема проекта:** {project_topic}
**Целевая аудитория:** {target_audience}

Найди:
1. 3-5 успешных аналогичных проекта
2. Ключевые факторы их успеха
3. Типичные ошибки в подобных заявках

Верни JSON с анализом.',
    'Анализ похожих проектов и успешных заявок',
    '{"project_topic": "string", "target_audience": "string"}',
    'gigachat',
    2000,
    TRUE,
    'system'
);

-- 5. WRITER: Шаблон написания гранта
INSERT INTO ai_agent_prompts (
    agent_name, prompt_type, prompt_key, prompt_text, prompt_description,
    variables, llm_provider, temperature, max_tokens, is_default, created_by
) VALUES (
    'writer',
    'grant_template',
    'writer_grant_template',
    'Ты эксперт по написанию грантовых заявок для {fund_name}.

**Контекст проекта:**
{project_context}

**Структура заявки:**
{structure}

**Исследование:**
{research_data}

**Задание:**
Напиши полноценную грантовую заявку на {word_count} слов, следуя структуре выше.
Используй профессиональный язык, конкретные цифры, ссылайся на исследование.

**Требования:**
- Формат: Markdown
- Объем: {word_count}±10% слов
- Стиль: Официально-деловой
- Фокус: Социальная значимость, инновационность, устойчивость',
    'Генерация полного текста грантовой заявки',
    '{"fund_name": "string", "project_context": "string", "structure": "object", "research_data": "object", "word_count": "int"}',
    'gigachat',
    0.7,
    8000,
    TRUE,
    'system'
);

-- Обновить счетчик последовательности (для следующих вставок)
SELECT setval('ai_agent_prompts_id_seq', (SELECT MAX(id) FROM ai_agent_prompts));

-- ============================================================================
-- Триггер для обновления updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_ai_agent_prompts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ai_agent_prompts_updated_at
    BEFORE UPDATE ON ai_agent_prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_agent_prompts_updated_at();

-- ============================================================================
-- Проверка успешности миграции
-- ============================================================================

-- Вывести количество загруженных промптов
DO $$
DECLARE
    prompt_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO prompt_count FROM ai_agent_prompts;
    RAISE NOTICE 'Migration 005 completed successfully. Loaded % prompts', prompt_count;
END $$;
