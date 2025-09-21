# План синхронизации баз данных между ботом и Streamlit

## Анализ текущей проблемы

### 1. Что происходит сейчас:
- **Telegram бот** генерирует токен в формате без подчеркиваний: `token17584331243f3b0b0370babf1754ec65521d469fbb`
- **Бот сохраняет** токен в базу данных по пути: `C:/SnowWhiteAI/GrantService/data/grantservice.db`
- **Streamlit проверяет** токен в той же базе, но не находит пользователей с токенами
- В логах видно: "Всего пользователей с токенами: 0"

### 2. Найденные файлы:
- Основной Streamlit: `GrantService/streamlit_app.py` - использует `from data.database import db`
- Тестовый Streamlit: `GrantService/test_streamlit_auth.py` - использует тестовую логику без БД
- База данных инициализируется в: `GrantService/data/database/__init__.py`

### 3. Проблемные места:
1. **Путь к БД в `__init__.py`** - уже исправлен для использования Windows пути
2. **Путь в `auth_pages.py`** (строка 12) - использует `/var/GrantService` (Linux путь)
3. **Формат токена** - уже исправлен для поддержки обоих форматов

## Необходимые исправления

### 1. Исправить путь в auth_pages.py
- Заменить `/var/GrantService` на динамический путь в зависимости от ОС

### 2. Убедиться, что бот и Streamlit используют один файл БД
- Проверить, что оба используют `C:/SnowWhiteAI/GrantService/data/grantservice.db`

### 3. Проверить сохранение токена в БД
- Убедиться, что токен действительно сохраняется при вызове `get_or_create_login_token`
- Проверить коммит транзакции

### 4. Перезапустить оба сервиса
- Остановить и запустить бота
- Остановить и запустить Streamlit

## Команды для тестирования

### 1. Перезапуск бота:
```bash
cd C:\SnowWhiteAI\GrantService\telegram-bot
restart_bot_venv.bat
```

### 2. Запуск Streamlit:
```bash
cd C:\SnowWhiteAI\GrantService
streamlit run streamlit_app.py
```

### 3. Проверка БД:
```bash
cd C:\SnowWhiteAI\GrantService
python scripts\check_databases.py
```

## Ожидаемый результат
1. Бот генерирует токен
2. Токен сохраняется в единую БД
3. Streamlit находит и валидирует токен
4. Пользователь успешно авторизуется