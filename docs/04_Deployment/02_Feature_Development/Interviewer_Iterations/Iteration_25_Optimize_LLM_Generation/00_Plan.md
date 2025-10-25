# Iteration 25: Optimize LLM Generation Speed - Plan

**Created:** 2025-10-22
**Status:** 🔄 IN PROGRESS
**Priority:** P0 CRITICAL (Performance bottleneck)

---

## Проблема

### Observed Performance:

После Iteration 23-24 мы оптимизировали:
- ✅ Agent init: 6-11s → <1s (-95%)
- ✅ Parallel processing: 5-6s → 0-2s (-70%)
- ✅ No duplicate questions

**НО осталась проблема:**

```
Turn 1: ✅ Question generated in 10.85s total
  - Parallel processing: 2.02s ✅
  - LLM generation: ~8.8s ❌

Turn 3: ✅ Question generated in 7.89s total
  - Parallel processing: 0.00s ✅
  - LLM generation: ~7.9s ❌

Turn 5: ✅ Question generated in 8.68s total
  - Parallel processing: 0.00s ✅
  - LLM generation: ~8.7s ❌
```

**Bottleneck:** Чистое LLM генерация времени = **8-11 секунд вместо 2-3 секунд**

---

## Root Cause Analysis

### 1. Prompt Size

**System Prompt (~600 chars):**
```python
system_prompt = """Ты - эксперт по грантам Фонда президентских грантов (ФПГ).

Твоя задача - провести структурированное интервью и собрать информацию о проекте.

ВСЕ КЛЮЧЕВЫЕ ВОПРОСЫ ИНТЕРВЬЮ (12 тем):
1. Имя заявителя - Как Ваше имя...
2. Суть проекта - Расскажите о вашем проекте...
3. Проблема - Какую конкретную проблему...
[... 9 more questions ...]

ВАЖНО:
- Ты знаешь ВСЕ вопросы заранее...
- Задавай ОДИН вопрос за раз...
- ПРОВЕРЯЙ контекст...
- Если имя известно, обращайся по имени...
"""
```

**User Prompt (переменный, ~800-1500 chars):**
```python
user_prompt = f"""# Задача
Нужно узнать: {reference_point.name}
Описание: {reference_point.description}

# Контекст проекта
{self._format_context(conversation_context)}  # Может быть длинным!

# Уровень пользователя
{user_level.value}

# Тип проекта
{project_type.value}

# Что уже собрано
{self._format_collected_data(conversation_context)}  # ДУБЛЬ с "Контекст проекта"!

# Пробелы в информации
{gaps if gaps else "Нет явных пробелов"}

# Контекст ФПГ
{fpg_context if fpg_context else "Нет специфичных требований"}

# Примеры вопросов (можешь использовать как референс, но НЕ КОПИРУЙ)
{reference_point.question_hints}  # Может быть 3-5 примеров

Сгенерируй ОДИН вопрос...
"""
```

**Total prompt size:** ~1400-2100 chars

### 2. Redundant Sections

**Дубликаты:**
- "Контекст проекта" И "Что уже собрано" содержат одну информацию
- "Уровень пользователя" редко используется
- "Примеры вопросов" слишком длинные (3-5 примеров)

**Избыточный контекст:**
- Full conversation history в "Контекст проекта"
- All gaps analysis в "Пробелы в информации"

### 3. LLM Parameters

```python
response = await self.llm.generate_async(
    prompt=full_prompt,
    temperature=0.7,  # ❌ Слишком высокая для задачи генерации вопроса
    max_tokens=200
)
```

**Temperature 0.7** = больше креативности = больше вычислений = медленнее

---

## Решение

### Approach 1: Streamline User Prompt (TARGET)

**Принцип:** Убрать всё лишнее, оставить только необходимое для генерации вопроса.

**Before (9 sections):**
```
1. # Задача
2. # Контекст проекта
3. # Уровень пользователя
4. # Тип проекта
5. # Что уже собрано
6. # Пробелы в информации
7. # Контекст ФПГ
8. # Примеры вопросов
9. Сгенерируй...
```

**After (5 sections):**
```
1. # Задача (merged with context)
2. # Контекст разговора (merged collected + conversation)
3. # Контекст ФПГ (only if exists)
4. # Референс (1-2 примера instead of 3-5)
5. Сгенерируй...
```

**Expected reduction:** ~800 chars → ~400 chars (-50%)

---

### Approach 2: Reduce Temperature

```python
# BEFORE:
temperature=0.7  # Высокая креативность

# AFTER:
temperature=0.5  # Достаточно для естественности, быстрее
```

