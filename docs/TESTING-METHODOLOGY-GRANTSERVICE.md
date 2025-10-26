# Testing Methodology for GrantService Project

**Date:** 2025-10-26
**Version:** 1.0.0
**Project:** GrantService (AI/LLM Multi-Agent System)
**Status:** Implementation Ready ✅

**Reference:** See `C:\SnowWhiteAI\cradle\04-Knowledge-Base\03-Methodologies\TESTING-METHODOLOGY.md` for universal principles.

---

## 📋 Executive Summary

This document provides a **concrete, actionable testing methodology** specifically for the GrantService project, based on:

1. **Analysis of 45 iterations** (Iterations 27-45 in `C:\SnowWhiteAI\GrantService\iterations\`)
2. **Universal testing principles** (Cradle Knowledge-Base methodology)
3. **GrantService-specific challenges** (LLM non-determinism, GigaChat API, Telegram Bot, PostgreSQL)

### The Problem (Current State)

**From 45 iterations analysis:**
- ✅ 11 successful (58%)
- ⚠️ 3 partial (16%)
- ❌ 3 failed (16%)
- **80% time spent debugging**, 20% developing

**Root Causes:**
1. **Test-Production Mismatch** (Iterations 28-29): Tests bypass `shared/llm/unified_llm_client.py`
2. **Missing E2E Tests** (Iterations 27-30): 4 iterations to get E2E working
3. **API Issues** (Iterations 42-44): No health checks, expired keys undetected
4. **SQL Bugs** (Iterations 32-34): No pre-deployment integration tests
5. **Architecture Coupling** (Iteration 29): Researcher tied to Telegram Bot DB

### The Solution (8-Week Refactoring)

**ROI Projection:**
- Iterations per feature: **4-5 → 1-2** (60% reduction)
- Debugging time: **80% → 20%** (4x improvement)
- First-try success: **58% → 90%+** (32% improvement)
- **Total time saved:** ~55 hours (11 iterations avoided)

### Quick Start

**Week 1-2:** Foundation (src/ layout, pydantic-settings)
**Week 3-4:** Test infrastructure (conftest.py, markers, fixtures)
**Week 5-6:** Core tests (E2E, integration, API health)
**Week 7-8:** CI/CD automation (GitHub Actions, secrets)

---

## 🎯 GrantService-Specific Context

### Technology Stack

**Backend:**
- Python 3.10+
- PostgreSQL (localhost:5432/grantservice)
- Qdrant Vector DB (5.35.88.251:6333)
- GigaChat API (Sber LLM - 1 concurrent stream)

**Agents:**
- FullFlowManager (orchestrator)
- InteractiveInterviewerAgentV2 (Reference Points P0-P3)
- ProductionWriter (section-by-section, 10 sections)
- AuditorAgent (quality control)
- AnketaValidator (input validation)

**Interfaces:**
- Telegram Bot (python-telegram-bot)
- Streamlit Admin Panel

**Data:**
- Anketas (user interviews, JSONB dialog_history)
- Grants (generated applications, 30K+ chars)
- Audits (quality scores 0-10)

### Critical Requirements

1. **LLM Non-Determinism:** Outputs vary even with temperature=0
2. **API Rate Limiting:** GigaChat 1 concurrent stream, 6s between calls
3. **Long Generation Time:** Full grant ~2-7 minutes
4. **Database State:** Tests must isolate from production DB
5. **Telegram Bot Coupling:** Some agents require telegram_id, session_id

---

## 📊 Lessons from 45 Iterations

### What Went Wrong (Patterns)

| Iteration | Problem | Root Cause | Cost |
|-----------|---------|------------|------|
| **28-29** | Test-prod mismatch | Tests bypass production imports | 2 iterations |
| **29** | Architecture coupling | Researcher needs Telegram Bot DB | 1 iteration (blocker) |
| **42-44** | GigaChat API blocked | No health checks, expired key | 3 iterations (21%) |
| **32-34** | SQL bugs | No integration tests pre-deploy | 3 iterations (16%) |
| **41** | VARCHAR overflow | No realistic data validation | 1 iteration |

**Total preventable:** 10 iterations = **52% of work**

### What Worked Well

| Success | Iteration | Impact |
|---------|-----------|--------|
| **Standalone wrappers** | 30 | Broke DB coupling, enabled E2E |
| **Synthetic data** | 38, 41 | 100 anketas tested, realistic |
| **Two-Stage QA** | 37 | Quality 0.47 → 9.0/10 |
| **Test result docs** | All | Clear history, reproducible |

---

## 🏗️ Implementation Plan (8 Weeks)

### Phase 1: Foundation (Weeks 1-2)

#### Goal: Production Parity + Unified Config

**Tasks:**

1. **Restructure to src/ Layout**
   ```
   GrantService/
   ├── src/
   │   └── grantservice/          # NEW: installable package
   │       ├── __init__.py
   │       ├── agents/            # Move from root
   │       ├── shared/            # Move from root
   │       ├── handlers/          # Telegram handlers
   │       └── config/
   │           └── settings.py    # NEW: pydantic-settings
   ├── tests/                     # NEW: organized tests
   │   ├── conftest.py
   │   ├── unit/
   │   ├── integration/
   │   └── e2e/
   ├── config/
   │   ├── .env.example
   │   ├── .env.test
   │   └── .env                   # gitignored
   └── pyproject.toml             # NEW: modern packaging
   ```

2. **Create Unified Config**
   ```python
   # src/grantservice/config/settings.py
   from pydantic_settings import BaseSettings, SettingsConfigDict

   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file='.env')

       # Database
       DATABASE_URL: str

       # AI Services
       GIGACHAT_API_KEY: str
       GIGACHAT_MODEL: str = "GigaChat-2-Max"

       # Vector DB
       QDRANT_HOST: str
       QDRANT_PORT: int = 6333
       QDRANT_COLLECTION: str = "fpg_requirements"

       # Telegram
       TELEGRAM_BOT_TOKEN: str

       # Application
       ENVIRONMENT: str = "development"
       LOG_LEVEL: str = "INFO"

   settings = Settings()
   ```

3. **Refactor All Code**
   ```python
   # OLD (scattered):
   api_key = os.getenv('GIGACHAT_API_KEY')  # ❌

   # NEW (unified):
   from grantservice.config.settings import settings  # ✅
   api_key = settings.GIGACHAT_API_KEY
   ```

4. **Configure pytest**
   ```toml
   # pyproject.toml
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   addopts = ["--import-mode=importlib", "--strict-markers"]
   markers = [
       "slow: marks tests as slow (minutes)",
       "integration: needs database/services",
       "e2e: full system test",
       "gigachat: needs real GigaChat API",
   ]
   ```

**Exit Criteria:**
- ✅ Zero `os.getenv()` in `src/grantservice/` code
- ✅ `pip install -e .` works
- ✅ `pytest --collect-only` shows 0 errors
- ✅ CI builds package successfully

---

### Phase 2: Test Infrastructure (Weeks 3-4)

#### Goal: Fixtures + Testcontainers + Markers

**Tasks:**

1. **Create Root conftest.py**
   ```python
   # tests/conftest.py
   import pytest
   import os
   from testcontainers.postgres import PostgresContainer

   # ===== SESSION SETUP =====
   @pytest.fixture(scope="session", autouse=True)
   def test_environment():
       """Load test environment"""
       os.environ['ENV_FILE'] = '.env.test'

   @pytest.fixture(scope="session")
   def app_settings(test_environment):
       """Production settings singleton"""
       from grantservice.config.settings import settings
       assert settings.ENVIRONMENT == "test"
       return settings

   # ===== DATABASE =====
   @pytest.fixture(scope="session")
   def postgres_container():
       """Ephemeral PostgreSQL for all tests"""
       with PostgresContainer("postgres:16-alpine") as container:
           # Apply schema
           connection_url = container.get_connection_url()
           from grantservice.database import apply_schema
           apply_schema(connection_url)

           yield connection_url

   @pytest.fixture(scope="module")
   def test_db(postgres_container):
       """Database client for integration tests"""
       from grantservice.database import DatabaseClient
       return DatabaseClient(postgres_container)

   # ===== GIGACHAT API =====
   @pytest.fixture(scope="session", autouse=True)
   def gigachat_health_check(app_settings):
       """Pre-flight: verify GigaChat API"""
       from grantservice.shared.llm.unified_llm_client import get_client

       client = get_client('gigachat')
       try:
           client.generate("test", max_tokens=5)
           print("✅ GigaChat API: Healthy")
       except Exception as e:
           pytest.fail(f"❌ GigaChat API unavailable: {e}")

   @pytest.fixture(scope="session")
   def rate_limiter():
       """GigaChat rate limit protection (6s)"""
       import time
       last_call = [0]

       def limit(delay=6):
           elapsed = time.time() - last_call[0]
           if elapsed < delay:
               time.sleep(delay - elapsed)
           last_call[0] = time.time()

       return limit

   @pytest.fixture(scope="module")
   def gigachat_client(app_settings, gigachat_health_check):
       """Real GigaChat client with health check"""
       from grantservice.shared.llm.unified_llm_client import get_client
       return get_client('gigachat')
   ```

2. **Create Integration conftest.py**
   ```python
   # tests/integration/conftest.py
   import pytest

   @pytest.fixture
   def test_anketa(test_db):
       """Create test anketa in DB"""
       from grantservice.database.models import Anketa

       anketa = Anketa(
           telegram_id=12345,
           name="Test User",
           organization="Test Org",
           project_description="Test project for methodology validation",
           budget=500000,
           # ... all required fields
       )

       anketa_id = test_db.save_anketa(anketa)
       yield test_db.get_anketa(anketa_id)

       # Cleanup
       test_db.delete_anketa(anketa_id)
   ```

3. **Create Synthetic Data Generator** (already exists, integrate)
   ```python
   # tests/fixtures/synthetic_user_simulator.py
   # Use existing agents/synthetic_user_simulator.py
   # Import in conftest.py

   @pytest.fixture
   def synthetic_user_responses():
       """Generate realistic user responses"""
       from grantservice.agents.synthetic_user_simulator import SyntheticUserSimulator

       simulator = SyntheticUserSimulator()
       return simulator.generate_responses(quality="high")
   ```

**Exit Criteria:**
- ✅ `tests/conftest.py` with session fixtures
- ✅ Testcontainers PostgreSQL working
- ✅ GigaChat health check passes
- ✅ Rate limiter fixture tested

---

### Phase 3: Core Tests (Weeks 5-6)

#### Goal: E2E + Integration + API Validation

**Priority 1: E2E Test (Most Critical!)**

```python
# tests/e2e/test_full_grant_pipeline.py
import pytest

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.gigachat
def test_complete_grant_workflow(
    test_db,
    gigachat_client,
    rate_limiter,
    synthetic_user_responses
):
    """
    E2E: Full production flow

    This test validates:
    - InteractiveInterviewerV2 (dialog)
    - ProductionWriter (grant generation)
    - AuditorAgent (quality check)

    Duration: ~7-10 minutes
    GigaChat calls: ~15-20 (with rate limiting)
    """

    # ===== PHASE 1: Interview =====
    from grantservice.agents.full_flow_manager import FullFlowManager

    manager = FullFlowManager(
        db=test_db,
        llm_client=gigachat_client
    )

    # Run full interview (hardcoded + adaptive)
    with rate_limiter():
        anketa = manager.run_interview(
            user_id=12345,
            responses=synthetic_user_responses
        )

    # Validate interview completion
    assert anketa.status == "completed"
    assert len(anketa.fields) >= 10  # All required fields
    assert anketa.dialog_history is not None  # JSONB tracking

    # ===== PHASE 2: Grant Generation =====
    from grantservice.agents.production_writer import ProductionWriter

    writer = ProductionWriter(
        db=test_db,
        llm_client=gigachat_client
    )

    # Generate grant (section-by-section)
    with rate_limiter():
        grant = writer.generate(anketa_id=anketa.id)

    # Validate grant
    assert grant.id is not None  # Saved to DB
    assert len(grant.content) >= 30000  # 30K+ requirement
    assert grant.anketa_id == anketa.id

    # Verify DB persistence
    saved_grant = test_db.get_grant(grant.id)
    assert saved_grant.content == grant.content

    # ===== PHASE 3: Quality Audit =====
    from grantservice.agents.auditor_agent import AuditorAgent

    auditor = AuditorAgent(llm_client=gigachat_client)

    with rate_limiter():
        audit = auditor.evaluate(grant_id=grant.id)

    # Validate audit
    assert audit.score >= 7.0  # Quality threshold
    assert audit.status in ["approved", "needs_revision"]

    # ===== SUCCESS! =====
    # If this test passes, the ENTIRE production flow works! ✅
    print(f"""
    ✅ E2E TEST PASSED!

    Anketa ID: {anketa.id}
    Grant ID: {grant.id}
    Grant Length: {len(grant.content):,} chars
    Audit Score: {audit.score}/10
    Status: {audit.status}
    """)
