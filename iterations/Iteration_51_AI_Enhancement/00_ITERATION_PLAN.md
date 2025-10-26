# Iteration 51: AI Enhancement - Embeddings + RL

**Дата начала:** 2025-10-26
**Дата завершения Phase 1:** 2025-10-26
**Статус:** ✅ PHASE 1 COMPLETE
**Цель:** Потратить 3 млн токенов GigaChat Embeddings на создание 3 оптимизированных коллекций + добавить RL для InterviewerAgent

---

## 🎯 Задача

**Бизнес-цель:** Показать на оценке Sber500 серьёзный AI-прогресс за 2 дня

**Технические цели:**
1. Создать 3 ОПТИМИЗИРОВАННЫХ Qdrant коллекции с GigaChat Embeddings (1024-dim)
2. Потратить 3 млн токенов embeddings + 2 млн резерв на fine-tuning
3. Использовать РЕАЛЬНЫЕ данные из веба (Perplexity, Parallel AI)
4. Добавить базовый RL для InterviewerAgent
5. Измерить улучшение качества (до/после)

---

## 📊 Бюджет токенов (5 млн total)

| Коллекция | Источник | Tokens | % бюджета | Status |
|-----------|----------|--------|-----------|--------|
| **fpg_real_winners** | Web scraping (Perplexity/Parallel AI) | 1,200,000 | 24% | ✅ DONE (1.6K used) |
| **fpg_requirements_gigachat** | БД + Web (критерии + методологии + бюджеты) | 1,000,000 | 20% | 🔥 NEW |
| **user_grants_all** | PostgreSQL grant_applications (174 гранта) | 800,000 | 16% | 🔥 NEW |
| **Резерв на fine-tuning** | - | 2,000,000 | 40% | 💎 RESERVED |
| **TOTAL** | - | **5,000,000** | **100%** | ✅ |

**Ключевое изменение:** user_grants_approved (наши тестовые 29 грантов) НЕ используем для обучения! Вместо них - РЕАЛЬНЫЕ победители из веба через web search.

---

## 📁 Структура коллекций (3 оптимизированных)

### 1. `fpg_real_winners` (1.2M tokens) 🔥 NEW

**Источник:** РЕАЛЬНЫЕ победители ФПГ 2020-2024 из веба

**Метод сбора данных:**
1. **Perplexity AI промты:**
   ```
   "Найди список победителей Фонда президентских грантов 2024 года в категории 'Социальное обслуживание'.
   Для каждого проекта укажи: название, организация, регион, сумма гранта, описание проблемы, предлагаемое решение."
   ```

2. **Parallel AI промты:**
   ```
   "Проанализируй победившие грантовые заявки ФПГ в категории 'Образование' за 2023 год.
   Извлеки ключевые характеристики: целевая аудитория, социальная значимость, измеримые результаты."
   ```

3. **Ручной анализ:** 50-100 реальных заявок победителей

**Что храним:**
- `title` - название проекта
- `organization` - организация-победитель
- `problem` - описание проблемы (300-500 слов)
- `solution` - решение (500-1000 слов)
- `target_audience` - целевая аудитория
- `social_impact` - социальная значимость
- `kpi` - измеримые результаты
- `budget` - бюджет и статьи расходов
- `fund_name` - ФПГ/РНФ/РФФИ
- `year` - год победы
- `region` - регион
- `amount` - сумма гранта
- `category` - категория конкурса
- `rating_score` - экспертная оценка (если доступна)

**Embedding strategy:**
- Каждый раздел отдельно: problem, solution, kpi, budget
- Метаданные в payload: fund, year, region, category, amount
- GigaChat Embeddings API (1024-dim)

**Использование:**
- **WriterAgent:** Поиск похожих успешных проектов для вдохновения
- **RL Training:** Положительные примеры (approved = +10 reward)
- **ReviewerAgent:** Сравнение с winning patterns

**Token budget:** ~1,200,000 tokens (100 грантов × ~12,000 tokens/грант)

---

### 2. `fpg_requirements_gigachat` (1M tokens) 🔥 NEW

**Источник:** КОНСОЛИДАЦИЯ 3 типов данных:
1. Критерии оценки фондов (grant_criteria)
2. Методологии исследования (research_methodologies)
3. Бюджетные шаблоны (budget_templates)

