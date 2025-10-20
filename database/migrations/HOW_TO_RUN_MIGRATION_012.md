# Как запустить миграцию 012: Expert Agent Tables

**Миграция:** 012_add_expert_agent_tables.sql
**Дата создания:** 2025-10-17
**Автор:** grant-architect agent
**Цель:** Добавить таблицы для Expert Agent в существующую БД `grantservice`

---

## ⚠️ Важно перед запуском

### 1. Проверьте версию PostgreSQL

Минимальная версия: **PostgreSQL 14+** (рекомендуется 18.0)

```bash
psql --version
# Должно быть: PostgreSQL 15.x или выше
```

### 2. Убедитесь что БД существует

```bash
# Локально
psql -U postgres -l | grep grantservice

# На сервере 5.35.88.251
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'
psql -h localhost -p 5434 -U grantservice -l | grep grantservice
```

### 3. Сделайте backup БД

**ОБЯЗАТЕЛЬНО!** Перед любой миграцией делайте бэкап.

```bash
# Локально
pg_dump -U postgres grantservice > backup_before_migration_012_$(date +%Y%m%d_%H%M).sql

# На сервере
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'
pg_dump -h localhost -p 5434 -U grantservice grantservice > backup_before_migration_012_$(date +%Y%m%d_%H%M).sql
```

---

## 🚀 Вариант 1: Локальная разработка (Windows)

### Шаг 1: Подготовка

```powershell
# Откройте PowerShell
cd C:\SnowWhiteAI\GrantService

# Проверьте что файл миграции существует
ls database\migrations\012_add_expert_agent_tables.sql
```

### Шаг 2: Создайте тестовую БД (опционально)

```powershell
# Подключиться к postgres
psql -U postgres

# В psql:
CREATE DATABASE grantservice_test;
\q
```

### Шаг 3: Запустите миграцию

```powershell
# Вариант A: На тестовой БД
psql -U postgres -d grantservice_test -f database\migrations\012_add_expert_agent_tables.sql

# Вариант B: На основной БД (осторожно!)
psql -U postgres -d grantservice -f database\migrations\012_add_expert_agent_tables.sql
```

### Шаг 4: Проверка

```powershell
# Подключиться к БД
psql -U postgres -d grantservice_test

# В psql выполнить:
\dt knowledge*
# Должны появиться 6 новых таблиц:
# - knowledge_sources
# - knowledge_sections
# - successful_grant_examples
# - evaluation_criteria
# - knowledge_embeddings
# - knowledge_updates

# Проверить views
\dv v_expert*

# Проверить функции
\df expert_*

# Проверить статистику
SELECT * FROM v_expert_knowledge_stats;

# Проверить что pgvector установлен
\dx vector

\q
```

---

## 🖥️ Вариант 2: Продакшн сервер (5.35.88.251)

### Шаг 1: SSH на сервер

```bash
ssh root@5.35.88.251
```

### Шаг 2: Перейти в директорию проекта

```bash
cd /var/GrantService
```

### Шаг 3: Backup БД

```bash
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'

# Создать backup
pg_dump -h localhost -p 5434 -U grantservice grantservice > backup_before_migration_012_$(date +%Y%m%d_%H%M).sql

# Проверить размер backup
ls -lh backup_before_migration_012_*.sql
```

### Шаг 4: Запустить миграцию

```bash
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'

# Запуск миграции
psql -h localhost -p 5434 -U grantservice -d grantservice -f database/migrations/012_add_expert_agent_tables.sql

# Если есть ошибки, они выведутся
# Если всё ок, увидите:
# CREATE EXTENSION
# CREATE TABLE
# CREATE INDEX
# ...
# NOTICE: Expert agent added to ai_agent_settings
# NOTICE: ============================================
# NOTICE: Expert Agent Migration 012 Complete!
# ...
```

### Шаг 5: Проверка на сервере

