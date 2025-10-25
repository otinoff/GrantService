# RL System Design - Reinforcement Learning для InteractiveInterviewer

## Обзор

**Цель:** Обучить агента задавать оптимальную последовательность вопросов для максимизации качества собранной информации.

**Подход:** Deep Reinforcement Learning с Policy Gradient (PPO)

---

## Формализация задачи

### Markov Decision Process (MDP)

#### 1. State Space (S)

**Компоненты состояния:**

```python
state = {
    # История диалога
    'dialog_turns': int,  # Количество обменов
    'questions_asked': List[int],  # ID заданных вопросов
    'answers_received': List[str],  # Полученные ответы

    # Собранная информация
    'collected_fields': {
        'project_name': bool,
        'project_goal': bool,
        'problem_description': bool,
        'target_audience': bool,
        # ... 20 полей всего
    },

    # Качество информации
    'field_quality_scores': {
        'project_name': float,  # 0-1, полнота/детальность
        'project_goal': float,
        # ...
    },

    # Контекст проекта (embeddings)
    'project_embeddings': np.array(384),  # Вектор типа проекта

    # Профиль пользователя
    'user_expertise': float,  # 0-1, опыт в грантах
    'user_engagement': float,  # 0-1, активность

    # Метрики диалога
    'avg_answer_length': float,
    'clarity_score': float,  # Понятность вопросов
}
```

**Размерность:** ~450 features

#### 2. Action Space (A)

**Тип действий:**

```python
action = {
    'question_category': Categorical[8],  # Категория вопроса
    'question_id': Discrete[100],  # ID конкретного вопроса из банка
    'adaptation_level': Discrete[3],  # 0: базовый, 1: упрощенный, 2: углубленный
    'follow_up': Binary,  # Нужен ли follow-up вопрос?
}
```

**Категории вопросов:**
1. Базовая информация (название, цель)
2. Проблема и актуальность
3. Целевая аудитория
4. Методология реализации
5. Бюджет и ресурсы
6. Команда и партнеры
7. Риски и устойчивость
8. Уточняющие вопросы

**Всего действий:** 8 × 100 × 3 × 2 = 4,800 возможных действий

#### 3. Reward Function (R)

**Компоненты награды:**

```python
def compute_reward(state, action, next_state, final=False):
    if final:
        # Финальная награда после завершения интервью
        audit_score = auditor.evaluate_anketa(next_state['collected_fields'])

        reward = (
            0.4 * (audit_score / 100) +  # Качество анкеты
            0.3 * completeness_score(next_state) +  # Полнота
            0.2 * efficiency_score(state['dialog_turns']) +  # Эффективность
            0.1 * user_satisfaction(next_state)  # Удовлетворенность
        )

        # Бонусы
        if audit_score >= 80:
            reward += 0.2
        if state['dialog_turns'] <= 20:
            reward += 0.1

    else:
        # Промежуточная награда на каждом шаге
        reward = (
            0.5 * information_gain(state, next_state) +  # Прирост информации
            0.3 * answer_quality(next_state['answers_received'][-1]) +  # Качество ответа
            0.2 * relevance_score(action, state)  # Релевантность вопроса
        )

        # Штрафы
        if is_repetitive_question(action, state):
            reward -= 0.3
        if answer_is_unclear(next_state['answers_received'][-1]):
            reward -= 0.1

    return reward
```

**Диапазон награды:** [-1, 1]

#### 4. Policy (π)

**Архитектура нейросети:**

```
Input: state (450 features)
    ↓
Embedding Layer (450 → 256)
    ↓
LSTM (256 → 128) ← Для учета истории
    ↓
Dense (128 → 128)
    ↓
ReLU + Dropout(0.2)
    ↓
Dense (128 → 64)
    ↓
Split:
    ├── Policy Head (64 → 4800)     # Probability distribution over actions
    └── Value Head (64 → 1)          # Estimated value of state
```

---

## RL Алгоритм: Proximal Policy Optimization (PPO)

### Почему PPO?

✅ Stable training (важно для production)
✅ Sample efficient (мало данных на старте)
✅ Works with continuous and discrete actions
✅ Easy to implement and tune

### Гиперпараметры

```python
PPO_CONFIG = {
    'learning_rate': 3e-4,
    'gamma': 0.99,  # Discount factor
    'lambda_gae': 0.95,  # GAE parameter
    'clip_epsilon': 0.2,  # PPO clipping
    'epochs_per_update': 10,
    'batch_size': 64,
    'horizon': 30,  # Max dialog turns
}
```

---

## Данные для обучения

### Offline Learning (Phase 1)

**Источники:**
1. Существующие 12 анкет из буткемпа
2. Синтетические данные (симулированные диалоги)
3. Экспертные траектории (ручные примеры идеальных интервью)

