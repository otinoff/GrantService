# Iteration 35: Auditor Integration in Grant Generation Workflow

**Created:** 2025-10-25
**Type:** Feature Enhancement
**Priority:** P0 - CRITICAL (Quality Control)
**Estimated Time:** 2-3 hours

---

## 🎯 ПРОБЛЕМА

### Текущая ситуация:

**Анкета #AN-20251007-theperipherals-005:**
```json
{
    "links": "фывафыва",
    "tasks": "фывафыва",
    "budget": "фывафыва",
    "events": "фывафыва",
    ...все поля заполнены мусором
}
```

**Проблемы:**
1. ❌ Нет проверки качества анкеты перед генерацией
2. ❌ Генерация гранта на тестовых данных = waste of resources
3. ❌ User может получить некачественную заявку
4. ❌ Нет обратной связи о качестве заполнения

### Существующая инфраструктура:

✅ **Auditor Agent существует:**
- `agents/auditor_agent.py` - основной аудитор
- `agents/auditor_agent_claude.py` - Claude version
- Таблица `auditor_results` в БД

✅ **Auditor Result Schema:**
```sql
auditor_results:
- completeness_score (1-10)
- clarity_score (1-10)
- feasibility_score (1-10)
- innovation_score (1-10)
- quality_score (1-10)
- average_score (numeric)
- approval_status (pending/approved/needs_revision/rejected)
- recommendations (jsonb)
```

✅ **Approval Status Logic (trigger):**
- average_score >= 7.0 → "approved"
- average_score >= 5.0 → "needs_revision"
- average_score < 5.0 → "rejected"

---

## 🎯 РЕШЕНИЕ

### New Workflow:

```
User: /generate_grant
   ↓
1. Get anketa_id
   ↓
2. Check: audit exists?
   ├─ NO → Run AuditorAgent.audit(anketa_data)
   │          ↓
   │       Save to auditor_results
   │
   └─ YES → Get audit result
   ↓
3. Check approval_status:
   ├─ "approved" → Continue to generation ✅
   │
   ├─ "needs_revision" → Show recommendations ⚠️
   │   Message: "Анкета требует доработки"
   │   Display: recommendations
   │   Action: User must improve anketa
   │
   └─ "rejected" → Block generation ❌
       Message: "Анкета не подходит для генерации"
       Display: reasons
       Action: User must re-do anketa
   ↓
4. IF approved → Generate grant with ProductionWriter
```

---

## 📝 IMPLEMENTATION PLAN

### Step 1: Add audit check method (30 min)

**File:** `telegram-bot/handlers/grant_handler.py`

**Add method:**
```python
async def _check_or_run_audit(self, session_id: int, anketa_id: str, anketa_data: dict, user_id: int) -> dict:
    """
    Check if audit exists, run if needed
    Returns: {'approved': bool, 'score': float, 'recommendations': list, 'status': str}
    """
    # 1. Check existing audit
    existing_audit = self.db.get_audit_by_session_id(session_id)

    if existing_audit:
        logger.info(f"[AUDIT] Found existing audit for session {session_id}, score: {existing_audit['average_score']}")
        return {
            'approved': existing_audit['approval_status'] == 'approved',
            'score': existing_audit['average_score'],
            'recommendations': existing_audit.get('recommendations', []),
            'status': existing_audit['approval_status']
        }

    # 2. Run new audit
    logger.info(f"[AUDIT] No audit found, running AuditorAgent for session {session_id}")

    # Import AuditorAgent
    from agents.auditor_agent import AuditorAgent

    # Get LLM preference
    llm_provider = self.db.get_user_llm_preference(user_id)

    # Create auditor
    auditor = AuditorAgent(self.db, llm_provider=llm_provider)

    # Run audit
    audit_result = await asyncio.to_thread(
        auditor.audit,
        anketa_data=anketa_data,
        session_id=session_id
    )

    # Return result
    return {
        'approved': audit_result['approval_status'] == 'approved',
        'score': audit_result['average_score'],
        'recommendations': audit_result.get('recommendations', []),
        'status': audit_result['approval_status']
    }
```

**Add DB method:**
```python
# In data/database/models.py

def get_audit_by_session_id(self, session_id: int) -> Optional[Dict]:
    """Get audit result for session"""
    try:
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM auditor_results
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (session_id,))

            row = cursor.fetchone()
            cursor.close()

            return self._dict_row(cursor, row) if row else None

    except Exception as e:
        logger.error(f"Error getting audit: {e}")
        return None
```

---

### Step 2: Integrate audit into generate_grant (45 min)

**File:** `telegram-bot/handlers/grant_handler.py`

**Modify generate_grant method:**

