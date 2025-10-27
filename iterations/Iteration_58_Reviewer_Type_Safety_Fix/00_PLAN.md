# Iteration 58: Reviewer Type Safety Fix

**Date:** 2025-10-27
**Status:** ✅ FIXED - Ready for Deployment
**Priority:** P0 - CRITICAL
**Related:** Iteration_57 (field mapping fix introduced this bug)

---

## 📋 Overview

**Problem:** Reviewer crashes with "'str' object has no attribute 'get'" after Iteration_57 deployment

**User Impact:**
- ❌ Ревью не работает: "❌ Произошла ошибка при ревью"
- ❌ Пользователь не получает оценку гранта
- ❌ Полная поломка ревью функции

**Root Cause:** Missing type checks - код предполагает что данные всегда словари/списки словарей, но не защищен от:
- `None` values
- Strings instead of dicts
- Lists of strings instead of lists of dicts

---

## 🔍 Root Cause Analysis

### Error in Production Logs

```
ERROR:agents.reviewer_agent:❌ Reviewer Evidence: Ошибка оценки: 'str' object has no attribute 'get'
ERROR:agents.reviewer_agent:❌ Reviewer Matching: Ошибка оценки: 'str' object has no attribute 'get'
ERROR:agents.reviewer_agent:❌ Reviewer: Ошибка оценки: object of type 'NoneType' has no len()
```

### Проблемные места в коде

**1. Line 331 (`_evaluate_evidence_base_async`)**
```python
# BEFORE:
has_official = any(
    any(source.lower() in c.get('source', '').lower() for source in official_sources)
    for c in citations  # ← Если citations = ["string1", "string2"], то c.get() упадет!
)
```

**2. Line 375 (`_evaluate_evidence_base_async`)**
```python
# BEFORE:
unique_sources = set([c.get('source', '') for c in citations if c.get('source')])
# ← Если citations = ["string"], то c.get() упадет!
```

**3. Lines 341-353 (`_evaluate_evidence_base_async`)**
```python
# BEFORE:
if research_results:  # ← Если research_results = "string", то .get() упадет!
    block1 = research_results.get('block1_problem', {})
```

**4. Lines 512-532 (`_evaluate_matching_async`)**
```python
# BEFORE:
has_kpi = any(task.get('kpi') for task in key_tasks)
# ← Если key_tasks = ["string"], то task.get() упадет!

has_natproject = any('нацпроект' in p.get('name', '').lower() for p in programs)
# ← Если programs = ["string"], то p.get() упадет!
```

**5. Line 195 (`review_grant_async`)**
```python
# BEFORE:
logger.info(f"📊 Reviewer: Получены данные - цитаты: {len(citations)}, таблицы: {len(tables)}")
# ← Если citations = None или tables = None, то len() упадет!
```

---

## 🎯 Solution

### Defensive Coding: Type Safety Checks

**1. Protect from None values**
```python
# Line 191-192:
citations = input_data.get('citations', []) or []  # ← Если None, то []
tables = input_data.get('tables', []) or []
```

**2. Check if citations/tables are dicts before calling .get()**
```python
# Line 332:
for c in citations if isinstance(c, dict)  # ← ADD TYPE CHECK

# Line 375:
for c in citations if isinstance(c, dict) and c.get('source')
```

**3. Check if research_results is dict before calling .get()**
```python
# Line 341, 351:
if research_results and isinstance(research_results, dict):  # ← ADD TYPE CHECK
    block1 = research_results.get('block1_problem', {})
```

**4. Check if tasks/programs are dicts in _evaluate_matching_async**
```python
# Line 513:
has_kpi = any(task.get('kpi') for task in key_tasks if isinstance(task, dict))

# Line 532:
has_natproject = any('нацпроект' in p.get('name', '').lower() for p in programs if isinstance(p, dict))

# Line 500:
if isinstance(first_goal, dict):
    smart_check = first_goal.get('smart_check', {})
```

---

## 🧪 Testing

### Test 1: Empty Data (как в production handler)
```python
review_input = {
    'grant_content': {},
    'user_answers': {},
    'research_results': {},  # Пустой словарь
    'citations': [],  # Пустой список
    'tables': [],
    'selected_grant': {}
}

result = await reviewer.review_grant_async(review_input)
assert 'review_score' in result  # ✅ PASS
```

### Test 2: Wrong Types (строки вместо словарей)
```python
review_input = {
    'research_results': "invalid string",  # ← Неправильный тип!
    'citations': ["string1", "string2"],  # ← Список строк!
    # ...
}

result = await reviewer.review_grant_async(review_input)
assert 'review_score' in result  # ✅ PASS - не падает!
```

