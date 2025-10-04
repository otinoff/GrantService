# Миграция GrantService на PostgreSQL 18

**Дата**: 2025-10-04
**Статус**: ✅ УСПЕШНО ЗАВЕРШЕНА

## 📊 Результаты миграции

### База данных
- **Source**: SQLite (`data/grantservice.db`)
- **Target**: PostgreSQL 18 (`localhost:5432/grantservice`)
- **Мигрировано строк**: 123/123 (100%)
- **Таблиц**: 18

### Детали миграции
```
[OK] users                          SQLite:    4 | PostgreSQL:    4
[OK] sessions                       SQLite:   16 | PostgreSQL:   16
[OK] interview_questions            SQLite:   25 | PostgreSQL:   25
[OK] grant_applications             SQLite:   19 | PostgreSQL:   19
[OK] agent_prompts                  SQLite:   14 | PostgreSQL:   14
[OK] auth_logs                      SQLite:    4 | PostgreSQL:    4
[OK] db_timestamps                  SQLite:    1 | PostgreSQL:    1
[OK] db_version                     SQLite:    1 | PostgreSQL:    1
[OK] page_permissions               SQLite:   10 | PostgreSQL:   10
[OK] prompt_categories              SQLite:   14 | PostgreSQL:   14
[OK] prompt_versions                SQLite:    1 | PostgreSQL:    1
[OK] researcher_logs                SQLite:    7 | PostgreSQL:    7
[OK] researcher_research            SQLite:    2 | PostgreSQL:    2
[OK] sent_documents                 SQLite:    5 | PostgreSQL:    5
```

## 🔧 Выполненные изменения

### 1. База данных

#### Исправления схемы
- `sessions.anketa_id`: VARCHAR(20) → VARCHAR(50)
- `researcher_research.research_id`: VARCHAR(50) → VARCHAR(100)
- `researcher_research.anketa_id`: VARCHAR(20) → VARCHAR(50)
- `grants.anketa_id`: VARCHAR(20) → VARCHAR(50)
- `grants.research_id`: VARCHAR(50) → VARCHAR(100)

#### Миграция данных
- Выполнена полная миграция всех таблиц
- Исправлен маппинг `auth_logs.user_id` (telegram_id → users.id)
- Сброшены последовательности (SERIAL)

### 2. Код приложения

#### `data/database/models.py`
**До**:
```python
import sqlite3

class GrantServiceDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)
```

**После**:
```python
import psycopg2

class GrantServiceDatabase:
    def __init__(self, connection_params: Optional[Dict] = None):
        # Читаем из переменных окружения
        self.connection_params = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': int(os.getenv('PGPORT', '5432')),
            'database': os.getenv('PGDATABASE', 'grantservice'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', 'root')
        }

    def connect(self):
        return psycopg2.connect(**self.connection_params)
```

#### `data/database/__init__.py`
**До**:
```python
if os.name == 'nt':  # Windows
    db_path = "C:/SnowWhiteAI/GrantService/data/grantservice.db"
else:
    db_path = "/var/GrantService/data/grantservice.db"

db = GrantServiceDatabase(db_path)
```

**После**:
```python
# Глобальный экземпляр БД для PostgreSQL
# Параметры подключения берутся из переменных окружения
db = GrantServiceDatabase()
```

#### `config/.env`
Добавлены переменные окружения:
```bash
# PostgreSQL Configuration
PGHOST=localhost
PGPORT=5432
PGDATABASE=grantservice
PGUSER=postgres
PGPASSWORD=root

# Database URL
DATABASE_URL=postgresql://postgres:root@localhost:5432/grantservice
```

### 3. Утилиты и скрипты

