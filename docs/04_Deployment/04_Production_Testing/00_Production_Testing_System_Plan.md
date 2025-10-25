# Iteration 26.2+: Production Testing System - План внедрения

**Iteration:** 26.2 (Smoke Tests) → 26.3 (Full System)
**Дата создания:** 2025-10-23
**Статус:** 📋 PLANNED
**Цель:** Создать полноценную систему автоматического тестирования на продакшн сервере
**Prerequisite:** Iteration 26.1 (Venv Setup) ✅ COMPLETE

---

## Проблема

**Текущая ситуация:**
- ❌ На продакшене нет зависимостей для pytest
- ❌ Нет psycopg2 для тестирования БД
- ❌ Невозможно запустить E2E тесты после деплоя
- ❌ Нет автоматической проверки качества деплоя
- ❌ Тесты запускаются только локально

**Последствия:**
- Деплоим "вслепую" без проверки на продакшене
- Можем пропустить ошибки, которые проявляются только в prod
- Нет уверенности что всё работает после деплоя
- Ручное тестирование в Telegram занимает время

---

## Решение

Создать **3-уровневую систему тестирования:**

### Level 1: Smoke Tests (Базовые, 10 секунд)
- Проверка что сервис запущен
- Проверка что БД доступна
- Проверка что Telegram API отвечает
- Проверка основных endpoints

### Level 2: Integration Tests (Средние, 1-2 минуты)
- Iteration 26 tests (6 тестов)
- Reference Points tests
- Database operations tests
- Qdrant connection tests

### Level 3: E2E Tests (Полные, 2-3 минуты)
- Real anketa E2E test
- Full interview flow
- Audit score generation
- PDF export (если нужно)

---

## Архитектура

```
Production Server (5.35.88.251)
│
├── /var/GrantService/
│   ├── tests/                    # Все тесты
│   │   ├── smoke/               # Smoke tests (Level 1)
│   │   ├── integration/         # Integration tests (Level 2)
│   │   └── e2e/                 # E2E tests (Level 3)
│   │
│   ├── scripts/
│   │   ├── test_after_deploy.sh        # Автозапуск после деплоя
│   │   ├── install_test_deps.sh        # Установка зависимостей
│   │   └── run_production_tests.sh     # Запуск всех тестов
│   │
│   └── config/
│       └── pytest.production.ini       # Конфиг pytest для prod
```

---

## Этапы внедрения

### Phase 1: Установка зависимостей (15 минут)

**Цель:** Установить все необходимые пакеты на продакшене

**Действия:**
```bash
# 1. Создать requirements-test.txt
pytest==8.4.2
pytest-asyncio==1.2.0
psycopg2-binary==2.9.9
pytest-timeout==2.2.0
pytest-xdist==3.5.0  # Parallel testing

# 2. Установить на продакшене
ssh root@5.35.88.251
cd /var/GrantService
pip3.12 install -r requirements-test.txt
```

**Success Criteria:**
- ✅ pytest доступен
- ✅ psycopg2 установлен
- ✅ Все зависимости установлены

**Time:** 15 минут

---

### Phase 2: Создание Smoke Tests (30 минут)

**Цель:** Быстрые базовые тесты (~10 секунд)

**Файл:** `tests/smoke/test_production_smoke.py`

**Тесты:**
1. `test_service_running()` - Проверка что systemd service активен
2. `test_postgresql_connection()` - БД доступна
3. `test_qdrant_connection()` - Qdrant отвечает
4. `test_telegram_api_polling()` - Telegram API работает
5. `test_environment_loaded()` - Переменные окружения загружены

**Пример:**
```python
import pytest
import psycopg2
import subprocess

def test_service_running():
    """Check if grantservice-bot is running"""
    result = subprocess.run(
        ["systemctl", "is-active", "grantservice-bot"],
        capture_output=True,
        text=True
    )
    assert result.stdout.strip() == "active"

def test_postgresql_connection():
    """Check PostgreSQL is accessible"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="grantservice",
            user="grantservice",
            password=os.getenv("POSTGRES_PASSWORD")
        )
        conn.close()
        assert True
    except Exception as e:
        pytest.fail(f"PostgreSQL connection failed: {e}")
```

