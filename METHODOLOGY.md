# GrantService Project - Development Methodology

**Version:** 1.0.0
**Based on:** Project Evolution Methodology v1.0.0
**Status:** Active

---

## 📚 Основная методология

Этот проект следует **Project Evolution Methodology** - универсальной методологии разработки для всех проектов SnowWhiteAI.

**Полная методология:**
```
C:\SnowWhiteAI\cradle\01-Active-Projects\Project-Evolution-Methodology\PROJECT-EVOLUTION-METHODOLOGY.md
```

**Философия:** Разрабатывать проекты как живые организмы - контролируемый рост с сохранением целостности.

**Основа:** 119 KB исследований (WebSearch + Perplexity + Parallel)

---

## 🎯 Краткая суть (One-Sentence Summary)

**Разрабатывай проект через малые частые изменения (метаболизм), автоматизированные проверки стабильности (гомеостаз) и управляемый технический долг (регенерация) - измеряемые DORA метриками.**

---

## 🔄 5-шаговый процесс итерации

### STEP 1: PLAN (Планирование)
- Приоритизация backlog
- Распределение: 80% новые фичи, 20% технический долг
- Определение метрик успеха
- Разбивка задач (<1 день каждая)
- Sprint goal (одно предложение)

### STEP 2: DEVELOP (Разработка)
- Малые коммиты (<200 строк)
- Trunk-based development
- Автоматизированные тесты на каждый коммит
- Code review (<4 часа)
- Continuous Integration

### STEP 3: INTEGRATE (Интеграция)
- Автоматическая сборка
- Интеграционные тесты
- Security scanning
- Performance testing
- Зелёный pipeline = готово к деплою

### STEP 4: DEPLOY (Деплой)
- Автоматизированный деплой
- Blue-green или canary deployment
- Мониторинг метрик после деплоя
- Rollback готов к использованию
- Feature flags для постепенного rollout

### STEP 5: MEASURE (Измерение)
- DORA метрики (deployment frequency, lead time, MTTR, failure rate)
- User feedback анализ
- Error budget tracking
- Retrospective (что улучшить)
- Документирование learnings

---

## 📊 DORA Metrics для GrantService

**Deployment Frequency:** Как часто деплоим в production
- **Цель:** 1+ раз в неделю
- **Elite:** Несколько раз в день

**Lead Time for Changes:** От коммита до production
- **Цель:** <1 день
- **Elite:** <1 час

**Mean Time to Recovery (MTTR):** Время восстановления после сбоя
- **Цель:** <1 час
- **Elite:** <15 минут

**Change Failure Rate:** % деплоев вызывающих проблемы
- **Цель:** <15%
- **Elite:** <5%

---

## ✅ Применение к GrantService

### Что уже делаем правильно:

**✅ Малые итерации:**
- Iteration 40: 6 тестов (isolated testing)
- Iteration 41: 100 realistic interviews
- Iteration 42: Real dialog flow
- Iteration 43: Full production flow
- Iteration 44: Project consolidation
- Iteration 45: Full flow testing (planned)

**✅ Git workflow:**
- Trunk-based development (master branch)
- Commit messages с контекстом
- Git history сохранена (git mv при refactoring)

**✅ Документация:**
- ITERATION_HISTORY.md (история изменений)
- Iteration summaries (детальные отчёты)
- Session state tracking

**✅ Тестирование:**
- Unit tests (agents, database)
- Integration tests (full flow)
- Realistic user simulation (SyntheticUserSimulator)

### Что нужно улучшить:

**🔧 CI/CD Pipeline:**
- [ ] Автоматизированные тесты при каждом коммите
- [ ] Automated deployment pipeline
- [ ] Pre-commit hooks для тестов

**🔧 Code Review:**
- [ ] Формализовать process (сейчас ad-hoc)
- [ ] Approval required для merge
- [ ] Review checklist

**🔧 Monitoring:**
- [ ] Error tracking (Sentry или аналог)
- [ ] Performance monitoring
- [ ] User analytics (Telegram bot metrics)

**🔧 DORA Metrics Tracking:**
- [ ] Deployment frequency measurement
- [ ] Lead time tracking
- [ ] MTTR calculation
- [ ] Change failure rate tracking

---

## 🎓 Специфика GrantService

### Технологический стек:

**Backend:**
- Python 3.10+
- PostgreSQL (localhost:5432/grantservice)
- Qdrant Vector DB (5.35.88.251:6333)

**AI/ML:**
- GigaChat API (Sber LLM)
- InteractiveInterviewerAgentV2 (Reference Points P0-P3)
- FullFlowManager (orchestration)
- SyntheticUserSimulator (testing)

**Interfaces:**
- Telegram Bot (python-telegram-bot)
- Web Admin Panel (Streamlit)

**Data:**
- dialog_history JSONB (PostgreSQL)
- Vector embeddings (Qdrant)
- Interview sessions tracking

### Workflow специфика:

**Разработка агентов:**
1. Isolated testing (как Iteration 40)
2. Mass testing (как Iteration 41)
3. Real dialog testing (как Iteration 42)
4. Full production flow (как Iteration 43)
5. Production deployment

