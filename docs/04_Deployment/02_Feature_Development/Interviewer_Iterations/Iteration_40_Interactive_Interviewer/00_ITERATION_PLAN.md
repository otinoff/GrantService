# Iteration 40: Interactive Interviewer Testing

**Date:** 2025-10-25
**Status:** 🚀 PLANNED
**Iteration:** 40 - Interactive Interviewer Testing

---

## 🎯 OBJECTIVE

**Goal:** Протестировать Interactive Interviewer Agent с автоматической симуляцией пользовательских ответов, проверить создание и связывание anketa_id в полном воркфлоу.

**Success Criteria:**
- ✅ Interviewer задаёт все 15 вопросов
- ✅ Принимает симулированные ответы пользователя
- ✅ Заполняет все обязательные поля (15 полей)
- ✅ Создаёт уникальный anketa_id
- ✅ Сохраняет в БД (sessions.interview_data)
- ✅ Готово для Audit Chain (Iteration 41)

---

## 📊 ПОЛНЫЙ ВОРКФЛОУ (Связь Итераций)

### **Iteration 38:** ✅ Synthetic Corpus Generator
```
OUTPUT: anketa_id (#AN-YYYYMMDD-username-NNN)
STATUS: DONE
```

### **Iteration 39:** ⏸️ RL Optimization
```
STATUS: PAUSED (GigaChat truncation issue)
```

### **Iteration 40:** 🎯 Interactive Interviewer ← **СЕЙЧАС**
```
INPUT: Симулированные ответы пользователя
PROCESS: InteractiveInterviewer → 15 вопросов/ответов
OUTPUT: anketa_id → sessions.anketa_id
СВЯЗЬ: sessions.anketa_id (PRIMARY KEY)
```

### **Iteration 41:** 📝 Audit Chain (СЛЕДУЮЩАЯ)
```
INPUT: anketa_id (из Iteration 40)
PROCESS: AnketaValidator → audit
OUTPUT: auditor_results.session_id → sessions.id
СВЯЗЬ: auditor_results ↔ sessions (через anketa_id)
```

### **Iteration 42:** 📄 Grant Writing
```
INPUT: anketa_id + audit_result
PROCESS: GrantWriter → grant document
OUTPUT: grant_id (#GR-YYYYMMDD-username-NNN)
СВЯЗЬ: grant_applications.anketa_id → sessions.anketa_id
```

---

## 🔗 НОМЕНКЛАТУРА (ID-Связывание)

### **Полная Цепочка:**

```
1. ANKETA_ID (#AN-20251025-username-001)
   ├─ sessions.anketa_id (PRIMARY KEY)
   ├─ sessions.id (FOREIGN KEY для audit)
   └─ sessions.interview_data (JSON с данными)

2. AUDIT_ID (auditor_results.id)
   ├─ auditor_results.session_id → sessions.id
   ├─ auditor_results.average_score (0-10)
   └─ auditor_results.approval_status

3. GRANT_ID (#GR-20251025-username-001)
   ├─ grant_applications.id
   ├─ grant_applications.anketa_id → sessions.anketa_id
   └─ grant_applications.document_path (PDF/DOCX)
```

### **SQL Связи:**

```sql
-- Anketa → Audit:
SELECT ar.*
FROM auditor_results ar
JOIN sessions s ON ar.session_id = s.id
WHERE s.anketa_id = '#AN-20251025-user-001';

-- Anketa → Grant:
SELECT ga.*
FROM grant_applications ga
WHERE ga.application_number = '#AN-20251025-user-001';

-- Full Chain (Anketa → Audit → Grant):
SELECT
    s.anketa_id,
    ar.average_score,
    ar.approval_status,
    ga.id as grant_id,
    ga.document_path
FROM sessions s
LEFT JOIN auditor_results ar ON s.id = ar.session_id
LEFT JOIN grant_applications ga ON s.anketa_id = ga.application_number
WHERE s.anketa_id = '#AN-20251025-user-001';
```

---

## 📝 ТЕСТ-КЕЙСЫ

### **Test 1: Complete Interview (Happy Path)**

**Описание:** Симулируем пользователя, который отвечает на все 15 вопросов корректно.

**Steps:**
1. Инициализировать InteractiveInterviewer
2. Симулировать 15 ответов пользователя:
   - project_name: "Тестовый проект культурного развития молодежи"
   - organization: "АНО 'Молодежные инициативы'"
   - region: "Москва"
   - problem: "Недостаточная вовлечённость молодёжи в культурные мероприятия..."
   - solution: "Создание молодёжного культурного центра..."
   - goals: ["Цель 1", "Цель 2", "Цель 3"]
   - activities: ["Мероприятие 1", "Мероприятие 2", "Мероприятие 3", "Мероприятие 4"]
   - results: ["Результат 1", "Результат 2", "Результат 3"]
   - budget: "1500000"
   - budget_breakdown: {"equipment": "500000", "teachers": "600000", "materials": "300000", "other": "100000"}
