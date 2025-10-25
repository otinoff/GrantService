# Implementation Plan - Улучшенный InteractiveInterviewer

## Цель

Создать **полностью интерактивного, но комфортного** интервьюера:
- ✅ 15 базовых вопросов (обязательно)
- ✅ Макс 5 уточняющих (адаптивно)
- ✅ Интеграция с Qdrant (база знаний ФПГ на сервере)
- ✅ 25-30 минут времени
- ✅ UX best practices

---

## Текущее состояние

### InteractiveInterviewerAgent (agents/interactive_interviewer_agent.py)

**Есть:**
- 15 базовых вопросов (3 блока × 5) ✓
- Interim audits после каждого блока ✓
- Clarifying questions на основе аудита ✓

**Проблемы:**
- ❌ Неограниченное количество уточняющих вопросов
- ❌ Нет приоритизации (все подряд)
- ❌ Нет интеграции с Qdrant
- ❌ Нет skip logic (задает лишнее)
- ❌ Нет прогресс-бара

---

## Улучшения

### 1. Ограничить уточняющие вопросы (макс 5)

**Текущий код:**
```python
# В _ask_clarifying_questions() - задает все подряд
for field, issue in audit_result['issues'].items():
    question = generate_clarifying_question(field, issue)
    answer = await ask_user(question)
    clarifications[field] = answer
```

**Улучшенный:**
```python
async def _ask_clarifying_questions(
    self,
    audit_result: dict,
    block_num: int,
    max_questions: int = 5  # НОВОЕ!
) -> dict:
    """
    Задать приоритетные уточняющие вопросы
    """
    # 1. Собрать все issues
    issues = audit_result.get('issues', {})

    # 2. Приоритизировать
    prioritized = self._prioritize_issues(issues)

    # 3. Взять топ-N
    top_issues = prioritized[:max_questions]

    # 4. Задать вопросы
    clarifications = {}
    for issue in top_issues:
        question = self._generate_clarifying_question(issue)
        answer = await self._ask_user(question)
        clarifications[issue['field']] = answer

    return clarifications
```

**Приоритизация:**
```python
def _prioritize_issues(self, issues: dict) -> list:
    """
    Приоритизировать issues по важности

    P0 (критично): цель, проблема, ЦА
    P1 (важно): бюджет, методология, результаты
    P2 (желательно): риски, команда, устойчивость
    """
    PRIORITY_MAP = {
        # P0 - критично для понимания проекта
        'project_goal': 0,
        'problem_description': 0,
        'target_audience': 0,

        # P1 - важно для оценки заявки
        'budget_total': 1,
        'methodology': 1,
        'expected_results': 1,
        'budget_breakdown': 1,

        # P2 - желательно, но не критично
        'team_description': 2,
        'partners': 2,
        'risks': 2,
        'sustainability': 2,
    }

    prioritized = []
    for field, issue in issues.items():
        priority = PRIORITY_MAP.get(field, 3)
        prioritized.append({
            'field': field,
            'issue': issue,
            'priority': priority,
            'severity': issue.get('severity', 0.5)  # От аудита
        })

    # Сортировка: сначала по priority, потом по severity
    prioritized.sort(key=lambda x: (x['priority'], -x['severity']))

    return prioritized
```

---

### 2. Интеграция с Qdrant (база знаний ФПГ)

**Подключение:**
```python
from qdrant_client import QdrantClient

class ImprovedInterviewerAgent(InteractiveInterviewerAgent):
    def __init__(self, db, llm_provider="claude_code"):
        super().__init__(db, llm_provider)

        # Подключение к Qdrant на production
        self.qdrant = QdrantClient(
            host="5.35.88.251",  # Production server
            port=6333,
            timeout=10
        )

        self.collection_name = "knowledge_sections"
```

**Use Case 1: Контекстные подсказки**
```python
async def _provide_context_hints(self, answer: str, field: str):
    """
    Дать подсказки на основе базы знаний ФПГ
    """
    # Поиск похожих секций
    results = self.qdrant.search(
        collection_name=self.collection_name,
        query_vector=self._embed_text(answer),
        limit=3,
        score_threshold=0.7
    )

    if results:
        # Взять самый релевантный
        top_result = results[0]

        # Извлечь ключевые моменты
        key_points = self._extract_key_points(top_result.payload['content'])

        # Отправить подсказку
        hint = f"💡 Совет: Похожие успешные проекты обычно указывают:\n{key_points}"
        await self._send_message(hint)
```

**Use Case 2: Проверка требований**
```python
async def _check_fpg_requirements(self, field: str, value: any):
    """
    Проверить соответствие требованиям ФПГ
    """
    # Найти требования для этого поля
    requirements = self.qdrant.search(
        collection_name=self.collection_name,
        query_text=f"требования {field}",
        limit=1
    )

    if requirements:
        req_text = requirements[0].payload['content']

        # Проверить соответствие (LLM)
        is_compliant = await self._check_compliance(value, req_text)

        if not is_compliant:
            warning = f"⚠️ Внимание: {req_text}"
            await self._send_message(warning)
```

**Use Case 3: Умные follow-up вопросы**
```python
async def _generate_smart_followup(self, field: str, answer: str):
    """
    Сгенерировать умный follow-up на основе контекста ФПГ
    """
    # Определить тип проекта
    project_type = self._classify_project_type(self.anketa)

    # Найти специфичные вопросы для этого типа
    specific_qs = self.qdrant.search(
        collection_name=self.collection_name,
        query_text=f"вопросы для {project_type} проект {field}",
        limit=2
    )

    if specific_qs:
        # Сгенерировать вопрос на основе контекста
        context = specific_qs[0].payload['content']
        question = await self._llm_generate_question(field, answer, context)
        return question
```

