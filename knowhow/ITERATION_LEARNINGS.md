# Iteration Learnings - GrantService

**Purpose:** Central repository of lessons learned from 66+ iterations

**Created:** 2025-10-29

---

## 📚 Index by Iteration

| Iteration | Topic | Key Learning |
|-----------|-------|--------------|
| **54** | Auditor Fix | AuditorAgent wraps result in `{'result': {...}}` - must unwrap |
| **58** | Reviewer Agent | Review must have strengths/weaknesses/recommendations fields |
| **60** | Researcher WebSearch | ResearcherAgent requires WebSearch-enabled LLM (claude_code) |
| **63** | Interactive Interview | InteractiveInterviewerV2 with automated LLM responses |
| **64** | E2E Pipeline Issues | Empty grant files - WriterAgent key mismatch |
| **65** | Writer Key Fix | WriterAgent returns `result['application']` NOT `result['grant_text']` |
| **66** | E2E Test Suite | Modular test architecture for reusable agent testing |

---

## 🔥 Critical Issues & Fixes

### Issue 1: Empty Grant Files (Iterations 64-65)

**Symptom:**
```python
# Grant files had 0 characters, only headers
grant_text = "N/A"
```

**Root Cause:**
WriterAgent returns different keys than expected:
```python
# Script expected:
writer_result['grant_text']  # ❌ WRONG

# WriterAgent actually returns:
writer_result['application']  # ✅ CORRECT
```

**Discovery Method:**
Created `test_writer_isolated.py` to inspect actual result structure:
```python
result = await writer.write_application_async(input_data)
print(f"Keys: {result.keys()}")
# Output: dict_keys(['status', 'application', 'structure', 'quality_score'])
```

**Fix (Iteration 65):**
```python
# Robust key extraction with fallbacks
grant_text = writer_result.get('application',
    writer_result.get('grant_text',
        writer_result.get('result', {}).get('text', '')))
```

**Prevention:**
- WriterTestModule enforces correct key extraction
- Always use test modules instead of ad-hoc code

---

### Issue 2: Nested Audit Results (Iteration 54)

**Symptom:**
```python
# KeyError when accessing audit fields
audit_result['completeness_score']  # ❌ KeyError
```

**Root Cause:**
AuditorAgent wraps result in BaseAgent response structure:
```python
{
    'status': 'success',
    'result': {
        'completeness_score': 0.85,
        'missing_fields': [...],
        ...
    }
}
```

**Fix:**
```python
# Unwrap BaseAgent result
if isinstance(audit_result, dict):
    if 'result' in audit_result:
        audit_data = audit_result['result']  # Unwrap!
    else:
        audit_data = audit_result
```

**Prevention:**
- AuditorTestModule handles unwrapping automatically
- Always use test modules for consistent behavior

---

### Issue 3: Research Without Sources (Iteration 60)

**Symptom:**
```python
research_data['sources'] = []  # Empty!
```

**Root Cause:**
ResearcherAgent requires WebSearch-enabled LLM provider:
```python
# ❌ WRONG: GigaChat doesn't support WebSearch
researcher = ResearcherAgent(llm_provider="gigachat")

# ✅ CORRECT: Claude Code has WebSearch
researcher = ResearcherAgent(llm_provider="claude_code")
```

**Fix:**
Always use `claude_code` for ResearcherAgent:
```python
research_data = await researcher.research_anketa(
    anketa_input,
    llm_provider="claude_code"  # WebSearch enabled!
)
```

**Prevention:**
- ResearcherTestModule defaults to `claude_code`
- Document WebSearch requirement in module docstring

---

## 🏗️ Architectural Insights

### Insight 1: Modular Testing (Iteration 66)

**Problem:**
- 66 iterations, tests scattered everywhere
- Difficult to reuse successful patterns
- Each iteration reinvents testing approach

**Solution:**
Modular test architecture:
```
tests/e2e/modules/
├── interviewer_module.py  # Reusable test component
├── auditor_module.py
├── researcher_module.py
├── writer_module.py
└── reviewer_module.py
```

**Benefits:**
1. Each module tests ONE production agent
2. Modules incorporate fixes from successful iterations
3. Easy to compose modules into E2E workflows
4. Easy to test individual agents in isolation

