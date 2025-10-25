# Iteration 24: Fix Duplicate Name Question - Plan

**Created:** 2025-10-22
**Status:** 🔄 IN PROGRESS
**Priority:** P1 HIGH (UX issue)

---

## Проблема

### Observed Behavior:

Бот спрашивает имя **ДВА РАЗА**:

1. **Первый раз (hardcoded):**
   ```
   [INSTANT] Sent name question
   "Скажите, как Ваше имя, как я могу к Вам обращаться?"
   ```
   Отправлено из `handle_start_interview_v2_direct()` (Iteration 20)

2. **Второй раз (LLM generated):**
   ```
   Generated question for rp_001_project_essence:
   "Здравствуйте! Как Ваше имя, как я могу к Вам обращаться?"
   ```
   Сгенерировано LLM на основе system prompt (Iteration 22)

### Root Cause:

**System prompt (Iteration 22) содержит:**
```
ВСЕ КЛЮЧЕВЫЕ ВОПРОСЫ ИНТЕРВЬЮ (12 тем):
1. Имя заявителя - Как Ваше имя, как я могу к Вам обращаться?  ← ПРОБЛЕМА!
2. Суть проекта - ...
...
```

**LLM видит:**
- Это первый turn
- В списке вопросов #1 = "Имя заявителя"
- Генерирует вопрос про имя

**Но:**
- Hardcoded вопрос про имя уже отправлен в `handle_start_interview_v2_direct()`
- Имя уже собрано в `user_data['applicant_name']`

**Результат:** Дублирование!

---

## Решение

### Approach 1: Убрать "Имя" из system prompt (ПРОСТОЕ)

**Изменить system prompt:**

**Before:**
```
ВСЕ КЛЮЧЕВЫЕ ВОПРОСЫ ИНТЕРВЬЮ (12 тем):
1. Имя заявителя - Как Ваше имя, как я могу к Вам обращаться?
2. Суть проекта - ...
```

**After:**
```
ВСЕ КЛЮЧЕВЫЕ ВОПРОСЫ ИНТЕРВЬЮ (11 тем):
1. Суть проекта - Расскажите о вашем проекте...
2. Проблема - Какую проблему решает...
...

ВАЖНО: Имя заявителя УЖЕ СОБРАНО в начале интервью.
```

**Pros:**
- ✅ Простое решение
- ✅ Нет дублирования

**Cons:**
- ⚠️ LLM не знает что имя уже есть (может запутаться)

---

### Approach 2: Передавать имя в context (ЛУЧШЕ)

**Изменить `_init_and_continue_interview()`:**

```python
# После получения имени
name = await answer_queue.get()
user_data['applicant_name'] = name

# Добавить в collected_fields чтобы LLM знал!
user_data['collected_fields'] = {'applicant_name'}
user_data['covered_topics'] = ['applicant_name', 'greeting']
```

**Изменить system prompt:**
```
ВАЖНО:
- Ты знаешь ВСЕ вопросы заранее
- НЕ дублируй вопросы которые уже были заданы
- Проверяй контекст разговора перед генерацией вопроса
```

**Pros:**
- ✅ LLM знает что имя собрано
- ✅ Может адаптировать следующие вопросы (обращаться по имени)
- ✅ Правильная архитектура

**Cons:**
- ⚠️ Чуть сложнее

---

### Approach 3: Skip первый RP если это "project_essence" (HYBRID)

**Логика:**
```python
# В generate_question()
if reference_point.id == 'rp_001_project_essence' and 'applicant_name' in context.get('collected_fields', {}):
    # Имя уже собрано, начинаем с сути проекта
    # Но учитываем что пользователь УЖЕ знает нас
    pass
```

---

## Рекомендуемое решение: Approach 2

**Почему:**
1. Правильная архитектура - context должен отражать реальность
2. LLM может адаптироваться (обращаться по имени)
3. Не нужно менять system prompt (он правильный)

---

## Implementation Plan

### Step 1: Update `_init_and_continue_interview()` (30 мин)

**Файл:** `telegram-bot/main.py`

**Изменения:**

```python
async def _init_and_continue_interview(...):
    # ... existing code ...

    # Ждать ответа на вопрос про имя
    name = await answer_queue.get()
    user_data['applicant_name'] = name

    # ✅ НОВОЕ: Отметить что имя собрано
    user_data['collected_fields'] = {'applicant_name'}
    user_data['covered_topics'] = ['applicant_name', 'greeting']

    # Дождаться завершения инициализации
    agent = await init_task

    # Обновить active_interviews с полными данными
    self.interview_handler.active_interviews[user_id] = {
        'agent': agent,
        'update': update,
        'context': context,
        'user_data': user_data,  # ✅ Содержит collected_fields
        'started_at': datetime.now(),
        'answer_queue': answer_queue
    }
```

### Step 2: Update system prompt - уточнить инструкцию (15 мин)

**Файл:** `agents/reference_points/adaptive_question_generator.py`

**Изменить:**

```python
ВАЖНО:
- Ты знаешь ВСЕ вопросы заранее, поэтому можешь делать естественные переходы
- Задавай ОДИН вопрос за раз, не дублируй уже заданные
- ПРОВЕРЯЙ контекст: если информация УЖЕ СОБРАНА (в collected_fields), НЕ спрашивай заново!
- Адаптируй формулировку под уровень пользователя (новичок/эксперт)
```

### Step 3: Test (15 мин)

1. Запустить бота
2. Начать интервью
3. Проверить что имя спрашивается только ОДИН раз
4. Проверить что второй вопрос - про суть проекта

---

## Expected Results

### Before (Iteration 23):

```
User: /start
Bot: "Скажите, как Ваше имя?"
User: "Андрей"
Bot: "Здравствуйте! Как Ваше имя?" ❌ ДУБЛЬ!
```

### After (Iteration 24):

```
User: /start
Bot: "Скажите, как Ваше имя?"
User: "Андрей"
Bot: "Андрей, расскажите о вашем проекте..." ✅ НЕТ ДУБЛЯ!
```

---

## Bonus Fix: Slow LLM Generation

### Observed:

```
✅ Question generated in 10.85s total  ← СЛИШКОМ ДОЛГО!
```

**Должно быть:** 2-3 сек
**Реально:** ~11 сек

### Investigate:

1. Проверить размер system_prompt + user_prompt
2. Возможно слишком большой контекст?
3. Проверить temperature и другие параметры LLM

### Possible fixes:

1. Уменьшить system_prompt (убрать лишнее)
2. Оптимизировать user_prompt
3. Использовать streaming (если поддерживается)

---

## Success Criteria

1. ✅ Имя спрашивается только ОДИН раз
2. ✅ Второй вопрос - про суть проекта (не про имя)
3. ✅ LLM может обращаться к пользователю по имени
4. ✅ Генерация вопроса < 5 сек (ideally < 3 сек)

---

**Next:** Implement Step 1-3
