# Claude Code: Best Practices Guide

**36 профессиональных советов для максимальной эффективности работы с Claude Code**

---

## 🌟 ТОП-6 САМЫХ ВАЖНЫХ ПРАКТИК

Эти практики оказывают наибольшее влияние на продуктивность работы с Claude Code:

### #14 - Claude.md файл (САМОЕ ВАЖНОЕ!)

**Почему это критично:** Claude.md - это "память проекта". Этот файл автоматически добавляется в контекст при каждой задаче.

**Что включать:**
- Git workflows и best practices
- Архитектура проекта и обзор
- Build команды
- Best practices для тестирования, отладки, аналитики
- Документация и How-to руководства

**Пример структуры:**
```markdown
# Git Workflow
- Всегда создавать ветку перед началом работы
- Делать коммиты регулярно
- Никогда не пушить напрямую в main

# Architecture
- Frontend: React + TypeScript
- Backend: Node.js + Express
- Database: PostgreSQL

# Build Commands
npm run dev    # Development
npm run build  # Production build
npm test       # Run tests
```

**Pro tip:** Не нужно писать Claude.md вручную - попросите Claude создать его за вас!

---

### #30 - Multi-clauding с Git Worktrees (Недельный объём работы за часы)

**Что это:** Запуск нескольких экземпляров Claude Code одновременно для работы над разными фичами без конфликтов.

**Как настроить:**
1. Создайте скрытую папку: `mkdir .trees`
2. Создайте worktree для каждой фичи:
   ```bash
   git worktree add .trees/feature-auth feature-auth
   git worktree add .trees/feature-payments feature-payments
   git worktree add .trees/feature-analytics feature-analytics
   ```
3. Откройте терминал для каждого worktree
4. Запустите Claude Code в каждом терминале
5. Работайте параллельно над всеми фичами

**Когда закончите:**
- Попросите Claude слить все worktrees вместе
- Claude автоматически разрешит конфликты
- Получите чистую git историю

**Результат:** Неделя разработки за несколько часов!

---

### #4 - Todo Lists (Ключевая фича Claude Code)

**Почему это важно:** Todo списки - это то, что выделяет Claude Code среди других AI coding tools. Вместо бездумного написания кода, Claude сначала планирует.

**Как работает:**
- Claude автоматически создаёт todo список для сложных задач
- Отмечает выполненные пункты в реальном времени
- Предотвращает зацикливание и потерю прогресса

**Как использовать явно:**
```
Создай функцию аутентификации. Используй todo список для структурирования работы.
```

**Преимущества:**
- Видите текущий прогресс
- Понимаете, что будет дальше
- Claude работает структурированно над большими задачами

---

### #17 - Planning Mode (Планировать перед реализацией)

**Что это:** Режим, в котором Claude создаёт план ПЕРЕД написанием кода.

**Как активировать:** Нажмите Tab + Shift до появления "Plan Only Mode"

**Когда использовать:**
- Архитектурные решения
- Сложные баги
- Новые большие фичи
- Критические изменения

**Pro tip:** Используйте **Opus Plan Mode** (команда `/model`):
- Opus для планирования (мощная модель)
- Sonnet для имплементации (быстрая и дешёвая модель)
- Лучшее соотношение качества и стоимости

**Комбинация:**
```
Planning Mode + Think Hard + Markdown Output = Мощный workflow
```

---

### #29 - Parallel Subagents (Множественные решения)

**Что это:** Claude создаёт несколько независимых агентов для изучения разных подходов к решению задачи.

**Как использовать:**
```
Спланируй добавление системы оплаты. Используй parallel subagents
для изучения разных решений (Stripe vs PayPal vs Paddle).
```

**Преимущества:**
- Исследование нескольких вариантов одновременно
- Сравнение подходов
- Выбор лучшего решения
- Как команда на брейншторминге

**Идеально для:**
- Сложных фич
- Критических багов
- Архитектурных решений

---

### #28 - Mindset: Думай как Product Manager

**Два ключевых принципа:**

**1. Давай Claude чёткий контекст и ограничения**
- Не: "Добавь аутентификацию"
- Да: "Добавь JWT аутентификацию с refresh tokens, используя bcrypt для хеширования паролей. Храни токены в httpOnly cookies. Добавь rate limiting для защиты от брутфорса."

