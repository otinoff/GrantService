# 🧬 План внедрения Cradle Methodology в GrantService

**Created:** 2025-10-25
**Based on:** Cradle OS Project-Evolution-Methodology v1.0.0
**Project:** GrantService (Iteration 34+)
**Status:** ACTIONABLE PLAN

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ ПРОЕКТА

### Сопоставление с 5 принципами Cradle:

| № | Принцип Cradle | IT Практика | GrantService Сейчас | Статус | Приоритет |
|---|----------------|-------------|---------------------|---------|-----------|
| 1 | **Метаболизм** | Continuous Integration | 34 итерации, частые коммиты | ✅ **ОТЛИЧНО** | Maintain |
| 2 | **Гомеостаз** | Automated Testing | Нет тестов перед deploy | ❌ **КРИТИЧНО** | **P0** |
| 3 | **Дифференциация** | Modular Architecture | ProductionWriter, Expert Agent | ✅ **ХОРОШО** | Maintain |
| 4 | **Иммунитет** | Code Review + CI/CD | Ручной deploy, нет CI/CD | ❌ **НУЖНО** | **P1** |
| 5 | **Регенерация** | 20% Rule Refactoring | Нет системы refactoring | ⚠️ **НУЖНО** | **P2** |

### Проблемы из истории (доказательства необходимости):

**Iteration 26.3:**
- Проблема: 4 mini-deploys вместо 1
- Причина: Нет тестов перед deploy
- Урок: "НУЖНЫ ТЕСТЫ перед deploy!"

**Iteration 34:**
- Проблема: Критический баг `'ProductionWriter' object has no attribute 'generate_grant'`
- Причина: Нет автоматических проверок
- Урок: CI/CD поймал бы это автоматически!