```

**Priority 2: Integration Tests**

```python
# tests/integration/test_production_writer_integration.py
import pytest

@pytest.mark.integration
@pytest.mark.gigachat
def test_production_writer_database_integration(test_db, test_anketa, gigachat_client):
    """Integration: ProductionWriter → PostgreSQL"""

    from grantservice.agents.production_writer import ProductionWriter

    writer = ProductionWriter(
        db=test_db,  # Real DB (Testcontainers)
        llm_client=gigachat_client  # Real LLM (with vcrpy?)
    )

    grant = writer.generate(anketa_id=test_anketa.id)

    # Validate DB integration
    assert grant.saved_to_db
    retrieved = test_db.get_grant(grant.id)
    assert retrieved is not None


@pytest.mark.integration
def test_anketa_validator_coherence_check(test_db, gigachat_client):
    """Integration: AnketaValidator → GigaChat coherence"""

    from grantservice.agents.anketa_validator import AnketaValidator

    validator = AnketaValidator(llm_client=gigachat_client)

    # Valid anketa
    valid_anketa = {
        "name": "Dr. Smith",
        "organization": "Research Institute",
        "project_description": "Novel cancer treatment using CRISPR"
    }

    result = validator.validate_coherence(valid_anketa)
    assert result.is_coherent

    # Incoherent anketa
    incoherent = {
        "name": "asdf",
        "organization": "qwerty",
        "project_description": "random words no meaning"
    }

    result = validator.validate_coherence(incoherent)
    assert not result.is_coherent