**Success Criteria:**
- ✅ 5 smoke tests созданы
- ✅ Все проходят на продакшене
- ✅ Время выполнения < 15 секунд

**Time:** 30 минут

---

### Phase 3: Адаптация Integration Tests (1 час)

**Цель:** Запустить существующие integration тесты на продакшене

**Проблемы:**
- Тесты используют локальные fixtures
- Некоторые тесты требуют mock данных
- Пути к файлам могут быть другие

**Решение:**
1. Создать `conftest.py` для production
2. Использовать production БД (осторожно!)
3. Создать production-safe fixtures

**Файл:** `tests/conftest.production.py`

```python
import pytest
import os

# Пометить что мы в production
@pytest.fixture(scope="session")
def is_production():
    return os.path.exists("/var/GrantService")

# Production database (read-only для большинства тестов)
@pytest.fixture
def prod_db():
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5434,
        database="grantservice",
        user="grantservice",
        password=os.getenv("POSTGRES_PASSWORD")
    )
    yield conn
    conn.close()
```

**Тесты для адаптации:**
- `tests/test_iteration_26_hardcoded_question2.py` (6 тестов)
- `tests/integration/test_hardcoded_rp_integration.py`

**Success Criteria:**
- ✅ Integration тесты запускаются на prod
- ✅ 6/6 тестов проходят
- ✅ Не влияют на production данные

**Time:** 1 час

---

### Phase 4: E2E Tests на продакшене (1 час)

**Цель:** Запустить полный E2E тест с реальными данными

**Проблема:**
- E2E тест требует многих зависимостей
- Использует real anketa data
- Может занять 1-2 минуты

**Решение:**
1. Создать упрощённую версию E2E теста для prod
2. Использовать test anketa вместо production
3. Изолировать от production БД

**Файл:** `tests/e2e/test_production_e2e.py`

**Тест:**
```python
@pytest.mark.asyncio
@pytest.mark.timeout(180)  # 3 minutes max
async def test_production_interview_flow():
    """
    Test full interview flow on production
    - Uses test user data
    - Does not pollute production DB
    - Validates question #2 is instant
    """
    # Setup test data
    test_anketa = {
        "applicant_name": "Test User",
        "project_name": "Test Project"
    }

    # Run interview
    agent = InteractiveInterviewerAgentV2(...)
    result = await agent.conduct_interview(...)

    # Validate
    assert result["questions_asked"] >= 10
    assert result["fields_collected"] >= 11
    assert result["question_2_time"] < 0.1  # INSTANT!
    assert result["audit_score"] > 7.0
```

**Success Criteria:**
- ✅ E2E тест создан для production
- ✅ Не влияет на production данные
- ✅ Проверяет question #2 instant
- ✅ Время выполнения < 3 минуты

**Time:** 1 час

---

### Phase 5: Automation Scripts (1 час)

**Цель:** Автоматизировать запуск тестов после деплоя

**Scripts:**

#### 1. `scripts/install_test_deps.sh`
```bash
#!/bin/bash
# Install test dependencies on production

set -e

echo "Installing test dependencies..."
cd /var/GrantService
pip3.12 install -r requirements-test.txt

echo "✅ Test dependencies installed"
```

#### 2. `scripts/run_production_tests.sh`
```bash
#!/bin/bash
# Run all production tests

set -e

cd /var/GrantService

echo "=========================================="
echo "🧪 RUNNING PRODUCTION TESTS"
echo "=========================================="

# Level 1: Smoke Tests (10s)
echo ""
echo "[1/3] Running Smoke Tests..."
pytest tests/smoke/ -v --tb=short || exit 1
echo "✅ Smoke tests passed"

# Level 2: Integration Tests (1-2min)
echo ""
echo "[2/3] Running Integration Tests..."
pytest tests/test_iteration_26_hardcoded_question2.py -v --tb=short || exit 1
echo "✅ Integration tests passed"

# Level 3: E2E Tests (2-3min)
echo ""
echo "[3/3] Running E2E Tests..."
pytest tests/e2e/test_production_e2e.py -v --tb=short || exit 1
echo "✅ E2E tests passed"

echo ""
echo "=========================================="
echo "✅ ALL TESTS PASSED"
echo "=========================================="
```