**2. Проверяй результаты на высоком уровне абстракции**
- ❌ НЕ нужно: Читать каждую строку кода
- ✅ НУЖНО: Проверять, что:
  - Приложение работает как задумано
  - Тесты проходят
  - UX соответствует ожиданиям

**Аналогия:** Управление умными людьми в команде - доверяй, но проверяй результаты.

**Эта смена мышления критична для продуктивности с AI coding tools!**

---

## 📚 ПОЛНЫЙ СПИСОК ВСЕХ 36 СОВЕТОВ

---

## LEVEL 1: BEGINNER (Основы)

### Установка и начало работы

#### Tip #1: Установка на локальную машину
Самый простой способ начать - установить Claude Code локально через терминал.

```bash
# Копируйте команду с сайта Anthropic и запустите
npm install -g @anthropic-ai/claude-code
```

**Преимущества:**
- Быстрая установка
- Немедленное начало работы
- Доступ ко всем локальным файлам

---

#### Tip #2: Установка на удалённый сервер
Установите Claude Code на сервер (AWS, Digital Ocean, Hetzner) для backend проектов.

```bash
# SSH на сервер
ssh user@your-server.com

# Установите Claude Code
npm install -g @anthropic-ai/claude-code
```

**Преимущества:**
- Кодирование из любого места
- Можно использовать Claude Code с телефона через Termius App
- Не нагружает локальную машину

---

#### Tip #3: Использование внутри других инструментов
Claude Code работает внутри Cursor, Windsurf и VS Code.

**Как начать:**
- Откройте директорию проекта
- Запустите: `claude` в терминале
- Используйте `claude --resume` для продолжения предыдущей сессии

**Идеально для:** Тех, кто уже использует эти IDE и не хочет переходить на чистый терминал.

---

### Основные фичи и команды

#### Tip #4: Todo Lists ⭐ (УЖЕ ОПИСАНО ВЫШЕ)

#### Tip #5: Bash Mode
Запускайте bash команды прямо внутри Claude Code без выхода из сессии.

**Что может делать Claude:**
- Читать и записывать файлы
- Искать по файлам
- Выполнять git команды
- Любые shell операции

**Пример:**
```
Прочитай все файлы в папке src/components и используй их для понимания структуры проекта
```

---

#### Tip #6: Instant Documentation
Попросите Claude изучить и задокументировать архитектуру проекта.

**Пример:**
```
Изучи архитектуру приложения и создай файл architecture.md с подробным описанием
```

**Когда использовать:**
- Новый проект
- Проект, к которому не прикасались несколько недель
- Документация для команды
- Создание контекста для будущих задач Claude

---

#### Tip #8: Auto Accept Mode
Автоматическое принятие всех изменений без подтверждения.

**Как активировать:** Shift + Tab (переключение режимов)

**Когда использовать:**
- Доверяете Claude на 100%
- Рутинные задачи
- Хотите максимальную скорость

**⚠️ Осторожно:** Используйте с умом на критических проектах!

---

#### Tip #9: Model Switching
Переключение между разными моделями Anthropic для разных задач.

**Команда:** `/model`

**Доступные модели:**
- **Opus** - Самая мощная модель (сложные задачи, глубокий анализ)
- **Sonnet** - Быстрая и эффективная модель (рутинные задачи)
- **Opus Plan Mode** - Opus для планирования, Sonnet для кода (рекомендуется!)

**Стратегия:**
- По умолчанию: Opus до достижения 50% лимита, потом Sonnet
- Рекомендация: Opus Plan Mode для лучшего соотношения цена/качество

---

#### Tip #10: Don't Be Afraid to Interrupt
Клавиша Escape - ваш друг.

**Как использовать:**
- **Escape 1 раз** - Прервать текущую задачу Claude
- **Escape 2 раза** - Вернуться к предыдущему промпту

**Золотое правило:** Лучше прервать рано, если Claude идёт не туда, чем тратить токены впустую.

---

### Отладка и тестирование

#### Tip #11: Screenshot Method for Debugging
Claude Code принимает изображения на вход.

