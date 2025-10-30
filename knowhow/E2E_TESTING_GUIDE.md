# E2E Testing Guide for GrantService

**Version:** 1.0.0
**Created:** 2025-10-29
**Iteration:** 66 - E2E Test Suite

---

## 📋 Overview

This guide documents the modular E2E testing architecture created in Iteration 66.

**Problem:**
- 66 iterations of development
- Tests scattered across iterations
- Difficult to reuse successful test patterns
- No centralized E2E validation

**Solution:**
- Modular test architecture (`tests/e2e/modules/`)
- Each module tests ONE production agent
- Main E2E test assembles modules into workflow
- Based on proven success patterns from iterations 54, 58, 60, 63, 65

---

## 🏗️ Architecture

### Directory Structure

```
tests/e2e/
├── modules/                      # Reusable test modules
│   ├── __init__.py
│   ├── interviewer_module.py     # Tests InteractiveInterviewerV2
│   ├── auditor_module.py         # Tests AuditorAgentClaude
│   ├── researcher_module.py      # Tests ResearcherAgent
│   ├── writer_module.py          # Tests WriterAgentV2
│   └── reviewer_module.py        # Tests ReviewerAgent
└── test_grant_workflow.py        # Main E2E test (assembles modules)
```

### Design Principles

1. **Test What You Run, Run What You Test**
   - All modules import PRODUCTION agents
   - No mocks, no synthetic workarounds
   - Test actual code paths used in production

2. **Modular Composition**
   - Each module is standalone
   - Modules can be reused in different test scenarios
   - Easy to test individual agents or full workflow

3. **Based on Proven Success**
   - Each module based on successful iteration
   - Incorporates critical fixes discovered in iterations
   - Validated against TESTING-METHODOLOGY.md

---

## 🧩 Test Modules

### 1. InterviewerTestModule

**Source:** Iteration 63 (Interactive Interview)

**Tests:** `agents.interactive_interviewer_v2.InteractiveInterviewerV2`

**Method:** `run_automated_interview(telegram_id, username, llm_provider)`

**What it does:**
1. Imports PRODUCTION InteractiveInterviewerV2
2. Runs interview with automated LLM responses
3. Records questions to `interview_questions` table
4. Records answers to `sessions.answers_data` (JSONB)

**Success Criteria:**
- ✅ >= 14 questions asked
- ✅ >= 5000 total characters in answers
- ✅ Questions saved to DB
- ✅ Session created with valid anketa_id

**Key Feature:** Falls back to SyntheticUserSimulator if `run_interview_automated` method doesn't exist

**Usage:**
```python
from tests.e2e.modules import InterviewerTestModule

interviewer = InterviewerTestModule(db)
anketa_data = await interviewer.run_automated_interview(
    telegram_id=999999001,
    username="test_user",
    llm_provider="gigachat"
)
```

**Returns:**
```python
{
    'anketa_id': '#ANKETA-...',
    'user_answers': {...},
    'questions_count': 15,
    'session_id': 123,
    'total_chars': 6234
}
```

---

### 2. AuditorTestModule

**Source:** Iteration 54 (Auditor Fix)

**Tests:** `agents.auditor_agent_claude.AuditorAgentClaude`

**Method:** `test_auditor(anketa_data, llm_provider)`

**What it does:**
1. Imports PRODUCTION AuditorAgentClaude
2. Calls `audit_anketa()` with anketa data
3. **Unwraps BaseAgent result** (critical fix from Iteration 54!)
4. Validates completeness score > 0
5. Saves to `auditor_results` table

**Success Criteria:**
- ✅ Completeness score > 0
- ✅ Missing fields identified
- ✅ Critical issues flagged
- ✅ Audit saved to DB

**Critical Fix (Iteration 54):**
```python
# AuditorAgent may return nested {'result': {...}}
if 'result' in audit_result:
    audit_data = audit_result['result']  # Unwrap!
else:
    audit_data = audit_result
```

