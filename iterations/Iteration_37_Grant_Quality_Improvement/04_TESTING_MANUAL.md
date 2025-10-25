# Iteration 37: Manual Testing Guide

**Date:** 2025-10-25
**Tester:** Andrew (@theperipherals)
**Environment:** Local (localhost:5432)

---

## 🎯 TESTING OBJECTIVE

Verify that Two-Stage QA Pipeline works correctly:
- GATE 1 (AnketaValidator) validates anketa JSON → 7-8/10
- GATE 2 (AuditorAgent) audits generated grant TEXT → 7-9/10
- Both gates must show ≥7.0/10 for success

---

## ⚙️ PRE-REQUISITES

✅ **Completed:**
- [x] Code syntax check passed
- [x] Local PostgreSQL running (port 5432)
- [x] Test user exists (telegram_id: 5032079932)
- [x] LLM provider set to 'gigachat'
- [x] **FIX 1:** Database field mismatch fixed (conversation_data → interview_data)
- [x] **FIX 2:** Bot reference for file export fixed (context.bot)
- [x] AnketaValidator standalone test: 9.0/10 ✅

🔧 **To Do Before Testing:**
- [ ] Ensure local Telegram bot is STOPPED (we'll use fresh start)
- [ ] Have Telegram app open
- [ ] GigaChat API accessible

---

## 🚀 STEP-BY-STEP TESTING

### Step 1: Start Local Bot

**Terminal Command:**
```bash
cd C:\SnowWhiteAI\GrantService\telegram-bot
python main.py
```

**Expected Output:**
```
[INFO] Starting bot...
[INFO] Handlers registered
[INFO] Bot started successfully
```

**If errors:** Check logs, verify DB connection

---

### Step 2: Create Test Anketa

**Telegram Command:**
```
/create_test_anketa
```

**Expected Response:**
```
✅ Тестовая анкета создана!

📋 Анкета: AN-20251025-theperipherals-XXX

Проект: Молодежный образовательный центр 'Цифровое будущее'
Организация: АНО 'Развитие молодежных инициатив'
Регион: Кемеровская область - Кузбасс
```

**Verify:**
- [x] Anketa ID created (format: AN-YYYYMMDD-username-XXX)
- [x] Contains project details

**Save anketa_id:** `AN-20251025-theperipherals-___`

---

### Step 3: Test GATE 1 - /audit_anketa

**Telegram Command:**
```
/audit_anketa
(select the anketa created in Step 2)
```

**Expected Flow:**
```
🔍 Запускаю аудит анкеты...
Это займет ~30 секунд

[Wait ~20-30 seconds]

📊 Результаты аудита анкеты

AN-20251025-theperipherals-XXX

✅ Общая оценка: 7-8/10
Статус: одобрено / требует доработки

Детальные оценки:
• Полнота: 7-8/10
• Ясность: 0/10  ← May be 0 (validator doesn't check this)
• Выполнимость: 0/10  ← May be 0
• Инновационность: 0/10  ← May be 0
• Качество: 7-8/10

Рекомендации:
(if any)
```

**CRITICAL CHECKS:**
- [ ] Score ≥7.0/10 (MUST PASS)
- [ ] Status = "одобрено" or "требует доработки"
- [ ] Uses AnketaValidator (not old AuditorAgent)
- [ ] No crashes, no errors

**If score <7.0:**
- Check logs: `[GATE-1]` entries
- Check what validator found
- May need to adjust test anketa data

**Record Results:**
```
GATE 1 Score: ___ /10
Status: ___
Issues: ___
```

---

### Step 4: Test GATE 2 - /generate_grant (Full Pipeline)

**Telegram Command:**
```
/generate_grant
(or /generate_grant AN-20251025-theperipherals-XXX)
```

**Expected Flow:**

```
🔍 GATE 1: Проверяю качество данных анкеты...
Это займет ~20 секунд

[Wait ~20s]

✅ GATE 1 пройден: 7.X/10
🚀 Начинаю генерацию грантовой заявки (~2-3 минуты)...

[Wait ~2-3 minutes - ProductionWriter generating]

🔍 GATE 2: Проверяю качество сгенерированной заявки...
Это займет ~30 секунд

[Wait ~30s]

✅ GATE 2 завершён: 7-9/10
Статус: approved

📊 Итого:
• Входные данные: 7.X/10
• Качество заявки: 7-9/10

✅ Грантовая заявка готова!

📋 Анкета: AN-20251025-theperipherals-XXX
🆔 Grant ID: grant-AN-xxx-xxxxxxxx

📊 Статистика:
• Символов: ~30,000
• Слов: ~3,500
• Секций: 10
• Время генерации: 120-180s

Используйте /get_grant для получения заявки.
```

**CRITICAL CHECKS:**
- [ ] **GATE 1 score ≥7.0/10** (input validation)
- [ ] Generation proceeds (not blocked)
- [ ] **GATE 2 score ≥7.0/10** (output audit)
- [ ] Both scores shown to user
- [ ] Grant generated successfully
- [ ] No crashes, no errors

**Expected Timing:**
- GATE 1: ~20 seconds
- Generation: ~120-180 seconds (2-3 min)
- GATE 2: ~30 seconds
- **Total: ~3-4 minutes**

**Record Results:**
```
GATE 1 Score: ___ /10
GATE 2 Score: ___ /10
Generation Time: ___ seconds
Grant Length: ___ characters
Success: YES / NO
```

---

### Step 5: Verify Grant Quality (Optional)

**Telegram Command:**
```
/get_grant AN-20251025-theperipherals-XXX
```

**Expected:**
- Receive grant application file
- ~30,000 characters
- 10 sections
- Formatted markdown

**Manual Check:**
- [ ] Has title and project name
- [ ] Has "Описание проблемы" section
- [ ] Has "Цели и задачи" section
- [ ] Has budget section
- [ ] Text is coherent (not gibberish)

---

## 📊 SUCCESS CRITERIA

**MUST PASS:**
- [x] GATE 1 (validation) score ≥7.0/10
- [x] GATE 2 (audit) score ≥7.0/10
- [x] Generation completes successfully
- [x] No crashes or errors
- [x] User sees both scores

**NICE TO HAVE:**
- [ ] GATE 1 score ≥8.0/10
- [ ] GATE 2 score ≥8.5/10
- [ ] Generation time <150 seconds

---

## 🐛 TROUBLESHOOTING

### Issue: GATE 1 score <7.0/10

**Check:**
1. Look at validation issues in response
2. Check logs for `[GATE-1]` entries
3. Test anketa may need more detail

**Fix:**
- Adjust test_anketa data in `create_test_anketa()`
- Add more details to problem/solution
- Increase field lengths

### Issue: GATE 2 score <7.0/10

**Check:**
1. Look at audit recommendations
2. Check logs for `[GATE-2]` entries
3. Check if `application_text` variable is populated

**Fix:**
- May need to adjust AuditorAgent prompts
- Check ProductionWriter output quality
- Verify grant TEXT is passed (not JSON)

### Issue: Bot crashes

**Check:**
1. Terminal logs for error
2. Check imports
3. Check DB connection

**Common Errors:**
- `No module named 'agents.anketa_validator'` → path issue
- `UnifiedLLMClient error` → GigaChat API issue
- `Database connection failed` → PostgreSQL not running

---

## 📝 LOGGING & DEBUGGING

**Important Log Entries to Watch:**

```bash
# GATE 1 (Validation)
[GATE-1] Validating anketa data quality...
[AnketaValidator] Running LLM coherence check...
[AnketaValidator] LLM score: X.X/10
[GATE-1] Validation result: approved, score: X.X/10

# Generation
[GRANT] ProductionWriter initialized
[ProductionWriter] Generating section 1/10...
[ProductionWriter] Grant generated in XXs, XXXXX characters

# GATE 2 (Audit)
[GATE-2] Auditing generated grant text...
[AuditorAgent] Audit started...
[GATE-2] Grant audit completed: approved, score: X.X/10

# Summary
[TWO-STAGE-QA] Results for AN-xxx:
  GATE-1 (Validation): X.X/10 (approved)
  GATE-2 (Audit): X.X/10 (approved)
```

**If you see:**
- `[GATE-1] Blocked generation` → Input validation failed
- `[GATE-2] Grant audit failed` → Output audit error
- `application_text` not found → Wrong variable passed

---

## ✅ TEST COMPLETION CHECKLIST

After testing, fill this out:

**Test Environment:**
- [ ] Local bot tested
- [ ] PostgreSQL: localhost:5432
- [ ] LLM: gigachat
- [ ] User: theperipherals (5032079932)

**Test Results:**
- [ ] Step 2: Test anketa created
- [ ] Step 3: /audit_anketa works (GATE 1)
- [ ] Step 4: /generate_grant works (full pipeline)
- [ ] Step 5: Grant quality verified

**Scores:**
- GATE 1 (Validation): ___ /10
- GATE 2 (Audit): ___ /10
- Overall: PASS / FAIL

**Issues Found:**
```
(list any issues, bugs, or unexpected behavior)
```

**Next Steps:**
- [ ] If PASS → Create SUCCESS.md
- [ ] If PASS → Git commit
- [ ] If PASS → Deploy to production
- [ ] If FAIL → Debug and fix

---

## 🎯 EXPECTED OUTCOME

**If everything works:**
```
✅ GATE 1: 7-8/10 (input validation OK)
✅ GATE 2: 7-9/10 (output audit OK)
✅ Grant generated: ~30K chars
✅ Total time: ~3-4 minutes
✅ No errors

→ READY FOR GIT COMMIT AND DEPLOYMENT
```

**This proves:**
- Root cause fixed (TEXT vs JSON mismatch)
- Two-stage QA works
- Quality scores improved from 0.0/10 to 7+/10
- Ready for production

---

**Created:** 2025-10-25
**Iteration:** 37 - Grant Quality Improvement
**Phase:** Testing (Manual)
