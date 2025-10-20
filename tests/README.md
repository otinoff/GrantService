# Тесты GrantService

Комплексное тестирование системы GrantService после миграции на PostgreSQL 18.

## Структура

```
tests/
├── conftest.py                 # Конфигурация pytest и фикстуры
├── pytest.ini                  # Настройки pytest (в корне проекта)
├── fixtures/
│   ├── database.py            # Фикстуры БД (не используется, фикстуры в conftest.py)
│   └── test_data.py           # Тестовые данные
├── unit/                      # Unit тесты (48 тестов)
│   ├── test_database_models.py   # Тесты models.py
│   ├── test_interview.py         # Тесты interview.py
│   ├── test_users.py             # Тесты users.py
│   └── test_sessions.py          # Тесты sessions.py
├── integration/               # Интеграционные тесты (29 тестов)
│   ├── test_bot_interview_flow.py      # Полный флоу заполнения анкеты
│   ├── test_anketa_save.py             # Тесты сохранения анкеты
│   └── test_postgresql_migration.py    # Тесты миграции
└── TEST_REPORT.md            # Отчет о тестировании
```

## Быстрый старт

### Запуск всех тестов
```bash
pytest tests/
```

### Запуск только unit тестов
```bash
pytest tests/unit/ -v
```

### Запуск только интеграционных тестов
```bash
pytest tests/integration/ -v
```

### Запуск с code coverage
```bash
pytest tests/ --cov=data/database --cov-report=html
```

### Запуск конкретного файла
```bash
pytest tests/unit/test_users.py -v
```

### Запуск конкретного теста
```bash
pytest tests/unit/test_users.py::TestUserManager::test_register_user -v
```

## Маркеры

Тесты помечены маркерами для удобной фильтрации:

```bash
# Только unit тесты
pytest -m unit

# Только интеграционные
pytest -m integration

# Только медленные тесты
pytest -m slow
```

## Требования

### Окружение
- PostgreSQL 18.0
- Python 3.12+
- pytest 7.4+

### Переменные окружения
```bash
PGHOST=localhost
PGPORT=5432
PGDATABASE=grantservice
PGUSER=postgres
PGPASSWORD=root
```

## Фикстуры

Основные фикстуры определены в `conftest.py`:

- `db` - GrantServiceDatabase instance
- `user_manager` - UserManager instance
- `interview_manager` - InterviewManager instance
- `session_manager` - SessionManager instance
- `test_user_data` - Тестовые данные пользователя
- `cleanup_test_user` - Очистка после теста

## Тестовые данные

Тестовый пользователь:
- `telegram_id`: 999999999
- `username`: test_user_pytest
- `first_name`: Test
- `last_name`: User

## Результаты

Последний запуск (2025-10-04):
- **Всего тестов:** 78
- **Прошли:** 67 (85.9%)
- **Упали:** 10 (12.8%)
- **Пропущены:** 1 (1.3%)
- **Время:** 18.69 сек

Подробный отчет: `TEST_REPORT.md`

## Известные проблемы

1. **grant_applications** - схема отличается от ожидаемой
2. **user_answers** - нет unique constraint на (session_id, question_id)
3. **Названия колонок** - `registration_date` вместо `created_at`

## Разработка

### Добавление нового теста

```python
import pytest

@pytest.mark.unit
def test_my_function(db):
    """Описание теста"""
    # Arrange
    user_id = db.create_user(123456, "testuser")

    # Act
    result = db.get_user_by_telegram_id(123456)

    # Assert
    assert result is not None
    assert result['username'] == "testuser"
```

### Добавление фикстуры

Добавьте в `conftest.py`:

```python
@pytest.fixture(scope='function')
def my_fixture(db):
    """Описание фикстуры"""
    # Setup
    data = create_test_data()
    yield data
    # Teardown
    cleanup_test_data(data)
```

## CI/CD

Тесты автоматически запускаются при:
- Push в любую ветку
- Pull request
- Перед деплоем

## Контакты

- Разработчик: Nikolay Stepanov
- Email: otinoff@gmail.com
