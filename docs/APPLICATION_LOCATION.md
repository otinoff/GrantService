# Расположение приложения GrantService

## Локальная версия

**Путь:** `C:\SnowWhiteAI\GrantService\`

**Структура:**
```
GrantService/
├── telegram-bot/           # Telegram bot implementation
├── web-admin/             # Streamlit admin interface
├── agents/                # AI agent implementations
│   ├── base_agent.py
│   ├── interactive_interviewer_agent.py
│   ├── auditor_agent.py
│   └── researcher_agent.py
├── data/                  # Database and storage
│   └── database/
├── n8n-workflows/         # n8n workflow definitions
├── scripts/               # Utility scripts
└── tests/                 # Test suite
```

---

## Production сервер

**URL Admin:** http://5.35.88.251:8501
**URL Bot:** @GrantServiceBot (Telegram)

**Сервер:** 5.35.88.251
**Путь:** `/var/GrantService`

**База данных (PostgreSQL):**
- Host: localhost (на сервере)
- Port: 5432
- Database: grantservice
- User: postgres

**Qdrant (векторная БД):**
- Host: 5.35.88.251
- Port: 6333
- Collection: knowledge_sections (31 секция ФПГ)

---

## Запуск локально

### Admin панель
```bash
cd C:\SnowWhiteAI\GrantService
python launcher.py
# или
admin.bat
```

### Telegram Bot
```bash
cd C:\SnowWhiteAI\GrantService\telegram-bot
python main.py
```

### Тесты
```bash
cd C:\SnowWhiteAI\GrantService
pytest tests/
```

---

## CI/CD

**Деплой:** Ручной через SSH
```bash
ssh root@5.35.88.251
cd /var/GrantService
git pull
systemctl restart grantservice-bot
systemctl restart grantservice-admin
```

**Мониторинг:**
```bash
# Логи бота
tail -f /var/log/grantservice-bot.log

# Логи админки
tail -f /var/log/grantservice-admin.log

# Статус сервисов
systemctl status grantservice-bot
systemctl status grantservice-admin
```

---

## Связанные документы

**В проекте:**
- [README проекта](README.md)
- [Описание архитектуры](00_Project_Info/ARCHITECTURE.md)
- [Roadmap агентов](00_Project_Info/ROADMAP.md)

**В коде:**
- [CLAUDE.md](C:\SnowWhiteAI\GrantService\CLAUDE.md) - Инструкции для Claude
- [ARCHITECTURE.md](C:\SnowWhiteAI\GrantService\ARCHITECTURE.md) - Техническая архитектура
