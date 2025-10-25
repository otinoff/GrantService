# Iteration 42: Real Dialog Simulation with InteractiveInterviewer

**Date:** 2025-10-25
**Parent:** Iteration 41 (Realistic Interview Simulation)
**Status:** 🚀 Starting

---

## 🎯 Mission

Create **real dialog simulation** between InteractiveInterviewer agent and SyntheticUserSimulator, saving full conversation history with questions and answers.

**Core Improvement:** Move from field-by-field generation to true conversational flow.

---

## 📋 What We Learned from Iteration 41

### ✅ What Worked:
1. **SyntheticUserSimulator** - Generates high-quality realistic answers
2. **Quality levels** - Low/Medium/High temperature settings work well
3. **Database schema** - VARCHAR→TEXT fix handles large responses
4. **Context generation** - Random region/topic/organization creates variety

### ❌ What Was Missing:
1. **No InteractiveInterviewer integration** - Questions were static, not from the agent
2. **No conversation history** - Lost the dialog flow
3. **No question adaptation** - No dynamic question adjustment based on previous answers
4. **No embeddings** - Missed opportunity for semantic search

---

## 🏗️ Architecture: Real Dialog Flow

### Current State (Iteration 41):
```python
# Static field loop
for field_name in REQUIRED_FIELDS:
    question = STATIC_QUESTIONS[field_name]  # Hardcoded
    answer = await user_simulator.answer_question(question, field_name)
    interview_data[field_name] = answer
```

❌ **Problems:**
- No agent involvement
- Questions never change
- No conversation context
- Can't see dialog progression

### Target State (Iteration 42):
```python
# Dynamic conversation
interviewer = InteractiveInterviewer(db, telegram_id, llm_provider='gigachat')
user_simulator = SyntheticUserSimulator(quality_level, context)

dialog_history = []

# Start interview
await interviewer.start_interview()

# Conversation loop
while not interviewer.is_complete():
    # Agent asks question
    question = await interviewer.ask_next_question()
    dialog_history.append({
        "role": "interviewer",
        "text": question,
        "timestamp": datetime.now().isoformat()
    })

    # User simulator answers
    answer = await user_simulator.answer_question(question, interviewer.current_field)
    dialog_history.append({
        "role": "user",
        "text": answer,
        "timestamp": datetime.now().isoformat()
    })

    # Agent processes answer and prepares next question
    await interviewer.process_answer(answer)

# Save with full history
anketa_data = {
    'session_id': session_id,
    'dialog_history': dialog_history,  # NEW!
    'interview_data': interviewer.get_collected_data()
}
```

✅ **Benefits:**
- Real agent interaction
- Question adaptation based on answers
- Full conversation history
- Can audit interview quality
- Can analyze question effectiveness

---

## 🗄️ Database Changes

### Add dialog_history field to sessions table:

```sql
-- Migration for Iteration 42
ALTER TABLE sessions
ADD COLUMN dialog_history JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN sessions.dialog_history IS 'Full conversation history between InteractiveInterviewer and user/simulator';
```

### dialog_history Structure:
```json
[
  {
    "role": "interviewer",
    "text": "Как называется ваш проект?",
    "timestamp": "2025-10-25T20:30:15.123Z",
    "field_name": "project_name"
  },
  {
    "role": "user",
    "text": "Социальный компас Самарской области...",
    "timestamp": "2025-10-25T20:30:18.456Z",
    "field_name": "project_name"
  },
  {
    "role": "interviewer",
    "text": "Подтвердите название вашей организации",
    "timestamp": "2025-10-25T20:30:20.789Z",
    "field_name": "organization"
  },
  ...
]
```

---

## 🔧 Implementation Plan

### Phase 1: Database Migration
**File:** `migrations/add_dialog_history.sql`

```sql
BEGIN;

ALTER TABLE sessions
ADD COLUMN dialog_history JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN sessions.dialog_history IS 'Full conversation history';

COMMIT;
```

### Phase 2: Update InteractiveInterviewer
**File:** `agents/interactive_interviewer.py`

**Add methods:**
```python
class InteractiveInterviewer:
    async def start_interview(self) -> str:
        """Initialize interview and return first question"""
        pass

    async def ask_next_question(self) -> str:
        """Get next question based on conversation state"""
        pass

    async def process_answer(self, answer: str) -> None:
        """Process user answer and update state"""
        pass

    def is_complete(self) -> bool:
        """Check if all required fields collected"""
        pass

    def get_collected_data(self) -> Dict[str, str]:
        """Get all collected interview data"""
        pass

    def get_dialog_history(self) -> List[Dict]:
        """Get full conversation history"""
        pass
```

