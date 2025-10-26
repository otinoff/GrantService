# Iteration 49: Reviewer/Auditor Agent Testing

**Дата создания:** 2025-10-26
**Статус:** 🟡 PLANNING
**Предыдущая итерация:** Iteration 48 - Writer Agent Fix ✅ COMPLETED
**Цель:** Протестировать Reviewer/Auditor Agent - проверка грантовой заявки по референсам из векторной БД

---

## 🎯 Sprint Goal

> **Протестировать Reviewer Agent: проверка сгенерированной грантовой заявки с аудитом каждого раздела по референсам из векторной БД (коллекция ФПГ данных).**

**Context:**
- У нас есть 2 успешно сгенерированные грантовые заявки (Iteration 48)
- Нужно протестировать как Reviewer/Auditor проверяет качество каждого раздела
- Reviewer должен использовать векторную БД с референсными примерами успешных заявок
- По методологии: `C:\SnowWhiteAI\cradle\Know-How\TESTING-METHODOLOGY.md`

**Input:**
- Грантовая заявка из БД: `GA-20251026-7A4C689D` (53,683 chars)
- Или из файла: `C:\SnowWhiteAI\GrantService\iterations\Iteration_47_Writer_Testing\grant_medium.txt`

**Expected Output:**
- Аудит отчёт по каждому разделу (10 sections)
- Общая оценка качества (score)
- Рекомендации по улучшению
- Сохранение в БД

---

## 📋 Success Criteria

### Обязательные (Must Have):

1. ✅ **Reviewer Agent запускается и работает**
   - Загружает грантовую заявку из БД/файла
   - Обрабатывает все 10 разделов
   - Возвращает структурированный результат

2. ✅ **Векторная БД используется**
   - Подключение к коллекции ФПГ референсов
   - Поиск похожих примеров для каждого раздела
   - Использование в промптах для сравнения

3. ✅ **Аудит каждого раздела**
   - 10 разделов проанализированы отдельно
   - Для каждого: оценка + рекомендации
   - Структурированный JSON output

4. ✅ **Результаты сохраняются в БД**
   - Audit report записывается в таблицу
   - Можно получить по grant_application_number
   - Production-ready storage

### Желательные (Nice to Have):

5. ⚪ Сравнительный анализ MEDIUM vs HIGH качества
6. ⚪ Визуализация результатов аудита
7. ⚪ Автоматические предложения по улучшению

---

## 📊 Задачи (Tasks)

### 1. Анализ Reviewer Agent кода (20 min) ⏸️

- [ ] Найти файл `agents/reviewer_agent.py` или `agents/auditor_agent.py`
- [ ] Понять структуру входных/выходных данных
- [ ] Проверить подключение к векторной БД
- [ ] Определить формат аудит отчёта

### 2. Проверка векторной БД (15 min) ⏸️

- [ ] Найти коллекцию ФПГ референсов
- [ ] Проверить что данные есть
- [ ] Проверить структуру документов
- [ ] Тестовый поиск по векторам

### 3. Создать тестовый скрипт (30 min) ⏸️

**Файл:** `tests/integration/test_reviewer_agent.py`

```python
import pytest
from agents.reviewer_agent import ReviewerAgent
from data.database import get_application_by_number

@pytest.mark.integration
@pytest.mark.gigachat
def test_review_grant_medium_quality():
    """Test Reviewer Agent on MEDIUM quality grant"""

    # 1. LOAD grant from DB
    grant = get_application_by_number('GA-20251026-7A4C689D')
    assert grant is not None
    assert len(grant['content_json']) > 50000

    # 2. REVIEW with Reviewer Agent
    reviewer = ReviewerAgent()
    result = reviewer.review_grant(grant)

    # 3. VALIDATE structure
    assert 'overall_score' in result
    assert 'section_reviews' in result
    assert len(result['section_reviews']) == 10

    # 4. CHECK each section
    for section in result['section_reviews']:
        assert 'section_name' in section
        assert 'score' in section
        assert 'feedback' in section
        assert 'references_used' in section  # Векторная БД

    # 5. SAVE to DB
    assert 'audit_id' in result

    print(f"\n✅ Overall Score: {result['overall_score']}/100")
    print(f"📊 Sections reviewed: {len(result['section_reviews'])}")
```

### 4. Запустить тест (5 min) ⏸️

```bash
python -m pytest tests/integration/test_reviewer_agent.py -xvs --tb=short
```

### 5. Проверить векторную БД integration (20 min) ⏸️

- [ ] Убедиться что Reviewer использует векторную БД
- [ ] Проверить что референсы действительно релевантны
- [ ] Добавить debug output для проверки

### 6. Валидация результатов (15 min) ⏸️

По методологии (TESTING-METHODOLOGY.md):

