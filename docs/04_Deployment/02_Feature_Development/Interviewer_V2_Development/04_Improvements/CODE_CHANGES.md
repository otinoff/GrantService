# Code Changes - Improved InteractiveInterviewer

## Ключевые изменения

### 1. Ограничить уточняющие вопросы (макс 5 за всё интервью)

**Файл:** `agents/interactive_interviewer_agent.py`

**Добавить в `__init__`:**
```python
def __init__(self, db, llm_provider: str = "claude_code"):
    super().__init__("interactive_interviewer", db, llm_provider)

    # ... существующий код ...

    # НОВОЕ: Трекинг уточняющих вопросов
    self.clarifying_questions_budget = 5  # Максимум за всё интервью
    self.clarifying_questions_used = 0

    # НОВОЕ: Подключение к Qdrant
    try:
        from qdrant_client import QdrantClient
        self.qdrant = QdrantClient(
            host="5.35.88.251",  # Production server
            port=6333,
            timeout=10
        )
        self.collection_name = "knowledge_sections"
        logger.info("✅ Qdrant connected (5.35.88.251:6333)")
    except Exception as e:
        logger.warning(f"⚠️ Qdrant unavailable: {e}")
        self.qdrant = None
```

---

### 2. Улучшенный метод `_ask_clarifying_questions`

**Заменить существующий метод:**

```python
async def _ask_clarifying_questions(
    self,
    audit_result: dict,
    block_num: int
) -> dict:
    """
    Задать ПРИОРИТЕТНЫЕ уточняющие вопросы

    Максимум 5 вопросов за всё интервью!
    """
    clarifications = {}

    # Проверить бюджет
    remaining_budget = self.clarifying_questions_budget - self.clarifying_questions_used

    if remaining_budget <= 0:
        logger.info(f"⚠️ Блок {block_num}: Бюджет уточняющих вопросов исчерпан (0/{self.clarifying_questions_budget})")
        return clarifications

    logger.info(f"💡 Блок {block_num}: Осталось {remaining_budget} уточняющих вопросов")

    # Извлечь issues из аудита
    issues = audit_result.get('issues', {})

    if not issues:
        logger.info(f"✅ Блок {block_num}: Нет issues, уточнения не нужны")
        return clarifications

    # НОВОЕ: Приоритизация
    prioritized_issues = self._prioritize_issues(issues)

    # Взять топ-N в пределах бюджета
    questions_to_ask = min(len(prioritized_issues), remaining_budget)

    logger.info(f"📋 Блок {block_num}: Задаю {questions_to_ask} приоритетных вопросов")

    for i, issue in enumerate(prioritized_issues[:questions_to_ask]):
        field = issue['field']

        # Генерировать вопрос
        question = await self._generate_clarifying_question_smart(
            field=field,
            issue_details=issue['details'],
            block_num=block_num
        )

        # Задать вопрос (здесь ваша логика общения с пользователем)
        # answer = await self._ask_user(question)

        # Placeholder (замените на реальную логику)
        answer = f"[Ответ пользователя на вопрос {i+1}]"

        clarifications[field] = answer
        self.clarifying_questions_used += 1

        logger.info(f"  ✓ Вопрос {i+1}/{questions_to_ask}: {field}")

    logger.info(f"📊 Использовано {self.clarifying_questions_used}/{self.clarifying_questions_budget} уточняющих вопросов")

    return clarifications
```

---

### 3. НОВЫЙ метод: Приоритизация issues

**Добавить новый метод:**