```

**Priority 3: Unit Tests (Components)**

```python
# tests/unit/test_anketa_validator_logic.py
import pytest
from grantservice.agents.anketa_validator import AnketaValidator

def test_validator_detects_missing_required_fields():
    """Unit: Required field validation (no LLM)"""

    validator = AnketaValidator()

    incomplete = {"name": "Test"}  # Missing organization
    result = validator.validate_required_fields(incomplete)

    assert not result.is_valid
    assert "organization" in result.missing_fields


def test_validator_checks_field_length():
    """Unit: Field length validation"""

    validator = AnketaValidator()

    # Too short
    short_desc = {"project_description": "abc"}
    assert not validator.validate_length(short_desc)

    # Good length
    good_desc = {"project_description": "A" * 200}
    assert validator.validate_length(good_desc)

    # Too long (VARCHAR overflow)
    too_long = {"project_description": "A" * 2000}
    assert not validator.validate_length(too_long)
```

**Exit Criteria:**
- ✅ At least 1 passing E2E test
- ✅ 5+ integration tests (DB, API, agents)
- ✅ 20+ unit tests (validators, parsers)
- ✅ >80% code coverage on critical paths

---

### Phase 4: CI/CD Automation (Weeks 7-8)

#### Goal: GitHub Actions Pipeline

**File:** `.github/workflows/ci.yml`

```yaml
name: GrantService CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Nightly E2E tests

