# Phase 1: Integration Tests with Real Agents

**Duration:** 3 days
**Priority:** 🔴 CRITICAL - Start here!
**Status:** Ready to Execute

---

## 🎯 Goal

**Create integration tests that validate the pipeline works with REAL agents and REAL database.**

**Why this phase is FIRST:**
- If integration tests fail → architecture problem
- Integration tests use production code paths
- Integration tests catch 80% of real bugs
- Manual testing comes AFTER these pass

---

## 📋 What We're Testing

### The Pipeline Flow
```
User completes anketa
    ↓
1. AuditorAgent.audit_application_async(anketa_data)
    ↓ saves audit_result to DB
2. ProductionWriter.write(anketa_data)
    ↓ saves grant to DB
3. ReviewerAgent.review_grant_async(grant_data)
    ↓ saves review to DB
4. Complete!
```

### What We're Validating
- ✅ Agents accept correct input format
- ✅ Agents return correct output format
- ✅ Data saves to database correctly
- ✅ Data retrieves from database correctly
- ✅ No import errors (production imports work)
- ✅ No AttributeErrors (all methods exist)

---

## 🛠️ Setup

### Step 1: Install Dependencies

```bash
# Create requirements-test.txt if not exists
cat > requirements-test.txt << 'EOF'
# Testing framework
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Test database
pytest-testcontainers>=0.1.0
testcontainers[postgresql]>=3.7.0

# Mocking
pytest-mock>=3.11.0

# Configuration
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
EOF

# Install
pip install -r requirements-test.txt
```

### Step 2: Create Test Database

**Option A: Testcontainers (Recommended)**
```python
# Will auto-create PostgreSQL in Docker
# No manual setup needed!
```

**Option B: Manual Test Database**
```bash
# Create database
createdb grantservice_test

# Apply schema
PGPASSWORD=root psql -h localhost -U postgres -d grantservice_test \
  -f data/database/schema.sql

# Verify
PGPASSWORD=root psql -h localhost -U postgres -d grantservice_test -c "\dt"
```

### Step 3: Configure Test Environment

```bash
# Create .env.test
cat > .env.test << 'EOF'
# Test Database
DATABASE_URL=postgresql://postgres:root@localhost:5432/grantservice_test

# Test API Keys (use mock or test keys)
GIGACHAT_API_KEY=test_key_mock_for_integration_tests
TELEGRAM_BOT_TOKEN=test_token_mock

# Test mode
ENVIRONMENT=test
LOG_LEVEL=DEBUG
EOF
```

---

## 📝 Test Structure

### Directory Layout
```
tests/
├── __init__.py
├── conftest.py                          # Root fixtures
└── integration/
    ├── __init__.py
    ├── conftest.py                      # Integration fixtures
    ├── test_pipeline_real_agents.py     # ← CREATE THIS (Phase 1)
    └── test_pipeline_edge_cases.py      # (Phase 2)
```

---

## 🧪 Test 1: Auditor Agent Integration

### File: `tests/integration/test_pipeline_real_agents.py`

