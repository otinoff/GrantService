# 📁 .claude/ - Claude Code Configuration & Memory

Эта директория содержит конфигурацию Claude Code и память о работе над проектом.

---

## 📂 Структура

```
.claude/
├── README.md                          # Этот файл
├── settings.local.json                # Настройки Claude Code (subagents)
├── SESSION_SUMMARY_2025-10-05.md     # Краткий summary последней сессии
├── QUICK_START_NEXT_SESSION.md       # Быстрый старт для следующей сессии
│
└── agents/                            # Custom Claude Code subagents
    ├── README.md                      # Обзор всех агентов
    │
    ├── grant-architect.md             # 🏗 Архитектор системы грантов
    ├── database-manager.md            # 💾 Эксперт по PostgreSQL
    ├── telegram-bot-developer.md      # 🤖 Разработчик Telegram бота
    ├── streamlit-admin-developer.md   # 📊 Разработчик админ-панели
    ├── ai-integration-specialist.md   # 🧠 Эксперт по AI интеграции
    ├── test-engineer.md               # 🧪 Инженер по тестированию
    ├── deployment-manager.md          # 🚀 Менеджер деплоя
    ├── documentation-keeper.md        # 📚 Хранитель документации
    ├── project-orchestrator.md        # 🎼 Оркестратор проекта
    │
    └── [agent-name]/                  # Папки агентов с документами
        ├── reports/                   # Отчеты агента
        ├── README.md                  # Документация агента
        └── ...
```

---

## 🚀 Быстрый старт для новой сессии

### Вариант 1: Продолжить с последней сессии

```
Привет! Прочитай:
.claude/SESSION_SUMMARY_2025-10-05.md

Расскажи что мы делали и что дальше.
```

### Вариант 2: Общий контекст проекта

```
Привет! Прочитай:
1. CLAUDE.md
2. .claude/SESSION_SUMMARY_2025-10-05.md

Дай overview проекта и текущих задач.
```

---

## 📄 Файлы в корне .claude/

### settings.local.json
Конфигурация кастомных subagents для Claude Code.

**Содержит**:
- Список доступных агентов
- Их роли и инструменты
- Правила использования

**Использование**:
```bash
@grant-architect помоги спроектировать новый модуль
@database-manager оптимизируй запрос
@deployment-manager задеплой на продакшн
```

### SESSION_SUMMARY_2025-10-05.md ⭐ ВАЖНО!
**Краткий summary последней сессии работы.**

**Читай этот файл первым** чтобы понять:
- Что было сделано
- Какие решения приняты
- Что делать дальше
- Какие файлы читать для деталей

**Обновляется**: В конце каждой важной сессии

### QUICK_START_NEXT_SESSION.md
**Инструкция для быстрого старта в следующей сессии.**

**Содержит**:
- Примеры запросов для продолжения работы
- Список ключевых файлов для чтения
- Быстрые команды
- Инсайты из предыдущей сессии

**Используй**: Когда забыл с чего начать

---

## 🤖 Custom Subagents

### grant-architect 🏗
**Роль**: Архитектор системы грантовых заявок
**Эксперт в**: AI agents, GigaChat, структура заявок, российские гранты
**Используй для**: Архитектурные решения, дизайн новых фич, планирование

```bash
@grant-architect спроектируй систему автоматической оценки заявок
```

### database-manager 💾
**Роль**: Эксперт по PostgreSQL и миграциям
**Эксперт в**: PostgreSQL 18, SQL оптимизация, миграции SQLite→PostgreSQL
**Используй для**: Схемы БД, оптимизация запросов, миграции

```bash
@database-manager оптимизируй запрос к grants таблице
```

### telegram-bot-developer 🤖
**Роль**: Разработчик Telegram бота
**Эксперт в**: python-telegram-bot v20+, conversation handlers, deep links
**Используй для**: Новые команды бота, handlers, user flows

```bash
@telegram-bot-developer добавь команду /status
```

### streamlit-admin-developer 📊
**Роль**: Разработчик Streamlit админ-панели
**Эксперт в**: Streamlit, data visualization, PostgreSQL integration
**Используй для**: UI страницы, дашборды, графики

```bash
@streamlit-admin-developer создай страницу аналитики грантов
```

### ai-integration-specialist 🧠
**Роль**: Эксперт по AI интеграции
**Эксперт в**: GigaChat API, Claude Code API, prompt engineering
**Используй для**: AI промпты, интеграция LLM, token optimization

```bash
@ai-integration-specialist улучши промпт для Writer агента
```

### test-engineer 🧪
**Роль**: Инженер по тестированию
**Эксперт в**: pytest, integration tests, E2E tests, mocking
**Используй для**: Написание тестов, debugging, coverage

```bash
@test-engineer напиши E2E тест для grant flow
```

### deployment-manager 🚀
**Роль**: Менеджер деплоя и мониторинга
**Эксперт в**: SSH, systemd, git, server monitoring, rollback
**Используй для**: Деплой на продакшн, проверка статуса, откат изменений

```bash
@deployment-manager задеплой последние изменения на 5.35.88.251
```