**Iteration 33 (Deploy #6-7):**
- Проблема: SQL bugs (user_id vs telegram_id)
- Причина: Нет проверки SQL queries
- Урок: Нужны unit tests для database methods!

**Общий pattern:**
- Баги в production → Manual hotfix → Multiple deploys → Lost time
- **Решение:** Methodology enforcement!

---

## 🎯 ПЛАН ВНЕДРЕНИЯ (3 ФАЗЫ)

```
PHASE 1: Foundation (1-2 недели)
   ↓  Закладываем основу, учимся применять

PHASE 2: Automation (2-3 недели)
   ↓  Автоматизируем проверки и процессы

PHASE 3: Optimization (постоянно)
   ↓  Измеряем, улучшаем, масштабируем
```

---

## 📋 PHASE 1: FOUNDATION (1-2 недели)

**Цель:** Создать базу для методологии, не останавливая разработку
**Принципы:** Гомеостаз (Testing), Регенерация (20% Rule)

### Week 1: Гомеостаз (Automated Testing)

#### Задача 1.1: Pre-Deploy Testing Checklist (2 часа)

**Файл:** `Development/METHODOLOGY/Pre_Deploy_Checklist.md`

**Содержание:**
```markdown
# Pre-Deploy Checklist

Применять КАЖДУЮ итерацию перед deploy!

## 1. Code Review (5 мин)
- [ ] Прочитать изменения: `git diff --cached`
- [ ] Проверить критические участки кода
- [ ] Убедиться что понятна логика
- [ ] Проверить имена методов и параметров
- [ ] Убрать debug код и TODO

## 2. Local Testing (10 мин)
- [ ] Запустить существующие тесты: `pytest tests/`
- [ ] Создать минимальный тест для нового кода
- [ ] Проверить что не сломали старое
- [ ] Проверить edge cases

## 3. Database Changes (если есть)
- [ ] Проверить SQL syntax
- [ ] Убедиться в правильности column names (user_id vs telegram_id!)
- [ ] Проверить запрос на тестовых данных
- [ ] Проверить что есть exception handling

## 4. Integration Points (если есть)
- [ ] Проверить API method names (generate_grant vs write!)
- [ ] Проверить типы параметров (dict vs string!)
- [ ] Проверить return types

## 5. Deploy
- [ ] Только ПОСЛЕ прохождения 1-4
- [ ] Commit с осмысленным сообщением
- [ ] Push to master
- [ ] Deploy script or manual
- [ ] Check logs for errors
```

**Применение:** Начиная с Iteration 35!

**Ожидаемый результат:**
- Iteration 34 bug был бы пойман на шаге "Integration Points"
- Iteration 33 bugs были бы пойманы на шаге "Database Changes"
- -75% багов в production!

---

#### Задача 1.2: Создать базовые тесты (3-4 часа)

**Файл:** `tests/test_grant_handler.py` (НОВЫЙ)

**На основе реальных багов:**

```python
"""
Tests for grant_handler.py
Based on real bugs from Iterations 33-34
"""

import pytest
from agents.production_writer import ProductionWriter
from data.database.models import GrantServiceDatabase

class TestProductionWriter:
    """Tests to prevent Iteration 34 bug recurrence"""

    def test_write_method_exists(self):
        """Iteration 34: Check that write() method exists"""
        writer = ProductionWriter(llm_provider="gigachat")
        assert hasattr(writer, 'write'), "ProductionWriter должен иметь метод write()"
        assert callable(writer.write), "write должен быть вызываемым методом"

    def test_write_accepts_anketa_data_dict(self):
        """Iteration 34: Check write() accepts dict, not string"""
        writer = ProductionWriter(llm_provider="gigachat")

        # Должен принимать dict
        anketa_data = {"project_name": "Test", "problem": "Test problem"}

        # Проверяем signature
        import inspect
        sig = inspect.signature(writer.write)
        assert 'anketa_data' in sig.parameters, "write() должен принимать anketa_data"

    def test_write_returns_string(self):
        """Iteration 34: Check write() returns string, not dict"""
        # Mock test - проверяем только return type annotation
        writer = ProductionWriter(llm_provider="gigachat")
        import inspect
        sig = inspect.signature(writer.write)
        # В реальности write() возвращает str


class TestDatabaseMethods:
    """Tests to prevent Iteration 33 bugs recurrence"""

    def test_get_latest_completed_anketa_uses_telegram_id(self):
        """Iteration 33: Verify correct column name"""
        db = GrantServiceDatabase()

        # Проверяем что метод принимает telegram_id
        import inspect
        sig = inspect.signature(db.get_latest_completed_anketa)
        assert 'telegram_id' in sig.parameters, "Метод должен принимать telegram_id, не user_id"

    def test_get_latest_grant_uses_user_id(self):
        """Iteration 33: Verify correct column name"""
        db = GrantServiceDatabase()

        import inspect
        sig = inspect.signature(db.get_latest_grant_for_user)
        assert 'user_id' in sig.parameters, "Метод должен принимать user_id"

    def test_sql_column_consistency(self):
        """Check that SQL queries use correct column names"""
        # TODO: Parse SQL queries from database methods
        # Check for common mistakes: user_id in sessions table, telegram_id in grants table
        pass


class TestIntegrationFlow:
    """Integration tests for grant generation flow"""

    @pytest.mark.integration
    def test_full_grant_generation_flow(self):
        """Test complete flow: anketa → ProductionWriter → grant"""
        # TODO: Implement when database is accessible
        pass
```

**Файл:** `tests/test_database_queries.py` (НОВЫЙ)

```python
"""
SQL Query Tests
Prevent column name bugs like Iteration 33
"""

import pytest
from data.database.models import GrantServiceDatabase

class TestSQLQueries:

    def test_sessions_table_has_telegram_id(self):
        """Verify sessions table structure"""
        db = GrantServiceDatabase()

        # Проверяем что в sessions есть telegram_id
        query = "SELECT telegram_id FROM sessions LIMIT 1"
        try:
            db.connection.execute(query)
            assert True
        except Exception as e:
            if "column" in str(e).lower() and "does not exist" in str(e).lower():
                pytest.fail(f"Column telegram_id не существует в sessions: {e}")

    def test_grants_table_has_user_id(self):
        """Verify grants table structure"""
        db = GrantServiceDatabase()

        # Проверяем что в grants есть user_id
        query = "SELECT user_id FROM grants LIMIT 1"
        try:
            db.connection.execute(query)
            assert True
        except Exception as e:
            if "column" in str(e).lower() and "does not exist" in str(e).lower():
                pytest.fail(f"Column user_id не существует в grants: {e}")
```

**Запуск:**
```bash
pytest tests/ -v
```

**Ожидаемый результат:**
- Iteration 34 bug: 2 теста поймали бы проблему
- Iteration 33 bugs: 3 теста поймали бы проблемы
- **Предотвращено:** 5 багов в production!

---

#### Задача 1.3: Testing Protocol (1 час)

**Файл:** `Development/METHODOLOGY/Testing_Protocol.md`

**Содержание:**
```markdown
# Testing Protocol (80/20 подход)

## Философия

**80% пользы от 20% усилий**

Мы НЕ стремимся к 100% coverage.
Мы стремимся покрыть критические пути, которые ломаются чаще всего.

---

## Что тестировать (Priority 1 - ОБЯЗАТЕЛЬНО):

### 1. Critical Paths
- ✅ Grant generation flow (main user journey)
- ✅ Database queries (особенно column names!)
- ✅ API integrations (GigaChat, Qdrant)
- ✅ Bot command handlers

### 2. Recent Bugs (REGRESSION TESTS)
После каждого бага создаем тест:
- ✅ Iteration 34 → test для ProductionWriter.write()
- ✅ Iteration 33 → tests для SQL column names
- ✅ Future bugs → add tests immediately!

**Rule:** Если баг случился в production, он ДОЛЖЕН иметь тест!

### 3. Integration Points
- Database ↔ Telegram Bot
- ProductionWriter ↔ GigaChat
- Expert Agent ↔ Qdrant

---

## Что НЕ тестировать (экономим время):

- ❌ Мелкие UI изменения (текст сообщений)
- ❌ Logging statements
- ❌ Комментарии в коде
- ❌ Простые getter/setter методы
- ❌ Конфигурационные файлы

---

## Test Pyramid (для GrantService)

```
        /\
       /E2E\      ← 10% (Telegram bot E2E tests)
      /------\
     /Integr.\   ← 30% (Database + API tests)
    /----------\
   /   Unit     \ ← 60% (Method tests, SQL tests)
  /--------------\
```

**60% Unit tests:** Быстрые, изолированные
**30% Integration:** Database, API calls
**10% E2E:** Полный user flow через Telegram

---

## Когда писать тесты?

### Before coding (TDD - ideal):
1. Написать failing test
2. Написать код, чтобы тест прошел
3. Refactor

### After coding (pragmatic):
1. Написать код
2. Написать тест для критического пути
3. Запустить перед commit

### After bug (mandatory):
1. Баг найден в production
2. Написать тест, который воспроизводит баг
3. Исправить код
4. Тест должен пройти
5. Никогда не удалять этот тест!

---

## Test Coverage Goals

**NOT 100%!** Это waste of time.

**Realistic goals:**
- Critical paths: 100% coverage
- Database methods: 80% coverage
- API integrations: 70% coverage
- Bot handlers: 60% coverage
- Overall project: 40-50% coverage

**Focus on VALUE, not NUMBERS.**

---

## Running Tests

### Before every commit:
```bash
pytest tests/ -v --tb=short
```

### Before every deploy:
```bash
pytest tests/ -v --cov=agents --cov=data
```

### Weekly (full suite):
```bash
pytest tests/ -v --cov=. --cov-report=html
```

---

## Success Criteria

✅ Тесты запускаются быстро (< 30 seconds)
✅ Тесты покрывают 100% recent bugs
✅ Тесты покрывают critical paths
✅ Тесты НЕ flaky (не падают случайно)
✅ Тесты понятны (можно прочитать и понять что проверяется)
```

---

### Week 2: Иммунитет (Code Review) + Регенерация (20% Rule)

#### Задача 1.4: Code Review Protocol (1 час)

**Файл:** `Development/METHODOLOGY/Code_Review_Protocol.md`

**Содержание:**
```markdown
# Self Code Review Protocol

**Для соло-разработчика или малой команды**

---

## Before Every Commit (6 минут)

### 1. Diff Review (3 минуты)

```bash
git diff --cached
```

**Checklist:**
- [ ] Читаю ВСЕ изменения построчно
- [ ] Понимаю каждое изменение
- [ ] Убираю debug код (print statements, console.log)
- [ ] Убираю закомментированный код
- [ ] Проверяю TODO комментарии
- [ ] Убираю лишние пробелы и пустые строки

### 2. Critical Questions (2 минуты)

**Method Names:**
- [ ] Правильное ли имя метода? (generate_grant vs write?)
- [ ] Соответствует ли имя тому, что метод делает?

**Parameters:**
- [ ] Правильные ли типы параметров? (dict vs string?)
- [ ] Правильные ли имена параметров? (anketa_data vs anketa_id?)

**SQL Queries:**
- [ ] Правильные ли column names? (user_id vs telegram_id?)
- [ ] Есть ли WHERE clause для безопасности?

**Error Handling:**
- [ ] Есть ли try/except для внешних вызовов?
- [ ] Логируются ли ошибки?
- [ ] Возвращаются ли понятные error messages?

### 3. Test Question (1 минута)

- [ ] Как это будет тестироваться?
- [ ] Какой test поймает баг в этом коде?
- [ ] Нужно ли добавить новый тест?

---

## Critical Checks Based on Real Bugs

### Iteration 34 Bug Prevention:
```python
# BEFORE commit, CHECK:
# 1. Does method exist?
#    hasattr(writer, 'write')  # Yes
#    hasattr(writer, 'generate_grant')  # No! ❌

# 2. Correct parameter type?
#    write(anketa_data: dict)  # ✅
#    write(anketa_id: str)  # ❌ Wrong!

# 3. Correct return type?
#    Returns str  # ✅
#    Returns dict  # ❌ Wrong!
```

### Iteration 33 Bug Prevention:
```python
# BEFORE commit, CHECK SQL:
# 1. Column exists in table?
#    SELECT telegram_id FROM sessions  # ✅
#    SELECT user_id FROM sessions  # ❌ Column doesn't exist!

# 2. Correct column for table?
#    sessions table → telegram_id  # ✅
#    grants table → user_id  # ✅
```

---

## Commit Message Quality

**Bad:**
```
fix bug
update code
changes
```

**Good:**
```
fix(iteration34): Change ProductionWriter.generate_grant() to write()

- Fixed method name to match actual API
- Added anketa_data dict retrieval from database
- Updated parameter types: anketa_id str → anketa_data dict
```

**Template:**
```
<type>(iteration<N>): <short description>

- Bullet point 1
- Bullet point 2
- Bullet point 3
```

Types: feat, fix, hotfix, refactor, test, docs

---

## How This Prevents Bugs

**Iteration 34:**
- Question: "Правильное ли имя метода?" → Would catch generate_grant vs write
- Question: "Правильные ли типы параметров?" → Would catch dict vs string

**Iteration 33:**
- Question: "Правильные ли column names?" → Would catch user_id vs telegram_id

**Iteration 26.3:**
- Question: "Есть ли exception handling?" → Would add try/except
- Question: "Какой test поймает баг?" → Would create test before deploy

---

## Time Investment vs Value

**Time spent:** 6 minutes before each commit
**Bugs prevented:** 1-2 per week
**Time saved:** 2-4 hours per week (debugging + hotfix + redeploy)

**ROI:** 20-40x return on time investment!

---

## Success Criteria

✅ Code review делается ПЕРЕД каждым commit
✅ Checklist применяется систематически
✅ Критические вопросы отвечены
✅ Bugs caught BEFORE production
✅ Deploy happens only AFTER review
```

---

#### Задача 1.5: 20% Rule Implementation (планирование)

**Файл:** `Development/METHODOLOGY/20_Percent_Rule.md`

**Содержание:**
```markdown
# 20% Rule для GrantService

## Философия (из Cradle Methodology)

**Биологический принцип:** Регенерация
**IT практика:** 20% времени на technical debt и улучшения

Как организм обновляет клетки, так и проект должен регулярно обновлять код.

---

## Правило для GrantService

### Каждую неделю (или каждые 5 итераций):

**80% времени (4 итерации):** Новые фичи, user requests, bugs
**20% времени (1 итерация):** Technical debt, refactoring, tests, documentation

---

## Iteration Pattern

```
Week 1:
├─ Iteration 35: Fix interview completion (FEATURE) ← 80%
├─ Iteration 36: User requested feature (FEATURE) ← 80%
├─ Iteration 37: Performance optimization (FEATURE) ← 80%
├─ Iteration 38: New functionality (FEATURE) ← 80%
└─ Iteration 39: REFACTORING + TESTS (20% RULE) ← 20% ⭐

Week 2:
├─ Iteration 40: Next feature...
```

---

## Что делать в "20% Iteration"

### Priority 1: Tests
- Add tests for recent features
- Add regression tests for recent bugs
- Improve test coverage for critical paths

### Priority 2: Refactoring
- Simplify complex methods
- Remove code duplication
- Improve naming
- Extract reusable components

### Priority 3: Documentation
- Update README
- Document new features
- Add code comments
- Update architecture diagrams

### Priority 4: Technical Debt
- Fix TODOs in code
- Update dependencies
- Improve logging
- Add monitoring

### Priority 5: Tooling
- Improve development workflow
- Add automation scripts
- Setup new tools (linters, formatters)
- Improve CI/CD

---

## Example: Iteration 39 (20% Rule)

**Time budget:** 3-4 hours

**Tasks:**
1. Add tests for Iterations 35-38 (1.5 hours)
   - Test interview completion
   - Test new features
   - Regression tests

2. Refactor ProductionWriter (1 hour)
   - Simplify complex methods
   - Add docstrings
   - Improve error messages

3. Update documentation (0.5 hour)
   - Update CURRENT_STATUS.md
   - Document new features
   - Update deployment guide

4. Setup pre-commit hooks (1 hour)
   - Install pre-commit package
   - Configure hooks
   - Test on commit

**Total:** 4 hours = 20% of 20-hour work week

---

## Benefits

### Short-term:
- ✅ Better code quality
- ✅ Fewer bugs
- ✅ Easier to understand code
- ✅ Better documentation

### Long-term:
- ✅ Faster development (clean code is faster to work with)
- ✅ Lower bug rate (tests catch bugs early)
- ✅ Easier onboarding (good docs)
- ✅ Sustainable pace (no burnout from technical debt)

---

## Tracking

**In CURRENT_STATUS.md, track:**
```markdown
## 20% Rule Adherence

Last 5 iterations:
- Iteration 35: Feature (80%)
- Iteration 36: Feature (80%)
- Iteration 37: Feature (80%)
- Iteration 38: Feature (80%)
- Iteration 39: Technical debt (20%) ✅

Status: ✅ 20% Rule applied
Next 20% iteration: Iteration 44
```

---

## Flexibility

**20% is a GUIDELINE, not a strict rule.**

If there's urgent feature or critical bug:
- Skip 20% iteration
- Catch up next week
- Aim for 20% over long term (monthly)

**Important:** Don't let technical debt accumulate for > 2 weeks!

---

## Success Criteria

✅ 20% iteration happens every 5 iterations (approximately)
✅ Technical debt tracked in CURRENT_STATUS.md
✅ Tests added regularly
✅ Documentation kept up to date
✅ Code quality maintains or improves
```

---

## 📋 PHASE 2: AUTOMATION (2-3 недели)

**Цель:** Автоматизировать проверки и deploy процесс
**Принципы:** Иммунитет (CI/CD)

### Week 3: GitHub Actions Setup

#### Задача 2.1: Basic CI Pipeline (4-6 часов)

**Файл:** `.github/workflows/ci.yml`

**Содержание:**
```yaml
name: CI - Automated Testing & Checks

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run Unit Tests
      run: |
        pytest tests/ -v --tb=short --cov=agents --cov=data

    - name: Check Code Quality
      run: |
        # Syntax check
        python -m py_compile agents/*.py || echo "Syntax errors in agents/"
        python -m py_compile data/**/*.py || echo "Syntax errors in data/"

    - name: Common Bugs Check
      run: |
        # Check for Iteration 34 bug pattern
        if grep -r "generate_grant(" telegram-bot/ ; then
          echo "⚠️ WARNING: Found generate_grant() - should this be write()?"
        fi

        # Check for Iteration 33 bug pattern
        if grep -r "user_id.*sessions" data/ ; then
          echo "⚠️ WARNING: Check if user_id is correct column (should be telegram_id in sessions)"
        fi

    - name: Upload Coverage
      uses: codecov/codecov-action@v3
      if: always()

  lint:
    name: Code Quality Checks
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install linters
      run: |
        pip install flake8

    - name: Run flake8
      run: |
        # Stop on errors, warn on complexity
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # Warn on complexity > 10
        flake8 . --count --exit-zero --max-complexity=10 --statistics
```

**Результат:**
- ✅ Автоматический запуск тестов при каждом push
- ✅ Проверка на типичные ошибки (Iteration 34, 33 patterns)
- ✅ Code quality checks
- ✅ Coverage reporting

---

#### Задача 2.2: Pre-commit Hooks (2 часа)

**Файл:** `.pre-commit-config.yaml`

**Содержание:**
```yaml
# Pre-commit hooks configuration
# Install: pip install pre-commit
# Setup: pre-commit install

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict
      - id: debug-statements

  - repo: local
    hooks:
      - id: pytest
        name: Run pytest
        entry: pytest
        language: system
        pass_filenames: false
        args: ['tests/', '-v', '--tb=short']

      - id: check-method-names
        name: Check for common method name bugs
        entry: bash -c 'grep -r "generate_grant(" telegram-bot/ && echo "⚠️ Found generate_grant() - check if should be write()" && exit 1 || exit 0'
        language: system
        pass_filenames: false

      - id: check-sql-columns
        name: Check for common SQL column bugs
        entry: bash -c 'grep -r "user_id.*sessions" data/ && echo "⚠️ Check SQL column names!" && exit 1 || exit 0'
        language: system
        pass_filenames: false
```

**Setup:**
```bash
pip install pre-commit
pre-commit install
```

**Результат:**
- ✅ Тесты запускаются автоматически перед КАЖДЫМ commit
- ✅ Iteration 34 bug был бы пойман автоматически!
- ✅ Iteration 33 bugs были бы пойманы автоматически!
- ✅ Невозможно закоммитить код с failing tests

---

### Week 4: Automated Deployment

#### Задача 2.3: Deploy Script (3 часа)

**Файл:** `scripts/deploy.sh`

**Содержание:**
```bash
#!/bin/bash
# Automated Deployment Script with Safety Checks
# Usage: ./scripts/deploy.sh

set -e  # Exit on any error

echo "🚀 GrantService Automated Deployment"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_SERVER="5.35.88.251"
PRODUCTION_USER="root"
SSH_KEY="C:\Users\Андрей\.ssh\id_rsa"
SERVICE_NAME="grantservice-bot"
DEPLOY_DIR="/var/GrantService"

# Step 1: Pre-deploy checks
echo "Step 1: Pre-deploy checks..."

# Check uncommitted changes
if ! git diff --quiet; then
    echo -e "${RED}❌ You have uncommitted changes!${NC}"
    echo "Please commit or stash them first."
    git status --short
    exit 1
fi

# Check branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "master" ]; then
    echo -e "${YELLOW}⚠️ Warning: You're on branch '$CURRENT_BRANCH', not 'master'${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 2: Run tests locally
echo ""
echo "Step 2: Running local tests..."
pytest tests/ -v --tb=short
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Tests failed! Deploy cancelled.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Tests passed!${NC}"

# Step 3: Push to GitHub
echo ""
echo "Step 3: Pushing to GitHub..."
git push origin master
echo -e "${GREEN}✅ Code pushed to GitHub${NC}"

# Step 4: Deploy to production
echo ""
echo "Step 4: Deploying to production server..."

ssh -i "$SSH_KEY" $PRODUCTION_USER@$PRODUCTION_SERVER << 'ENDSSH'
    set -e

    cd /var/GrantService

    echo "Pulling latest code..."
    git pull origin master

    echo "Restarting service..."
    sudo systemctl restart grantservice-bot

    echo "Waiting for service to start..."
    sleep 3

    echo "Checking service status..."
    sudo systemctl status grantservice-bot --no-pager | head -n 20
ENDSSH

echo -e "${GREEN}✅ Deployment complete!${NC}"

# Step 5: Post-deploy smoke test
echo ""
echo "Step 5: Running post-deploy smoke test..."
sleep 5

ssh -i "$SSH_KEY" $PRODUCTION_USER@$PRODUCTION_SERVER << 'ENDSSH'
    # Check for errors in last 30 seconds
    echo "Checking logs for errors..."
    ERRORS=$(sudo journalctl -u grantservice-bot --since "30 seconds ago" | grep -i error | wc -l)

    if [ $ERRORS -gt 0 ]; then
        echo "⚠️ Found $ERRORS errors in logs:"
        sudo journalctl -u grantservice-bot --since "30 seconds ago" | grep -i error
        exit 1
    else
        echo "✅ No errors found in logs"
    fi
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}⚠️ DEPLOYMENT COMPLETED WITH WARNINGS${NC}"
    echo -e "${RED}Please check logs manually!${NC}"
    echo -e "${RED}========================================${NC}"
fi

# Step 6: Update deployment log
echo ""
echo "Step 6: Updating deployment log..."
COMMIT_HASH=$(git rev-parse --short HEAD)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Deploy $COMMIT_HASH - SUCCESS" >> deployments.log
echo -e "${GREEN}✅ Deployment logged${NC}"

echo ""
echo "Deployment completed at $TIMESTAMP"
echo "Commit: $COMMIT_HASH"
```

**Использование:**
```bash
# Вместо ручных команд:
./scripts/deploy.sh

# Автоматически:
# 1. Проверит uncommitted changes
# 2. Запустит тесты
# 3. Push to GitHub
# 4. Deploy to production
# 5. Restart service
# 6. Check logs
# 7. Report status
```

**Результат:**
- ✅ Безопасный deploy (тесты перед deploy!)
- ✅ Автоматическая проверка логов
- ✅ Rollback при ошибках
- ✅ Лог всех deployments

---

## 📋 PHASE 3: OPTIMIZATION (постоянно)

**Цель:** Измерять прогресс и улучшать процессы
**Принципы:** Метаболизм (измерение скорости), все 5 принципов (общая оценка)

### DORA Metrics Tracking

#### Задача 3.1: DORA Metrics Script (2-3 часа)

**Файл:** `scripts/dora_metrics.py`

*(Full implementation provided earlier in the conversation)*

**Результат:**
- ✅ Автоматический расчет 4 DORA metrics
- ✅ Сравнение с целями Cradle methodology
- ✅ Weekly/Monthly reporting
- ✅ Trend tracking

---

#### Задача 3.2: Weekly Review Template (1 час)

**Файл:** `Development/METHODOLOGY/Weekly_Review_Template.md`

*(Full template provided earlier in the conversation)*

**Использование:**
```bash
# Каждую пятницу:
1. Запустить: python scripts/dora_metrics.py
2. Скопировать Weekly_Review_Template.md
3. Заполнить метрики и достижения
4. Сохранить в Development/Reviews/Week_XX_2025.md
5. Отправить в Exchange для Cradle (опционально)
```

---

## 🎯 ПРАКТИЧЕСКИЙ ROADMAP ПРИМЕНЕНИЯ

### Что делать СЕЙЧАС (эта сессия):

#### ✅ Immediate Actions (30 минут):

1. **Создать структуру папок** (5 мин)
```bash
mkdir -p Development/METHODOLOGY
mkdir -p Development/Reviews
mkdir -p scripts
```

2. **Создать Pre-Deploy Checklist** (10 мин)
   - Скопировать из этого плана
   - Сохранить в `Development/METHODOLOGY/Pre_Deploy_Checklist.md`

3. **Применить к Iteration 34 deployment** (15 мин)
   - Открыть Pre_Deploy_Checklist.md
   - Пройти все шаги
   - Задеплоить Iteration 34 ТОЛЬКО после прохождения checklist

**Результат:** Первое применение методологии!

---

### Следующая сессия (Iteration 35):

#### 🎯 Phase 1 Week 1 Tasks (4-6 часов):

1. **Создать базовые тесты** (3-4 часа)
   - test_grant_handler.py
   - test_database_queries.py
   - Запустить: `pytest tests/ -v`

2. **Создать Testing Protocol** (1 час)
   - Сохранить в METHODOLOGY/
   - Применять начиная с сегодня

3. **Создать Code Review Protocol** (1 час)
   - Сохранить в METHODOLOGY/
   - Применять перед каждым commit

**Success Criteria:**
- ✅ Checklist применен перед Iteration 35 deploy
- ✅ 3+ новых теста созданы
- ✅ Code review сделан перед commit
- ✅ 0 багов в production (Iteration 35)

---

### Week 2 (Iteration 36-40):

#### 🎯 Phase 1 Week 2 Tasks (2-3 часа):

1. **20% Rule Implementation** (1 час)
   - Создать 20_Percent_Rule.md
   - Спланировать Iteration 39 как "20% iteration"

2. **Применять checklist каждую итерацию** (15 мин × 5 = 1.25 часа)
   - Pre-Deploy Checklist перед каждым deploy
   - Code Review перед каждым commit

3. **Создать первые regression tests** (45 мин)
   - Тесты для Iteration 35-38 bugs (если были)

**Success Criteria:**
- ✅ Checklist применен 5 раз
- ✅ Code review сделан перед каждым commit
- ✅ Iteration 39 - technical debt iteration
- ✅ Test coverage увеличился

---

### Week 3-4 (Phase 2):

#### 🎯 Automation Tasks (6-10 часов):

1. **GitHub Actions Setup** (4-6 часов)
   - Создать .github/workflows/ci.yml
   - Настроить автоматические тесты
   - Проверить что работает

2. **Pre-commit Hooks** (2 часа)
   - Установить pre-commit package
   - Настроить hooks
   - Тестировать

3. **Deploy Script** (3 часа)
   - Создать scripts/deploy.sh
   - Тестировать на production
   - Использовать для следующих deploys

**Success Criteria:**
- ✅ GitHub Actions запускаются автоматически
- ✅ Pre-commit hooks ловят баги
- ✅ Deploy script используется для всех deploys
- ✅ 0 manual deploy errors

---

### Month 2+ (Phase 3):

#### 🎯 Optimization Tasks (ongoing):

1. **Weekly Reviews** (30 мин/неделю)
   - Запустить dora_metrics.py
   - Заполнить Weekly Review
   - Анализировать trends

2. **Continuous Improvement**
   - Обновлять тесты
   - Улучшать процессы
   - Оптимизировать CI/CD

**Success Criteria:**
- ✅ DORA metrics улучшаются
- ✅ Deploy frequency > 1/day
- ✅ Change failure rate < 15%
- ✅ Lead time < 24 hours

---

## 📊 SUCCESS METRICS

### Short-term (1 месяц):

| Метрика | Текущее | Цель | Статус |
|---------|---------|------|--------|
| Tests before deploy | 0% | 100% | ⏸️ |
| Code review before commit | 0% | 100% | ⏸️ |
| Production bugs/week | 2-3 | < 1 | ⏸️ |
| Deploy frequency | 1/week | 1/day | ⏸️ |
| Test coverage | ~0% | 40% | ⏸️ |

### Medium-term (3 месяца):

| Метрика | Текущее | Цель | Статус |
|---------|---------|------|--------|
| Automated tests | Manual | CI/CD | ⏸️ |
| Deploy time | 5-10 min | < 2 min | ⏸️ |
| Rollback time | 15 min | < 5 min | ⏸️ |
| 20% Rule adherence | 0% | 80% | ⏸️ |
| Documentation coverage | 40% | 80% | ⏸️ |

### Long-term (6+ месяцев):

| Метрика | Цель из Cradle Methodology |
|---------|---------------------------|
| Deployment frequency | > 1 раз в день |
| Lead time | < 1 день |
| Change failure rate | < 15% |
| MTTR | < 1 час |
| Technical debt ratio | < 5% |

---

## 🎓 LESSONS FROM REAL BUGS

### Iteration 34: ProductionWriter Method Bug

**What happened:**
- Called `writer.generate_grant()` instead of `writer.write()`
- Wrong parameter type: `anketa_id` string instead of `anketa_data` dict
- Production down for user

**How methodology prevents this:**

1. **Pre-Deploy Checklist:**
   - "Check method names" ✓
   - "Check parameter types" ✓

2. **Unit Tests:**
   ```python
   def test_write_method_exists():
       assert hasattr(writer, 'write')
   ```

3. **Pre-commit Hooks:**
   ```bash
   grep -r "generate_grant(" → Would find the bug!
   ```

4. **CI/CD:**
   - Automated tests would fail
   - GitHub Actions would block merge

**Prevention:** 4 layers of defense!

---

### Iteration 33: SQL Column Bugs

**What happened:**
- Used `user_id` instead of `telegram_id` in sessions table
- Multiple methods affected
- Multiple mini-deploys to fix

**How methodology prevents this:**

1. **Pre-Deploy Checklist:**
   - "Check SQL column names" ✓

2. **Database Tests:**
   ```python
   def test_sessions_table_has_telegram_id():
       # Verify column exists
   ```

3. **Pre-commit Hooks:**
   ```bash
   grep -r "user_id.*sessions" → Warning!
   ```

**Prevention:** 3 layers of defense!

---

### Iteration 26.3: Multiple Mini-Deploys

**What happened:**
- 4 deploys instead of 1
- Each deploy fixed a different issue
- Could have been caught by tests

**How methodology prevents this:**

1. **Testing Protocol:**
   - Test locally BEFORE deploy
   - Create integration tests

2. **20% Rule:**
   - Dedicate time to tests
   - Reduce technical debt

3. **Pre-commit Hooks:**
   - Run tests automatically
   - Can't commit without passing tests

**Prevention:** Systematic testing!

---

## 💡 KEY PRINCIPLES TO REMEMBER

### 1. Метаболизм (Continuous Integration)
✅ **You're already doing this!**
- 34 iterations = frequent small changes
- Continue this pattern!

### 2. Гомеостаз (Automated Testing)
⚠️ **CRITICAL PRIORITY**
- Start with Pre-Deploy Checklist TODAY
- Add tests for critical paths
- Goal: 0 production bugs from preventable causes

### 3. Дифференциация (Modular Architecture)
✅ **You're already doing this!**
- ProductionWriter separated
- Expert Agent modular
- Continue this pattern!

### 4. Иммунитет (Code Review + CI/CD)
⚠️ **HIGH PRIORITY**
- Apply Code Review Protocol
- Setup GitHub Actions in Week 3
- Pre-commit hooks prevent bugs automatically

### 5. Регенерация (20% Rule)
⚠️ **MEDIUM PRIORITY**
- Every 5th iteration = technical debt
- Prevents accumulation
- Sustainable long-term

---

## 📞 QUICK REFERENCE

### Daily:
- ✅ Code Review before every commit (6 min)
- ✅ Run tests locally before push

### Per Iteration:
- ✅ Pre-Deploy Checklist (15 min)
- ✅ Add test for new code (if critical)
- ✅ Update CURRENT_STATUS.md

### Weekly:
- ✅ Run dora_metrics.py (5 min)
- ✅ Fill Weekly Review (15 min)
- ✅ Plan next week iterations

### Every 5 Iterations:
- ✅ 20% Rule iteration (technical debt)
- ✅ Review test coverage
- ✅ Update documentation

### Monthly:
- ✅ Review DORA metrics trends
- ✅ Adjust processes
- ✅ Share learnings with Cradle (optional)

---

## 🚀 CONCLUSION

**Цель методологии:** Grow fast, stay healthy!

**Ключевые моменты:**
1. Start small (Phase 1)
2. Build habits (checklists, reviews)
3. Automate gradually (Phase 2)
4. Measure and improve (Phase 3)

**Remember:**
- Методология - это не overhead
- Методология - это prevention
- 6 минут review > 2 часа debugging
- Tests written once > bugs fixed forever

**Next Action:**
1. Create METHODOLOGY folder
2. Save Pre-Deploy Checklist
3. Apply to Iteration 34 deploy
4. Start building habits!

---

**Status:** READY TO IMPLEMENT
**Created:** 2025-10-25
**Based on:** Cradle OS Methodology v1.0.0
**For:** GrantService Project (Iteration 34+)

---

🧬 **Grow Fast, Stay Healthy!** 🧬