```python
"""
Integration tests for pipeline with REAL agents.

Tests use:
- REAL agent classes (production imports)
- REAL PostgreSQL database (Testcontainers OR test DB)
- MOCKED LLM calls (GigaChat) with realistic responses
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Production imports (same as production!)
from agents.auditor_agent import AuditorAgent
from agents.production_writer import ProductionWriter
from agents.reviewer_agent import ReviewerAgent


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auditor_agent_integration(test_db, test_anketa, gigachat_mock):
    """
    Test AuditorAgent with real database.

    Flow:
    1. Create AuditorAgent with real DB
    2. Call audit_application_async() with test anketa
    3. Verify audit result returned
    4. Verify audit saved to database
    """

    # Arrange: Create real agent with test DB
    auditor = AuditorAgent(db=test_db)

    # Mock GigaChat response with realistic audit data
    gigachat_mock.return_value = {
        'score': 8.5,
        'strengths': [
            'Четкая цель проекта',
            'Обоснованный бюджет',
            'Опыт команды'
        ],
        'weaknesses': [
            'Недостаточно метрик результата'
        ],
        'recommendations': [
            'Добавить конкретные KPI'
        ]
    }

    # Act: Run audit with REAL agent
    result = await auditor.audit_application_async(
        input_data={
            'anketa_id': test_anketa['id'],
            'anketa_data': test_anketa
        }
    )

    # Assert: Verify result structure
    assert result is not None
    assert 'status' in result
    assert result['status'] == 'success'
    assert 'audit_details' in result

    # Assert: Verify audit details
    audit = result['audit_details']
    assert 'score' in audit
    assert isinstance(audit['score'], (int, float))
    assert 0 <= audit['score'] <= 10
    assert 'strengths' in audit
    assert isinstance(audit['strengths'], list)
    assert len(audit['strengths']) > 0

    # Assert: Verify data saved to database
    saved_audit = test_db.get_audit_by_anketa_id(test_anketa['id'])
    assert saved_audit is not None
    assert saved_audit['score'] == audit['score']

    print(f"✅ Auditor integration test passed! Score: {audit['score']}")
```

---

## 🧪 Test 2: Production Writer Integration

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_writer_agent_integration(test_db, test_anketa, test_audit_result, gigachat_mock):
    """
    Test ProductionWriter with real database.

    Flow:
    1. Create ProductionWriter with real DB
    2. Call write() with anketa data
    3. Verify grant generated
    4. Verify grant saved to database
    """

    # Arrange: Create real agent with test DB
    writer = ProductionWriter(db=test_db)

    # Mock GigaChat to return realistic grant content
    gigachat_mock.return_value = """
# Грантовая заявка: Тестовый проект

## 1. Актуальность

Проект направлен на решение проблемы...

## 2. Цель и задачи

**Цель:** Достижение конкретного результата...

**Задачи:**
1. Задача 1
2. Задача 2

## 3. Методология

Для достижения цели будет использована методология...

## 4. Бюджет

**Общий бюджет:** 1 000 000 рублей

**Статьи расходов:**
- Оборудование: 500 000 руб
- Персонал: 400 000 руб
- Прочее: 100 000 руб

## 5. Ожидаемые результаты

Ожидается достижение следующих результатов...
"""

    # Act: Generate grant with REAL agent
    result = writer.write(anketa_data=test_anketa)

    # Assert: Verify result structure
    assert result is not None
    assert 'grant_id' in result or 'content' in result

    # Get grant content
    if 'content' in result:
        grant_content = result['content']
    else:
        grant_id = result['grant_id']
        grant_content = test_db.get_grant_content(grant_id)

    # Assert: Verify grant quality
    assert grant_content is not None
    assert len(grant_content) > 10000  # Minimum 10K chars
    assert 'Актуальность' in grant_content
    assert 'Бюджет' in grant_content
    assert 'Методология' in grant_content

    # Assert: Verify saved to database
    saved_grant = test_db.get_grant_by_anketa_id(test_anketa['id'])
    assert saved_grant is not None
    assert saved_grant['content'] == grant_content

    print(f"✅ Writer integration test passed! Grant length: {len(grant_content)} chars")
