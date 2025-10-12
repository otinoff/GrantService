# GrantService - Руководство по тестированию

## 📋 Обзор

В проекте используются **pytest** для автоматического тестирования. Тесты помогают:
- ✅ Находить ошибки **до** деплоя на продакшн
- ✅ Предотвращать **регрессии** (возврат старых ошибок)
- ✅ Проверять совместимость **SQLite → PostgreSQL**

## 🗂 Структура тестов

```
tests/
├── unit/                    # Unit-тесты (изолированные компоненты)
│   ├── test_database_models.py
│   ├── test_users.py
│   ├── test_sessions.py
│   └── test_interview.py
│
├── integration/             # Интеграционные тесты (полный стек)
│   ├── test_postgres_helper.py          # NEW! Проверка типов данных
│   ├── test_streamlit_agents_page.py    # NEW! Проверка страницы Агенты
│   ├── test_full_application_flow.py    # Полный флоу заявки
│   ├── test_streamlit_users_page.py     # Страница Пользователи
│   ├── test_streamlit_grants_ui.py      # Страница Гранты
│   └── test_postgresql_migration.py     # Миграция данных
│
└── fixtures/                # Тестовые данные и фикстуры
    ├── database.py
    └── test_data.py
```

## 🚀 Как запускать тесты

### Все тесты
```bash
pytest tests/ -v
```

### Только интеграционные
```bash
pytest tests/integration/ -v
```

### Только unit-тесты
```bash
pytest tests/unit/ -v
```

### Конкретный файл
```bash
pytest tests/integration/test_postgres_helper.py -v
```

### Конкретный тест
```bash
pytest tests/integration/test_postgres_helper.py::TestPostgresHelperReturnTypes::test_execute_query_returns_list_of_dicts -v
```

### С покрытием кода
```bash
pytest tests/ --cov=data --cov=web-admin --cov-report=html
```

## 🆕 Новые тесты (после миграции PostgreSQL)

### 1. `test_end_to_end_grant_flow.py` ⭐ НОВЫЙ!

**Назначение**: Комплексное E2E тестирование **полного цикла** создания грантовой заявки

**Что тестируется**:
- ✅ **Structured Interview** (24 hardcoded вопроса) → Auditor → Planner → Writer → БД
- ✅ **Claude Code Interview** (AI-powered адаптивное интервью) → Auditor → Planner → Writer → БД
- ✅ Сохранение всех данных в PostgreSQL (sessions, user_answers, auditor_results, planner_structures, grants)
- ✅ Корректное чтение и экспорт готовой заявки
- ✅ Производительность полного цикла (< 30 секунд)

**Тестовые данные**:
- Тема заявки: "Развитие молодежного технологического центра в Кемерово"
- 24 вопроса с готовыми ответами (project_name, project_goal, budget, etc.)
- Mock Claude Code API для предсказуемых результатов
- Mock GigaChat API для тестирования без реальных вызовов

**Какие ошибки ловит**:
```python
# ❌ Неполные данные в БД:
AssertionError: Должно быть 10 ответов, получено 5

# ❌ Некорректный статус сессии:
AssertionError: completion_status должен быть 'completed', получено 'in_progress'

# ❌ Отсутствие финальной заявки:
AssertionError: Grant не найден в БД после завершения цикла
```

**Запуск**:
```bash
# Все E2E тесты
pytest tests/integration/test_end_to_end_grant_flow.py -v

# Только Structured interview
pytest tests/integration/test_end_to_end_grant_flow.py::TestEndToEndGrantFlow::test_structured_interview_to_final_grant -v

# Только Claude Code interview
pytest tests/integration/test_end_to_end_grant_flow.py::TestEndToEndGrantFlow::test_claude_code_interview_to_final_grant -v

# С подробным выводом
pytest tests/integration/test_end_to_end_grant_flow.py -v -s
```

### 2. `test_postgres_helper.py`

**Назначение**: Проверяет что `execute_query()` возвращает **dict**, а не **tuple**