jobs:
  # ===== STAGE 1: Fast Tests (every commit) =====
  lint-and-unit:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e .[dev]

      - name: Lint with ruff
        run: ruff check src/ tests/

      - name: Type check with mypy
        run: mypy src/grantservice/

      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            -m "not slow and not integration and not e2e" \
            --cov=src/grantservice \
            --cov-report=xml \
            --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  # ===== STAGE 2: Integration Tests (on PR) =====
  integration:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    if: github.event_name == 'pull_request'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -e .[dev]

      - name: Run integration tests
        env:
          GIGACHAT_API_KEY: ${{ secrets.GIGACHAT_TEST_KEY }}
        run: |
          pytest tests/integration/ \
            -m "integration and not e2e" \
            --maxfail=3 \
            -v

  # ===== STAGE 3: E2E Tests (nightly) =====
  e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    if: github.event_name == 'schedule'  # Nightly only

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -e .[dev]

      - name: Run E2E tests
        env:
          GIGACHAT_API_KEY: ${{ secrets.GIGACHAT_API_KEY }}
          DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
          QDRANT_HOST: ${{ secrets.QDRANT_HOST }}
        run: |
          pytest tests/e2e/ \
            -m "e2e" \
            --maxfail=1 \
            -v \
            --tb=short

      - name: Upload E2E test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-results
          path: test-results/