---

### 3. Skip Logic (не задавать лишнее)

```python
def _should_skip_question(self, question_id: str, state: dict) -> bool:
    """
    Определить, нужно ли пропустить вопрос
    """
    # Проверить, уже ответили на этот вопрос?
    if question_id in state['answered_questions']:
        return True

    # Проверить контекстные условия
    skip_rules = {
        'partners': lambda s: s.get('project_type') == 'solo',
        'team_description': lambda s: 'команда' in s.get('methodology', '').lower(),
        'sustainability': lambda s: s.get('project_duration_months', 0) < 6,
    }

    if question_id in skip_rules:
        return skip_rules[question_id](state)

    return False
```

---

### 4. Прогресс-бар и промежуточная мотивация

```python
async def _show_progress(self, current: int, total: int, block_name: str):
    """
    Показать прогресс
    """
    percentage = int((current / total) * 100)
    bar_length = 20
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)

    message = f"""
[{bar}] {current}/{total} вопросов ({percentage}%)

{'✓' if current > 5 else '→'} Блок 1: Базовая информация
{'✓' if current > 10 else '→' if current > 5 else ' '} Блок 2: Реализация
{'✓' if current > 15 else '→' if current > 10 else ' '} Блок 3: Команда
"""

    await self._send_message(message)

    # Промежуточные похвалы
    if current == 5:
        await self._send_message("✨ Отличное начало! Осталось еще 10 вопросов.")
    elif current == 10:
        await self._send_message("🎯 Половина пути! Вы молодец!")
    elif current == 15:
        await self._send_message("🏁 Почти готово! Последние штрихи...")
```

---

### 5. Улучшенный final audit с Qdrant

```python
async def _final_audit_with_context(self, anketa: dict):
    """
    Финальный аудит с учетом контекста ФПГ
    """
    # Базовый аудит
    basic_audit = await self.auditor.evaluate_anketa(anketa)

    # Дополнительная проверка через Qdrant
    for field, value in anketa.items():
        # Найти требования ФПГ для этого поля
        fpg_requirements = self.qdrant.search(
            collection_name=self.collection_name,
            query_text=f"требования ФПГ {field}",
            limit=1
        )

        if fpg_requirements:
            # Проверить соответствие
            compliance = await self._check_compliance(
                value,
                fpg_requirements[0].payload['content']
            )

            # Скорректировать оценку
            if not compliance:
                basic_audit['scores'][field] -= 10

    # Пересчитать итоговый score
    final_score = self._recalculate_score(basic_audit)

    return {
        **basic_audit,
        'final_score': final_score,
        'fpg_compliance': True  # or False
    }
```

---

## Deployment Plan

### Phase 1: Локальная разработка

```bash
cd C:\SnowWhiteAI\GrantService\agents

# 1. Создать новую ветку
git checkout -b feature/improved-interactive-interviewer

# 2. Создать improved_interactive_interviewer_agent.py
# (или улучшить существующий)

# 3. Локальное тестирование
python test_improved_interviewer.py
```

### Phase 2: GitHub

```bash
# 1. Коммит изменений
git add agents/improved_interactive_interviewer_agent.py
git commit -m "feat: Add improved interactive interviewer with Qdrant integration

- Limit follow-up questions to max 5
- Integrate with Qdrant knowledge base
- Add skip logic for redundant questions
- Implement progress bar
- Add context-aware hints from FPG database"

# 2. Push на GitHub
git push origin feature/improved-interactive-interviewer

# 3. Create Pull Request (optional)
gh pr create --title "Improved Interactive Interviewer" --body "See commit message"
```

### Phase 3: Production Deployment

```bash
# 1. SSH на production
ssh root@5.35.88.251

# 2. Pull latest code
cd /var/GrantService
git pull origin master  # или feature branch

# 3. Обновить зависимости (если нужно)
pip install qdrant-client

# 4. Restart bot
systemctl restart grantservice-bot

# 5. Check logs
tail -f /var/log/grantservice-bot.log

# 6. Проверить Qdrant connectivity
curl http://localhost:6333/collections/knowledge_sections
```

---

## Testing Checklist

### Локально:
- [ ] 15 базовых вопросов работают
- [ ] Макс 5 уточняющих вопросов
- [ ] Qdrant подключается (5.35.88.251:6333)
- [ ] Контекстные подсказки появляются
- [ ] Skip logic работает
- [ ] Прогресс-бар отображается
- [ ] Время интервью ≤ 30 мин

### На production:
- [ ] Бот запускается без ошибок
- [ ] Qdrant доступен с сервера
- [ ] Интервью завершается успешно
- [ ] Audit score корректный
- [ ] Данные сохраняются в БД

---

## Rollback Plan

Если что-то пойдет не так:

```bash
# На production
ssh root@5.35.88.251
cd /var/GrantService

# Откатить к предыдущему коммиту
git revert HEAD

# Restart bot
systemctl restart grantservice-bot

# Проверить
systemctl status grantservice-bot
```

---

## Next Steps

1. **Сейчас:** Создать improved_interactive_interviewer_agent.py
2. **Завтра:** Локальное тестирование
3. **Послезавтра:** Деплой на production
4. **Через неделю:** Собрать feedback из буткемпа

---

**Создано:** 2025-10-20
**Готов к реализации!** 🚀
