# Iteration 26: Hardcode Question #2 - Quick Plan

**Date:** 2025-10-22
**Status:** 🔄 IN PROGRESS
**Priority:** P0 CRITICAL (UX bottleneck)
**Time:** ~20 minutes

---

## Problem

**LLM generation still slow:** 9.67s for second question!

```
23:35:17 - Turn 1 starts
23:35:19 - Parallel: 2.01s ✅
23:35:26 - LLM: 7.66s ❌ TOO SLOW!
23:35:27 - Question sent (total 9.67s)
```

**User experience:** Waiting 9+ seconds for obvious first question

---

## Solution: Hardcode Question #2

**Insight:** First question is ALWAYS the same - "Tell me about your project"

**Approach:**
1. Hardcode question #2 template
2. Insert user's name for personalization
3. Send instantly after name received
4. Agent skips rp_001 (already asked)

---

## Implementation

### Step 1: Add Hardcoded Question #2

**File:** `telegram-bot/main.py`
**Location:** `_init_and_continue_interview()` after name received

```python
# Wait for name
name = await answer_queue.get()
user_data['applicant_name'] = name

# ✅ ITERATION 24: Mark as collected
user_data['collected_fields'] = {'applicant_name'}
user_data['covered_topics'] = ['applicant_name', 'greeting']

# ✅ ITERATION 26: Send hardcoded question #2
essence_question = (
    f"{name}, расскажите, пожалуйста, в чем суть вашего проекта? "
    f"Что вы планируете делать и какую главную цель хотите достичь?"
)

await context.bot.send_message(
    chat_id=user_id,
    text=essence_question
)

logger.info(f"[INSTANT] Sent hardcoded essence question to user {user_id}")

# Mark that rp_001 is already asked
user_data['covered_topics'].append('project_essence_started')
user_data['hardcoded_questions'] = ['applicant_name', 'project_essence']
```

### Step 2: Agent Skip Logic

**File:** `agents/interactive_interviewer_agent_v2.py`
**Location:** `_conversation_loop()` before asking question

```python
# Check if this RP was already asked via hardcoded question
if reference_point.id == 'rp_001_project_essence':
    if 'project_essence_started' in user_data.get('covered_topics', []):
        logger.info(f"[SKIP] rp_001 already asked as hardcoded question")
        # Don't ask, just collect answer
        # (answer will come from user, we'll process it)
        # Mark as in_progress, not ask again
        reference_point.update_state(ReferencePointState.IN_PROGRESS)
```

---

## Expected Result

### Before (Iteration 25):
```
User: /start
Bot: "Как ваше имя?"
User: "Андрей" [takes 10s to type]
--- 9.67s wait for LLM ---
Bot: "Расскажите о проекте..."
```

### After (Iteration 26):
```
User: /start
Bot: "Как ваше имя?"
User: "Андрей" [takes 10s to type]
Bot: "Андрей, расскажите о проекте..." [INSTANT! <0.1s]
```

**Improvement:** -9.67s on second question = instant response!

---

## Risks

1. **Loss of adaptivity** - Question always the same
   - **Mitigation:** First question IS always the same anyway

2. **Skip logic bugs** - Agent might skip or duplicate
   - **Mitigation:** Clear flag in user_data, test thoroughly

---

## Success Criteria

1. ✅ Second question sent instantly (<1s)
2. ✅ Agent doesn't duplicate rp_001 question
3. ✅ Agent processes answer correctly
4. ✅ Turn 3+ work normally

---

**Next:** Implement in main.py + agent
