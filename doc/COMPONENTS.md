# System Components
**Version**: 1.0.2 | **Last Modified**: 2025-09-30

## Table of Contents
- [Telegram Bot](#telegram-bot)
- [Web Admin Panel](#web-admin-panel)
- [Core Services](#core-services)
- [Shared Libraries](#shared-libraries)
- [n8n Workflows](#n8n-workflows)
- [Scripts & Utilities](#scripts--utilities)

## Telegram Bot

### Overview
- **Version**: 2.1.4
- **Path**: `/telegram-bot/`
- **Main Files**:
  - `unified_bot.py` - Унифицированный бот для всех платформ
  - `main.py` - Основной файл бота
  - `main_windows.py` - Версия для Windows
- **Dependencies**: python-telegram-bot, aiogram, asyncio
- **Configuration**: Environment variables, config files

### Architecture
```
telegram-bot/
├── handlers/           # Обработчики команд и сообщений
│   ├── start.py       # /start команда
│   ├── interview.py   # Интервью процесс
│   ├── admin.py       # Админские команды
│   └── documents.py   # Работа с документами
├── services/          # Сервисы бота
│   ├── gigachat.py    # Интеграция с GigaChat
│   ├── database.py    # Работа с БД
│   └── notifications.py # Уведомления
├── utils/             # Утилиты
│   ├── keyboards.py   # Клавиатуры
│   ├── states.py      # FSM состояния
│   ├── validators.py  # Валидация данных
│   └── admin_notifications.py # Уведомления администраторам
└── config/            # Конфигурация
    └── settings.py    # Настройки бота
```

### Key Features
1. **Команды пользователя**:
   - `/start` - Начало работы
   - `/interview` - Запуск интервью
   - `/status` - Статус заявки
   - `/help` - Помощь
   - `/export` - Экспорт документов

2. **Команды администратора**:
   - `/admin` - Админ-панель
   - `/stats` - Статистика
   - `/broadcast` - Рассылка
   - `/users` - Управление пользователями

3. **Система уведомлений** (v2.1.4):
   - Автоматические уведомления администраторам о новых заявках
   - Отправка в группу "Грантсервис" (ID: -4930683040)
   - Bot: @Grafana_SnowWhite_bot (ID: 8057176426)
   - Форматированные сообщения с данными заявки и пользователя
   - Улучшена обработка None значений в данных заявки
   - Добавлен импорт ParseMode для корректного форматирования
   - Протестировано: 13/13 тестов пройдено, готовность 92.3%

4. **FSM States**:
   ```python
   class InterviewStates(StatesGroup):
       waiting_for_name = State()
       waiting_for_description = State()
       waiting_for_goals = State()
       waiting_for_audience = State()
       waiting_for_budget = State()
       confirming_data = State()
   ```

4. **Интеграции**:
   - GigaChat API для AI обработки
   - PostgreSQL для хранения данных
   - n8n для автоматизации
   - File storage для документов

### Usage Example
```python
# Запуск бота
from telegram_bot import UnifiedBot

bot = UnifiedBot(
    token=TELEGRAM_BOT_TOKEN,
    database_url=DATABASE_URL,
    gigachat_api_key=GIGACHAT_KEY
)

bot.run()

# Использование системы уведомлений (v2.1.4)
from telegram_bot.utils.admin_notifications import AdminNotifier
from telegram.constants import ParseMode  # Добавлен в v2.1.4

notifier = AdminNotifier(bot_token=TELEGRAM_BOT_TOKEN)

# Отправка уведомления о новой заявке
try:
    message_id = await notifier.send_new_application_notification(
        application_data={
            'application_number': 'GA-20250929-A1B2C3D4',
            'title': 'Инновационный проект',
            'status': 'submitted'
        },
        user_data={
            'telegram_id': 123456789,
            'username': 'user123',
            'full_name': 'Иван Иванов'
        }
    )
    # Успешная отправка - возвращает message_id (например, 313)
    print(f"Notification sent, message ID: {message_id}")
except Exception as e:
    # Улучшенная обработка ошибок в v2.1.4
    print(f"Failed to send notification: {e}")

# Тестирование готовности системы
readiness_score = notifier.check_readiness()  # Возвращает 92.3%
```

## Web Admin Panel

### Overview
- **Version**: 1.5.0
- **Path**: `/web-admin/`
- **Technology**: Streamlit
- **Main File**: `streamlit_app.py`
- **Port**: 8501 (default)

### Structure
```
web-admin/
├── pages/             # Страницы админки
│   ├── 01_Dashboard.py
│   ├── 02_Users.py
│   ├── 03_Anketas.py
│   ├── 04_Grants.py
│   ├── 05_AI_Prompts.py
│   └── 06_Settings.py
├── utils/             # Утилиты
│   ├── auth.py        # Авторизация
│   ├── database.py    # Работа с БД
│   └── charts.py      # Графики
├── components/        # Компоненты UI
│   ├── sidebar.py
│   ├── header.py
│   └── footer.py
└── assets/           # Статические файлы
    ├── css/
    └── images/
```

### Features
1. **Dashboard**:
   - Общая статистика
   - Графики активности
   - Последние заявки
   - Системные метрики

2. **User Management**:
   - Список пользователей
   - Роли и права
   - Блокировка/разблокировка
   - История действий

3. **Anketa Management**:
   - Просмотр анкет
   - Редактирование
   - Статусы
   - Экспорт данных

4. **AI Prompts Editor**:
   - Управление промптами
   - Версионирование
   - A/B тестирование
   - Метрики эффективности

### Authentication
```python
# Telegram-based authentication
def authenticate_user(telegram_data):
    user_id = telegram_data.get('id')
    auth_date = telegram_data.get('auth_date')
    hash = telegram_data.get('hash')

    if verify_telegram_auth(user_id, auth_date, hash):
        return create_session(user_id)
    return None
```

## Core Services

### Overview
- **Version**: 1.8.0
- **Path**: `/core/`
- **Purpose**: Основная бизнес-логика

### Components

#### 1. Anketa Manager
```python
class AnketaManager:
    def create_anketa(user_id: int) -> Anketa
    def update_anketa(anketa_id: int, data: dict) -> Anketa
    def get_anketa(anketa_id: int) -> Anketa
    def list_anketas(filters: dict) -> List[Anketa]
    def export_anketa(anketa_id: int, format: str) -> bytes
```

#### 2. Grant Manager
```python
class GrantManager:
    def generate_application(anketa_id: int, grant_type: str) -> Grant
    def submit_grant(grant_id: int) -> bool
    def check_status(grant_id: int) -> str
    def get_statistics() -> dict
```

#### 3. Document Generator
```python
class DocumentGenerator:
    def generate_word(data: dict, template: str) -> bytes
    def generate_pdf(data: dict, template: str) -> bytes
    def merge_documents(docs: List[bytes]) -> bytes
    def apply_template(data: dict, template_id: str) -> str
```

#### 4. Notification Service
```python
class NotificationService:
    def send_telegram(user_id: int, message: str)
    def send_email(email: str, subject: str, body: str)
    def broadcast(user_ids: List[int], message: str)
    def schedule_notification(user_id: int, message: str, time: datetime)
```

## Shared Libraries

### Overview
- **Path**: `/shared/`
- **Purpose**: Общие библиотеки и утилиты

### Structure
```
shared/
├── database/          # База данных
│   ├── models.py      # SQLAlchemy модели
│   ├── migrations/    # Alembic миграции
│   └── connection.py  # Подключение к БД
├── llm/              # AI интеграция
│   ├── gigachat.py   # GigaChat клиент
│   ├── prompts.py    # Управление промптами
│   └── unified_llm_client.py
└── utils/            # Утилиты
    ├── validators.py  # Валидация
    ├── formatters.py  # Форматирование
    └── helpers.py     # Хелперы
```

### Database Models
```python
# User model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String(255))
    role = Column(String(50), default='user')
    created_at = Column(DateTime, default=datetime.utcnow)

# Anketa model
class Anketa(Base):
    __tablename__ = 'anketas'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    data = Column(JSON)
    status = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### LLM Integration
```python
from shared.llm import UnifiedLLMClient

client = UnifiedLLMClient(
    provider='gigachat',
    api_key=GIGACHAT_API_KEY
)

response = client.generate(
    prompt="Analyze this project",
    model="GigaChat-Pro",
    temperature=0.7
)
```

## n8n Workflows

### Overview
- **Path**: `/n8n-workflows/`
- **Purpose**: Автоматизация процессов
- **Technology**: n8n.io

### Main Workflows

#### 1. User Registration
```json
{
  "name": "User Registration",
  "nodes": [
    {
      "type": "webhook",
      "name": "Telegram Webhook",
      "webhookPath": "/register"
    },
    {
      "type": "postgres",
      "name": "Create User",
      "operation": "insert"
    },
    {
      "type": "telegram",
      "name": "Send Welcome",
      "action": "sendMessage"
    }
  ]
}
```

#### 2. Interview Process
```json
{
  "name": "Interview Process",
  "nodes": [
    {
      "type": "webhook",
      "name": "Start Interview"
    },
    {
      "type": "gigachat",
      "name": "Process Question"
    },
    {
      "type": "postgres",
      "name": "Save Answer"
    },
    {
      "type": "telegram",
      "name": "Send Next Question"
    }
  ]
}
```

#### 3. Document Generation
```json
{
  "name": "Document Generation",
  "nodes": [
    {
      "type": "postgres",
      "name": "Get Anketa Data"
    },
    {
      "type": "gigachat",
      "name": "Generate Text"
    },
    {
      "type": "document",
      "name": "Create Document"
    },
    {
      "type": "telegram",
      "name": "Send Document"
    }
  ]
}
```

## Scripts & Utilities

### Overview
- **Path**: `/scripts/`
- **Purpose**: Вспомогательные скрипты

### Key Scripts

#### 1. Database Management
```bash
# Миграции
python scripts/migrate_database.py

# Бэкап
python scripts/backup_database.py

# Восстановление
python scripts/restore_database.py
```

#### 2. Data Import/Export
```bash
# Импорт пользователей
python scripts/import_users.py users.csv

# Экспорт анкет
python scripts/export_anketas.py --format=excel

# Миграция данных
python scripts/migrate_data.py --from=sqlite --to=postgres
```

#### 3. Testing & Debug
```bash
# Тест бота
python scripts/test_bot.py

# Проверка промптов
python scripts/test_prompts.py

# Debug mode
python scripts/debug_mode.py --verbose
```

#### 4. Deployment
```bash
# Deploy to production
./scripts/deploy.sh production

# Update dependencies
./scripts/update_deps.sh

# Health check
python scripts/health_check.py
```

### PowerShell Scripts
```powershell
# Register agents
.\register-agents.ps1

# Start services
.\start-services.ps1

# Check status
.\check-status.ps1
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-29 | Initial components documentation |

---

*This document is maintained by documentation-keeper agent*