#### 3. `scripts/test_after_deploy.sh`
```bash
#!/bin/bash
# Run after deployment to verify everything works

set -e

echo "Post-deployment testing..."

# Wait for service to start
sleep 5

# Run tests
./scripts/run_production_tests.sh

# Create test report
echo "Creating test report..."
pytest tests/ --html=reports/test_report_$(date +%Y%m%d_%H%M%S).html

echo "✅ Post-deployment tests complete"
```

**Success Criteria:**
- ✅ 3 скрипта созданы
- ✅ Скрипты исполняемые (chmod +x)
- ✅ Работают на продакшене

**Time:** 1 час

---

### Phase 6: Интеграция в Deploy Process (30 минут)

**Цель:** Автоматически запускать тесты после каждого деплоя

**Обновить:** `deploy_v2_to_production.sh`

```bash
#!/bin/bash
# Deploy Reference Points Framework V2 to Production
# WITH AUTOMATED TESTING

set -e

echo "=========================================="
echo "🚀 DEPLOYING TO PRODUCTION"
echo "=========================================="

# ... existing deployment steps ...

# Step 6: Run post-deployment tests
echo "[6/6] Running post-deployment tests..."
./scripts/test_after_deploy.sh

if [ $? -eq 0 ]; then
    echo "✅ DEPLOYMENT SUCCESSFUL - ALL TESTS PASSED"
else
    echo "❌ DEPLOYMENT FAILED - TESTS FAILED"
    echo "   Consider rollback!"
    exit 1
fi
```

**Success Criteria:**
- ✅ Тесты запускаются автоматически
- ✅ Деплой останавливается если тесты падают
- ✅ Отчёт создаётся автоматически

**Time:** 30 минут

---

## Timeline

**Total Time:** ~4.5 часа

| Phase | Task | Time | Cumulative |
|-------|------|------|------------|
| 1 | Install dependencies | 15 min | 15 min |
| 2 | Create smoke tests | 30 min | 45 min |
| 3 | Adapt integration tests | 1 hour | 1h 45min |
| 4 | Create E2E tests | 1 hour | 2h 45min |
| 5 | Automation scripts | 1 hour | 3h 45min |
| 6 | Deploy integration | 30 min | 4h 15min |

**Recommended Schedule:**
- **Session 1 (2 hours):** Phases 1-2 (Dependencies + Smoke tests)
- **Session 2 (2 hours):** Phases 3-4 (Integration + E2E)
- **Session 3 (1 hour):** Phases 5-6 (Automation + Integration)

---

## Dependencies to Install

### Core Testing:
```
pytest==8.4.2
pytest-asyncio==1.2.0
pytest-timeout==2.2.0
pytest-xdist==3.5.0
```

### Database:
```
psycopg2-binary==2.9.9
```

### Reports:
```
pytest-html==4.1.1
pytest-json-report==1.5.0
```

### Coverage (optional):
```
pytest-cov==4.1.0
```

**File:** `requirements-test.txt`

---

## Success Criteria

### Phase 1-2 (Smoke Tests):
- ✅ pytest установлен на продакшене
- ✅ 5 smoke тестов созданы
- ✅ Все smoke тесты проходят
- ✅ Время выполнения < 15 секунд

### Phase 3-4 (Integration + E2E):
- ✅ 6 integration тестов адаптированы
- ✅ 1 E2E тест создан для production
- ✅ Все тесты проходят
- ✅ Question #2 instant подтверждён

### Phase 5-6 (Automation):
- ✅ 3 automation скрипта созданы
- ✅ Тесты запускаются автоматически после деплоя
- ✅ Отчёт генерируется автоматически
- ✅ Деплой останавливается при ошибках

### Overall:
- ✅ 100% деплоев тестируются автоматически
- ✅ Время тестирования < 5 минут
- ✅ Отчёты сохраняются для истории
- ✅ Нет false positives

