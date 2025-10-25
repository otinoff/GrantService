# Iteration 37: Phase 1 - Diagnostic Findings

**Completed:** 2025-10-25
**Duration:** 1 hour
**Status:** ✅ ROOT CAUSE IDENTIFIED

---

## 🎯 PROBLEM STATEMENT

Audit scores extremely low for test anketa:
- Overall: 0.0/10
- Completeness: 4.0/10
- Clarity: 0/10
- Feasibility: 0/10
- Innovation: 0/10

**User request:** "генерация заявка не корректная как можем сделать чтобы заявки были хорошие генерировалось?"

---

## 🔍 DIAGNOSTIC RESULTS

### Phase 1.1: Test Anketa Analysis ✅

**File:** `telegram-bot/handlers/anketa_management_handler.py:786-840`

**Findings:**
- `create_test_anketa()` creates **19 fields** with good realistic data:
  - project_name, organization, region
  - problem (detailed ~500 chars)
  - solution (detailed ~400 chars)
  - goals (3 items)
  - activities (5 items)
  - results (3 items)
  - budget, budget_breakdown (detailed)
  - team, experience, sustainability, innovation, social_impact

**Conclusion:** ✅ Test anketa has sufficient data - NOT the problem

---

### Phase 1.2: AuditorAgent Prompts Analysis ✅

**Database query:**
```sql
SELECT name, prompt_type, prompt_template
FROM agent_prompts
WHERE agent_type='auditor' AND is_active=true;
```

**Findings:**
- 6 prompts found:
  - backstory
  - goal
  - llm_completeness
  - llm_compliance
  - llm_innovation
  - llm_quality

**🚨 CRITICAL DISCOVERY:**

All prompts use variable: `{application_text}`

Example from llm_completeness:
```
Ты эксперт по грантовым заявкам.
Проанализируй ПОЛНОТУ заявки.

ТЕКСТ ЗАЯВКИ:
{application_text}

Оцени по шкале 0-10...
```

**Conclusion:** ❌ AuditorAgent expects **FORMATTED GRANT TEXT**, not raw JSON!

---

### Phase 1.3: Anketa → Audit Mapping ✅

**Current flow:**

```
anketa_management_handler.py (line 433-444):
  audit_input = {
      'application': interview_data,  # ❌ RAW JSON
      'user_answers': interview_data,
      ...
  }
  → AuditorAgent.audit_application_async(audit_input)
```

**What AuditorAgent receives:**
```json
{
  "project_name": "Молодежный центр...",
  "organization": "АНО...",
  "problem": "...",
  ...
}
```

**What AuditorAgent expects:**
```markdown
# Заявка на грант: Молодежный центр

## Краткое описание
[formatted text ~500 words]

## Описание проблемы
[formatted text ~1500 words]

...
```