```bash
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'

# Подключиться к БД
psql -h localhost -p 5434 -U grantservice -d grantservice

# В psql:
-- Проверить таблицы
\dt knowledge*

-- Проверить количество записей
SELECT
    'knowledge_sources' as table_name,
    COUNT(*) as count
FROM knowledge_sources
UNION ALL
SELECT 'knowledge_sections', COUNT(*) FROM knowledge_sections
UNION ALL
SELECT 'evaluation_criteria', COUNT(*) FROM evaluation_criteria
UNION ALL
SELECT 'successful_grant_examples', COUNT(*) FROM successful_grant_examples;

-- Проверить pgvector
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Проверить статистику
SELECT * FROM v_expert_knowledge_stats;

-- Проверить Expert Agent в настройках
SELECT * FROM ai_agent_settings WHERE agent_name = 'expert';

\q
```

---

## ✅ Что должно получиться

После успешной миграции должны быть созданы:

### Таблицы (6 штук):
1. ✅ `knowledge_sources` - источники знаний
2. ✅ `knowledge_sections` - разделы документов
3. ✅ `successful_grant_examples` - примеры успешных заявок
4. ✅ `evaluation_criteria` - критерии оценки
5. ✅ `knowledge_embeddings` - векторные embeddings (с pgvector!)
6. ✅ `knowledge_updates` - история обновлений

### Views (3 штуки):
1. ✅ `v_expert_active_knowledge` - актуальные знания
2. ✅ `v_expert_knowledge_stats` - статистика по фондам
3. ✅ `v_expert_recent_updates` - последние обновления

### Functions (2 штуки):
1. ✅ `update_expert_updated_at_column()` - триггер для updated_at
2. ✅ `expert_search_similar_sections()` - семантический поиск

### Triggers (4 штуки):
- ✅ На `knowledge_sources`
- ✅ На `knowledge_sections`
- ✅ На `successful_grant_examples`
- ✅ На `evaluation_criteria`

### Extension:
- ✅ `vector` (pgvector) - для векторного поиска

### Sample Data:
- ✅ 3 источника (knowledge_sources)
- ✅ 2 раздела (knowledge_sections)
- ✅ 3 критерия оценки (evaluation_criteria)
- ✅ 1 пример заявки (successful_grant_examples)
- ✅ 1 запись в `ai_agent_settings` для expert agent

---

## 🐛 Troubleshooting

### Ошибка: "extension vector does not exist"

**Проблема:** pgvector не установлен

**Решение:**

```bash
# Установить pgvector
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Перезапустить PostgreSQL
sudo systemctl restart postgresql
```

### Ошибка: "relation already exists"

**Проблема:** Таблицы уже созданы (миграция запускалась ранее)

**Решение 1 (безопасно):** Пропустить миграцию, таблицы уже есть

**Решение 2 (если нужно пересоздать):**

```sql
-- ОСТОРОЖНО! Удалит все данные Expert Agent
DROP TABLE IF EXISTS knowledge_updates CASCADE;
DROP TABLE IF EXISTS knowledge_embeddings CASCADE;
DROP TABLE IF EXISTS evaluation_criteria CASCADE;
DROP TABLE IF EXISTS successful_grant_examples CASCADE;
DROP TABLE IF EXISTS knowledge_sections CASCADE;
DROP TABLE IF EXISTS knowledge_sources CASCADE;

-- Теперь можно запустить миграцию заново
```

### Ошибка: "column embedding does not exist"

**Проблема:** pgvector установлен некорректно

**Решение:**

```sql
-- Проверить что extension создан
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Если нет, создать вручную
CREATE EXTENSION IF NOT EXISTS vector;
```

### Ошибка доступа (permission denied)

**Проблема:** Недостаточно прав у пользователя

**Решение:**

```bash
# Запустить миграцию от имени postgres (superuser)
export PGPASSWORD='UVIA8wA3p2kV6x3ucDB7RQJu'
psql -h localhost -p 5434 -U postgres -d grantservice -f database/migrations/012_add_expert_agent_tables.sql
```

---

## 🔄 Откат миграции (Rollback)

Если что-то пошло не так и нужно откатиться:

### Вариант 1: Восстановить из backup