**Метод сбора:**
1. **Из PostgreSQL:** 17 существующих knowledge_sections
2. **Web scraping:** Официальные сайты ФПГ, РНФ, РФФИ
3. **Perplexity/Parallel AI:** "Критерии оценки грантовых заявок ФПГ 2024"

**Что храним:**

**A. Критерии оценки (40%):**
- `fund_name` - ФПГ/РНФ/РФФИ
- `criterion_name` - название критерия
- `criterion_description` - описание
- `weight` - вес в оценке (0-100%)
- `requirements` - конкретные требования
- `examples` - примеры соответствия

**B. Методологии (30%):**
- `methodology_name` - SMART, Agile, Design Thinking
- `description` - описание
- `application_area` - область применения
- `kpi_examples` - примеры KPI
- `smart_goals_examples` - примеры SMART-целей

**C. Бюджетные шаблоны (30%):**
- `fund_name` - фонд
- `project_type` - тип проекта
- `budget_categories` - категории расходов
- `justification` - обоснование
- `total_amount` - общая сумма
- `duration_months` - длительность

**Embedding strategy:**
- Каждый тип данных (критерии, методологии, бюджеты) с отдельными metadata tags
- GigaChat Embeddings API (1024-dim)
- Hierarchical chunking: раздел → подраздел → параграф

**Использование:**
- **ReviewerAgent:** Адаптивная оценка под конкретный фонд
- **AuditorAgent:** Проверка соответствия требованиям
- **WriterAgent:** Раздел "Бюджет" + методология

**Token budget:** ~1,000,000 tokens (200 документов × ~5,000 tokens/doc)

---

### 3. `user_grants_all` (800K tokens) 🔥 NEW

**Источник:** Готовые заявки из PostgreSQL grant_applications (174 гранта)

**Метод извлечения:**
```sql
-- Все гранты (draft + approved)
SELECT id, title, content_json, status, quality_score, created_at, updated_at
FROM grant_applications
WHERE content_json IS NOT NULL
ORDER BY created_at DESC;
```

**Что векторизуем:**
- **174 гранта total:**
  - 145 draft (черновики)
  - 29 approved (одобренные)
- **10 разделов каждой заявки:**
  - problem (проблема)
  - solution (решение)
  - target_audience (целевая аудитория)
  - goals (цели)
  - methodology (методология)
  - timeline (план реализации)
  - budget (бюджет)
  - team (команда)
  - risks (риски)
  - impact (ожидаемые результаты)

**Метаданные (payload):**
- `status` - draft/approved/submitted
- `quality_score` - оценка ReviewerAgent (0-10)
- `created_at` - дата создания
- `user_id` - ID пользователя
- `fund_target` - целевой фонд

**Embedding strategy:**
- Каждый раздел отдельно (10 vectors per grant × 174 grants = 1,740 vectors)
- GigaChat Embeddings API (1024-dim)
- Metadata-based filtering для similarity search

**Использование:**
- **WriterAgent:** Поиск похожих проектов пользователей
- **Рекомендации:** "Похожие проекты в нашей базе"
- **RL Training:**
  - approved grants (29) = положительные примеры (+5 reward)
  - draft grants (145) = примеры для обучения (neutral)
- **Персонализация:** Учет истории пользователя

**Token budget:** ~800,000 tokens (174 grants × 10 sections × ~460 tokens/section)

**Отличие от fpg_real_winners:**
- `fpg_real_winners` = РЕАЛЬНЫЕ победители из веба (эталон качества)
- `user_grants_all` = НАШИ пользователи (история системы, персонализация)

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

### День 1 (26 октября, сегодня) - Data Collection

**Commit #1: Iteration plan + schemas (СЕЙЧАС, 1 час)**
```bash
git commit -m "feat(iteration-51): Plan + 3 collection schemas (3M tokens + 2M reserve)"
```
- ✅ Update iteration plan (3 коллекции вместо 5)
- Create Pydantic models для 3 коллекций
- Create Qdrant collection schemas (JSON)
- **Test:** Schema validation
- **CI:** Lint + type check
- **Lines:** ~150 lines

**Commit #2: Web search промты + parsers (день, 3 часа)**
```bash
git commit -m "feat(iteration-51): Perplexity/Parallel AI prompts + FPG parsers"
```
- **Perplexity AI промты** для fpg_real_winners:
  - "Победители ФПГ 2024: Социальное обслуживание"
  - "Победители ФПГ 2023: Образование"
  - "Победители ФПГ 2024: Культура"