```python
def _prioritize_issues(self, issues: dict) -> list:
    """
    Приоритизировать issues по важности

    Returns:
        List[dict]: Список issues, отсортированный по приоритету
            [
                {
                    'field': 'project_goal',
                    'priority': 0,  # 0 = высший
                    'severity': 0.8,
                    'details': {...}
                },
                ...
            ]
    """
    # Карта приоритетов полей
    PRIORITY_MAP = {
        # P0 (критично) - без этого проект непонятен
        'project_goal': 0,
        'problem_description': 0,
        'target_audience': 0,

        # P1 (важно) - нужно для оценки заявки
        'budget_total': 1,
        'methodology': 1,
        'expected_results': 1,
        'budget_breakdown': 1,

        # P2 (желательно) - улучшает заявку, но не критично
        'team_description': 2,
        'partners': 2,
        'risks': 2,
        'sustainability': 2,
        'project_name': 2,

        # P3 (опционально)
        'region': 3,
        'project_duration_months': 3,
    }

    prioritized = []

    for field, issue_details in issues.items():
        priority = PRIORITY_MAP.get(field, 3)  # Default P3
        severity = issue_details.get('severity', 0.5)  # 0-1

        prioritized.append({
            'field': field,
            'priority': priority,
            'severity': severity,
            'details': issue_details
        })

    # Сортировка: сначала по priority (меньше = важнее), потом по severity (больше = хуже)
    prioritized.sort(key=lambda x: (x['priority'], -x['severity']))

    return prioritized
```

---

### 4. НОВЫЙ метод: Умная генерация вопроса (с Qdrant)

**Добавить новый метод:**

```python
async def _generate_clarifying_question_smart(
    self,
    field: str,
    issue_details: dict,
    block_num: int
) -> str:
    """
    Сгенерировать умный уточняющий вопрос

    Использует:
    - Контекст из базы знаний ФПГ (Qdrant)
    - Информацию об issue из аудита
    - Текущее состояние анкеты
    """
    # Базовый вопрос
    base_questions = {
        'project_goal': "Уточните, пожалуйста: какую конкретную цель вы хотите достичь в результате проекта?",
        'problem_description': "Опишите проблему более детально: кого она затрагивает и как проявляется?",
        'target_audience': "Кто именно будет пользоваться результатами проекта? Опишите вашу целевую аудиторию.",
        'methodology': "Как именно вы планируете реализовать проект? Опишите конкретные шаги.",
        'budget_total': "Какой общий бюджет проекта вы планируете? (в рублях)",
        'expected_results': "Какие конкретные, измеримые результаты вы ожидаете получить?",
    }

    question = base_questions.get(field, f"Уточните информацию о поле: {field}")

    # НОВОЕ: Добавить контекст из Qdrant
    if self.qdrant:
        try:
            # Поиск в базе ФПГ
            search_results = self.qdrant.search(
                collection_name=self.collection_name,
                query_text=f"требования {field} ФПГ",
                limit=1
            )

            if search_results:
                context = search_results[0].payload.get('content', '')

                # Добавить подсказку
                hint = self._extract_key_requirement(context, field)
                if hint:
                    question += f"\n\n💡 Совет: {hint}"

        except Exception as e:
            logger.warning(f"Qdrant search failed: {e}")

    return question


def _extract_key_requirement(self, content: str, field: str) -> str:
    """
    Извлечь ключевое требование из контента
    """
    # Простая эвристика (можно улучшить с LLM)
    if 'бюджет' in field.lower() and 'минимум' in content.lower():
        import re
        numbers = re.findall(r'(\d+[\s,]*\d*)\s*(?:рубл|₽)', content)
        if numbers:
            return f"Минимальный бюджет для ФПГ: {numbers[0]} рублей"

    # Взять первое предложение с ключевым словом
    sentences = content.split('.')
    for sent in sentences[:3]:  # Первые 3 предложения
        if any(keyword in sent.lower() for keyword in ['требование', 'необходимо', 'должен']):
            return sent.strip()

    return ""
```

---

### 5. НОВЫЙ метод: Прогресс-бар

**Добавить новый метод:**

```python
async def _show_progress(self, current_block: int, current_question: int = 0):
    """
    Показать прогресс интервью

    Args:
        current_block: 1, 2, 3
        current_question: номер вопроса в блоке (0-5)
    """
    total_questions = 15
    questions_done = (current_block - 1) * 5 + current_question

    percentage = int((questions_done / total_questions) * 100)

    bar_length = 20
    filled = int(bar_length * questions_done / total_questions)
    bar = "█" * filled + "░" * (bar_length - filled)

    blocks_status = [
        f"{'✓' if current_block > 1 else '→'} Блок 1: Базовая информация",
        f"{'✓' if current_block > 2 else '→' if current_block == 2 else ' '} Блок 2: Реализация",
        f"{'✓' if current_block > 3 else '→' if current_block == 3 else ' '} Блок 3: Команда и устойчивость"
    ]

    message = f"""
[{bar}] {questions_done}/{total_questions} вопросов ({percentage}%)

{chr(10).join(blocks_status)}

Осталось уточняющих вопросов: {self.clarifying_questions_budget - self.clarifying_questions_used}
"""

    logger.info(message)

    # Промежуточные похвалы
    if questions_done == 5:
        logger.info("✨ Отличное начало! Осталось еще 10 вопросов.")
    elif questions_done == 10:
        logger.info("🎯 Половина пути! Вы молодец!")
    elif questions_done == 15:
        logger.info("🏁 Базовые вопросы завершены! Проверяю качество...")
```