**Что тестируется**:
- ✅ `execute_query()` возвращает `List[Dict]`, не `List[tuple]`
- ✅ Результаты имеют метод `.get()` (dict-like объекты)
- ✅ Можно использовать `stats.get('total', 0)` без ошибок
- ✅ SQL с `NOW() - INTERVAL '30 days'` работает (PostgreSQL синтаксис)
- ✅ Boolean сравнения (`= TRUE` вместо `= 1`)

**Какие ошибки ловит**:
```python
# ❌ БЕЗ ТЕСТА - ошибка в продакшене:
AttributeError: 'tuple' object has no attribute 'get'

# ✅ С ТЕСТОМ - ошибка найдена ДО деплоя
FAILED test_execute_query_returns_list_of_dicts
```

**Запуск**:
```bash
pytest tests/integration/test_postgres_helper.py -v
```

### 2. `test_streamlit_agents_page.py`

**Назначение**: Проверяет работу страницы **Агенты** (🤖_Агенты.py)

**Что тестируется**:
- ✅ Статистика для всех агентов (interviewer, auditor, planner, writer)
- ✅ SQL-запросы возвращают корректные типы
- ✅ Паттерн `st.metric("Label", stats.get('value', 0))` работает
- ✅ PostgreSQL синтаксис `NOW() - INTERVAL` работает
- ✅ Boolean сравнения `= TRUE` работают

**Какие ошибки ловит**:
```python
# ❌ SQLite синтаксис в PostgreSQL:
function datetime(unknown, unknown) does not exist

# ❌ Tuple вместо dict:
AttributeError: 'tuple' object has no attribute 'get'

# ❌ Неверные boolean сравнения:
operator does not exist: boolean = integer
```

**Запуск**:
```bash
pytest tests/integration/test_streamlit_agents_page.py -v
```

## 📊 Пример вывода тестов

```bash
$ pytest tests/integration/test_postgres_helper.py -v

tests/integration/test_postgres_helper.py::TestPostgresHelperReturnTypes::test_execute_query_returns_list_of_dicts PASSED
tests/integration/test_postgres_helper.py::TestPostgresHelperReturnTypes::test_execute_query_with_real_database PASSED
tests/integration/test_postgres_helper.py::TestAgentsPageQueries::test_interviewer_stats_query PASSED
tests/integration/test_postgres_helper.py::TestSQLiteTupleVsPostgreSQLDict::test_no_tuple_in_results PASSED

======================= 12 passed, 2 warnings in 2.51s =======================
```

## 🔍 Примеры тестов

### Проверка типа возвращаемого значения

```python
def test_execute_query_returns_list_of_dicts(self):
    """КРИТИЧНО: execute_query должен возвращать список словарей"""
    result = execute_query("SELECT 1 as test_value")

    first_row = result[0]

    # ❌ НЕ должно быть tuple!
    assert not isinstance(first_row, tuple)

    # ✅ Должен иметь метод .get()
    assert hasattr(first_row, 'get')

    # ✅ Должен работать как dict
    assert first_row.get('test_value') == 1
```

### Проверка SQL-запроса из реального кода

```python
def test_interviewer_stats_query(self):
    """Тест запроса статистики интервьюера"""
    result = execute_query("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed
        FROM sessions
        WHERE started_at >= NOW() - INTERVAL '30 days'
    """)

    stats = result[0]

    # Этот код падал с AttributeError до исправления
    total = stats.get('total', 0)
    completed = stats.get('completed', 0)

    assert total >= 0
    assert completed <= total
```

### Регрессионный тест (предотвращение старых ошибок)

```python
def test_no_sqlite_datetime_syntax(self):
    """Проверка что не используется SQLite синтаксис"""
    with pytest.raises(Exception) as exc_info:
        execute_query("""
            SELECT COUNT(*) as total
            FROM sessions
            WHERE started_at >= datetime('now', '-30 days')
        """)

    # Должна быть ошибка о несуществующей функции
    error_msg = str(exc_info.value).lower()
    assert 'datetime' in error_msg
```

## 🎯 Когда запускать тесты

