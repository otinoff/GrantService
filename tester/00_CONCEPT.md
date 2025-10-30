# Test Engineer Agent - Концепция

**Создано:** 2025-10-30
**Автор:** AI-ассистент + Наталья (GrantService)
**Статус:** Концепция → Готов к реализации

---

## 🎯 Главная Идея

**Test Engineer Agent** - это автономный AI-агент на базе GigaChat, который:

1. **Знает кодовую базу** через RAG-поиск по `C:\SnowWhiteAI\GrantService\knowhow/`
2. **Тестирует E2E** используя модульные тесты из `tests/e2e/modules/`
3. **Симулирует пользователя** Telegram-бота БЕЗ реального Telegram
4. **Поддерживает 5 агентов** в рабочем состоянии (Interviewer, Auditor, Researcher, Writer, Reviewer)
5. **Учится на ошибках** через систему памяти и reinforcement learning

---

## 🧠 Почему именно GigaChat?

### Преимущества для GrantService:

1. **Русский язык** - понимает контекст НКО, грантовые термины, методические рекомендации
2. **Локальность** - работает без зависимости от зарубежных API
3. **Интеграция** - 4 из 5 production агентов уже на GigaChat
4. **Скорость** - 2x быстрее западных аналогов
5. **Экосистема** - поддержка российского AI ecosystem

### Технические требования:

- **Модель:** GigaChat-Max (та же что у production агентов)
- **Температура:** 0.1-0.3 для детерминированности тестов
- **Контекст:** 32K tokens (достаточно для анализа кода + тестов)
- **RAG:** Embeddings через GigaChat Embeddings API

---

## 🏗️ Архитектура

### Компоненты:

```
Test Engineer Agent (GigaChat-Max)
├── Knowledge Base (RAG)
│   ├── knowhow/*.md (E2E_TESTING_GUIDE, ITERATION_LEARNINGS, etc)
│   ├── tests/e2e/modules/*.py (source code тестов)
│   └── agents/*.py (production agent code)
│
├── User Simulator
│   ├── Quality Level Selection (beginner/expert)
│   ├── Response Generator (realistic user answers)
│   └── Context Manager (диалоговая память)
│
├── E2E Test Runner
│   ├── Workflow Executor (5 steps: Interview → Audit → Research → Write → Review)
│   ├── Validation Engine (checks на каждом шаге)
│   └── Artifact Manager (saves results to iterations/)
│
├── Memory System
│   ├── Short-term: текущий тест run
│   ├── Long-term: история багов, fixes, patterns
│   ├── Working: активный контекст (код + тесты)
│   └── Meta-memory: "что я знаю о системе"
│
└── Reinforcement Learning
    ├── Reward Function (+/- за успешные/неуспешные тесты)
    ├── Policy: какие тесты запускать
    └── Improvement Loop: обновление knowledge base
```

---

## 📊 Customer Journey Map - Test Engineer Agent

### Сценарий: Проверка production готовности перед деплоем

**Актор:** Test Engineer Agent
**Цель:** Убедиться что все 5 агентов работают корректно

#### Шаг 1: Получение задачи
- **Триггер:** Pre-deploy checklist запускается через CI/CD
- **Действие:** Agent получает команду "run full E2E test"
- **Инструмент:** GigaChat анализирует git diff для определения scope тестов

