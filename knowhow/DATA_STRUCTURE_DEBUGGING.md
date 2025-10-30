# Debugging Data Structures - Nested Dicts

**Дата:** 2025-10-29
**Источник:** Iteration 62 - N/A Bug Fix
**Статус:** ✅ Проверено в production

---

## 🐛 Проблема: N/A вместо данных

### Симптом

Файл `research_*.txt` показывает:
```
=== ЗАПРОС 1 ===

Вопрос: официальная статистика...

Ответ:
N/A

------------------------------------------------------------
```

Вместо ожидаемого:
```
Ответ:
РЕЗЮМЕ: По данным Росстата за 2022-2024 годы...
[200-300 слов реального текста]
```

### Root Cause

**Mismatch между структурой данных:**

**Что возвращает API** (`researcher_agent.py:_websearch_simple()`):
```python
{
    'query': 'официальная статистика...',
    'result': {                    # ← Nested structure
        'summary': '[Real answer]',
        'raw_response': '[Full text]'
    }
}
```

**Что искал парсер** (`file_generators.py:generate_research_txt()`):
```python
answer = query_data.get('answer', 'N/A')  # ← Wrong key!
```

**Результат:** Ключ `'answer'` не существует → возвращается default `'N/A'`

---

## 🔍 Методология Debugging

### Шаг 1: Найти где генерируются данные

**Вопрос:** Откуда берутся research results?

**Поиск:**
```bash
grep -r "websearch_simple" agents/
grep -r "research_anketa" agents/
```

**Найдено:**
- `agents/researcher_agent.py` - метод `research_anketa()` и `_websearch_simple()`

### Шаг 2: Прочитать код генерации

**File:** `agents/researcher_agent.py:393-469`

```python
def _websearch_simple(self, query: str, ...) -> Dict:
    """
    Perform WebSearch using Claude Code
    Returns: {
        'query': str,
        'result': {
            'summary': str,    # ← Actual answer here!
            'raw_response': str
        }
    }
    """
    # ... WebSearch call ...
    return {
        'query': query,
        'result': {
            'summary': claude_response,
            'raw_response': claude_response
        }
    }
```

**Вывод:** Данные ВЛОЖЕНЫ в `result.summary`, а не в плоском `answer`

### Шаг 3: Найти где читаются данные

**Вопрос:** Где файл генерируется?

**Поиск:**
```bash
grep -r "generate_research_txt" shared/
grep -r "research_.*\.txt" telegram-bot/
```

**Найдено:**
- `shared/telegram_utils/file_generators.py:generate_research_txt()`

### Шаг 4: Сравнить структуры

**Ожидаемая структура (parser):**
```python
# file_generators.py:462
answer = query_data.get('answer', 'N/A')
```

**Реальная структура (API):**
```python
# researcher_agent.py:469
return {'query': '...', 'result': {'summary': '...'}}
```

**Mismatch найден!** ❌

### Шаг 5: Применить фикс

**BEFORE:**
```python
answer = query_data.get('answer', 'N/A')
```

**AFTER:**
```python
result = query_data.get('result', {})
answer = result.get('summary', 'N/A')
```

---

## 🛠️ Паттерны Extraction

### Паттерн 1: Flat Dict (простой)

**Структура:**
```python
data = {'name': 'John', 'age': 30}
```

**Extraction:**
```python
name = data.get('name', 'Unknown')
```

### Паттерн 2: Nested Dict (вложенный)

**Структура:**
```python
data = {
    'user': {
        'name': 'John',
        'profile': {
            'email': 'john@example.com'
        }
    }
}
```

**Extraction (ПРАВИЛЬНО):**
```python
user = data.get('user', {})
name = user.get('name', 'Unknown')

profile = user.get('profile', {})
email = profile.get('email', 'N/A')
```

**Extraction (НЕПРАВИЛЬНО):**
```python
# ❌ KeyError если 'user' не существует
name = data['user']['name']

# ❌ Пропускает вложенность
name = data.get('name', 'Unknown')  # Всегда 'Unknown'!
```

### Паттерн 3: List of Dicts

