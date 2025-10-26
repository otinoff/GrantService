# Iteration 51: AI Enhancement - Embeddings + RL

**Дата начала:** 2025-10-26
**Статус:** 🚀 PLANNING
**Цель:** Потратить 5 млн токенов GigaChat Embeddings на создание 5 коллекций + добавить RL для InterviewerAgent

---

## 🎯 Задача

**Бизнес-цель:** Показать на оценке Sber500 серьёзный AI-прогресс за 2 дня

**Технические цели:**
1. Создать 5 новых Qdrant коллекций с GigaChat Embeddings
2. Потратить ~5 млн токенов embeddings (баланс до 04.10.2026)
3. Добавить базовый RL для InterviewerAgent
4. Измерить улучшение качества (до/после)

---

## 📊 Бюджет токенов (5 млн total)

| Коллекция | Документов | Tokens/doc | Total tokens | % бюджета |
|-----------|------------|------------|--------------|-----------|
| successful_grants | 50 | 10,000 | 500,000 | 10% |
| grant_criteria | 100 | 5,000 | 500,000 | 10% |
| research_methodologies | 200 | 3,000 | 600,000 | 12% |
| budget_templates | 150 | 4,000 | 600,000 | 12% |
| user_projects | 500 | 5,000 | 2,500,000 | 50% |
| **Резерв (тестирование)** | - | - | 300,000 | 6% |
| **TOTAL** | 1,000 | - | **5,000,000** | **100%** |

---

## 📁 Структура коллекций

### 1. `successful_grants` (500K tokens)
**Источник:** Открытые данные победителей ФПГ 2020-2024

**Что храним:**
- title (название проекта)
- problem (описание проблемы)
- solution (решение)
- implementation (план реализации)
- budget (бюджет)
- fund_name (ФПГ/РНФ/РФФИ)
- year (год победы)
- region (регион)
- amount (сумма гранта)

**Embedding strategy:**
- Каждый раздел отдельно (title, problem, solution, etc.)
- Метаданные в payload для фильтрации

**Использование:**
- WriterAgent: поиск похожих успешных проектов
- Контекст для LLM: "Вот как писали победители"

---

### 2. `grant_criteria` (500K tokens)
**Источник:** Требования фондов (ФПГ, РНФ, РФФИ, региональные)

**Что храним:**
- fund_name (название фонда)
- criterion_name (название критерия)
- criterion_description (описание)
- weight (вес в оценке, 0-100%)
- requirements (конкретные требования)
- examples (примеры соответствия)

**Использование:**
- ReviewerAgent: адаптивная оценка под конкретный фонд
- AuditorAgent: проверка соответствия требованиям

---

### 3. `research_methodologies` (600K tokens)
**Источник:** Научная литература, методички, best practices

**Что храним:**
- methodology_name (SMART, Agile, Design Thinking, etc.)
- description (описание методологии)
- application_area (область применения)
- kpi_examples (примеры KPI)
- smart_goals_examples (примеры SMART-целей)
- metrics (метрики оценки)

**Использование:**
- WriterAgent: раздел "Методология исследования"
- InterviewerAgent: подсказки по метрикам

---

### 4. `budget_templates` (600K tokens)
**Источник:** Шаблоны смет из победивших заявок

**Что храним:**
- fund_name (фонд)
- project_type (тип проекта)
- budget_categories (категории расходов)
- justification (обоснование)
- total_amount (общая сумма)
- duration_months (длительность)

**Использование:**
- WriterAgent: раздел "Бюджет"
- Проверка реалистичности запрашиваемой суммы

---

### 5. `user_projects` (2.5M tokens) - **приоритет!**
**Источник:** Готовые заявки из нашей БД

**Что векторизуем:**
- Все grant_applications (таблица)
- Структура: 10 разделов каждой заявки
- Метаданные: status, quality_score, created_at

**Использование:**
- Поиск похожих проектов пользователей
- Рекомендации: "Похожие проекты получили гранты"
- RL reward: успешные заявки = положительный feedback

