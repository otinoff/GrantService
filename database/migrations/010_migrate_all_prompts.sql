-- Migration 010: Migrate all hardcoded prompts to database
-- Дата: 2025-10-10
-- Описание: Переносим ВСЕ промпты из кода в БД для редактирования через Streamlit
-- Агенты: Interviewer, Auditor, Researcher V2, Writer V2, Reviewer

-- ============================================================================
-- ЧАСТЬ 1: Расширение схемы БД
-- ============================================================================

-- 1.1 Добавляем новые поля в agent_prompts
ALTER TABLE agent_prompts ADD COLUMN IF NOT EXISTS agent_type VARCHAR(50);
ALTER TABLE agent_prompts ADD COLUMN IF NOT EXISTS prompt_type VARCHAR(50);
ALTER TABLE agent_prompts ADD COLUMN IF NOT EXISTS order_index INTEGER DEFAULT 0;
ALTER TABLE agent_prompts ADD COLUMN IF NOT EXISTS template_format VARCHAR(20) DEFAULT 'text';
ALTER TABLE agent_prompts ADD COLUMN IF NOT EXISTS max_tokens INTEGER;
ALTER TABLE agent_prompts ADD COLUMN IF NOT EXISTS temperature FLOAT;

-- 1.2 Создаем индексы
CREATE INDEX IF NOT EXISTS idx_agent_prompts_agent_type ON agent_prompts(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_prompts_prompt_type ON agent_prompts(prompt_type);
CREATE INDEX IF NOT EXISTS idx_agent_prompts_order ON agent_prompts(order_index);

-- 1.3 Добавляем новые категории промптов
INSERT INTO prompt_categories (name, description, agent_type) VALUES
  ('agent_system', 'Системные промпты агентов (goal, backstory)', 'system'),
  ('interviewer_fallback', 'Fallback вопросы Interviewer Agent', 'interviewer'),
  ('interviewer_llm', 'LLM промпты для генерации вопросов Interviewer', 'interviewer'),
  ('auditor_llm', 'LLM промпты Auditor для анализа качества', 'auditor'),
  ('researcher_block1', 'Researcher блок 1: Проблема и социальная значимость (10 запросов)', 'researcher_v2'),
  ('researcher_block2', 'Researcher блок 2: География и целевая аудитория (10 запросов)', 'researcher_v2'),
  ('researcher_block3', 'Researcher блок 3: Задачи, мероприятия и цели (7 запросов)', 'researcher_v2'),
  ('writer_stage1', 'Writer V2 Stage 1: Planning промпт', 'writer_v2'),
  ('writer_stage2', 'Writer V2 Stage 2: Writing промпт', 'writer_v2'),
  ('writer_quality', 'Writer V2 Quality Check промпт', 'writer_v2'),
  ('reviewer_system', 'Reviewer системные промпты', 'reviewer')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- ЧАСТЬ 2: Миграция промптов Interviewer Agent (17 промптов)
-- ============================================================================

-- 2.1 Goal и Backstory
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, is_active, priority) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'agent_system'),
  'Interviewer Goal',
  'Цель агента Interviewer',
  'Создать персонализированные вопросы для интервью на основе профиля пользователя и требований гранта',
  'interviewer',
  'goal',
  true,
  100
),
(
  (SELECT id FROM prompt_categories WHERE name = 'agent_system'),
  'Interviewer Backstory',
  'Предыстория агента Interviewer',
  'Ты опытный интервьюер и консультант по грантам с психологическим образованием. Ты умеешь задавать правильные вопросы, которые помогают раскрыть сильные стороны проекта и получить всю необходимую информацию для успешной заявки.',
  'interviewer',
  'backstory',
  true,
  100
);