**Структура:**
```python
data = {
    'queries': [
        {'query': 'Q1', 'result': {'summary': 'A1'}},
        {'query': 'Q2', 'result': {'summary': 'A2'}}
    ]
}
```

**Extraction:**
```python
queries = data.get('queries', [])
for query_data in queries:
    query_text = query_data.get('query', 'N/A')

    # Извлечь вложенный result
    result = query_data.get('result', {})
    answer = result.get('summary', 'N/A')
```

---

## 📋 Debugging Checklist

**Когда данные не извлекаются (показывает N/A, None, default):**

1. **[ ] Найти источник данных**
   - Где данные генерируются? (API, database, agent)
   - Какой метод возвращает данные?

2. **[ ] Прочитать структуру возвращаемых данных**
   - Открыть файл с генерацией
   - Найти `return` statement
   - Записать структуру на бумаге

3. **[ ] Найти потребителя данных**
   - Где данные используются?
   - Какие ключи ищет код?

4. **[ ] Сравнить структуры**
   - Совпадают ли ключи?
   - Правильная ли вложенность?
   - Типы данных совпадают?

5. **[ ] Применить фикс**
   - Изменить extraction код
   - Добавить `.get()` для безопасности
   - Использовать defaults (`'N/A'`, `{}`, `[]`)

6. **[ ] Протестировать**
   - Локально с реальными данными
   - На production с real user flow
   - Проверить edge cases (пустые данные, None)

---

## 🎯 Best Practices

### 1. Всегда используй `.get()` для dict

```python
# ❌ BAD - может вызвать KeyError
value = data['key']

# ✅ GOOD - безопасно, возвращает default
value = data.get('key', 'default')
```

### 2. Проверяй вложенность перед доступом

```python
# ❌ BAD - KeyError если 'result' нет
answer = data['result']['summary']

# ✅ GOOD - безопасно извлекает
result = data.get('result', {})
answer = result.get('summary', 'N/A')
```

### 3. Используй meaningful defaults

```python
# ❌ BAD - default None скрывает проблему
answer = data.get('answer', None)

# ✅ GOOD - default показывает что данных нет
answer = data.get('answer', 'N/A')
count = data.get('count', 0)
items = data.get('items', [])
```

### 4. Документируй структуру данных

```python
def process_research(research_data: Dict[str, Any]) -> str:
    """
    Process research results

    Expected structure:
    {
        'queries': [
            {
                'query': str,
                'result': {
                    'summary': str,
                    'raw_response': str
                }
            }
        ]
    }
    """
    queries = research_data.get('queries', [])
    # ...
```

### 5. Добавляй комментарии при извлечении

```python
# Extract answer from nested 'result.summary'
result = query_data.get('result', {})
answer = result.get('summary', 'N/A')
```

---

## 🔍 Debugging Tools

### 1. Print структуру данных

```python
import json
print(json.dumps(data, indent=2, ensure_ascii=False))
```

### 2. Проверь тип данных

```python
print(f"Type: {type(data)}")
print(f"Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
```

### 3. Trace data flow

```python
# В начале функции
logger.info(f"Input data: {data}")

# После extraction
logger.info(f"Extracted answer: {answer}")
```

### 4. Unit test с реальной структурой

```python
def test_extract_nested_answer():
    # Копируем РЕАЛЬНУЮ структуру из API
    query_data = {
        'query': 'test query',
        'result': {
            'summary': 'test answer',
            'raw_response': 'full text'
        }
    }

    # Тестируем extraction
    result = query_data.get('result', {})
    answer = result.get('summary', 'N/A')

    assert answer == 'test answer'
```

---

## 🧪 Пример из Iteration 62

### Реальный код ДО фикса

**File:** `shared/telegram_utils/file_generators.py:460-467`

```python
for i, query_data in enumerate(queries, 1):
    query_text = query_data.get('query', 'N/A')
    answer = query_data.get('answer', 'N/A')  # ← WRONG!
    sources = query_data.get('sources', [])

    lines.append(f"=== ЗАПРОС {i} ===")
    lines.append(f"Вопрос: {query_text}")
    lines.append(f"Ответ:\n{answer}")  # Всегда N/A!
```

### Реальный код ПОСЛЕ фикса

