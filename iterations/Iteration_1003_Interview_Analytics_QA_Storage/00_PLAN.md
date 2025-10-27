# Iteration 1003: Interview Analytics & Q&A Storage (FUTURE PLAN)

**Status:** 📅 PLANNED (not started)
**Priority:** MEDIUM
**Prerequisites:** Iteration 53 complete ✅
**Estimated Time:** 3-4 hours
**Assigned To:** TBD

---

## 🎯 Goal

Add **question-answer logging** to interview process + upgrade InteractiveInterviewerAgentV2 to **GigaChat-2-Max** for better quality questions.

**Current State (from Iteration 53):**
- ✅ InteractiveInterviewerAgentV2 works (Reference Points Framework)
- ✅ Saves `interview_data` (answers only) to sessions table
- ❌ Questions NOT logged (cannot reproduce interviews)
- ❌ Uses basic `GigaChat` model (not Max/2-Max)

**Target State:**
- ✅ Questions + Answers logged to database (every turn)
- ✅ Corpus of real interviews for ML training
- ✅ Analytics: most asked questions, answer lengths, follow-up patterns
- ✅ GigaChat-2-Max for better question generation
- ✅ Reproducible interviews (see exact Q&A flow)

---

## 📊 Scope

### In Scope ✅
1. New database table `interview_qa` for logging questions and answers
2. Update InteractiveInterviewerAgentV2 to log Q&A after each turn
3. Upgrade to GigaChat-2-Max model
4. Analytics queries (examples)
5. Documentation

### Out of Scope ❌
- ML fine-tuning on corpus (deferred to Iteration 1004)
- Web UI for analytics (use SQL queries)
- Real-time dashboards
- Question recommendation system

---

## 📋 Tasks Breakdown

### Phase 1: Database Schema (30 min)
**Goal:** Create `interview_qa` table for logging questions and answers

**Database Migration:**
```sql
CREATE TABLE interview_qa (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,  -- 1, 2, 3...

    -- Question
    question_text TEXT NOT NULL,
    question_generated_by VARCHAR(50),  -- 'llm' | 'fallback' | 'hardcoded'
    reference_point_id VARCHAR(100),    -- rp_001_project_essence

    -- Answer
    answer_text TEXT NOT NULL,
    answer_length INTEGER,
    answer_received_at TIMESTAMP DEFAULT NOW(),

    -- Metrics
    completion_confidence FLOAT,  -- 0-1 (how complete is the answer)
    was_follow_up BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_session_turn UNIQUE(session_id, turn_number)
);

CREATE INDEX idx_qa_session ON interview_qa(session_id);
CREATE INDEX idx_qa_rp ON interview_qa(reference_point_id);
CREATE INDEX idx_qa_created_at ON interview_qa(created_at DESC);
```

**Tasks:**
- [ ] Create migration SQL file: `data/migrations/005_interview_qa_table.sql`
- [ ] Run migration on localhost (test)
- [ ] Add DB methods: `save_interview_qa()`, `get_interview_qa()`
- [ ] Test insertion and retrieval

**Acceptance Criteria:**
- ✅ Table created successfully
- ✅ Can insert Q&A records
- ✅ Can query by session_id, turn_number, rp_id

---

### Phase 2: Update Agent to Log Q&A (1.5 hours)
**Goal:** Modify InteractiveInterviewerAgentV2 to save Q&A after each turn

**Files to Modify:**
1. `agents/interactive_interviewer_v2/agent.py` - Add logging in `_conversation_loop()`
2. `data/database/models.py` - Add `save_interview_qa()` method

**Implementation:**
```python
# In agents/interactive_interviewer_v2/agent.py
# _conversation_loop() method, after receiving answer:

async def _conversation_loop(...):
    turn = 1

    while turn <= max_turns:
        # ... existing code ...

        # Generate question
        question = await self._generate_question_for_rp(rp, context)

        # Determine question source
        question_source = (
            'hardcoded' if rp.id in hardcoded_rps else
            'fallback' if question in fallback_bank else
            'llm'
        )

        # Ask question
        answer = await callback_ask_question(question)

        # Save to RP
        rp.add_data('text', answer)

        # ✅ NEW: Log Q&A to database
        await self.db.save_interview_qa(
            session_id=user_data['session_id'],
            turn_number=turn,
            question_text=question,
            question_generated_by=question_source,
            reference_point_id=rp.id,
            answer_text=answer,
            answer_length=len(answer),
            completion_confidence=rp.completion_confidence,
            was_follow_up=is_follow_up
        )

        turn += 1
```

