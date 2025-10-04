# GrantService Agents Architecture

Команда специализированных AI агентов для управления проектом GrantService.

## 📂 Структура

```
.claude/agents/
├── README.md                          # этот файл
├── project-orchestrator/              # главный оркестратор
│   ├── project-orchestrator.md        # определение агента
│   ├── gc-rules.yaml                  # правила garbage collection
│   └── reports/                       # артефакты оркестратора
│       ├── task_delegation_log.md
│       ├── gc_cleanup_log.md
│       └── architecture_decisions.md
│
├── grant-architect/                   # архитектор грантовой системы
│   └── grant-architect.md
│
├── streamlit-admin-developer/         # разработчик админ-панели
│   ├── streamlit-admin-developer.md
│   ├── streamlit-admin-developer2.md
│   └── reports/                       # временные артефакты
│       └── [auto-cleaned]
│
├── telegram-bot-developer/            # разработчик бота
│   ├── telegram-bot-developer.md
│   └── reports/
│
├── database-manager/                  # менеджер БД
│   ├── database-manager.md
│   └── reports/                       # миграции (архивируются)
│
├── ai-integration-specialist/         # AI интеграции
│   ├── ai-integration-specialist.md
│   └── reports/
│
├── test-engineer/                     # тестирование и QA
│   ├── test-engineer.md
│   └── reports/                       # удаляются после деплоя
│
├── deployment-manager/                # деплой и DevOps
│   ├── deployment-manager.md
│   └── reports/                       # архивируются на 90 дней
│
└── documentation-keeper/              # документация
    ├── documentation-keeper.md
    └── reports/                       # permanent
```

## 🎭 Команда агентов

### 🎯 Project Orchestrator
**Роль:** Главный координатор
**Задачи:**
- Анализ задач и делегирование агентам
- Контроль качества интеграции
- Управление garbage collection
- Архитектурный надзор

**Вызов:**
```bash
/claude-chat project-orchestrator
```

### 🏗️ Development Team

#### Grant Architect
Архитектор грантовой системы и бизнес-логики

#### Streamlit Admin Developer
Разработка админ-панели на Streamlit

#### Telegram Bot Developer
Разработка Telegram бота для пользователей

#### Database Manager
Управление схемой БД, миграциями, оптимизация запросов

#### AI Integration Specialist
Интеграция с LLM (OpenAI, Claude), векторные БД, RAG

### 🔧 Operations Team

#### Test Engineer
Тестирование, QA, написание тестов, CI/CD проверки

#### Deployment Manager
Деплой, мониторинг, настройка серверов, Docker

#### Documentation Keeper
Поддержка актуальности документации

## 📋 Правила работы

### Размещение артефактов

**✅ ПРАВИЛЬНО:**
```
# Временные отчёты агентов
.claude/agents/{agent-name}/reports/2025-10-03_feature_report.md

# Постоянная документация
doc/ARCHITECTURE.md

# Архив важных отчётов
reports/archive/2025-10/audits/security_audit.md
```

**❌ НЕПРАВИЛЬНО:**
```
# НЕ размещать отчёты в корне doc/
doc/TEST_REPORT_AGENTS_PAGE.md

# НЕ создавать временные файлы в корне
REFACTORING_PHASE1_REPORT.md
```

### Garbage Collection

**Автоматическая очистка:**
- Отчёты агентов старше 7 дней → удаление
- Тестовые отчёты после деплоя → удаление
- Аудиты старше 30 дней → архив
- Миграции БД → архив на 90 дней

**Permanent файлы (никогда не удаляются):**
- `doc/ARCHITECTURE.md`
- `doc/API_REFERENCE.md`
- `doc/DATABASE.md`
- `doc/DEPLOYMENT.md`
- `doc/README.md`
- `doc/CHANGELOG.md`

**Конфигурация:** `.claude/agents/project-orchestrator/gc-rules.yaml`

## 🚀 Workflow примеры

### Новая фича

```yaml
Задача: "Добавить экспорт грантов в Excel"

Оркестратор делегирует:
  1. grant-architect → проектирование архитектуры
  2. streamlit-admin-developer → UI для экспорта
  3. database-manager → оптимизация запросов
  4. test-engineer → тесты функционала
  5. documentation-keeper → обновить docs

Артефакты:
  - .claude/agents/streamlit-admin-developer/reports/2025-10-03_excel_export.md
  - .claude/agents/test-engineer/reports/2025-10-03_export_tests.md

После деплоя:
  - Отчёты разработки → удалены (7 дней)
  - Отчёты тестов → удалены (триггер on_deploy)
  - doc/CHANGELOG.md → обновлён
```

### Исправление бага