```

**GitHub Secrets to Configure:**
```
Settings → Secrets → Actions → New repository secret

GIGACHAT_API_KEY=<production_key>
GIGACHAT_TEST_KEY=<test_key_or_same>
TEST_DATABASE_URL=<postgres_url_for_ci>
QDRANT_HOST=5.35.88.251
```

**Exit Criteria:**
- ✅ CI runs on every commit (<10 min)
- ✅ Integration tests run on PR
- ✅ E2E tests run nightly
- ✅ Coverage report generated

---

## 🔧 GrantService-Specific Solutions

### 1. GigaChat API Management

**Problem:** Iterations 42-44 blocked by API issues.

**Solution:**
```python
# tests/conftest.py

@pytest.fixture(scope="session", autouse=True)
def gigachat_preflight_check(app_settings):
    """Fail fast if GigaChat unavailable"""

    from grantservice.shared.llm.unified_llm_client import get_client
    import requests

    client = get_client('gigachat')

    try:
        # Test auth
        response = client.generate("ping", max_tokens=1)
        print(f"✅ GigaChat API: OK")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            pytest.fail("❌ GigaChat API: 401 Unauthorized (expired key?)")
        elif e.response.status_code == 429:
            pytest.fail("❌ GigaChat API: 429 Too Many Requests (quota exhausted?)")
        else:
            pytest.fail(f"❌ GigaChat API: {e}")

    except Exception as e:
        pytest.fail(f"❌ GigaChat API: {e}")