-- 2.2 Fallback вопросы (10 вопросов)
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, order_index, variables, is_active) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_fallback'),
  'Fallback Question 1: Проект и идея',
  'Вопрос о проекте и его основной идее',
  'Расскажите подробнее о вашем проекте и его основной идее?',
  'interviewer',
  'fallback_question',
  1,
  '{"category": "project_basics", "required": true, "type": "open"}'::jsonb,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_fallback'),
  'Fallback Question 2: Проблема',
  'Вопрос о проблеме, которую решает проект',
  'Какую проблему решает ваш проект и почему это важно?',
  'interviewer',
  'fallback_question',
  2,
  '{"category": "project_basics", "required": true, "type": "open"}'::jsonb,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_fallback'),
  'Fallback Question 3: Команда',
  'Вопрос о команде и опыте',
  'Кто входит в вашу команду и какой у участников опыт?',
  'interviewer',
  'fallback_question',
  3,
  '{"category": "team_experience", "required": true, "type": "open"}'::jsonb,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_fallback'),
  'Fallback Question 4: Реализация',
  'Вопрос о планах реализации',
  'Как вы планируете реализовать проект пошагово?',
  'interviewer',
  'fallback_question',
  4,
  '{"category": "implementation", "required": true, "type": "open"}'::jsonb,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_fallback'),
  'Fallback Question 5: Бюджет',
  'Вопрос о расходовании средств',
  'На что конкретно будут потрачены запрашиваемые средства?',
  'interviewer',
  'fallback_question',
  5,
  '{"category": "budget_finances", "required": true, "type": "open"}'::jsonb,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_fallback'),
  'Fallback Question 6: Результаты',
  'Вопрос об ожидаемых результатах',
  'Какие результаты вы ожидаете получить от проекта?',
  'interviewer',
  'fallback_question',
  6,
  '{"category": "impact_results", "required": true, "type": "open"}'::jsonb,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_fallback'),
  'Fallback Question 7: Измерение успеха',
  'Вопрос о критериях успеха',
  'Как вы будете измерять успех проекта?',
  'interviewer',
  'fallback_question',
  7,
  '{"category": "impact_results", "required": true, "type": "open"}'::jsonb,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_fallback'),
  'Fallback Question 8: Риски',
  'Вопрос о рисках проекта',
  'Какие риски видите в реализации проекта и как их минимизировать?',
  'interviewer',
  'fallback_question',
  8,
  '{"category": "implementation", "required": false, "type": "open"}'::jsonb,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_fallback'),
  'Fallback Question 9: Опыт управления',
  'Вопрос об опыте управления проектами',
  'Есть ли у вас опыт управления подобными проектами?',
  'interviewer',
  'fallback_question',
  9,
  '{"category": "team_experience", "required": false, "type": "open"}'::jsonb,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_fallback'),
  'Fallback Question 10: Устойчивость',
  'Вопрос о дальнейшем развитии',
  'Как ваш проект будет продолжаться после окончания гранта?',
  'interviewer',
  'fallback_question',
  10,
  '{"category": "implementation", "required": false, "type": "open"}'::jsonb,
  true
);

-- 2.3 LLM промпт для генерации вопросов
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, variables, max_tokens, temperature, is_active) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'interviewer_llm'),
  'LLM Question Generation',
  'Промпт для генерации персонализированных вопросов через LLM',
  'Создай {question_count} вопросов {category_description} для интервью с заявителем гранта.

ПРОФИЛЬ ЗАЯВИТЕЛЯ:
{user_profile}

ОПИСАНИЕ ПРОЕКТА:
{project_description}

ТРЕБОВАНИЯ ГРАНТА:
{grant_requirements}

Создай открытые вопросы, которые помогут раскрыть важные детали проекта.
Формат ответа:
1. Вопрос 1
2. Вопрос 2
...',
  'interviewer',
  'llm_question_generation',
  '{"user_profile": "string", "project_description": "string", "grant_requirements": "string", "category_description": "string", "question_count": "integer"}'::jsonb,
  1000,
  0.7,
  true
);

-- Продолжение в следующей части...
