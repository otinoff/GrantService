# GrantService Documentation
**Version**: 2.0.0 | **Last Updated**: 2025-01-29 18:00

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Components](#components)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [AI Agents](#ai-agents)
- [Deployment](#deployment)
- [Change Log](#change-log)

## 🎯 Project Overview

**GrantService** - интеллектуальная система автоматизации подготовки грантовых заявок с использованием AI технологий.

### Ключевые возможности:
- 🤖 AI-ассистенты для сбора информации и написания заявок
- 📱 Telegram бот как основной интерфейс
- 🎨 Веб-панель администратора на Streamlit
- 🧠 Интеграция с GigaChat для обработки естественного языка
- 📊 PostgreSQL для хранения данных
- 🔄 n8n workflows для автоматизации процессов

### Технологический стек:
- **Backend**: Python 3.9+, FastAPI
- **Frontend**: Telegram Bot API, Streamlit
- **AI**: GigaChat API
- **Database**: PostgreSQL 14+
- **Automation**: n8n
- **Deployment**: Beget VPS, Docker

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface Layer                  │
├─────────────────┬──────────────────┬───────────────────┤
│  Telegram Bot   │  Web Admin Panel │   API Endpoints   │
└────────┬────────┴──────────┬───────┴──────────┬────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                  Business Logic Layer                    │
├─────────────────┬──────────────────┬───────────────────┤
│   AI Agents     │  n8n Workflows   │  Core Services    │
└────────┬────────┴──────────┬───────┴──────────┬────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                           │
├─────────────────┬──────────────────┬───────────────────┤
│   PostgreSQL    │  File Storage    │   Cache (Redis)   │
└─────────────────┴──────────────────┴───────────────────┘
```

## 🔧 Components

### Telegram Bot
- **Path**: `/telegram-bot/`
- **Version**: 2.0.0
- **Last Modified**: 2025-01-29
- **Main File**: `unified_bot.py`
- **Description**: Основной интерфейс взаимодействия с пользователями
- **Key Features**:
  - Многоэтапное интервью для сбора данных
  - Интеграция с AI агентами
  - Экспорт документов в Word/PDF
  - Deep links для быстрого доступа
  - Автосохранение анкет

### Web Admin Panel
- **Path**: `/web-admin/`
- **Version**: 1.5.0
- **Technology**: Streamlit
- **Main File**: `streamlit_app.py`
- **Features**:
  - Управление пользователями
  - Просмотр и редактирование заявок
  - Настройка AI промптов
  - Статистика и аналитика
  - Управление правами доступа

### Core Services
- **Path**: `/core/`
- **Version**: 1.8.0
- **Services**:
  - `anketa_manager.py` - Управление анкетами
  - `grant_manager.py` - Обработка грантов
  - `notification_service.py` - Уведомления
  - `document_generator.py` - Генерация документов

### Shared Libraries
- **Path**: `/shared/`
- **Components**:
  - `/database/` - ORM модели и миграции
  - `/llm/` - Интеграция с GigaChat
  - `/utils/` - Вспомогательные функции
  - `/config/` - Конфигурационные файлы

## 💾 Database Schema

### Основные таблицы:

#### users
```sql
- user_id: BIGINT PRIMARY KEY
- telegram_id: BIGINT UNIQUE
- username: VARCHAR(255)
- first_name: VARCHAR(255)
- last_name: VARCHAR(255)
- role: VARCHAR(50) DEFAULT 'user'
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### anketas
```sql
- id: SERIAL PRIMARY KEY
- user_id: BIGINT REFERENCES users
- status: VARCHAR(50)
- data: JSONB
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
- completed_at: TIMESTAMP
```

#### grants
```sql
- id: SERIAL PRIMARY KEY
- anketa_id: INTEGER REFERENCES anketas
- type: VARCHAR(100)
- status: VARCHAR(50)
- application_text: TEXT
- created_at: TIMESTAMP
- submitted_at: TIMESTAMP
```

#### ai_prompts
```sql
- id: SERIAL PRIMARY KEY
- agent_type: VARCHAR(50)
- prompt_text: TEXT
- version: VARCHAR(10)
- is_active: BOOLEAN DEFAULT true
- created_at: TIMESTAMP
```

## 📡 API Reference

### Authentication
```http
POST /api/auth/login
Content-Type: application/json

{
  "telegram_id": 123456789,
  "auth_date": 1234567890,
  "hash": "..."
}
```

### Anketas
```http
GET /api/anketas/{user_id}
Authorization: Bearer {token}

POST /api/anketas/create
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": 123456789,
  "data": {...}
}
```

### Grants
```http
GET /api/grants/{anketa_id}
Authorization: Bearer {token}

POST /api/grants/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "anketa_id": 123,
  "grant_type": "presidential"
}
```

## 🤖 AI Agents

### Агент-Интервьюер
- **Version**: 1.2.0
- **Model**: GigaChat-Max
- **Purpose**: Сбор информации о проекте через диалог
- **Prompt Version**: 2025-01-15

### Агент-Аудитор
- **Version**: 1.1.0
- **Model**: GigaChat-Pro
- **Purpose**: Анализ и оценка проекта по критериям
- **Prompt Version**: 2025-01-10

### Агент-Планировщик
- **Version**: 1.0.5
- **Model**: GigaChat-Pro
- **Purpose**: Структурирование заявки
- **Prompt Version**: 2025-01-08

### Агент-Писатель
- **Version**: 1.3.0
- **Model**: GigaChat-Max
- **Purpose**: Написание текстов заявки
- **Prompt Version**: 2025-01-20

## 🚀 Deployment

### Requirements:
- Python 3.9+
- PostgreSQL 14+
- Redis (optional)
- 2GB+ RAM
- 20GB+ Storage

### Environment Variables:
```bash
# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_ID=

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# GigaChat
GIGACHAT_API_KEY=
GIGACHAT_CLIENT_ID=

# Admin Panel
ADMIN_SECRET_KEY=
STREAMLIT_PORT=8501
```

### Quick Start:
```bash
# Clone repository
git clone https://github.com/org/grantservice

# Install dependencies
pip install -r requirements.txt

# Run migrations
python migrate.py

# Start services
python start_bot_unified.py
streamlit run web-admin/streamlit_app.py
```

## 📝 Change Log

### Version 2.0.0 - 2025-01-29
- **[Agents]**: Добавлены новые AI агенты (ai-integration-specialist, telegram-bot-developer, test-engineer)
- **[Documentation]**: Создан documentation-keeper агент для автоматизации документирования
- **[Scripts]**: Добавлен PowerShell скрипт для регистрации агентов

### Version 1.9.0 - 2025-01-25
- **[Bot]**: Реализовано автосохранение анкет
- **[Admin]**: Добавлена система авторизации через Telegram
- **[Database]**: Оптимизированы индексы для быстрого поиска

### Version 1.8.0 - 2025-01-20
- **[Bot]**: Добавлены deep links для быстрого доступа
- **[AI]**: Обновлены промпты всех агентов
- **[Admin]**: Новый интерфейс управления грантами

### Version 1.7.0 - 2025-01-15
- **[Core]**: Рефакторинг модуля anketa_manager
- **[Bot]**: Исправлены проблемы с таймаутами
- **[Database]**: Добавлена таблица ai_prompts

### Version 1.6.0 - 2025-01-10
- **[Integration]**: Подключение n8n workflows
- **[Bot]**: Новые команды для администраторов
- **[Docs]**: Обновлена документация API

---

## 📚 Additional Resources

- [Installation Guide](./INSTALLATION.md)
- [API Documentation](./API.md)
- [Contributing Guide](./CONTRIBUTING.md)
- [Security Policy](./SECURITY.md)

## 🤝 Support

- **Telegram**: @grantsupport_bot
- **Email**: support@grantservice.ru
- **Documentation**: https://docs.grantservice.ru

---

*This documentation is maintained by documentation-keeper agent and updated automatically*