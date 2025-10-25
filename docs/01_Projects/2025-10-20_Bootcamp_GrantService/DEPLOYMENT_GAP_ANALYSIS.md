# 🔍 DEPLOYMENT GAP ANALYSIS
## Сравнение: Production Code vs Deployment Plan

**Дата анализа:** 2025-10-24
**Production Server:** 5.35.88.251 (Beget VPS)
**Project Path:** `/var/GrantService/`

---

## 📊 ЧТО УЖЕ ЕСТЬ В PRODUCTION

### 1. Database Tables (PostgreSQL 18, port 5434)

#### ✅ ЕСТЬ:
```sql
-- Таблица пользователей
users (id, telegram_id, username, role, ...)

-- Таблица сессий (с anketa_id!)
sessions (id, telegram_id, anketa_id, interview_data, ...)

-- Таблица грантовых заявок (старый формат)
grant_applications (id, application_number, content_json, ...)

-- Таблица финальных грантов (ТРЕБУЕТ research_id!)
grants (
    id, grant_id, anketa_id,
    research_id NOT NULL,  -- <-- ПРОБЛЕМА!
    grant_content TEXT,
    grant_sections JSONB,
    llm_provider, status, ...
)
```

#### ❌ НЕТ:
```sql
-- Отдельной таблицы anketas НЕТ (используется sessions.anketa_id)

-- Таблицы для ProductionWriter НЕТ
-- grants требует research_id, а ProductionWriter не использует Researcher
```

---

### 2. Code Structure

#### ✅ ЕСТЬ в `agents/`:
```
agents/
├── writer_agent.py (25 KB)
├── writer_agent_v2.py (71 KB)
├── researcher_agent.py (21 KB)
├── researcher_agent_v2.py (55 KB)
├── auditor_agent.py (55 KB)
├── interactive_interviewer_agent_v2.py (21 KB)
└── [другие агенты]
```

#### ❌ НЕТ:
```
agents/
└── production_writer.py  <-- НЕТ!
```

---

### 3. Telegram Bot Handlers

#### ✅ ЕСТЬ в `telegram-bot/handlers/`:
```
handlers/
├── interactive_interview_handler.py (16 KB)
└── auth_middleware.py
```

#### ❌ НЕТ:
```
handlers/
└── grant_handler.py  <-- НЕТ!
```

---

### 4. Database Methods

**Нужно проверить:** Есть ли методы для работы с grants в существующем DB wrapper?

---

## 🔧 ЧТО НУЖНО ДОБАВИТЬ

### Option 1: Использовать существующую таблицу `grants` ✅ РЕКОМЕНДУЕТСЯ

**Решение:** Сделать `research_id` NULLABLE в таблице `grants`

```sql
-- Migration: 014_make_research_id_nullable.sql

ALTER TABLE grants
ALTER COLUMN research_id DROP NOT NULL;

-- Добавить новые колонки для ProductionWriter
ALTER TABLE grants
ADD COLUMN character_count INTEGER,
ADD COLUMN word_count INTEGER,
ADD COLUMN sections_generated INTEGER DEFAULT 10,
ADD COLUMN duration_seconds FLOAT,
ADD COLUMN qdrant_queries INTEGER DEFAULT 0;

-- Комментарии
COMMENT ON COLUMN grants.research_id IS 'Research ID (nullable for ProductionWriter workflow)';
COMMENT ON COLUMN grants.character_count IS 'Grant length in characters (target: 44K+)';
COMMENT ON COLUMN grants.duration_seconds IS 'Generation time in seconds (target: <180s)';
```

**Преимущества:**
- ✅ Не нужно создавать новую таблицу
- ✅ Используем существующую infrastructure
- ✅ Совместимость со старым workflow (Researcher + Writer)
- ✅ Новый workflow (ProductionWriter без Researcher)

**Недостатки:**
- ⚠️ Нужна миграция БД

---

### Option 2: Создать новую таблицу `production_grants`

