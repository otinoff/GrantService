-- Migration 010 Part 2: Auditor, Researcher, Writer, Reviewer промпты
-- Продолжение миграции промптов
-- ВАЖНО: Эта часть применяется ТОЛЬКО после успешного выполнения 010_migrate_all_prompts.sql

-- ============================================================================
-- ЧАСТЬ 3: Миграция промптов Auditor Agent (11 промптов)
-- ============================================================================

-- 3.1 Goal и Backstory
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, is_active, priority) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'agent_system'),
  'Auditor Goal',
  'Цель агента Auditor',
  'Провести комплексный анализ качества заявки и дать рекомендации по улучшению',
  'auditor',
  'goal',
  true,
  100
),
(
  (SELECT id FROM prompt_categories WHERE name = 'agent_system'),
  'Auditor Backstory',
  'Предыстория агента Auditor',
  'Ты опытный эксперт по грантовым заявкам с 20-летним стажем. Ты работал в комиссиях по рассмотрению заявок и знаешь все критерии оценки. Твоя задача - объективно оценить заявку и дать конкретные рекомендации по улучшению.',
  'auditor',
  'backstory',
  true,
  100
);

-- 3.2 LLM промпты для анализа (4 промпта)
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, variables, max_tokens, temperature, is_active) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'auditor_llm'),
  'Auditor LLM Completeness Check',
  'LLM проверка полноты заявки',
  'Проанализируй полноту следующей заявки на грант:

{application_text}

Оцени по шкале 1-10:
1. Наличие всех необходимых разделов
2. Детальность описания
3. Четкость формулировок

Дай оценку и краткие комментарии.',
  'auditor',
  'llm_completeness',
  '{"application_text": "string"}'::jsonb,
  1500,
  0.3,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'auditor_llm'),
  'Auditor LLM Quality Check',
  'LLM оценка качества содержания',
  'Оцени качество содержания заявки на грант:

ЗАЯВКА:
{application_text}

ДАННЫЕ ИССЛЕДОВАНИЯ:
{research_data}

Оцени по шкале 1-10:
1. Качество изложения
2. Логичность структуры
3. Убедительность аргументов
4. Соответствие данным исследования

Дай оценку и рекомендации.',
  'auditor',
  'llm_quality',
  '{"application_text": "string", "research_data": "string"}'::jsonb,
  2000,
  0.3,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'auditor_llm'),
  'Auditor LLM Compliance Check',
  'LLM проверка соответствия требованиям',
  'Проанализируй соответствие заявки требованиям гранта:

ЗАЯВКА:
{application_text}

ТРЕБОВАНИЯ ГРАНТА:
{grant_criteria}

Оцени по шкале 1-10:
1. Соответствие тематике гранта
2. Соответствие бюджетным ограничениям
3. Соответствие срокам реализации
4. Выполнение формальных требований

Дай оценку и укажи несоответствия.',
  'auditor',
  'llm_compliance',
  '{"application_text": "string", "grant_criteria": "string"}'::jsonb,
  1800,
  0.3,
  true
),
(
  (SELECT id FROM prompt_categories WHERE name = 'auditor_llm'),
  'Auditor LLM Innovation Check',
  'LLM оценка инновационности',
  'Оцени инновационность проекта:

{application_text}

Оцени по шкале 1-10:
1. Новизна подхода
2. Технологическую инновационность
3. Потенциал влияния
4. Уникальность решения

Дай оценку и обоснование.',
  'auditor',
  'llm_innovation',
  '{"application_text": "string"}'::jsonb,
  1500,
  0.3,
  true
);

-- ============================================================================
-- ЧАСТЬ 4: Миграция промптов Researcher V2 Agent (29 промптов)
-- ============================================================================

-- 4.1 Goal и Backstory
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, is_active, priority) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'agent_system'),
  'Researcher V2 Goal',
  'Цель агента Researcher V2',
  'Провести комплексное исследование через 27 экспертных WebSearch запросов для грантовой заявки',
  'researcher_v2',
  'goal',
  true,
  100
),
(
  (SELECT id FROM prompt_categories WHERE name = 'agent_system'),
  'Researcher V2 Backstory',
  'Предыстория агента Researcher V2',
  'Ты эксперт-исследователь с 15-летним опытом в грантовом консалтинге. Специализация: поиск официальной статистики, анализ госпрограмм, изучение успешных кейсов. Используешь только проверенные российские источники: Росстат, министерства, нацпроекты.',
  'researcher_v2',
  'backstory',
  true,
  100
);

-- 4.2 Блок 1: Проблема и социальная значимость (10 запросов)
-- Запрос 1
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, order_index, variables, is_active) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'researcher_block1'),
  'Block1 Query 1: Формулировка проблемы',
  'Запрос для чёткой формулировки проблемы',
  'Чётко сформулируй проблему ''{ПРОБЛЕМА}'' в контексте сферы ''{СФЕРА}'' и целевой группы ''{ЦЕЛЕВАЯ_ГРУППА}''. Опиши суть проблемы, её масштаб и последствия для целевой аудитории. Источники: официальные документы, исследования.',
  'researcher_v2',
  'block1_query',
  1,
  '{"ПРОБЛЕМА": "string", "СФЕРА": "string", "ЦЕЛЕВАЯ_ГРУППА": "string"}'::jsonb,
  true
);

-- Запрос 2
INSERT INTO agent_prompts (category_id, name, description, prompt_template, agent_type, prompt_type, order_index, variables, is_active) VALUES
(
  (SELECT id FROM prompt_categories WHERE name = 'researcher_block1'),
  'Block1 Query 2: Официальные подтверждения',
  'Поиск официальных подтверждений проблемы',
  'Найди официальные подтверждения проблемы ''{ПРОБЛЕМА}'' из следующих источников:
- Росстат (rosstat.gov.ru) и ЕМИСС (fedstat.ru)
- {ПРОФИЛЬНОЕ_МИНИСТЕРСТВО} (официальный сайт .gov.ru)
- Исследования российских ВУЗов и НИИ по сфере ''{СФЕРА}''
- Профильные реестры и базы данных

Требования к результату:
- Прямые цитаты с указанием источника, документа, даты публикации
- Конкретные цифры с единицами измерения и периодами
- URL ссылки на первоисточники
- Уровень данных (РФ/субъект/муниципалитет)',
  'researcher_v2',
  'block1_query',
  2,
  '{"ПРОБЛЕМА": "string", "ПРОФИЛЬНОЕ_МИНИСТЕРСТВО": "string", "СФЕРА": "string"}'::jsonb,
  true
);

-- Из-за большого объема, создам скрипт Python для генерации остальных запросов
-- Всего нужно добавить еще 25 запросов для Researcher V2

-- Продолжение следует...
