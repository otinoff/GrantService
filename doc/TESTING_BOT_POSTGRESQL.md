# Тестирование Telegram Бота с PostgreSQL 18

## 🚀 Запуск бота

### Windows
```bash
start_bot_postgresql.bat
```

### Ручной запуск
```bash
# Установить переменные окружения
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=grantservice
set PGUSER=postgres
set PGPASSWORD=root

# Запустить бота
cd telegram-bot
python main.py
```

## ✅ Чек-лист тестирования

### 1. Запуск и подключение к БД
- [ ] Бот запускается без ошибок
- [ ] Подключение к PostgreSQL успешно
- [ ] Логи показывают "Connected to PostgreSQL"
- [ ] Нет ошибок импорта модулей

### 2. Команда /start
**Действие**: Отправить `/start` боту в Telegram

**Ожидаемое поведение**:
- [ ] Бот отвечает приветственным сообщением
- [ ] Создается новая запись в таблице `users` (если пользователь новый)
- [ ] Создается новая сессия в таблице `sessions`
- [ ] Отображается главное меню

**SQL проверка**:
```sql
-- Проверить создание пользователя
SELECT * FROM users ORDER BY id DESC LIMIT 1;

-- Проверить создание сессии
SELECT * FROM sessions ORDER BY id DESC LIMIT 1;
```

### 3. Создание заявки / Интервью
**Действие**: Начать процесс создания заявки

**Ожидаемое поведение**:
- [ ] Бот загружает вопросы из `interview_questions`
- [ ] Отображается первый вопрос
- [ ] Ответы сохраняются в сессию
- [ ] Можно переходить к следующему вопросу

**SQL проверка**:
```sql
-- Проверить количество вопросов
SELECT COUNT(*) FROM interview_questions WHERE is_active = TRUE;

-- Проверить последнюю активную сессию
SELECT id, telegram_id, current_step, status
FROM sessions
WHERE status = 'active'
ORDER BY last_activity DESC
LIMIT 1;
```

### 4. Сохранение данных
**Действие**: Ответить на несколько вопросов

**Ожидаемое поведение**:
- [ ] Ответы сохраняются в PostgreSQL
- [ ] Поле `last_activity` обновляется
- [ ] Счетчик `total_messages` увеличивается

**SQL проверка**:
```sql
-- Проверить обновление сессии
SELECT id, total_messages, last_activity, answers_data
FROM sessions
WHERE id = <session_id>;
```

### 5. Завершение заявки
**Действие**: Завершить процесс заполнения заявки

**Ожидаемое поведение**:
- [ ] Создается запись в `grant_applications`
- [ ] Статус сессии меняется на 'completed'
- [ ] Генерируется номер заявки (GA-YYYYMMDD-XXXXXXXX)

**SQL проверка**:
```sql
-- Проверить созданную заявку
SELECT application_number, status, created_at
FROM grant_applications
ORDER BY created_at DESC
LIMIT 1;
```

### 6. Просмотр истории
**Действие**: Запросить список своих заявок

**Ожидаемое поведение**:
- [ ] Бот показывает список заявок пользователя
- [ ] Данные загружаются из PostgreSQL
- [ ] Отображаются корректные статусы

**SQL проверка**:
```sql
-- Проверить заявки пользователя
SELECT ga.application_number, ga.status, s.telegram_id
FROM grant_applications ga
JOIN sessions s ON ga.session_id = s.id
WHERE s.telegram_id = <your_telegram_id>
ORDER BY ga.created_at DESC;
```

## 🔍 Мониторинг логов

### Логи бота
Проверить наличие следующих сообщений:
```
✅ PostgreSQL connection configured: localhost:5432/grantservice
✅ Connected to PostgreSQL: PostgreSQL 18.0...
✅ Found 25 questions in database
✅ Created session X for telegram_id Y
✅ Grant application GA-XXXXXXXX saved successfully
```

### Логи PostgreSQL
```sql
-- Проверить активные подключения
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity
WHERE datname = 'grantservice';
```

## ⚠️ Возможные проблемы

### Ошибка: "Failed to connect to PostgreSQL"
**Причина**: PostgreSQL не запущен или неверные параметры

**Решение**:
```bash
# Проверить статус PostgreSQL
sc query postgresql-x64-18

# Запустить PostgreSQL
net start postgresql-x64-18

# Проверить подключение
psql -h localhost -U postgres -d grantservice
```

### Ошибка: "ModuleNotFoundError: No module named 'psycopg2'"
**Причина**: Не установлен драйвер PostgreSQL

**Решение**:
```bash
pip install psycopg2-binary
```

### Ошибка: "Missing tables"
**Причина**: Схема БД не применена

**Решение**:
```bash
cd database
python recreate_and_migrate.py
```

## 📊 Проверка производительности

### Время отклика
```sql
-- Включить логирование медленных запросов
ALTER DATABASE grantservice SET log_min_duration_statement = 100;

-- Просмотр медленных запросов
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE dbid = (SELECT oid FROM pg_database WHERE datname = 'grantservice')
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Использование памяти
```sql
-- Размер базы данных
SELECT pg_size_pretty(pg_database_size('grantservice'));

-- Размер таблиц
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## ✅ Критерии успешного теста

- ✅ Бот запускается без ошибок
- ✅ Все данные сохраняются в PostgreSQL 18
- ✅ Нет потери данных при работе с сессиями
- ✅ Время отклика < 500ms для всех операций
- ✅ Нет ошибок в логах PostgreSQL
- ✅ Корректное завершение сессий

## 📝 Отчет о тестировании

После тестирования заполните:

### Результаты
- **Дата тестирования**: _____________
- **Версия PostgreSQL**: 18.0
- **Версия бота**: _____________
- **Статус**: ⬜ PASSED / ⬜ FAILED

### Обнаруженные проблемы
1. _____________________
2. _____________________
3. _____________________

### Метрики
- Время запуска бота: ______ сек
- Время создания пользователя: ______ мс
- Время загрузки вопросов: ______ мс
- Время сохранения ответа: ______ мс
- Время создания заявки: ______ мс

---

**Документ создан**: 2025-10-04
**Автор**: Grant Architect + Test Engineer
