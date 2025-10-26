# Iteration 1002: E2E Tests Complete (FUTURE PLAN)

**Status:** 📅 PLANNED (not started)
**Priority:** 🔥 HIGH (ваш приоритет)
**Prerequisites:** None (может выполняться независимо)
**Estimated Time:** 6-8 hours
**Assigned To:** TBD

---

## 🎯 Goal

Завершить end-to-end тестирование полного флоу GrantService: **Anketa → Research → Writer → Reviewer → Database → Telegram Bot**.

**Текущая ситуация:**
- ⚠️ E2E тесты начаты, но не завершены
- ⚠️ Есть Iteration 50 с частичными E2E тестами
- ⚠️ Нужно доделать интеграционное тестирование

**Целевое состояние:**
- ✅ Полный E2E тест от начала до конца
- ✅ Все компоненты протестированы вместе
- ✅ Автоматизированные тесты запускаются через pytest
- ✅ CI/CD готово (опционально)

---

## 📊 Scope

### In Scope ✅
1. **E2E Test: Full Grant Application Flow**
   - User starts anketa in Telegram bot
   - InterviewerAgent collects answers
   - ResearchAgent finds grant info
   - WriterAgent generates application
   - ReviewerAgent scores quality
   - Application saved to database
   - User receives notification

2. **Integration Tests:**
   - Telegram Bot ↔ PostgreSQL
   - Agents ↔ LLM APIs (GigaChat/Claude)
   - Agents ↔ Database
   - Vector DB (Qdrant) ↔ WriterAgent

3. **Mock Services:**
   - Mock Telegram API (test without real bot)
   - Mock LLM APIs (fast tests)
   - Test database (isolated from production)

4. **Test Coverage:**
   - Happy path (successful application)
   - Error paths (API failures, validation errors)
   - Edge cases (empty inputs, long texts)

### Out of Scope ❌
- Unit tests для отдельных агентов (уже есть)
- Load testing / Performance tests
- Security testing (penetration tests)
- UI/UX testing

---

## 📋 Tasks Breakdown

### Phase 1: Audit Existing E2E Tests (1 hour)
**Goal:** Понять, что уже есть, что нужно доделать

**Tasks:**
- [ ] Прочитать Iteration 50 план и код
- [ ] Найти существующие E2E тесты: `grep -r "test.*e2e" tests/`
- [ ] Запустить существующие тесты: `pytest tests/ -k e2e`
- [ ] Определить gaps (что не протестировано)
- [ ] Создать чеклист недостающих тестов

**Acceptance Criteria:**
- ✅ Список существующих E2E тестов
- ✅ Список недостающих тестов
- ✅ Приоритизация (что важнее доделать)

---

### Phase 2: Setup Test Infrastructure (1 hour)
**Goal:** Подготовить окружение для E2E тестов

**Tasks:**
- [ ] Создать test database: `grantservice_test`
- [ ] Настроить pytest fixtures для E2E:
  ```python
  @pytest.fixture
  async def test_db():
      # Create test database
      # Run migrations
      # Yield connection
      # Cleanup after test

  @pytest.fixture
  async def test_telegram_bot():
      # Mock Telegram bot API
      # Return bot instance

  @pytest.fixture
  async def test_agents():
      # Initialize all agents with test DB
      # Return agents dict
  ```

- [ ] Настроить mock для Telegram API (pytest-telegram)
- [ ] Настроить mock для LLM APIs (pytest-mock)
- [ ] Создать test data fixtures (sample projects)

**Acceptance Criteria:**
- ✅ Test database создается/удаляется автоматически
- ✅ Fixtures работают
- ✅ Mocks настроены

---

### Phase 3: Test #1 - Full Happy Path (2 hours)
**Goal:** Протестировать успешный флоу от начала до конца