#### Созданные инструменты миграции
```
database/
├── test_pg18_connection.py          # Тест подключения к PostgreSQL 18
├── check_schema.py                   # Проверка схемы БД
├── check_sqlite.py                   # Проверка данных в SQLite
├── recreate_and_migrate.py           # Полная миграция с пересозданием БД
├── final_verification.py             # Проверка результатов
├── fix_varchar_limits.py             # Исправление VARCHAR лимитов
├── fix_auth_logs_migration.py        # Исправление auth_logs
├── psql_connect.bat/sh               # Быстрое подключение к PostgreSQL
└── migrations/
    ├── run_migration.bat/sh          # Запуск миграции
    ├── migrate_sqlite_to_postgresql.py
    └── 001_initial_postgresql_schema.sql (исправлена)
```

#### Тесты
```
test_postgresql_connection.py        # Тест подключения через обновленные модели
```

## ✅ Проверки

### Подключение к PostgreSQL
```bash
python test_postgresql_connection.py
```
**Результат**: ✅ Успешно
- Подключение установлено
- Все таблицы доступны
- Данные мигрированы полностью

### Данные
```
Users: 4
Sessions: 16
Interview Questions: 25
Grant Applications: 19
```

## 🚀 Запуск приложения

### Telegram Bot
```bash
cd telegram-bot
python main.py
```
**Статус**: Готов к тестированию

### Streamlit Admin
```bash
cd web-admin
streamlit run app.py
```
**Статус**: Готов к тестированию

### Прямое подключение к PostgreSQL
```bash
# Windows
cd database
psql_connect.bat

# Linux/Mac
cd database
./psql_connect.sh
```

## 📝 Следующие шаги

### Тестирование
1. ✅ Подключение к PostgreSQL - работает
2. ⏳ Telegram бот - требуется тест
3. ⏳ Streamlit админка - требуется тест
4. ⏳ Создание новой заявки через бота
5. ⏳ Отображение данных в админке

### Оптимизация (опционально)
1. Настройка connection pooling
2. Добавление индексов для часто используемых запросов
3. Настройка кеширования (Redis)
4. Партиционирование больших таблиц

### Бекапы
Настроить автоматические бекапы:
```bash
# Ежедневный бекап
0 2 * * * pg_dump -h localhost -U postgres -d grantservice | gzip > /backups/grantservice_$(date +\%Y\%m\%d).sql.gz
```

## 🔐 Безопасность

### Текущие настройки
- **Host**: localhost
- **Port**: 5432
- **User**: postgres
- **Password**: root ⚠️ ИЗМЕНИТЬ В ПРОДАКШЕНЕ!

### Рекомендации
1. Создать отдельного пользователя БД для приложения
2. Использовать сильный пароль
3. Настроить SSL-соединение
4. Ограничить доступ по IP в `pg_hba.conf`

## 📊 Сравнение производительности

### SQLite vs PostgreSQL

| Параметр | SQLite | PostgreSQL 18 |
|----------|--------|---------------|
| Подключение | Файл | Сетевое |
| Конкурентность | Ограниченная | Высокая |
| Размер БД | Неограничен | Неограничен |
| ACID | Да | Да |
| JSON поддержка | JSON | JSONB (быстрее) |
| Полнотекстовый поиск | Базовый | Продвинутый |
| Репликация | Нет | Да |

### Преимущества PostgreSQL 18 для GrantService
1. ✅ Конкурентный доступ (бот + админка + API)
2. ✅ JSONB для быстрой работы с динамическими данными
3. ✅ Полнотекстовый поиск по грантовым заявкам
4. ✅ Продвинутые индексы (GIN, GiST)
5. ✅ Репликация и отказоустойчивость
6. ✅ Партиционирование для больших объемов данных

## 🎯 Заключение

Миграция на PostgreSQL 18 завершена успешно!

**Время миграции**: ~10 минут
**Даунтайм**: 0 (база была в разработке)
**Потери данных**: 0

Все 123 строки данных мигрированы корректно. Система готова к тестированию с PostgreSQL.

---

**Автор**: Database Manager Agent + Grant Architect
**Дата**: 2025-10-04