---

## 🤖 RL Component

### Задача
Оптимизировать InterviewerAgent: выбирать вопросы, которые приводят к лучшим заявкам

### Архитектура

**State (состояние):**
- Текущие ответы пользователя
- Embedding текущей анкеты
- История вопросов

**Action (действие):**
- Выбор следующего вопроса из 50 возможных

**Reward (награда):**
- Положительная: заявка одобрена фондом (+10)
- Нейтральная: заявка подана (+5)
- Отрицательная: заявка не подана (-5)
- Бонус: высокая оценка ReviewerAgent (+2 за каждый балл >7)

**Algorithm:**
- Q-Learning (простой, хорошо работает)
- Epsilon-greedy exploration (90% best, 10% random)

### Implementation

**Файл:** `agents/rl_interviewer_agent.py`

**Основные компоненты:**
```python
class RLInterviewerAgent:
    def __init__(self):
        self.q_table = {}  # state -> {question_id: q_value}
        self.epsilon = 0.1  # exploration rate
        self.alpha = 0.1    # learning rate
        self.gamma = 0.9    # discount factor

    def get_next_question(self, state):
        # Epsilon-greedy
        if random.random() < self.epsilon:
            return random_question()
        else:
            return best_question_from_q_table(state)

    def update_q_value(self, state, action, reward, next_state):
        # Q-learning update
        ...
```

**Storage:**
- Сохранение Q-table в PostgreSQL
- Таблица: `rl_q_values (state_hash, question_id, q_value, updated_at)`

---

## 🧪 Testing & Metrics - Following TESTING-METHODOLOGY.md

### Test Pyramid (70% Unit / 20% Integration / 10% E2E)

#### Unit Tests (70%) - `tests/unit/`

**test_fpg_parser.py**
```python
def test_parse_fpg_grant():
    """Parse single FPG grant page"""
    html = load_fixture("fpg_grant_sample.html")
    grant = parse_fpg_grant(html)
    assert grant['title']
    assert grant['problem']
    assert len(grant['problem']) > 100
```

**test_gigachat_embeddings_client.py**
```python
def test_create_embedding():
    """Test GigaChat API embedding creation"""
    client = GigaChatEmbeddingsClient()
    text = "Тестовый текст для векторизации"
    embedding = client.create_embedding(text)
    assert len(embedding) == 1024  # GigaChat embedding size
```

**test_rl_q_table.py**
```python
def test_q_value_update():
    """Test Q-learning update formula"""
    q_table = QTable()
    state = "answered_3_questions"
    action = "ask_question_5"
    reward = 10

    q_table.update(state, action, reward)
    assert q_table.get(state, action) > 0
```

#### Integration Tests (20%) - `tests/integration/`

**test_gigachat_embedding_integration.py**
```python
@pytest.mark.integration
@pytest.mark.gigachat
def test_create_collection_with_gigachat():
    """Integration: Create Qdrant collection with GigaChat embeddings"""
    # Load sample data
    grants = load_successful_grants(limit=5)

    # Create embeddings
    loader = GigaChatEmbeddingsLoader()
    collection = loader.create_collection("test_successful_grants")

    # Verify
    assert collection.points_count == 5
    assert collection.vectors_size == 1024
```

**test_writer_with_embeddings.py**
```python
@pytest.mark.integration
@pytest.mark.gigachat
def test_writer_uses_successful_grants():
    """WriterAgent queries successful_grants collection"""
    writer = WriterAgent(use_embeddings=True)

    # Generate grant with embeddings context
    result = writer.process({
        'user_answers': sample_anketa,
        'use_successful_grants': True
    })

    # Verify embeddings were used
    assert 'successful_grants_context' in result
    assert len(result['successful_grants_context']) > 0
```

#### E2E Tests (10%) - `tests/integration/`