```python
def validate_reviewer_business_logic(review_result):
    # 1. Structure validation
    assert 'overall_score' in review_result
    assert 0 <= review_result['overall_score'] <= 100

    # 2. Section coverage
    required_sections = ['title', 'summary', 'problem', 'solution',
                        'implementation', 'budget', 'timeline',
                        'team', 'impact', 'sustainability']
    reviewed_sections = [s['section_name'] for s in review_result['section_reviews']]
    for req in required_sections:
        assert req in reviewed_sections

    # 3. Vector DB usage
    for section in review_result['section_reviews']:
        assert len(section.get('references_used', [])) > 0, \
               f"Section {section['section_name']} должен использовать векторную БД"

    # 4. Quality differentiation
    # HIGH grant should score higher than MEDIUM
    # (будет проверено когда протестируем обе заявки)
```

### 7. Документация (10 min) ⏸️

- [ ] Создать ITERATION_49_SUMMARY.md
- [ ] Git commit

**Estimated Time:** ~2 hours

---

## 🔄 Методология: TESTING-METHODOLOGY.md Alignment

### Core Principles Applied:

1. **Production Parity** (Principle 1)
   - Тест использует production imports (`from agents.reviewer_agent import ReviewerAgent`)
   - Тест использует production БД (`get_application_by_number()`)
   - Тест использует production векторную БД

2. **Unified Configuration** (Principle 2)
   - GigaChat API через `unified_llm_client`
   - Vector DB через production config

3. **Integration Testing** (Section 9)
   - End-to-end: Grant → Reviewer → Audit Report → DB
   - Реальные данные, реальные API calls
   - Semantic validation (не точное совпадение, а проверка концепций)

4. **AI/LLM-Specific Testing** (Section 10)
   - Response structure validation
   - Output quality checks
   - Rate limiting awareness
   - Vector DB integration

### Test Structure (Section 9.2):

```python
# 1. SETUP
grant = load_grant_from_db()

# 2. EXECUTE
result = reviewer.review_grant(grant)

# 3. VALIDATE TECHNICAL
assert result is not None
assert 'overall_score' in result

# 4. VALIDATE BUSINESS
validate_reviewer_business_logic(result)

# 5. SAVE & VERIFY
audit_id = save_audit_to_db(result)
assert audit_id is not None
```

---

## 📁 Location References

### Code Files:
- **Reviewer Agent:** `agents/reviewer_agent.py` или `agents/auditor_agent.py`
- **Vector DB:** `shared/vector_db/` или `data/vector_db/`
- **Database:** `data/database/models.py`

### Test Files:
- **New Test:** `tests/integration/test_reviewer_agent.py`
- **Reference:** `tests/integration/test_write_two_grants.py` (успешный пример)

### Data:
- **Grant in DB:** `GA-20251026-7A4C689D` (53,683 chars)
- **Grant file:** `iterations/Iteration_47_Writer_Testing/grant_medium.txt`

### Documentation:
- **Methodology:** `C:\SnowWhiteAI\cradle\Know-How\TESTING-METHODOLOGY.md`
- **GrantService Methodology:** `docs/TESTING-METHODOLOGY-GRANTSERVICE.md`
- **Quick Ref:** `TESTING_QUICK_REF.md`

---

## ⚠️ Risks

1. **Vector DB может быть пустой**
   - Mitigation: Проверить наличие данных перед тестом
   - Fallback: Создать минимальный тестовый датасет

2. **Reviewer Agent может не существовать**
   - Mitigation: Найти аудитор/reviewer код
   - Fallback: Использовать существующий auditor_agent.py

3. **GigaChat rate limit**
   - Mitigation: Sequential execution с delays
   - Expected time: ~2-3 минуты для 10 секций

4. **Формат данных может не совпадать**
   - Mitigation: Сначала изучить структуру
   - Fallback: Адаптировать тест под реальную структуру

---

## 🚀 Quick Start

```bash
# 1. Найти Reviewer Agent
find . -name "*reviewer*" -o -name "*auditor*" | grep -E "\.py$"

# 2. Проверить векторную БД
python -c "from shared.vector_db import check_collections; check_collections()"

# 3. Создать тест
# Редактировать: tests/integration/test_reviewer_agent.py

# 4. Запустить
python -m pytest tests/integration/test_reviewer_agent.py -xvs

# 5. Проверить результаты
python -c "from data.database import db; print(db.get_all_audits())"
```

---

## ✅ Checklist

**Planning:**
- [x] Create 00_ITERATION_PLAN.md
- [ ] Find Reviewer/Auditor Agent code
- [ ] Check Vector DB exists and has data
- [ ] Understand audit report format

**Execution:**
- [ ] Create test_reviewer_agent.py
- [ ] Test on MEDIUM quality grant
- [ ] Validate vector DB usage
- [ ] Check all 10 sections reviewed
- [ ] Verify DB save works

**Validation:**
- [ ] Business logic validation
- [ ] Semantic validation (concepts present)
- [ ] Production parity check

**Documentation:**
- [ ] Create ITERATION_49_SUMMARY.md
- [ ] Git commit

---

**Status:** 🟡 READY TO START
**Next Step:** Find and analyze Reviewer/Auditor Agent code
**Created:** 2025-10-26
**Estimated Completion:** 2025-10-26 (same day, ~2 hours)