**Тестирование с GigaChat:**
- Учитывать rate limits (1 concurrent stream для физ. лиц)
- Мониторить daily quota (~1M tokens tested successfully)
- Retry logic с exponential backoff

**Database migrations:**
- VARCHAR размеры (1000+ для описаний)
- JSONB для dialog_history
- Indexes для performance

---

## 📁 Структура проекта

```
GrantService/
├── agents/                  # AI Agents (Production Code)
├── data/                    # Database Layer
├── telegram-bot/            # Telegram Bot
├── web-admin/               # Admin Panel
├── shared/                  # Shared Utilities
├── tests/                   # All Tests
├── iterations/              # Development Iterations
├── scripts/                 # Utility Scripts
├── docs/                    # ALL Documentation
├── archive/                 # Archived Files
├── ITERATION_HISTORY.md     # История изменений
├── METHODOLOGY.md           # Этот файл
└── README.md                # Project overview
```

---

## 🔄 Iteration Process для GrantService

### Начало итерации:

1. **Прочитать контекст:**
   - `ITERATION_HISTORY.md` (последние 2-3 итерации)
   - `iterations/Iteration_NN/SESSION_STATE.md` (если есть)
   - Предыдущий `ITERATION_SUMMARY.md`

2. **Создать план:**
   - `iterations/Iteration_NN/00_ITERATION_PLAN.md`
   - Определить цель (1 предложение)
   - Разбить на tasks (<1 день каждая)
   - Критерии успеха

3. **Track progress:**
   - `SESSION_STATE.md` для текущего состояния
   - `PROGRESS_LOG.md` для детального лога
   - Git commits с контекстом

### Во время итерации:

- **Малые коммиты:** 2-5 раз в день
- **Commit messages:** Формат "type: subject - details"
- **Testing:** После каждого изменения
- **Documentation:** Обновлять по ходу, не в конце

### Завершение итерации:

1. **Создать summary:**
   - `iterations/Iteration_NN/ITERATION_NN_SUMMARY.md`
   - Что было → Что сделали → Результат
   - Статистика, learnings, файлы

2. **Обновить историю:**
   - Добавить запись в `ITERATION_HISTORY.md`
   - Формат: 3-5 строк (краткость!)
   - Ссылки на файлы, не дублирование

3. **Git commit:**
   - Зафиксировать все изменения
   - Commit message: "docs: Complete Iteration NN - [summary]"

---

## 📚 Связанные документы

### Основная методология:
- `C:\SnowWhiteAI\cradle\01-Active-Projects\Project-Evolution-Methodology\PROJECT-EVOLUTION-METHODOLOGY.md`
- `C:\SnowWhiteAI\cradle\01-Active-Projects\Project-Evolution-Methodology\README.md`

### Exchange Protocol:
- `C:\SnowWhiteAI\Exchange\EXCHANGE-PROTOCOL.md` - Inter-project communication
- `C:\SnowWhiteAI\Exchange\METHODOLOGY-3-SOURCE-KNOWLEDGE-BASE.md` - Knowledge methodology

### Специфичные для проекта:
- `C:\SnowWhiteAI\Exchange\from-cradle\GrantService_Project\METHODOLOGY.md` - Project-specific guidance
- `ITERATION_HISTORY.md` - История изменений
- `README.md` - Project overview

---

## 🎯 Ключевые принципы

### 1. Малые частые изменения
> "Метаболизм проекта" - постоянный рост малыми шагами

**Практика:**
- Iteration каждые 1-2 дня (не недели!)
- Commits 2-5 раз в день
- Deploy минимум раз в неделю (цель: каждый день)

### 2. Автоматизация стабильности
> "Гомеостаз проекта" - автоматическое поддержание здоровья

**Практика:**
- Automated tests на каждый commit
- CI/CD pipeline (зелёный = деплой)
- Monitoring & alerts

### 3. Управление техническим долгом
> "Регенерация проекта" - постоянное обновление

**Практика:**
- 20% времени на refactoring
- Technical debt backlog
- Regular code review

### 4. Измерение прогресса
> "Метрики здоровья проекта" - DORA metrics

**Практика:**
- Deployment frequency
- Lead time for changes
- MTTR (восстановление)
- Change failure rate

---

## ✨ Следующие шаги

### Iteration 45 (Immediate):
- Выполнить full production flow testing
- Валидировать architecture end-to-end
- Собрать performance baselines

### Short-term (1-2 weeks):
- Setup CI/CD pipeline
- Implement automated testing
- Start DORA metrics tracking

### Medium-term (1-2 months):
- Achieve 80%+ test coverage
- Deploy frequency: >1x/week
- MTTR <1 hour

### Long-term (3-6 months):
- Production deployment (MVP)
- Elite DORA metrics
- Continuous improvement process

---

**Last Updated:** 2025-10-25
**Version:** 1.0.0
**Status:** Active - применяется с Iteration 44

**Для детальной информации:** См. полную методологию в `Project-Evolution-Methodology/`