**test_embeddings_quality_improvement.py**
```python
@pytest.mark.e2e
@pytest.mark.slow
def test_embeddings_improve_quality():
    """E2E: Compare grant quality before/after embeddings"""
    # BASELINE (Iteration 50)
    baseline_grant = generate_grant_without_embeddings()
    baseline_score = review_grant(baseline_grant)

    # WITH EMBEDDINGS (Iteration 51)
    enhanced_grant = generate_grant_with_embeddings()
    enhanced_score = review_grant(enhanced_grant)

    # Expect improvement
    assert enhanced_score > baseline_score
    assert enhanced_score - baseline_score >= 1.0  # +1 point minimum
```

---

### AI/LLM-Specific Testing (Section 10 of TESTING-METHODOLOGY)

**Semantic Validation:**
```python
def test_embeddings_semantic_similarity():
    """Verify similar texts have high cosine similarity"""
    text1 = "Развитие науки среди молодежи"
    text2 = "Популяризация научных исследований для студентов"

    emb1 = create_embedding(text1)
    emb2 = create_embedding(text2)

    similarity = cosine_similarity(emb1, emb2)
    assert similarity > 0.7  # High similarity expected
```

**Non-Determinism Handling:**
```python
@pytest.mark.repeat(3)  # Run 3 times
def test_rl_stability():
    """RL agent should converge to similar results"""
    results = []
    for _ in range(3):
        agent = RLInterviewerAgent()
        score = agent.train(episodes=100)
        results.append(score)

    # Results should be within 10% of each other
    assert max(results) - min(results) < 0.1 * mean(results)
```

---

### Production Parity Tests

**test_production_qdrant.py**
```python
def test_use_production_qdrant():
    """Verify tests use production Qdrant (5.35.88.251:6333)"""
    from expert_agent.expert_agent import ExpertAgent

    agent = ExpertAgent()
    assert agent.qdrant.host == "5.35.88.251"
    assert agent.qdrant.port == 6333
```

**test_gigachat_credentials.py**
```python
def test_use_production_gigachat():
    """Verify GigaChat uses production credentials"""
    from shared.llm.unified_llm_client import get_client

    client = get_client(provider="gigachat")
    # Should use config.py, not env vars
    assert client.auth_method == "oauth"
```

### Метрики для презентации Sber500

| Метрика | До (Iteration 50) | После (Iteration 51) | Δ |
|---------|-------------------|----------------------|---|
| Qdrant vectors | 53 | **5,053** | +5,000 ✅ |
| Collections | 2 | **7** | +5 ✅ |
| GigaChat tokens used | 0 | **5,000,000** | +5M ✅ |
| WriterAgent quality | 3.25/10 | **5-6/10** | +2 🎯 |
| ReviewerAgent requirements | 11 | **30+** | +20 🎯 |
| InterviewerAgent questions | 50 fixed | **Adaptive (RL)** | Smart ✅ |

---

## 📋 Success Criteria

**Must Have (обязательно):**
1. ✅ 5 новых Qdrant коллекций созданы
2. ✅ 5 млн токенов GigaChat Embeddings потрачено
3. ✅ user_projects векторизованы (все grant_applications из БД)
4. ✅ WriterAgent использует successful_grants
5. ✅ RL для InterviewerAgent работает (Q-learning базовый)

**Should Have (желательно):**
1. ✅ ReviewerAgent использует grant_criteria
2. ✅ Тесты качества (до/после) показывают улучшение
3. ✅ Документация всех коллекций

**Nice to Have (бонус):**
1. ⭐ Dashboard для визуализации embeddings (t-SNE/UMAP)
2. ⭐ A/B тест: RL vs Random question selection
3. ⭐ Экспорт метрик для презентации

---

## 🗓️ Timeline (2 дня) - Following PROJECT-EVOLUTION-METHODOLOGY

### День 1 (26 октября, сегодня)

**Commit #1: Iteration plan + schemas (утро, 2 часа)**
```bash
git commit -m "feat(iteration-51): Plan + collection schemas"
```
- ✅ Create iteration plan (этот файл)
- Create Qdrant collection schemas (JSON)
- Create data models (Pydantic)
- **Test:** Schema validation
- **CI:** Lint + type check

