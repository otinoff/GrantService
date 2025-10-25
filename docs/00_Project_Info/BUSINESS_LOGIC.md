# GrantService Business Logic Documentation

**Version**: 1.0.0
**Last Modified**: 2025-10-01
**Status**: MVP (Minimum Viable Product)

---

## Table of Contents
1. [Product Overview](#1-product-overview)
2. [User Journey (MVP)](#2-user-journey-mvp)
3. [Data Flow Diagram](#3-data-flow-diagram)
4. [Database Schema for Business Logic](#4-database-schema-for-business-logic)
5. [Decision Logic](#5-decision-logic)
6. [MVP Scope vs Future Features](#6-mvp-scope-vs-future-features)
7. [Business Metrics](#7-business-metrics)

---

## 1. Product Overview

### 1.1 What GrantService Does

GrantService - это AI-powered платформа для автоматизации создания грантовых заявок. Система проводит пользователя через полный цикл подготовки заявки: от сбора информации о проекте до генерации профессионального грантового документа.

**Ключевая ценность:**
- **Время**: Сокращение подготовки заявки с 2-3 недель до 2-3 часов
- **Качество**: Экспертный уровень текста благодаря AI агентам
- **Успех**: Повышение процента одобрения с 10-15% до 40-50%

### 1.2 Target Audience

**Основная аудитория:**
- НКО и социальные предприниматели
- Стартапы и инновационные команды
- Научные коллективы и исследователи
- Образовательные организации

**Типичный пользователь:**
- Возраст: 25-45 лет
- Имеет проектную идею, но не имеет опыта грантрайтинга
- Ценит время и качество результата
- Готов к конструктивному диалогу с системой

### 1.3 Value Proposition

```
┌────────────────────────────────────────────────────────┐
│          ТРАДИЦИОННЫЙ ПОДХОД                           │
├────────────────────────────────────────────────────────┤
│ ❌ 2-3 недели ручной работы                            │
│ ❌ Найм грантрайтера (от 50 000 руб)                  │
│ ❌ Процент одобрения 10-15%                            │
│ ❌ Один шанс в год на крупные гранты                   │
└────────────────────────────────────────────────────────┘

                        ↓↓↓

┌────────────────────────────────────────────────────────┐
│             GRANTSERVICE ПОДХОД                         │
├────────────────────────────────────────────────────────┤
│ ✅ 2-3 часа на полную заявку                           │
│ ✅ Бесплатно / доступная подписка                      │
│ ✅ Процент одобрения 40-50%                            │
│ ✅ Множественные итерации и улучшения                  │
└────────────────────────────────────────────────────────┘
```

---

## 2. User Journey (MVP)

### 2.1 Stage 1: User Registration & Interview

**Entry Point:** Пользователь запускает Telegram бота командой `/start`

**Process:**
1. **Приветствие и объяснение процесса**
   - Система объясняет 6 этапов подготовки заявки
   - Показывает примерное время (2-3 часа)
   - Получает согласие на начало

2. **Hardcoded 24-вопросная анкета** (MVP approach)
   - Статический список вопросов в фиксированном порядке
   - Типы вопросов: текст, выбор, число, дата
   - Автосохранение каждого ответа
   - Возможность паузы и продолжения

3. **Вопросы разделены на блоки:**
   ```
   Блок 1: О проекте (5 вопросов)
   - Название проекта
   - Краткое описание
   - Целевая аудитория
   - География реализации
   - Сроки реализации

   Блок 2: Проблема и решение (4 вопроса)
   - Какую проблему решает
   - Почему проблема актуальна
   - Ваше уникальное решение
   - Альтернативные решения

   Блок 3: Команда и опыт (3 вопроса)
   - Состав команды
   - Опыт реализации проектов
   - Партнеры и поддержка

   Блок 4: Бюджет и ресурсы (4 вопроса)
   - Необходимая сумма
   - Планируемые расходы
   - Собственный вклад
   - Дополнительные источники

   Блок 5: Результаты и измерение (4 вопроса)
   - Ожидаемые результаты
   - Количественные показатели
   - Социальный эффект
   - Устойчивость проекта

   Блок 6: Дополнительно (4 вопроса)
   - Риски и их минимизация
   - План коммуникации
   - Предыдущие достижения
   - Дополнительные материалы
   ```

4. **Автосохранение и отслеживание прогресса**
   - После каждого ответа: UPDATE sessions SET answers_data, progress_percentage
   - Progress bar: "5 из 24 вопросов (21%)"
   - Session ID сохраняется в cookies Telegram

**Database Impact:**
```sql
-- Создаётся запись в sessions
INSERT INTO sessions (
    telegram_id,
    anketa_id,  -- Генерируется: #AN-20251001-username-001
    status = 'active',
    total_questions = 24,
    questions_answered = 0,
    progress_percentage = 0
)

-- После каждого ответа обновляется:
UPDATE sessions SET
    answers_data = JSON,  -- {"q1": "answer1", "q2": "answer2", ...}
    questions_answered = questions_answered + 1,
    progress_percentage = (questions_answered / 24) * 100,
    last_activity = NOW()
WHERE id = session_id
```

**Output:** Заполненная анкета в таблице `sessions` со статусом `completed`

---

### 2.2 Stage 2: Auditor Stage

**Trigger:** Автоматический запуск после завершения всех 24 вопросов

**Process:**
1. **Извлечение данных анкеты**
   ```python
   session = get_session(session_id)
   answers = json.loads(session.answers_data)
   ```

2. **Оценка по 5 критериям** (каждый от 1 до 10):
   - **Полнота информации** (completeness_score)
     - Все ли вопросы содержат развёрнутые ответы
     - Есть ли конкретные данные и цифры
     - Достаточно ли деталей для написания заявки

   - **Ясность и структурированность** (clarity_score)
     - Понятна ли суть проекта
     - Логична ли связь проблема-решение-результаты
     - Нет ли противоречий в ответах

   - **Реалистичность** (feasibility_score)
     - Адекватность бюджета задачам
     - Реальность сроков
     - Соответствие ресурсов команды масштабу проекта

   - **Инновационность** (innovation_score)
     - Уникальность решения
     - Отличие от существующих подходов
     - Потенциал масштабирования

   - **Социальная значимость** (quality_score)
     - Масштаб решаемой проблемы
     - Количество благополучателей
     - Долгосрочный эффект

3. **Расчёт итоговой оценки**
   ```python
   average_score = (
       completeness_score +
       clarity_score +
       feasibility_score +
       innovation_score +
       quality_score
   ) / 5
   ```

4. **Принятие решения**
   ```python
   if average_score >= 6.0:
       approval_status = 'approved'
       next_stage = 'planner'
   else:
       approval_status = 'needs_revision'
       next_stage = 'feedback'
   ```

5. **Генерация рекомендаций**
   - Для каждого критерия < 6: конкретные советы по улучшению
   - Примеры качественных ответов
   - Предложение доработать слабые блоки

**Database Impact:**
```sql
-- Создаётся запись в auditor_results (NEW TABLE)
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
    auditor_llm_provider = 'gigachat',
    created_at = NOW()
)

-- Обновляется sessions
UPDATE sessions SET
    current_step = 'audit_completed',
    audit_result = JSON  -- Для обратной совместимости
WHERE id = session_id
```

**Output:**
- Структурированная оценка в `auditor_results`
- Решение: approved (переход к Planner) или needs_revision (возврат пользователю)

---

### 2.3 Stage 3: Planner Stage (MVP - simplified)

**Trigger:** Автоматический запуск для заявок с `approval_status = 'approved'`

**Process:**
1. **Выбор шаблона структуры**
   - MVP: Единый универсальный шаблон для всех грантов
   - Future: Адаптивный выбор на основе типа гранта и фонда

2. **Стандартная структура заявки** (7 разделов):
   ```json
   {
     "sections": [
       {
         "id": 1,
         "title": "Описание проблемы",
         "description": "Анализ текущей ситуации и обоснование актуальности",
         "word_count_target": 300,
         "data_sources": ["q1", "q2", "q3"]  // Вопросы анкеты
       },
       {
         "id": 2,
         "title": "Целевая аудитория и география",
         "description": "Кто получит пользу и где",
         "word_count_target": 200,
         "data_sources": ["q4", "q5"]
       },
       {
         "id": 3,
         "title": "Цели и задачи проекта",
         "description": "Что мы хотим достичь и как",
         "word_count_target": 250,
         "data_sources": ["q6", "q7", "q8"]
       },
       {
         "id": 4,
         "title": "Методы и механизмы реализации",
         "description": "Конкретные шаги и инструменты",
         "word_count_target": 400,
         "data_sources": ["q9", "q10", "q11"]
       },
       {
         "id": 5,
         "title": "Команда и партнёры",
         "description": "Кто реализует проект",
         "word_count_target": 200,
         "data_sources": ["q12", "q13", "q14"]
       },
       {
         "id": 6,
         "title": "Бюджет проекта",
         "description": "Финансовый план и обоснование",
         "word_count_target": 300,
         "data_sources": ["q15", "q16", "q17", "q18"]
       },
       {
         "id": 7,
         "title": "Ожидаемые результаты и оценка",
         "description": "Измеримые показатели эффективности",
         "word_count_target": 250,
         "data_sources": ["q19", "q20", "q21"]
       }
     ],
     "total_estimated_words": 1900,
     "estimated_pages": 8
   }
   ```

3. **Mapping вопросов к разделам**
   - Автоматическое распределение ответов анкеты по разделам
   - Определение приоритетных данных для каждого раздела
   - Выявление gap'ов (разделов с недостаточными данными)

**Database Impact:**
```sql
-- Создаётся запись в planner_structures (NEW TABLE)
INSERT INTO planner_structures (
    session_id,
    audit_id,
    structure_json,  -- Полная структура выше
    sections_count = 7,
    total_word_count_target = 1900,
    data_mapping_complete = true,
    created_at = NOW()
)

-- Обновляется sessions
UPDATE sessions SET
    current_step = 'planning_completed',
    plan_structure = JSON  -- Для обратной совместимости
WHERE id = session_id
```

**Output:** Структурированный план заявки в `planner_structures`

---

### 2.4 Stage 4: Researcher Stage

**Trigger:** Автоматический запуск после создания плана

**Process:**
1. **Генерация поисковых запросов для каждого раздела**
   ```python
   for section in plan.sections:
       # Берём данные анкеты для этого раздела
       section_data = extract_answers(session, section.data_sources)

       # Формируем контекст для поиска
       search_query = f"""
       Найди актуальные данные для раздела "{section.title}":
       - Статистика и цифры по теме: {section_data['problem']}
       - Лучшие практики реализации: {section_data['solution']}
       - Кейсы успешных проектов в области: {section_data['domain']}
       """
   ```

2. **Поиск через Perplexity API**
   ```python
   research_results = []

   for query in queries:
       result = perplexity_client.search(
           query=query,
           focus='academic',  # Приоритет научным источникам
           max_results=5
       )
       research_results.append(result)
   ```

3. **Структурирование результатов**
   ```json
   {
     "section_1": {
       "statistics": [
         "По данным Росстата 2024, 23% населения...",
         "Исследование НИУ ВШЭ показало..."
       ],
       "best_practices": [
         "Проект 'Название' в Москве достиг 80% охвата...",
         "Международный опыт Финляндии..."
       ],
       "expert_opinions": [
         "Д.э.н. Иванов отмечает, что..."
       ],
       "sources": [
         {"url": "...", "title": "...", "date": "2024-09"}
       ]
     },
     "section_2": { ... }
   }
   ```

**Database Impact:**
```sql
-- Создаётся запись в researcher_research
INSERT INTO researcher_research (
    research_id = '#RS-20251001-username-001-AN-anketa_id',
    anketa_id,
    session_id,
    user_id,
    research_type = 'comprehensive',
    llm_provider = 'perplexity',
    status = 'completed',
    research_results = JSON,  -- Структурированные результаты
    metadata = JSON,  -- {"tokens": 5000, "cost": 0.05, "duration_sec": 45}
    created_at = NOW(),
    completed_at = NOW()
)

-- Обновляется sessions
UPDATE sessions SET
    current_step = 'research_completed'
WHERE id = session_id
```

**Output:** Исследовательские данные в `researcher_research` для каждого раздела плана

---

### 2.5 Stage 5: Writer Stage

**Trigger:** Автоматический запуск после завершения исследования

**Process:**
1. **Сборка контекста для генерации**
   ```python
   context = {
       'anketa': session.answers_data,
       'audit': auditor_result,
       'plan': planner_structure,
       'research': researcher_data
   }
   ```

2. **Последовательная генерация разделов**
   ```python
   grant_sections = []

   for section in plan.sections:
       prompt = f"""
       Напиши раздел грантовой заявки:

       РАЗДЕЛ: {section.title}
       ОПИСАНИЕ: {section.description}
       ЦЕЛЕВОЙ ОБЪЁМ: {section.word_count_target} слов

       ДАННЫЕ АНКЕТЫ:
       {context['anketa'][section.data_sources]}

       РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ:
       {context['research'][section.id]}

       ТРЕБОВАНИЯ:
       - Академический стиль
       - Конкретные данные и цифры
       - Ссылки на источники
       - Логичная структура
       """

       section_text = gigachat.generate(prompt)
       grant_sections.append({
           'section_id': section.id,
           'title': section.title,
           'content': section_text,
           'word_count': len(section_text.split())
       })
   ```

3. **Компоновка финального документа**
   ```python
   final_grant = {
       'title': session.project_name,
       'sections': grant_sections,
       'total_words': sum(s['word_count'] for s in grant_sections),
       'generated_at': datetime.now()
   }
   ```

4. **Автоматическая оценка качества**
   ```python
   quality_checks = {
       'word_count_match': check_word_counts(grant_sections, plan.sections),
       'has_statistics': check_contains_numbers(final_grant),
       'has_sources': check_citations(final_grant),
       'readability_score': calculate_readability(final_grant),
       'completeness_score': check_all_sections_present(final_grant)
   }

   quality_score = calculate_average(quality_checks)
   ```

**Database Impact:**
```sql
-- Создаётся запись в grants
INSERT INTO grants (
    grant_id = '#GR-20251001-username-001-AN-anketa_id',
    anketa_id,
    research_id,
    user_id,
    grant_title = session.project_name,
    grant_content = final_grant_text,  -- Полный текст
    grant_sections = JSON,  -- Структурированные разделы
    metadata = JSON,  -- Токены, время, стоимость
    llm_provider = 'gigachat',
    model = 'GigaChat-Pro',
    status = 'completed',
    quality_score = calculated_score,
    created_at = NOW()
)

-- Обновляется sessions
UPDATE sessions SET
    current_step = 'writing_completed',
    final_document = grant_id,
    completion_status = 'completed'
WHERE id = session_id
```

**Output:** Готовый грант в таблице `grants` со статусом `completed`

---

### 2.6 Stage 6: Delivery Stage

**Trigger:** Администратор видит готовый грант в админ-панели и решает отправить

**Process:**
1. **Просмотр гранта администратором**
   - Админ открывает страницу "Управление грантами"
   - Видит список завершённых грантов
   - Открывает детальный просмотр
   - Проверяет quality_score и содержание

2. **Отправка пользователю**
   ```python
   # В админ-панели нажимается кнопка "Отправить в Telegram"

   # 1. Генерация PDF документа
   pdf_file = generate_pdf(grant)

   # 2. Отправка через Telegram Bot API
   bot.send_document(
       chat_id=user.telegram_id,
       document=pdf_file,
       caption=f"""
       ✅ Ваша грантовая заявка готова!

       📋 Проект: {grant.grant_title}
       📊 Оценка качества: {grant.quality_score}/10
       📄 Объём: {grant.metadata['total_words']} слов

       Документ содержит 7 разделов с подробным описанием проекта,
       актуальной статистикой и обоснованием бюджета.

       Рекомендации по подаче:
       - Проверьте требования конкретного фонда
       - Адаптируйте при необходимости
       - Добавьте приложения (бюджет, команда)
       """
   )

   # 3. Логирование отправки
   log_grant_delivery(grant.id, user.telegram_id, pdf_file.name)
   ```

**Database Impact:**
```sql
-- Создаётся запись в sent_documents
INSERT INTO sent_documents (
    grant_id,
    user_id,
    telegram_message_id,
    file_name,
    file_size,
    sent_at = NOW(),
    delivery_status = 'delivered'
)

-- Обновляется grants
UPDATE grants SET
    status = 'delivered',
    submitted_at = NOW()
WHERE id = grant_id
```

**Output:** Пользователь получает PDF документ в Telegram боте

---

## 3. Data Flow Diagram

### 3.1 Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER JOURNEY                              │
└─────────────────────────────────────────────────────────────────┘

[TELEGRAM BOT]                    [DATABASE]                    [ADMIN PANEL]
      │                                │                               │
      ├─ /start                        │                               │
      │                                │                               │
      ├─ Fill 24 questions ──────► sessions                           │
      │   (auto-save each)            │ (answers_data,                │
      │                               │  progress_percentage)          │
      │                                │                               │
      ├─ Complete ──────────────────► sessions                        │
      │   (24/24)                     │ (status='completed')          │
      │                                │                               │
      │                                ▼                               │
      │                          [AUDITOR AGENT]                       │
      │                                │                               │
      │                                ├─ Analyze ──────────►  auditor_results
      │                                │   answers           (5 scores)
      │                                │                               │
      │                                ├─ Score < 6? ─────► sessions  │
      │                                │   YES: return       (needs_revision)
      │                                │   feedback                    │
      │                                │                               │
      │                                ├─ Score >= 6 ──────► sessions │
      │                                │   Continue          (approved)
      │                                ▼                               │
      │                          [PLANNER AGENT]                       │
      │                                │                               │
      │                                ├─ Generate ─────────► planner_structures
      │                                │   structure        (7 sections)
      │                                │                               │
      │                                ▼                               │
      │                         [RESEARCHER AGENT]                     │
      │                                │                               │
      │                                ├─ Search ───────────► researcher_research
      │                                │   for each         (Perplexity API)
      │                                │   section                      │
      │                                │                               │
      │                                ▼                               │
      │                           [WRITER AGENT]                       │
      │                                │                               │
      │                                ├─ Generate ─────────► grants  │
      │                                │   grant text       (GigaChat) │
      │                                │                               │
      │                                │                               ├─ Admin views
      │                                │                               │   ready grant
      │                                │                               │
      │                                │                               ├─ Click "Send"
      │                                │                               │
      │ ◄─── PDF document ─────────────┴───────────────────────────────┤
      │      via Telegram Bot                                         │
      │                                                                │
      ▼                                                                │
  [USER RECEIVES]                                                     │
   Grant Document                                                     │
```

### 3.2 Database Relationships

```
┌──────────────────────────────────────────────────────────────────┐
│                     DATABASE SCHEMA FLOW                          │
└──────────────────────────────────────────────────────────────────┘

users (telegram_id)
  │
  └──► sessions (telegram_id FK)
         │
         ├──► auditor_results (session_id FK)
         │      │
         │      └──► planner_structures (audit_id FK, session_id FK)
         │             │
         │             └──► researcher_research (session_id FK, anketa_id)
         │                    │
         │                    └──► grants (research_id FK, anketa_id FK)
         │                           │
         │                           └──► sent_documents (grant_id FK)
         │
         └──► user_answers (session_id FK)
```

### 3.3 Status Flow

```
SESSION STATUS TRANSITIONS:
┌─────────┐     ┌──────────┐     ┌───────────┐     ┌───────────┐
│ active  │ ──► │completed │ ──► │ approved  │ ──► │ delivered │
└─────────┘     └──────────┘     └───────────┘     └───────────┘
                      │
                      ├──► needs_revision (score < 6)
                      │
                      └──► rejected (critical issues)

GRANT STATUS TRANSITIONS:
┌───────┐     ┌───────────┐     ┌───────────┐     ┌──────────┐
│ draft │ ──► │ completed │ ──► │ delivered │ ──► │submitted │
└───────┘     └───────────┘     └───────────┘     └──────────┘
```

---

## 4. Database Schema for Business Logic

### 4.1 Core Tables and Their Business Purpose

#### sessions - User Interview Data
**Business Purpose:** Хранит анкету пользователя - фундамент всего процесса

**Key Fields:**
- `anketa_id` - Уникальный ID анкеты (#AN-20251001-username-001)
- `answers_data` - JSON с ответами на 24 вопроса
- `progress_percentage` - Для UI progress bar
- `completion_status` - in_progress | completed | approved | delivered

**Business Rules:**
- Нельзя запустить Auditor, пока `questions_answered < 24`
- `anketa_id` генерируется при первом сохранении ответа
- Session считается abandoned, если `last_activity > 7 дней`

---

#### auditor_results - Quality Assessment (NEW)
**Business Purpose:** Структурированная оценка качества анкеты

**Fields:**
```sql
CREATE TABLE auditor_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    completeness_score INTEGER CHECK(completeness_score >= 1 AND completeness_score <= 10),
    clarity_score INTEGER CHECK(clarity_score >= 1 AND clarity_score <= 10),
    feasibility_score INTEGER CHECK(feasibility_score >= 1 AND feasibility_score <= 10),
    innovation_score INTEGER CHECK(innovation_score >= 1 AND innovation_score <= 10),
    quality_score INTEGER CHECK(quality_score >= 1 AND quality_score <= 10),
    average_score REAL,
    approval_status VARCHAR(30) DEFAULT 'pending',  -- pending | approved | needs_revision | rejected
    recommendations TEXT,  -- JSON с рекомендациями для каждого критерия
    auditor_llm_provider VARCHAR(50) NOT NULL,
    model VARCHAR(50),
    metadata TEXT,  -- JSON с токенами, временем, стоимостью
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

**Business Rules:**
- `average_score = (sum of 5 scores) / 5`
- `approval_status = 'approved'` if `average_score >= 6.0`
- Можно запустить повторный аудит после доработки
- `recommendations` содержит советы только для scores < 6

---

#### planner_structures - Grant Application Structure (NEW)
**Business Purpose:** План структуры заявки - bridge между анкетой и генерацией

**Fields:**
```sql
CREATE TABLE planner_structures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    audit_id INTEGER NOT NULL,
    structure_json TEXT NOT NULL,  -- JSON с разделами и mapping'ом
    sections_count INTEGER DEFAULT 7,
    total_word_count_target INTEGER DEFAULT 1900,
    data_mapping_complete BOOLEAN DEFAULT FALSE,
    metadata TEXT,  -- JSON с настройками генерации
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (audit_id) REFERENCES auditor_results(id)
);
```

**Business Rules:**
- Создаётся ТОЛЬКО для approved анкет
- MVP: все планы используют один шаблон (7 разделов)
- `data_mapping_complete = TRUE` означает, что все разделы mapped к вопросам
- Future: multiple templates для разных типов грантов

---

#### researcher_research - Research Data
**Business Purpose:** Собранные данные для обогащения заявки

**Key Business Logic:**
- Каждый раздел плана → отдельный поисковый запрос
- `research_results` - JSON с структурой:
  ```json
  {
    "section_1": {
      "statistics": [...],
      "best_practices": [...],
      "sources": [...]
    }
  }
  ```
- `status = 'completed'` означает, что все разделы исследованы

---

#### grants - Final Grant Documents
**Business Purpose:** Готовые грантовые заявки для отправки пользователям

**Key Business Logic:**
- `grant_id` формат: #GR-20251001-username-001-AN-anketa_id
- `quality_score` - автоматическая оценка качества текста (1-10)
- `status`:
  - `draft` - сгенерирован, но не проверен
  - `completed` - прошёл все проверки
  - `delivered` - отправлен пользователю
  - `submitted` - пользователь подал в фонд
  - `approved` / `rejected` - результат от фонда

---

### 4.2 Relationship Rules

**Cascade Deletions:**
- DELETE user → CASCADE DELETE sessions, grants
- DELETE session → RESTRICT (нельзя удалить, если есть grants)

**Integrity Constraints:**
- Нельзя создать `auditor_results` без `session_id`
- Нельзя создать `planner_structures` без `audit_id`
- Нельзя создать `grants` без `research_id`

---

## 5. Decision Logic

### 5.1 Auditor Approval Logic

**Decision Tree:**
```
START: Анкета completed (24/24)
  │
  ├─ Auditor анализирует ответы
  │
  ├─ Вычисляет 5 scores (1-10 каждый)
  │
  ├─ Average score = Sum / 5
  │
  ├─ IF average_score >= 8.0:
  │    ├─ approval_status = 'approved'
  │    ├─ priority = 'high'
  │    └─ Переход к Planner (без задержки)
  │
  ├─ ELIF average_score >= 6.0:
  │    ├─ approval_status = 'approved'
  │    ├─ priority = 'normal'
  │    └─ Переход к Planner
  │
  ├─ ELIF average_score >= 4.0:
  │    ├─ approval_status = 'needs_revision'
  │    ├─ Генерация recommendations
  │    └─ Возврат пользователю для доработки
  │
  └─ ELSE (score < 4.0):
       ├─ approval_status = 'rejected'
       ├─ Детальный feedback
       └─ Предложение начать заново
```

**Scoring Thresholds:**
```python
SCORE_THRESHOLDS = {
    'excellent': (8, 10),    # Автоматическая генерация
    'good': (6, 7.9),        # Генерация с мониторингом
    'revision': (4, 5.9),    # Требуется доработка
    'poor': (1, 3.9)         # Рекомендация переделать
}
```

**Recommendations Generation:**
```python
def generate_recommendations(scores):
    recommendations = {}

    for criterion, score in scores.items():
        if score < 6:
            recommendations[criterion] = {
                'current_score': score,
                'target_score': 6,
                'suggestions': get_improvement_tips(criterion),
                'examples': get_good_examples(criterion)
            }

    return recommendations
```

---

### 5.2 Planner Section Generation Logic

**Section Selection (MVP):**
```python
# MVP: Fixed 7 sections for all grants
STANDARD_SECTIONS = [
    'problem_description',
    'target_audience',
    'goals_and_objectives',
    'implementation_methods',
    'team_and_partners',
    'budget',
    'expected_results'
]

def generate_structure(session, audit_result):
    structure = {
        'sections': []
    }

    for section_template in STANDARD_SECTIONS:
        section = {
            'id': section_template['id'],
            'title': section_template['title'],
            'word_count_target': section_template['words'],
            'data_sources': map_questions_to_section(
                session.answers_data,
                section_template
            )
        }
        structure['sections'].append(section)

    return structure
```

**Question Mapping Logic:**
```python
QUESTION_TO_SECTION_MAP = {
    'problem_description': [1, 2, 3, 6],      # Вопросы о проблеме
    'target_audience': [4, 5],                 # Аудитория и география
    'goals_and_objectives': [7, 8, 9],         # Цели проекта
    'implementation_methods': [10, 11, 12],    # Как будем делать
    'team_and_partners': [13, 14, 15],         # Команда
    'budget': [16, 17, 18],                    # Финансы
    'expected_results': [19, 20, 21, 22]       # Результаты и метрики
}
```

---

### 5.3 Researcher Query Building Logic

**Query Generation Strategy:**
```python
def build_research_queries(section, anketa_data):
    """
    Для каждого раздела формируем 3 типа запросов:
    1. Статистика и данные
    2. Лучшие практики
    3. Экспертные мнения
    """

    project_domain = anketa_data['q1']  # Тема проекта
    problem = anketa_data['q6']         # Проблема
    solution = anketa_data['q7']        # Решение

    queries = []

    # Query 1: Statistics
    queries.append(f"""
    Найди актуальную статистику за 2023-2024 годы:
    - Масштаб проблемы: {problem}
    - Регион: {anketa_data['q5']}
    - Целевая аудитория: {anketa_data['q4']}
    Источники: Росстат, НИУ ВШЭ, профильные министерства
    """)

    # Query 2: Best Practices
    queries.append(f"""
    Найди успешные кейсы и лучшие практики:
    - Область: {project_domain}
    - Похожие решения: {solution}
    - География: Россия и международный опыт
    Фокус: проекты с измеримыми результатами
    """)

    # Query 3: Expert Opinions
    queries.append(f"""
    Найди экспертные мнения и исследования:
    - Тема: {problem}
    - Фокус: обоснование актуальности и эффективности
    - Источники: научные публикации, отраслевые отчёты
    """)

    return queries
```

**Source Prioritization:**
```python
SOURCE_PRIORITIES = {
    'high': [
        'rosstat.gov.ru',
        'hse.ru',
        'cyberleninka.ru',
        'elibrary.ru'
    ],
    'medium': [
        'consultant.ru',
        'rbc.ru',
        'vedomosti.ru'
    ],
    'low': [
        'general news sites'
    ]
}
```

---

## 6. MVP Scope vs Future Features

### 6.1 MVP (Current Version)

**✅ Implemented:**

1. **Interviewer Agent = Static Questions**
   - 24 hardcoded questions
   - Fixed order
   - No adaptation based on answers
   - **Rationale:** Обеспечивает полноту данных, проще тестировать

2. **Basic Auditor**
   - 5 criteria scoring
   - Threshold-based approval (>= 6)
   - Simple recommendations
   - **Rationale:** Minimum viable quality control

3. **Simplified Planner**
   - Single template (7 sections)
   - Static question mapping
   - No customization
   - **Rationale:** Works for 80% of grants

4. **Perplexity-based Researcher**
   - Template-based queries
   - One search per section
   - Basic structuring
   - **Rationale:** Good enough data enrichment

5. **GigaChat Writer**
   - Sequential section generation
   - Template-based prompts
   - Basic quality checks
   - **Rationale:** Produces acceptable grant text

6. **One-way Bot → Admin**
   - Bot collects data
   - Admin sends grants
   - No real-time sync
   - **Rationale:** Simplest integration

---

### 6.2 Future Features (Post-MVP)

**🚀 Planned Enhancements:**

1. **AI-Powered Dynamic Interviewer**
   ```python
   # Future: Adaptive questioning
   class SmartInterviewer:
       def next_question(self, previous_answers):
           # Анализирует предыдущие ответы
           # Генерирует персонализированный вопрос
           # Адаптирует глубину проработки

           context = analyze_answers(previous_answers)

           if context['needs_more_detail']:
               return generate_followup_question(context)
           elif context['ready_to_skip']:
               return skip_to_next_section()
   ```

   **Benefits:**
   - Shorter interviews (from 24 to ~15 questions)
   - More relevant questions
   - Better data quality

2. **Advanced Planner with Template Selection**
   ```python
   # Future: Multiple templates
   GRANT_TEMPLATES = {
       'presidential_grants': {
           'sections': 10,
           'focus': 'social_impact',
           'word_count': 3000
       },
       'innovation_grants': {
           'sections': 8,
           'focus': 'innovation_metrics',
           'word_count': 2500
       },
       'scientific_grants': {
           'sections': 12,
           'focus': 'methodology',
           'word_count': 4000
       }
   }

   def select_template(project_data, target_fund):
       # ML model predicts best template
       # Based on project type and fund requirements
   ```

   **Benefits:**
   - Higher approval rates for specific funds
   - Optimized structure per grant type
   - Compliance with fund requirements

3. **Two-way Bot ↔ Admin Integration**
   ```python
   # Future: Real-time synchronization
   class BotAdminBridge:
       def on_anketa_completed(self, session_id):
           # Webhook to admin panel
           notify_admin_new_anketa(session_id)

       def on_grant_ready(self, grant_id):
           # Auto-send to user (optional)
           if settings.AUTO_DELIVERY:
               send_to_telegram(grant_id)

       def on_admin_message(self, user_id, message):
           # Admin can message user via bot
           bot.send_message(user_id, message)
   ```

   **Benefits:**
   - Faster delivery
   - Better communication
   - Real-time monitoring

4. **Multi-LLM Orchestration**
   ```python
   # Future: Best LLM for each task
   LLM_TASK_MAP = {
       'interviewer': 'claude-3-opus',      # Best at dialogue
       'auditor': 'gpt-4',                  # Best at evaluation
       'planner': 'gigachat-pro',           # Good structure
       'researcher': 'perplexity',          # Best search
       'writer': 'claude-3-sonnet'          # Best writing
   }
   ```

   **Benefits:**
   - Optimal quality per stage
   - Cost optimization
   - Redundancy and fallbacks

5. **Collaborative Editing**
   ```python
   # Future: User can edit generated grant
   class GrantEditor:
       def suggest_edits(self, grant_id, user_feedback):
           # User highlights sections to improve
           # AI regenerates only those sections
           # Preserves context and style
   ```

   **Benefits:**
   - User control over final text
   - Iterative improvement
   - Higher user satisfaction

---

### 6.3 Why MVP Approach is Optimal

**Reasons for Hardcoded Questions (MVP):**

1. **Completeness Guarantee**
   - We KNOW we collect all necessary data
   - No risk of missing critical information
   - Easier to debug and improve

2. **Faster Time to Market**
   - No need to train adaptive model
   - Simpler testing
   - Less edge cases

3. **Better Baseline Metrics**
   - Consistent data collection
   - Easier to measure improvements
   - Clear A/B testing when adding AI

4. **Lower LLM Costs**
   - 24 static questions = 0 LLM calls
   - AI interviewer = 15-20 LLM calls per user
   - MVP: $0 per interview vs Future: $0.50 per interview

5. **Easier User Support**
   - Predictable flow
   - Standard troubleshooting
   - Can pre-write help articles

**When to Upgrade:**
- After 100+ completed grants
- When we have data to train on
- When user feedback shows interview fatigue
- When ROI justifies LLM costs

---

## 7. Business Metrics

### 7.1 Funnel Metrics

**Primary Conversion Funnel:**
```
┌─────────────────────────────────────────────────────────┐
│  STAGE                 │ COUNT │ CONVERSION │ AVG TIME  │
├─────────────────────────────────────────────────────────┤
│  1. /start             │  100  │   100%     │    -      │
│  2. Question 1         │   90  │    90%     │  1 min    │
│  3. Question 12 (50%)  │   70  │    78%     │  10 min   │
│  4. Completed (24/24)  │   60  │    86%     │  25 min   │
│  5. Audit Approved     │   48  │    80%     │  2 min    │
│  6. Planning Done      │   48  │   100%     │  3 min    │
│  7. Research Done      │   45  │    94%     │  10 min   │
│  8. Grant Generated    │   43  │    96%     │  8 min    │
│  9. Grant Delivered    │   40  │    93%     │  1 day    │
│ 10. Grant Submitted    │   35  │    88%     │  7 days   │
│ 11. Grant Approved     │   17  │    49%     │  2 months │
└─────────────────────────────────────────────────────────┘

OVERALL CONVERSION: 17 / 100 = 17% (from /start to grant approval)
TARGET: 40-50% approval rate
```

**SQL Queries for Metrics:**
```sql
-- Overall funnel
SELECT
    'Started' as stage,
    COUNT(*) as count,
    100.0 as conversion_pct
FROM sessions
WHERE started_at >= DATE('now', '-30 days')

UNION ALL

SELECT
    'Completed Interview' as stage,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sessions WHERE started_at >= DATE('now', '-30 days')), 1)
FROM sessions
WHERE completion_status = 'completed'
    AND started_at >= DATE('now', '-30 days')

UNION ALL

SELECT
    'Audit Approved' as stage,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sessions WHERE completion_status = 'completed'), 1)
FROM auditor_results
WHERE approval_status = 'approved'
    AND created_at >= DATE('now', '-30 days')

-- ... и так далее для каждого этапа
```

---

### 7.2 Quality Metrics

**Auditor Scores Distribution:**
```sql
-- Распределение оценок
SELECT
    CASE
        WHEN average_score >= 8 THEN 'Excellent (8-10)'
        WHEN average_score >= 6 THEN 'Good (6-7.9)'
        WHEN average_score >= 4 THEN 'Needs Revision (4-5.9)'
        ELSE 'Poor (1-3.9)'
    END as score_category,
    COUNT(*) as count,
    ROUND(AVG(average_score), 2) as avg_score,
    MIN(average_score) as min_score,
    MAX(average_score) as max_score
FROM auditor_results
GROUP BY score_category
ORDER BY avg_score DESC;
```

**Expected Distribution (Target):**
- Excellent: 15-20%
- Good: 60-70%
- Needs Revision: 10-15%
- Poor: < 5%

---

### 7.3 Operational Metrics

**Processing Times:**
```sql
-- Среднее время на каждом этапе
SELECT
    'Interview' as stage,
    ROUND(AVG(session_duration_minutes), 1) as avg_minutes,
    MIN(session_duration_minutes) as min_minutes,
    MAX(session_duration_minutes) as max_minutes
FROM sessions
WHERE completion_status = 'completed'

UNION ALL

SELECT
    'Audit' as stage,
    ROUND(AVG(CAST((julianday(created_at) - julianday(s.completed_at)) * 24 * 60 AS INTEGER)), 1),
    MIN(CAST((julianday(created_at) - julianday(s.completed_at)) * 24 * 60 AS INTEGER)),
    MAX(CAST((julianday(created_at) - julianday(s.completed_at)) * 24 * 60 AS INTEGER))
FROM auditor_results ar
JOIN sessions s ON ar.session_id = s.id

-- ... аналогично для других этапов
```

**Target Times:**
- Interview: 20-30 min
- Audit: < 5 min
- Planning: < 5 min
- Research: 5-15 min
- Writing: 10-20 min
- **Total: 40-75 minutes** (from /start to grant ready)

---

### 7.4 Financial Metrics

**LLM Costs per Grant:**
```sql
-- Суммарная стоимость генерации гранта
SELECT
    g.grant_id,
    -- Auditor cost
    CAST(json_extract(ar.metadata, '$.cost') AS REAL) as audit_cost,
    -- Research cost
    CAST(json_extract(rr.metadata, '$.cost') AS REAL) as research_cost,
    -- Writing cost
    CAST(json_extract(g.metadata, '$.cost') AS REAL) as writing_cost,
    -- Total
    (
        CAST(json_extract(ar.metadata, '$.cost') AS REAL) +
        CAST(json_extract(rr.metadata, '$.cost') AS REAL) +
        CAST(json_extract(g.metadata, '$.cost') AS REAL)
    ) as total_cost
FROM grants g
LEFT JOIN auditor_results ar ON ar.session_id = (SELECT session_id FROM sessions WHERE anketa_id = g.anketa_id)
LEFT JOIN researcher_research rr ON rr.research_id = g.research_id
WHERE g.created_at >= DATE('now', '-30 days');
```

**Cost Targets (MVP):**
- Auditor: $0.01 per anketa (GigaChat)
- Researcher: $0.03 per grant (Perplexity)
- Writer: $0.10 per grant (GigaChat Pro)
- **Total: ~$0.14 per grant**

**Revenue Model:**
- Free: 1 grant per user
- Basic: $9.99/month - 5 grants
- Pro: $29.99/month - unlimited grants
- Target: 40% conversion to paid (from free users)

---

### 7.5 User Satisfaction Metrics

**NPS Tracking:**
```sql
-- Net Promoter Score по грантам
CREATE TABLE grant_feedback (
    id INTEGER PRIMARY KEY,
    grant_id VARCHAR(50),
    user_id BIGINT,
    nps_score INTEGER CHECK(nps_score >= 0 AND nps_score <= 10),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grant_id) REFERENCES grants(grant_id)
);

-- NPS calculation
SELECT
    COUNT(CASE WHEN nps_score >= 9 THEN 1 END) * 100.0 / COUNT(*) as promoters_pct,
    COUNT(CASE WHEN nps_score <= 6 THEN 1 END) * 100.0 / COUNT(*) as detractors_pct,
    (
        COUNT(CASE WHEN nps_score >= 9 THEN 1 END) -
        COUNT(CASE WHEN nps_score <= 6 THEN 1 END)
    ) * 100.0 / COUNT(*) as nps
FROM grant_feedback
WHERE created_at >= DATE('now', '-30 days');
```

**Target NPS:** > 50 (excellent for SaaS)

---

### 7.6 Success Metrics (North Star)

**Grant Approval Rate by Fund:**
```sql
-- Процент одобрения грантов фондами
SELECT
    json_extract(metadata, '$.target_fund') as fund_name,
    COUNT(*) as total_submitted,
    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
    ROUND(
        COUNT(CASE WHEN status = 'approved' THEN 1 END) * 100.0 / COUNT(*),
        1
    ) as approval_rate_pct
FROM grants
WHERE status IN ('approved', 'rejected')
    AND submitted_at IS NOT NULL
GROUP BY fund_name
ORDER BY approval_rate_pct DESC;
```

**Targets:**
- Президентские гранты: 40-50%
- Росмолодежь: 45-55%
- РФФИ: 30-40%
- **Overall: 40%+** (vs industry average 10-15%)

---

### 7.7 Dashboard Widgets

**Recommended Admin Panel Widgets:**

1. **Pipeline Overview** (real-time)
   - Заявки на каждом этапе
   - Средняя конверсия между этапами
   - Alerts для застрявших заявок

2. **Quality Trends** (weekly)
   - График Auditor scores
   - Процент approved vs needs_revision
   - Топ-3 слабых критерия

3. **Financial Dashboard** (monthly)
   - LLM costs breakdown
   - Cost per successful grant
   - ROI: revenue / costs

4. **User Activity** (daily)
   - New /starts
   - Completed interviews
   - Delivered grants

5. **Success Tracker** (quarterly)
   - Submitted grants
   - Approval rate by fund
   - User testimonials

---

## Changelog

**Version 1.0.0 (2025-10-01)**
- Initial business logic documentation
- Defined MVP scope (hardcoded interviewer)
- Established 6-stage pipeline
- Created decision logic for Auditor and Planner
- Defined core business metrics

---

## Next Steps

1. **Implement Missing Tables:**
   - Create `auditor_results` table
   - Create `planner_structures` table
   - Add foreign key constraints

2. **Build Pipeline Dashboard:**
   - Visualize funnel metrics
   - Real-time status tracking
   - Admin action buttons

3. **Set Up Analytics:**
   - Implement SQL queries from Section 7
   - Create automated reports
   - Set up alerts for anomalies

4. **Test End-to-End Flow:**
   - 10 test users through full pipeline
   - Measure actual conversion rates
   - Validate cost estimates

5. **Prepare for Scale:**
   - Optimize slow queries
   - Add caching for common operations
   - Set up monitoring and logging

---

**Document Maintained By:** Grant Architect Agent
**Last Review:** 2025-10-01
**Next Review:** 2025-11-01