---

### 6. Интеграция прогресс-бара в conduct_interview_with_audit

**Обновить метод `conduct_interview_with_audit`:**

```python
async def conduct_interview_with_audit(
    self,
    user_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Основной метод: проведение интервью с интерактивным аудитом
    """
    start_time = time.time()
    logger.info("=" * 80)
    logger.info("НАЧАЛО ИНТЕРАКТИВНОГО ИНТЕРВЬЮ С АУДИТОМ")
    logger.info("=" * 80)

    # Инициализация
    anketa = self._init_anketa(user_data)
    interactive_feedback = []

    # НОВОЕ: Сброс счетчика уточняющих вопросов
    self.clarifying_questions_used = 0

    # БЛОК 1
    logger.info("\n[БЛОК 1/3] Базовая информация о проекте")
    await self._show_progress(current_block=1, current_question=0)  # НОВОЕ!

    block1_answers = await self._ask_question_block(
        block_num=1,
        questions=INTERVIEW_QUESTIONS["block_1"],
        user_data=user_data
    )
    anketa.update(self._map_block1_answers(block1_answers))

    await self._show_progress(current_block=1, current_question=5)  # НОВОЕ!

    # Interim Audit #1
    audit1_result = await self._interim_audit(anketa, block_num=1)
    clarifying1 = await self._ask_clarifying_questions(audit1_result, block_num=1)  # УЛУЧШЕННЫЙ!
    interactive_feedback.append({
        'block': 1,
        'audit_score': audit1_result.get('partial_score', 0),
        'clarifications': clarifying1
    })
    anketa.update(clarifying1)

    # БЛОК 2
    logger.info("\n[БЛОК 2/3] Методология и бюджет")
    await self._show_progress(current_block=2, current_question=0)  # НОВОЕ!

    # ... аналогично для блоков 2 и 3 ...

    # ФИНАЛЬНЫЙ АУДИТ
    logger.info("\n[ФИНАЛЬНЫЙ АУДИТ] Комплексная оценка заявки")
    final_audit = await self._final_audit(anketa)

    # ... остальной код без изменений ...
```

---

## Summary изменений

### Добавлено:
1. ✅ Бюджет уточняющих вопросов (5 макс)
2. ✅ Приоритизация issues (P0, P1, P2, P3)
3. ✅ Интеграция с Qdrant (база ФПГ)
4. ✅ Умные уточнения с контекстом
5. ✅ Прогресс-бар с мотивацией

### Изменено:
- `__init__`: добавлены budget tracking и Qdrant
- `_ask_clarifying_questions`: ограничение и приоритизация
- `conduct_interview_with_audit`: прогресс-бар

### Итого:
- **15 базовых** + **макс 5 уточняющих** = **15-20 вопросов**
- **25-30 минут** времени
- **Контекст из базы ФПГ**

---

## Тестирование

```python
# Локальный тест
async def test_improved_interviewer():
    from agents.interactive_interviewer_agent import InteractiveInterviewerAgent

    agent = InteractiveInterviewerAgent(db, llm_provider="claude_code")

    user_data = {
        'telegram_id': 123456,
        'username': 'test_user',
        'grant_fund': 'fpg'
    }

    result = await agent.conduct_interview_with_audit(user_data)

    print(f"Audit score: {result['audit_score']}")
    print(f"Уточняющих вопросов задано: {agent.clarifying_questions_used}/5")
    print(f"Время: {result['processing_time']:.1f} секунд")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_improved_interviewer())
```

---

**Готово к реализации!** 🚀