**Commit #2: Data collection + Unit tests (день, 3 часа)**
```bash
git commit -m "feat(iteration-51): Data parsers + unit tests"
```
- Scrape successful_grants (ФПГ parser)
- Create grant_criteria dataset
- Unit tests для парсеров (70% coverage)
- **Test:** `test_fpg_parser.py`, `test_criteria_loader.py`
- **CI:** All unit tests pass

**Commit #3: Embeddings loader + Integration test (вечер, 3 часа)**
```bash
git commit -m "feat(iteration-51): GigaChat embeddings loader"
```
- Create `scripts/gigachat_embeddings_loader.py`
- Load successful_grants (500K tokens)
- Integration test: `test_gigachat_embedding.py`
- **Test:** Verify collection created, vectors count
- **CI:** Integration tests pass

**Commit #4: Load 3 more collections (вечер, 2 часа)**
```bash
git commit -m "feat(iteration-51): Load grant_criteria + research + budget"
```
- Load grant_criteria (500K)
- Load research_methodologies (600K)
- Load budget_templates (600K)
- **Test:** All collections green
- **Metrics:** 2.2M / 5M tokens used (44%)

### День 2 (27 октября)

**Commit #5: Vectorize user_projects (утро, 3 часа)**
```bash
git commit -m "feat(iteration-51): Vectorize all user grant applications"
```
- Query all grant_applications from PostgreSQL
- Create embeddings (2.5M tokens)
- **Test:** `test_user_projects_vectorization.py`
- **Metrics:** 4.7M / 5M tokens used (94%)

**Commit #6: WriterAgent integration (день, 2 часа)**
```bash
git commit -m "feat(iteration-51): Integrate successful_grants in WriterAgent"
```
- Add semantic search to WriterAgent
- Query successful_grants before generation
- **Test:** Compare quality (Iteration 50 baseline)
- **Metrics:** Readiness score improvement

**Commit #7: RL for InterviewerAgent (день, 3 часа)**
```bash
git commit -m "feat(iteration-51): Q-learning for InterviewerAgent"
```
- Create `agents/rl_interviewer_agent.py`
- Q-table storage in PostgreSQL
- **Test:** `test_rl_convergence.py` (100 simulations)
- **Metrics:** Questions reduction (50 → 40)

**Commit #8: Documentation + SUMMARY (вечер, 2 часа)**
```bash
git commit -m "docs(iteration-51): Summary + metrics for Sber500"
```
- Create ITERATION_51_SUMMARY.md
- Export metrics dashboard
- Final token usage report
- **Deliverable:** Ready for presentation

---

## 🔧 Technical Implementation

### GigaChat Embeddings API

**Endpoint:**
```python
POST https://gigachat.devices.sberbank.ru/api/v1/embeddings

Headers:
  Authorization: Bearer <access_token>

Body:
{
  "model": "Embeddings",  # или "EmbeddingsGigaR"
  "input": ["текст для векторизации"]
}

Response:
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.1, 0.2, ...],  # 1024-dim vector
      "index": 0
    }
  ],
  "model": "Embeddings"
}
```

**Размерность:** 1024 (vs 384 у Sentence Transformers)

**Скрипт:**
```bash
python scripts/create_gigachat_embeddings.py \
  --collection successful_grants \
  --source data/fpg_winners_2020_2024.json \
  --batch-size 100
```

---

## 📊 Data Sources

### 1. ФПГ победители (successful_grants)
**Источники:**
- https://фондпрезидентскихгрантов.рф/competitions/results
- Парсинг: BeautifulSoup + Selenium
- Формат: JSON [{title, problem, solution, ...}, ...]

### 2. Критерии оценки (grant_criteria)
**Источники:**
- Документация ФПГ: https://фондпрезидентскихгрантов.рф/
- РНФ: https://rscf.ru/
- РФФИ архив
- Ручная разметка