```python
async def generate_grant(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate grant application with AUDIT CHECK"""

    # ... existing code до ProductionWriter ...

    # Get session_id
    session = self.db.get_session_by_anketa_id(anketa_id)
    if not session:
        await update.message.reply_text("❌ Сессия не найдена")
        return

    session_id = session['id']

    # ===== NEW: RUN AUDIT CHECK =====
    await update.message.reply_text(
        "🔍 Проверяю качество анкеты...\n"
        "Это займет ~30 секунд"
    )

    audit_result = await self._check_or_run_audit(
        session_id=session_id,
        anketa_id=anketa_id,
        anketa_data=anketa_data,
        user_id=user_id
    )

    # Check approval status
    if not audit_result['approved']:
        # Not approved - show recommendations
        status = audit_result['status']
        score = audit_result['score']
        recommendations = audit_result.get('recommendations', [])

        if status == 'needs_revision':
            message = f"⚠️ **Анкета требует доработки**\n\n"
            message += f"📊 Оценка качества: {score}/10\n\n"
            message += "**Рекомендации:**\n"

            for i, rec in enumerate(recommendations[:5], 1):
                message += f"{i}. {rec}\n"

            message += "\n💡 Пожалуйста, улучшите анкету и попробуйте снова"

        elif status == 'rejected':
            message = f"❌ **Анкета не подходит для генерации**\n\n"
            message += f"📊 Оценка качества: {score}/10 (минимум 5.0)\n\n"
            message += "**Основные проблемы:**\n"

            for i, rec in enumerate(recommendations[:5], 1):
                message += f"{i}. {rec}\n"

            message += "\n💡 Рекомендуем заполнить анкету заново"

        else:
            message = f"⏳ Анкета на рассмотрении (статус: {status})"

        await update.message.reply_text(message)
        logger.warning(f"[GRANT] Audit blocked generation: {status}, score: {score}")
        return

    # Approved - continue generation
    logger.info(f"[GRANT] Audit approved (score: {audit_result['score']}), proceeding with generation")

    await update.message.reply_text(
        f"✅ Качество анкеты: {audit_result['score']}/10 - отлично!\n"
        f"🚀 Начинаю генерацию грантовой заявки..."
    )

    # ... existing ProductionWriter code ...
```

---

### Step 3: Add database method (15 min)

**File:** `data/database/models.py`

Add `get_audit_by_session_id()` method (see above)

---

### Step 4: Testing (30 min)

**Test Scenario 1: No audit exists**
1. User runs `/generate_grant`
2. System checks audit → Not found
3. System runs AuditorAgent
4. System saves audit result
5. IF approved → Generate grant
6. IF not approved → Show recommendations

**Test Scenario 2: Audit exists - Approved**
1. User runs `/generate_grant`
2. System checks audit → Found, status: approved
3. System proceeds with generation

**Test Scenario 3: Audit exists - Needs Revision**
1. User runs `/generate_grant`
2. System checks audit → Found, status: needs_revision
3. System shows recommendations
4. System blocks generation

**Test Scenario 4: Audit exists - Rejected**
1. User runs `/generate_grant`
2. System checks audit → Found, status: rejected
3. System shows problems
4. System blocks generation

---

## 📊 EXPECTED RESULTS

### Quality Control:

**Before:**
- ❌ Any anketa → Grant generation
- ❌ Garbage data → Garbage grant
- ❌ No feedback to user

**After:**
- ✅ Quality check before generation
- ✅ Only approved anketas → Grant generation
- ✅ Recommendations for improvement
- ✅ User gets feedback

### Metrics:

**Quality:**
- Grant quality improves (only approved anketas)
- User satisfaction improves (better guidance)
- Less wasted resources (no generation on garbage)

**Performance:**
- First generation: +30s (audit time)
- Subsequent generations: +0.1s (cache check)
- Net: Positive (better quality > slight delay)

---

## 🐛 EDGE CASES

### Edge Case 1: Audit fails
**Scenario:** AuditorAgent crashes
**Solution:** Try/except, fallback to warning + continue generation

### Edge Case 2: Audit in progress
**Scenario:** User clicks /generate_grant while audit is running
**Solution:** Check audit status, show "⏳ Audit in progress"

### Edge Case 3: Multiple audits
**Scenario:** Anketa modified after audit
**Solution:** Get latest audit (ORDER BY created_at DESC LIMIT 1)

### Edge Case 4: Audit takes too long
**Scenario:** Audit takes > 60 seconds
**Solution:** Run in background, notify user when done

---

## 🔧 CONFIGURATION

### Audit Score Thresholds (configurable):

```python
AUDIT_THRESHOLDS = {
    'approved': 7.0,        # >= 7.0 → approved
    'needs_revision': 5.0,  # >= 5.0 → needs_revision
    'rejected': 0.0         # < 5.0 → rejected
}
```

### Audit Timeout:
```python
AUDIT_TIMEOUT = 60  # seconds
```

---

## 📝 SUCCESS CRITERIA

- [ ] Audit runs automatically before grant generation
- [ ] Approved anketas proceed to generation
- [ ] Non-approved anketas show recommendations
- [ ] User receives clear feedback about quality
- [ ] Audit result cached (no re-run on same anketa)
- [ ] All tests pass
- [ ] Deployed to production
- [ ] User tested successfully

---

## 🔄 ROLLBACK PLAN

If audit integration causes problems:

1. Comment out audit check in grant_handler.py
2. Restore original behavior (generate without audit)
3. Deploy hotfix
4. Debug audit offline
5. Re-deploy when fixed

**Rollback time:** < 5 minutes

---

## 📞 NEXT ACTIONS

### Immediate:
1. Create `get_audit_by_session_id()` method
2. Create `_check_or_run_audit()` method
3. Integrate into `generate_grant()`
4. Test locally

### Deploy:
1. Apply Pre-Deploy Checklist
2. Commit to git
3. Deploy to production
4. Test with real user

### After Deploy:
1. Monitor audit results
2. Adjust thresholds if needed
3. Collect user feedback
4. Document learnings

---

**Status:** READY TO IMPLEMENT
**Estimated Total Time:** 2-3 hours
**Impact:** HIGH (Quality Control)
**Risk:** LOW (Can rollback easily)

---

🎯 **Goal: Zero garbage grants, 100% quality control!**
