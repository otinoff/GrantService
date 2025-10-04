# GrantService Documentation Hub
**Version**: 1.0.5 | **Last Updated**: 2025-10-03

## 📚 Documentation Structure

| Section | File | Description | Version | Last Updated |
|---------|------|-------------|---------|--------------|
| 🏗️ Architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) | System design, data flows, CI/CD pipeline | 1.0.1 | 2025-09-30 |
| 🔧 Components | [COMPONENTS.md](./COMPONENTS.md) | All system components and modules | 1.0.3 | 2025-10-01 |
| 📡 API Reference | [API_REFERENCE.md](./API_REFERENCE.md) | API endpoints and webhooks | 1.0.1 | 2025-09-30 |
| 🤖 AI Agents | [AI_AGENTS.md](./AI_AGENTS.md) | AI agents, prompts, GigaChat config, GC rules | 1.1.0 | 2025-10-03 |
| 🚀 Deployment | [DEPLOYMENT.md](./DEPLOYMENT.md) | Installation, CI/CD, troubleshooting | 1.0.4 | 2025-10-01 |
| 📝 Change Log | [CHANGELOG.md](./CHANGELOG.md) | Version history and updates | 1.0.5 | 2025-10-03 |

## 🎯 Project Overview

**GrantService** - интеллектуальная система автоматизации подготовки грантовых заявок с использованием AI технологий.

### Ключевые возможности:
- 🤖 AI-ассистенты для сбора информации и написания заявок
- 🎯 Project Orchestrator для координации всех агентов
- 📱 Telegram бот как основной интерфейс взаимодействия
- 🎨 Веб-панель администратора на Streamlit
- 🧠 Интеграция с GigaChat для обработки естественного языка
- 🗑️ Автоматическая система Garbage Collection
- 📊 PostgreSQL/SQLite для хранения данных
- 🔄 n8n workflows для автоматизации процессов

### Технологический стек:
- **Backend**: Python 3.9+, FastAPI
- **Frontend**: Telegram Bot API, Streamlit
- **AI**: GigaChat API, Claude 3 (для Project Orchestrator)
- **Database**: PostgreSQL (production), SQLite (development)
- **Automation**: n8n workflows
- **Deployment**: Beget VPS, Docker
- **Agent Management**: Claude Code Agents Architecture

## 🤖 Claude Code Agents

### Project Orchestrator
Главный координатор проекта, управляющий командой специализированных агентов:
- Анализ задач и делегирование подзадач
- Управление артефактами и Garbage Collection
- Архитектурный надзор и контроль качества
- Интеграция результатов работы всех агентов

### Development Agents
- **grant-architect** - архитектор грантовой системы
- **streamlit-admin-developer** - разработчик админ-панели
- **telegram-bot-developer** - разработчик Telegram бота
- **database-manager** - управление БД и миграциями
- **ai-integration-specialist** - интеграция с AI сервисами

### Quality & Operations
- **test-engineer** - тестирование и QA
- **deployment-manager** - деплой и DevOps
- **documentation-keeper** - документация проекта

## 📂 Repository Structure

```
GrantService/
├── 📁 .claude/              # Claude Code конфигурация
│   └── agents/              # Специализированные агенты
│       ├── project-orchestrator/
│       │   ├── project-orchestrator.md
│       │   ├── gc-rules.yaml
│       │   └── reports/
│       ├── grant-architect/
│       ├── streamlit-admin-developer/
│       ├── telegram-bot-developer/
│       ├── database-manager/
│       ├── ai-integration-specialist/
│       ├── test-engineer/
│       ├── deployment-manager/
│       └── documentation-keeper/
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
├── 📁 reports/            # Отчёты и архивы
│   └── archive/          # Архивированные важные отчёты
└── 📁 data/              # Данные и миграции
```

## 🗑️ Garbage Collection System

### Автоматическая очистка
Система GC автоматически управляет артефактами агентов:
- **Временные отчёты**: удаляются через 7 дней
- **Audit отчёты**: архивируются через 30 дней
- **Deployment логи**: архивируются через 90 дней
- **Incident reports**: хранятся 365 дней