```sql
-- Migration: 014_add_production_grants.sql

CREATE TABLE production_grants (
    id SERIAL PRIMARY KEY,
    grant_id VARCHAR(50) UNIQUE NOT NULL,
    anketa_id VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    grant_content TEXT NOT NULL,
    character_count INTEGER NOT NULL,
    word_count INTEGER,
    sections_generated INTEGER DEFAULT 10,
    duration_seconds FLOAT,
    qdrant_queries INTEGER DEFAULT 0,
    llm_provider VARCHAR(50) DEFAULT 'gigachat',
    status VARCHAR(30) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_to_user_at TIMESTAMP,
    admin_notified_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (anketa_id) REFERENCES sessions(anketa_id) ON DELETE RESTRICT
);

-- Индексы
CREATE INDEX idx_production_grants_grant_id ON production_grants(grant_id);
CREATE INDEX idx_production_grants_anketa_id ON production_grants(anketa_id);
CREATE INDEX idx_production_grants_user_id ON production_grants(user_id);
CREATE INDEX idx_production_grants_status ON production_grants(status);
CREATE INDEX idx_production_grants_created ON production_grants(created_at DESC);

COMMENT ON TABLE production_grants IS 'ProductionWriter generated grants (no research phase)';
```

**Преимущества:**
- ✅ Чистая separation of concerns
- ✅ Не трогаем существующие таблицы
- ✅ Специфичная структура для ProductionWriter

**Недостатки:**
- ⚠️ Дублирование похожей структуры
- ⚠️ Две таблицы для грантов (grants + production_grants)

---

## 📋 РЕКОМЕНДАЦИЯ

### ✅ ВЫБИРАЕМ OPTION 1: Модифицировать `grants` таблицу

**Причины:**
1. Таблица `grants` уже есть и используется
2. Добавление nullable research_id - минимальное изменение
3. Поддержка обоих workflow (старый + новый)
4. Меньше дублирования кода

**План deployment:**

### Phase 1: Database Migration (15 минут)

```bash
# 1. SSH на production
ssh root@5.35.88.251

# 2. Создать миграцию
cd /var/GrantService/database/migrations
nano 014_update_grants_for_production_writer.sql

# 3. Применить миграцию
PGPASSWORD=${DB_PASSWORD} psql -h localhost -p 5434 -U grantservice -d grantservice \
  -f 014_update_grants_for_production_writer.sql
```

### Phase 2: Code Deployment (30 минут)

```bash
# Локально (C:\SnowWhiteAI\GrantService)
# 1. Скопировать ProductionWriter
copy ..\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\lib\production_writer.py \
     agents\production_writer.py

# 2. Update requirements.txt
echo qdrant-client==1.7.0 >> requirements.txt
echo sentence-transformers==2.2.2 >> requirements.txt

# 3. Commit & push (GitHub Actions задеплоит)
git add agents/production_writer.py requirements.txt
git commit -m "feat: Add ProductionWriter"
git push origin main
```

### Phase 3: Integration (30 минут)

```bash
# Создать grant_handler.py
# Добавить DB methods
# Зарегистрировать handler
```

### Phase 4: Testing (15 минут)

```bash
# Manual test через /generate_grant
# Проверить metrics в БД
```

**Total time:** ~1.5 часа (не 4 часа!)

---

## 🔍 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА

### Нужно проверить в production code:

1. **Database wrapper:**
   - Где находится DB wrapper класс?
   - Какие методы уже есть для работы с grants?

2. **Writer Agent integration:**
   - Как writer_agent_v2.py сохраняет в grants?
   - Можем ли переиспользовать?

3. **Telegram Bot:**
   - Как unified_bot.py регистрирует handlers?
   - Где импортируются DB классы?

---

## ✅ NEXT STEPS

1. **Прочитать:**
   - writer_agent_v2.py (как работает с grants таблицей)
   - Найти DB wrapper класс
   - Посмотреть unified_bot.py

2. **Принять решение:**
   - Option 1 (модифицировать grants) ИЛИ
   - Option 2 (создать production_grants)

3. **Создать миграцию:**
   - 014_update_grants_for_production_writer.sql

4. **Deployment:**
   - Следовать скорректированному плану (1.5 часа)

---

**Prepared by:** Claude Code
**Date:** 2025-10-24
**Status:** ⏸️ DEPLOYMENT PAUSED - WAITING FOR DECISION
