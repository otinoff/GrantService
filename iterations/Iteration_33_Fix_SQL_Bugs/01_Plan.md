# Iteration 33 - Fix SQL Bugs in Grant Handler

**Date Started:** 2025-10-24
**Status:** 🔄 READY TO START
**Previous:** Iteration 32 (ProductionWriter Integration - bugs found)
**Deploy:** Deploy #7 (planned)

---

## 🎯 Goal

Исправить SQL ошибки в database методах для grant handler и обеспечить работу генерации грантов.

---

## 🐛 Problems to Fix

### Critical (Must Fix):

1. **SQL Error: user_id → telegram_id**
   - 3 methods use wrong column name
   - Blocks all grant generation

2. **Interview Not Completing**
   - Anketa not saved to database
   - Blocks grant generation workflow

### Medium (Should Fix):

3. **Verify grants table schema**
   - Check if column is user_id or telegram_id
   - Update grant_handler references

---

## 📋 Detailed Plan

### Step 1: Check Database Schema ✅

**Commands:**
```sql
-- Check grants table
\d grants

-- Check sessions table (already done)
\d sessions
```

**Expected columns:**
- sessions.telegram_id (confirmed)
- grants.user_id or telegram_id? (to verify)

### Step 2: Fix Database Methods

**File:** `data/database/models.py`

**Method 1:** `get_latest_completed_anketa(user_id)` (line ~1122)
```python
# BEFORE:
WHERE user_id = %s AND status = 'completed'

# AFTER:
WHERE telegram_id = %s AND status = 'completed'
```

**Method 2:** `get_latest_grant_for_user(user_id)` (line ~1186)
```python
# BEFORE:
WHERE user_id = %s AND status = 'completed'

# AFTER:
WHERE telegram_id = %s AND status = 'completed'
# OR
WHERE user_id = %s AND status = 'completed'  # if grants table uses user_id
```

**Method 3:** `get_user_grants(user_id)` (line ~1208)
```python
# BEFORE:
WHERE user_id = %s

# AFTER:
WHERE telegram_id = %s  # or user_id depending on grants table
```

### Step 3: Fix Grant Handler References

**File:** `telegram-bot/handlers/grant_handler.py`

**Check all references:**
- `grant['user_id']` → might need `grant['telegram_id']`
- Verify parameter names in method calls

### Step 4: Fix Interview Completion (If Needed)

**File:** `agents/interactive_interviewer_agent_v2.py` or handler

**Issue:** Interview reaches "finalizing" but doesn't save anketa

**Possible causes:**
- Min 10 questions required, only 9 asked
- Finalization logic not completing
- Database save not triggered

**Action:**
- Review completion flow
- Add debug logging
- Ensure anketa saves on completion

### Step 5: Testing

**Local (if possible):**
1. Test database methods with correct column names
2. Verify SQL queries work

**Production:**
1. Deploy fixes
2. Complete full interview
3. Verify anketa created in database
4. Run `/generate_grant`
5. Verify grant generation works
6. Check `/get_grant` and `/list_grants`

---

## 📝 Task Checklist

### Investigation:
- [ ] Query `grants` table schema
- [ ] Identify correct column name (user_id vs telegram_id)
- [ ] Review interview completion logic

### Code Fixes:
- [ ] Fix `get_latest_completed_anketa()` - telegram_id
- [ ] Fix `get_latest_grant_for_user()` - correct column
- [ ] Fix `get_user_grants()` - correct column
- [ ] Update grant_handler.py references
- [ ] Review interview finalization code

### Testing:
- [ ] Test each database method manually
- [ ] Deploy to production
- [ ] Complete full interview test
- [ ] Verify anketa created
- [ ] Test `/generate_grant`
- [ ] Test `/get_grant`
- [ ] Test `/list_grants`

### Documentation:
- [ ] Update BUGS_FOUND.md with solutions
- [ ] Update ITERATION_33_COMPLETE.md
- [ ] Update deployment docs

---

## 🎯 Success Criteria

- [ ] All SQL errors fixed
- [ ] No errors in logs
- [ ] Interview completes and creates anketa
- [ ] `/generate_grant` works end-to-end
- [ ] Grant appears in database
- [ ] `/get_grant` returns grant text
- [ ] `/list_grants` shows user's grants
- [ ] Production stable

---

## 📊 Timeline

**Investigation:** 15 minutes
**Code fixes:** 30 minutes
**Testing:** 30 minutes
**Deployment:** 15 minutes

**Total:** ~1.5 hours

---

## 🔗 Files to Modify

1. `data/database/models.py` - Fix 3 methods
2. `telegram-bot/handlers/grant_handler.py` - Update references
3. Possibly: Interview agent for completion fix

---

## 🚀 Deployment Steps

1. Fix code locally
2. Git commit with fixes
3. Git push to GitHub
4. SSH to production
5. Git pull
6. Restart bot
7. Test full workflow
8. Monitor logs

---

## 📞 Rollback Plan

If bugs persist:
1. Git revert to previous commit (0817e40)
2. Restart bot
3. Investigate further
4. Fix and redeploy

---

## 🔮 After This Iteration

**If successful:**
- Grant generation fully working
- Move to feature enhancements (Iteration 34)
- Add tests to prevent regressions

**Possible future work:**
- Unit tests for database methods
- E2E tests for grant workflow
- Schema documentation in repo

---

**Status:** 📋 PLANNED
**Ready to start:** ✅ YES
**Previous iteration bugs:** Documented in Iteration_32/02_Bugs_Found.md