**Pattern:**
```python
# Bad: Monolithic test
def test_e2e():
    # 500 lines of mixed logic...

# Good: Modular composition
def test_e2e():
    anketa = await interviewer.run_automated_interview(...)
    audit = await auditor.test_auditor(anketa, ...)
    research = await researcher.test_researcher(anketa, ...)
    grant = await writer.test_writer(anketa, research, ...)
    review = await reviewer.test_reviewer(grant, ...)
```

---

### Insight 2: Test What You Run (Iteration 66)

**Principle (from TESTING-METHODOLOGY.md):**
> The testing environment must mirror production

**Application:**
```python
# ❌ BAD: Test uses mocks
@mock.patch('agents.writer_agent_v2.WriterAgentV2')
def test_writer(mock_writer):
    mock_writer.return_value = {"grant_text": "test"}

# ✅ GOOD: Test uses production code
from agents.writer_agent_v2 import WriterAgentV2
async def test_writer():
    writer = WriterAgentV2(db, llm_provider="gigachat")
    result = await writer.write_application_async(input_data)
```

**Key Rules:**
1. Import PRODUCTION agents, not test doubles
2. Use real database (port 5434)
3. Use real LLM APIs (GigaChat, Claude Code)
4. No mocks unless absolutely necessary

---

### Insight 3: Production Parity Prevents Surprises

**Example from Iteration 64:**
```python
# Test used SyntheticUserSimulator
# But production uses InteractiveInterviewerV2
# → No coverage of production code path!
```

**Correct Approach (Iteration 66):**
```python
# Test PRODUCTION InteractiveInterviewerV2
from agents.interactive_interviewer_v2 import InteractiveInterviewerV2

interviewer = InteractiveInterviewerV2(db, llm_provider="gigachat")
anketa = await interviewer.run_interview_automated(
    telegram_id=telegram_id,
    username=username,
    auto_answer=True  # Automated mode for testing
)
```

**Lesson:**
If you have automated workaround (SyntheticUserSimulator) and production code (InteractiveInterviewer), you must test BOTH:
1. Test production code with automated responses
2. Use workaround only as fallback

---

## 🎯 Testing Patterns

### Pattern 1: Isolated Testing for Diagnosis

**Use Case:** Agent returns unexpected structure

**Method:**
```python
# Create minimal isolated test
# File: test_writer_isolated.py

async def test_writer_keys():
    writer = WriterAgentV2(db, llm_provider="gigachat")
    result = await writer.write_application_async(input_data)

    print(f"Result keys: {result.keys()}")
    print(f"Result type: {type(result)}")

    # Inspect actual structure
    import json
    print(json.dumps(result, indent=2, default=str))
```

**Benefits:**
- Fast feedback loop
- No interference from other components
- Easy to share for debugging

---

### Pattern 2: Module-Based Testing

**Use Case:** Reusable test components

**Structure:**
```python
class AgentTestModule:
    """Reusable test module for ONE agent"""

    def __init__(self, db):
        self.db = db

    async def test_agent(self, input_data, llm_provider):
        """Test production agent with validation"""
        # 1. Import PRODUCTION agent
        from agents.my_agent import MyAgent

        # 2. Run agent
        agent = MyAgent(self.db, llm_provider=llm_provider)
        result = await agent.process(input_data)

        # 3. Validate
        self._validate_result(result)

        # 4. Save to DB
        self._save_to_db(result)

        # 5. Return structured data
        return {...}

    def export_to_file(self, data, filepath):
        """Export for manual inspection"""
        ...
```

---

### Pattern 3: Progressive Validation

**Problem:** E2E test fails, but which step?

**Solution:** Validate + save after EACH step:
```python
async def run_workflow(self):
    # Step 1
    anketa = await interviewer.run_automated_interview(...)
    self._validate_anketa(anketa)  # Fail fast!
    self._save_artifact('step1_anketa.txt', anketa)

    # Step 2
    audit = await auditor.test_auditor(anketa, ...)
    self._validate_audit(audit)  # Fail fast!
    self._save_artifact('step2_audit.txt', audit)

    # ... etc
```

**Benefits:**
- Know exactly which step failed
- Artifacts for manual inspection
- Easy to resume from checkpoint

---

## 📊 Success Criteria by Agent

