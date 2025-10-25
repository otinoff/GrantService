# Training Data для RL InteractiveInterviewer

## Обзор

Эта папка содержит данные для обучения RL-агента:
- Успешные интервью (audit_score ≥ 70)
- Неудачные интервью (audit_score < 50)
- Все интервью для анализа

---

## Структура

```
02_Training_Data/
├── all_interviews/           # Все собранные интервью (12 шт)
│   ├── AN-*.md              # Анкеты в markdown
│   └── EKATERINA_*.md
├── successful_interviews/    # Успешные (для positive examples)
│   └── (будут отобраны после анализа)
├── failed_interviews/        # Неудачные (для negative examples)
│   └── (будут отобраны после анализа)
└── synthetic_data/          # Синтетические данные (будущее)
```

---

## Существующие интервью

### Из all_interviews/ (12 примеров)

**archery_kemerovo (11 анкет):**
- AN-20251013-archery_kemerovo-260-RS-001.md
- AN-20251013-archery_kemerovo-462-RS-001.md
- AN-20251013-archery_kemerovo-493-RS-001.md
- AN-20251013-archery_kemerovo-587-RS-001.md
- AN-20251013-archery_kemerovo-646-RS-001.md
- AN-20251013-archery_kemerovo-648-RS-001.md
- AN-20251013-archery_kemerovo-676-RS-001.md
- AN-20251013-archery_kemerovo-801-RS-001.md
- AN-20251013-archery_kemerovo-822-RS-001.md
- AN-20251013-archery_kemerovo-844-RS-001.md
- AN-20251013-archery_kemerovo-959-RS-001.md

**Другие:**
- AN-20251012-Natalia_bruzzzz-001-RS-001.md
- EKATERINA_20251010_235448-RS-016.md (?)

---

## Задачи по организации данных

### Шаг 1: Извлечь audit_score

Для каждой анкеты нужно:
1. Прочитать файл
2. Найти `audit_score` (если есть)
3. Классифицировать:
   - ≥ 70 → successful_interviews/
   - < 50 → failed_interviews/
   - 50-70 → neutral (оставить в all_interviews/)

### Шаг 2: Стандартизировать формат

Конвертировать анкеты в RL-friendly формат:

```json
{
    "episode_id": "AN-20251013-archery-260",
    "project_type": "social",
    "states": [
        {
            "turn": 1,
            "question": "Как называется ваш проект?",
            "answer": "Лучники Кузбасса",
            "collected_fields": ["project_name"],
            "field_quality_scores": {"project_name": 0.8}
        },
        // ... остальные turns
    ],
    "final_audit_score": 75,
    "metadata": {
        "user_id": "archery_kemerovo",
        "date": "2025-10-13",
        "dialog_length": 15,
        "completion_time_minutes": 28
    }
}
```

### Шаг 3: Анализ паттернов

**Для успешных интервью:**
- Какие вопросы задавались?
- В каком порядке?
- Какие уточнения были эффективны?

**Для неудачных интервью:**
- Что пошло не так?
- Какие поля остались пустыми?
- Какие вопросы были непонятны?

---

## Синтетические данные (будущее)

### Зачем?

- Недостаточно реальных примеров (12 шт)
- Нужно ~1000 episodes для обучения RL
- Расширить разнообразие типов проектов

### Как генерировать?

**Метод 1: Rule-based симуляция**
```python
def simulate_interview(project_template):
    """
    Симулировать интервью на основе шаблона проекта
    """
    state = init_state(project_template)
    for i in range(15):
        question = select_question_rule_based(state)
        answer = generate_answer(project_template, question)
        state = update_state(state, question, answer)
    return episode
```

**Метод 2: LLM-based генерация**
```python
def generate_synthetic_episode(project_type):
    """
    Использовать GPT/Claude для генерации реалистичных диалогов
    """
    prompt = f"Generate realistic interview for {project_type} project..."
    episode = llm.generate(prompt)
    return episode
```

**Метод 3: Augmentation**
```python
def augment_existing_episode(episode):
    """
    Вариации существующих интервью:
    - Изменить порядок вопросов
    - Перефразировать ответы
    - Добавить/убрать детали
    """
    return augmented_episode
```

---

## Метрики качества данных

### Разнообразие

**Типы проектов:**
- [ ] Социальные
- [ ] Культурные
- [ ] Образовательные
- [ ] Спортивные ✓ (archery_kemerovo)
- [ ] Экологические
- [ ] Научные

**Audit scores:**
- High (≥80): ? примеров
- Medium (60-79): ? примеров
- Low (<60): ? примеров

### Полнота

**Обязательные поля:**
- project_name: 12/12 (100%)
- project_goal: ?/12
- problem_description: ?/12
- target_audience: ?/12
- ...

---

## Использование данных

### Offline Training

```python
from rl_interviewer import PPOAgent, load_episodes

# Загрузить данные
train_episodes = load_episodes('02_Training_Data/all_interviews')

# Аугментация
train_episodes += augment_episodes(train_episodes, factor=10)

# Обучение
agent = PPOAgent()
agent.train(train_episodes, epochs=1000)
```

### Evaluation

```python
# Разделить на train/val/test
train, val, test = split_episodes(all_episodes, [0.7, 0.15, 0.15])

# Оценить на validation
metrics = agent.evaluate(val)
print(f"Avg reward: {metrics['avg_reward']}")
print(f"Avg audit score: {metrics['avg_audit_score']}")
```

---

## Следующие шаги

### Немедленно (Week 1):
1. [ ] Извлечь audit_score из всех 12 анкет
2. [ ] Классифицировать на successful/failed
3. [ ] Конвертировать в JSON формат для RL
4. [ ] Проанализировать паттерны успешных интервью

### Скоро (Week 2-3):
1. [ ] Собрать 20+ новых интервью через буткемп
2. [ ] Генерировать синтетические данные (100+ episodes)
3. [ ] Создать validation set
4. [ ] Подготовить для offline training

### Позже (Week 4+):
1. [ ] Continuous data collection в production
2. [ ] Автоматическая аугментация
3. [ ] Active learning (выбор наиболее полезных примеров)

---

**Создано:** 2025-10-20
**Обновлено:** 2025-10-20
