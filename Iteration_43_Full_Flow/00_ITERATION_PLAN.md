# Iteration 43: Full Production Flow Test

**Date:** 2025-10-25
**Status:** 🚀 STARTING
**Goal:** Test COMPLETE production flow (hardcoded questions + InteractiveInterviewerAgentV2)

---

## 🎯 Objective

Test the **FULL PRODUCTION FLOW** as users experience it in the Telegram bot:

```
PHASE 1: Hardcoded Questions (interview_handler.py)
  ↓
  Q1: "Скажите, как Ваше имя, как я могу к Вам обращаться?"
  Q2: "Расскажите о вашей организации"
  ↓
PHASE 2: Adaptive Questions (InteractiveInterviewerAgentV2)
  ↓
  Q3: "Как называется ваш проект?"
  Q4-Q15: Dynamic questions based on answers
  ↓
RESULT: Complete dialog_history with BOTH hardcoded + adaptive parts
```

---

## 🔑 Key Innovation

**Previous Iterations:**
- **Iteration 40:** Tested InteractiveInterviewer in isolation (6 tests)
- **Iteration 41:** Generated 100 realistic interviews (field-by-field)
- **Iteration 42:** Real dialog flow (InteractiveInterviewerAgentV2 only)

**Iteration 43 (NEW):**
- **FIRST TIME** testing COMPLETE flow
- Hardcoded questions + Adaptive questions
- Full dialog_history from start to finish
- Exactly as users experience in production

---

## 📋 Test Scope

### Scale
**2 Anketas:**
- 1 × Medium quality
- 1 × High quality

**Why only 2?**
- Focused testing of full flow
- Avoid GigaChat rate limits
- Validate architecture before scaling

### Components

#### Phase 1: Hardcoded Questions
From `handlers/interview_handler.py`:

```python
HARDCODED_QUESTIONS = [
    {
        "id": "user_name",
        "text": "Скажите, как Ваше имя, как я могу к Вам обращаться?",
        "field_name": "user_name"
    },
    {
        "id": "organization",
        "text": "Расскажите о вашей организации",
        "field_name": "organization"
    }
]
```

#### Phase 2: Adaptive Questions
From `InteractiveInterviewerAgentV2`:
- Reference Points Framework (P0-P3)
- Qdrant semantic search
- Adaptive question generation
- ~10-15 questions per interview

---

## 🏗️ Architecture

### Flow Diagram

```
┌─────────────────────────────────────────┐
│  Test Script (test_iteration_43.py)    │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Full Flow Manager │
         └─────────┬──────────┘
                   │
      ┌────────────┴─────────────┐
      │                          │
┌─────▼──────┐          ┌────────▼─────────┐
│ Hardcoded  │          │ InteractiveInterv│
│ Questions  │──────────▶ iewer AgentV2    │
│ (Phase 1)  │          │ (Phase 2)        │
└─────┬──────┘          └────────┬─────────┘
      │                          │
      │    ┌──────────────┐      │
      └────▶ SyntheticUser◀──────┘
           │ Simulator    │
           └──────┬───────┘
                  │
         ┌────────▼─────────┐
         │ dialog_history   │
         │ (JSONB in DB)    │
         └──────────────────┘
```

### Data Structure

```json
{
  "dialog_history": [
    {
      "role": "interviewer",
      "text": "Скажите, как Ваше имя?",
      "timestamp": "2025-10-25T21:00:00",
      "phase": "hardcoded",
      "question_id": "user_name"
    },
    {
      "role": "user",
      "text": "Меня зовут Александр",
      "timestamp": "2025-10-25T21:00:05",
      "phase": "hardcoded"
    },
    {
      "role": "interviewer",
      "text": "Как называется ваш проект?",
      "timestamp": "2025-10-25T21:00:10",
      "phase": "adaptive",
      "reference_point": "rp_001_project_essence"
    },
    {
      "role": "user",
      "text": "Наш проект называется...",
      "timestamp": "2025-10-25T21:00:15",
      "phase": "adaptive",
      "field_name": "project_essence"
    }
  ]
}
```

---

## 📝 Implementation Plan

### Step 1: Create FullFlowManager

**File:** `agents/full_flow_manager.py`

```python
class FullFlowManager:
    """
    Manages complete interview flow: hardcoded + adaptive
    """

    async def conduct_full_interview(
        self,
        user_data: Dict,
        user_simulator: SyntheticUserSimulator
    ) -> Dict:
        """
        Conducts complete interview with both phases

        Returns:
            {
                'anketa': {...},
                'dialog_history': [...],
                'audit_score': float,
                'hardcoded_questions_asked': int,
                'adaptive_questions_asked': int
            }
        """
        dialog_history = []

        # Phase 1: Hardcoded questions
        hardcoded_data = await self._ask_hardcoded_questions(
            user_simulator,
            dialog_history
        )

        # Phase 2: Adaptive questions (InteractiveInterviewerAgentV2)
        adaptive_data = await self._conduct_adaptive_interview(
            user_data,
            user_simulator,
            dialog_history,
            hardcoded_data
        )

        return {
            'dialog_history': dialog_history,
            'hardcoded_data': hardcoded_data,
            'adaptive_data': adaptive_data,
            ...
        }
```