**Формат:**
```json
{
    "episode_id": "001",
    "states": [...],
    "actions": [...],
    "rewards": [...],
    "final_audit_score": 75
}
```

### Online Learning (Phase 2)

**Real-time сбор:**
- Каждое интервью → сохраняется как episode
- Аудит в конце → финальная награда
- User feedback → корректировка reward

**Exploration vs Exploitation:**
- ε-greedy: 20% случайных действий (exploration)
- 80% policy-based (exploitation)

---

## Архитектура системы

```
┌─────────────────────────────────────────────────┐
│           InteractiveInterviewerAgent            │
│  (текущая реализация с жесткими вопросами)      │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
         ┌─────────────────────┐
         │   RL Wrapper         │
         │  - State encoder     │
         │  - Action decoder    │
         │  - Reward calculator │
         └──────────┬───────────┘
                    │
                    ↓
         ┌──────────────────────┐
         │   PPO Agent          │
         │  - Policy network    │
         │  - Value network     │
         │  - Experience buffer │
         └──────────┬───────────┘
                    │
                    ↓
         ┌──────────────────────┐
         │   Training Pipeline  │
         │  - Offline learning  │
         │  - Online fine-tuning│
         │  - A/B testing       │
         └──────────────────────┘
```

---

## Метрики и мониторинг

### Training Metrics

**Loss functions:**
- `policy_loss`: Negative log-likelihood of taken actions
- `value_loss`: MSE between predicted and actual returns
- `entropy_loss`: Для exploration

**Performance metrics:**
- `avg_episode_reward`: Средняя награда за episode
- `avg_audit_score`: Средний audit score финальных анкет
- `avg_dialog_length`: Среднее количество вопросов

### Production Metrics

**Real-time:**
- User satisfaction (1-5 stars)
- Completion rate (% завершенных интервью)
- Average time per interview

**Post-interview:**
- Audit score distribution
- Field completeness
- Grant success rate (long-term)

---

## Этапы реализации

### Phase 1: Offline Training (Week 1-2)

```python
# 1. Подготовить датасет
episodes = load_existing_interviews(12) + generate_synthetic(100)

# 2. Обучить baseline policy
agent = PPOAgent(state_dim=450, action_dim=4800)
agent.train_offline(episodes, epochs=1000)

# 3. Оценить на validation set
metrics = agent.evaluate(validation_episodes)
print(f"Avg reward: {metrics['avg_reward']}")
```

### Phase 2: Integration (Week 3)

```python
# Обернуть текущего агента
class RLInterviewer(InteractiveInterviewerAgent):
    def __init__(self):
        super().__init__()
        self.rl_agent = PPOAgent.load('checkpoints/best_model.pt')

    async def select_next_question(self, state):
        action = self.rl_agent.act(state)
        question = self.decode_action(action)
        return question
```

### Phase 3: Online Learning (Week 4+)

```python
# Continuous learning from production
async def interview_with_learning(user_id):
    episode = []
    state = init_state()

    while not done:
        action = agent.act(state, explore=True)
        next_state, reward = await execute_action(action)
        episode.append((state, action, reward))
        state = next_state

    # Обучение после завершения
    agent.learn_from_episode(episode)
```

---

## Риски и митигация

### Риск 1: Недостаточно данных

**Митигация:**
- Синтетические данные (симуляция)
- Transfer learning от других conversational agents
- Few-shot learning подходы

### Риск 2: Нестабильное обучение

**Митигация:**
- PPO с conservative clipping
- Regular checkpointing
- Rollback к предыдущей версии при деградации

### Риск 3: Плохой user experience

**Митигация:**
- A/B тестирование (50% старый агент, 50% RL)
- Human-in-the-loop validation
- Постепенный rollout (5% → 20% → 50% → 100%)

---

## Вдохновение: Michael's RL System

Изучить реализацию в:
```
C:\SnowWhiteAI\Michael\.rl/
C:\SnowWhiteAI\Michael\HOW_TO_USE_RL_SYSTEM.md
C:\SnowWhiteAI\Michael\RL_SYSTEM_ACTIVATED.md
```

**Можем переиспользовать:**
- Архитектуру reward tracking
- Memory system для хранения episodes
- Learning loop и checkpointing

---

## Литература

**RL Foundations:**
- Sutton & Barto - "Reinforcement Learning: An Introduction"
- Schulman et al. - "Proximal Policy Optimization Algorithms" (2017)

**Conversational AI:**
- Li et al. - "Deep Reinforcement Learning for Dialogue Generation" (2016)
- Serban et al. - "A Deep Reinforcement Learning Chatbot" (2017)

**Applied RL:**
- OpenAI Spinning Up in Deep RL
- Ray RLlib documentation

---

**Автор:** Grant Service AI Team
**Дата:** 2025-10-20
**Версия:** 1.0