**Mismatch Result:**
- Completeness: 4.0/10 (recognizes some fields)
- Clarity: 0/10 (expects prose, gets JSON keys)
- Feasibility: 0/10 (can't evaluate structure)
- Innovation: 0/10 (can't find narrative)

**Conclusion:** ❌ **DATA FORMAT MISMATCH** - This is the ROOT CAUSE!

---

### Phase 1.4: ProductionWriter Analysis ✅

**File:** `C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\lib\production_writer.py`

**Findings:**

ProductionWriter EXISTS and works correctly:

```python
class ProductionWriter:
    async def write(self, anketa_data: Dict) -> str:
        """
        Generate 30K+ symbols grant application

        Args:
            anketa_data: Raw JSON from anketa

        Returns:
            grant_application: Formatted text (10 sections)
        """
```

**Sections generated (10):**
1. Краткое описание (500 words)
2. Описание проблемы (1500 words)
3. География (800 words)
4. Целевая аудитория (800 words)
5. Цели и задачи (1000 words)
6. Мероприятия (1500 words)
7. Ожидаемые результаты (1000 words)
8. Партнёры (500 words)
9. Устойчивость (800 words)
10. Заключение (600 words)

**Integration (from Iteration 32):**
- ProductionWriter deployed to production
- Integrated into `/generate_grant` command
- Uses Qdrant for FPG requirements
- Working with GigaChat

**Conclusion:** ✅ ProductionWriter works and formats correctly!

---

## 🎯 ROOT CAUSE ANALYSIS

### Current Workflows:

**1. /audit_anketa (anketa_management_handler.py):**
```
Anketa JSON → AuditorAgent → 0.0/10 ❌
```

**2. /generate_grant (grant_handler.py):**
```
Anketa JSON → Audit (0.0/10) → BLOCKED ❌
              ↓
           (never reaches)
              ↓
        ProductionWriter → Grant Text
```

### The Problem:

**TWO workflows audit RAW anketa JSON:**

1. **anketa_management_handler.py (lines 433-444):**
   ```python
   audit_input = {
       'application': interview_data,  # ❌ RAW JSON
       ...
   }
   audit_wrapped = await auditor.audit_application_async(audit_input)
   ```

2. **grant_handler.py (lines 107-115) in `_check_or_run_audit()`:**
   ```python
   audit_input = {
       'application': anketa_data,  # ❌ RAW JSON
       ...
   }
   audit_wrapped = await auditor.audit_application_async(audit_input)
   ```

**Both pass RAW JSON where AuditorAgent expects FORMATTED TEXT.**

### Why This Happens:

**Intended workflow (Iteration 35 design):**
```
User completes anketa → Audit raw anketa → If OK, proceed
```

**But AuditorAgent was designed (from previous iterations) to audit:**
```
Formatted grant application TEXT (from ProductionWriter)
```

**Design mismatch!** Iteration 35 added audit to anketa stage, but auditor expects grant text stage.

---

## 💡 ROOT CAUSE IDENTIFIED

**The fundamental issue:**

AuditorAgent prompts are designed to analyze **formatted grant application text** with sections, narrative, and structure.

But in Iteration 35, audit was added to anketa stage which only has **raw JSON data**.

**Visual:**

```
ITERATION 32-34: ProductionWriter Integration
  Anketa JSON → ProductionWriter → Grant TEXT → [no audit]

ITERATION 35: Auditor Integration
  Anketa JSON → AuditorAgent → [expects TEXT, gets JSON] → 0.0/10 ❌

CORRECT FLOW SHOULD BE:
  Anketa JSON → ProductionWriter → Grant TEXT → AuditorAgent → 7.0+/10 ✅
```

---

## 📊 EVIDENCE SUMMARY

| Component | Status | Evidence |
|-----------|--------|----------|
| Test anketa data | ✅ Good | 19 fields, detailed, realistic |
| ProductionWriter | ✅ Works | Generates 30K+ formatted text |
| AuditorAgent prompts | ✅ Correct | Designed for grant TEXT |
| /audit_anketa flow | ❌ Wrong | Passes JSON to text auditor |
| /generate_grant flow | ❌ Wrong | Audits JSON before generation |

---

## 🎯 SOLUTION OPTIONS

### Option A: Audit AFTER Generation (Recommended)

**Change /generate_grant workflow:**
```python
1. Get anketa JSON
2. Generate grant TEXT with ProductionWriter  # ← Move this UP
3. Run audit on GENERATED TEXT                # ← Audit the TEXT
4. If score < 7.0 → Save with "needs_revision" status
5. If score >= 7.0 → Save with "approved" status
6. Send grant to user with audit results
```

**Pros:**
- ✅ AuditorAgent works as designed (audits grant text)
- ✅ No changes to auditor prompts needed
- ✅ ProductionWriter already works
- ✅ Quality control on final product

**Cons:**
- Always generates grant (even if will be rejected)
- Uses tokens for generation + audit

---

### Option B: Two-Stage Audit

**Stage 1: Anketa validation (simple checks)**
```python
def validate_anketa(anketa_data):
    """
    Simple validation: check required fields exist and have content
    No LLM needed
    """
    required = ['project_name', 'problem', 'solution', 'goals', 'budget']
    for field in required:
        if not anketa_data.get(field):
            return False, f"Missing {field}"
    return True, "OK"
```

**Stage 2: Grant text audit (AuditorAgent)**
```python
1. Validate anketa (fast, no LLM)
2. If validation OK → Generate with ProductionWriter
3. Audit generated TEXT with AuditorAgent
4. If audit OK → Send to user
```

**Pros:**
- ✅ Fast validation catches missing data
- ✅ AuditorAgent audits proper grant text
- ✅ Two layers of quality control

**Cons:**
- More complex implementation

---

### Option C: Change AuditorAgent to Accept JSON (NOT Recommended)

**Modify auditor prompts:**
```
Instead of: "Analyze this grant TEXT: {application_text}"
Use: "Analyze this grant DATA: {application_json}"
```

**Pros:**
- Audits before generation (saves tokens if rejected)

**Cons:**
- ❌ Requires rewriting all 6 auditor prompts
- ❌ LLM less effective at judging raw JSON vs formatted text
- ❌ Contradicts original auditor design
- ❌ Quality scores likely still low

---

## 📋 RECOMMENDATION

**Implement Option A: Audit After Generation**

**Why:**
1. Minimal code changes (just reorder operations)
2. AuditorAgent works as designed
3. Quality control on actual grant text (what user receives)
4. Clear separation: ProductionWriter generates, AuditorAgent validates

**Implementation:**
- Modify `grant_handler.py:generate_grant()`:
  - Move ProductionWriter.write() BEFORE audit
  - Pass generated text to AuditorAgent
  - Save grant with audit scores

- Modify `anketa_management_handler.py:/audit_anketa`:
  - Either:
    - Option A1: Generate text first, then audit
    - Option A2: Change to simple field validation (no LLM)
    - Option A3: Disable /audit_anketa, only audit in /generate_grant

**For /audit_anketa command specifically:**

**Best approach:** Generate text first, then audit (Option A1)

```python
async def audit_anketa(update, context):
    # 1. Get anketa data
    anketa_data = get_anketa_data(anketa_id)

    # 2. Generate grant text (temporary, not saved)
    writer = ProductionWriter(...)
    grant_text = await writer.write(anketa_data)

    # 3. Audit the GENERATED TEXT
    auditor = AuditorAgent(...)
    audit_result = await auditor.audit_application_async({
        'application_text': grant_text,  # ← TEXT not JSON
        ...
    })

    # 4. Return audit scores (don't save grant yet)
    return audit_result
```

This way:
- /audit_anketa works correctly (audits generated text)
- /generate_grant works correctly (generates then audits)
- User can preview audit scores before committing to generation

---

## 🚀 NEXT STEPS (Phase 2)

Based on Option A recommendation:

### Phase 2.1: Modify /generate_grant workflow
- [x] Diagnostic complete (this document)
- [ ] Move ProductionWriter before audit
- [ ] Pass generated text to AuditorAgent
- [ ] Test with test_anketa

### Phase 2.2: Modify /audit_anketa workflow
- [ ] Generate temp grant text
- [ ] Audit the generated text
- [ ] Return results without saving

### Phase 2.3: Update AuditorAgent integration
- [ ] Ensure `application_text` variable is populated
- [ ] Verify prompts receive formatted text

### Phase 2.4: Testing
- [ ] Create test anketa
- [ ] Run /audit_anketa → expect 7.0+/10
- [ ] Run /generate_grant → expect successful generation

---

## 📊 ESTIMATED IMPACT

**Before (Current):**
- Audit score: 0.0/10
- Generation blocked
- User can't get grants

**After (Fix):**
- Audit score: 7.0-8.5/10 (expected)
- Generation succeeds
- User receives quality grants

---

## 📝 FILES TO MODIFY

1. **telegram-bot/handlers/grant_handler.py**
   - Method: `generate_grant()` (lines 156-430)
   - Change: Move ProductionWriter before audit
   - Lines affected: ~30

2. **telegram-bot/handlers/anketa_management_handler.py**
   - Method: `audit_anketa()` (lines 380-480)
   - Change: Generate text before audit OR add validation
   - Lines affected: ~20

3. **agents/auditor_agent.py** (maybe)
   - Verify `application_text` variable usage
   - Ensure prompts receive text not JSON
   - Lines affected: 0-10 (verification only)

---

**Total estimated changes:** <60 lines
**Methodology principle:** Метаболизм (small targeted change)
**Risk level:** LOW (reordering operations, no breaking changes)

---

## ✅ PHASE 1 SUCCESS CRITERIA - MET

- [x] Понятна причина низких оценок (data format mismatch)
- [x] Mapping anketa → audit requirements (incompatible formats)
- [x] ProductionWriter проверен (works correctly)
- [x] Root cause identified (audit before generation)
- [x] Solution designed (audit after generation)

---

**Created:** 2025-10-25
**Phase:** 1/4 (Diagnostic)
**Next:** Phase 2 (Implementation)
**Methodology:** Project Evolution (Метаболизм)
