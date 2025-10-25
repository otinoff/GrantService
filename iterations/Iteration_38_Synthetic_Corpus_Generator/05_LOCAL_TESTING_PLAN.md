# Local Testing Plan: Iteration 38

**Date:** 2025-10-25
**Status:** ⏳ READY TO START
**Iteration:** 38 - Synthetic Corpus Generator

---

## 🎯 OBJECTIVE

Протестировать Iteration 38 локально перед git commit и production deployment.

**Цель:** Убедиться что все команды работают корректно, токены тратятся правильно, база данных обновляется.

---

## 📋 PREREQUISITES

### 1. Environment Check

```bash
# Verify we're in correct directory
cd C:\SnowWhiteAI\GrantService

# Check Python environment
python --version  # Should be Python 3.10+

# Check database is running
psql -h localhost -p 5432 -U postgres -d grantservice -c "SELECT 1"
```

### 2. Bot Running

```bash
# Make sure telegram bot is running
# Check process or restart if needed
python telegram-bot/main.py
```

### 3. User Setup

**Test User:** andrew_otinoff (or current Telegram user)

**Prerequisites:**
- [ ] User has at least 1 completed anketa (for template)
- [ ] User is authorized (has access token)
- [ ] User has GigaChat API access

---

## 🧪 TEST PLAN

### Phase 1: Basic Functionality Tests

#### Test 1.1: Generate 1 Synthetic Anketa

**Command:**
```
/generate_synthetic_anketa 1 medium
```

**Expected Result:**
```
🔄 Генерирую 1 синтетических анкет...
💡 Используется: GIGACHAT-LITE
📊 Качество: medium
⏱️ Примерное время: ~15 секунд

✅ Синтетические анкеты созданы!

📊 Статистика:
• Сгенерировано: 1 анкет
• Сохранено в БД: 1 анкет
• Использовано токенов: ~1,500 (GigaChat Lite)

Качество:
• Low: 0 анкет
• Medium: 1 анкет
• High: 0 анкет

Используйте /corpus_stats для общей статистики
```

**Verification:**
```sql
-- Check in database
SELECT anketa_id, status, completed_at
FROM sessions
WHERE telegram_id = <USER_ID>
ORDER BY completed_at DESC
LIMIT 1;

-- Check interview_data contains synthetic flag
SELECT interview_data->>'synthetic' as is_synthetic,
       interview_data->>'quality_target' as quality,
       interview_data->>'project_name' as project
FROM sessions
WHERE telegram_id = <USER_ID>
  AND interview_data->>'synthetic' = 'true'
ORDER BY completed_at DESC
LIMIT 1;
```

**Pass Criteria:**
- [x] Bot responds within 30 seconds
- [x] No errors in bot logs
- [x] Anketa saved to database
- [x] `synthetic: true` flag present
- [x] `quality_target: 'medium'` present
- [x] Token usage shown (~1,500 Lite)

---

#### Test 1.2: Generate 5 Synthetic Anketas (Mixed Quality)

**Command:**
```
/generate_synthetic_anketa 5
```

**Expected Result:**
```
📊 Качество: mixed (20% low, 50% medium, 30% high)

✅ Синтетические анкеты созданы!

📊 Статистика:
• Сгенерировано: 5 анкет
• Сохранено в БД: 5 анкет
• Использовано токенов: ~7,500 (GigaChat Lite)

Качество:
• Low: 1 анкет
• Medium: 3 анкет  (50% of 5 = 2.5 ≈ 3)
• High: 1 анкет   (30% of 5 = 1.5 ≈ 1)
```

**Verification:**
```sql
-- Count synthetic anketas by quality
SELECT
    interview_data->>'quality_target' as quality,
    COUNT(*) as count
FROM sessions
WHERE telegram_id = <USER_ID>
  AND interview_data->>'synthetic' = 'true'
GROUP BY quality;
```

**Pass Criteria:**
- [x] 5 anketas generated
- [x] Distribution approximately matches (20/50/30)
- [x] All have different project names
- [x] Token usage ~7,500 Lite

---

#### Test 1.3: Batch Audit 5 Anketas

**Command:**
```
/batch_audit_anketas 5
```

**Expected Result:**
```
🔄 Запускаю batch аудит 5 анкет...
💡 Используется: GigaChat Max (критично для Sber500!)
📊 Ожидаемое использование: ~10,000 Max tokens
⏱️ Примерное время: ~150 секунд

✅ Batch аудит завершён!

📊 Результаты:
• Проверено: 5 анкет
• Средний балл: 6.8/10  (depends on quality)

Распределение:
• ✅ Одобрено (≥7.0): 2-3
• ⚠️ Требует доработки (5.0-6.9): 2-3
• ❌ Отклонено (<5.0): 0-1

Токены:
• Использовано: ~10,000 Max tokens
• Стоимость: ~10 руб (из 1,987,948 доступных)

💡 Отлично для демонстрации Sber500!
```