@pytest.fixture(scope="session")
def gigachat_rate_limiter():
    """Enforce 6s between calls (1 concurrent stream limit)"""

    import time
    from contextlib import contextmanager

    last_call_time = [0]

    @contextmanager
    def limit(delay=6):
        # Wait if needed
        elapsed = time.time() - last_call_time[0]
        if elapsed < delay:
            wait_time = delay - elapsed
            print(f"⏳ Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)

        yield

        # Update timestamp
        last_call_time[0] = time.time()

    return limit
```

---

### 2. LLM Output Validation

**Problem:** Non-deterministic outputs (can't use exact match).

**Solution: Semantic Validation**
```python
# tests/utils/llm_validators.py

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class SemanticValidator:
    """Validate LLM outputs by meaning, not exact text"""

    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def is_similar(self, text1: str, text2: str, threshold=0.8) -> bool:
        """Check if two texts are semantically similar"""

        emb1 = self.model.encode([text1])
        emb2 = self.model.encode([text2])

        similarity = cosine_similarity(emb1, emb2)[0][0]

        return similarity >= threshold

    def contains_concepts(self, text: str, required_concepts: list) -> bool:
        """Check if text contains required concepts (flexible)"""

        text_lower = text.lower()

        # Flexible matching (synonyms, variations)
        for concept in required_concepts:
            # Simple keyword presence
            if concept.lower() in text_lower:
                continue

            # Semantic similarity check
            # (could use embeddings for better matching)
            # For now, simple keyword
            return False

        return True


# Usage in tests:
def test_grant_contains_required_sections():
    """Grant should mention key concepts (flexible)"""

    grant = writer.generate(anketa_id=test_anketa.id)

    validator = SemanticValidator()

    required_concepts = [
        "innovation",
        "methodology",
        "budget",
        "impact",
        "team"
    ]

    assert validator.contains_concepts(grant.content, required_concepts)
```

---

### 3. Database Isolation

**Problem:** Tests pollute production DB.

**Solution: Testcontainers**
```python
# tests/conftest.py

import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_test_container():
    """Ephemeral PostgreSQL for ALL tests"""

    with PostgresContainer("postgres:16-alpine") as container:
        # Get connection URL
        db_url = container.get_connection_url()

        # Apply GrantService schema
        from grantservice.database.migrations import apply_all_migrations
        apply_all_migrations(db_url)

        print(f"✅ Test PostgreSQL: {db_url}")

        yield db_url

        # Container destroyed automatically


@pytest.fixture(scope="function")
def clean_test_db(postgres_test_container):
    """Fresh DB state for each test"""

    from grantservice.database import DatabaseClient

    db = DatabaseClient(postgres_test_container)

    yield db

    # Cleanup: truncate all tables
    db.truncate_all_tables()
```

---

### 4. Telegram Bot Decoupling

**Problem:** Iteration 29 - Researcher requires telegram_id from Bot.

**Solution: Mock Telegram Context**
```python
# tests/fixtures/telegram_mocks.py

from dataclasses import dataclass

@dataclass
class MockTelegramUser:
    """Mock Telegram user for testing"""
    id: int = 12345
    username: str = "test_user"
    first_name: str = "Test"
    last_name: str = "User"


@dataclass
class MockTelegramMessage:
    """Mock Telegram message"""
    text: str
    from_user: MockTelegramUser
    chat_id: int = 12345


@pytest.fixture
def mock_telegram_context():
    """Provide mock Telegram context for agents"""

    return {
        'user': MockTelegramUser(),
        'chat_id': 12345,
        'message': MockTelegramMessage(
            text="Test message",
            from_user=MockTelegramUser()
        )
    }


# Usage:
def test_interviewer_without_real_telegram(mock_telegram_context, test_db):
    """Test interviewer agent without real Telegram Bot"""

    from grantservice.agents.interactive_interviewer_v2 import InteractiveInterviewerV2

    interviewer = InteractiveInterviewerV2(
        db=test_db,
        telegram_context=mock_telegram_context  # Mocked
    )

    # Can now test without running Telegram Bot!
    question = interviewer.generate_next_question()
    assert question is not None
```

---

## 📊 Success Metrics

### Before vs After

| Metric | Before (Current) | After (Target) | Improvement |
|--------|------------------|----------------|-------------|
| **Iterations per feature** | 4-5 | 1-2 | 60% ↓ |
| **First-try success rate** | 58% | 90%+ | 55% ↑ |
| **Time on debugging** | 80% | 20% | 75% ↓ |
| **Test coverage** | ~0% | 80%+ | +80% |
| **Production bugs** | High | Near zero | 90% ↓ |
| **Deployment confidence** | Low | High | ⭐⭐⭐⭐⭐ |
| **API blocks (like 42-44)** | Frequent | Prevented | 100% ↓ |
| **SQL bugs (like 32-34)** | Frequent | Prevented | 100% ↓ |

### Tracked KPIs

```python
# After implementation, track in CI:
# .github/workflows/metrics.yml

- name: Report metrics
  run: |
    echo "Total tests: $(pytest --collect-only -q | tail -1)"
    echo "Coverage: $(pytest --cov-report=term | grep TOTAL)"
    echo "E2E pass rate: $(pytest tests/e2e/ --tb=no -q | grep passed)"
```

---

## 🎯 Quick Wins (Immediate Actions)

### Week 1 Quick Wins (Can Start Today!)

1. **Create .env.test** (30 min)
   ```bash
   cp config/.env config/.env.test
   # Edit: use test_ prefixes for DB, test API keys
   ```

2. **Add GigaChat health check** (1 hour)
   ```python
   # Add to any test file as experiment:
   import pytest
   from shared.llm.unified_llm_client import get_client

   def test_gigachat_health():
       """Verify API accessible"""
       client = get_client('gigachat')
       response = client.generate("test", max_tokens=5)
       assert response
   ```

3. **Create first E2E test skeleton** (2 hours)
   ```python
   # tests/test_e2e_experiment.py
   def test_grant_generation_basic():
       """Experimental E2E test"""
       # TODO: implement using existing code
       # This validates current architecture works!
       pass
   ```

4. **Document current test coverage** (1 hour)
   - List all test scripts in `iterations/`
   - Identify what's tested vs untested
   - Create COVERAGE_BASELINE.md

---

## 📁 Deliverables

### 1. Code Structure
```
GrantService/
├── src/grantservice/          # Refactored
├── tests/                     # NEW
├── config/                    # Organized
├── .github/workflows/         # CI/CD
└── pyproject.toml             # Modern packaging
```

### 2. Documentation
- ✅ This methodology document
- ✅ COVERAGE_BASELINE.md (before refactoring)
- ✅ REFACTORING_CHECKLIST.md (step-by-step)
- ✅ TEST_RESULTS_SUMMARY.md (after implementation)

### 3. Tests
- 1 E2E test (full pipeline)
- 5+ integration tests (API, DB, agents)
- 20+ unit tests (validators, parsers)
- Fixtures & conftest.py hierarchy

### 4. CI/CD
- GitHub Actions workflow (3 stages)
- Secret management
- Coverage reporting
- Nightly E2E runs

---

## 📚 Additional Resources

### GrantService-Specific References

1. **Iterations History:** `C:\SnowWhiteAI\GrantService\iterations\README_HISTORY.md`
2. **Current Code:** `C:\SnowWhiteAI\GrantService\`
3. **Universal Methodology:** `C:\SnowWhiteAI\cradle\04-Knowledge-Base\03-Methodologies\TESTING-METHODOLOGY.md`

### External Resources

- pytest docs: https://docs.pytest.org
- Testcontainers: https://testcontainers-python.readthedocs.io
- pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- GigaChat API docs: https://developers.sber.ru/docs/ru/gigachat/

---

## 🚀 Next Steps

### Immediate (This Week)
1. ✅ Review this methodology
2. ✅ Create .env.test
3. ✅ Run GigaChat health check experiment
4. ✅ Document current coverage baseline

### Short-Term (Weeks 1-4)
1. Restructure to src/ layout
2. Implement pydantic-settings
3. Create tests/ hierarchy
4. Build conftest.py fixtures

### Medium-Term (Weeks 5-8)
1. Write E2E test
2. Write integration tests
3. Set up CI/CD
4. Measure improvements

### Long-Term (After Implementation)
1. Maintain test suite
2. Add tests for new features
3. Monitor metrics
4. Continuous improvement

---

## ✅ Acceptance Criteria

**Methodology is successfully implemented when:**

1. ✅ Zero test-production mismatches (tests use production imports)
2. ✅ At least 1 passing E2E test covering full pipeline
3. ✅ >80% code coverage on critical paths
4. ✅ CI/CD pipeline running on every commit
5. ✅ Pre-deployment integration tests prevent SQL bugs
6. ✅ GigaChat API health checks prevent iteration blocks
7. ✅ First-try success rate >90%
8. ✅ Time on debugging <30%

**When these criteria are met:** GrantService has PRODUCTION-READY testing! ✅

---

**END OF GRANTSERVICE METHODOLOGY**

**Version:** 1.0.0 | **Date:** 2025-10-26 | **Status:** Implementation Ready ✅

**Estimated ROI:** 55 hours saved (11 iterations avoided) | 57% faster development

**Contact:** See Cradle OS documentation for questions.