### Локально (перед коммитом)
```bash
# Быстрая проверка (только критичные тесты)
pytest tests/integration/test_postgres_helper.py tests/integration/test_streamlit_agents_page.py -v

# E2E тесты (перед важными изменениями)
pytest tests/integration/test_end_to_end_grant_flow.py -v

# Полная проверка (все тесты)
pytest tests/integration/ -v
```

### Перед реализацией новых фич
```bash
# 1. Сначала запускаем E2E тесты - они показывают что ДОЛЖНО работать
pytest tests/integration/test_end_to_end_grant_flow.py -v

# 2. Реализуем фичу (например, Claude Code interviewer)

# 3. Запускаем E2E снова - проверяем что всё работает
pytest tests/integration/test_end_to_end_grant_flow.py::TestEndToEndGrantFlow::test_claude_code_interview_to_final_grant -v
```

### В CI/CD (GitHub Actions)
Тесты запускаются автоматически:
- ✅ При push в GitHub
- ✅ Перед деплоем на продакшн
- ✅ При создании Pull Request

## 🐛 История найденных ошибок

### Ошибка #1: Tuple вместо Dict (2025-10-04)

**Ошибка**:
```python
AttributeError: 'tuple' object has no attribute 'get'
```

**Место**: `web-admin/pages/🤖_Агенты.py:316`
```python
st.metric("Всего интервью", stats.get('total', 0))
```

**Причина**: `execute_query()` возвращал `tuple` вместо `dict`

**Решение**: Использовать `RealDictCursor` в `postgres_helper.py`

**Тест, который теперь ловит эту ошибку**:
```bash
pytest tests/integration/test_postgres_helper.py::TestPostgresHelperReturnTypes::test_execute_query_returns_list_of_dicts
```

### Ошибка #2: SQLite синтаксис в PostgreSQL (2025-10-04)

**Ошибка**:
```
function datetime(unknown, unknown) does not exist
```

**Место**: SQL-запросы в страницах админки

**Причина**: Использовался SQLite синтаксис `datetime('now', '-30 days')`

**Решение**: Заменить на PostgreSQL `NOW() - INTERVAL '30 days'`

**Тест, который теперь ловит эту ошибку**:
```bash
pytest tests/integration/test_streamlit_agents_page.py::TestAgentsPageRegressionTests::test_no_sqlite_datetime_syntax
```

## 📈 Статистика тестов

| Категория | Количество | Описание |
|-----------|-----------|----------|
| Unit-тесты | 15+ | Изолированные компоненты |
| Integration-тесты | 30+ | Полный стек с БД |
| **E2E тесты (NEW)** | **5** | **Полный цикл заявки (structured + AI-powered)** |
| **Новые (PostgreSQL)** | **19** | **Типы данных, SQL синтаксис** |
| **Всего** | **50+** | **Покрытие основной функциональности** |

## 🔧 Troubleshooting

### Ошибка: "ModuleNotFoundError"
```bash
# Запускать из корня проекта:
cd C:\SnowWhiteAI\GrantService
pytest tests/integration/test_postgres_helper.py -v
```

### Ошибка: "Database connection failed"
```bash
# Проверить что PostgreSQL запущен:
pg_lsclusters

# Проверить переменные окружения:
echo $PGPORT
echo $PGDATABASE
```

### Тесты медленно работают
```bash
# Запускать только быстрые тесты:
pytest tests/unit/ -v

# Или с ограничением по времени:
pytest tests/integration/ -v --timeout=5
```

## 📚 Дополнительные ресурсы

- [Pytest документация](https://docs.pytest.org/)
- [PostgreSQL Testing Best Practices](https://www.postgresql.org/docs/current/regress.html)
- [Streamlit Testing Guide](https://docs.streamlit.io/library/advanced-features/testing)

## ✅ Checklist перед коммитом

- [ ] Запущены unit-тесты: `pytest tests/unit/ -v`
- [ ] Запущены integration-тесты: `pytest tests/integration/ -v`
- [ ] Все тесты прошли (0 failed)
- [ ] Нет warnings о deprecated функциях
- [ ] Покрытие кода не уменьшилось

---

**Автор**: Database Manager & Test Engineer Agents
**Дата**: 2025-10-05
**Версия**: 1.0.0