**Verification:**
```sql
-- Check audit results
SELECT
    s.anketa_id,
    ar.average_score,
    ar.approval_status,
    s.interview_data->>'quality_target' as target_quality
FROM sessions s
JOIN auditor_results ar ON s.id = ar.session_id
WHERE s.telegram_id = <USER_ID>
  AND s.interview_data->>'synthetic' = 'true'
ORDER BY ar.created_at DESC
LIMIT 5;
```

**Pass Criteria:**
- [x] 5 anketas audited
- [x] All have `average_score` in database
- [x] All have `approval_status` set
- [x] Scores correlate with quality targets:
  - Low: ~4-6/10
  - Medium: ~6-8/10
  - High: ~7-9/10
- [x] Token usage ~10,000 Max

---

#### Test 1.4: Corpus Statistics

**Command:**
```
/corpus_stats
```

**Expected Result:**
```
📊 Статистика корпуса анкет

Общее количество: 7  (1 real + 6 synthetic)
• Реальные: 1
• Синтетические: 6

Аудит:
• Проверено: 5
• Не проверено: 2  (1 synthetic + 1 real if not audited)
• Средний балл: 6.8/10

Качество (проверенные):
• ✅ Одобрено: 2-3
• ⚠️ Требует доработки: 2-3
• ❌ Отклонено: 0-1

Использование токенов:
• GigaChat Lite: ~9,000
• GigaChat Max: ~10,000

💡 Используйте:
• /generate_synthetic_anketa [N] - создать ещё
• /batch_audit_anketas [N] - проверить качество
```

**Pass Criteria:**
- [x] Correct count of anketas
- [x] Correct synthetic vs real split
- [x] Correct audit statistics
- [x] Token estimates reasonable

---

### Phase 2: Edge Cases & Error Handling

#### Test 2.1: Invalid Parameters

**Commands:**
```
/generate_synthetic_anketa 0
/generate_synthetic_anketa 101
/generate_synthetic_anketa abc
/generate_synthetic_anketa 10 invalid_quality
/batch_audit_anketas -1
/batch_audit_anketas 501
```

**Expected Results:**
- Error messages for each invalid input
- No anketas generated
- No database writes

---

#### Test 2.2: No Template Anketas Available

**Scenario:** New user with no completed anketas

**Command:**
```
/generate_synthetic_anketa 1
```

**Expected Result:**
```
❌ Не найдено реальных анкет для использования как шаблоны.

Сначала создайте хотя бы одну анкету через /start
```

---

#### Test 2.3: No Unaudited Anketas

**Scenario:** All anketas already audited

**Command:**
```
/batch_audit_anketas 10
```

**Expected Result:**
```
❌ Нет анкет для аудита.

Все ваши анкеты уже проверены.
```

---

### Phase 3: Performance & Load Tests

#### Test 3.1: Generate 10 Anketas (Stress Test)

**Command:**
```
/generate_synthetic_anketa 10
```