### Step 2: Define Hardcoded Questions

**File:** `agents/full_flow_manager.py`

```python
HARDCODED_QUESTIONS = [
    {
        "id": "user_name",
        "text": "Скажите, как Ваше имя, как я могу к Вам обращаться?",
        "field_name": "user_name",
        "required": True
    },
    {
        "id": "organization",
        "text": "Расскажите о вашей организации",
        "field_name": "organization_description",
        "required": True
    }
]
```

### Step 3: Integrate with InteractiveInterviewerAgentV2

Pass hardcoded data to InteractiveInterviewerAgentV2:

```python
# Prepare user_data with hardcoded responses
user_data_enriched = {
    **user_data,
    'user_name': hardcoded_data['user_name'],
    'organization_description': hardcoded_data['organization_description']
}

# Conduct adaptive interview
interviewer = InteractiveInterviewerAgentV2(...)
result = await interviewer.conduct_interview(
    user_data=user_data_enriched,
    callback_ask_question=callback
)
```

### Step 4: Create Test Script

**File:** `test_iteration_43_full_flow.py`

Test 2 anketas:
- 1 medium quality
- 1 high quality

Save complete dialog_history to database.

---

## 🎯 Success Criteria

### Must Have:
✅ Both hardcoded questions answered
✅ InteractiveInterviewerAgentV2 adaptive questions asked
✅ Complete dialog_history saved to DB
✅ dialog_history includes BOTH phases
✅ 2 anketas successfully created
✅ Audit scores calculated

### Nice to Have:
✅ Display formatted dialog with phase markers
✅ Statistics (hardcoded vs adaptive question count)
✅ Comparison between medium/high quality responses

---

## ⚠️ Known Constraints

### GigaChat Rate Limit
- **Issue:** 429 Too Many Requests
- **Mitigation:**
  - Test only 2 anketas (minimal requests)
  - Add 30-second delays between anketas
  - Use exponential backoff on errors

### Token Budget
- **Available:** 2M tokens (GigaChat Pro)
- **Estimated Usage:** ~50K tokens for 2 anketas
- **Safe:** ✅ Well within budget

---

## 📊 Expected Results

### Deliverables

1. **agents/full_flow_manager.py** (~250 lines)
   - FullFlowManager class
   - Hardcoded questions
   - Integration logic

2. **test_iteration_43_full_flow.py** (~300 lines)
   - Test runner for 2 anketas
   - Dialog history display
   - Statistics reporting

3. **Iteration_43_Full_Flow/** (documentation)
   - 00_ITERATION_PLAN.md (this file)
   - PROGRESS_LOG.md
   - ITERATION_43_SUMMARY.md

4. **Database Results**
   - 2 new sessions with complete dialog_history
   - Anketa nomenclature: #AN-20251025-iter43_user_1-001, etc.

### Metrics

**Per Anketa:**
- Hardcoded questions: 2
- Adaptive questions: ~10-15
- Total questions: ~12-17
- Dialog history messages: ~24-34 (questions + answers)
- Processing time: ~60-120 seconds

---

## 🚀 Execution Timeline

### Phase 1: Implementation (10 minutes)
- Create FullFlowManager
- Define hardcoded questions
- Integration logic

### Phase 2: Testing (5-10 minutes)
- Run test_iteration_43_full_flow.py
- Monitor execution
- Handle rate limits

### Phase 3: Validation (5 minutes)
- Verify dialog_history in DB
- Display formatted dialogs
- Calculate statistics

### Phase 4: Documentation (5 minutes)
- Update PROGRESS_LOG.md
- Create ITERATION_43_SUMMARY.md
- Git commit

**Total:** 25-35 minutes

---

## 📁 File Structure

```
Iteration_43_Full_Flow/
├── 00_ITERATION_PLAN.md          (this file)
├── PROGRESS_LOG.md                (execution log)
└── ITERATION_43_SUMMARY.md        (final results)

agents/
└── full_flow_manager.py           (NEW - full flow orchestration)

test_iteration_43_full_flow.py     (NEW - test script)
```

---

## 🎓 Key Learnings Expected

1. **Integration Complexity**
   - How hardcoded + adaptive phases integrate
   - Data passing between phases
   - Dialog history continuity

2. **User Experience Validation**
   - Complete flow as users see it
   - Question sequencing
   - Natural conversation progression

3. **Production Readiness**
   - Architecture validation
   - Performance metrics
   - Error handling

---

## 🔄 Next Steps (Iteration 44+)

If successful:
- **Iteration 44:** Scale to 10 anketas (full distribution)
- **Iteration 45:** A/B testing (different question strategies)
- **Iteration 46:** Multi-language support testing

---

**Created:** 2025-10-25
**Target Completion:** 2025-10-25 (same day)
**Status:** 🚀 Ready to implement