**Usage:**
```python
from tests.e2e.modules import AuditorTestModule

auditor = AuditorTestModule(db)
audit_data = await auditor.test_auditor(
    anketa_data=anketa_data,
    llm_provider="gigachat"
)
```

---

### 3. ResearcherTestModule

**Source:** Iteration 60 (Researcher WebSearch Fix)

**Tests:** `agents.researcher_agent.ResearcherAgent`

**Method:** `test_researcher(anketa_data, llm_provider)`

**What it does:**
1. Imports PRODUCTION ResearcherAgent
2. Calls `research_anketa()` with **WebSearch enabled**
3. Validates >= 3 sources found
4. Saves to `researcher_research` table

**Success Criteria:**
- ✅ >= 3 sources from WebSearch
- ✅ Research has key sections (problem_analysis, target_audience, similar_projects)
- ✅ Sources have valid URLs
- ✅ Research saved to DB

**Important:** Must use LLM provider with WebSearch support (e.g., `claude_code`)

**Usage:**
```python
from tests.e2e.modules import ResearcherTestModule

researcher = ResearcherTestModule(db)
research_data = await researcher.test_researcher(
    anketa_data=anketa_data,
    llm_provider="claude_code"  # WebSearch enabled!
)
```

---

### 4. WriterTestModule

**Source:** Iteration 65 (Writer Key Fix)

**Tests:** `agents.writer_agent_v2.WriterAgentV2`

**Method:** `test_writer(anketa_data, research_data, llm_provider)`

**What it does:**
1. Imports PRODUCTION WriterAgentV2
2. Calls `write_application_async()` with anketa + research
3. **Extracts from `result['application']`** (critical fix from Iteration 65!)
4. Validates grant >= 15000 characters
5. Validates no TODO/INSERT placeholders
6. Saves to `grants` table

**Success Criteria:**
- ✅ Grant >= 15000 characters
- ✅ Has required sections (ОПИСАНИЕ ПРОБЛЕМЫ, ЦЕЛИ И ЗАДАЧИ, МЕРОПРИЯТИЯ, БЮДЖЕТ)
- ✅ No unfinished parts (TODO/INSERT)
- ✅ Grant saved to DB

**Critical Fix (Iteration 65):**
```python
# WriterAgent returns 'application' key, NOT 'grant_text'!
grant_text = writer_result.get('application',
    writer_result.get('grant_text',
        writer_result.get('result', {}).get('text', '')))
```

**This fix is ENFORCED in the module** - if you see empty grants, check this!

**Usage:**
```python
from tests.e2e.modules import WriterTestModule

writer = WriterTestModule(db)
grant_data = await writer.test_writer(
    anketa_data=anketa_data,
    research_data=research_data,
    llm_provider="gigachat"
)
```

---

### 5. ReviewerTestModule

**Source:** Iteration 58 (Reviewer Agent)

**Tests:** `agents.reviewer_agent.ReviewerAgent`

**Method:** `test_reviewer(grant_data, llm_provider)`

**What it does:**
1. Imports PRODUCTION ReviewerAgent
2. Calls `review_grant()` with grant text
3. Validates review has strengths/weaknesses/recommendations
4. Validates review score > 0
5. Saves to `reviewer_reviews` table

**Success Criteria:**
- ✅ Review score > 0
- ✅ Has strengths (list)
- ✅ Has weaknesses (list)
- ✅ Has recommendations (list)
- ✅ Review saved to DB

**Usage:**
```python
from tests.e2e.modules import ReviewerTestModule

reviewer = ReviewerTestModule(db)
review_data = await reviewer.test_reviewer(
    grant_data=grant_data,
    llm_provider="gigachat"
)
```

---

## 🔄 Complete E2E Workflow

The main E2E test (`test_grant_workflow.py`) assembles all modules:

```python
from tests.e2e.modules import (
    InterviewerTestModule,
    AuditorTestModule,
    ResearcherTestModule,
    WriterTestModule,
    ReviewerTestModule
)

class E2EGrantWorkflowTest:
    async def run_workflow(self):
        # STEP 1: Interview
        anketa_data = await self.interviewer.run_automated_interview(...)

        # STEP 2: Audit
        audit_data = await self.auditor.test_auditor(anketa_data, ...)

        # STEP 3: Research
        research_data = await self.researcher.test_researcher(anketa_data, ...)

        # STEP 4: Write
        grant_data = await self.writer.test_writer(anketa_data, research_data, ...)

        # STEP 5: Review
        review_data = await self.reviewer.test_reviewer(grant_data, ...)

        return results
```

---

## 🚀 Running Tests

### Run Full E2E Workflow

```bash
# Using pytest
python -m pytest tests/e2e/test_grant_workflow.py -v -s

# Or directly
python tests/e2e/test_grant_workflow.py
```

### Run Individual Module

```python
# Example: Test only WriterAgent
import asyncio
from data.database.models import GrantServiceDatabase
from tests.e2e.modules import WriterTestModule

async def test_writer_only():
    db = GrantServiceDatabase()
    writer = WriterTestModule(db)

    # Prepare test data
    anketa_data = {...}
    research_data = {...}

    grant_data = await writer.test_writer(anketa_data, research_data)
    print(f"Grant ID: {grant_data['grant_id']}")

asyncio.run(test_writer_only())
```

---

## 📂 Artifacts

Each test run creates artifacts directory:

```
iterations/Iteration_66_E2E_Test_Suite/artifacts/run_YYYYMMDD_HHMMSS/
├── step1_anketa.txt          # Interview results
├── step2_audit.txt           # Audit results
├── step3_research.txt        # Research results
├── step4_grant.txt           # Grant application
├── step5_review.txt          # Review results
└── SUMMARY.txt               # Test summary
```

---

## ✅ Validation Checklist

Before committing new E2E tests:

- [ ] Test uses PRODUCTION imports (no mocks)
- [ ] Success criteria from successful iteration
- [ ] Saves to production database tables
- [ ] Exports artifacts for manual inspection
- [ ] Validates against known issues (e.g., Iteration 65 key fix)
- [ ] Follows modular architecture (one module = one agent)

---

## 🔧 Common Issues

### Issue 1: Empty Grant Files

**Symptom:** Grant text is empty or "N/A"

**Cause:** WriterAgent returns `result['application']` not `result['grant_text']` (Iteration 65)

**Fix:** WriterTestModule already enforces correct key extraction - check if you're using the module!

### Issue 2: Audit Returns Nested Structure

**Symptom:** `audit_result['completeness_score']` raises KeyError

**Cause:** AuditorAgent wraps result in `{'result': {...}}` (Iteration 54)

**Fix:** AuditorTestModule already unwraps - check if you're using the module!

### Issue 3: Research Has No Sources

**Symptom:** `research_data['sources']` is empty

**Cause:** LLM provider doesn't support WebSearch

**Fix:** Use `llm_provider="claude_code"` for ResearcherAgent

---

## 📚 Related Documents

- **TESTING-METHODOLOGY.md** - Testing principles followed
- **SOFTWARE-DEVELOPMENT-BEST-PRACTICES.md** - General best practices
- **ITERATION_LEARNINGS.md** - Lessons from 66 iterations

---

## 🎯 Future Improvements

1. **Add Pre-Flight Health Checks**
   - Check GigaChat API availability
   - Check Claude Code API availability
   - Check Database connectivity
   - Check Qdrant vector DB

2. **CI/CD Integration**
   - Add GitHub Actions workflow
   - Run nightly E2E tests
   - Upload artifacts on failure

3. **Performance Metrics**
   - Track execution time per step
   - Monitor token usage
   - Identify bottlenecks

4. **Error Recovery**
   - Retry logic for transient failures
   - Checkpoint system to resume from failure
   - Better error messages

---

**Created:** 2025-10-29
**Author:** Claude Code
**Iteration:** 66 - E2E Test Suite
**Status:** Production Ready