**Test Scenario:**
```python
# tests/e2e/test_full_grant_application_flow.py

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_full_grant_application_flow_success(
    test_db,
    test_telegram_bot,
    test_agents
):
    """
    E2E Test: User completes full grant application flow

    Flow:
    1. User /start in Telegram bot
    2. InterviewerAgent asks questions via anketa
    3. User answers all questions
    4. ResearchAgent searches for grants
    5. User selects grant
    6. WriterAgent generates application
    7. ReviewerAgent scores application (7+)
    8. Application saved to database
    9. User receives PDF download link
    """

    # Step 1: User starts conversation
    user_id = 123456
    await test_telegram_bot.send_message(user_id, "/start")

    # Verify: Bot responds with welcome message
    response = await test_telegram_bot.get_last_message(user_id)
    assert "Привет" in response.text
    assert "анкета" in response.text.lower()

    # Step 2: User starts anketa
    await test_telegram_bot.send_message(user_id, "Начать анкету")

    # Step 3: InterviewerAgent asks questions
    interviewer = test_agents["interviewer"]

    # Answer question 1: Project name
    question_1 = await test_telegram_bot.get_last_message(user_id)
    assert "название проекта" in question_1.text.lower()
    await test_telegram_bot.send_message(user_id, "Школа молодых предпринимателей")

    # Answer question 2: Description
    question_2 = await test_telegram_bot.get_last_message(user_id)
    await test_telegram_bot.send_message(user_id, "Образовательная программа для молодежи")

    # ... (answer all 10 questions)

    # Step 4: ResearchAgent searches for grants
    research_agent = test_agents["research"]
    grants = await research_agent.search_grants_async(
        user_answers={
            "project_name": "Школа молодых предпринимателей",
            "description": "Образовательная программа...",
            # ... other answers
        }
    )

    # Verify: Found at least 3 grants
    assert len(grants) >= 3

    # Step 5: User selects grant
    selected_grant = grants[0]
    await test_telegram_bot.send_message(user_id, f"Выбрать грант {selected_grant['id']}")

    # Step 6: WriterAgent generates application
    writer_agent = test_agents["writer"]
    result = await writer_agent.write_application_async({
        "user_answers": {...},
        "research_data": {...},
        "selected_grant": selected_grant
    })

    # Verify: Application generated successfully
    assert result["status"] == "success"
    assert "problem" in result["application_content"]
    assert len(result["application_content"]["problem"]) > 500

    # Step 7: ReviewerAgent scores application
    reviewer_agent = test_agents["reviewer"]
    review = await reviewer_agent.review_application_async(
        result["application_content"]
    )

    # Verify: Quality score is 7+
    assert review["score"] >= 7.0

    # Step 8: Application saved to database
    from data.database.grant_service_db import GrantServiceDatabase
    db = GrantServiceDatabase()

    saved = await db.save_grant_application(
        user_id=user_id,
        content=result["application_content"],
        review_score=review["score"],
        status="approved"
    )

    # Verify: Saved successfully
    assert saved["id"] > 0

    # Step 9: User receives notification
    notification = await test_telegram_bot.get_last_message(user_id)
    assert "заявка готова" in notification.text.lower()
    assert "скачать" in notification.text.lower()

    # Verify: PDF link present
    assert notification.reply_markup is not None
    assert "download_pdf" in str(notification.reply_markup)

    print(f"✅ E2E Test PASSED: Full grant application flow completed")
```

**Acceptance Criteria:**
- ✅ Test проходит от начала до конца
- ✅ Все шаги выполняются успешно
- ✅ Данные сохраняются в БД
- ✅ Пользователь получает результат

---

### Phase 4: Test #2 - Error Handling (1 hour)
**Goal:** Протестировать обработку ошибок

**Test Scenarios:**
```python
@pytest.mark.asyncio
@pytest.mark.e2e
async def test_llm_api_failure_handling():
    """Test: LLM API unavailable"""
    # Mock LLM API to return 500 error
    # Verify: System handles gracefully
    # Verify: User receives error message
    pass

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_database_connection_failure():
    """Test: Database unavailable"""
    # Mock database connection to fail
    # Verify: System handles gracefully
    # Verify: User receives error message
    pass

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_empty_user_input():
    """Test: User provides empty answers"""
    # Send empty strings for all questions
    # Verify: Validation errors caught
    # Verify: User prompted to provide valid input
    pass

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_research_agent_no_grants_found():
    """Test: ResearchAgent finds no matching grants"""
    # Mock search to return empty results
    # Verify: User informed about no grants
    # Verify: Suggestions provided
    pass
```

**Acceptance Criteria:**
- ✅ All error scenarios tested
- ✅ System doesn't crash
- ✅ User receives helpful error messages

---

### Phase 5: Test #3 - WriterAgent with RAG (30 min)
**Goal:** Протестировать WriterAgent с RAG enhancement

**Test Scenario:**
```python
@pytest.mark.asyncio
@pytest.mark.e2e
async def test_writer_agent_with_rag_enhancement():
    """Test: WriterAgent uses RAG to improve quality"""

    # Setup: Load Qdrant collections
    # (assumes Iteration 51 complete)

    # Generate application WITH RAG
    result_with_rag = await writer_agent.write_application_async(...)

    # Verify: RAG retrieval happened (check logs)
    assert "[RAG]" in captured_logs

    # Verify: Application quality improved
    review = await reviewer_agent.review_application_async(
        result_with_rag["application_content"]
    )
    assert review["score"] >= 7.5
```

**Acceptance Criteria:**
- ✅ RAG retrieval works in E2E test
- ✅ Quality improvement verified

---

### Phase 6: Test #4 - Telegram Bot Integration (1 hour)
**Goal:** Протестировать интеграцию с Telegram Bot

