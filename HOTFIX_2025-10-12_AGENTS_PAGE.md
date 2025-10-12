# 🔧 HOTFIX: Agents Page - 2025-10-12

## 📋 Описание проблемы

На странице 🤖 Агенты обнаружены критические ошибки:

1. **ModuleNotFoundError**: Отсутствие необходимых utility-модулей на продакшене
2. **SQL Error (current_stage)**: Использование несуществующей колонки `current_stage` вместо `current_step`
3. **SQL Error (agents_passed)**: Использование колонки `agents_passed`, отсутствующей на продакшене
4. **Пустой список интервью**: Неправильный запрос к таблице `user_answers`

## 🔨 Выполненные исправления

### 1. Копирование недостающих модулей на продакшен

**Скопированные файлы:**
```bash
web-admin/utils/agent_settings.py     # 9,837 bytes
web-admin/utils/agent_processor.py    # 40,356 bytes
web-admin/utils/agent_queue.py        # 6,219 bytes
web-admin/utils/prompt_manager.py     # 21,177 bytes
web-admin/utils/prompt_editor.py      # 18,751 bytes
web-admin/utils/stage_tracker.py      # 8,560 bytes
```

### 2. Исправление SQL запросов в `🤖_Агенты.py`

#### a) Запрос для воронки (строки 2423-2431)

**Было:**
```python
SELECT
    COALESCE(s.current_stage, 'interviewer') as current_stage,
    COUNT(*) as count
FROM sessions s
WHERE s.anketa_id IS NOT NULL
  AND s.status != 'archived'
GROUP BY s.current_stage
```

**Стало:**
```python
SELECT
    COALESCE(s.current_step, 'interviewer') as current_stage,
    COUNT(*) as count
FROM sessions s
WHERE s.anketa_id IS NOT NULL
  AND s.status != 'archived'
GROUP BY s.current_step
```

#### b) Запрос для отображения сессий (строки 2446-2459)

**Было:**
```python
SELECT
    s.anketa_id,
    COALESCE(s.current_stage, 'interviewer') as current_stage,
    COALESCE(s.agents_passed, ARRAY[]::TEXT[]) as agents_passed,
    u.username,
    s.started_at,
    s.stage_updated_at
FROM sessions s
LEFT JOIN users u ON s.telegram_id = u.telegram_id
WHERE s.anketa_id IS NOT NULL
  AND s.status != 'archived'
ORDER BY COALESCE(s.stage_updated_at, s.started_at) DESC
LIMIT 10
```

**Стало:**
```python
SELECT
    s.anketa_id,
    COALESCE(s.current_step, 'interviewer') as current_stage,
    u.username,
    s.started_at,
    s.last_activity
FROM sessions s
LEFT JOIN users u ON s.telegram_id = u.telegram_id
WHERE s.anketa_id IS NOT NULL
  AND s.status != 'archived'
ORDER BY COALESCE(s.last_activity, s.started_at) DESC
LIMIT 10
```

#### c) Запрос для завершенных интервью (строки 1056-1074)

**Было:**
```python
SELECT
    s.id as session_id,
    s.telegram_id,
    u.username,
    s.anketa_id,
    s.current_step,
    s.answers_data,
    s.status,
    s.started_at as created_at,
    s.last_activity as updated_at,
    (SELECT COUNT(*) FROM user_answers ua WHERE ua.session_id = s.id) as answered_questions
FROM sessions s
LEFT JOIN users u ON s.telegram_id = u.telegram_id
WHERE s.anketa_id IS NOT NULL
    AND (
        s.answers_data IS NOT NULL
        OR EXISTS (SELECT 1 FROM user_answers ua WHERE ua.session_id = s.id)
    )
ORDER BY s.last_activity DESC
LIMIT %s
```

**Стало:**
```python
SELECT
    s.id as session_id,
    s.telegram_id,
    u.username,
    s.anketa_id,
    s.current_step,
    s.answers_data,
    s.status,
    s.started_at as created_at,
    s.last_activity as updated_at,
    s.questions_answered as answered_questions
FROM sessions s
LEFT JOIN users u ON s.telegram_id = u.telegram_id
WHERE s.anketa_id IS NOT NULL
    AND s.answers_data IS NOT NULL
ORDER BY s.last_activity DESC
LIMIT %s
```

## 📊 Схема базы данных (актуальная)

### Таблица `sessions`

**Колонки, используемые в запросах:**
- `current_step` (VARCHAR) - текущий шаг сессии
- `last_activity` (TIMESTAMP) - последняя активность
- `questions_answered` (INTEGER) - количество отвеченных вопросов
- `answers_data` (JSONB) - ответы пользователя

**Несуществующие колонки (были в коде ошибочно):**
- ❌ `current_stage` - использовалась вместо `current_step`
- ❌ `stage_updated_at` - использовалась вместо `last_activity`
- ❌ `agents_passed` - отсутствует на продакшене

## 🚀 Развертывание

```bash
# Копирование исправленной страницы
scp "web-admin/pages/🤖_Агенты.py" root@5.35.88.251:/var/GrantService/web-admin/pages/

# Перезапуск сервиса
ssh root@5.35.88.251 "systemctl restart grantservice-admin"
```

## ✅ Результат

- ✅ Страница 🤖 Агенты загружается без ошибок
- ✅ Воронка обработки заявок отображается корректно
- ✅ Список завершенных интервью работает
- ✅ Все SQL запросы используют актуальные названия колонок
- ✅ Сервис успешно перезапущен на продакшене

## 📝 Статус

**Дата:** 2025-10-12 03:27 UTC
**Сервер:** 5.35.88.251
**Сервис:** grantservice-admin (порт 8550)
**Статус:** ✅ Active (running)

---

*Хотфикс применен: 2025-10-12 03:27 UTC*