**Как использовать:**
1. Сделайте скриншот UI проблемы
2. Прикрепите скриншот к промпту
3. Claude видит полный контекст и понимает проблему

**Также используйте для:**
- UI дизайны
- Диаграммы архитектуры
- Mockups для реализации

**Самый частый use case:** Отладка UI багов

---

#### Tip #12: Let Claude Write Tests
Попросите Claude написать тесты для вашего кода.

**Пример:**
```
Напиши тесты для функции onboarding flow
```

**Best practice:** Фокусируйтесь на end-to-end тестах, а не на тестах специфичных для implementation details.

---

#### Tip #13: Test Driven Development (TDD)
Попросите Claude сначала написать тесты, потом реализацию.

**Workflow:**
```
1. Напиши тесты для системы аутентификации
2. Теперь реализуй код, чтобы тесты прошли
```

**Преимущества:**
- Claude ловит проблемы раньше
- Структурированный подход
- Лучшее качество кода

---

### Конфигурация проекта

#### Tip #14: Claude.md File ⭐ (УЖЕ ОПИСАНО ВЫШЕ)

#### Tip #15: Message Queue
Не ждите окончания текущей задачи - добавляйте новые задачи в очередь.

**Как работает:**
1. Claude работает над задачей
2. Вы печатаете новую инструкцию
3. Она добавляется в message queue
4. Claude выполнит её после текущей задачи

**Преимущества:**
- Не теряете мысли
- Не прерываете workflow
- Claude работает последовательно через все задачи

**Используйте:** Когда приходят идеи во время работы Claude

---

#### Tip #16: Markdown File Prompts
Длинные промпты можно хранить в markdown файлах.

**Как использовать:**
1. Создайте файл `feature-spec.md` с подробным описанием
2. Ссылайтесь на него: `@feature-spec.md`

**Преимущества:**
- Чище, чем длинные промпты в терминале
- Можно обдумать и отредактировать перед отправкой
- Переиспользование промптов

---

## LEVEL 2: INTERMEDIATE (Продвинутые workflow)

### Планирование и thinking

#### Tip #17: Planning Mode ⭐ (УЖЕ ОПИСАНО ВЫШЕ)

#### Tip #18: Opus Plan Mode ⭐ (УЖЕ ОПИСАНО ВЫШЕ В TIP #17)

