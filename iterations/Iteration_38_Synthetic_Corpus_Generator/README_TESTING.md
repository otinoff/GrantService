# Quick Start: Testing Iteration 38

**Date:** 2025-10-25
**Iteration:** 38 - Synthetic Corpus Generator

---

## 🚀 Automated Testing

### Run Full Test Suite:

```bash
cd C:\SnowWhiteAI\GrantService
python test_iteration_38.py
```

**What it tests:**
1. ✅ AnketaSyntheticGenerator initialization
2. ✅ Generate single synthetic anketa (medium quality)
3. ✅ Generate batch of 5 anketas (mixed quality)
4. ✅ Database integration (verify storage)
5. ✅ Batch audit (validate 3 anketas with GigaChat Max)
6. ✅ Corpus statistics

**Duration:** ~3-5 minutes (depends on GigaChat API speed)

**Expected Output:**
```
================================================================================
                 ITERATION 38 AUTOMATED TESTS
================================================================================

[TEST] 1. AnketaSyntheticGenerator Initialization
✅ Generator Initialization - PASSED

[TEST] 2. Generate Single Synthetic Anketa (Medium Quality)
ℹ️  Generating anketa (this may take ~15 seconds)...
✅ Generate Single Anketa - PASSED (Anketa ID: #AN-20251025-test_user-001)

[TEST] 3. Generate Batch (5 anketas, mixed quality)
ℹ️  Generating 5 anketas (this may take ~75 seconds)...
✅ Generate Batch - PASSED (L:1, M:3, H:1)

[TEST] 4. Database Integration (verify synthetic anketas)
✅ Database Integration - PASSED (6 synthetic anketas)

[TEST] 5. Batch Audit (validate 3 synthetic anketas)
ℹ️  Auditing 3 anketas (this may take ~90 seconds)...
✅ Batch Audit - PASSED (Avg: 7.2/10, Audited: 3)

[TEST] 6. Corpus Statistics
✅ Corpus Statistics - PASSED (6 synthetic, 3 audited)

================================================================================
                       TEST SUMMARY
================================================================================

✅ ALL TESTS PASSED (6/6)
ℹ️  Success rate: 100.0%

✅ ITERATION 38 TESTS COMPLETE - ALL PASSED
ℹ️  System ready for production deployment!
```

---

## 📱 Manual Testing via Telegram

### Prerequisites:
1. Telegram bot running: `python telegram-bot/main.py`
2. User authorized (has access token)
3. At least 1 completed anketa exists (for templates)

### Test Commands:

#### 1. Generate Single Anketa:
```
/generate_synthetic_anketa 1 medium
```

#### 2. Generate Batch (Mixed Quality):
```
/generate_synthetic_anketa 10
```

#### 3. Batch Audit:
```
/batch_audit_anketas 10
```

#### 4. View Statistics:
```
/corpus_stats
```

#### 5. List All Anketas:
```
/my_anketas
```

---

## 🔍 Verify Results in Database

### Check Synthetic Anketas:

```sql
-- Count synthetic anketas
SELECT COUNT(*)
FROM sessions
WHERE interview_data->>'synthetic' = 'true';

-- View synthetic anketas with quality
SELECT
    anketa_id,
    interview_data->>'project_name' as project,
    interview_data->>'quality_target' as quality,
    interview_data->>'region' as region,
    completed_at
FROM sessions
WHERE interview_data->>'synthetic' = 'true'
ORDER BY completed_at DESC
LIMIT 10;
```

### Check Audit Results:

```sql
-- View audit results for synthetic anketas
SELECT
    s.anketa_id,
    s.interview_data->>'quality_target' as target_quality,
    ar.average_score,
    ar.approval_status
FROM sessions s
JOIN auditor_results ar ON s.id = ar.session_id
WHERE s.interview_data->>'synthetic' = 'true'
ORDER BY ar.created_at DESC;
```

---

## 📊 Token Usage Estimates

### Per 100 Anketas:

| Operation | Model | Tokens per Item | Total (100 items) |
|-----------|-------|-----------------|-------------------|
| Generation | GigaChat Lite | ~1,500 | ~150,000 |
| Audit | GigaChat Max | ~2,000 | ~200,000 |
| **Total** | | | **~350,000** |

### Weekly Target (7.7M tokens):

- 22 runs × 100 anketas = 2,200 anketas
- ~7.7M total tokens spent
- Excellent for Sber500 demonstration!

---

## ✅ Success Criteria

### Tests Must Pass:

- [x] All 6 automated tests pass
- [x] No Python exceptions
- [x] Database writes successful
- [x] Token usage within ±20% of estimates
- [x] Response times acceptable

### Ready for Production if:

- ✅ Automated tests: **6/6 passed**
- ✅ Manual Telegram tests: All commands work
- ✅ Database integrity: No orphaned records
- ✅ Token usage: Verified with actual API calls

---

## 🐛 Troubleshooting

### Issue: "No template anketas"

**Error:**
```
❌ Не найдено реальных анкет для использования как шаблоны.
```

**Solution:**
1. Create a real anketa via `/start`
2. Complete the interview
3. Verify anketa saved: `/my_anketas`

---

### Issue: "Connection refused" (Database)

**Error:**
```
psycopg2.OperationalError: connection refused
```

**Solution:**
1. Check PostgreSQL is running: `pg_ctl status`
2. Verify port (5432 for local, 5434 for production)
3. Check credentials in code

---

### Issue: GigaChat API errors

**Error:**
```
GigaChat API error: 429 Too Many Requests
```

**Solution:**
1. Add retry logic with exponential backoff
2. Reduce batch size
3. Wait 60 seconds and retry

---

## 📝 Next Steps After Testing

### If Tests Pass:

1. **Git Commit:**
   ```bash
   git add .
   git commit -m "Iteration 38: Synthetic Corpus Generator - TESTED"
   ```

2. **Production Run:**
   - Generate 100 synthetic anketas
   - Audit 100 anketas
   - Spend ~350K tokens

3. **Sber500 Demo:**
   - Show professional token distribution
   - Demonstrate corpus statistics
   - Present architecture

---

### If Tests Fail:

1. Check logs for exceptions
2. Verify database schema
3. Test GigaChat API manually
4. Fix issues and retest

---

**Created:** 2025-10-25
**Purpose:** Quick testing guide for Iteration 38
**Status:** READY ✅