```

---

## 🧪 Test 3: Reviewer Agent Integration

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_reviewer_agent_integration(test_db, test_grant, gigachat_mock):
    """
    Test ReviewerAgent with real database.

    Flow:
    1. Create ReviewerAgent with real DB
    2. Call review_grant_async() with grant data
    3. Verify review generated
    4. Verify review saved to database
    """

    # Arrange: Create real agent with test DB
    reviewer = ReviewerAgent(db=test_db)

    # Mock GigaChat to return realistic review
    gigachat_mock.return_value = {
        'overall_score': 8.0,
        'sections': {
            'актуальность': {'score': 9, 'comment': 'Отлично обоснована'},
            'цель': {'score': 8, 'comment': 'Четко сформулирована'},
            'методология': {'score': 7, 'comment': 'Можно усилить'},
            'бюджет': {'score': 8, 'comment': 'Обоснован'}
        },
        'strengths': [
            'Хорошая структура',
            'Четкие задачи'
        ],
        'improvements': [
            'Добавить больше метрик'
        ],
        'recommendation': 'approve'
    }

    # Act: Review grant with REAL agent
    result = await reviewer.review_grant_async(
        input_data={
            'grant_id': test_grant['id'],
            'grant_content': test_grant['content']
        }
    )

    # Assert: Verify result structure
    assert result is not None
    assert 'status' in result
    assert result['status'] == 'success'
    assert 'review_details' in result

    # Assert: Verify review details
    review = result['review_details']
    assert 'overall_score' in review
    assert isinstance(review['overall_score'], (int, float))
    assert 0 <= review['overall_score'] <= 10
    assert 'recommendation' in review
    assert review['recommendation'] in ['approve', 'revise', 'reject']

    # Assert: Verify saved to database
    saved_review = test_db.get_review_by_grant_id(test_grant['id'])
    assert saved_review is not None
    assert saved_review['overall_score'] == review['overall_score']

    print(f"✅ Reviewer integration test passed! Score: {review['overall_score']}")
```

---

## 🧪 Test 4: Full Pipeline Integration

```python
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_full_pipeline_integration(test_db, test_anketa, gigachat_mock):
    """
    Test complete pipeline: Anketa → Audit → Grant → Review

    This is the most important test - validates end-to-end flow.
    """

    print("\n" + "="*60)
    print("FULL PIPELINE INTEGRATION TEST")
    print("="*60)

    # Setup mocks for all stages
    setup_full_pipeline_mocks(gigachat_mock)

    # Stage 1: Audit
    print("\n[1/3] Running Auditor...")
    auditor = AuditorAgent(db=test_db)
    audit_result = await auditor.audit_application_async({
        'anketa_id': test_anketa['id'],
        'anketa_data': test_anketa
    })

    assert audit_result['status'] == 'success'
    audit_score = audit_result['audit_details']['score']
    print(f"✅ Audit complete. Score: {audit_score}/10")

    # Stage 2: Write Grant
    print("\n[2/3] Running Production Writer...")
    writer = ProductionWriter(db=test_db)
    grant_result = writer.write(anketa_data=test_anketa)

    assert grant_result is not None
    grant_content = grant_result.get('content') or test_db.get_grant_content(grant_result['grant_id'])
    print(f"✅ Grant generated. Length: {len(grant_content)} chars")

    # Stage 3: Review Grant
    print("\n[3/3] Running Reviewer...")
    reviewer = ReviewerAgent(db=test_db)
    review_result = await reviewer.review_grant_async({
        'grant_id': grant_result.get('grant_id', 'test_grant'),
        'grant_content': grant_content
    })

    assert review_result['status'] == 'success'
    review_score = review_result['review_details']['overall_score']
    print(f"✅ Review complete. Score: {review_score}/10")

    # Final assertions: Complete flow
    print("\n" + "="*60)
    print("PIPELINE VALIDATION")
    print("="*60)
    print(f"Audit Score:  {audit_score}/10")
    print(f"Grant Length: {len(grant_content)} chars")
    print(f"Review Score: {review_score}/10")
    print("="*60)

    assert audit_score >= 5.0, "Audit score too low"
    assert len(grant_content) >= 10000, "Grant too short"
    assert review_score >= 5.0, "Review score too low"

    print("\n✅ ✅ ✅ FULL PIPELINE TEST PASSED! ✅ ✅ ✅\n")


def setup_full_pipeline_mocks(gigachat_mock):
    """Setup realistic mock responses for full pipeline"""

    # Will be called 3 times (audit, grant, review)
    gigachat_mock.side_effect = [
        # 1. Audit response
        {
            'score': 8.5,
            'strengths': ['Good goal', 'Clear budget'],
            'weaknesses': ['Need more metrics'],
            'recommendations': ['Add KPIs']
        },
        # 2. Grant content response
        """
# Грантовая заявка

## 1. Актуальность
Проект решает важную проблему...

## 2. Цель и задачи
**Цель:** Достижение результата...

## 3. Методология
Используется научный подход...

## 4. Бюджет
**Общий бюджет:** 1 000 000 рублей

## 5. Ожидаемые результаты
Ожидаются следующие результаты...
""" * 3,  # Multiply to reach 10K+ chars
        # 3. Review response
        {
            'overall_score': 8.0,
            'sections': {
                'актуальность': {'score': 9, 'comment': 'Excellent'},
                'цель': {'score': 8, 'comment': 'Clear'},
                'методология': {'score': 7, 'comment': 'Good'},
                'бюджет': {'score': 8, 'comment': 'Justified'}
            },
            'recommendation': 'approve'
        }
    ]
```