#### Tip #19: Parallel Subagents for Multiple Plans
(Связано с Tip #29, см. ниже)

---

#### Tip #20-22: Think Keywords (Basic, Hard, Ultra)

Контролируйте, сколько времени Claude тратит на размышления.

**Три уровня:**

**Basic Think:**
```
think: Как лучше реализовать кеширование?
```

**Think Hard:**
```
think hard: Спроектируй архитектуру микросервисов для e-commerce платформы
```

**Ultra Think:**
```
ultra think: Оптимизируй этот алгоритм для обработки миллионов записей
```

**Когда использовать:**
- Basic: Простые вопросы дизайна
- Hard: Сложные архитектурные решения
- Ultra: Критические оптимизации и алгоритмы

**Pro combo:**
```
Planning Mode + Think Hard + Markdown Output = Мощнейший инструмент планирования
```

---

### Больше чем код: Research, Documentation, Changelogs

#### Tip #23: Research with Web Search
Claude Code имеет web search и web fetch инструменты.

**Примеры использования:**

**Малые задачи:**
```
Найди документацию Stripe API для создания subscription
```

**Большие задачи:**
```
Исследуй и создай отчёт: какой UI framework лучше всего подходит
для нашего приложения с учётом требований к accessibility
```

**Мощь:** Claude учитывает контекст вашего приложения при исследовании!

---

#### Tip #24: Claude Can Read PDFs
Комбинируйте PDF файлы с web search для более глубокого исследования.

**Use case:**
1. Получите ChatGPT Deep Research report в PDF
2. Загрузите его Claude
3. Claude использует информацию из PDF + web search
4. Получаете более качественный research

**Другие применения:**
- Технические спецификации
- API документация
- Дизайн документы

---

#### Tip #25: Document Generation
Claude отлично генерирует документацию с учётом контекста проекта.

**Что генерировать:**
- **PRD** (Product Requirement Documents) для фич
- **User Experience Guides**
- **API Documentation**
- **Technical Design Docs**
- **Architecture Decisions Records (ADR)**

**Почему лучше чем ChatGPT:**
- Учитывает реальную структуру вашего приложения
- Использует весь контекст проекта
- Более точные и релевантные документы

**Пример:**
```
Создай PRD для системы уведомлений. Учти текущую архитектуру
и интеграцию с существующим backend
```

---

#### Tip #26: Automatic Change Tracking
Используйте Claude для автоматического отслеживания изменений в проекте.

**Что создавать:**
- **CHANGELOG.md** - история изменений
- **Feature documentation** - актуальные фичи для сайта
- **Decision docs** - почему было принято решение
- **Migration guides** - как обновляться между версиями

**Пример workflow:**
```
После каждой фичи обнови CHANGELOG.md и создай entry в decision docs,
объясняющий архитектурный выбор
```

**Почему это важно:**
- Ваше будущее "я" поблагодарит вас
- Будущие Claude агенты будут иметь контекст
- Команда понимает эволюцию проекта

---

### GitHub Integration

#### Tip #27: GitHub Actions Integration
Claude Code глубоко интегрируется с GitHub для автоматизации workflow.

**Как настроить:**
```bash
# В Claude Code выполните:
/install gh-actions
```

**Что можно делать:**

**1. Tag Claude в issues:**
```
@claude-code fix this authentication bug
```

**2. Tag Claude в Pull Requests:**
```
@claude-code review this PR and suggest improvements
```

**Что происходит:**
- Claude запускается через GitHub Actions
- Работает в облаке (не на вашей машине)
- Создаёт PR с фиксом
- Автоматически ревьюит код

**Идеально для:** Команды, работающие с GitHub

---

### Mindset

#### Tip #28: Think Like a Product Manager ⭐ (УЖЕ ОПИСАНО ВЫШЕ)

---

## LEVEL 3: MASTER (Мастерство)

### Работа в параллель

#### Tip #29: Parallel Subagents ⭐ (УЖЕ ОПИСАНО ВЫШЕ)

#### Tip #30: Multi-Clauding with Git Worktrees ⭐ (УЖЕ ОПИСАНО ВЫШЕ)

---

### Продвинутая кастомизация

#### Tip #31-33: Custom Slash Commands

Создавайте сокращённые команды для повторяющихся задач.

**Зачем:** Вместо длинных промптов используйте короткие команды.

**Как создать (простой способ):**
```
Claude, создай custom команду /changelog, которая будет обновлять CHANGELOG.md
```

**Как создать (вручную):**

1. Создайте папку: `.claude/commands/` в проекте
2. Создайте файл: `changelog.md`
3. Структура файла:

```markdown
# Changelog Updater

## Description
Updates CHANGELOG.md with recent changes

## Allowed Tools
- bash
- read
- write

## Command Prompt
1. Read git log since last release
2. Categorize changes (features, fixes, breaking changes)
3. Update CHANGELOG.md with new entry
4. Format using Keep a Changelog standard
```

**Project-specific vs Personal:**
- **Project commands:** `.claude/commands/` в проекте
- **Personal commands:** `~/.config/claude-code/commands/` (работают везде)

**⚠️ Важно:** Custom commands НЕ добавляются в контекст автоматически!
Для постоянного контекста используйте `claude.md`

**Примеры custom commands:**
- `/changelog` - обновить changelog
- `/deploy` - задеплоить приложение
- `/test-all` - запустить все тесты
- `/docs` - сгенерировать документацию
- `/review` - code review текущих изменений

---

#### Tip #34-35: Custom Subagents

Создавайте специализированных AI ассистентов для определённых задач.

**Что это:** Subagents с кастомными промптами и разрешениями на инструменты.

**Как создать:**
```bash
# В Claude Code:
/agents
# Следуйте wizard для создания нового агента
```

**Что происходит под капотом:**
- Создаётся markdown файл в `.claude/agents/`
- Указывается тип агента, описание использования
- Определяются доступные инструменты
- Задаётся system prompt

**Примеры специализированных агентов:**

**1. UX Design Agent:**
```markdown
# UX Design Specialist

## Agent Type
ux-designer

## Usage
Use for user experience design, UI/UX improvements, and accessibility

## Accessible Tools
- read
- write
- web-search

## System Prompt
You are a UX design specialist. Focus on user-centered design,
accessibility (WCAG compliance), and modern UI/UX best practices.
Always consider mobile-first design and responsive layouts.
```

**2. Security Review Agent:**
```markdown
# Security Auditor

## Agent Type
security-reviewer

## Usage
Use for security audits, vulnerability scanning, and secure coding practices

## Accessible Tools
- read
- grep
- bash

## System Prompt
You are a security specialist. Review code for common vulnerabilities
(OWASP Top 10), check for SQL injection, XSS, CSRF, insecure dependencies.
Always suggest security best practices and threat mitigation.
```

**3. Database Agent:**
```markdown
# Database Administrator

## Agent Type
database-admin

## Usage
Use for database design, query optimization, and data migrations

## System Prompt
You are a database specialist. Focus on query optimization,
proper indexing, data normalization, and efficient schema design.
```

**Как Claude использует субагентов:**

**Автоматически:**
- Claude видит доступных субагентов
- Читает описание usage
- Делегирует задачи релевантному субагенту

**Явно:**
```
Используй test-runner субагента для запуска всех тестов

Используй database-admin агента для оптимизации этих SQL запросов
```

**Project-specific vs Personal:**
- Project: `.claude/agents/` в проекте
- Personal: `~/.config/claude-code/agents/` (везде)

---

### MCP Servers

#### Tip #36: MCP Server Usage

Расширяйте возможности Claude Code через Model Context Protocol (MCP).

**Что такое MCP:**
Протокол для интеграции Claude Code с внешними инструментами и сервисами.

**Популярные MCP серверы:**

**1. Database MCP:**
- **MongoDB MCP** - прямая работа с MongoDB
- **PostgreSQL MCP** - запросы к Postgres
- **Supabase MCP** - интеграция с Supabase

**Use case:**
```
Используя PostgreSQL MCP, проанализируй медленные запросы
и предложи индексы для оптимизации
```

**2. Playwright MCP (Browser Automation):**
- Claude видит ваш UI визуально
- Может взаимодействовать с браузером
- Идеально для тестирования и отладки

**Use case:**
```
Используя Playwright MCP, протестируй процесс регистрации
и найди UX проблемы
```

**3. Figma MCP (Design to Code):**
- Прямая интеграция с Figma
- Конвертация дизайнов в код
- Sync между дизайном и кодом

**Use case:**
```
Используя Figma MCP, импортируй дизайн Dashboard
и создай React компоненты
```

**Другие полезные MCP:**
- **Notion MCP** - работа с Notion документами
- **Slack MCP** - интеграция со Slack
- **Linear MCP** - task management
- **Sentry MCP** - error tracking

**Как настроить MCP:**
Обычно через конфигурационный файл Claude Code (проверьте документацию конкретного MCP).

**Будущее MCP:**
Экосистема MCP серверов быстро растёт - это будет всё более мощный инструмент!

---

## 💰 СТОИМОСТЬ И ЦЕННОСТЬ

### Ценовые планы:

**Pro Plan - $20/месяц**
- Базовый доступ к Claude Code
- Подходит для начала и экспериментов
- Ограниченные rate limits

**Max 5X Plan - $100/месяц**
- 5x выше rate limits чем Pro
- Рекомендуется для серьёзной разработки

**Max 20X Plan - $200/месяц** (рекомендуется автором)
- 20x выше rate limits
- Для профессионального использования
- Максимальная продуктивность

**Anthropic API**
- Очень дорого (pay-per-use)
- Только для enterprise компаний
- Не рекомендуется для индивидуалов

### Стоит ли своих денег?

**ДА!** Claude Code окупает себя через:
- Экономию времени (недели за часы с multi-clauding)
- Качество кода с auto-тестами
- Документацию и планирование
- Интеграцию с workflow

**⚠️ Примечание:** Anthropic анонсировал дополнительные weekly rate limits для Max users (начало с августа). Следите за обновлениями.

---

## 🎯 БЫСТРАЯ ШПАРГАЛКА ПО КОМАНДАМ

### Горячие клавиши:
- **Shift + Tab** - Переключение режимов (Auto Accept, Plan Only)
- **Escape (1x)** - Прервать Claude
- **Escape (2x)** - Вернуться к предыдущему промпту

### Slash команды:
- `/model` - Переключить модель (Opus/Sonnet/Opus Plan)
- `/install gh-actions` - Установить GitHub Actions интеграцию
- `/agents` - Управление custom субагентами
- `@filename.md` - Ссылка на файл в промпте

### Ключевые слова:
- `think` - Базовое размышление
- `think hard` - Глубокий анализ
- `ultra think` - Максимальная мощность мышления

---

## 📋 WORKFLOW TEMPLATES

### Template 1: Новая фича (Полный цикл)
```
1. Planning Mode: Спланируй архитектуру фичи
2. Think Hard: Продумай edge cases
3. Используй todo list для структурирования
4. TDD: Сначала тесты, потом код
5. Обнови claude.md с новыми правилами
6. Обнови CHANGELOG.md
7. Создай decision doc с объяснением решений
8. GitHub Actions: Создай PR
```

### Template 2: Исправление бага
```
1. Screenshot Method: Покажи баг
2. Planning Mode: Спланируй подход
3. Think: Проанализируй root cause
4. Исправь баг
5. Напиши regression test
6. Задокументируй в changelog
```

### Template 3: Research задача
```
1. Web Search: Исследуй опции
2. PDF Reading: Добавь документацию
3. Parallel Subagents: Изучи разные подходы
4. Document Generation: Создай comparison report
5. Сохрани в markdown для будущего reference
```

### Template 4: Multi-feature Development (Master Level)
```
1. Создай git worktrees для каждой фичи
2. Запусти multiple Claude instances
3. Для каждого Claude:
   - Planning Mode
   - Todo Lists
   - TDD approach
4. Параллельная разработка
5. Попроси Claude слить всё вместе
6. Review финального результата на high level
```

---

## ✅ CHECKLIST: Готовы ли вы к Claude Code?

### Beginner Checklist:
- [ ] Claude Code установлен (локально или на сервере)
- [ ] Создан claude.md файл для проекта
- [ ] Понимаю, как использовать todo lists
- [ ] Знаю, как прерывать Claude (Escape)
- [ ] Умею переключать модели (/model)
- [ ] Пробовал bash mode для чтения файлов

### Intermediate Checklist:
- [ ] Использую Planning Mode для сложных задач
- [ ] Применяю think keywords по необходимости
- [ ] Генерирую документацию через Claude
- [ ] Использую web search для research
- [ ] Настроена GitHub Actions интеграция
- [ ] Мыслю как Product Manager (high-level verification)

### Master Checklist:
- [ ] Создал custom slash commands для частых задач
- [ ] Настроил specialized субагентов
- [ ] Использую git worktrees + multiple Claude instances
- [ ] Интегрировал MCP servers для расширения возможностей
- [ ] Применяю parallel subagents для exploration
- [ ] Получаю недельный объём работы за несколько часов

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ

### Если вы новичок:
1. Начните с простой задачи
2. Создайте claude.md файл
3. Используйте todo lists
4. Экспериментируйте с planning mode

### Если на intermediate уровне:
1. Попробуйте multi-clauding с git worktrees
2. Создайте первый custom субагент
3. Интегрируйте с GitHub Actions
4. Используйте web search для research задач

### Если стремитесь к мастерству:
1. Настройте полный набор custom commands
2. Создайте библиотеку специализированных субагентов
3. Интегрируйте MCP серверы для вашего стека
4. Оптимизируйте workflow для максимальной параллельности

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- **Официальная документация:** https://docs.anthropic.com/claude-code
- **GitHub:** https://github.com/anthropics/claude-code
- **Community:** Discord, Reddit для обмена опытом
- **MCP Servers:** https://github.com/modelcontextprotocol

---

**Создано:** На основе видео "Claude Code: The New King of AI Coding?" by Avthar
**Всего советов:** 36 (16 Beginner + 12 Intermediate + 8 Master)
**Версия:** 1.0
**Дата:** 2025-10-05

---

**Помните:** Используйте Claude Code, чтобы помочь вам лучше использовать Claude Code! Попросите Claude обновить этот файл по мере открытия новых практик.
