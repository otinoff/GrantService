# Iteration 48: Writer Agent Fix - LLM Generation for All Sections

**Дата создания:** 2025-10-26
**Статус:** 🟡 PLANNING
**Предыдущая итерация:** Iteration 47 - Writer Testing ⚠️ PARTIAL
**Цель:** Исправить Writer Agent чтобы генерировать реальный контент через LLM (не заглушки)

---

## 🎯 Sprint Goal

> **Исправить Writer Agent: убрать hardcoded заглушки, добавить LLM генерацию для ВСЕХ 10 секций.**

**Problem Statement (из Iteration 47):**
```python
# agents/writer_agent.py lines 314-336
# Упрощенная генерация остальных полей для быстрого тестирования
content['problem'] = user_answers.get('problem', 'Проблема требует решения')  # ← ЗАГЛУШКА!
content['solution'] = user_answers.get('solution', 'Инновационное решение')  # ← ЗАГЛУШКА!
```

**Current State:**
- ❌ 8/10 секций = hardcoded stubs
- ❌ Результат: 2311 chars (требование: 30K+)
- ❌ Business validation: FAIL

**Target State:**
- ✅ 10/10 секций генерируются через GigaChat LLM
- ✅ Результат: 30,000+ chars
- ✅ Business validation: PASS
- ✅ No stubs ("Проблема требует решения", etc.)

---

## 📋 Success Criteria

### Обязательные (Must Have):

1. ✅ **LLM генерация для ВСЕХ секций**
   - `title` ✅ (уже работает)
   - `summary` ✅ (уже работает)
   - `problem` ❌ → ✅ (НОВОЕ)
   - `solution` ❌ → ✅ (НОВОЕ)
   - `implementation` ❌ → ✅ (НОВОЕ)
   - `budget` ❌ → ✅ (НОВОЕ)
   - `timeline` ❌ → ✅ (НОВОЕ)
   - `team` ❌ → ✅ (НОВОЕ)
   - `impact` ❌ → ✅ (НОВОЕ)
   - `sustainability` ❌ → ✅ (НОВОЕ)

2. ✅ **Length requirement:**
   - MEDIUM quality: ≥20,000 chars
   - HIGH quality: ≥30,000 chars

3. ✅ **No stubs:**
   - Запрещённые фразы не встречаются
   - Каждая секция содержит детальный текст

4. ✅ **Business validation passes:**
   - Required concepts present
   - Quality differentiation (HIGH > MEDIUM)

### Желательные (Nice to Have):

5. ⚪ Использование audit recommendations
6. ⚪ Разная детализация для MEDIUM vs HIGH
7. ⚪ PDF generation

---

## 📊 Задачи (Tasks)

### 1. Анализ текущего кода (15 min) ⏸️

- [ ] Прочитать agents/writer_agent.py lines 283-344
- [ ] Понять структуру промптов (title, summary работают)
- [ ] Определить где менять код

### 2. Создать промпты для секций (30 min) ⏸️

**Для каждой секции создать LLM промпт:**

- [ ] `problem`: Детальное описание проблемы (500-1000 слов)
- [ ] `solution`: Предлагаемое решение (800-1500 слов)
- [ ] `implementation`: План реализации (1000-2000 слов)
- [ ] `budget`: Детализация бюджета (500-800 слов)
- [ ] `timeline`: График работ (300-500 слов)
- [ ] `team`: Описание команды (400-600 слов)
- [ ] `impact`: Ожидаемый эффект (600-1000 слов)
- [ ] `sustainability`: Устойчивость (400-600 слов)

**Формат промпта:**
```python
prompt = f"""
Ты - эксперт по грантовым заявкам.

КОНТЕКСТ:
- Проект: {user_answers.get('project_name')}
- Описание: {user_answers.get('description')}

ЗАДАЧА:
Напиши детальное описание [СЕКЦИИ] для грантовой заявки.

ТРЕБОВАНИЯ:
- Объём: [MIN-MAX] слов
- Стиль: формальный, убедительный
- Детализация: {quality_level} (MEDIUM/HIGH)

ФОРМАТ:
[Конкретные требования для секции]
"""
```

