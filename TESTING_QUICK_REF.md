# Testing Quick Reference - GrantService

**Полная методология:** `docs/TESTING-METHODOLOGY-GRANTSERVICE.md`

---

## 🎯 Business Logic Testing Principles

### 1. End-to-End Validation (строки 336-428 методологии)

**Что тестировать:**
- ✅ Полный flow: Interview → Writer → Auditor
- ✅ Реалистичные данные (synthetic user simulator)
- ✅ Сохранение в БД
- ✅ Бизнес-требования (30K+ chars, quality score 7+)

### 2. Semantic Validation (строки 732-790)

**Проверяем смысл, не код:**
```python
# ❌ НЕ ТАК:
assert grant.sections['problem'] == "Expected text"  # Точное совпадение

# ✅ ТАК:
required_concepts = ["innovation", "methodology", "budget", "team"]
assert validator.contains_concepts(grant.content, required_concepts)
```

### 3. Success Criteria (строки 899-912)

**Метрики качества:**
- Iterations per feature: 4-5 → **1-2** (60% reduction)
- First-try success: 58% → **90%+**
- Time on debugging: 80% → **20%**
- Production bugs: High → **Near zero**

---

## 📊 Grant Quality Requirements

### Minimum Production Standards:

1. **Length:** ≥30,000 chars (методология line 398)
2. **Sections:** 10 полных разделов (не заглушки!)
3. **Business Concepts:**
   - Problem: Детальное описание проблемы
   - Solution: Конкретная методология/технология
   - Budget: Детализация по статьям расходов
   - Team: ФИО, опыт, роли членов команды
   - Impact: Измеримые результаты (KPI)

4. **Quality Differentiation:**
   - MEDIUM: Базовая детализация
   - HIGH: +30% длины, больше примеров, цифр, ссылок

### Запрещённые заглушки:

❌ "Проблема требует решения"
❌ "Инновационное решение"
❌ "План реализации на X месяцев"
❌ "Профессиональная команда"
❌ "Значительный социальный эффект"

---

## 🔧 Test Structure Template

```python
def test_grant_generation_e2e():
    """E2E: Full production flow with business validation"""

    # 1. GENERATE
    grant = writer.generate(anketa_id=test_anketa.id)

    # 2. TECHNICAL VALIDATION (код работает)
    assert grant.id is not None
    assert grant.status == 'success'

    # 3. BUSINESS VALIDATION (результат полезен)
    validate_business_requirements(grant)
    validate_no_stubs(grant.content)
    validate_semantic_quality(grant.content)

    # 4. SAVE & VERIFY
    saved = db.get_grant(grant.id)
    assert saved.content == grant.content
```

---

## 📁 Location References

- **Методология (полная):** `docs/TESTING-METHODOLOGY-GRANTSERVICE.md`
- **E2E примеры:** Методология строки 336-428
- **Semantic validation:** Методология строки 732-790
- **Success criteria:** Методология строки 899-912
- **GigaChat rate limiting:** Методология строки 665-723

---

## 🚨 Current Issues (Iteration 47)

### Проблема: Writer Agent генерирует заглушки

**Симптомы:**
- Title + Summary: ✅ Детальные
- Остальные 8 секций: ❌ Заглушки ("Проблема требует решения")

**Решение:**
1. Улучшить промпты в `agents/writer_agent.py` (lines 283-336)
2. Добавить business validation в тест
3. Использовать audit recommendations для детализации

### Критерий прохождения:

✅ Тест проходит **И** заявка проходит business validation
❌ Тест проходит **НО** заявка - заглушки (текущее состояние)

---

**Создано:** 2025-10-26
**Iteration:** 47
**Статус:** Reference для всех будущих тестов