### Test 3: None Values
```python
review_input = {
    'research_results': None,
    'citations': None,
    'tables': None,
    # ...
}

result = await reviewer.review_grant_async(review_input)
assert 'review_score' in result  # ✅ PASS
```

**Result:**
```
PASS: score=0.3, status=rejected
```

---

## 📦 Deployment

### Commit & Push
```bash
git add agents/reviewer_agent.py
git add iterations/Iteration_58_Reviewer_Type_Safety_Fix/
git add test_reviewer_simple.py test_reviewer_quick.py

git commit -m "fix(reviewer): Add type safety checks for None/wrong types

- Fix 'str' object has no attribute 'get' errors
- Add isinstance() checks for citations, research_results, programs, tasks
- Protect from None values with 'or []' syntax
- Prevents reviewer crashes on malformed data

Fixes:
- citations/tables can be None → protected with 'or []'
- citations can be list of strings → check isinstance(c, dict)
- research_results can be string → check isinstance(..., dict)
- programs/tasks can be list of strings → check isinstance(p, dict)

Related: Iteration_58
Tested: test_reviewer_simple.py PASSED"

git push origin master
```

### Production Deployment
```bash
ssh root@5.35.88.251
cd /var/GrantService
git pull origin master
systemctl restart grantservice-bot
systemctl status grantservice-bot  # Verify running
```

---

## 🎓 Lessons Learned

### Pattern: Defensive Programming

**Problem:**
Code assumes data types but doesn't validate them:
- Assumes `citations` is list of dicts → crashes on list of strings
- Assumes `research_results` is dict → crashes on string
- Assumes values are not None → crashes on None

**Solution:**
1. **Type Guards:** Use `isinstance(x, dict)` before calling `.get()`
2. **None Protection:** Use `x or []` or `x or {}`
3. **Try-Except:** Wrap in try-except as last resort

**Code Pattern:**
```python
# BAD:
for item in items:
    value = item.get('key')  # ← Crashes if items = ["string"]

# GOOD:
for item in items if isinstance(item, dict):
    value = item.get('key')  # ← Safe!
```

### Add to GRANTSERVICE-LESSONS-LEARNED.md

```markdown
## Type Safety Pattern (Iteration_58)

**Problem:** Code crashes when data types don't match expectations

**Examples:**
- Iteration_58: Reviewer crashes on wrong types (None, strings instead of dicts)

**Solution:**
1. Use isinstance() checks before accessing methods
2. Protect from None with 'or []' / 'or {}'
3. Wrap risky code in try-except

**Prevention:**
- Add type hints: `def func(data: Dict[str, Any])`
- Use Pydantic models for validation
- Add integration tests with malformed data
```

---

## 📊 Expected Results

### Before Fix
```
❌ Произошла ошибка при ревью. Попробуйте позже.
```

### After Fix
```
✅ Ревью завершено!
Оценка: 6.2/10
СТАТУС: ⚠️ ТРЕБУЕТСЯ ДОРАБОТКА
```

---

## 📝 Files

### Modified
- `agents/reviewer_agent.py` - Added type safety checks (9 locations)

### Created
- `iterations/Iteration_58_Reviewer_Type_Safety_Fix/00_PLAN.md` (this file)
- `test_reviewer_simple.py` - Simple type safety test
- `test_reviewer_quick.py` - Comprehensive type safety test

### Related
- `telegram-bot/handlers/interactive_pipeline_handler.py` - Passes empty data to reviewer

---

## ✅ Checklist

**Planning**
- [x] Identified root cause (missing type checks)
- [x] Documented problem and solution
- [x] Created 00_PLAN.md

**Implementation**
- [x] Add type checks for citations (2 places)
- [x] Add type checks for research_results (3 places)
- [x] Add type checks for programs/tasks (3 places)
- [x] Add None protection for citations/tables
- [x] Test locally (PASSED)

**Deployment**
- [ ] Commit changes
- [ ] Push to GitHub
- [ ] Deploy to production
- [ ] Restart bot

**Verification**
- [ ] User tests review feature
- [ ] Verify ревью works (not "Ошибка")
- [ ] Create SUCCESS.md

**Documentation**
- [ ] Update GRANTSERVICE-LESSONS-LEARNED.md
- [ ] Mark Iteration_58 as complete
- [ ] Close Iteration_57 (was OK, Iteration_58 is separate bug)

---

**Created by:** Claude Code
**Date:** 2025-10-27
**Time:** 20:30 MSK (17:30 UTC)
**Related:** Iteration_57 (field mapping - unrelated bug)
