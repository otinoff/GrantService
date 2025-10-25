# Новая архитектура: Reference Points вместо жестких вопросов

## Findings из research (WebSearch)

### 🔍 Best Practices из мира:

**1. Semi-structured interviews (NUS 2024):**
> "allows creativity and flexibility to ensure that each participant's story is fully uncovered"

**2. Discovery interviews:**
> "ongoing and iterative process, extract context, reference real-life examples"

**3. Contextual inquiry (NN/Group):**
> "two-way partnership where conversation flows naturally, adapt on the fly"

**4. Grant Assistant (AI tool):**
> "questionnaire containing questions similar to what a project consultant might ask"

**5. UX Research frameworks:**
> "flexible enough to tailor to specific objectives, real-time adaptation based on participant responses"

---

## ❌ Проблема жестких вопросов

### Почему 15 фиксированных вопросов - это плохо:

1. **Люди разные:**
   - Социальный проект ≠ Культурный проект ≠ Научный
   - Опытный грантополучатель ≠ Новичок
   - Экстраверт ≠ Интроверт

2. **Контекст теряется:**
   - Если человек ответил на 3 вопроса в рамках одного, зачем спрашивать снова?
   - "Вопрос 7" не видит, что было в "Вопросе 3"

3. **Неестественно:**
   - Живой консультант не задает 15 вопросов подряд
   - Это допрос, а не беседа

4. **Неэффективно:**
   - Вопросы могут быть нерелевантными
   - Пропущены важные детали (вне списка)

---

## ✅ Решение: Reference Points Framework

### Концепция

**Вместо жестких вопросов → Опорные точки (milestones)**

```
Не: "Вопрос 7: Опишите методологию"
А:  MILESTONE: "Понять, КАК будет реализован проект"
    → Система сама формулирует вопрос на основе контекста
```

### Архитектура

```
┌─────────────────────────────────────────────────────────┐
│         REFERENCE POINTS (Опорные точки)                │
│                                                         │
│  1. Понять суть проекта                                │
│  2. Определить проблему                                │
│  3. Найти целевую аудиторию                            │
│  4. Узнать методологию реализации                      │
│  5. Оценить бюджет                                     │
│  6. Понять команду                                     │
│  7. Выявить риски                                      │
│  8. Оценить устойчивость                               │
│  ...                                                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│         CONTEXT ENGINE (Движок контекста)               │
│                                                         │
│  - Что уже собрано?                                    │
│  - Что упомянуто косвенно?                             │
│  - Какой тип проекта?                                  │
│  - Уровень пользователя?                               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│         ADAPTIVE QUESTION GENERATOR                     │
│         (Генератор адаптивных вопросов)                │
│                                                         │
│  Input: Reference Point + Context                       │
│  Output: Contextual Question                            │
│                                                         │
│  Example:                                              │
│  RP: "Понять методологию"                              │
│  Context: Социальный проект, новичок                   │
│  → "Расскажите, как вы планируете помогать людям?      │
│     Какие конкретные шаги вы будете делать?"          │
│                                                         │
│  RP: "Понять методологию"                              │
│  Context: Научный проект, эксперт                      │
│  → "Какую методологию исследования вы планируете       │
│     использовать? Есть ли пилотные данные?"           │
└─────────────────────────────────────────────────────────┘
```

---

## Reference Points Structure

### Определение Reference Point

```python
class ReferencePoint:
    """
    Опорная точка - цель, которую нужно достичь в интервью
    """
    id: str              # "understand_methodology"
    name: str            # "Понять методологию реализации"
    priority: int        # 0 (критично) - 3 (желательно)
    required: bool       # Обязательно или нет?

    # Критерии завершенности
    completion_criteria: dict = {
        'min_length': 100,          # Минимум символов
        'has_specifics': True,      # Есть конкретика?
        'no_contradictions': True   # Нет противоречий?
    }

    # Связанные поля анкеты
    related_fields: list = ['methodology', 'tasks', 'timeline']

    # Подсказки для генерации вопросов
    question_templates: list = [
        "Расскажите, как вы планируете...",
        "Какие конкретные шаги...",
        "Опишите процесс реализации..."
    ]
```

### Примеры Reference Points

