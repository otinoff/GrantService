# GrantService Test Suite

**Total Tests:** 87 files
**Created:** 2025-10-22
**Status:** Организация в процессе

---

## 📂 Структура

```
tests/
├── unit/                    # Unit тесты (изолированные)
├── integration/             # Интеграционные (несколько компонентов)
├── autonomous/              # Автономные (без LLM, моки)
├── smoke/                   # Smoke тесты (быстрая проверка)
└── .claude/skills/test-engineer/  # Claude Skill для запуска
```

---

## 🎯 Быстрый старт

### Запуск тестов:

```bash
# Все тесты
pytest tests/

# Только unit
pytest tests/unit/

# Только интервьюер
pytest tests/ -k "interviewer"

# С подробным выводом
pytest tests/ -v
```

### Через Claude Skill:

```
"Run unit tests"
"Test the interviewer"
"Run smoke tests"
```

---

## 📊 Категории тестов (87 файлов)

### 🟢 Autonomous (без LLM) - 6 тестов

**Цель:** Быстрая проверка без затрат на API

- `test_agent_local_autonomous.py` - Локальные агенты
- `test_bot_autonomous.py` - Telegram bot моки
- `test_interviewer_v2_autonomous.py` - Интервьюер V2
- `test_interview_fully_mocked.py` - Полностью замокированное интервью
- `test_agent_router.py` - Роутинг агентов
- `test_fallback_strategy.py` - Fallback стратегии

---

### 🔵 Unit Tests - 8 тестов

**Цель:** Изолированные компоненты

- `telegram-bot/tests/unit/test_interview_agent.py`
- `telegram-bot/tests/unit/test_interview_handler.py`
- `test_fix_isolated.py`
- `database/test_pg18_connection.py`
- `test_database_prompt_manager.py`
- `test_get_questions.py`
- `test_question_display.py`
- `test_interview_hints.py`

---

### 🟡 Integration Tests - 23 теста

**Цель:** Проверка взаимодействия компонентов

#### Interviewer Tests (10):
- `test_interactive_interviewer_v2.py` ⭐ - V2 Reference Points
- `test_interactive_interviewer_automated.py`
- `test_interactive_interviewer_simple.py`
- `test_bot_interactive.py`
- `test_interactive_handler.py`
- `telegram-bot/tests/test_interview_auto.py`
- `test_v2_interview_workflow.py`
- `test_interactive_prod.py`
- `test_prod_telegram_bot.py`
- `test_grant_export_session_9.py`

#### Agent Tests (7):
- `test_agents.py`
- `test_expert_agent.py`
- `test_gigachat_auditor.py`
- `test_writer_claude.py`
- `test_writer_with_expert.py`
- `test_crew.py`
- `test_claude_code_178.py`

#### Research Tests (6):
- `test_researcher_perplexity.py`
- `test_researcher_archery.py`
- `test_researcher_logging.py`
- `test_researcher_mock.py`
- `test_researcher_with_db.py`
- `test_websearch_synthesis.py`

---

### 🟣 Perplexity API Tests - 9 тестов

**Цель:** Тестирование Perplexity integration

- `test_perplexity.py`
- `test_perplexity_direct.py`
- `test_perplexity_simple.py`
- `test_real_perplexity.py`
- `test_minimal_perplexity.py`
- `test_safe_perplexity.py`
- `test_sync_perplexity.py`
- `test_websearch_fix.py`
- `test_websearch_russian.py`

---

### 🔴 Smoke Tests - 3 теста

**Цель:** Быстрая проверка критичных функций

- `test_interactive_interviewer_smoke.py` ⭐
- `test_qdrant_search.py`
- `test_qdrant_remote.py`

---

### 🟠 UI/Web Tests - 6 тестов

**Цель:** Streamlit admin панель

- `test_all_pages.py`
- `test_page_headless.py`
- `test_account_stats.py`
- `test_balance_display.py`
- `test_balance_edit.py`
- `test_model_settings.py`

---

### ⚪ Other/Legacy - 12 тестов

**Цель:** Старые/специфичные тесты

- `test_auto_grant_creation.py`
- `test_prompt_fix.py`
- `test_real_questions.py`
- `run_trainer_test.py`
- Claude Code CLI тесты (3 файла)
- И другие...

---

## 🎯 Приоритетные тесты для CI/CD

### Must Run (всегда):
1. `test_interviewer_v2_autonomous.py` - Быстро, без API
2. `test_interactive_interviewer_smoke.py` - Критичные функции
3. `test_database_prompt_manager.py` - База данных

### Should Run (pre-deploy):
4. `test_interactive_interviewer_v2.py` - Полное интервью
5. `test_agents.py` - Все агенты
6. `test_qdrant_search.py` - Векторный поиск

### Nice to Have (weekly):
7. All integration tests
8. Perplexity tests
9. UI tests

---

## 🚀 Использование test-engineer Skill

**Skill location:** `tests/.claude/skills/test-engineer/`

### Команды:

```
"Run autonomous tests"     → pytest tests/autonomous/
"Test interviewer"         → pytest -k "interviewer"
"Smoke test"               → pytest tests/smoke/
"All tests verbose"        → pytest tests/ -v
```

**Skill экономит:** ~60% токенов vs прямые запросы

---

## 📝 TODO: Migration Plan

**Сейчас:** 87 тестов разбросаны по проекту
**Цель:** Организовать в tests/ по категориям

### Phase 1 (приоритет):
- [ ] Переместить autonomous тесты → tests/autonomous/
- [ ] Переместить smoke тесты → tests/smoke/
- [ ] Создать conftest.py с общими fixtures

### Phase 2:
- [ ] Переместить unit тесты → tests/unit/
- [ ] Переместить integration → tests/integration/

### Phase 3:
- [ ] Добавить CI/CD pipeline
- [ ] Coverage reporting
- [ ] Automated test runs

---

## 🔗 Links

- **Test Engineer Skill:** `.claude/skills/test-engineer/SKILL.md`
- **Autonomous Testing Methodology:** `C:\SnowWhiteAI\GrantService_Project\Development\00_Technical_Docs\AUTONOMOUS_TESTING_METHODOLOGY.md`
- **cradle test-engineer:** `C:\SnowWhiteAI\cradle\.claude\skills\test-engineer\`

---

**Created:** 2025-10-22
**Total Tests:** 87 files
**Organized:** 0% (migration pending)
**Priority:** После рефакторинга интервьюера
