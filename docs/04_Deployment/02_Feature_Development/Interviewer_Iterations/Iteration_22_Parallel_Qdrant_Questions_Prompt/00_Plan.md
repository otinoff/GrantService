# Iteration 22: Параллельная Qdrant + Промпт с 10-15 вопросами

**Date:** 2025-10-22
**Status:** Planning
**Goal:** Ускорить интервью через параллельную обработку

---

## 🎯 Цели итерации

### 1. Промпт с 10-15 вопросами
**Идея:** LLM знает все вопросы заранее в системном промпте

**Преимущества:**
- ✅ Лучшее планирование последовательности
- ✅ Понимает зависимости между вопросами
- ✅ Может пропускать очевидные вопросы

### 2. Параллельная Qdrant обработка
**Идея:** Запустить Qdrant search в отдельном потоке

**Преимущества:**
- ✅ Не блокирует интервью
- ✅ Быстрее генерация вопросов
- ✅ Лучший UX (нет зависаний)

---

## 📊 Анализ текущей архитектуры

### Текущий flow:

```
1. User ответ → answer_queue
2. Agent: get_next_reference_point()
3. Agent: generate_question()
   └─→ [BLOCKING] Qdrant search (1-2 сек)
   └─→ [BLOCKING] LLM call (2-3 сек)
4. Agent: send question
5. Repeat
```

**Проблемы:**
- ❌ Qdrant блокирует (1-2 сек)
- ❌ LLM не знает все вопросы заранее
- ❌ Нет предварительного планирования

### Целевой flow:

```
1. [INIT] LLM получает промпт с 10-15 вопросами
2. User ответ → answer_queue
3. Agent: [ASYNC] Запустить Qdrant search в фоне
4. Agent: [PARALLEL] Пока Qdrant ищет, LLM думает
5. Agent: Объединить результаты
6. Agent: send question
7. Repeat
```

**Улучшения:**
- ✅ Qdrant не блокирует
- ✅ LLM планирует лучше
- ✅ Параллельная обработка

---

## 🔍 Анализ компонентов

### 1. adaptive_question_generator.py

**Текущий код (строка 111-125):**
```python
async def generate_question(...):
    # ...
    # 4. Получить контекст из Qdrant (BLOCKING!)
    fpg_context = await self._get_fpg_context(reference_point, project_type)
    
    # 5. Определить пробелы
    gaps = self._identify_information_gaps(...)
    
    # 6. Сгенерировать вопрос с LLM (BLOCKING!)
    question = await self._llm_generate_question(...)
```

**Проблема:** Последовательное выполнение (5-6 сек total)

**Решение:** Параллельный запуск:
```python
async def generate_question(...):
    # Запустить параллельно
    qdrant_task = asyncio.create_task(self._get_fpg_context(...))
    gaps_task = asyncio.create_task(self._identify_information_gaps(...))
    
    # Дождаться результатов
    fpg_context = await qdrant_task
    gaps = await gaps_task
    
    # LLM с обоими результатами
    question = await self._llm_generate_question(...)
```

---

### 2. Системный промпт

**Текущий промпт (строка 352-366):**
```python
system_prompt = """Ты - эксперт по грантам ФПГ.
Твоя задача - задать ОДИН уточняющий вопрос...
"""
```

**Проблема:** Не знает все вопросы заранее

**Решение:** Добавить список вопросов:
```python
system_prompt = """Ты - эксперт по грантам ФПГ.

ВАЖНЫЕ ВОПРОСЫ для заявки (10-15):
1. Название проекта (3-7 слов)
2. Суть проекта (что делаете?)
3. Проблема (какую решаете?)
4. Целевая аудитория (кому помогаете?)
5. География (где реализуете?)
6. Бюджет (сколько нужно?)
7. Методология (как будете делать?)
8. Результаты (что получится?)
9. Команда (кто будет делать?)
10. Партнеры (с кем работаете?)

ТВОЯ ЗАДАЧА:
- Ты ЗНАЕШЬ все эти вопросы
- Задавай их в логичном порядке
- Пропускай очевидные (если уже ответили)
- Добавляй уточнения когда нужно

Сейчас задай ОДИН следующий вопрос...
"""
```

---

## 📝 План реализации

### Phase 1: Промпт с вопросами (1 час)

**Шаги:**
1. Составить список 10-15 ключевых вопросов
2. Обновить system_prompt в adaptive_question_generator.py
3. Протестировать с текущей архитектурой

**Файлы:**
- `agents/reference_points/adaptive_question_generator.py` (строка 352)

**Тест:**
- Запустить интервью
- Проверить, что LLM понимает контекст всех вопросов

---

### Phase 2: Параллельная Qdrant (2 часа)

**Шаги:**
1. Изменить `generate_question()` на async parallel
2. Добавить `asyncio.create_task()` для Qdrant
3. Добавить timeout для Qdrant (fallback)

**Файлы:**
- `agents/reference_points/adaptive_question_generator.py` (строка 111-125)

**Изменения:**
```python
async def generate_question(...):
    # Параллельно
    tasks = [
        asyncio.create_task(self._get_fpg_context(...)),
        asyncio.create_task(self._identify_information_gaps(...))
    ]
    
    # Timeout 2 сек для Qdrant
    try:
        fpg_context, gaps = await asyncio.wait_for(
            asyncio.gather(*tasks),
            timeout=2.0
        )
    except asyncio.TimeoutError:
        logger.warning("Qdrant timeout, using fallback")
        fpg_context = ""
        gaps = []
```

---

### Phase 3: Тестирование (1 час)

**Тесты:**
1. Unit test: параллельные задачи
2. Integration test: полное интервью
3. Performance test: измерить ускорение

**Метрики:**
- Время генерации вопроса: было 5-6 сек → цель 2-3 сек
- UX: нет зависаний

---

## 🎯 Ожидаемые результаты

### Метрики:

| Метрика | До | После | Улучшение |
|---------|-----|--------|-----------|
| Время вопроса | 5-6 сек | 2-3 сек | **-50%** |
| Qdrant блокировка | Да | Нет | ✅ |
| LLM понимание | Локальное | Глобальное | ✅ |
| UX зависания | Есть | Нет | ✅ |

---

## 📋 Чеклист

**Phase 1:**
- [ ] Составить 10-15 вопросов
- [ ] Обновить system_prompt
- [ ] Протестировать

**Phase 2:**
- [ ] Async parallel для generate_question()
- [ ] Timeout для Qdrant
- [ ] Fallback если timeout

**Phase 3:**
- [ ] Unit тесты
- [ ] Integration тесты
- [ ] Performance тесты
- [ ] Написать отчет

---

## 🚀 Next Steps

1. **Сейчас:** Завершить этот план
2. **Далее:** Реализовать Phase 1
3. **Потом:** Реализовать Phase 2
4. **Финал:** Тесты и отчет

---

**Created:** 2025-10-22
**Estimated time:** 4 hours
**Priority:** HIGH (UX improvement)