#### Шаг 2: Анализ изменений
- **Действие:** RAG-поиск по knowhow/ для понимания контекста
- **Запрос:** "Какие модули затронуты коммитом a2a194e?"
- **Результат:** Определяет что изменены writer_module.py (FIX #15) и researcher_module.py (FIX #13)

#### Шаг 3: Генерация тестовых данных
- **User Simulation:** Создает realistic анкету соискателя гранта
  - Качество: "средний уровень" (не слишком просто, не слишком идеально)
  - Контекст: НКО, образование, молодежная политика
  - Детальность: 4-5 предложений на вопрос
- **Инструмент:** GigaChat генерирует ответы на 10 вопросов интервью

#### Шаг 4: Запуск E2E pipeline
- **STEP 1 - Interview:**
  - Вызов `InterviewerModule.run_interview(user_simulator_answers)`
  - Validation: 10 questions, 4000+ chars
  - Result: anketa_id = 999999XXX

- **STEP 2 - Audit:**
  - Вызов `AuditorModule.run_audit(anketa_id)`
  - Validation: score >= 5.0/10
  - Result: audit_id, session_id

- **STEP 3 - Research:**
  - Вызов `ResearcherModule.run_research(anketa_id)`
  - Validation: >= 2 sources
  - Result: research_id, 5-10 sources

- **STEP 4 - Writer (FIX #15):**
  - Вызов `WriterModule.run_writer(anketa_id, research_id)`
  - Validation: grant_length >= 15000 chars ← проверяет FIX #15!
  - Result: grant_id, full_text

- **STEP 5 - Review:**
  - Вызов `ReviewerModule.run_review(grant_id)`
  - Validation: review_score >= 6.0/10
  - Result: review complete

#### Шаг 5: Анализ результатов
- **Действие:** GigaChat анализирует логи, артефакты, ERROR.txt (если есть)
- **Проверка:**
  - Все ли validation passed?
  - Какие warnings?
  - Качество grant_text адекватно?

#### Шаг 6: Обновление Knowledge Base
- **Успех:**
  - Записывает в `knowhow/ITERATION_LEARNINGS.md`: "FIX #15 verified ✅"
  - Обновляет meta-memory: "writer_module.py extract full_text works"

- **Ошибка:**
  - Создает `iterations/Iteration_XX/BUG_REPORT.md`
  - Записывает в long-term memory: "FIX #15 failed with error: ..."
  - Negative reward → policy adjustment

#### Шаг 7: Отчет
- **Формат:** Markdown report в `iterations/Iteration_XX/TEST_REPORT.md`
- **Содержание:**
  - Test ID, timestamp
  - All 5 steps: status, duration, key metrics
  - Artifacts: anketa.txt, grant.txt, research.json
  - Recommendation: "Ready for deploy ✅" или "Fix required ⚠️"

---

## 🎓 Обучение на опыте

### Пример: FIX #15 Discovery

**До Test Engineer Agent:**
- Bug найден вручную через failed E2E test
- FIX #15 закоммичен локально → untracked
- SESSION_SUMMARY написал "deployed" ← но НЕ проверил git status
- Потребовалось 45 минут новой сессии чтобы найти что файл untracked

**С Test Engineer Agent:**
1. **Pre-commit hook:**
   - Agent проверяет `git status` перед записью "deployed"
   - Видит untracked files → warning
   - Refuse to mark as deployed до commit

2. **Post-commit validation:**
   - Agent запускает E2E test после commit
   - Verifies FIX #15 работает на production
   - Если fail → rollback или hotfix

3. **Knowledge update:**
   - Записывает в meta-memory: "Always check git status before 'deployed'"
   - Обновляет policy: pre-commit validation обязательно

---

## 💰 ROI Analysis

### Метрики до внедрения:

**Текущие затраты на тестирование:**
- Manual E2E testing: 2 часа/неделя (8 часов/месяц)
- Bug discovery latency: 1-3 дня после deploy
- Cost per bug: ~4 часа разработки + 2 часа тестирования
- Среднее количество bugs: 2-3/месяц

**Total cost:** ~20 часов/месяц = 30,000₽/месяц (при ставке 1,500₽/час)

### Метрики после внедрения:

**Автоматизация:**
- E2E test run: 15 минут (vs 2 часа manual)
- Bug discovery: immediate (в CI/CD pipeline)
- Cost per test run: ~200₽ (GigaChat tokens)
- Тестов в месяц: 20 runs (каждый deploy + nightly)

**Total cost:** 4,000₽/месяц (tokens) + 4 часа/месяц (maintenance) = 10,000₽/месяц

**Savings:** 30,000 - 10,000 = **20,000₽/месяц** (67% снижение)

### Качественные улучшения:

1. **Скорость:** 8x faster (15 min vs 2 hours)
2. **Покрытие:** 100% E2E scenarios (vs 70% manual)
3. **Консистентность:** детерминированные тесты (нет human error)
4. **Документация:** автоматические TEST_REPORT.md после каждого run

---

## 🚀 Фазы Реализации

### Phase 1: Knowledge Base (1 неделя)
**Цель:** RAG-поиск по knowhow/ работает

**Deliverables:**
- Embeddings для knowhow/*.md (GigaChat Embeddings API)
- Vector DB (Qdrant, уже используется в production)
- RAG retriever module

**Success Metric:** Agent может ответить "Что такое FIX #15?" → правильный ответ

### Phase 2: User Simulator (1 неделя)
**Цель:** Генерация realistic user answers

**Deliverables:**
- GigaChat prompt для генерации анкет
- Quality level selector (beginner/intermediate/expert)
- Context manager для диалога

**Success Metric:** Generated anketa passes AuditorAgent validation (score >= 5.0)

### Phase 3: E2E Test Runner (2 недели)
**Цель:** Полный pipeline работает автономно

**Deliverables:**
- Integration с tests/e2e/modules/
- Workflow executor (5 steps)
- Validation engine на каждом шаге
- Artifact manager

**Success Metric:** Full E2E test run успешно завершается, создает artifacts

### Phase 4: Memory & RL (2 недели)
**Цель:** Self-learning система работает

**Deliverables:**
- Short-term/long-term memory storage
- Reward function
- Policy для выбора тестов
- Knowledge base update loop

**Success Metric:** Agent learns from failures, improves over time

### Phase 5: CI/CD Integration (1 неделя)
**Цель:** Pre-deploy hook работает

**Deliverables:**
- GitHub Actions integration
- Pre-commit hook
- Auto-report generation

**Success Metric:** Deploy blocked если E2E test fails

**Total:** 7 недель (1.75 месяца)

---

## 📈 Success Metrics

### Технические:

1. **Test Success Rate:** >= 95% (false positives < 5%)
2. **Test Duration:** <= 20 minutes per full E2E run
3. **Coverage:** 100% of 5-agent pipeline
4. **Reliability:** >= 99% uptime

### Бизнес:

1. **Cost Reduction:** >= 50% (vs manual testing)
2. **Bug Detection Speed:** <= 30 minutes (vs 1-3 days)
3. **Deploy Confidence:** >= 90% (subjective developer survey)
4. **Documentation Quality:** 100% tests documented automatically

---

## 🔗 Integration с Production

### Существующая инфраструктура:

**Production Server:** 5.35.88.251
**Database:** PostgreSQL (localhost:5432)
**Vector DB:** Qdrant (localhost:6333)
**Telegram Bot:** main.py (systemd service)

### Test Engineer Agent deployment:

```
/var/GrantService/
├── agents/                 # Production agents
├── tests/e2e/             # E2E test modules
├── tester/                # ← Test Engineer Agent (NEW)
│   ├── agent.py           # Main agent code
│   ├── knowledge_base.py  # RAG retriever
│   ├── user_simulator.py  # User simulation
│   ├── workflow.py        # E2E runner
│   └── memory.py          # Memory system
└── knowhow/               # Knowledge base (existing)
```

**Запуск:**
```bash
# Manual run:
python tester/agent.py --mode full

# CI/CD (GitHub Actions):
python tester/agent.py --mode pre-deploy --commit $COMMIT_SHA
```

---

## 🎯 Roadmap

**Q4 2025:**
- ✅ Концепция утверждена
- ⏳ Phase 1: Knowledge Base (Nov 2025)
- ⏳ Phase 2: User Simulator (Nov 2025)
- ⏳ Phase 3: E2E Runner (Dec 2025)

**Q1 2026:**
- ⏳ Phase 4: Memory & RL (Jan 2026)
- ⏳ Phase 5: CI/CD Integration (Feb 2026)
- ⏳ Production deployment (Mar 2026)

---

## 📚 Связанные документы

**В этой папке:**
- `01_METHODOLOGY_ADAPTATION.md` - Адаптация Cradle методологий
- `02_IMPLEMENTATION_PLAN.md` - Детальный план реализации
- `03_ARCHITECTURE.md` - Техническая архитектура

**Cradle Know-How:**
- `C:\SnowWhiteAI\cradle\Know-How\TESTING-METHODOLOGY.md`
- `C:\SnowWhiteAI\cradle\Know-How\SELF_LEARNING_SYSTEM_DESIGN.md`

**GrantService:**
- `C:\SnowWhiteAI\GrantService\knowhow\E2E_TESTING_GUIDE.md`
- `C:\SnowWhiteAI\GrantService\iterations\Iteration_66_E2E_Test_Suite\`

---

**Last Updated:** 2025-10-30
**Status:** ✅ Concept Complete, Ready for Phase 1
**Next:** Read 01_METHODOLOGY_ADAPTATION.md
