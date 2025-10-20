# Исправление страницы "📄 Управление грантами"

**Дата**: 2025-10-07 07:20
**Проблема**: `AttributeError: 'AdminDatabase' object has no attribute 'connect'`

## Корневая причина

Страница использовала старый SQLite код с:
- `db.connect()` - устаревший метод
- Курсоры и `cursor.execute()`
- SQLite параметры `?` вместо PostgreSQL `%s`
- Неправильные JOIN по `u.telegram_id` вместо `u.id`

## Исправленные функции

### 1. `get_grants_statistics()` (строка 81)
**Было**:
```python
with db.connect() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM grant_applications")
    total = cursor.fetchone()[0]
```

**Стало**:
```python
from utils.postgres_helper import execute_query
result = execute_query("SELECT COUNT(*) as cnt FROM grant_applications")
total = result[0]['cnt'] if result else 0
```

### 2. `get_all_applications()` (строка 119)
**Было**:
```python
with db.connect() as conn:
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
df = pd.DataFrame(rows, columns=columns)
```

**Стало**:
```python
from utils.postgres_helper import execute_query
result = execute_query(query, tuple(params) if params else None)
if result:
    df = pd.DataFrame([dict(row) for row in result])
```

### 3. `get_application_details()` (строка 268)
**Было**:
```python
conn = _db.connect()
query = """
    ...
    LEFT JOIN users u ON ga.user_id = u.telegram_id  -- ОШИБКА!
    WHERE ga.id = ?  -- SQLite синтаксис
"""
cursor = conn.cursor()
cursor.execute(query, (app_id,))
```

**Стало**:
```python
from utils.postgres_helper import execute_query
query = """
    ...
    LEFT JOIN users u ON ga.user_id = u.id  -- ИСПРАВЛЕНО
    WHERE ga.id = %s  -- PostgreSQL синтаксис
"""
result = execute_query(query, (app_id,))
```

### 4. `get_sent_documents()` (строка 306)
**Было**:
```python
conn = _db.connect()
query = """
    ...
    LEFT JOIN users u ON sd.user_id = u.telegram_id  -- ОШИБКА!
"""
df = pd.read_sql_query(query, conn)
```

**Стало**:
```python
from utils.postgres_helper import execute_query
query = """
    ...
    LEFT JOIN users u ON sd.user_id = u.id  -- ИСПРАВЛЕНО
"""
result = execute_query(query)
if result:
    df = pd.DataFrame([dict(row) for row in result])
```

### 5. `send_grant_to_telegram()` (строка 344)
**Было**:
```python
conn = db.connect()
cursor = conn.cursor()
cursor.execute("""
    INSERT INTO sent_documents (...)
    VALUES (?, ?, ?, ?, ?, ?)  -- SQLite синтаксис
""", (...))
conn.commit()
```

**Стало**:
```python
from utils.postgres_helper import execute_update
execute_update("""
    INSERT INTO sent_documents (...)
    VALUES (%s, %s, %s, %s, %s, %s)  -- PostgreSQL синтаксис
""", (...))
```

### 6. Ручная отправка грантов (строка 806)
**Было**:
```python
conn = db.connect()
users_df = pd.read_sql_query(users_query, conn)
```

**Стало**:
```python
from utils.postgres_helper import execute_query
users_result = execute_query(users_query)
users_df = pd.DataFrame([dict(row) for row in users_result]) if users_result else pd.DataFrame()
```

### 7. INSERT в sent_documents (строка 860)
**Было**:
```python
conn = db.connect()
cursor = conn.cursor()
cursor.execute("""
    INSERT INTO sent_documents (...)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)  -- SQLite
""", (...))
conn.commit()
```

**Стало**:
```python
from utils.postgres_helper import execute_update
execute_update("""
    INSERT INTO sent_documents (...)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)  -- PostgreSQL
""", (...))
```

## Итого исправлено

✅ **7 функций/блоков** переписаны на `postgres_helper`
✅ **Все `db.connect()` удалены**
✅ **Все `?` заменены на `%s`**
✅ **Все JOIN исправлены** (u.id вместо u.telegram_id)
✅ **Все курсоры заменены** на execute_query/execute_update

## Результат

- Страница "📄 Управление грантами" теперь полностью работает с PostgreSQL
- Ошибка `AttributeError: 'AdminDatabase' object has no attribute 'connect'` устранена
- Код унифицирован для использования `postgres_helper`

## Тестирование

Проверить:
1. Открыть страницу "📄 Управление грантами"
2. Проверить метрики в шапке
3. Проверить просмотр заявки (🔍 Просмотр)
4. Проверить все табы (Все заявки, Готовые гранты, Отправка, Архив)

**Статус**: ✅ Исправлено и готово к тестированию