---

## 📦 Fixtures (tests/integration/conftest.py)

```python
"""
Integration test fixtures.

Provides:
- test_db: Real PostgreSQL database
- test_anketa: Realistic test anketa data
- test_audit_result: Mock audit result
- test_grant: Mock grant data
- gigachat_mock: Mocked GigaChat client
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Database fixtures
@pytest.fixture(scope="module")
def test_db():
    """
    Provide real PostgreSQL database for testing.

    Options:
    1. Testcontainers (automatic Docker PostgreSQL)
    2. Manual test database (grantservice_test)
    """

    # Option 1: Testcontainers (if available)
    try:
        from testcontainers.postgres import PostgresContainer

        with PostgresContainer("postgres:16-alpine") as postgres:
            # Get connection URL
            db_url = postgres.get_connection_url()

            # Apply schema
            import subprocess
            subprocess.run([
                'psql', db_url,
                '-f', 'data/database/schema.sql'
            ], check=True)

            # Create DB client
            from data.database import DatabaseClient
            db = DatabaseClient(connection_url=db_url)

            yield db

            # Cleanup automatic

    except ImportError:
        # Option 2: Manual test database
        from data.database import DatabaseClient

        db = DatabaseClient(
            connection_url="postgresql://postgres:root@localhost:5432/grantservice_test"
        )

        yield db

        # Cleanup: truncate tables
        db.execute("TRUNCATE TABLE sessions, grants, audits, reviews CASCADE")


@pytest.fixture
def test_anketa():
    """Realistic test anketa data"""
    return {
        'id': 'test_anketa_001',
        'user_id': 12345,
        'project_name': 'Тестовый инновационный проект',
        'organization': 'Тестовая Организация',
        'budget': 1000000,
        'duration_months': 12,
        'goal': 'Разработать инновационное решение для тестирования',
        'target_audience': 'Исследователи и разработчики',
        'expected_results': 'Создание рабочего прототипа',
        'team_experience': 'Команда с опытом 5+ лет',
        'created_at': datetime.now().isoformat()
    }


@pytest.fixture
def test_audit_result():
    """Mock audit result for testing writer"""
    return {
        'score': 8.5,
        'strengths': [
            'Четкая постановка цели',
            'Обоснованный бюджет',
            'Опытная команда'
        ],
        'weaknesses': [
            'Недостаточно метрик результата'
        ],
        'recommendations': [
            'Добавить конкретные KPI',
            'Уточнить методологию'
        ]
    }


@pytest.fixture
def test_grant():
    """Mock grant data for testing reviewer"""
    return {
        'id': 'test_grant_001',
        'anketa_id': 'test_anketa_001',
        'content': """
# Грантовая заявка: Тестовый проект

## 1. Актуальность

Проект направлен на решение важной проблемы в области тестирования...

## 2. Цель и задачи

**Цель:** Разработать инновационное решение

**Задачи:**
1. Провести анализ
2. Разработать прототип
3. Протестировать решение

## 3. Методология

Используется научный подход...

## 4. Бюджет

**Общий бюджет:** 1 000 000 рублей

**Статьи расходов:**
- Оборудование: 500 000 руб
- Персонал: 400 000 руб
- Прочее: 100 000 руб

## 5. Ожидаемые результаты

Ожидается создание рабочего прототипа...
""" * 5  # Multiply to reach realistic length
    }


@pytest.fixture
def gigachat_mock():
    """
    Mock GigaChat client for testing.

    Returns AsyncMock that can be configured per test.
    """
    with patch('shared.llm.unified_llm_client.GigaChatClient') as mock:
        # Create async mock for generate method
        mock_instance = AsyncMock()
        mock.return_value = mock_instance

        yield mock_instance.generate
```

