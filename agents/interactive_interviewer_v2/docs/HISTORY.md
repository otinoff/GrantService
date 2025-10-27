# История Развития InteractiveInterviewerAgent

**Проект:** GrantService - AI Grant Application Generator
**Агент:** InteractiveInterviewerAgent (V1 → V2)
**Период:** 2025-09 — 2025-10

---

## Оглавление

1. [Версия 1.0 - Как Было](#версия-10---как-было)
2. [Проблемы V1](#проблемы-v1)
3. [Решение: Reference Points Framework](#решение-reference-points-framework)
4. [Версия 2.0 - Что Изменилось](#версия-20---что-изменилось)
5. [Хронология Итераций](#хронология-итераций)
6. [Ключевые Рефакторинги](#ключевые-рефакторинги)
7. [Lessons Learned](#lessons-learned)

---

## Версия 1.0 - Как Было

### Архитектура V1 (Сентябрь 2025)

**Файл:** `agents/interactive_interviewer_agent.py` (старое расположение)

**Подход:** Жёсткий список из 10 фиксированных вопросов

```python
# V1 CODE (упрощённо):
class InteractiveInterviewerAgent(BaseAgent):
    def __init__(self):
        self.questions = [
            "Как называется ваш проект?",
            "Опишите цель вашего проекта.",
            "Какую проблему решает ваш проект?",
            "Кто ваша целевая аудитория?",
            "Опишите методологию реализации.",
            "Какой бюджет требуется?",
            "Кто входит в команду проекта?",
            "Какие ожидаемые результаты?",
            "Как будет обеспечена устойчивость?",
            "Есть ли риски у проекта?"
        ]

    async def conduct_interview(self, user_data, callback):
        answers = {}

        # Задать все вопросы по порядку
        for i, question in enumerate(self.questions):
            answer = await callback(question)
            answers[f"question_{i+1}"] = answer

        # Сохранить всё в конце
        anketa = self._format_anketa(answers)
        return anketa
```

### Как Это Работало?

**Workflow:**

```
1. Пользователь: "Начать интервью"
   ↓
2. Бот: "Как называется ваш проект?"
3. Пользователь: "Проект X"
   ↓
4. Бот: "Опишите цель вашего проекта."
5. Пользователь: "Цель Y"
   ↓
6. Бот: "Какую проблему решает ваш проект?"
7. Пользователь: "Проблема Z"
   ↓
... (всего 10 вопросов)
   ↓
10. Бот: "Анкета готова!" (отправляет файл)
```

**Характеристики V1:**

- ✅ Просто и понятно
- ✅ Предсказуемо (всегда 10 вопросов)
- ✅ Быстро (1-2 минуты на интервью)
- ❌ Негибко (не учитывает контекст)
- ❌ Не адаптируется к ответам
- ❌ Нет уточняющих вопросов
- ❌ Шаблонные вопросы (не естественные)
- ❌ Сохранение только в конце (риск потери данных)

---

## Проблемы V1

### Проблема 1: Негибкие Вопросы

**Симптом:**
```
[БОТ] Опишите методологию реализации.
[USER] Организуем мастер-классы
[БОТ] Какой бюджет требуется?  ← Следующий вопрос, игнорируя неполный ответ
```

Агент **НЕ** мог:
- Задать уточняющий вопрос ("А сколько мастер-классов?")
- Адаптировать следующий вопрос к контексту
- Пропустить вопрос если ответ уже дан

**Последствия:**
- Неполные анкеты (audit score 30-40/100)
- Пользователи давали краткие ответы
- Приходилось вручную дополнять анкеты

---

### Проблема 2: Отсутствие Контекста

**Симптом:**
```
[USER] (отвечает на вопрос 3) "Проект для школьников, хотим развивать спорт, бюджет 500 тысяч"
[БОТ] (вопрос 4) Кто ваша целевая аудитория?  ← Уже сказал "школьники"!
[БОТ] (вопрос 6) Какой бюджет требуется?      ← Уже сказал "500 тысяч"!
```

Агент **НЕ** анализировал предыдущие ответы.

**Последствия:**
- Пользователи раздражались повторами
- Снижение engagement'а
- Неестественный диалог

---

### Проблема 3: Нет Приоритизации

Все 10 вопросов **равнозначны**.

Если пользователь ушёл после 5 вопросов → анкета неполная.

Нет понятия "критичные вопросы" (MUST HAVE) vs "дополнительные" (NICE TO HAVE).

**Последствия:**
- Потеря данных при незавершённых интервью
- Не понятно что важнее собрать

---

### Проблема 4: Сохранение Только в Конце

**Код V1:**
```python
async def conduct_interview(self, user_data, callback):
    answers = {}  # In-memory!

    for question in self.questions:
        answer = await callback(question)
        answers[question] = answer  # Только в памяти!

    # Сохранить ВСЁ в конце
    db.save_anketa(answers)  # ← Если бот упал - всё потеряно!
```

**Последствия:**
- Если бот упал в процессе → все ответы потеряны
- Пользователь начинает заново
- Production инциденты (Iteration 53)

---

### Проблема 5: Шаблонные Вопросы

Вопросы были **статичными строками**.

```python
self.questions = [
    "Опишите методологию реализации.",  # Звучит формально
    "Какие ожидаемые результаты?",      # Грамматическая ошибка
]
```

**Последствия:**
- Неестественный язык
- Не учитывается специфика проекта
- Одинаковые вопросы для всех

---

## Решение: Reference Points Framework

### Концепция

**Идея:** Вместо жёстких вопросов использовать **информационные точки** (Reference Points).

**Reference Point** - это не вопрос, а **цель**:
- Что нужно узнать?
- Насколько это важно?
- Когда можно считать информацию собранной?

### Преимущества Подхода

**1. Адаптивность:**
```python
# Вместо:
question = "Опишите методологию реализации."

# Стало:
rp = ReferencePoint(
    id="methodology",
    name="Методология реализации",
    description="Как будут реализовывать проект (мероприятия, подходы)",
    priority=P1
)

# LLM генерирует вопрос на основе контекста:
question = await generate_question(rp, context={
    'project_name': "Стрельба из лука",
    'target_audience': "школьники",
    'last_answer': "..."
})
# Результат: "Расскажите, какие мероприятия планируете для школьников?"
```

**2. Приоритизация:**
```python
P0 = MUST HAVE   # Критично (название, цель, проблема)
P1 = SHOULD HAVE # Важно (методология, команда)
P2 = NICE TO HAVE # Полезно (партнёры, риски)
P3 = OPTIONAL    # Бонус (дополнительные детали)
```

**3. Гибкая Последовательность:**
```python
# Не:
for question in questions:  # Жёсткий порядок
    ask(question)

# А:
while not all_critical_rps_completed():
    rp = get_next_rp(priority="highest")  # Динамический выбор
    question = generate_question(rp)
    answer = ask(question)

    if answer_is_incomplete(answer):
        # Можем задать follow-up!
        follow_up = generate_follow_up(rp, answer)
        additional_answer = ask(follow_up)
```

**4. Сохранение После Каждого Ответа:**
```python
for rp in reference_points:
    question = generate_question(rp)
    answer = ask(question)

    # Сохранить СРАЗУ!
    db.save_answer(session_id, rp.id, answer)  # ← Database-First!

    rp.add_data('text', answer)
    mark_completed(rp)
```

---

## Версия 2.0 - Что Изменилось

### Таблица Сравнения

| Аспект | V1 (Старая) | V2 (Текущая) |
|--------|------------|--------------|
| **Файл** | `agents/interactive_interviewer_agent.py` | `agents/interactive_interviewer_v2/agent.py` |
| **Структура** | Одиночный файл | Subproject (5 модулей) |
| **Вопросы** | 10 фиксированных шаблонов | Генерируются LLM на лету |
| **Последовательность** | Жёсткая (1→2→...→10) | Гибкая (state machine) |
| **Контекст** | Нет | Да (история + Qdrant) |
| **Адаптация** | Нет | Да (зависит от ответов) |
| **Follow-up** | Нет | Да (до 5 уточнений) |
| **Приоритизация** | Нет (все равны) | Да (P0→P1→P2→P3) |
| **Сохранение** | В конце (риск потери) | После каждого ответа |
| **Completion Check** | По количеству вопросов | По полноте информации |
| **LLM Provider** | Claude только | GigaChat + Claude fallback |
| **База знаний** | Нет | Qdrant (ФПГ docs) |
| **Среднее время** | 60-90 сек | 45-60 сек |
| **Качество анкет** | 30-40/100 | 40-60/100 |

---

### Новые Компоненты V2

**1. Reference Point Manager**
- Управляет коллекцией RP
- Определяет следующий RP для обработки
- Отслеживает прогресс (сколько P0 завершено)

**2. Conversation Flow Manager**
- State machine (INIT → EXPLORING → DEEPENING → VALIDATING → FINALIZING)
- Определяет переходы между состояниями
- Управляет бюджетом follow-up вопросов

**3. Adaptive Question Generator**
- Генерирует вопросы через LLM
- Учитывает контекст диалога
- Интегрируется с Qdrant для ФПГ контекста

**4. Qdrant Integration**
- Векторная база знаний (руководство ФПГ)
- Обогащает вопросы контекстом
- Опциональна (graceful degradation)

**5. Database-First Approach**
- Сохранение после каждого ответа
- Защита от потери данных
- Recovery при сбоях

---

## Хронология Итераций

### Iteration 26 (Октябрь 2025) - Birth of V2

**Проблема:** V1 не справляется с требованиями ФПГ

**Решение:** Создать V2 с Reference Points Framework

**Изменения:**
- Создан `agents/interactive_interviewer_agent_v2.py`
- Разработан Reference Points Framework
- Добавлена интеграция с Qdrant
- Реализована адаптивная генерация вопросов

**Результат:** V2 работает параллельно с V1

---

### Iteration 35 (Октябрь 2025) - Subproject Architecture

**Проблема:** Код V2 растёт, нужна лучшая организация

**Решение:** "Проект в проекте" - вынести V2 в отдельную папку

**Изменения:**
- Создана структура `agents/interactive_interviewer_v2/`
- Агент перемещён: `agent.py` (внутри subproject)
- Reference Points вынесены в `reference_points/` модуль
- Добавлена собственная test suite

**Результат:** V2 стал самостоятельным subproject'ом

---

### Iteration 53 (Октябрь 2025) - Production Crisis & Testing

**Проблема:** Production bot не работает несколько дней! Ошибка импорта.

**Root Cause:**
```python
# telegram-bot/main.py:1965 (СТАРЫЙ ИМПОРТ)
from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2
# ❌ WRONG! Файл переехал в agents/interactive_interviewer_v2/agent.py
```

**Почему тесты не поймали?**
- E2E test импортировал агента НАПРЯМУЮ с новым путём
- Не тестировал production entry point (Telegram handler)
- Использовал static answers вместо LLM
- Сохранял данные в память, не в БД

**Решения:**
1. **Исправлен импорт:**
```python
# telegram-bot/main.py:1965 (ИСПРАВЛЕНО)
from agents.interactive_interviewer_v2.agent import InteractiveInterviewerAgentV2
```

2. **Добавлены Smoke Tests:**
```python
# tests/smoke/test_production_imports.py
def test_agent_modules_import():
    """Проверяет что импорты работают - поймал бы баг!"""
    from agents.interactive_interviewer_v2.agent import InteractiveInterviewerAgentV2
```

3. **Документирована IDEAL методология тестирования:**
- LLM-driven tests (не static answers)
- Database-first (не in-memory)
- Production parity (через handlers, не напрямую)

**Результат:**
- Баг исправлен
- Smoke tests защитят от повторения
- Методология тестирования задокументирована

---

### Phase 3 (Iteration 53) - Bug Fixes

**Проблемы в коде:**
1. Broad exception handling
2. Fake audit score on error
3. Unimplemented DB save
4. Missing error chaining

**Решения:**
- Убран автоматический запуск аудита (был долгий, замедлял интервью)
- Исправлена обработка ошибок
- Добавлены specific exceptions
- Добавлен error chaining (`raise ... from e`)

---

## Ключевые Рефакторинги

### 1. От Шаблонов к LLM Генерации

**Было:**
```python
questions = [
    "Как называется ваш проект?",
    "Опишите цель вашего проекта."
]
```

**Стало:**
```python
async def generate_question(rp, context):
    prompt = f"""
    Задай вопрос чтобы узнать "{rp.name}".
    Контекст: {context}
    Вопрос должен быть естественным и учитывать предыдущие ответы.
    """
    question = await llm.generate(prompt)
    return question
```

---

### 2. От Линейного Flow к State Machine

**Было:**
```python
for i in range(10):
    ask_question(questions[i])
```

**Стало:**
```python
state = ConversationState.INIT

while state != ConversationState.FINALIZING:
    if state == EXPLORING:
        rp = get_next_rp(priority="P0")
        ask_question(rp)
        if rp_incomplete:
            state = DEEPENING

    elif state == DEEPENING:
        ask_follow_up(rp)
        if all_p0_complete:
            state = FINALIZING
```

---

### 3. От In-Memory к Database-First

**Было:**
```python
answers = {}  # Всё в памяти
for q in questions:
    answers[q] = ask(q)

# Сохранить в конце
db.save(answers)  # Риск потери!
```

**Стало:**
```python
for rp in reference_points:
    answer = ask_question(rp)

    # Сохранить СРАЗУ
    db.save_answer(session_id, rp.id, answer)  # Database-First!

    rp.add_data('text', answer)
```

---

### 4. От Одиночного Файла к Subproject

**Было:**
```
agents/
  ├── interactive_interviewer_agent.py  # 500+ строк
  └── auditor_agent.py
```

**Стало:**
```
agents/
  ├── interactive_interviewer_v2/  # Subproject
  │   ├── agent.py
  │   ├── reference_points/
  │   │   ├── reference_point_manager.py
  │   │   ├── conversation_flow_manager.py
  │   │   └── adaptive_question_generator.py
  │   ├── tests/
  │   │   ├── unit/
  │   │   ├── integration/
  │   │   └── e2e/
  │   └── docs/
  │       ├── BUSINESS_LOGIC.md
  │       ├── HISTORY.md
  │       └── ARCHITECTURE.md
  └── auditor_agent.py
```

---

## Lessons Learned

### 1. Database-First Критично для Production

**Урок:** Сохраняйте данные **после каждого действия**, не в конце.

**Почему:** Защита от сбоев. В production всё может упасть.

**Как:** `db.save()` после каждого ответа пользователя.

---

### 2. Тесты Должны Проверять Production Workflow

**Урок:** E2E тесты должны использовать **реальные** entry points, не моки.

**Почему:** E2E test passed, но production failed (Iteration 53).

**Как:**
- Тестировать через Telegram handlers
- Использовать реальный LLM (или очень похожий mock)
- Читать из БД, не из памяти

---

### 3. Smoke Tests - Первая Линия Защиты

**Урок:** Добавьте быстрые (<10 сек) smoke tests для критичных модулей.

**Почему:** Ловят простые ошибки (импорты, config) до деплоя.

**Как:** `tests/smoke/test_production_imports.py` - проверяет что всё импортируется.

---

### 4. Subproject Architecture Масштабируется

**Урок:** Сложные агенты заслуживают отдельной папки ("проект в проекте").

**Почему:**
- Изоляция кода
- Независимые тесты
- Легче навигация
- Можно версионировать отдельно

**Как:** `agents/interactive_interviewer_v2/` с собственной структурой.

---

### 5. Документация = Часть Кода

**Урок:** Документируйте не только "что" но и "почему".

**Почему:** Через месяц забудете почему сделали так, а не иначе.

**Как:**
- `docs/BUSINESS_LOGIC.md` - как работает сейчас
- `docs/HISTORY.md` - почему изменили
- `docs/ARCHITECTURE.md` - как устроено технически

---

## Что Дальше?

### V3 (Возможные Улучшения)

**1. Multi-Agent Conversation:**
- Несколько специализированных агентов (бюджет, методология, команда)
- Каждый эксперт в своей области

**2. Динамические Reference Points:**
- Создавать новые RP на основе ответов
- Например, пользователь упомянул "партнёров" → создать RP "partnership_details"

**3. Персонализация:**
- Учитывать стиль ответов пользователя (короткие/длинные)
- Адаптировать тон вопросов

**4. Voice Interface:**
- Голосовые вопросы и ответы
- Speech-to-text интеграция

---

**Дата:** 2025-10-27
**Автор:** Grant Service Team
**Статус:** Archived Documentation ✅
