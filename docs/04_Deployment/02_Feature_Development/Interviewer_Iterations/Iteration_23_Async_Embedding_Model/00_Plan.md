# Iteration 23: Async Embedding Model Loading - Plan

**Created:** 2025-10-22
**Status:** 🔄 IN PROGRESS
**Priority:** P0 CRITICAL (production blocker)

---

## Проблема

### Observed Behavior:

Бот **завис** на загрузке SentenceTransformer модели:

```
2025-10-22 22:32:33,637 - sentence_transformers.SentenceTransformer - INFO - Load pretrained SentenceTransformer: paraphrase-multilingual-MiniLM-L12-v2
Press any key to continue . . .  ← ЗАСТРЯЛ!
```

### Root Cause:

**Файл:** `C:\SnowWhiteAI\GrantService\agents\reference_points\adaptive_question_generator.py`
**Строки:** 87-94

```python
self.embedding_model = None
if SENTENCE_TRANSFORMERS_AVAILABLE and qdrant_client is not None:
    try:
        # БЛОКИРУЕТ! Синхронная загрузка модели
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        logger.info("Embedding model initialized for Qdrant search")
    except Exception as e:
        logger.warning(f"Failed to initialize embedding model: {e}")
```

**Проблема:**
1. `SentenceTransformer()` - **синхронная операция**
2. Загружает модель ~100MB с диска или скачивает из интернета
3. Может занимать **5-10 секунд** на первом запуске
4. **Блокирует** весь `_init_agent_for_user()` метод
5. Пользователь ждет пока модель загрузится

### Impact:

- ❌ Параллельная инициализация из Iteration 22 **не работает** полностью
- ❌ Первый вопрос отправляется, но агент не готов принять ответ
- ❌ Пользователь получает timeout или долгое ожидание

---

## Решение

### Approach: Lazy Loading + Async Initialization

**Идея:**
1. **НЕ загружать** модель в `__init__()` агента
2. Загружать модель **только когда нужна** (lazy loading)
3. Загружать **асинхронно** в background thread
4. Использовать **fallback** если модель не готова

### Architecture (Before):

```python
# __init__():
self.embedding_model = SentenceTransformer(...)  # БЛОКИРУЕТ 5-10 сек!

# generate_question():
query_vector = self.embedding_model.encode(query)  # Использует модель
```

**Время:** ~10-15 сек до первого вопроса (init + первый вопрос)

### Architecture (After):

```python
# __init__():
self.embedding_model = None  # Не загружаем!
self._model_loading_task = None

# _ensure_embedding_model_loaded():
async def _ensure_embedding_model_loaded(self):
    if self.embedding_model is not None:
        return True  # Уже загружена

    if self._model_loading_task is None:
        # Запустить загрузку в background
        self._model_loading_task = asyncio.create_task(
            self._load_embedding_model_async()
        )

    try:
        # Дождаться загрузки (с timeout 3 сек)
        await asyncio.wait_for(self._model_loading_task, timeout=3.0)
        return True
    except asyncio.TimeoutError:
        logger.warning("Embedding model loading timeout, using fallback")
        return False

# generate_question():
model_ready = await self._ensure_embedding_model_loaded()
if model_ready:
    query_vector = self.embedding_model.encode(query)
else:
    # Fallback: пропустить Qdrant search
    fpg_context = ""
```

**Время:** ~2-3 сек до первого вопроса (модель грузится в фоне)

---

## Implementation Plan

### Phase 1: Lazy Loading (1 час)

**Изменения:**

1. **`__init__()` в adaptive_question_generator.py:**
   - Убрать загрузку модели
   - Добавить `self._model_loading_task = None`

2. **Новый метод `_ensure_embedding_model_loaded()`:**
   - Проверить если модель уже загружена
   - Если нет, запустить async загрузку
   - Дождаться с timeout 3 сек
   - Return True/False

