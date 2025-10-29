# Iteration 64: Full E2E Pipeline (Steps 2-5)

**Date:** 2025-10-29 02:25 MSK
**Status:** 🔧 IN PROGRESS
**Priority:** 🔥 CRITICAL (буткемп Сбера - deadline 30 октября)
**Parent:** Iteration 63 - E2E Synthetic Workflow (Step 1)

---

## 🎯 Goal

Доделать полный E2E pipeline: добавить Steps 2-5 для генерации **25 файлов** (5 анкет × 5 этапов).

**Deadline:** 30 октября (завтра) для сдачи на буткемп Сбера 1 ноября.

---

## 📊 Current Status

**Iteration 63 Result:**
- ✅ Step 1 (GENERATE): 5 anketa files
- ❌ Steps 2-5: Not implemented

**Need:**
- Step 2 (AUDIT): 5 audit files
- Step 3 (RESEARCH): 5 research files
- Step 4 (WRITER): 5 grant files
- Step 5 (REVIEW): 5 review files

**Total:** 25 files (5 already exist)

---

## 🎯 Solution

### Step 2: Audit Integration

**Agent:** `AuditorAgentClaude`
**Method:** `evaluate_project_async(project_data: Dict)`

**Input:** Load session answers_data from DB
**Output:** Save to audits table + export to `audit_*.txt`

**Format project_data:**
```python
project_data = {
    "название": f"Проект {anketa_id}",
    "проблема": answers['problem'],
    "решение": answers['solution'],
    "цели": answers['goals'],
    "мероприятия": answers['activities'],
    "результаты": answers['results'],
    "бюджет": answers['budget_breakdown']
}
```

### Step 3: Research Integration

**Agent:** `ResearcherAgent`
**Method:** `research_anketa(anketa_id: str)`

**Input:** anketa_id
**Output:** Saves to researcher_research table + export to `research_*.txt`

**Note:** Agent automatically loads from DB and saves results

### Step 4: Writer Integration

**Agent:** `WriterAgentV2`
**Method:** `write_application_async(input_data: Dict)`

**Input:**
```python
input_data = {
    "anketa_id": anketa_id,
    "user_answers": answers_data,
    "selected_grant": {
        "name": "Президентский грант",
        "organization": "Фонд президентских грантов"
    }
}
```

**Output:** Saves to grants table + export to `grant_*.txt`

### Step 5: Review (Simplified)

**Implementation:** Use AuditorAgent again to review the generated grant

**Input:** Grant text from Step 4
**Output:** Save review to reviews table + export to `review_*.txt`

---

## 📝 Implementation Steps

### Phase 1: Fix e2e_synthetic_workflow.py (30 min)

1. Uncomment Steps 2-5 in `run_full_cycle()`
2. Fix agent initialization
3. Fix method calls with correct parameters
4. Add file export after each step

### Phase 2: Test Locally (15 min)

1. Test with 1 cycle first
2. Fix any import/API errors
3. Verify files are generated

### Phase 3: Deploy to Production (10 min)

1. Git commit & push
2. SSH pull on server
3. Run with 5 cycles
4. Monitor execution

### Phase 4: Verification (5 min)

1. Check 25 files generated
2. Verify file sizes reasonable
3. Verify database records

**Total Estimated Time:** 60 minutes

---

## ✅ Success Criteria

- [x] Step 1: 5 anketa files (already done)
- [ ] Step 2: 5 audit files
- [ ] Step 3: 5 research files
- [ ] Step 4: 5 grant files
- [ ] Step 5: 5 review files
- [ ] All 25 files exist on production
- [ ] All database records correct
- [ ] No errors in logs

---

## 🔗 API Reference

**AuditorAgentClaude:**
```python
from agents.auditor_agent_claude import AuditorAgentClaude

auditor = AuditorAgentClaude(db=db, llm_provider="claude")
result = await auditor.evaluate_project_async(project_data, use_quick_score=False)
```

**ResearcherAgent:**
```python
from agents.researcher_agent import ResearcherAgent

researcher = ResearcherAgent(db=db)
result = researcher.research_anketa(anketa_id)
```

**WriterAgentV2:**
```python
from agents.writer_agent_v2 import WriterAgentV2

writer = WriterAgentV2(db=db, llm_provider="gigachat")
result = await writer.write_application_async(input_data)
```

---

**Created:** 2025-10-29 02:25 MSK
**Target Completion:** 2025-10-29 03:30 MSK
**Deadline:** 2025-10-30 (для буткемпа Сбера)
