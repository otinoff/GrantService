# GrantService: Lessons Learned & Project-Specific Best Practices

**Project:** GrantService - AI-powered Grant Application Generator
**Version:** 1.0.0
**Date:** 2025-10-27
**Status:** Living Document 📝
**Based on:** 53 Iterations of Real Development

> "Every bug is a lesson. Every iteration makes us stronger."

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Testing Lessons](#1-testing-lessons)
3. [AI/LLM Integration Lessons](#2-aillm-integration-lessons)
4. [Telegram Bot Lessons](#3-telegram-bot-lessons)
5. [Database Lessons](#4-database-lessons)
6. [Architecture Lessons](#5-architecture-lessons)
7. [Production Bugs Hall of Fame](#6-production-bugs-hall-of-fame)
8. [Iteration-Specific Lessons](#7-iteration-specific-lessons)
9. [Quick Decision Matrix](#8-quick-decision-matrix)

---

## Introduction

This document captures **real lessons learned** during GrantService development.

**Unlike generic best practices**, these are:
- ✅ Based on actual production bugs
- ✅ Tested in real bootcamp conditions
- ✅ Validated by manual and automated testing
- ✅ Specific to AI/Telegram/Grant domain

**Read this BEFORE starting similar projects.**

---

## 1. Testing Lessons

### 🎯 Lesson 1.1: Manual Testing First = 62x Slower

**What Happened (Iteration 52):**
```
Flow: Manual test → Bug found → Fix → Manual test again
Result: 5 bugs × 20 min/bug = 100 minutes wasted
```

**What We Should Do (Iteration 53):**
```
Flow: Automated tests → Fix all → Manual test once
Result: 96 seconds automated + 20 min manual = 22 minutes total
Time saved: 78 minutes (78% reduction)
```

**Rule:**
> **Automated integration tests FIRST, manual testing LAST.**

**Code Example:**
```python
# ❌ BAD: Manual testing first
def develop_feature():
    write_code()
    manual_test()  # ← Found bug 1
    fix_bug_1()
    manual_test()  # ← Found bug 2
    fix_bug_2()
    manual_test()  # ← Found bug 3
    # ... 5 times total!

# ✅ GOOD: Automated tests first
def develop_feature():
    write_code()
    write_integration_tests()  # ← Catches all structural bugs
    run_tests()  # ← 96 seconds
    fix_all_bugs()
    manual_test()  # ← Final smoke test only
```

---

### 🎯 Lesson 1.2: Production Parity in Tests

**What Happened:**
- Tests used `MockAgent` instead of `AuditorAgent`
- Production bug: `AuditorAgent.__init__()` requires `db` parameter
- Tests didn't catch it because they used mocks

**What We Learned:**
> **Tests must use the SAME imports as production code.**

**Code Example:**
```python
# ❌ BAD: Using mocks for structural tests
def test_auditor():
    auditor = MockAuditorAgent()  # ← Not real production code!
    result = auditor.audit(...)

# ✅ GOOD: Using real agents (production parity)
def test_auditor(test_db):
    from agents.auditor_agent import AuditorAgent  # ← Real import
    auditor = AuditorAgent(db=test_db)  # ← Real instantiation
    # Only mock LLM calls, everything else is real
```

**Rule:**
- Mock external APIs (GigaChat, Telegram)
- Use REAL agents, database, imports
- Test the actual code that runs in production

---

### 🎯 Lesson 1.3: Edge Cases Catch Production Bugs

**What Happened (Production Bug):**
```python
# Code expected dict:
for key, value in answers_data.items():  # ← CRASH!

# But database returned:
answers_data = None  # ← NULL in database!
```

**What We Learned:**
> **Edge case tests catch real production bugs that smoke tests miss.**

**Tests We Added (10 edge cases):**
```python
def test_null_answers_data():
    """Database returned NULL instead of dict"""

def test_empty_dict():
    """Empty {} dict"""

def test_wrong_type():
    """List instead of dict"""

def test_invalid_json():
    """JSON parse error"""

def test_missing_fields():
    """Required fields absent"""
```

**Rule:**
- Write edge case tests AFTER finding production bugs
- Each production bug = 1+ edge case test
- Test with real production data structures

---

## 2. AI/LLM Integration Lessons

### 🎯 Lesson 2.1: LLM Provider Switching is HARD

**What Happened:**
- Switched from Claude Code to GigaChat (Iteration 35)
- Had to update 47+ files
- Different APIs, different response formats
- 3 days of integration work

**What We Learned:**
> **Abstract LLM calls through UnifiedLLMClient from day 1.**

**Code Example:**
```python
# ❌ BAD: Direct LLM calls
def audit():
    response = gigachat.chat.completions.create(
        model="GigaChat-Max",
        messages=[...]
    )
    return response.choices[0].message.content

# ✅ GOOD: Unified client
def audit():
    response = self.llm_client.generate_response(
        prompt=prompt,
        model_params={"temperature": 0.7}
    )
    return response  # Same format for all providers
```

**Architecture:**
```python
class UnifiedLLMClient:
    def __init__(self, provider: str):
        if provider == "gigachat":
            self.client = GigaChatAPI()
        elif provider == "claude":
            self.client = ClaudeAPI()
        # ... more providers

    def generate_response(self, prompt: str, **kwargs) -> str:
        # Unified interface for all providers
        pass
```

**Rule:**
- Never call LLM APIs directly
- Always use abstraction layer
- Makes switching providers 10x easier

---

### 🎯 Lesson 2.2: Prompt Management in Database

**What Happened:**
- Prompts hardcoded in Python files
- To change prompt → redeploy application
- No A/B testing, no versioning

**What We Learned:**
> **Store prompts in database, not in code.**

**Database Schema:**
```sql
CREATE TABLE agent_prompts (
    id SERIAL PRIMARY KEY,
    agent_type VARCHAR(50),  -- 'auditor', 'writer', 'reviewer'
    prompt_key VARCHAR(100), -- 'goal', 'backstory', 'task'
    prompt_text TEXT,
    temperature FLOAT DEFAULT 0.7,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Code Example:**
```python
# ❌ BAD: Hardcoded prompts
AUDITOR_PROMPT = """
You are an expert auditor...
"""

# ✅ GOOD: Database prompts
def get_prompt(agent_type: str, prompt_key: str) -> str:
    return db.execute_query(
        "SELECT prompt_text FROM agent_prompts "
        "WHERE agent_type = %s AND prompt_key = %s",
        (agent_type, prompt_key)
    )
```

**Benefits:**
- Change prompts without redeployment ✅
- A/B test different prompts ✅
- Version history in database ✅
- Hot-reload prompts in production ✅

---

### 🎯 Lesson 2.3: LLM Calls are Expensive - Cache Everything

**What Happened:**
- Audit same anketa twice → 2× cost
- Generate same grant section twice → 2× cost
- No caching = wasted tokens

**What We Learned:**
> **Cache LLM responses aggressively.**

**Implementation:**
```python
class LLMCache:
    def __init__(self):
        self.cache = {}  # In production: Redis

    def get_or_generate(self, cache_key: str, generator_func):
        if cache_key in self.cache:
            logger.info(f"Cache HIT: {cache_key}")
            return self.cache[cache_key]

        logger.info(f"Cache MISS: {cache_key}")
        result = generator_func()
        self.cache[cache_key] = result
        return result

# Usage:
def audit_application(anketa_id: str):
    cache_key = f"audit:{anketa_id}:{hash(anketa_data)}"
    return cache.get_or_generate(
        cache_key,
        lambda: auditor.audit(anketa_data)
    )
```

**Cache Invalidation:**
```python
# Invalidate when anketa changes
def update_anketa(anketa_id: str, new_data: dict):
    db.update_anketa(anketa_id, new_data)
    cache.delete(f"audit:{anketa_id}:*")  # Clear all related
```

**Rule:**
- Cache by content hash, not just ID
- Invalidate on data changes
- Monitor cache hit rate (aim for >80%)

---

## 3. Telegram Bot Lessons

### 🎯 Lesson 3.1: Callback Queries Need update.effective_chat

**What Happened (Iteration 52, Phase 15):**
```python
# Code tried:
await update.message.reply_text("Hello")  # ← CRASH!
# Error: 'NoneType' object has no attribute 'reply_text'
```

**Why It Failed:**
- Callback queries don't have `update.message`
- They have `update.callback_query` instead

**What We Learned:**
> **Use update.effective_chat for compatibility with both message and callback.**

**Code Example:**
```python
# ❌ BAD: Works only for messages
async def handler(update, context):
    await update.message.reply_text("Hello")

# ✅ GOOD: Works for messages AND callbacks
async def handler(update, context):
    chat = update.effective_chat
    await context.bot.send_message(
        chat_id=chat.id,
        text="Hello"
    )
```

**Rule:**
- Always use `update.effective_chat`
- Never use `update.message` in shared handlers
- Test handlers with both message and callback_query

---

### 🎯 Lesson 3.2: Background Tasks Need Separate Update Object

**What Happened:**
```python
async def continue_interview(update, context):
    asyncio.create_task(run_interview())  # ← Background task
    # ... returns immediately

async def run_interview():
    # Later tries to use 'update'
    await update.message.reply_text("Done")  # ← CRASH!
    # Error: update is from different context
```

**What We Learned:**
> **Background tasks can't use the original update object.**

**Solution:**
```python
# ✅ Store what you need in interview dict
async def continue_interview(update, context):
    self.active_interviews[user_id] = {
        'chat_id': update.effective_chat.id,  # ← Store chat_id
        'user_id': user_id,
        'context': context  # ← Store context
    }

    asyncio.create_task(run_interview(user_id))

async def run_interview(user_id):
    interview = self.active_interviews[user_id]
    chat_id = interview['chat_id']
    context = interview['context']

    # Use stored context
    await context.bot.send_message(
        chat_id=chat_id,
        text="Done"
    )
```

**Rule:**
- Background tasks can't access original `update`
- Store `chat_id` and `context` in interview dict
- Use `context.bot.send_message()` with stored `chat_id`

---

### 🎯 Lesson 3.3: Double-Click Prevention

**What Happened:**
- User clicks "Начать аудит" button twice
- Two audit processes start
- Database race condition
- Wasted LLM tokens

**What We Learned:**
> **Implement double-click prevention for expensive operations.**

**Implementation:**
```python
class PipelineHandler:
    def __init__(self):
        self.active_operations = {}  # user_id → operation_type

    async def handle_start_audit(self, update, context):
        user_id = update.effective_user.id

        # Check if already running
        if user_id in self.active_operations:
            await update.callback_query.answer(
                "⏳ Аудит уже запущен, подождите...",
                show_alert=True
            )
            return

        # Mark as running
        self.active_operations[user_id] = "audit"

        try:
            # Run audit
            await run_audit(...)
        finally:
            # Clean up
            del self.active_operations[user_id]
```

**Rule:**
- Track active operations per user
- Show "already running" message
- Always clean up in `finally` block

---

## 4. Database Lessons

### 🎯 Lesson 4.1: NULL vs Empty String vs Missing Field

**What Happened (THE BIG BUG):**
```python
# Code expected:
answers_data = {"problem": "text"}

# Database returned:
answers_data = None  # ← NULL!

# Code crashed:
for key, value in answers_data.items():  # ← AttributeError!
```

**What We Learned:**
> **Always check data type before accessing methods.**

**Defensive Coding:**
```python
# ❌ BAD: Assumes dict
def process_data(data):
    for key, value in data.items():  # ← Assumes dict!
        print(key, value)

# ✅ GOOD: Checks type first
def process_data(data):
    if not data:
        data = {}
    if not isinstance(data, dict):
        data = {}

    for key, value in data.items():
        print(key, value)
```

**Database Query Pattern:**
```python
def get_anketa(anketa_id: str) -> dict:
    result = db.query("SELECT * FROM sessions WHERE anketa_id = %s", (anketa_id,))

    if not result:
        return {}  # Empty dict, not None

    # Parse JSON fields
    answers = result.get('answers_data')
    if isinstance(answers, str):
        try:
            answers = json.loads(answers)
        except:
            answers = {}

    if not isinstance(answers, dict):
        answers = {}

    return answers
```

**Rule:**
- Never trust database data types
- Always check `isinstance()` before calling methods
- Provide sensible defaults (empty dict, not None)

---

### 🎯 Lesson 4.2: JSONB vs TEXT for Complex Data

**What Happened:**
- Stored anketa as TEXT field
- Had to parse JSON every time
- No ability to query nested fields
- Migration to JSONB took 2 iterations

**What We Learned:**
> **Use JSONB from day 1 for complex structured data.**

**Schema Evolution:**
```sql
-- ❌ BAD: TEXT with JSON
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    interview_data TEXT  -- JSON as string
);

-- Query requires parsing:
SELECT * FROM sessions
WHERE interview_data::jsonb->>'problem' = 'test';  -- Slow!

-- ✅ GOOD: Native JSONB
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    interview_data JSONB  -- Native JSON type
);

-- Fast queries:
SELECT * FROM sessions
WHERE interview_data->>'problem' = 'test';  -- Fast!

-- Can create indexes:
CREATE INDEX idx_problem ON sessions
USING gin ((interview_data->'problem'));
```

**Benefits:**
- 10x faster queries ✅
- Can query nested fields ✅
- Automatic validation ✅
- Indexing support ✅

---

### 🎯 Lesson 4.3: Migration Strategy for Production

**What We Did (PostgreSQL Migration):**
```python
# Step 1: Add new JSONB columns (non-breaking)
ALTER TABLE sessions ADD COLUMN interview_data_jsonb JSONB;

# Step 2: Copy data (background process)
UPDATE sessions
SET interview_data_jsonb = interview_data::jsonb
WHERE interview_data_jsonb IS NULL;

# Step 3: Update code to use new column
# (Old code still works with TEXT column)

# Step 4: After validation, drop old column
ALTER TABLE sessions DROP COLUMN interview_data;
ALTER TABLE sessions RENAME COLUMN interview_data_jsonb TO interview_data;
```

**Rule:**
- Never drop columns immediately
- Add new, copy data, validate, then drop old
- Allow rollback at every step
- Monitor production during migration

---

## 5. Architecture Lessons

### 🎯 Lesson 5.1: When to Refactor (and When Not To)

**Iteration 53 Decision:**
- **Option A:** Full architecture migration (src/ layout, pydantic-settings)
  - Time: 3-4 weeks
  - Risk: High (breaking production)
  - Benefit: Clean architecture

- **Option B:** Minimal fixes only
  - Time: 1 week
  - Risk: Low
  - Benefit: Working features

**Decision: Option B** ✅

**Rationale:**
> **During bootcamp deadline: features > architecture.**

**When to Refactor:**
- ✅ After stable release
- ✅ When tech debt blocks features
- ✅ When team has 3+ weeks
- ❌ NOT during bootcamp/deadline
- ❌ NOT when production is working

**Technical Debt Matrix:**
```
High Impact, High Effort → Do after bootcamp
High Impact, Low Effort  → Do now
Low Impact, High Effort  → Never do
Low Impact, Low Effort   → Do when bored
```

---

### 🎯 Lesson 5.2: Separation of Concerns - Agent vs Handler

**What We Learned:**
> **Agents do business logic. Handlers do Telegram UI.**

**Bad Architecture (Iteration 26):**
```python
class InterviewerAgent:
    async def conduct_interview(self):
        # Sends Telegram messages directly ❌
        await bot.send_message(chat_id, "Question?")
        answer = await wait_for_answer()
        # Business logic mixed with UI!
```

**Good Architecture (Iteration 52):**
```python
class InterviewerAgent:
    async def conduct_interview(self, callback_ask_question):
        # Pure business logic ✅
        question = self.generate_question()
        answer = await callback_ask_question(question)  # Callback!
        return self.process_answer(answer)

class InterviewHandler:
    async def handle_interview(self, update, context):
        # UI logic ✅
        async def ask_question_callback(question: str):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=question
            )
            return await self.wait_for_answer()

        # Call agent with callback
        result = await agent.conduct_interview(ask_question_callback)
```

**Benefits:**
- Agent testable without Telegram ✅
- Can reuse agent in Web UI ✅
- Clear separation of concerns ✅

---

### 🎯 Lesson 5.3: Feature Flags for Incremental Rollout

**What We Should Have Done:**
```python
# Config
FEATURES = {
    'interactive_pipeline': True,  # Enable for all users
    'gigachat_max': False,  # Beta testing only
    'auto_researcher': True,
}

# Usage
if FEATURES['interactive_pipeline']:
    handler = InteractivePipelineHandler()
else:
    handler = OldPipelineHandler()
```

**Benefits:**
- Rollback without redeployment ✅
- A/B testing ✅
- Gradual rollout ✅

**Rule:**
- All major features behind flags
- Store flags in database or Redis
- Easy to toggle without code changes

---

## 6. Production Bugs Hall of Fame

### 🏆 Bug #1: The NULL answers_data Bug

**Impact:** ⭐⭐⭐⭐⭐ (Production down)

**What Happened:**
```python
# Expected:
answers_data = {"problem": "..."}

# Got:
answers_data = None

# Crashed:
for key, value in answers_data.items():  # AttributeError!
```

**Root Cause:**
- Data saved in `interview_data` field
- Code read from `answers_data` field (NULL)

**Fix:**
```python
# Fallback logic
if not answers_data or not isinstance(answers_data, dict):
    answers_data = anketa_data.get('interview_data', {})
```

**Lesson:** Always validate data types from database.

**Tests Added:** 10 edge case tests

---

### 🏆 Bug #2: The Background Task Update Bug

**Impact:** ⭐⭐⭐⭐ (Interview breaks)

**What Happened:**
```python
async def continue_interview(update, context):
    asyncio.create_task(run_interview())  # Background

async def run_interview():
    await update.message.reply_text("Done")  # ← CRASH!
    # Error: update is from different context
```

**Root Cause:**
- Background task tried to use original `update` object
- `update` only valid in original handler scope

**Fix:**
```python
# Store what we need
async def continue_interview(update, context):
    self.active[user_id] = {
        'chat_id': update.effective_chat.id,
        'context': context
    }

async def run_interview(user_id):
    data = self.active[user_id]
    await data['context'].bot.send_message(
        chat_id=data['chat_id'],
        text="Done"
    )
```

**Lesson:** Background tasks need separate context.

---

### 🏆 Bug #3: The Callback Query AttributeError

**Impact:** ⭐⭐⭐ (Buttons don't work)

**What Happened:**
```python
async def handle_button(update, context):
    await update.message.reply_text("Clicked")  # ← CRASH!
    # Error: Callback query has no 'message'
```

**Root Cause:**
- Callback queries use `update.callback_query`
- Not `update.message`

**Fix:**
```python
async def handle_button(update, context):
    chat = update.effective_chat  # ← Works for both!
    await context.bot.send_message(chat_id=chat.id, text="Clicked")
```

**Lesson:** Use `effective_chat` for compatibility.

---

## 7. Iteration-Specific Lessons

### Iteration 26: Hardcoded Questions Integration

**Lesson:**
> Reference point system is flexible but complex. Document state machine clearly.

**Files:**
- `reference_points/reference_point.py` - State machine
- Tests must cover all state transitions

---

### Iteration 35: GigaChat Integration

**Lesson:**
> Switching LLM providers takes 3 days. Use abstraction layer from start.

**Changes:**
- Created `UnifiedLLMClient`
- Updated 47+ files
- Migrated all prompts to database

---

### Iteration 52: Interactive Pipeline (5 Bugs Found)

**Lesson:**
> Manual testing first = inefficient. 5 rounds of manual testing wasted 100 minutes.

**Bugs:**
- Phase 12: `AttributeError` - method doesn't exist
- Phase 13: Finalize callback issue
- Phase 14: Database save error
- Phase 15: Background task update error
- Phase 15: Callback query issue

**Fix:** Iteration 53 with automated tests first

---

### Iteration 53: Testing Validation (SUCCESS)

**Lesson:**
> Automated tests catch bugs 62x faster than manual testing.

**Results:**
- 22 passing tests
- 1 production bug found and fixed by tests
- 96 seconds to run all tests
- 78 minutes saved vs manual approach

---

## 8. Quick Decision Matrix

### Should I Write Tests?

| Scenario | Write Tests? | Why |
|----------|-------------|-----|
| Adding new feature | ✅ YES | Catch bugs early |
| Fixing production bug | ✅ YES | Prevent regression |
| Refactoring code | ✅ YES | Ensure no breaks |
| Quick prototype | ❌ NO | Speed over quality |
| During bootcamp deadline | ⚠️ BASIC ONLY | Critical paths only |

---

### Should I Refactor?

| Tech Debt Impact | Effort Required | Decision |
|-----------------|----------------|----------|
| High | Low | ✅ Do now |
| High | High | ⏰ After release |
| Low | Low | 🤔 When bored |
| Low | High | ❌ Never |

---

### Should I Use Feature Flag?

| Feature Type | Use Flag? | Why |
|--------------|-----------|-----|
| Major new feature | ✅ YES | Gradual rollout |
| Bug fix | ❌ NO | Deploy immediately |
| Experimental | ✅ YES | Easy rollback |
| Breaking change | ✅ YES | Safety net |

---

## 9. Checklist for New Features

Before deploying new feature:

### Development Checklist
- [ ] Written integration tests (production parity)
- [ ] Added edge case tests for failure modes
- [ ] Tested with real production data structure
- [ ] Validated NULL/empty/missing field handling
- [ ] Documented in code with clear comments

### Testing Checklist
- [ ] Automated tests pass (>95% coverage critical paths)
- [ ] Manual smoke test in staging
- [ ] Tested double-click scenarios
- [ ] Tested concurrent user scenarios
- [ ] Load testing (if high traffic expected)

### Production Checklist
- [ ] Feature flag configured
- [ ] Monitoring/alerting set up
- [ ] Rollback plan documented
- [ ] Database migration tested
- [ ] Backup taken before deploy

### Post-Deploy Checklist
- [ ] Monitor logs for 24 hours
- [ ] Check error rates
- [ ] Validate database integrity
- [ ] User feedback collected
- [ ] Document lessons learned

---

## Conclusion

**Top 3 Lessons:**

1. **Test First, Manual Last** - Saves 78% of debugging time
2. **Production Parity in Tests** - Catches real bugs, not mock bugs
3. **Never Trust Database Types** - Always validate before accessing

**Next Steps:**

Read these documents:
- `SOFTWARE-DEVELOPMENT-BEST-PRACTICES.md` - General practices
- `TESTING-METHODOLOGY.md` - Testing strategies
- This file - GrantService-specific lessons

**Remember:**
> "Code without tests is legacy code."
> "Every production bug deserves an edge case test."
> "When in doubt, test it out."

---

**Maintained by:** GrantService Team
**Last Updated:** 2025-10-27 (Iteration 53)
**Status:** Living Document - Updated after each major iteration

**Contributing:**
- Found a new bug? → Add to "Production Bugs Hall of Fame"
- Learned a lesson? → Add to relevant section
- Solved a hard problem? → Document the solution

**END OF DOCUMENT**