- **Parallel AI промты** для анализа заявок
- Create FPG web parser (BeautifulSoup)
- Unit tests: `test_web_parsers.py`
- **Test:** Mock HTML fixtures
- **CI:** All unit tests pass
- **Lines:** ~180 lines

**Commit #3: GigaChat embeddings loader (вечер, 2 часа)**
```bash
git commit -m "feat(iteration-51): GigaChat Embeddings API client + loader"
```
- Create `shared/llm/gigachat_embeddings.py`
- GigaChat Embeddings API client (1024-dim)
- Batch processing (100 texts per batch)
- Integration test: `test_gigachat_embeddings_client.py`
- **Test:** Create 10 test embeddings
- **Metrics:** Test token usage (~5K tokens)
- **Lines:** ~120 lines

**Commit #4: Load fpg_real_winners (вечер, 3 часа)**
```bash
git commit -m "feat(iteration-51): Load 100 real FPG winners (1.2M tokens)"
```
- Process Perplexity/Parallel AI результаты
- Parse 100 real grant applications
- Create Qdrant collection `fpg_real_winners`
- Load embeddings (1.2M tokens)
- **Test:** `test_fpg_real_winners_collection.py`
- **Metrics:** 1.2M / 3M tokens used (40%)
- **Lines:** ~150 lines

### День 2 (27 октября) - Vectorization + Integration

**Commit #5: Load fpg_requirements_gigachat (утро, 2 часа)**
```bash
git commit -m "feat(iteration-51): Consolidate criteria + methodologies + budgets (1M tokens)"
```
- Consolidate 3 типа данных:
  - A. Критерии оценки (40%)
  - B. Методологии (30%)
  - C. Бюджетные шаблоны (30%)
- Create Qdrant collection `fpg_requirements_gigachat`
- Load embeddings (1M tokens)
- **Test:** `test_fpg_requirements_collection.py`
- **Metrics:** 2.2M / 3M tokens used (73%)
- **Lines:** ~120 lines

**Commit #6: Load user_grants_all (день, 2 часа)**
```bash
git commit -m "feat(iteration-51): Vectorize 174 user grants (800K tokens)"
```
- Query PostgreSQL grant_applications (174 total)
- Vectorize 10 sections × 174 grants = 1,740 vectors
- Create Qdrant collection `user_grants_all`
- Load embeddings (800K tokens)
- **Test:** `test_user_grants_collection.py`
- **Metrics:** 3M / 3M tokens used (100%) + 2M reserve
- **Lines:** ~100 lines

**Commit #7: WriterAgent integration (день, 3 часа)**
```bash
git commit -m "feat(iteration-51): Integrate fpg_real_winners + fpg_requirements in WriterAgent"
```
- Add semantic search в WriterAgent:
  - Query `fpg_real_winners` для похожих успешных проектов
  - Query `fpg_requirements_gigachat` для критериев/методологий
  - Query `user_grants_all` для персонализации
- Integration test: `test_writer_with_embeddings.py`
- **Test:** Compare quality (Iteration 50 baseline)
- **Expected:** +1 point minimum в ReviewerAgent score
- **Lines:** ~150 lines

**Commit #8: RL for InterviewerAgent (вечер, 3 часа)**
```bash
git commit -m "feat(iteration-51): Q-learning for InterviewerAgent (optional)"
```
- Create `agents/rl_interviewer_agent.py`
- Q-table storage в PostgreSQL (table: rl_q_values)
- Epsilon-greedy policy (ε=0.1)
- **Test:** `test_rl_q_learning.py` (unit test)
- **Metrics:** Q-table size, convergence
- **Lines:** ~120 lines
- **Note:** ⚠️ OPTIONAL - if time allows

**Commit #9: Documentation + SUMMARY (вечер, 2 часа)**
```bash
git commit -m "docs(iteration-51): Summary + Sber500 presentation metrics"
```
- Create ITERATION_51_SUMMARY.md
- Export metrics:
  - Token usage: 3M / 5M (60%)
  - Collections created: 3
  - Vectors total: ~2,840 (100 + 200 + 1,740)
  - Quality improvement: baseline vs embeddings
- Final deliverable for Sber500
- **Lines:** ~200 lines (markdown)

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