### Phase 3: Create Test Script
**File:** `test_iteration_42_real_dialog.py`

**Test cases:**
1. Single dialog (low quality)
2. Single dialog (medium quality)
3. Single dialog (high quality)
4. Batch: 10 dialogs (3 low + 5 medium + 2 high)
5. Verify dialog_history saved to database
6. Display sample dialog with Q&A pairs

### Phase 4: Embeddings Integration (Optional for this iteration)
**File:** `add_embeddings_to_dialogs.py`

- Generate embeddings for each answer using GigaChat Embeddings API
- Save to Production Qdrant (5.35.88.251:6333)
- Enable semantic search on interview data

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Real InteractiveInterviewer usage | 100% | Verify agent asks all questions |
| Dialog history saved | 100% | Check sessions.dialog_history field |
| Conversation flow | Natural | Manual review of Q&A pairs |
| Question adaptation | Working | Verify questions change based on context |
| Database schema | Updated | dialog_history JSONB field exists |

---

## 🧪 Test Scenarios

### Test 1: Single Low-Quality Dialog
**Setup:**
- quality_level = 'low'
- region = 'Москва'
- topic = 'молодёжь'
- organization = 'АНО "Развитие"'

**Expected:**
- 10-15 question-answer pairs
- Each pair logged in dialog_history
- Final anketa saved with interview_data
- dialog_history visible in database

### Test 2: Single Medium-Quality Dialog
**Setup:**
- quality_level = 'medium'
- region = 'Санкт-Петербург'
- topic = 'культура'

**Expected:**
- More detailed answers (~1000-1500 chars)
- Professional terminology
- Proper dialog flow

### Test 3: Single High-Quality Dialog
**Setup:**
- quality_level = 'high'
- region = 'Кемеровская область'
- topic = 'социальная поддержка'

**Expected:**
- Detailed answers with legal citations
- 1500-3000 char responses
- Structured and professional

### Test 4: Batch Run (10 dialogs)
**Setup:**
- 3 low + 5 medium + 2 high quality
- Random regions, topics, organizations

**Expected:**
- 10 complete dialog histories
- All saved to database
- Statistics: avg questions, avg answer length, completion rate

---

## 🎯 Deliverables

### Files to Create:
1. **00_ITERATION_PLAN.md** (this file) ✅
2. **migrations/add_dialog_history.sql** - Database migration
3. **test_iteration_42_real_dialog.py** - Main test script
4. **display_dialog_sample.py** - Show Q&A pairs from database
5. **ITERATION_42_SUMMARY.md** - Results documentation

### Database Changes:
- `sessions.dialog_history JSONB` field

### Expected Output:
- 10 complete dialogs with full history
- Verification that InteractiveInterviewer agent works
- Sample dialog display showing real Q&A flow

---

## 🔄 Workflow

```
1. Apply database migration
   ↓
2. Update InteractiveInterviewer with new methods
   ↓
3. Create test script with dialog loop
   ↓
4. Run Test 1: Single dialog (verify flow)
   ↓
5. Run Test 2-3: Quality variations
   ↓
6. Run Test 4: Batch 10 dialogs
   ↓
7. Verify dialog_history in database
   ↓
8. Display sample dialog
   ↓
9. Document results
   ↓
10. Commit to git
```

---

## 💡 Key Innovations

### 1. Real Conversational AI
- Not just Q&A pairs, but actual dialog simulation
- Agent adapts questions based on previous answers
- Conversation context maintained throughout

### 2. Full Transparency
- Every question and answer logged
- Can audit the interview process
- Can analyze question effectiveness

### 3. Quality Analysis
- Compare dialog quality across low/medium/high levels
- Identify which questions get best answers
- Optimize question phrasing for future interviews

### 4. RL-Ready Data Structure
- dialog_history provides rich state information
- Can analyze: question → answer → next_question patterns
- Enables reinforcement learning on interview strategy

---

## 📈 Token Budget

**Estimated usage:**
- 10 dialogs × 15 questions × ~200 tokens/question = **30,000 tokens**
- 10 dialogs × 15 answers × ~500 tokens/answer = **75,000 tokens**
- **Total: ~105,000 tokens** (conservative estimate)

**Available:** GigaChat Sber500 package (~1.1M tokens used in Iter 41, plenty remaining)

---

## 🚀 Next Steps After Iteration 42

1. **Embeddings Integration** - Add GigaChat Embeddings to Production Qdrant
2. **Semantic Search** - Enable finding similar interviews by meaning
3. **RL Optimization** - Use dialog history for reinforcement learning
4. **Question Optimization** - Analyze which questions get best responses

---

**Let's build real conversational AI!** 🎯
