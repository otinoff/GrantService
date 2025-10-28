# Iteration 62: Fix Research Results Parsing (N/A Bug)

**Date:** 2025-10-29 01:05 MSK
**Status:** 🔧 IN PROGRESS
**Priority:** 🔥 CRITICAL (breaks research file output)
**Parent:** Iteration 61 - Research Results File Generation

---

## 🐛 Problem

**User Report:** Research file shows `N/A` for all answers
```
=== ЗАПРОС 1 ===

Вопрос: официальная статистика неизвестная проблема Россия 2022-2025

Ответ:
N/A

------------------------------------------------------------
```

**Root Cause Found:**

`generate_research_txt()` looks for wrong key in query_data!

**File:** `shared/telegram_utils/file_generators.py:462`

```python
# WRONG (current code):
answer = query_data.get('answer', 'N/A')
```

But `researcher_agent.py` returns data structure:
```python
{
    'query': '...',
    'result': {              # ← Data is HERE!
        'summary': '...',    # ← Answer text
        'raw_response': '...'
    }
}
```

And saved in `research_anketa()` as:
```python
results['queries'].append({
    'name': 'Официальная статистика',
    'query': q1['query'],
    'result': q1['result']   # ← {'summary': ..., 'raw_response': ...}
})
```

**Correct parsing:**
```python
# CORRECT:
result = query_data.get('result', {})
answer = result.get('summary', 'N/A')
```

---

## 📊 Impact

### Before Fix:
```
Все 3 ответа: N/A
Sources: 0 (не извлекаются)
User видит пустой файл ❌
Writer не получает research data ❌
```

### After Fix:
```
Все 3 ответа: реальные тексты из Claude Code WebSearch ✅
Sources: URLs из WebSearch результатов ✅
User видит полный файл с данными ✅
Writer получает research data для грантов ✅
```

---

## 🎯 Solution

### Step 1: Fix Answer Extraction

**File:** `shared/telegram_utils/file_generators.py`

**Line 462: Change answer extraction**
```python
# BEFORE (WRONG):
answer = query_data.get('answer', 'N/A')

# AFTER (CORRECT):
result = query_data.get('result', {})
answer = result.get('summary', 'N/A')
```

**Full context (lines 460-478):**
```python
for i, query_data in enumerate(queries, 1):
    query_text = query_data.get('query', 'N/A')

    # FIX: Extract answer from nested 'result' dict
    result = query_data.get('result', {})
    answer = result.get('summary', 'N/A')

    # TODO: Extract sources from WebSearch response
    # For now, sources list is empty - needs separate fix
    sources = query_data.get('sources', [])

    lines.append(f"=== ЗАПРОС {i} ===")
    lines.append("")
    lines.append(f"Вопрос: {query_text}")
    lines.append("")
    lines.append("Ответ:")
    lines.append(answer)
    lines.append("")

    if sources:
        lines.append("Источники:")
        for source in sources:
            lines.append(f"  • {source}")
        lines.append("")

    lines.append("-" * 60)
    lines.append("")
```

---

### Step 2: Fix Sources Extraction (Optional - Future)

**Current Issue:** Sources are not extracted from Claude Code WebSearch response

**WebSearch response structure:**
```json
{
    "response": "...",
    "citations": [
        {
            "url": "https://rosstat.gov.ru/...",
            "title": "..."
        }
    ]
}
```

**Future Enhancement (Iteration 63):**
- Parse Claude Code WebSearch citations
- Extract URLs from response
- Add to sources list

**For Now (Iteration 62):**
- Focus on fixing answer extraction only
- Sources extraction = deferred to Iteration 63

---

## 📝 Implementation Plan

### Phase 1: Code Fix (5 min)

**File:** `shared/telegram_utils/file_generators.py`

**Change:**
```python
# Line 460-463 (inside for loop)
for i, query_data in enumerate(queries, 1):
    query_text = query_data.get('query', 'N/A')

    # ✅ FIX: Extract from nested result.summary
    result = query_data.get('result', {})
    answer = result.get('summary', 'N/A')

    sources = query_data.get('sources', [])
```

---

### Phase 2: Testing (5 min)

**Test 1: Check existing research file**
1. Get anketa_id from failed research
2. Regenerate file with fix
3. Verify answers are NOT N/A

**Test 2: New research flow**
1. Create new anketa
2. Complete interview + audit
3. Run research
4. Check file - answers should contain real text

**Expected Output:**
```
=== ЗАПРОС 1 ===

Вопрос: официальная статистика неизвестная проблема Россия 2022-2025

Ответ:
РЕЗЮМЕ: По данным Росстата, в России в 2022-2024 годах наблюдалась тенденция...
[200-300 слов реального текста]

------------------------------------------------------------
```

---

### Phase 3: Deployment (5 min)

**Steps:**
1. Commit fix to master
2. Push to GitHub
3. SSH to production
4. Pull changes
5. Restart bot
6. Verify with real user flow

---

## ✅ Success Criteria

- [ ] Fixed answer extraction in `generate_research_txt()`
- [ ] Answers are NOT "N/A" (contain real text)
- [ ] File shows real WebSearch results
- [ ] Code deployed to production
- [ ] Bot restarted successfully
- [ ] User verification: file contains real answers

---

## 🧪 Testing

### Manual Test

**Input:** anketa_30_1761566498 (from user screenshot)

**Current Output:**
```
Ответ:
N/A
```

**Expected After Fix:**
```
Ответ:
РЕЗЮМЕ: [Real WebSearch result from Claude Code]
[200-300 words of actual data]
```

---

## 📁 Files to Modify

**Modified:**
1. `shared/telegram_utils/file_generators.py` (1 line change)
   - Line 462: Fix answer extraction

**Created:**
2. `iterations/Iteration_62_Fix_Research_Results_Parsing/00_PLAN.md` (this file)
3. `iterations/Iteration_62_Fix_Research_Results_Parsing/SUCCESS.md` (after deployment)

---

## 🔗 Related Iterations

**Parent:** Iteration 61 - Research Results File Generation
- Added `generate_research_txt()` function
- BUT had wrong key for answer extraction

**This Iteration (62):**
- Fix answer extraction key: 'answer' → 'result.summary'
- Fixes N/A bug

**Next:** Iteration 63 - Extract Sources from WebSearch Citations
- Parse Claude Code citations
- Show real URLs in file

---

## 📅 Timeline

**Start:** 2025-10-29 01:05 MSK
**Estimated:** 15 minutes
**ETA:** 2025-10-29 01:20 MSK

**Breakdown:**
- Code fix: 5 min
- Testing: 5 min
- Deployment: 5 min

---

## 💡 Why This Happened

**Iteration 61:** Created `generate_research_txt()` based on assumed data structure
**Iteration 60:** `researcher_agent.py` returns nested structure `{'result': {'summary': ...}}`
**Mismatch:** Generator looked for `'answer'` key, but data is in `'result.summary'`

**Lesson:** Always check actual data structure returned by API/agent before writing parser!

---

## 🎉 Expected Outcome

**After Iteration 62:**
- ✅ Research file shows REAL answers (not N/A)
- ✅ Writer receives research data with real statistics
- ✅ Grants strengthened with WebSearch data
- ✅ $200 Claude Code subscription value demonstrated

---

**Created by:** Claude Code
**Date:** 2025-10-29 01:05 MSK
**Priority:** CRITICAL (blocks research data flow)
**Status:** 🔧 IN PROGRESS

**Next Steps:**
1. Apply fix to `file_generators.py`
2. Test with anketa_30_1761566498
3. Deploy to production
4. Verify user sees real answers