```yaml
Задача: "Фикс ошибки при отправке заявки"

Оркестратор делегирует:
  1. telegram-bot-developer → исправление кода
  2. test-engineer → regression тесты

Артефакты:
  - .claude/agents/telegram-bot-developer/reports/2025-10-03_submit_fix.md

После деплоя:
  - Отчёты → удалены
```

### Рефакторинг

```yaml
Задача: "Рефакторинг системы авторизации"

Оркестратор делегирует:
  1. grant-architect → новая архитектура auth
  2. streamlit-admin-developer → обновление админки
  3. telegram-bot-developer → обновление бота
  4. test-engineer → полное тестирование
  5. documentation-keeper → обновить ARCHITECTURE.md

Артефакты:
  - .claude/agents/grant-architect/reports/2025-10-03_auth_refactoring_plan.md
  - Отчёты других агентов в их reports/

Финальный отчёт:
  - reports/archive/2025-10/refactoring/auth_system_refactoring.md (архив)
```

## 🔧 Управление

### Вызов конкретного агента

```bash
# Прямой вызов
/claude-chat streamlit-admin-developer

# Через оркестратор (рекомендуется)
/claude-chat project-orchestrator "делегируй streamlit-admin-developer задачу..."
```

### Просмотр логов агента

```bash
# Отчёты конкретного агента
ls .claude/agents/test-engineer/reports/

# Логи оркестратора
cat .claude/agents/project-orchestrator/reports/task_delegation_log.md
cat .claude/agents/project-orchestrator/reports/gc_cleanup_log.md
```

### Ручная очистка

```bash
# Очистка артефактов всех агентов
rm -rf .claude/agents/*/reports/*

# Очистка конкретного агента
rm -rf .claude/agents/test-engineer/reports/*

# Архивация перед очисткой
mkdir -p reports/archive/2025-10
cp .claude/agents/*/reports/*.md reports/archive/2025-10/
```

## 📊 Мониторинг

### Проверка размера артефактов

```bash
# Размер всех артефактов агентов
du -sh .claude/agents/*/reports

# Топ агентов по размеру артефактов
du -sh .claude/agents/*/reports | sort -hr | head -5
```

### Статистика файлов

```bash
# Количество отчётов по агентам
find .claude/agents -type f -name "*.md" | grep reports | wc -l

# Старые файлы (> 7 дней)
find .claude/agents/*/reports -type f -mtime +7
```

## 🎯 Best Practices

### ДЛЯ АГЕНТОВ:

1. **Артефакты только в свою папку**
   ```
   ✅ .claude/agents/{your-name}/reports/
   ❌ doc/
   ❌ корень проекта
   ```

2. **Именование с датой**
   ```
   ✅ 2025-10-03_feature_implementation.md
   ✅ test_report_2025-10-03.md
   ❌ report.md
   ❌ temp_notes.md
   ```

3. **Обновление permanent docs**
   ```
   ✅ Обновить doc/ARCHITECTURE.md при изменении архитектуры
   ✅ Обновить doc/API_REFERENCE.md при новых API
   ❌ Создавать новый файл для каждого изменения
   ```

### ДЛЯ ПОЛЬЗОВАТЕЛЕЙ:

1. **Используй оркестратор для сложных задач**
2. **Проверяй логи после работы агентов**
3. **Запускай GC cleanup еженедельно**
4. **Архивируй важные отчёты вручную**

## 🆘 Troubleshooting

### Проблема: Слишком много файлов в doc/

**Решение:**
```bash
# 1. Запусти оркестратор для очистки
/claude-chat project-orchestrator "проведи garbage collection"

# 2. Или вручную перенеси отчёты
mv doc/*_REPORT_*.md .claude/agents/*/reports/
mv doc/REFACTORING_*.md reports/archive/2025-10/
```

### Проблема: Не могу найти отчёт агента

**Решение:**
```bash
# Поиск по всем артефактам
find .claude/agents -name "*keyword*"

# Поиск в архивах
find reports/archive -name "*keyword*"
```

### Проблема: Агент создал файл не в своей папке

**Решение:**
1. Переместить в правильное место
2. Сообщить оркестратору для обновления правил
3. Проверить определение агента

## 📚 Дополнительно

- **Конфигурация GC:** `.claude/agents/project-orchestrator/gc-rules.yaml`
- **Логи оркестратора:** `.claude/agents/project-orchestrator/reports/`
- **Архив:** `reports/archive/{year}-{month}/`
- **Основная документация:** `doc/`

## 🔄 Версионирование

**Текущая версия:** 1.0
**Дата:** 2025-10-03

**История изменений:**
- v1.0 (2025-10-03): Начальная структура с оркестратором и GC правилами