```bash
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'

# Удалить текущую БД (ОСТОРОЖНО!)
dropdb -h localhost -p 5434 -U grantservice grantservice

# Создать новую БД
createdb -h localhost -p 5434 -U grantservice grantservice

# Восстановить из backup
psql -h localhost -p 5434 -U grantservice -d grantservice < backup_before_migration_012_20251017_1234.sql
```

### Вариант 2: Удалить только таблицы Expert Agent

```sql
-- Подключиться к БД
psql -h localhost -p 5434 -U grantservice -d grantservice

-- Удалить таблицы (CASCADE удалит связанные объекты)
DROP TABLE IF EXISTS knowledge_updates CASCADE;
DROP TABLE IF EXISTS knowledge_embeddings CASCADE;
DROP TABLE IF EXISTS evaluation_criteria CASCADE;
DROP TABLE IF EXISTS successful_grant_examples CASCADE;
DROP TABLE IF EXISTS knowledge_sections CASCADE;
DROP TABLE IF EXISTS knowledge_sources CASCADE;

-- Удалить views
DROP VIEW IF EXISTS v_expert_recent_updates;
DROP VIEW IF EXISTS v_expert_knowledge_stats;
DROP VIEW IF EXISTS v_expert_active_knowledge;

-- Удалить функции
DROP FUNCTION IF EXISTS expert_search_similar_sections;
DROP FUNCTION IF EXISTS update_expert_updated_at_column;

-- Удалить из ai_agent_settings
DELETE FROM ai_agent_settings WHERE agent_name = 'expert';
```

---

## 📊 Проверка после миграции

### SQL скрипт для полной проверки

```sql
-- Сохраните этот скрипт как test_migration_012.sql

-- 1. Проверка таблиц
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename LIKE 'knowledge%' OR tablename = 'evaluation_criteria' OR tablename = 'successful_grant_examples'
ORDER BY tablename;

-- 2. Проверка данных
SELECT
    'knowledge_sources' as table_name,
    COUNT(*) as count
FROM knowledge_sources
UNION ALL
SELECT 'knowledge_sections', COUNT(*) FROM knowledge_sections
UNION ALL
SELECT 'evaluation_criteria', COUNT(*) FROM evaluation_criteria
UNION ALL
SELECT 'successful_grant_examples', COUNT(*) FROM successful_grant_examples
UNION ALL
SELECT 'knowledge_embeddings', COUNT(*) FROM knowledge_embeddings
UNION ALL
SELECT 'knowledge_updates', COUNT(*) FROM knowledge_updates;

-- 3. Проверка индексов
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename LIKE 'knowledge%'
ORDER BY tablename, indexname;

-- 4. Проверка pgvector
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 5. Проверка Expert Agent в настройках
SELECT * FROM ai_agent_settings WHERE agent_name = 'expert';

-- 6. Тест векторного поиска (создать тестовый вектор)
SELECT expert_search_similar_sections(
    query_embedding := array_fill(0.1::float, ARRAY[1536])::vector(1536),
    fund_filter := 'fpg',
    top_k := 5,
    min_similarity := 0.0
);
```

Запустить:
```bash
psql -h localhost -p 5434 -U grantservice -d grantservice -f test_migration_012.sql
```

---

## 📞 Помощь

Если возникли проблемы:

1. Проверьте логи PostgreSQL:
   ```bash
   tail -f /var/log/postgresql/postgresql-18-main.log
   ```

2. Проверьте версию PostgreSQL:
   ```bash
   psql --version
   ```

3. Проверьте доступность БД:
   ```bash
   pg_isready -h localhost -p 5434
   ```

4. Посмотрите документацию:
   - `doc/EXPERT_AGENT.md` - полная документация Expert Agent
   - `00-Project-Stages/2025-10-17_Expert-Agent-Architecture/` - детали архитектуры

---

**Дата создания:** 2025-10-17
**Последнее обновление:** 2025-10-17

✅ **МИГРАЦИЯ ГОТОВА К ЗАПУСКУ!**