### 3. Методологии (research_methodologies)
**Источники:**
- Научные статьи (Google Scholar)
- Методички университетов
- Best practices (Harvard Business Review, etc.)

### 4. Бюджеты (budget_templates)
**Источники:**
- Победившие заявки (публичные)
- Шаблоны фондов
- Наш опыт

### 5. Проекты пользователей (user_projects)
**Источник:**
- PostgreSQL: `grant_applications` table
- Фильтр: все записи с content_json IS NOT NULL

---

## 🎓 RL Theory (для понимания)

### Q-Learning основы

**Q-value (качество действия):**
```
Q(state, action) = ожидаемая награда при выборе action в state
```

**Update rule:**
```
Q(s, a) ← Q(s, a) + α[r + γ·max Q(s', a') - Q(s, a)]
```

Где:
- α (alpha) = learning rate (0.1) - скорость обучения
- γ (gamma) = discount factor (0.9) - важность будущих наград
- r = immediate reward - мгновенная награда
- s' = next state - следующее состояние

### Пример для InterviewerAgent

**State:**
```python
state = {
  'answered_questions': [1, 5, 12],
  'current_topic': 'team',
  'completeness': 0.3  # 30% заполнено
}
```

**Action:**
```python
action = question_id  # ID следующего вопроса (1-50)
```

**Reward:**
```python
# После завершения интервью:
if grant_approved:
  reward = +10
elif grant_submitted:
  reward = +5
else:
  reward = -5

# Бонус от ReviewerAgent:
reward += (readiness_score - 5) * 2  # +2 за каждый балл >5
```

### Convergence (сходимость)

**Ожидаем:**
- После 50-100 интервью: Q-values стабилизируются
- Epsilon decay: 0.1 → 0.05 (меньше случайных вопросов)
- Avg questions per interview: 50 → 35-40 (оптимизация)

---

## 🚀 Deployment Plan

**Staging (тест):**
1. Создать коллекции на prod Qdrant (5.35.88.251:6333)
2. Тестировать на локальной БД
3. Проверить токены: баланс до/после

**Production (боевой):**
1. Обновить WriterAgent (использовать successful_grants)
2. Обновить ReviewerAgent (использовать grant_criteria)
3. Деплой RL InterviewerAgent (с fallback на старый)

**Rollback plan:**
- Старые агенты продолжают работать
- RL только для A/B теста (50% пользователей)

---

## 📚 References

- **GigaChat Embeddings:** https://developers.sber.ru/docs/ru/gigachat/guides/embeddings
- **Qdrant Collections:** http://5.35.88.251:6333/dashboard
- **RL Theory:** Sutton & Barto "Reinforcement Learning: An Introduction"
- **Q-Learning:** https://en.wikipedia.org/wiki/Q-learning

---

## ✅ Checklist

**Planning:**
- [x] Create iteration plan
- [ ] Collect data sources
- [ ] Design collection schemas
- [ ] Estimate token usage

**Execution:**
- [ ] Create 5 Qdrant collections
- [ ] Load successful_grants (500K)
- [ ] Load grant_criteria (500K)
- [ ] Load research_methodologies (600K)
- [ ] Load budget_templates (600K)
- [ ] Vectorize user_projects (2.5M)
- [ ] Implement RL for InterviewerAgent
- [ ] Integration tests

**Validation:**
- [ ] Test WriterAgent improvement
- [ ] Test ReviewerAgent accuracy
- [ ] Test RL convergence
- [ ] Measure token usage (должно быть ~5M)

**Documentation:**
- [ ] Update ITERATION_51_SUMMARY.md
- [ ] Create metrics dashboard
- [ ] Git commit

---

**Status:** 🚀 READY TO START
**Estimated time:** 2 days (20 hours total)
**Tokens budget:** 5,000,000
**Key deliverable:** 5 новых коллекций + RL для InterviewerAgent + метрики для Sber500