**Tasks:**
- [ ] Add `save_interview_qa()` method to Database class
- [ ] Modify `_conversation_loop()` to log Q&A
- [ ] Determine question source (LLM vs fallback vs hardcoded)
- [ ] Handle errors gracefully (if DB save fails, log warning but continue)
- [ ] Test with mock interview (verify Q&A logged)

**Acceptance Criteria:**
- ✅ Every Q&A turn is logged to database
- ✅ Can retrieve full interview Q&A sequence
- ✅ Errors don't break interview flow

---

### Phase 3: Upgrade to GigaChat-2-Max (30 min)
**Goal:** Switch from basic GigaChat to GigaChat-2-Max

**Current Model:** `GigaChat` (base, 1st generation)
**Target Model:** `GigaChat-2-Max` (2nd generation, best quality)

**Files to Modify:**
```python
# shared/llm/config.py

AGENT_CONFIGS = {
    "interviewer": {
        "provider": "gigachat",
        "model": "GigaChat-2-Max",  # ← UPGRADE!
        "temperature": 0.7,
        "max_tokens": 150
    },
    # ... other agents unchanged
}
```

**Tasks:**
- [ ] Update `shared/llm/config.py` - add "interviewer" config
- [ ] Test question generation with GigaChat-2-Max
- [ ] Compare question quality (manual spot check)
- [ ] Update documentation

**Acceptance Criteria:**
- ✅ InteractiveInterviewerAgentV2 uses GigaChat-2-Max
- ✅ Questions are more natural and context-aware
- ✅ No performance degradation

---

### Phase 4: Analytics Queries (30 min)
**Goal:** Create useful SQL queries for analyzing interview corpus

**Example Queries:**

**1. Most Asked Questions:**
```sql
-- Top 10 most frequently asked questions
SELECT
    question_text,
    COUNT(*) as frequency,
    AVG(answer_length) as avg_answer_length
FROM interview_qa
GROUP BY question_text
ORDER BY frequency DESC
LIMIT 10;
```

**2. Follow-Up Pattern Analysis:**
```sql
-- How often are follow-ups used?
SELECT
    reference_point_id,
    COUNT(*) FILTER (WHERE was_follow_up = TRUE) as follow_up_count,
    COUNT(*) as total_questions,
    ROUND(100.0 * COUNT(*) FILTER (WHERE was_follow_up = TRUE) / COUNT(*), 1) as follow_up_percentage
FROM interview_qa
GROUP BY reference_point_id
ORDER BY follow_up_percentage DESC;
```

**3. Question Source Distribution:**
```sql
-- How are questions generated?
SELECT
    question_generated_by,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage
FROM interview_qa
GROUP BY question_generated_by;
```

**4. Average Interview Length:**
```sql
-- Average turns per interview
SELECT
    AVG(max_turn) as avg_turns,
    MIN(max_turn) as min_turns,
    MAX(max_turn) as max_turns
FROM (
    SELECT session_id, MAX(turn_number) as max_turn
    FROM interview_qa
    GROUP BY session_id
) as turns_per_session;
```

**5. Completion Confidence by RP:**
```sql
-- Which RPs get the best answers?
SELECT
    reference_point_id,
    AVG(completion_confidence) as avg_confidence,
    COUNT(*) as sample_size
FROM interview_qa
WHERE completion_confidence IS NOT NULL
GROUP BY reference_point_id
ORDER BY avg_confidence DESC;
```

**Tasks:**
- [ ] Create SQL file: `data/analytics/interview_analytics.sql`
- [ ] Test queries on sample data
- [ ] Document query usage

**Acceptance Criteria:**
- ✅ 5+ useful analytics queries ready to use
- ✅ Queries tested on real data
- ✅ Results provide actionable insights