**Test Scenarios:**
```python
@pytest.mark.asyncio
@pytest.mark.e2e
async def test_telegram_bot_commands():
    """Test: All bot commands work"""
    # Test /start
    # Test /help
    # Test /anketa
    # Test /status
    # Test /download
    pass

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_telegram_bot_buttons():
    """Test: Inline keyboards work"""
    # Test grant selection buttons
    # Test confirmation buttons
    # Test download button
    pass

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_telegram_bot_file_upload():
    """Test: User can upload documents"""
    # Upload PDF (project description)
    # Verify: File saved
    # Verify: Content extracted
    pass
```

**Acceptance Criteria:**
- ✅ All bot commands tested
- ✅ Buttons work correctly
- ✅ File upload works

---

### Phase 7: Test Coverage Report (30 min)
**Goal:** Измерить покрытие тестами

**Tasks:**
- [ ] Run pytest with coverage: `pytest --cov=. --cov-report=html`
- [ ] Analyze coverage report
- [ ] Identify uncovered code
- [ ] Add tests for critical uncovered paths

**Target Coverage:**
- E2E tests: 80%+ of main flow
- Integration tests: 70%+ of API calls
- Overall: 60%+ (combined with unit tests)

**Acceptance Criteria:**
- ✅ Coverage report generated
- ✅ Critical paths covered
- ✅ Report committed to repo

---

### Phase 8: CI/CD Integration (Optional, 1 hour)
**Goal:** Автоматизировать запуск тестов

**Tasks:**
- [ ] Create GitHub Actions workflow: `.github/workflows/e2e-tests.yml`
- [ ] Run E2E tests on every PR
- [ ] Run E2E tests on main branch push
- [ ] Notify on Telegram if tests fail

**Workflow Example:**
```yaml
name: E2E Tests

on:
  pull_request:
  push:
    branches: [master]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: root
        ports:
          - 5432:5432

      qdrant:
        image: qdrant/qdrant
        ports:
          - 6333:6333

    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run E2E tests
        run: pytest tests/e2e/ -v --maxfail=1

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

**Acceptance Criteria:**
- ✅ CI/CD workflow created
- ✅ Tests run automatically
- ✅ Notifications work

---

### Phase 9: Documentation (30 min)
**Goal:** Документировать E2E тесты

**Documents:**
- [ ] `E2E_TESTS_GUIDE.md` - how to run tests
- [ ] `E2E_COVERAGE_REPORT.md` - coverage metrics
- [ ] Update `README.md` with testing section
- [ ] Iteration 1002 Summary

**Acceptance Criteria:**
- ✅ Documentation complete
- ✅ Easy for new developers to run tests
- ✅ Coverage metrics documented

---

## 📊 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **E2E Coverage** | 80%+ | pytest --cov |
| **Test Execution Time** | <5 min | pytest --durations=10 |
| **Tests Passing** | 100% | pytest exit code |
| **Critical Bugs Found** | Document all | Manual tracking |
| **CI/CD Setup** | Working | GitHub Actions badge |

---

## 🚀 Deployment Plan

### Prerequisites
- ✅ Python 3.12+
- ✅ PostgreSQL 14+
- ✅ Docker (for Qdrant)
- ✅ pytest + pytest-asyncio installed

### Steps
1. Create test database
2. Install test dependencies: `pip install -r requirements-test.txt`
3. Run E2E tests: `pytest tests/e2e/ -v`
4. Review coverage report: `open htmlcov/index.html`
5. Fix failing tests
6. Setup CI/CD (optional)

---

## 🐛 Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tests too slow | MEDIUM | Use mocks, parallel execution |
| Flaky tests | HIGH | Improve assertions, add retries |
| API rate limits | LOW | Use test API keys, mocks |
| Database conflicts | MEDIUM | Isolated test database |

---

## 📝 Notes

- **Why E2E tests важны?** Они проверяют всю систему целиком, ловят интеграционные баги
- **Why not unit tests?** Unit tests уже есть, E2E дополняют их
- **Why mock LLM?** Чтобы тесты были быстрыми и не зависели от API availability
- **Why CI/CD optional?** Можно делать локально, CI/CD - nice to have

---

## 🔗 Related Iterations

- **Iteration 50:** E2E Full Flow Test (частично) ⚠️ INCOMPLETE
- **Iteration 49:** ReviewerAgent testing ✅ COMPLETE
- **Iteration 51:** AI Enhancement ✅ COMPLETE
- **Iteration 1001:** RAG Full Integration (future)

---

## ✅ Definition of Done

- [ ] Full happy path E2E test written and passing
- [ ] Error handling tests written and passing
- [ ] WriterAgent RAG integration tested
- [ ] Telegram bot integration tested
- [ ] Test coverage report generated (80%+ E2E)
- [ ] Documentation complete
- [ ] CI/CD setup (optional but recommended)
- [ ] Code reviewed
- [ ] Git committed

---

**When to Start:** ASAP (высокий приоритет)

**Owner:** TBD
**Status:** 📅 PLANNED

**Estimated Completion:** После завершения → переименовать в `Iteration_053_E2E_Tests_Complete`