```python
REFERENCE_POINTS = [
    # Блок 1: Понимание проекта (P0 - критично)
    ReferencePoint(
        id="understand_essence",
        name="Понять суть проекта",
        priority=0,
        required=True,
        completion_criteria={
            'fields_filled': ['project_name', 'project_goal'],
            'min_clarity_score': 0.7
        }
    ),

    ReferencePoint(
        id="identify_problem",
        name="Определить проблему",
        priority=0,
        required=True,
        completion_criteria={
            'fields_filled': ['problem_description'],
            'has_specifics': True,  # Не "плохая ситуация", а "30% детей..."
        }
    ),

    ReferencePoint(
        id="find_target_audience",
        name="Найти целевую аудиторию",
        priority=0,
        required=True,
        completion_criteria={
            'fields_filled': ['target_audience'],
            'is_specific': True  # Не "люди", а "многодетные семьи..."
        }
    ),

    # Блок 2: Реализация (P1 - важно)
    ReferencePoint(
        id="understand_methodology",
        name="Узнать методологию реализации",
        priority=1,
        required=True,
        completion_criteria={
            'fields_filled': ['methodology', 'tasks'],
            'has_timeline': True,
            'has_concrete_steps': True
        }
    ),

    ReferencePoint(
        id="assess_budget",
        name="Оценить бюджет",
        priority=1,
        required=True,
        completion_criteria={
            'fields_filled': ['budget_total', 'budget_breakdown'],
            'is_realistic': True,  # Проверка через Qdrant
            'has_justification': True
        }
    ),

    # Блок 3: Команда и устойчивость (P2 - желательно)
    ReferencePoint(
        id="understand_team",
        name="Понять команду",
        priority=2,
        required=False,  # Может быть solo project
        completion_criteria={
            'fields_filled': ['team_description'],
            'has_roles': True
        }
    ),

    ReferencePoint(
        id="identify_risks",
        name="Выявить риски",
        priority=2,
        required=True,
        completion_criteria={
            'fields_filled': ['risks'],
            'has_mitigation': True
        }
    ),

    ReferencePoint(
        id="assess_sustainability",
        name="Оценить устойчивость",
        priority=2,
        required=True,
        completion_criteria={
            'fields_filled': ['sustainability'],
            'has_plan': True
        }
    ),
]
```

---

## Adaptive Question Generation

### Алгоритм

```python
class AdaptiveQuestionGenerator:
    """
    Генерирует контекстные вопросы на основе:
    - Reference Point (что нужно узнать)
    - Current Context (что уже знаем)
    - User Profile (кто отвечает)
    - Qdrant Knowledge (база ФПГ)
    """

    async def generate_question(
        self,
        reference_point: ReferencePoint,
        context: dict
    ) -> str:
        """
        Сгенерировать адаптивный вопрос
        """
        # 1. Проверить, может уже ответили?
        if self._already_covered(reference_point, context):
            return None  # Skip this reference point

        # 2. Определить тип проекта
        project_type = self._classify_project(context)

        # 3. Оценить уровень пользователя
        user_level = self._assess_user_level(context)

        # 4. Найти релевантный контекст из Qdrant
        fpg_context = await self._get_fpg_context(reference_point)

        # 5. Сгенерировать вопрос через LLM
        question = await self._generate_with_llm(
            reference_point=reference_point,
            project_type=project_type,
            user_level=user_level,
            fpg_context=fpg_context,
            conversation_history=context['history']
        )

        return question


    def _already_covered(self, rp: ReferencePoint, context: dict) -> bool:
        """
        Проверить, уже ли ответили на этот reference point
        """
        # Проверить связанные поля
        for field in rp.related_fields:
            if field in context['collected_fields']:
                # Проверить качество
                if self._meets_criteria(
                    context['collected_fields'][field],
                    rp.completion_criteria
                ):
                    return True  # Уже собрано достаточно

        return False


    async def _generate_with_llm(
        self,
        reference_point,
        project_type,
        user_level,
        fpg_context,
        conversation_history
    ) -> str:
        """
        Генерация через LLM с контекстом
        """
        prompt = f"""
Ты - эксперт по грантовым заявкам ФПГ, проводящий интервью.

ЦЕЛЬ: {reference_point.name}

КОНТЕКСТ ПРОЕКТА:
- Тип: {project_type}
- Уровень заявителя: {user_level}

ЧТО УЖЕ ОБСУДИЛИ:
{conversation_history[-3:]}  # Последние 3 обмена

ТРЕБОВАНИЯ ФПГ (из базы знаний):
{fpg_context}

ЗАДАЧА: Сформулируй ЕСТЕСТВЕННЫЙ вопрос, который:
1. Поможет достичь цели: "{reference_point.name}"
2. Учитывает предыдущий контекст беседы
3. Адаптирован под уровень человека
4. Не дублирует то, что уже обсуждалось

ВАЖНО:
- Говори как живой человек, а не как форма
- Используй "вы" (уважительно)
- Если нужно, дай подсказку на основе требований ФПГ

ВОПРОС:
"""

        question = await self.llm.generate(prompt)

        return question
```

---

## Conversation Flow

### Не линейный, а адаптивный