---

## 🚀 Running Tests

### Run All Integration Tests
```bash
# Run all 4 integration tests
pytest tests/integration/test_pipeline_real_agents.py -v

# Expected output:
# test_auditor_agent_integration PASSED
# test_writer_agent_integration PASSED
# test_reviewer_agent_integration PASSED
# test_full_pipeline_integration PASSED
# 4 passed in 45.2s
```

### Run Single Test
```bash
# Run just auditor test
pytest tests/integration/test_pipeline_real_agents.py::test_auditor_agent_integration -v

# Run with output
pytest tests/integration/test_pipeline_real_agents.py::test_auditor_agent_integration -v -s
```

### Run with Coverage
```bash
pytest tests/integration/test_pipeline_real_agents.py --cov=agents --cov=handlers --cov-report=term-missing
```

---

## ✅ Success Criteria

**All tests must pass:**
- [ ] `test_auditor_agent_integration` - PASS
- [ ] `test_writer_agent_integration` - PASS
- [ ] `test_reviewer_agent_integration` - PASS
- [ ] `test_full_pipeline_integration` - PASS

**Quality metrics:**
- [ ] All tests run in <60 seconds total
- [ ] No flaky tests (run 3 times, all pass)
- [ ] No import errors
- [ ] No AttributeErrors
- [ ] Database operations work correctly

---

## 🐛 Troubleshooting

### Issue: ImportError
```
ImportError: cannot import name 'AuditorAgent' from 'agents'
```

**Solution:** Check import paths match production
```python
# Try different import paths:
from agents.auditor_agent import AuditorAgent  # Current
# OR
from agents import AuditorAgent
```

### Issue: Database connection failed
```
psycopg2.OperationalError: could not connect to server
```

**Solution:** Check database exists and is running
```bash
# Check PostgreSQL running
pg_isready

# Check database exists
psql -l | grep grantservice_test

# Recreate if needed
createdb grantservice_test
```

### Issue: Test hangs
```
Test runs forever, doesn't complete
```

**Solution:** Check async/await
```python
# Make sure test is marked async
@pytest.mark.asyncio
async def test_name():
    result = await agent.method()  # Need await!
```

---

## 📊 Next Steps

**When Phase 1 complete (all 4 tests passing):**

1. ✅ Commit progress:
   ```bash
   git add tests/integration/
   git commit -m "test(iteration-53): Add Phase 1 integration tests with real agents"
   ```

2. ✅ Document results in iteration log:
   ```markdown
   ## Phase 1 Complete ✅
   - All 4 integration tests passing
   - Test suite runtime: 45s
   - No flaky tests
   - Ready for Phase 2
   ```

3. ✅ Move to Phase 2: Edge Cases
   - Read `PHASE_2_EDGE_CASES.md`
   - Start writing edge case tests

---

**Remember:** If tests fail, don't skip to manual testing! Fix the tests first. They're finding real problems.

✅ Phase 1 complete when all 4 tests consistently pass.

---

🤖 Generated with Claude Code - Phase 1 Integration Tests Guide