### 3. Исправить writer_agent.py (60 min) ⏸️

**Изменения в `_generate_application_content_async()`:**

```python
# OLD (lines 314-336):
content['problem'] = user_answers.get('problem', 'Проблема требует решения')

# NEW:
problem_prompt = f"""
Ты - эксперт по грантовым заявкам.
Проект: {user_answers.get('project_name', '')}
Описание: {user_answers.get('description', '')}

Напиши детальное описание ПРОБЛЕМЫ для грантовой заявки (500-1000 слов).
Объясни:
- В чём суть проблемы?
- Почему она важна?
- Кого это затрагивает?
- Какие последствия если не решить?
"""
content['problem'] = await client.generate_text(problem_prompt, 2000)
await asyncio.sleep(6)  # GigaChat rate limit
```

**Реализовать для ВСЕХ 8 секций.**

### 4. Добавить rate limiting (10 min) ⏸️

- [ ] Добавить `await asyncio.sleep(6)` между LLM вызовами
- [ ] Итого: ~60 секунд для 10 секций (приемлемо)

### 5. Тестирование (30 min) ⏸️

- [ ] Запустить test_write_two_grants.py
- [ ] Проверить длину результата (≥20K chars)
- [ ] Проверить отсутствие заглушек
- [ ] Сравнить MEDIUM vs HIGH

### 6. Business Validation (20 min) ⏸️

Добавить в тест:

```python
def validate_grant_business_logic(grant_text, quality_level):
    # 1. Length
    if quality_level == "HIGH":
        assert len(grant_text) >= 30000, f"HIGH must be ≥30K: {len(grant_text)}"
    else:
        assert len(grant_text) >= 20000, f"MEDIUM must be ≥20K: {len(grant_text)}"

    # 2. No stubs
    forbidden_stubs = [
        "Проблема требует решения",
        "Инновационное решение",
        "План реализации на",
        "Профессиональная команда",
        "Значительный социальный эффект"
    ]
    for stub in forbidden_stubs:
        assert stub not in grant_text, f"Found forbidden stub: {stub}"

    # 3. Required concepts
    required = ["проблем", "решен", "бюджет", "команд", "результат"]
    for concept in required:
        assert concept in grant_text.lower(), f"Missing concept: {concept}"
```

### 7. Документация (15 min) ⏸️

- [ ] Создать ITERATION_48_SUMMARY.md
- [ ] Git commit

**Estimated Time:** ~3 hours

---

## 🔄 Методология: 5-Step Workflow

### STEP 1: PLAN (15%) ✅ CURRENT
- [x] Создать 00_ITERATION_PLAN.md
- [x] Определить success criteria
- [x] Estimate time

### STEP 2: DEVELOP (60%)
- [ ] Написать промпты для 8 секций
- [ ] Исправить writer_agent.py
- [ ] Добавить rate limiting

### STEP 3: TEST (15%)
- [ ] Запустить integration tests
- [ ] Проверить business validation
- [ ] Сравнить MEDIUM vs HIGH

### STEP 4: DOCUMENT (10%)
- [ ] Создать ITERATION_48_SUMMARY.md
- [ ] Git commit

### STEP 5: MEASURE
- [ ] Length: 20K+ (MEDIUM), 30K+ (HIGH)
- [ ] Quality: No stubs
- [ ] Time: <10 min generation

---

## 🎓 Learning from Iteration 47

### ❌ Что пошло не так:

1. **Test-Production Mismatch** (методология line 28-34)
   - Тест проходил ✅
   - Но production был сломан ❌

2. **Hardcoded stubs вместо LLM**
   - Комментарий: "для быстрого тестирования"
   - Забыли заменить на production код