---

### Phase 5: Export Interview Q&A Script (30 min)
**Goal:** Script to export full Q&A sequence for any interview

**Script:** `scripts/export_interview_qa.py`

```python
#!/usr/bin/env python3
"""
Export complete Q&A sequence for an interview session.

Usage:
    python scripts/export_interview_qa.py <session_id>
    python scripts/export_interview_qa.py 608
"""

import sys
import psycopg2

def export_interview_qa(session_id: int):
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="grantservice",
        user="postgres",
        password="root"
    )
    cursor = conn.cursor()

    # Get session info
    cursor.execute("SELECT project_name, started_at FROM sessions WHERE id = %s", (session_id,))
    project_name, started_at = cursor.fetchone()

    # Get Q&A sequence
    query = """
        SELECT
            turn_number,
            question_text,
            answer_text,
            question_generated_by,
            reference_point_id,
            was_follow_up
        FROM interview_qa
        WHERE session_id = %s
        ORDER BY turn_number
    """
    cursor.execute(query, (session_id,))
    qa_pairs = cursor.fetchall()

    # Format output
    print(f"\n{'='*60}")
    print(f"INTERVIEW Q&A SEQUENCE")
    print(f"Session: {session_id} | Project: {project_name}")
    print(f"Date: {started_at}")
    print(f"{'='*60}\n")

    for turn, question, answer, source, rp, is_follow_up in qa_pairs:
        follow_up_mark = " [FOLLOW-UP]" if is_follow_up else ""
        print(f"--- Turn {turn}{follow_up_mark} ({rp}) ---")
        print(f"[Q] {question}")
        print(f"    Source: {source}")
        print(f"[A] {answer[:200]}{'...' if len(answer) > 200 else ''}")
        print()

    cursor.close()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_interview_qa.py <session_id>")
        sys.exit(1)

    session_id = int(sys.argv[1])
    export_interview_qa(session_id)
```

**Tasks:**
- [ ] Create `scripts/export_interview_qa.py`
- [ ] Test with session 608 (archery project)
- [ ] Add to documentation

**Acceptance Criteria:**
- ✅ Script exports full Q&A sequence
- ✅ Output is readable and useful
- ✅ Can be used for debugging and analysis

---

## 🎓 Benefits

### 1. ML Training Corpus
- Build dataset of real interviews (1000+ Q&A pairs)
- Fine-tune question generation model
- Improve follow-up question logic

### 2. Quality Control
- Review what questions agent is asking
- Identify problematic questions (too vague, repetitive)
- Spot patterns in user answers (too short, off-topic)

### 3. Analytics & Insights
- Which RPs take most turns to complete?
- Which questions get longest/shortest answers?
- How often are follow-ups needed?
- Question source distribution (LLM vs fallback)

### 4. Debugging & Reproducibility
- Reproduce any interview exactly
- Understand why certain interviews failed
- Validate improvements (before/after comparisons)

### 5. A/B Testing Foundation
- Compare question quality: GigaChat vs GigaChat-2-Max
- Test different temperature settings
- Measure impact of prompt changes

---

## 📝 Documentation Updates

**Files to Update:**
- `agents/interactive_interviewer_v2/docs/ARCHITECTURE.md` - Add Q&A logging section
- `agents/interactive_interviewer_v2/README.md` - Mention GigaChat-2-Max upgrade
- `data/database/README.md` - Document `interview_qa` table

---

## ✅ Definition of Done

- [ ] Database table `interview_qa` created and tested
- [ ] Agent logs Q&A after each turn
- [ ] Upgraded to GigaChat-2-Max
- [ ] 5+ analytics queries documented
- [ ] Export script created and tested
- [ ] Documentation updated
- [ ] Tested on 3+ real interviews

---

## 🔗 Related

**Prerequisites:**
- Iteration 53: Production bug fixed, agent working

**Enables:**
- Iteration 1004: ML fine-tuning on interview corpus
- Iteration 1005: Intelligent question recommendation system
- Iteration 1006: Multi-language interview support

---

**Created:** 2025-10-27
**Author:** Grant Service Team
**Status:** PLANNED (not started)