```python
for i, query_data in enumerate(queries, 1):
    query_text = query_data.get('query', 'N/A')

    # ITERATION 62 FIX: Extract answer from nested 'result.summary'
    result = query_data.get('result', {})
    answer = result.get('summary', 'N/A')

    sources = query_data.get('sources', [])

    lines.append(f"=== ЗАПРОС {i} ===")
    lines.append(f"Вопрос: {query_text}")
    lines.append(f"Ответ:\n{answer}")  # Теперь реальный ответ!
```

### Результат

**BEFORE:**
```
Ответ:
N/A
```

**AFTER:**
```
Ответ:
РЕЗЮМЕ: По данным Росстата за 2022-2024 годы, в России наблюдается...
[200-300 слов реального текста]
ИСТОЧНИКИ: rosstat.gov.ru, mintrud.gov.ru
```

---

## 💡 Lessons Learned

### Что пошло не так:

1. **Предположили структуру данных** вместо проверки реальной
2. **Не добавили integration test** между researcher_agent и file_generators
3. **Не документировали** expected data structure в docstrings

### Что сделать в будущем:

1. ✅ **Всегда проверять реальную структуру** возвращаемых данных из API/agent
2. ✅ **Документировать структуру** в docstrings функций
3. ✅ **Писать integration tests** для data flow между модулями
4. ✅ **Использовать type hints** для предотвращения mismatches
5. ✅ **Добавлять комментарии** при извлечении из вложенных структур

### Улучшения для кодовой базы:

```python
# Добавить type hint для research results
from typing import TypedDict

class ResearchResult(TypedDict):
    query: str
    result: dict[str, str]  # {'summary': str, 'raw_response': str}

def _websearch_simple(self, query: str) -> ResearchResult:
    """Returns structured research result"""
    return {
        'query': query,
        'result': {
            'summary': answer,
            'raw_response': full_text
        }
    }
```

---

## 🔗 Related Knowhow

- `knowhow/DEPLOYMENT_SSH_PRACTICES.md` - SSH deployment workflow
- `knowhow/TESTING_BEST_PRACTICES.md` - Integration testing patterns
- `iterations/Iteration_62_Fix_Research_Results_Parsing/` - Полный example

---

**Автор:** Claude Code
**Дата:** 2025-10-29
**Iteration:** 62
**Impact:** Critical bug fix (blocked research data flow)
**Status:** ✅ Production-tested

---

# Production Database Schema & Credentials

**Дата:** 2025-10-29
**Источник:** Iteration 64 - Full E2E Pipeline
**Статус:** ✅ Tested in production

---

## 🐛 Проблема: Неправильные credentials и table names

### Симптом 1: Authentication Failed

```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1),
port 5434 failed: FATAL: password authentication failed for user "postgres"
```

### Симптом 2: Table Does Not Exist

```
psycopg2.errors.UndefinedTable: relation "audits" does not exist
LINE 2: INSERT INTO audits (session_id, audit_data...)
```

---

## ✅ Решение

### Production Database Credentials

```bash
# ❌ WRONG (Local dev)
PGUSER=postgres
PGPASSWORD=root
PGPORT=5432

# ✅ CORRECT (Production - 5.35.88.251)
export PGHOST=localhost
export PGPORT=5434
export PGDATABASE=grantservice
export PGUSER=grantservice
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'
```

### Production Table Names

| Dev/Test Name | Production Name | Status |
|---------------|-----------------|--------|
| `audits` | `auditor_results` | ✅ EXISTS |
| `researcher_research` | `researcher_research` | ✅ EXISTS |
| `grants` | `grants` | ✅ EXISTS |
| `reviews` | N/A | ❌ DOES NOT EXIST |

**Key Tables:**
- `auditor_results` - Audit data from AuditorAgentClaude
- `researcher_research` - Research results from ResearcherAgent
- `grants` - Grant applications from WriterAgent
- `sessions` - Session data with JSONB answers_data
- `users` - User accounts

---

## 📋 Правильные SQL Queries

### Step 2 (Audit)