### documentation-keeper 📚
**Роль**: Хранитель актуальной документации
**Эксперт в**: Markdown, документирование кода, README, changelogs
**Используй для**: Обновление документации, changelog, README

```bash
@documentation-keeper обнови документацию после добавления фичи
```

### project-orchestrator 🎼
**Роль**: Координатор работы других агентов
**Эксперт в**: Делегирование задач, GC правила, multi-agent workflow
**Используй для**: Сложные задачи требующие нескольких агентов

```bash
@project-orchestrator реализуй новую фичу с тестами и деплоем
```

---

## 📊 Папки агентов (agents/[agent-name]/)

Некоторые агенты имеют собственные папки с документацией:

### database-manager/
- **MIGRATION_GUIDE.md** - Руководство по миграциям PostgreSQL
- **README.md** - Обзор database package
- **database_structure.md** - Структура БД

### deployment-manager/
- **README_SYNC.md** - Синхронизация с продакшном
- **reports/** - Отчеты о деплоях

### streamlit-admin-developer/
- **README_AGENTS_PAGE.md** - Документация страницы Агенты
- **HOSTING_SETUP.md** - Настройка хостинга
- **reports/** - Отчеты о рефакторинге UI

### test-engineer/
- **README_TESTING.md** - Руководство по тестированию

### telegram-bot-developer/
- **MENU_SETUP.md** - Настройка меню бота

---

## 🎯 Как использовать агентов

### В Claude Code CLI/IDE:

```bash
# Запустить агента с задачей
@grant-architect помоги спроектировать новую фичу

# Несколько агентов последовательно
@grant-architect спроектируй фичу
@test-engineer напиши тесты для нее
@deployment-manager задеплой

# Агент с чтением файла
@database-manager прочитай doc/schema.sql и оптимизируй
```

### В обычном чате (через Task tool):

```
Запусти @grant-architect агента с задачей:
Спроектируй систему автоматической оценки грантовых заявок
```

---

## 📝 Session Summaries

### Зачем нужны?

Claude Code **не имеет памяти** между сессиями. Session summaries помогают:
- Быстро восстановить контекст
- Понять что было сделано
- Увидеть next steps
- Найти ключевые файлы

### Как создавать?

В конце важной сессии:

```
Создай session summary в .claude/ о том что мы делали:
1. Какие файлы создали/изменили
2. Какие решения приняли
3. Что делать дальше
4. Ключевые инсайты
```

### Формат названия:

```
SESSION_SUMMARY_YYYY-MM-DD.md
SESSION_SUMMARY_2025-10-05.md  # пример
```

---

## 🔄 Обновление этой директории

### Когда добавлять новые файлы:

1. **Новый агент** → создать `agents/new-agent.md`
2. **Важная сессия** → создать `SESSION_SUMMARY_YYYY-MM-DD.md`
3. **Новая конфигурация** → обновить `settings.local.json`
4. **Отчет агента** → `agents/[agent-name]/reports/report.md`

### Правила:

- ✅ Все session summaries в корне `.claude/`
- ✅ Агенты в `agents/` директории
- ✅ Отчеты агентов в `agents/[agent-name]/reports/`
- ✅ Markdown формат для всех документов
- ✅ Русский язык для контента, английский для code

---

## 🎓 Best Practices

### 1. Начинай сессию с чтения SESSION_SUMMARY

```
Привет! Прочитай .claude/SESSION_SUMMARY_2025-10-05.md
```

### 2. Используй агентов для специфичных задач

```
# ❌ Плохо (без агента)
Создай миграцию PostgreSQL

# ✅ Хорошо (с агентом)
@database-manager создай миграцию для добавления таблицы ai_agent_settings
```

### 3. Сохраняй важные решения в Session Summary

После важной работы создавай summary чтобы не потерять контекст.

### 4. Обновляй QUICK_START после больших изменений

Если изменился main flow или появились новые ключевые файлы - обнови QUICK_START.

---

## 📚 Дополнительные ресурсы

- **CLAUDE.md** (корень проекта) - Основная память проекта
- **doc/** - Техническая документация
- **tests/TESTING_GUIDE.md** - Руководство по тестированию
- **.claude/agents/README.md** - Обзор всех агентов

---

## 🔗 Связь с основными файлами проекта

```
GrantService/
├── CLAUDE.md                    # Главная память проекта
├── .claude/                     # <-- ВЫ ЗДЕСЬ
│   ├── SESSION_SUMMARY_*.md    # Память о сессиях
│   ├── QUICK_START_*.md        # Инструкции быстрого старта
│   └── agents/                 # Кастомные агенты
│
├── doc/                        # Техническая документация
│   └── AI_AGENTS_SETTINGS_ARCHITECTURE.md  # Пример
│
└── tests/                      # Тесты
    └── TESTING_GUIDE.md
```

---

**Создано**: 2025-10-05
**Обновлено**: 2025-10-05
**Версия**: 1.0

---

## ✅ Quick Reference

**Восстановить контекст** → `.claude/SESSION_SUMMARY_2025-10-05.md`
**Быстрый старт** → `.claude/QUICK_START_NEXT_SESSION.md`
**Список агентов** → `.claude/agents/README.md`
**Главная память** → `CLAUDE.md` (корень проекта)