```
НЕ ТАК (жесткий порядок):
Q1 → Q2 → Q3 → Q4 → Q5 → ...

А ТАК (адаптивный):

                 Start
                   ↓
         Check Reference Points
                   ↓
    [RP1: Понять суть] ← Priority 0, не заполнен
                   ↓
         Generate Question
                   ↓
    "Расскажите о вашем проекте..."
                   ↓
         User Answer
                   ↓
         Extract Info ← Может заполнить несколько полей!
                   ↓
         Update Context
                   ↓
         Check Reference Points снова
                   ↓
    [RP1: ✓] [RP2: Определить проблему] ← Следующий
                   ↓
         Generate Question (контекстный!)
                   ↓
    "Вы упомянули {детали из RP1}, какую конкретно
     проблему это решает?"
                   ↓
         ...

ЦИКЛ продолжается, пока:
- Все P0 reference points заполнены
- Все P1 достигнуты (или 80%+)
- Макс 20 вопросов
```

---

## Integration с Qdrant

### Use Cases

**1. Контекстная проверка:**
```python
# Пользователь сказал: "Бюджет 300 тысяч рублей"
fpg_req = qdrant.search("минимальный бюджет ФПГ")
# → "Для ФПГ минимум 500,000₽"

hint = "💡 Обратите внимание: минимальный бюджет для ФПГ - 500,000₽"
```

**2. Умные подсказки:**
```python
# Reference Point: "Узнать методологию"
# Тип проекта: "социальный", "работа с детьми"

similar_projects = qdrant.search(
    "методология социальные проекты дети",
    limit=3
)

hint = f"""
💡 Совет: Похожие успешные проекты обычно используют:
- {similar_projects[0]['key_method']}
- {similar_projects[1]['key_method']}
"""
```

**3. Адаптация вопросов:**
```python
# Генерировать вопрос с учетом требований ФПГ
fpg_requirements = qdrant.search(
    f"{reference_point.name} требования ФПГ"
)

question = llm.generate(
    context + fpg_requirements  # Вопрос учитывает требования!
)
```

---

## Преимущества новой архитектуры

### ✅ VS жесткие вопросы

| Аспект | Жесткие вопросы | Reference Points |
|--------|----------------|------------------|
| Адаптация | ❌ Нет | ✅ Полная |
| Контекст | ❌ Теряется | ✅ Учитывается |
| Естественность | ❌ Допрос | ✅ Беседа |
| Эффективность | ❌ Много лишнего | ✅ Только нужное |
| Персонализация | ❌ Одинаково для всех | ✅ Для каждого свой путь |
| Qdrant integration | ⚠️ Сложно | ✅ Органично |

### Пример разницы

**Жесткие вопросы:**
```
Q7: Опишите методологию реализации проекта.
```
- Непонятно новичку
- Не учитывает, что уже сказано
- Формальный тон

**Reference Points:**
```
[Context: Социальный проект, новичок, уже рассказал про помощь семьям]

AI: "Вы хотите помогать многодетным семьям - это замечательно!
     Расскажите, какие конкретные шаги вы планируете?
     Например, будут ли это консультации, мастер-классы,
     материальная помощь?"

💡 Совет: В успешных проектах ФПГ обычно указывают 3-5
   конкретных активностей с четкими сроками.
```

---

## Implementation Plan

### Phase 1: Core System

```python
# 1. Определить Reference Points
REFERENCE_POINTS = [...]  # 8-10 основных

# 2. Создать Context Engine
context_engine = ContextEngine()

# 3. Интегрировать Qdrant
qdrant_client = QdrantClient("5.35.88.251:6333")

# 4. Создать Adaptive Question Generator
generator = AdaptiveQuestionGenerator(
    llm=claude_opus,
    qdrant=qdrant_client
)
```

### Phase 2: Interview Loop

```python
async def conduct_adaptive_interview(user_data):
    context = init_context(user_data)

    while not all_required_points_covered(context):
        # Выбрать следующий reference point
        next_rp = select_next_reference_point(
            REFERENCE_POINTS,
            context
        )

        if next_rp is None:
            break  # Все собрано!

        # Сгенерировать вопрос
        question = await generator.generate_question(
            reference_point=next_rp,
            context=context
        )

        # Задать вопрос
        answer = await ask_user(question)

        # Обновить контекст
        context = update_context(context, answer)

        # Проверить лимит
        if context['questions_asked'] >= 20:
            break

    return context['collected_fields']
```

---

## Источники Best Practices

1. **Semi-structured interviews (NUS 2024):** Гибкость и адаптация
2. **Discovery interviews:** Итеративный процесс, контекст
3. **Contextual inquiry (NN/Group):** Партнерство, естественный поток
4. **Grant Assistant (TechCrunch):** AI questionnaire как консультант
5. **UX Research frameworks:** Real-time адаптация

---

**Вывод:** Reference Points >> Жесткие вопросы!

**Создано:** 2025-10-20
**Основано на:** WebSearch research + Best practices