### InteractiveInterviewerV2
- ✅ >= 14 questions asked
- ✅ >= 5000 total characters
- ✅ Questions saved to `interview_questions` table
- ✅ Answers saved to `sessions.answers_data` (JSONB)

### AuditorAgentClaude
- ✅ Completeness score > 0
- ✅ Missing fields identified (list)
- ✅ Critical issues flagged (list)
- ✅ Audit saved to `auditor_results` table

### ResearcherAgent
- ✅ >= 3 sources from WebSearch
- ✅ Has key sections (problem_analysis, target_audience, similar_projects)
- ✅ Sources have valid URLs
- ✅ Research saved to `researcher_research` table

### WriterAgentV2
- ✅ Grant >= 15000 characters
- ✅ Has required sections (ОПИСАНИЕ ПРОБЛЕМЫ, ЦЕЛИ И ЗАДАЧИ, МЕРОПРИЯТИЯ, БЮДЖЕТ)
- ✅ No TODO/INSERT placeholders
- ✅ Grant saved to `grants` table

### ReviewerAgent
- ✅ Review score > 0
- ✅ Has strengths (non-empty list)
- ✅ Has weaknesses (non-empty list)
- ✅ Has recommendations (non-empty list)
- ✅ Review saved to `reviewer_reviews` table

---

## 🚨 Common Pitfalls

### Pitfall 1: Using Mocks in Integration Tests

**Why it's bad:**
- Test passes but production fails
- Misses real API behavior
- Creates false confidence

**Example:**
```python
# ❌ BAD
@mock.patch('agents.writer_agent_v2.WriterAgentV2.write_application_async')
async def test_writer(mock_write):
    mock_write.return_value = {"grant_text": "test"}
    # Test passes, but you didn't test WriterAgent!

# ✅ GOOD
async def test_writer():
    writer = WriterAgentV2(db, llm_provider="gigachat")
    result = await writer.write_application_async(input_data)
    # Tests REAL WriterAgent behavior
```

---

### Pitfall 2: Ignoring Database State

**Why it's bad:**
- Tests pass in isolation but fail when run together
- Flaky tests due to shared state

**Solution:**
```python
# Create test users with unique IDs
telegram_id = 999999000 + test_run_id

# Or use DB transactions with rollback
with db.connect() as conn:
    cursor = conn.cursor()
    try:
        # Run test
        ...
        conn.rollback()  # Don't persist test data
    finally:
        cursor.close()
```

---

### Pitfall 3: Hardcoded Test Data

**Why it's bad:**
- Tests break when data format changes
- Difficult to test edge cases

**Solution:**
```python
# ❌ BAD: Hardcoded
anketa_data = {
    "anketa_id": "#ANKETA-123",
    "user_answers": {"name": "Test", ...}
}

# ✅ GOOD: Use production data generator
from tests.e2e.modules import InterviewerTestModule
interviewer = InterviewerTestModule(db)
anketa_data = await interviewer.run_automated_interview(...)
# Uses REAL InteractiveInterviewer logic!
```

---

## 📝 Documentation Standards

### Standard 1: Module Docstrings

Every test module must have:
```python
"""
AgentTestModule - Testing PRODUCTION AgentName

Source: Iteration XX (Feature Name)
Tests: Production AgentClass
Critical: Key fix or validation

Iteration 66: E2E Test Suite
"""
```

### Standard 2: Method Docstrings

Every test method must document:
```python
async def test_agent(self, input_data, llm_provider):
    """
    Test PRODUCTION Agent

    What it does:
    1. Step one
    2. Step two
    3. ...

    Args:
        input_data: Description
        llm_provider: Description

    Returns:
        Dict with:
            - field1: description
            - field2: description

    Raises:
        ValueError: When validation fails
    """
```

---

## 🔮 Future Learnings Template

When adding new iteration learnings:

```markdown
### Issue/Insight: [Title]

**Symptom:**
[What did you observe?]

**Root Cause:**
[Why did it happen?]

**Fix:**
```python
# Code example
```

**Prevention:**
[How to avoid in future?]
```

---

**Version:** 1.0.0
**Last Updated:** 2025-10-29
**Total Iterations Covered:** 66
**Status:** Living Document (add learnings as you go!)