3. **Новый метод `_load_embedding_model_async()`:**
   - Обертка для `SentenceTransformer()` в executor
   - Загружает модель в отдельном thread
   - Обрабатывает ошибки

4. **Обновить `generate_question()`:**
   - Вызывать `_ensure_embedding_model_loaded()` перед Qdrant search
   - Если модель не готова, пропускать Qdrant (fallback)

### Phase 2: Background Preloading (30 мин)

**Опциональная оптимизация:**

1. **Метод `start_loading_in_background()`:**
   - Вызывать сразу после создания агента
   - Запускает загрузку модели в фоне
   - Не блокирует

2. **В `_init_agent_for_user()`:**
   ```python
   agent = InteractiveInterviewerAgentV2(...)
   agent.question_generator.start_loading_in_background()  # Фоновая загрузка
   return agent
   ```

---

## Expected Results

### Performance:

| Scenario | Before (Iteration 22) | After (Iteration 23) | Improvement |
|----------|----------------------|---------------------|-------------|
| Init agent | 10-15 сек (блок) | 0.5 сек (async) | **-95%** |
| First question | +3-5 сек | +3-5 сек | Same |
| Total to first question | 13-20 сек | 3.5-5.5 сек | **-70%** |

### User Experience:

**Before:**
1. User clicks "Начать интервью"
2. Bot sends name question (instant ✅)
3. User types name
4. **WAIT 10-15 сек** while agent initializes ❌
5. Bot asks second question

**After:**
1. User clicks "Начать интервью"
2. Bot sends name question (instant ✅)
3. User types name (while model loads in background)
4. **WAIT 0-3 сек** if model not ready yet ✅
5. Bot asks second question (maybe without Qdrant context on first question, but fast!)

---

## Files to Modify

1. **C:\SnowWhiteAI\GrantService\agents\reference_points\adaptive_question_generator.py**
   - `__init__()` - remove model loading
   - Add `_ensure_embedding_model_loaded()`
   - Add `_load_embedding_model_async()`
   - Add `start_loading_in_background()`
   - Update `generate_question()`

2. **C:\SnowWhiteAI\GrantService\telegram-bot\main.py**
   - Update `_init_agent_for_user()` to start background loading

---

## Testing Plan

### Test 1: Model Loads Asynchronously
- Проверить что модель НЕ загружается в `__init__()`
- Проверить что загрузка начинается при первом `generate_question()`
- Время init < 1 сек

### Test 2: Timeout Fallback Works
- Имитировать медленную загрузку модели (>3 сек)
- Проверить что используется fallback (без Qdrant)
- Вопрос все равно генерируется

### Test 3: Background Preloading
- Вызвать `start_loading_in_background()` сразу после init
- Проверить что к моменту первого вопроса модель готова
- Qdrant search работает

### Test 4: Production Scenario
- Реальный запуск бота
- User starts interview
- Измерить время от "Начать интервью" до второго вопроса
- Target: < 6 сек

---

## Risk Analysis

### Risks:

1. **Model never loads** - если всегда timeout
   - Mitigation: fallback работает, но без Qdrant контекста
   - Impact: Medium (качество вопросов ниже)

2. **Thread safety issues** - если модель используется из разных threads
   - Mitigation: Lock при загрузке
   - Impact: Low (SentenceTransformer thread-safe)

3. **Memory leak** - если задача загрузки не завершается
   - Mitigation: Timeout + proper cleanup
   - Impact: Low

### Mitigation:

- ✅ Graceful degradation (fallback без модели)
- ✅ Timeout защита (3 сек)
- ✅ Comprehensive logging
- ✅ Tests для всех scenarios

---

## Success Criteria

1. ✅ Agent initialization < 1 сек
2. ✅ First question generation < 6 сек total (from button click)
3. ✅ Model loads in background successfully
4. ✅ Fallback works if model not ready
5. ✅ All tests PASS

---

**Next:** Implement Phase 1 (Lazy Loading)