### Правила GC
Конфигурация в `.claude/agents/project-orchestrator/gc-rules.yaml`:
- Автоматическая очистка при успешном деплое
- Еженедельная очистка временных файлов
- Ежемесячная архивация отчётов агентов
- Permanent файлы в `/doc` никогда не удаляются

## 🔄 Recent Updates

### 2025-10-03 (v1.0.5)
- **Project Orchestrator**: Создан главный координатор для управления агентами
- **GC System**: Реализована система автоматической очистки (43 → 11 файлов в doc/)
- **Agent Reorganization**: Все артефакты агентов перемещены в `.claude/agents/{agent}/reports/`
- **Documentation**: Обновлены AI_AGENTS.md с новой архитектурой, README.md, CHANGELOG.md
- **Cleanup Rules**: Добавлены gc-rules.yaml для автоматического управления артефактами

### 2025-10-01 (v1.0.4)
- **Critical Fixes**: Token protection в CI/CD, исправлен порт 8550 для Admin Panel
- **Incident Resolution**: Token security incident разрешен за 15 минут
- **Documentation**: TOKEN_INCIDENT_ANALYSIS.md, DEPLOYMENT_STRATEGY.md, BUSINESS_LOGIC.md
- **Scripts**: Добавлены quick_check.sh, check_services_status.sh, update_admin_service.sh
- **Security**: config/.env защищен при деплое
- **Performance**: Success rate 98.5% → 99.2%, recovery time <2 минуты

## 🚀 Quick Start

```bash
# Клонирование репозитория
git clone https://github.com/org/grantservice
cd grantservice

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp config/.env.example config/.env
# Отредактируйте config/.env с вашими настройками

# Запуск Telegram бота
cd telegram-bot
python main.py

# Запуск админ-панели (в новом терминале)
cd web-admin
streamlit run app.py --server.port 8550

# Работа с агентами Claude Code
claude-chat project-orchestrator  # Вызов главного координатора
```

## 📋 Environment Variables

```bash
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token
ADMIN_GROUP_ID=your_admin_group_id

# Database
DATABASE_URL=postgresql://user:pass@localhost/grantservice
# или для разработки
DATABASE_URL=sqlite:///./data/grants.db

# GigaChat API
GIGACHAT_API_KEY=your_gigachat_api_key
GIGACHAT_CLIENT_ID=your_gigachat_client_id

# Admin Panel
ADMIN_PASSWORD=your_secure_password
```

## 🔍 Testing

```bash
# Запуск всех тестов
pytest

# Тесты с покрытием
pytest --cov=core --cov=shared

# Только unit тесты
pytest tests/unit

# Только интеграционные тесты
pytest tests/integration
```

## 🚀 Deployment

Деплой осуществляется автоматически через GitHub Actions при push в main ветку:
1. Автоматические тесты
2. Сборка и проверка кода
3. Деплой на Beget VPS
4. Перезапуск сервисов
5. Health check

Ручной деплой:
```bash
./scripts/deploy.sh
```

## 📖 Documentation Files

### Core Documents
- **ARCHITECTURE.md** - Архитектура системы, компоненты, data flow
- **COMPONENTS.md** - Детальное описание всех компонентов
- **API_REFERENCE.md** - REST API и Webhook endpoints
- **DATABASE.md** - Схема БД, миграции, индексы

### Configuration & Deployment
- **DEPLOYMENT.md** - Инструкции по деплою и настройке
- **AI_AGENTS.md** - Конфигурация AI агентов и промптов

### Development
- **CHANGELOG.md** - История изменений
- **PROJECT_DOCUMENTATION.md** - Руководство разработчика

## 🤝 Contributing

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📬 Support

- **Email**: support@grantservice.ru
- **Telegram**: @Grafana_SnowWhite_bot
- **Issues**: [GitHub Issues](https://github.com/org/grantservice/issues)

## 📄 License

MIT License - подробности в файле [LICENSE](../LICENSE)

---

*This documentation hub is maintained by documentation-keeper agent*
*Last automatic GC cleanup: 2025-10-03*