```python
# ❌ WRONG
INSERT INTO audits (session_id, audit_data, created_at)
VALUES (%s, %s, %s)

# ✅ CORRECT
INSERT INTO auditor_results (session_id, audit_data, created_at)
VALUES (%s, %s, %s)
```

### Step 5 (Review)

```python
# ❌ WRONG - Table doesn't exist
INSERT INTO reviews (session_id, review_data, created_at)

# ✅ CORRECT - Skip DB save, file-only
logger.info("⚠️ Skipping database save (reviews table not found)")
# Just generate review_*.txt file
```

---

## 🔍 How to Check Schema

```bash
# Connect to production DB
PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' psql \
  -h localhost \
  -p 5434 \
  -U grantservice \
  -d grantservice \
  -c '\dt'

# Check specific tables
PGPASSWORD='...' psql -h localhost -p 5434 -U grantservice -d grantservice \
  -c "SELECT table_name FROM information_schema.tables
      WHERE table_schema='public'
      AND table_name ~ 'audit|research|grant|review';"
```

---

## 🚨 Common Mistakes

### 1. Wrong Port (5432 instead of 5434)

```bash
# ❌ WRONG - Default PostgreSQL port
psql -h localhost -U grantservice -d grantservice
# Fails: password authentication failed

# ✅ CORRECT - Custom port 5434
psql -h localhost -p 5434 -U grantservice -d grantservice
```

### 2. Wrong User (postgres instead of grantservice)

```bash
# ❌ WRONG
PGUSER=postgres

# ✅ CORRECT
PGUSER=grantservice
```

### 3. Wrong Table Names

```python
# ❌ WRONG
self.db.execute("INSERT INTO audits ...")

# ✅ CORRECT
self.db.execute("INSERT INTO auditor_results ...")
```

---

## 📚 Related Code

**Files using DB:**
- `scripts/e2e_synthetic_workflow.py` - E2E pipeline
- `data/database/models.py` - Database connection class
- `agents/*_agent.py` - Agent implementations

**Environment Setup:**
```python
# agents/base_agent.py or scripts
import os
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5434'
os.environ['PGDATABASE'] = 'grantservice'
os.environ['PGUSER'] = 'grantservice'
os.environ['PGPASSWORD'] = 'jPsGn%Nt%q#THnUB&&cqo*1Q'

db = GrantServiceDatabase()  # Will use env vars
```

---

**Автор:** Claude Code
**Дата:** 2025-10-29
**Iteration:** 64
**Impact:** Critical - Production deployment blocker
**Status:** ✅ Documented and fixed

---

## 📊 Production Table Schemas (Complete)

### grants Table

**Full Schema** (queried via `\d grants` on production):

```sql
Column            | Type                        | Constraints
------------------+-----------------------------+----------------------------------
grant_id          | varchar(50)                 | not null, unique
anketa_id         | varchar(50)                 | not null, FK → sessions.anketa_id
research_id       | varchar(100)                | FK → researcher_research.research_id
user_id           | bigint                      | not null, FK → users.telegram_id
grant_title       | varchar(200)                |
grant_content     | text                        |
grant_sections    | jsonb                       |
metadata          | jsonb                       |
llm_provider      | varchar(50)                 | not null
model             | varchar(50)                 |
status            | varchar(30)                 | default 'draft'
created_at        | timestamp                   | default CURRENT_TIMESTAMP
updated_at        | timestamp                   | default CURRENT_TIMESTAMP

Indexes:
  "grants_pkey" PRIMARY KEY, btree (grant_id)
  "grants_anketa_id_key" UNIQUE CONSTRAINT, btree (anketa_id)
  "grants_grant_id_key" UNIQUE CONSTRAINT, btree (grant_id)

Foreign Key Constraints:
  "grants_anketa_id_fkey" FOREIGN KEY (anketa_id) → sessions(anketa_id)
  "grants_research_id_fkey" FOREIGN KEY (research_id) → researcher_research(research_id)
  "grants_user_id_fkey" FOREIGN KEY (user_id) → users(telegram_id)
```

**Correct INSERT Query:**