**Rationale:**
- Генерация вопроса НЕ требует высокой креативности
- У нас есть question_hints для вариативности
- Temperature 0.5 достаточно для естественного языка

---

### Approach 3: Simplify System Prompt

**Before (~200 chars instructions):**
```
ВАЖНО:
- Ты знаешь ВСЕ вопросы заранее, поэтому можешь делать естественные переходы
- Задавай ОДИН вопрос за раз, не дублируй уже заданные
- ПРОВЕРЯЙ контекст: если информация УЖЕ СОБРАНА, НЕ спрашивай заново!
- Если имя известно, обращайся по имени для естественности
- Адаптируй формулировку под уровень пользователя (новичок/эксперт)
```

**After (~100 chars):**
```
ВАЖНО:
- Задавай ОДИН вопрос, не дублируй уже заданные
- Проверяй собранный контекст перед вопросом
- Обращайся по имени если известно
```

**Rationale:**
- Инструкции дублируются в user_prompt
- Можно сократить без потери смысла

---

### Approach 4: Limit Question Hints

```python
# BEFORE (все примеры):
question_hints = "\n".join(reference_point.question_hints)  # 3-5 примеров

# AFTER (только 2 примера):
question_hints = "\n".join(reference_point.question_hints[:2])  # 2 примера
```

---

## Implementation Plan

### Phase 1: Streamline User Prompt (30 min)

**File:** `agents/reference_points/adaptive_question_generator.py`
**Lines:** 609-660

**Changes:**

1. **Merge "Контекст проекта" + "Что уже собрано":**
```python
# BEFORE:
# Контекст проекта
{self._format_context(conversation_context)}
...
# Что уже собрано
{self._format_collected_data(conversation_context)}

# AFTER:
# Контекст разговора
Уже обсуждено: {', '.join(conversation_context.get('covered_topics', []))}
Собрано: {self._format_collected_data(conversation_context)}
```

2. **Remove "Уровень пользователя"** (редко используется)

3. **Limit "Примеры вопросов" to 2:**
```python
hints = reference_point.question_hints[:2]
```

4. **Make "Контекст ФПГ" optional:**
```python
# Only include if exists and non-empty
if fpg_context and len(fpg_context) > 20:
    prompt += f"\n# Контекст ФПГ\n{fpg_context}\n"
```

---

### Phase 2: Reduce Temperature (5 min)

**File:** `agents/reference_points/adaptive_question_generator.py`
**Lines:** 645-650

```python
response = await self.llm.generate_async(
    prompt=full_prompt,
    temperature=0.5,  # CHANGED from 0.7
    max_tokens=200
)
```

---

### Phase 3: Simplify System Prompt (10 min)

**File:** `agents/reference_points/adaptive_question_generator.py`
**Lines:** 593-600

**Shorten instructions from 5 bullets to 3 bullets.**

---

### Phase 4: Test Performance (15 min)

1. Run bot with changes
2. Measure LLM generation time
3. Verify question quality remains high
4. Check for regressions

**Target:**
- LLM generation: 8-11s → 2-4s (-60% to -80%)
- Total question time: 8-11s → 2-4s

---

## Expected Results

### Before (Iteration 24):
```
Turn 1: Question generated in 10.85s
  - Parallel: 2.02s
  - LLM: ~8.8s ❌

Turn 3: Question generated in 7.89s
  - Parallel: 0.00s
  - LLM: ~7.9s ❌
```

### After (Iteration 25):
```
Turn 1: Question generated in 4-5s
  - Parallel: 2.02s
  - LLM: ~2-3s ✅

Turn 3: Question generated in 2-3s
  - Parallel: 0.00s
  - LLM: ~2-3s ✅
```

**Improvement:** -60% to -75% LLM time

---

## Success Criteria

1. ✅ LLM generation < 4s (target: 2-3s)
2. ✅ Total question time < 5s
3. ✅ Question quality remains natural and relevant
4. ✅ No regression in question accuracy
5. ✅ Tests pass (no functional changes)

---

## Risks

1. **Quality degradation** - Упрощение промпта может снизить качество вопросов
   - Mitigation: Тестировать на реальных диалогах, откатить если качество упало

2. **Temperature too low** - Temperature 0.5 может сделать вопросы слишком шаблонными
   - Mitigation: Можно попробовать 0.6 если 0.5 слишком низкая

3. **Missing context** - Убрав секции можем потерять важный контекст
   - Mitigation: Оставить самые важные секции, убрать только явно избыточные

---

**Next:** Implement Phase 1-3 → Test → Report