3. **Business validation не была добавлена**
   - Не проверили длину результата
   - Не проверили отсутствие заглушек

### ✅ Что применяем в Iteration 48:

1. **Production-First Approach**
   - Код сразу для production
   - Никаких "для тестирования"

2. **Business Validation ОБЯЗАТЕЛЬНА**
   - Длина ≥20K/30K chars
   - Отсутствие stubs
   - Required concepts

3. **End-to-End Testing**
   - От user_answers до final grant
   - Проверка реального контента

---

## 📊 Ожидаемые метрики

### До исправления (Iteration 47):
```
MEDIUM: 2311 chars (❌ <20K)
HIGH:   2371 chars (❌ <30K)
Stubs:  8/10 секций (❌)
```

### После исправления (Iteration 48 target):
```
MEDIUM: 20,000-25,000 chars (✅)
HIGH:   30,000-40,000 chars (✅)
Stubs:  0/10 секций (✅)
Quality differentiation: HIGH > MEDIUM (✅)
```

### Execution time:
```
LLM calls: 10 секций × 6s rate limit = 60s
+ generation time ~3-5s per section = ~90-120s total
Target: <10 минут (acceptable)
```

---

## 🔗 References

- **Iteration 47 Summary:** `iterations/Iteration_47_Writer_Testing/ITERATION_47_SUMMARY.md`
- **Testing Methodology:** `docs/TESTING-METHODOLOGY-GRANTSERVICE.md`
- **Quick Reference:** `TESTING_QUICK_REF.md`
- **Writer Agent:** `agents/writer_agent.py` lines 283-344
- **Test:** `tests/integration/test_write_two_grants.py`

---

## ⚠️ Risks

1. **GigaChat rate limit (429 errors)**
   - Mitigation: `await asyncio.sleep(6)` между вызовами ✅

2. **Generation time >10 минут**
   - Mitigation: Ограничить max_tokens для каждой секции

3. **Quality может быть низкой**
   - Mitigation: Итеративно улучшать промпты

4. **Parser всё ещё извлекает мало полей**
   - Impact: MEDIUM - промпты компенсируют это
   - Solution: Исправить в следующей итерации

---

## 🚀 Quick Start

```bash
# 1. Прочитать текущий код
code agents/writer_agent.py:283-344

# 2. Внести изменения (добавить LLM промпты)

# 3. Запустить тест
python -m pytest tests/integration/test_write_two_grants.py -xvs

# 4. Проверить результаты
cat iterations/Iteration_47_Writer_Testing/grant_medium.txt | wc -m  # Should be ≥20K
cat iterations/Iteration_47_Writer_Testing/grant_high.txt | wc -m    # Should be ≥30K
```

---

## ✅ Checklist

**Planning:**
- [x] Create 00_ITERATION_PLAN.md
- [ ] Read writer_agent.py current implementation
- [ ] Design prompts for 8 sections

**Execution:**
- [ ] Implement LLM generation for problem
- [ ] Implement LLM generation for solution
- [ ] Implement LLM generation for implementation
- [ ] Implement LLM generation for budget
- [ ] Implement LLM generation for timeline
- [ ] Implement LLM generation for team
- [ ] Implement LLM generation for impact
- [ ] Implement LLM generation for sustainability
- [ ] Add rate limiting (asyncio.sleep)

**Testing:**
- [ ] Run integration test
- [ ] Verify length ≥20K (MEDIUM), ≥30K (HIGH)
- [ ] Verify no stubs
- [ ] Verify required concepts present

**Documentation:**
- [ ] Create ITERATION_48_SUMMARY.md
- [ ] Git commit

---

**Status:** 🟡 READY TO START
**Next Step:** Read writer_agent.py and design prompts
**Created:** 2025-10-26
**Estimated Completion:** 2025-10-26 (same day, ~3 hours)