```python
# ITERATION 64 FIX: Use correct grants table schema
timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
grant_id = f"{anketa_id}-GR-{timestamp}"

# Extract title (first line or default)
grant_title = grant_text.split('\n')[0][:200] if grant_text else "Грантовая заявка"

with self.db.connect() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO grants (
            grant_id, anketa_id, research_id, user_id,
            grant_title, grant_content, grant_sections, metadata,
            llm_provider, model, status, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        grant_id,           # varchar(50) - Primary key
        anketa_id,          # varchar(50) - FK to sessions
        research_id,        # varchar(100) - FK to researcher_research
        telegram_id,        # bigint - FK to users
        grant_title,        # varchar(200)
        grant_text,         # text - Full grant content
        json.dumps({}),     # jsonb - Empty sections structure
        json.dumps({'generated_by': 'e2e_workflow'}),  # jsonb - Metadata
        'gigachat',         # varchar(50) - LLM provider
        'GigaChat-Max',     # varchar(50) - Model name
        'draft',            # varchar(30) - Status
        datetime.now()      # timestamp - Created at
    ))
    conn.commit()
```

### researcher_research Table

**Key Fields:**

```sql
Column            | Type                        | Constraints
------------------+-----------------------------+----------------------------------
research_id       | varchar(100)                | not null, unique (PRIMARY KEY)
session_id        | integer                     | not null, FK → sessions
anketa_id         | varchar(50)                 | FK → sessions.anketa_id
research_data     | jsonb                       | Full research results
queries           | jsonb                       | Array of queries
created_at        | timestamp                   |
```

**Correct INSERT Query:**

```python
# ITERATION 64 FIX: Make research_id unique with timestamp
timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
research_id = f"{anketa_id}-RS-{timestamp}"

with self.db.connect() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO researcher_research (
            research_id, session_id, anketa_id,
            research_data, queries, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        research_id,
        session_id,
        anketa_id,
        json.dumps(research_data),
        json.dumps(queries),
        datetime.now()
    ))
```

---

## 🔑 Pattern: Timestamp-Based Unique IDs

### Problem: Static IDs Cause Duplicates

**❌ BAD Pattern:**
```python
research_id = f"{anketa_id}-RS-001"  # Always same ID!
# → duplicate key violation when re-running workflow
```

**Why it fails:**
- E2E workflows may re-run with same anketa_id
- Testing creates duplicate entries
- No uniqueness guarantee

### Solution: Add Timestamp

**✅ GOOD Pattern:**
```python
from datetime import datetime

timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
research_id = f"{anketa_id}-RS-{timestamp}"
# Example: "ANK-20251029031145-RS-20251029031202"
```

**Benefits:**
- ✅ Guaranteed unique per second
- ✅ Human-readable timestamp
- ✅ Sortable chronologically
- ✅ Debugging-friendly

### When to Use

**Use timestamp-based IDs for:**
1. **Research IDs** - Multiple research runs per anketa
2. **Grant IDs** - Multiple grant versions
3. **Audit IDs** - Multiple audits
4. **Review IDs** - Multiple reviews

**Don't use for:**
1. **User IDs** - Already unique (telegram_id)
2. **Session IDs** - Database auto-increment
3. **Anketa IDs** - Already timestamp-based in session creation

### Full Pattern

```python
from datetime import datetime

def generate_unique_id(prefix: str, base_id: str) -> str:
    """
    Generate unique ID with timestamp

    Args:
        prefix: ID type prefix (RS, GR, AU, RV)
        base_id: Base identifier (usually anketa_id)

    Returns:
        Unique ID like: "ANK-123-RS-20251029031145"

    Example:
        >>> generate_unique_id("RS", "ANK-20251029-001")
        "ANK-20251029-001-RS-20251029031145"
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{base_id}-{prefix}-{timestamp}"

# Usage:
research_id = generate_unique_id("RS", anketa_id)
grant_id = generate_unique_id("GR", anketa_id)
audit_id = generate_unique_id("AU", anketa_id)
review_id = generate_unique_id("RV", anketa_id)
```

---

**Автор:** Claude Code
**Дата:** 2025-10-29
**Iteration:** 64
**Impact:** Critical - Resolved duplicate key violations and schema mismatches
**Status:** ✅ Production-tested and documented
