# Expert Agent - Центральная база знаний

**Дата создания:** 2025-10-17
**Версия:** 1.0
**Авторы:** grant-architect agent
**Статус:** 🔄 В разработке (Этап 1: Миграция БД)

---

## 📋 Оглавление

1. [Обзор](#обзор)
2. [Архитектура](#архитектура)
3. [База данных](#база-данных)
4. [API](#api)
5. [Интеграция с агентами](#интеграция-с-агентами)
6. [Установка](#установка)
7. [Использование](#использование)
8. [Разработка](#разработка)

---

## Обзор

### Что такое Expert Agent?

**Expert Agent** - это центральный AI-агент системы GrantService, который:

- 🗄️ **Хранит базу знаний** в PostgreSQL (вместо markdown файлов)
- 🔍 **Выполняет семантический поиск** через векторные embeddings (pgvector)
- 🎓 **Дообучает других агентов** (Writer, Reviewer, Researcher, Interviewer)
- 🔄 **Автоматически обновляет знания** через Researcher agent
- ✨ **Служит единым источником правды** о требованиях грантов

### Зачем нужен Expert Agent?

**Проблемы текущего подхода:**
- База знаний в markdown (329 KB) загружается целиком
- Нет семантического поиска - только текстовый поиск
- Обновление требований = ручное редактирование файлов
- Агенты не "обучаются" динамически
- Нет версионности и истории изменений

**Решение через Expert Agent:**
- ⚡ **Быстрее:** Векторный поиск возвращает только релевантное (5-10 KB вместо 329 KB)
- 📊 **Актуальнее:** БД обновляется автоматически через Researcher
- 🎯 **Релевантнее:** Семантический поиск находит похожие разделы
- 📈 **Версионность:** История всех изменений в `knowledge_updates`
- 🔄 **Динамическое обучение:** Агенты всегда работают с последней информацией

---

## Архитектура

### High-Level Design

```
┌────────────────────────────────────────────────┐
│         GrantService Ecosystem                 │
└────────────────────────────────────────────────┘

┌──────────────┐         ┌────────────────────────┐
│  Telegram    │         │    n8n Workflow        │
│     Bot      │◄────────│   Orchestrator         │
└──────────────┘         └────────────────────────┘
                                   │
            ┌──────────────────────┼────────────────┐
            │                      │                 │
            ▼                      ▼                 ▼
    ┌────────────┐          ┌──────────┐     ┌──────────┐
    │   Writer   │          │ Reviewer │     │Interview │
    │   Agent    │          │  Agent   │     │  Agent   │
    └────────────┘          └──────────┘     └──────────┘
            │                      │                 │
            └──────────────────────┼─────────────────┘
                                   │
            ┌──────────────────────▼─────────────────┐
            │       ⭐ EXPERT AGENT ⭐                │
            │     (Knowledge Hub + Router)           │
            │                                        │
            │  ┌──────────────────────────────┐     │
            │  │ • query_knowledge()          │     │
            │  │ • train_agent()              │     │
            │  │ • update_knowledge()         │     │
            │  │ • vector_search()            │     │
            │  └──────────────────────────────┘     │
            └────────────────┬───────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌────────────┐      ┌────────────┐
│  PostgreSQL  │    │ Researcher │      │  GigaChat  │
│  + pgvector  │    │   Agent    │      │    API     │
└──────────────┘    └────────────┘      └────────────┘
        │
        └── Tables:
            • knowledge_sources
            • knowledge_sections
            • successful_grant_examples
            • evaluation_criteria
            • knowledge_embeddings (vector!)
            • knowledge_updates
```

### Компоненты

| Компонент | Технология | Назначение |
|-----------|-----------|-----------|
| **Expert Agent Service** | Python 3.11 + FastAPI | REST API для запросов к БЗ |
| **PostgreSQL** | PostgreSQL 18.0 | Хранилище знаний |
| **pgvector** | Extension 0.5+ | Векторный поиск |
| **Embeddings** | ruBERT / sberGPT | Генерация векторов |
| **LLM** | GigaChat / Claude Code | Генерация ответов |
| **n8n** | Self-hosted | Оркестрация агентов |

---

## База данных

### Схема

Expert Agent использует **6 новых таблиц** в существующей БД `grantservice`:

#### 1. `knowledge_sources` - Источники знаний

Хранит информацию об источниках (статьи с сайта ФПГ, методички, примеры).

```sql
CREATE TABLE knowledge_sources (
    id SERIAL PRIMARY KEY,
    fund_name VARCHAR(100) NOT NULL,      -- 'fpg', 'kultura', 'rosmolodjezh'
    source_type VARCHAR(50) NOT NULL,     -- 'official_article', 'example'
    title TEXT NOT NULL,
    url TEXT,
    version VARCHAR(20),                  -- '2025', '2024'
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 5,
    metadata JSONB,
    downloaded_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. `knowledge_sections` - Разделы документов

Разделы документов (требования, примеры, советы).

```sql
CREATE TABLE knowledge_sections (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES knowledge_sources(id),
    section_type VARCHAR(50) NOT NULL,    -- 'requirement', 'example', 'tip'
    section_name TEXT NOT NULL,           -- "Цель проекта", "Бюджет"
    content TEXT NOT NULL,
    char_limit INTEGER,                   -- 300, 5000, etc.
    priority INTEGER DEFAULT 5,
    tags TEXT[],
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. `successful_grant_examples` - Примеры успешных заявок

```sql
CREATE TABLE successful_grant_examples (
    id SERIAL PRIMARY KEY,
    fund_name VARCHAR(100) NOT NULL,
    application_number VARCHAR(50),
    year INTEGER NOT NULL,
    direction VARCHAR(200),
    organization_name VARCHAR(200),
    region VARCHAR(100),
    requested_amount DECIMAL(12, 2),
    awarded_amount DECIMAL(12, 2),
    cofinancing_amount DECIMAL(12, 2),
    status VARCHAR(50) DEFAULT 'winner',
    full_text TEXT,
    extracted_parts JSONB,                -- Структурированные разделы
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. `evaluation_criteria` - Критерии оценки

10 критериев экспертной оценки ФПГ (каждый до 10 баллов).

```sql
CREATE TABLE evaluation_criteria (
    id SERIAL PRIMARY KEY,
    fund_name VARCHAR(100) NOT NULL,
    criterion_number INTEGER,             -- 1-10 для ФПГ
    criterion_name VARCHAR(200) NOT NULL,
    max_score INTEGER NOT NULL DEFAULT 10,
    description TEXT NOT NULL,
    examples TEXT,
    tips TEXT,
    common_mistakes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5. `knowledge_embeddings` - Векторные embeddings ⚡

**Самая важная таблица!** Хранит векторные представления разделов для семантического поиска.

```sql
CREATE TABLE knowledge_embeddings (
    id SERIAL PRIMARY KEY,
    section_id INTEGER REFERENCES knowledge_sections(id),
    embedding vector(1536),               -- Вектор 1536 измерений!
    model_name VARCHAR(50) DEFAULT 'rubert',
    model_version VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW индекс для быстрого поиска
CREATE INDEX idx_knowledge_embeddings_hnsw
ON knowledge_embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Как работает векторный поиск:**

1. Вопрос пользователя → Embedding (1536-мерный вектор)
2. Поиск похожих векторов через HNSW индекс
3. Cosine similarity для ранжирования
4. Возврат top-5 наиболее релевантных разделов

#### 6. `knowledge_updates` - История обновлений

Audit log всех изменений в базе знаний.

```sql
CREATE TABLE knowledge_updates (
    id SERIAL PRIMARY KEY,
    updated_by VARCHAR(50) NOT NULL,      -- 'expert_agent', 'researcher', 'admin'
    update_type VARCHAR(50) NOT NULL,     -- 'new', 'modified', 'deleted'
    description TEXT,
    affected_tables TEXT[],
    record_ids INTEGER[],
    old_values JSONB,                     -- Для rollback
    new_values JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Views и Functions

#### View: `v_expert_active_knowledge`

Актуальные знания с embeddings:

```sql
SELECT * FROM v_expert_active_knowledge
WHERE fund_name = 'fpg';
```

#### Function: `expert_search_similar_sections()`

Семантический поиск:

```sql
SELECT * FROM expert_search_similar_sections(
    query_embedding := '[0.123, -0.456, ...]'::vector(1536),
    fund_filter := 'fpg',
    top_k := 5,
    min_similarity := 0.75
);
```

---

## API

### Python Class: `ExpertAgent`

```python
from expert_agent import ExpertAgent

# Инициализация
async with ExpertAgent(db_pool, embeddings_service, llm_client) as expert:

    # 1. Запрос знаний (семантический поиск)
    result = await expert.query_knowledge(
        question="Какие ограничения по символам в разделе 'О проекте'?",
        fund="fpg",
        top_k=5
    )
    print(result['answer'])
    print(f"Confidence: {result['confidence']:.2%}")

    # 2. Дообучить агента
    result = await expert.train_agent(
        agent_name="writer",
        fund="fpg",
        section="project_goals"
    )
    print(f"Updated prompt for Writer: {result['updated_prompt']}")

    # 3. Обновить знания через Researcher
    result = await expert.update_knowledge(
        topic="fpg_requirements_2025",
        trigger="manual",
        validate=True
    )
    print(f"Added {result['sections_added']} new sections")

    # 4. Health check
    health = await expert.health_check()
    print(f"Status: {health['status']}")
```

### REST API Endpoints (FastAPI)

```python
# GET /api/expert/query
POST /api/expert/query
{
    "question": "Какие требования к целям проекта для ФПГ?",
    "fund": "fpg",
    "top_k": 5,
    "min_similarity": 0.75
}

Response:
{
    "answer": "Цель проекта должна соответствовать SMART критериям...",
    "sources": [42, 84, 91],
    "confidence": 0.92,
    "relevant_sections": [...]
}

# POST /api/expert/train
POST /api/expert/train
{
    "agent_name": "writer",
    "fund": "fpg",
    "format": "markdown"
}

Response:
{
    "status": "success",
    "updated_prompt": "...",
    "knowledge_items": 15,
    "version": "2025-10-17_v1"
}

# POST /api/expert/update
POST /api/expert/update
{
    "topic": "fpg_requirements_2025",
    "fund": "fpg",
    "trigger": "manual",
    "validate": true
}

Response:
{
    "status": "success",
    "sections_added": 5,
    "sections_updated": 2
}

# GET /api/expert/health
GET /api/expert/health

Response:
{
    "status": "healthy",
    "database": {"connected": true, "version": "18.0"},
    "statistics": {
        "total_sources": 15,
        "active_sources": 12,
        "sections": 127,
        "embeddings": 127
    }
}
```

---

## Интеграция с агентами

### 1. Writer Agent → Expert

**Старый workflow:**
```
User → Writer → Читает весь UNIFIED_KNOWLEDGE_BASE.md (329 KB)
        → Генерирует текст
```

**Новый workflow:**
```
User → Writer → Expert.query_knowledge("Требования к целям?")
              → Expert возвращает только релевантные разделы (5-10 KB)
              → Writer генерирует текст
```

**Код интеграции:**

```python
# telegram-bot/agents/writer_agent.py

class WriterAgent(BaseAgent):
    def __init__(self, db, llm_provider="claude_code"):
        super().__init__("writer", db, llm_provider)
        self.expert = ExpertAgent(db, embeddings_service, llm_client)

    async def write_section(self, section_name: str, user_input: str):
        """Генерация раздела заявки"""

        # 1. Запрос требований у Expert
        requirements = await self.expert.query_knowledge(
            question=f"Какие требования к разделу '{section_name}' для ФПГ?",
            fund="fpg",
            top_k=5
        )

        # 2. Формирование промпта с требованиями
        prompt = f"""
Требования к разделу '{section_name}':
{requirements['answer']}

Пользовательский ввод:
{user_input}

Напиши раздел '{section_name}' для грантовой заявки.
        """

        # 3. Генерация через LLM
        result = await self.llm.generate(prompt)

        return result
```

### 2. Reviewer Agent → Expert

**Задача:** Оценить заявку по 10 критериям ФПГ

```python
class ReviewerAgent(BaseAgent):
    async def review_application(self, application_id: str):
        """Оценка заявки"""

        # Получить критерии от Expert
        result = await self.expert.query_knowledge(
            question="Дай все 10 критериев оценки для ФПГ",
            fund="fpg"
        )

        criteria = result['relevant_sections']  # 10 критериев

        # Оценить заявку по каждому критерию
        scores = []
        for criterion in criteria:
            score = await self._evaluate_criterion(
                application_id,
                criterion
            )
            scores.append(score)

        total_score = sum(scores)
        return {'total_score': total_score, 'criteria_scores': scores}
```

### 3. Researcher ↔ Expert (двусторонняя!)

**Сценарий 1: Expert вызывает Researcher**

```python
# Еженедельное обновление БЗ
@scheduler.scheduled_job('cron', day_of_week='mon', hour=3)
async def update_knowledge_base():
    """Автообновление базы знаний"""

    expert = ExpertAgent(...)

    # Expert → Researcher: "Собери новую информацию"
    await expert.update_knowledge(
        topic="fpg_requirements_2025",
        trigger="scheduled"
    )
```

**Сценарий 2: Researcher использует Expert**

```python
class ResearcherAgent(BaseAgent):
    async def find_examples(self, direction: str):
        """Найти примеры заявок"""

        # Researcher → Expert: "Примеры по направлению X"
        result = await self.expert.query_knowledge(
            question=f"Примеры успешных заявок по направлению '{direction}'",
            fund="fpg"
        )

        return result['relevant_sections']
```

---

## Установка

### Шаг 1: Миграция базы данных

**Файл:** `database/migrations/012_add_expert_agent_tables.sql`

#### Локальная разработка (Windows):

```bash
# 1. Подключиться к локальной БД
cd C:\SnowWhiteAI\GrantService

# 2. Создать тестовую БД (опционально)
psql -U postgres -c "CREATE DATABASE grantservice_test;"

# 3. Выполнить миграцию
psql -U postgres -d grantservice_test -f database/migrations/012_add_expert_agent_tables.sql

# 4. Проверить
psql -U postgres -d grantservice_test -c "SELECT * FROM v_expert_knowledge_stats;"
```

#### Продакшн (сервер 5.35.88.251):

```bash
# SSH на сервер
ssh root@5.35.88.251

cd /var/GrantService

# Backup БД перед миграцией
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'
pg_dump -h localhost -p 5434 -U grantservice grantservice > backup_before_expert_$(date +%Y%m%d).sql

# Выполнить миграцию
psql -h localhost -p 5434 -U grantservice -d grantservice -f database/migrations/012_add_expert_agent_tables.sql

# Проверить
psql -h localhost -p 5434 -U grantservice -d grantservice -c "\dt knowledge*"
psql -h localhost -p 5434 -U grantservice -d grantservice -c "SELECT * FROM v_expert_knowledge_stats;"
```

### Шаг 2: Установить зависимости Python

```bash
cd C:\SnowWhiteAI\GrantService

# Добавить в requirements.txt
echo "pgvector==0.2.3" >> requirements.txt
echo "asyncpg==0.29.0" >> requirements.txt
echo "sentence-transformers==2.2.2" >> requirements.txt
echo "numpy==1.24.3" >> requirements.txt

# Установить
pip install -r requirements.txt
```

### Шаг 3: Копировать код Expert Agent

```bash
# Скопировать из 00-Project-Stages
cp "00-Project-Stages/2025-10-17_Expert-Agent-Architecture/03_Implementation/expert_agent.py" \
   "shared/agents/expert_agent.py"
```

### Шаг 4: Настроить переменные окружения

Добавить в `config/.env`:

```bash
# Expert Agent Settings
EXPERT_AGENT_ENABLED=true
EXPERT_AGENT_EMBEDDING_MODEL=rubert
EXPERT_AGENT_VECTOR_SEARCH_THRESHOLD=0.75
EXPERT_AGENT_DEFAULT_FUND=fpg

# Embeddings API (выбрать один)
# Вариант 1: ruBERT локально
RUBERT_MODEL_PATH=/path/to/rubert-tiny2

# Вариант 2: sberGPT embeddings API
SBER_API_KEY=your_sber_api_key

# Вариант 3: OpenAI (fallback)
OPENAI_API_KEY=your_openai_key
```

---

## Использование

### Миграция данных (Этап 2)

После установки таблиц, нужно мигрировать данные из `fpg_docs_2025/UNIFIED_KNOWLEDGE_BASE.md`:

```bash
# Запустить скрипт миграции
python scripts/migrate_knowledge_to_expert.py

# Что делает скрипт:
# 1. Парсит UNIFIED_KNOWLEDGE_BASE.md
# 2. Разбивает на разделы
# 3. Загружает в knowledge_sources и knowledge_sections
# 4. Создает embeddings для каждого раздела
# 5. Сохраняет в knowledge_embeddings
```

### Тестирование

```python
# tests/test_expert_agent.py

import pytest
from shared.agents.expert_agent import ExpertAgent

@pytest.mark.asyncio
async def test_query_knowledge():
    """Тест запроса знаний"""
    expert = ExpertAgent(db_pool, embeddings_service, llm_client)

    result = await expert.query_knowledge(
        question="Какие ограничения символов в разделе 'О проекте'?",
        fund="fpg"
    )

    assert result['confidence'] > 0.8
    assert len(result['sources']) > 0
    assert 'символ' in result['answer'].lower()

@pytest.mark.asyncio
async def test_train_writer():
    """Тест дообучения Writer агента"""
    expert = ExpertAgent(...)

    result = await expert.train_agent("writer", fund="fpg")

    assert result['status'] == 'success'
    assert result['knowledge_items'] > 10
```

### Мониторинг

```sql
-- Статистика по базе знаний
SELECT * FROM v_expert_knowledge_stats;

-- Последние обновления
SELECT * FROM v_expert_recent_updates LIMIT 10;

-- Health check
SELECT
    (SELECT COUNT(*) FROM knowledge_sources WHERE is_active = true) as active_sources,
    (SELECT COUNT(*) FROM knowledge_sections) as total_sections,
    (SELECT COUNT(*) FROM knowledge_embeddings) as total_embeddings,
    (SELECT COUNT(*) FROM knowledge_updates WHERE created_at >= NOW() - INTERVAL '7 days') as updates_last_week;
```

---

## Разработка

### Добавить новый фонд

```sql
-- 1. Добавить источники
INSERT INTO knowledge_sources (fund_name, source_type, title, url, version)
VALUES ('kultura', 'official_article', 'Требования КультураРФ', 'https://...', '2025');

-- 2. Добавить разделы
INSERT INTO knowledge_sections (source_id, section_type, section_name, content)
VALUES (
    (SELECT id FROM knowledge_sources WHERE fund_name = 'kultura' LIMIT 1),
    'requirement',
    'Название проекта',
    'Требования к названию...'
);

-- 3. Создать embeddings
-- (автоматически через скрипт)
python scripts/create_embeddings_for_fund.py --fund kultura
```

### Расширить API

```python
# shared/agents/expert_agent.py

class ExpertAgent:
    # Добавить новый метод
    async def compare_applications(
        self,
        app1_id: str,
        app2_id: str,
        fund: str = 'fpg'
    ) -> Dict:
        """Сравнить две заявки по критериям"""

        # Получить критерии
        criteria = await self._get_reviewer_knowledge(fund)

        # Сравнить
        comparison = {}
        for criterion in criteria:
            score1 = await self._evaluate_app(app1_id, criterion)
            score2 = await self._evaluate_app(app2_id, criterion)
            comparison[criterion['criterion_name']] = {
                'app1': score1,
                'app2': score2,
                'diff': score2 - score1
            }

        return comparison
```

---

## Roadmap

### ✅ Этап 0: Документирование (Завершён)
- [x] Архитектура
- [x] SQL схема
- [x] Python код
- [x] Документация

### 🔄 Этап 1: Database Schema (В процессе)
- [x] Создать миграцию 012
- [ ] Запустить на локальной БД
- [ ] Запустить на продакшн БД
- [ ] Тесты схемы

### ⏳ Этап 2: Data Migration
- [ ] Парсинг UNIFIED_KNOWLEDGE_BASE.md
- [ ] Создание embeddings (ruBERT)
- [ ] Загрузка в БД
- [ ] Валидация данных

### ⏳ Этап 3: Expert Agent Implementation
- [ ] Реализация ExpertAgent класса
- [ ] FastAPI endpoints
- [ ] Unit-тесты
- [ ] Integration-тесты

### ⏳ Этап 4: Writer Integration
- [ ] Модификация Writer для использования Expert
- [ ] A/B тестирование
- [ ] Метрики качества

### ⏳ Этап 5: Full Integration
- [ ] Интеграция всех агентов
- [ ] Web Admin панель
- [ ] Мониторинг
- [ ] Документация пользователя

---

## Связанные документы

- **Архитектура:** `00-Project-Stages/2025-10-17_Expert-Agent-Architecture/01_Planning/architecture.md`
- **STATUS:** `STATUS.md`
- **SESSION CONTEXT:** `SESSION_CONTEXT_2025-10-17.md`
- **AI Agents:** `doc/AI_AGENTS_SETTINGS_ARCHITECTURE.md`
- **Database:** `doc/DATABASE.md`
- **Architecture:** `doc/ARCHITECTURE.md`

---

**Дата последнего обновления:** 2025-10-17
**Следующий шаг:** Запустить миграцию 012 на локальной БД