3. Проверить создание anketa_id
4. Проверить сохранение в sessions.interview_data

**Expected Output:**
```python
{
    'anketa_id': '#AN-20251025-test_user_iter40-001',
    'status': 'completed',
    'all_fields_filled': True,
    'fields_count': 15
}
```

---

### **Test 2: Short Answers (Min Length Validation)**

**Описание:** Проверяем обработку коротких ответов (менее минимальной длины).

**Steps:**
1. Отвечаем короткими ответами:
   - problem: "Плохо" (< 200 chars)
   - solution: "Хорошо" (< 150 chars)
2. Проверяем что Interviewer:
   - ✅ Запрашивает дополнительную информацию
   - ✅ Не принимает короткие ответы
   - ✅ Повторяет вопрос

**Expected Output:**
```python
{
    'validation_failed': True,
    'reason': 'Answers too short',
    'retry_count': 2
}
```

---

### **Test 3: Long Answers (Max Length Handling)**

**Описание:** Проверяем обработку длинных ответов (> 2000 chars).

**Steps:**
1. Отвечаем очень длинными ответами (3000+ chars)
2. Проверяем что система:
   - ✅ Принимает длинные ответы
   - ✅ Сохраняет полностью в JSON
   - ✅ Не обрезает данные

**Expected Output:**
```python
{
    'long_answers_accepted': True,
    'problem_length': 3000,
    'solution_length': 2500
}
```

---

### **Test 4: Invalid Answers (Validation)**

**Описание:** Проверяем обработку некорректных ответов.

**Test Cases:**
- budget: "много денег" (не число)
- budget: "-500000" (отрицательное)
- budget: "0" (слишком мало)
- goals: [] (пустой список)
- region: "Нью-Йорк" (не российский регион)

**Expected Output:**
```python
{
    'validation_errors': [
        'Budget must be positive number',
        'Goals cannot be empty',
        'Region must be Russian region'
    ]
}
```

---

### **Test 5: Multiple Anketas (Unique IDs)**

**Описание:** Создаём 10 анкет и проверяем уникальность anketa_id.

**Steps:**
1. Создаём 10 анкет для разных пользователей
2. Проверяем что все anketa_id уникальные
3. Проверяем формат: `#AN-YYYYMMDD-username-NNN`

**Expected Output:**
```python
{
    'anketas_created': 10,
    'unique_ids': True,
    'format_valid': True,
    'anketa_ids': [
        '#AN-20251025-user1-001',
        '#AN-20251025-user1-002',
        '#AN-20251025-user2-001',
        ...
    ]
}
```

---

### **Test 6: Anketa → Audit Chain Preparation**

**Описание:** Проверяем что anketa готова для Audit Chain (Iteration 41).

**Steps:**
1. Создаём anketa через Interviewer
2. Получаем anketa_id
3. Проверяем структуру данных для Audit:
   - ✅ sessions.id существует
   - ✅ sessions.anketa_id = '#AN-...'
   - ✅ sessions.status = 'completed'
   - ✅ sessions.interview_data заполнено (15 полей)

**Expected Output:**
```python
{
    'ready_for_audit': True,
    'session_id': 123,
    'anketa_id': '#AN-20251025-test_user-001',
    'fields_complete': 15
}
```

---

## 🧪 AUTOMATED TEST SCRIPT

**Файл:** `test_iteration_40_interviewer.py`

**Структура:**

```python
class Iteration40Test:
    """Automated tests for Interactive Interviewer"""

    async def test_1_complete_interview(self):
        """Test 1: Complete 15-question interview"""
        pass

    async def test_2_short_answers(self):
        """Test 2: Validation of short answers"""
        pass

    async def test_3_long_answers(self):
        """Test 3: Handling long answers"""
        pass

    async def test_4_invalid_answers(self):
        """Test 4: Validation errors"""
        pass

    async def test_5_multiple_anketas(self):
        """Test 5: Create 10 unique anketas"""
        pass

    async def test_6_audit_chain_prep(self):
        """Test 6: Verify anketa ready for Audit Chain"""
        pass
```

---

## 📊 EXPECTED RESULTS

### **Success Metrics:**

```
✅ Test 1: PASS - Complete interview (15 fields filled)
✅ Test 2: PASS - Short answers rejected (validation works)
✅ Test 3: PASS - Long answers accepted (no truncation)
✅ Test 4: PASS - Invalid answers rejected (validation works)
✅ Test 5: PASS - 10 unique anketa_ids created
✅ Test 6: PASS - Anketa ready for Audit Chain
```

**Overall:** 6/6 tests PASSED ← **TARGET**

---

## 🔍 DATABASE VERIFICATION

### **После Тестов:**