**Expected Behavior:**
- Progress updates every 10 anketas (won't see for 10, but code tested)
- ~150 seconds total time (15 sec/anketa)
- ~15,000 Lite tokens used
- All 10 saved successfully

---

#### Test 3.2: Batch Audit 20 Anketas

**Command:**
```
/batch_audit_anketas 20
```

**Expected Behavior:**
- Progress update at 10/20
- ~10 minutes total time (30 sec/anketa)
- ~40,000 Max tokens used
- All 20 audited successfully

---

### Phase 4: Integration Tests

#### Test 4.1: Full Workflow

**Steps:**
1. `/generate_synthetic_anketa 10 medium`
2. `/corpus_stats` (verify 10 synthetic, 0 audited)
3. `/batch_audit_anketas 10`
4. `/corpus_stats` (verify 10 synthetic, 10 audited)
5. `/my_anketas` (verify list shows synthetic anketas)

**Expected:**
- Full pipeline works end-to-end
- Database consistent
- Token counts accurate

---

#### Test 4.2: Existing Commands Still Work

**Verify no regressions:**

```
/my_anketas          # Should still work
/audit_anketa        # Should still work on real anketas
/delete_anketa       # Should work on synthetic anketas
/generate_grant      # Should work with synthetic anketa
```

---

## 📊 SUCCESS CRITERIA

### Must Pass:

- [x] All basic functionality tests (1.1-1.4) pass
- [x] No Python exceptions in bot logs
- [x] Database integrity maintained
- [x] Token usage within expected ranges (±20%)
- [x] Response times acceptable (<30s for single, <5min for batch)

### Nice to Have:

- [x] All edge case tests (2.1-2.3) pass
- [x] Performance tests (3.1-3.2) complete without errors
- [x] Integration tests (4.1-4.2) pass
- [x] No regressions in existing commands

---

## 🐛 KNOWN ISSUES TO WATCH

### Potential Issues:

1. **GigaChat API Rate Limiting:**
   - If generating 100+ anketas, may hit rate limits
   - Solution: Add exponential backoff retry logic

2. **Database Connection Pooling:**
   - Batch operations may exhaust connection pool
   - Solution: Ensure connections are closed properly

3. **Memory Usage:**
   - Generating 100 embeddings in memory might be heavy
   - Solution: Process in smaller batches

4. **JSON Parsing from GigaChat:**
   - Already fixed in AnketaSyntheticGenerator (lines 262-311)
   - But watch for new edge cases

---

## 📝 TEST EXECUTION LOG

### Test Session: 2025-10-25

| Test | Command | Status | Notes |
|------|---------|--------|-------|
| 1.1 | `/generate_synthetic_anketa 1 medium` | ⏳ | |
| 1.2 | `/generate_synthetic_anketa 5` | ⏳ | |
| 1.3 | `/batch_audit_anketas 5` | ⏳ | |
| 1.4 | `/corpus_stats` | ⏳ | |
| 2.1 | Invalid params | ⏳ | |
| 2.2 | No templates | ⏳ | |
| 2.3 | No unaudited | ⏳ | |
| 3.1 | Generate 10 | ⏳ | |
| 3.2 | Audit 20 | ⏳ | |
| 4.1 | Full workflow | ⏳ | |
| 4.2 | Regression | ⏳ | |

---

## 🚀 NEXT STEPS AFTER TESTING

### If All Tests Pass:

1. **Document Results:**
   - Update test log with results
   - Note any issues found and fixes applied
   - Calculate actual token usage

2. **Git Commit:**
   ```bash
   git add .
   git commit -m "Iteration 38: Synthetic Corpus Generator

   Features:
   - /generate_synthetic_anketa: Generate 1-100 synthetic anketas (GigaChat Lite)
   - /batch_audit_anketas: Batch audit using GigaChat Max
   - /corpus_stats: Show corpus statistics

   Testing:
   - All tests passed locally
   - Token usage verified (~350K per 100 anketas)
   - Database integration working

   Files:
   - agents/anketa_synthetic_generator.py (NEW)
   - telegram-bot/handlers/anketa_management_handler.py (+442 lines)
   - telegram-bot/main.py (+20 lines)
   - data/database/models.py (+97 lines)

   Iteration: 38
   Status: TESTED LOCALLY, READY FOR PRODUCTION"
   ```

3. **Prepare for Production:**
   - Test on production server (optional)
   - Monitor first production run
   - Document token usage

4. **Run Production Batch:**
   - Generate 100 synthetic anketas
   - Audit 100 anketas
   - Spend ~350K tokens
   - Demonstrate to Sber500

---

### If Tests Fail:

1. **Debug Issues:**
   - Check bot logs for exceptions
   - Verify database queries
   - Test LLM API responses

2. **Fix and Retest:**
   - Apply fixes
   - Re-run failed tests
   - Verify no regressions

3. **Document Issues:**
   - Note issues found
   - Document fixes applied
   - Update testing plan if needed

---

## 📄 FILES TO MONITOR

### Log Files:

```bash
# Bot logs
telegram-bot/logs/*.log

# Database logs
/var/log/postgresql/*.log  (on server)

# GigaChat API logs
Check bot output for API errors
```

### Database Tables:

```sql
-- Sessions (anketas)
SELECT COUNT(*) FROM sessions WHERE interview_data->>'synthetic' = 'true';

-- Audits
SELECT COUNT(*) FROM auditor_results;

-- Check for orphaned records
SELECT COUNT(*) FROM sessions s
LEFT JOIN auditor_results ar ON s.id = ar.session_id
WHERE ar.id IS NULL AND s.status = 'completed';
```

---

**Created:** 2025-10-25
**Purpose:** Local testing plan for Iteration 38
**Status:** READY TO EXECUTE ✅
**Next Step:** Start Test 1.1