---

## Risks & Mitigation

### Risk #1: Тесты влияют на production данные
**Probability:** Medium
**Impact:** High
**Mitigation:**
- Использовать test user accounts
- Read-only доступ к production БД
- Отдельная test БД если нужно

### Risk #2: Тесты падают из-за production environment
**Probability:** Medium
**Impact:** Medium
**Mitigation:**
- Создать production-specific fixtures
- Адаптировать тесты для production
- Мягкие проверки вместо жёстких

### Risk #3: Тесты занимают слишком много времени
**Probability:** Low
**Impact:** Low
**Mitigation:**
- Использовать pytest-xdist для parallel
- Ограничить timeouts
- Запускать только критичные тесты

### Risk #4: Тесты ложные срабатывания (flaky tests)
**Probability:** Medium
**Impact:** Medium
**Mitigation:**
- Retry failed tests (pytest-rerunfailures)
- Стабилизировать тесты
- Логирование для debugging

---

## Expected Benefits

### Short Term (Week 1):
- ✅ Автоматическая проверка после каждого деплоя
- ✅ Быстрое обнаружение проблем
- ✅ Уверенность в деплоях

### Medium Term (Month 1):
- ✅ Меньше багов в production
- ✅ Быстрее деплоим (нет ручного тестирования)
- ✅ История тестов и метрик

### Long Term (Quarter 1):
- ✅ CI/CD pipeline
- ✅ Automatic rollback при ошибках
- ✅ Performance regression detection
- ✅ A/B testing infrastructure

---

## Cost-Benefit Analysis

### Investment:
- **Time:** ~4.5 hours setup
- **Storage:** ~100MB для dependencies
- **CPU:** +30 seconds на каждый тест run
- **Cost:** $0 (все бесплатно)

### Return:
- **Time saved:** ~10 минут на каждый деплой (no manual testing)
- **Bug prevention:** Catch issues before users do
- **Confidence:** 100% verified deploys
- **Risk reduction:** Less production incidents

### ROI:
- After 10 deploys: **~1 hour saved**
- After 50 deploys: **~5 hours saved**
- Plus: prevented bugs, faster incident response
- **ROI: Infinite** (one-time setup, ongoing benefit)

---

## Next Steps

### Immediate:
1. ✅ Review this plan
2. ⏳ Approve plan
3. ⏳ Start Phase 1 (Install dependencies)

### This Week:
1. Complete Phases 1-2 (Smoke tests)
2. Complete Phases 3-4 (Integration + E2E)
3. Complete Phases 5-6 (Automation)

### This Month:
1. Monitor test results
2. Improve test coverage
3. Add performance tests
4. Create dashboard

---

## Documentation Structure

```
Development/04_Production_Testing/
├── 00_Production_Testing_System_Plan.md    (this file)
├── 01_Installation_Guide.md                (Phase 1)
├── 02_Smoke_Tests_Implementation.md        (Phase 2)
├── 03_Integration_Tests_Adaptation.md      (Phase 3)
├── 04_E2E_Tests_Production.md              (Phase 4)
├── 05_Automation_Scripts.md                (Phase 5)
└── 06_Deploy_Integration.md                (Phase 6)
```

---

## References

**Related Documents:**
- `DEPLOYMENT_INDEX.md` - История деплоев
- `Deploy_2025-10-23_Iteration_26_PLANNED/04_Post_Deploy_Tests.md` - Test instructions
- `tests/README.md` - Existing test documentation

**Production Server:**
- IP: 5.35.88.251
- Path: /var/GrantService
- Service: grantservice-bot

**Test Files:**
- Smoke: `tests/smoke/`
- Integration: `tests/integration/`, `tests/test_iteration_*.py`
- E2E: `tests/integration/test_real_anketa_e2e.py`

---

**Status:** 📋 READY TO START
**Approval:** Pending
**Start Date:** TBD
**Estimated Completion:** 3 sessions (~4.5 hours)

---

**Created:** 2025-10-23
**Author:** Claude Code AI Assistant
**Version:** 1.0
**Next Review:** After Phase 2 completion
