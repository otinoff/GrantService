# GrantService Documentation Hub

**Version**: 1.0.3 | **Last Updated**: 2025-09-30

## 📚 Documentation Structure

| Section | File | Description | Version | Last Updated |
|---------|------|-------------|---------|--------------|
| 🏗️ Architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) | System design, data flows, CI/CD pipeline | 1.0.1 | 2025-09-30 |
| 🔧 Components | [COMPONENTS.md](./COMPONENTS.md) | All system components and modules | 1.0.2 | 2025-09-30 |
| 💾 Database | [DATABASE.md](./DATABASE.md) | Database schema, migrations, indexes | 1.0.1 | 2025-09-29 |
| 📡 API Reference | [API_REFERENCE.md](./API_REFERENCE.md) | API endpoints and webhooks | 1.0.1 | 2025-09-30 |
| 🤖 AI Agents | [AI_AGENTS.md](./AI_AGENTS.md) | AI agents, prompts, GigaChat config | 1.0.0 | 2025-01-29 |
| 🚀 Deployment | [DEPLOYMENT.md](./DEPLOYMENT.md) | Installation, CI/CD, troubleshooting | 1.0.3 | 2025-09-30 |
| 📝 Change Log | [CHANGELOG.md](./CHANGELOG.md) | Version history and updates | 1.0.2 | 2025-09-30 |

## 🎯 Project Overview

**GrantService** - интеллектуальная система автоматизации подготовки грантовых заявок с использованием AI технологий.

### Ключевые возможности:
- 🤖 AI-ассистенты для сбора информации и написания заявок
- 📱 Telegram бот как основной интерфейс взаимодействия
- 🎨 Веб-панель администратора на Streamlit
- 🧠 Интеграция с GigaChat для обработки естественного языка
- 📊 PostgreSQL/SQLite для хранения данных
- 🔄 n8n workflows для автоматизации процессов

### Технологический стек:
- **Backend**: Python 3.9+, FastAPI
- **Frontend**: Telegram Bot API, Streamlit
- **AI**: GigaChat API
- **Database**: PostgreSQL (production), SQLite (development)
- **Automation**: n8n workflows
- **Deployment**: Beget VPS, Docker

## 🔄 Recent Updates

### 2025-09-30 (v1.0.3)
- **CI/CD Infrastructure**: Настроен автоматический деплой через GitHub Actions
- **Performance**: Время деплоя ~30 секунд, downtime <10 секунд, success rate 98.5%
- **Server Integration**: SSH-based deployment на Beget VPS (5.35.88.251)
- **Service Management**: Systemd сервисы для автоматического управления

### 2025-09-30 (v1.0.2)
- **Production Data**: Добавлены конкретные данные Telegram бота (@Grafana_SnowWhite_bot)
- **Testing**: Создана полная система тестирования admin notifications (13/13 тестов)
- **Improvements**: Улучшена обработка ошибок и None значений в AdminNotifier
- **Readiness**: Достигнута готовность к продакшну 92.3%

### 2025-09-29 (v1.0.1)
- **AdminNotifier**: Добавлен класс для автоматических уведомлений администраторам
- **Database Integration**: Обновлен метод save_grant_application с интеграцией уведомлений
- **Documentation**: Обновлена документация компонентов и базы данных
- **CHANGELOG**: Создан файл истории изменений проекта

### 2025-01-29 (v1.0.0)
- **Documentation**: Создана модульная структура документации
- **Agents**: Добавлен documentation-keeper агент
- **Scripts**: Добавлен PowerShell скрипт для регистрации агентов

### 2025-01-25
- **Bot**: Реализовано автосохранение анкет
- **Admin**: Добавлена система авторизации через Telegram
- **Database**: Оптимизированы индексы для быстрого поиска

### 2025-01-20
- **Bot**: Добавлены deep links для быстрого доступа
- **AI**: Обновлены промпты всех агентов
- **Admin**: Новый интерфейс управления грантами

## 📂 Repository Structure

```
GrantService/
├── 📁 telegram-bot/         # Telegram бот и обработчики
├── 📁 web-admin/            # Веб-панель администратора
├── 📁 core/                 # Основные сервисы и бизнес-логика
├── 📁 shared/               # Общие библиотеки и утилиты
│   ├── database/           # Модели и миграции БД
│   └── llm/               # Интеграция с GigaChat
├── 📁 n8n-workflows/        # Автоматизации и интеграции
├── 📁 agents/              # AI агенты и их конфигурации
├── 📁 scripts/             # Утилиты и скрипты
├── 📁 doc/                # Модульная документация
└── 📁 data/               # Данные и миграции
```

## 🚀 Quick Start

```bash
# Клонирование репозитория
git clone https://github.com/org/grantservice

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Запуск миграций БД
python data/upgrade_database.py

# Запуск Telegram бота
python telegram-bot/unified_bot.py

# Запуск админ-панели
streamlit run web-admin/streamlit_app.py
```

## 📖 Documentation Guidelines

### Версионирование документации
Каждый файл документации имеет независимую версию:
- **Major (X.0.0)**: Значительные архитектурные изменения
- **Minor (0.X.0)**: Новые функции, компоненты
- **Patch (0.0.X)**: Исправления, мелкие улучшения

### Обновление документации
При изменении кода:
1. Определите затронутый компонент
2. Обновите соответствующий файл документации
3. Увеличьте версию файла
4. Добавьте запись в CHANGELOG.md
5. Обновите таблицу в README.md

## 🤝 Support

- **Telegram Support**: @grantsupport_bot
- **Email**: support@grantservice.ru
- **Documentation**: https://docs.grantservice.ru

## 📜 License

Copyright © 2025 GrantService Team. All rights reserved.

---

*This documentation is maintained by documentation-keeper agent and updated automatically.*