```sql
-- Check anketas created:
SELECT
    anketa_id,
    status,
    completed_at,
    interview_data->>'project_name' as project
FROM sessions
WHERE telegram_id = 999999999  -- test user
ORDER BY created_at DESC
LIMIT 10;

-- Verify all 15 fields present:
SELECT
    anketa_id,
    jsonb_object_keys(interview_data) as field_name
FROM sessions
WHERE anketa_id = '#AN-20251025-test_user_iter40-001';

-- Count should be 15 fields
```

---

## 📁 FILES TO CREATE

1. **`00_ITERATION_PLAN.md`** ← THIS FILE
2. **`test_iteration_40_interviewer.py`** - Automated test script
3. **`01_TEST_RESULTS.md`** - Test execution log
4. **`02_ANKETA_IDS.txt`** - List of created anketa_ids
5. **`03_AUDIT_CHAIN_READY.md`** - Verification for Iteration 41
6. **`04_SUMMARY.md`** - Final summary

---

## 🚀 EXECUTION PLAN

### **Step 1: Setup**
```bash
cd C:\SnowWhiteAI\GrantService
python test_iteration_40_interviewer.py
```

**Duration:** ~10-15 minutes

### **Step 2: Verify Results**
```bash
# Check database
psql -U postgres -d grantservice -c "SELECT COUNT(*) FROM sessions WHERE telegram_id = 999999999;"
```

### **Step 3: Document**
- Save test results to `01_TEST_RESULTS.md`
- List anketa_ids to `02_ANKETA_IDS.txt`

---

## 🔗 INTEGRATION WITH ITERATION 41

**После Iteration 40:**

1. ✅ У нас есть 10+ anketa_ids
2. ✅ Все anketas завершены (status='completed')
3. ✅ Все 15 полей заполнены

**Iteration 41 сможет:**
```python
# Получить anketa_id из Iteration 40:
anketa_ids = ['#AN-20251025-user-001', '#AN-20251025-user-002', ...]

# Запустить audit:
for anketa_id in anketa_ids:
    audit_result = await validator.validate(anketa_id)
    # Сохранить в auditor_results
```

---

## 💡 KEY INSIGHTS

### **Что Тестируем:**

1. **Функциональность Interviewer:**
   - ✅ Задаёт правильные вопросы
   - ✅ Принимает ответы
   - ✅ Валидирует данные

2. **Создание anketa_id:**
   - ✅ Уникальность
   - ✅ Формат `#AN-YYYYMMDD-username-NNN`
   - ✅ Сохранение в sessions.anketa_id

3. **Подготовка к Audit Chain:**
   - ✅ sessions.id существует
   - ✅ sessions.status = 'completed'
   - ✅ interview_data заполнено (15 полей)

### **Что НЕ Тестируем:**

- ❌ Audit (это Iteration 41)
- ❌ Grant Writing (это Iteration 42)
- ❌ RL Optimization (это Iteration 39)

---

## 📊 TOKEN USAGE

**Минимальное использование:**
- InteractiveInterviewer: ~5,000 tokens per anketa (GigaChat)
- 10 anketas: ~50,000 tokens
- **TOTAL**: ~50,000 tokens

**Очень экономно!** ← Не требует Max модели

---

## 🎯 SUCCESS CRITERIA

### **Must Pass:**

- [x] Test 1: Complete interview (15 fields) ← **CRITICAL**
- [x] Test 5: Multiple anketas (10 unique IDs) ← **CRITICAL**
- [x] Test 6: Audit chain preparation ← **CRITICAL**

### **Nice to Have:**

- [ ] Test 2: Short answer validation
- [ ] Test 3: Long answer handling
- [ ] Test 4: Invalid answer errors

**Minimum:** 3/6 tests must pass (Tests 1, 5, 6)
**Target:** 6/6 tests pass ← **IDEAL**

---

## 📝 NEXT STEPS (After Iteration 40)

### **Iteration 41: Audit Chain**
```
INPUT: anketa_ids (from Iteration 40)
PROCESS: AnketaValidator → audit
OUTPUT: auditor_results (linked to anketa_id)
```

### **Iteration 42: Grant Writing**
```
INPUT: anketa_id + audit_result
PROCESS: GrantWriter → generate grant
OUTPUT: grant_id + PDF document
```

---

**Created:** 2025-10-25
**Status:** PLANNED
**Ready to Execute:** ✅ YES

---

## 📌 QUICK START

```bash
# 1. Run automated tests
cd C:\SnowWhiteAI\GrantService
python test_iteration_40_interviewer.py

# 2. Verify database
psql -U postgres -d grantservice -c "SELECT anketa_id, status FROM sessions WHERE telegram_id = 999999999 LIMIT 10;"

# 3. Review results
cat C:\SnowWhiteAI\GrantService_Project\Development\02_Feature_Development\Interviewer_Iterations\Iteration_40_Interactive_Interviewer\01_TEST_RESULTS.md
```

**Estimated Time:** 10-15 minutes
**Token Usage:** ~50,000 tokens
**Cost:** ~5 руб

**LET'S GO! 🚀**
