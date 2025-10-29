# Iteration 65: E2E Pipeline с Контролем Качества

**Date:** 2025-10-29 23:00 MSK
**Status:** 🔧 IN PROGRESS
**Priority:** 🔥 CRITICAL (буткемп Сбера - deadline 30 октября)
**Parent:** Iteration 64 - Full E2E Pipeline

---

## 🎯 Goal

Переписать E2E pipeline с **автоматической проверкой качества** и **повторами при неудаче**.

**Проблема Iteration 64:**
- ✅ 25 файлов созданы
- ❌ Grant файлы пустые (0 символов)
- ❌ Нет проверки качества
- ❌ Нет повторов при ошибках

**Решение:**
- Проверять каждый файл после создания
- Если качество плохое → повторять (max 3 попытки)
- Гарантировать минимальный размер и содержимое

---

## 📊 Критерии Качества

### Anketa (247+ строк)
```python
- Минимум 5000 символов
- Все 6 полей заполнены
- Нет "N/A" значений
- Нет пустых строк
```

### Research (50+ строк)
```python
- Минимум 3 запроса
- Все ответы заполнены (нет N/A)
- Минимум 3000 символов
```

### Grant (200+ строк) ← **ГЛАВНОЕ!**
```python
- Минимум 15000 символов
- Обязательные разделы присутствуют
- Нет TODO/INSERT заглушек
- Полноценный текст гранта
```

### Audit (25+ строк)
```python
- Минимум 500 символов
- Оценка присутствует
- Рекомендации есть
```

### Review (18+ строк)
```python
- Минимум 400 символов
- Оценка качества
- Замечания/рекомендации
```

---

## 🔧 Новая Архитектура

### До (Iteration 64):
```
step1() → save → export
step2() → save → export
step3() → save → export
step4() → save → export  ← ПУСТОЙ ГРАНТ!
step5() → save → export
```

### После (Iteration 65):
```
step1() → save → export → ✅ CHECK → если плохо: RETRY (max 3)
step2() → save → export → ✅ CHECK → если плохо: RETRY
step3() → save → export → ✅ CHECK → если плохо: RETRY
step4() → save → export → ✅ CHECK → если плохо: RETRY ← FIX GRANT!
step5() → save → export → ✅ CHECK → если плохо: RETRY
```

---

## 📝 Implementation Plan

### Phase 1: Добавить Quality Checkers (30 min)

**File:** `scripts/e2e_synthetic_workflow_v2.py`

```python
def check_anketa_quality(filepath: Path) -> tuple[bool, str]:
    content = filepath.read_text(encoding='utf-8')
    if len(content) < 5000:
        return False, "Слишком короткая анкета"
    if content.count('N/A') > 2:
        return False, "Слишком много пустых полей"
    return True, "OK"

def check_grant_quality(filepath: Path) -> tuple[bool, str]:
    content = filepath.read_text(encoding='utf-8')
    if len(content) < 15000:
        return False, f"Грант слишком короткий: {len(content)} символов"
    if 'TODO' in content:
        return False, "Есть незавершённые части"
    return True, "OK"
```

### Phase 2: Добавить Retry Logic (20 min)

```python
async def step4_writer_with_retry(self, anketa_data, research_data, max_retries=3):
    for attempt in range(max_retries):
        logger.info(f"🔄 Попытка {attempt+1}/{max_retries}")

        # Генерируем грант
        grant_result = await self.step4_writer(anketa_data, research_data)
        filepath = Path(grant_result['filename'])

        # Проверяем качество
        is_good, reason = check_grant_quality(filepath)

        if is_good:
            logger.info(f"✅ Грант качественный!")
            return grant_result
        else:
            logger.warning(f"⚠️ Попытка {attempt+1}: {reason}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5)

    raise Exception(f"❌ Не удалось создать качественный грант за {max_retries} попыток")
```

### Phase 3: Обновить run_full_cycle (10 min)

```python
async def run_full_cycle(self, index: int):
    # Step 1: Generate (с retry)
    anketa = await self.step1_generate_with_retry(index)

    # Step 2: Audit (с retry)
    audit = await self.step2_audit_with_retry(anketa['anketa_id'])

    # Step 3: Research (с retry)
    research = await self.step3_research_with_retry(anketa['anketa_id'])

    # Step 4: Writer (с retry) ← ВАЖНО!
    grant = await self.step4_writer_with_retry(anketa, research)

    # Step 5: Review (с retry)
    review = await self.step5_review_with_retry(grant['grant_text'])

    return {'cycle': index+1, 'files': {...}}
```

### Phase 4: Тестирование (10 min)

1. Запустить с 1 циклом
2. Проверить что все файлы качественные
3. Запустить с 5 циклами
4. Верифицировать 25 файлов

**Total Time:** 70 минут

---

## ✅ Success Criteria

- [ ] Все 5 checkers реализованы
- [ ] Retry logic работает
- [ ] 1 тестовый цикл успешен
- [ ] 5 циклов = 25 качественных файлов
- [ ] Все гранты > 15000 символов
- [ ] Все записи в БД корректны

---

## 🔗 Files

**New:**
- `scripts/e2e_synthetic_workflow_v2.py` (с quality control)

**Modified:**
- None (создаём новый файл)

---

**Created:** 2025-10-29 23:00 MSK
**Target Completion:** 2025-10-29 24:10 MSK
**Deadline:** 2025-10-30 (буткемп Сбера)
