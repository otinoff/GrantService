# Phase 4: RAG Integration Design

**Date:** 2025-10-26
**Author:** Claude Code
**Iteration:** 51 - AI Enhancement

---

## 📊 Current State Analysis

### WriterAgent Structure
**Location:** `agents/writer_agent.py`

**Current Flow:**
1. `write_application_async()` - entry point
2. `_generate_application_content_async()` - generates 10 sections sequentially:
   - title (project name)
   - summary (brief description)
   - **problem** (500-1000 words) ← **RAG TARGET #1**
   - **solution** (800-1500 words) ← **RAG TARGET #2**
   - **implementation** (1000-2000 words) ← **RAG TARGET #3**
   - **budget** (500-800 words) ← **RAG TARGET #4**
   - timeline (300-500 words)
   - team (400-600 words)
   - **impact** (600-1000 words) ← **RAG TARGET #5**
   - sustainability (400-600 words)

**Current Prompt Pattern:**
```python
problem_prompt = f"""Ты - эксперт по грантовым заявкам.

ПРОЕКТ: {project_name}
ОПИСАНИЕ: {description}

Напиши детальное описание ПРОБЛЕМЫ для грантовой заявки...
"""
```

**Key Issue:** No examples, no context from successful grants, purely generative.

---

## 🗄️ Available Qdrant Collections

### Collection 1: fpg_real_winners (42 vectors)
**Source:** 17 real FPG grant winners from web research

**Vector Structure:**
- 1 grant → 4 vectors (problem, solution, kpi, budget sections)
- Each vector has metadata: title, org, year, region, amount, category, fund_name

**Quality:** 0.81+ semantic similarity (tested)

**Use Cases:**
- Retrieve similar problem descriptions
- Retrieve solution examples
- Retrieve KPI/impact examples
- Retrieve budget breakdowns

### Collection 2: fpg_requirements_gigachat (18 vectors)
**Source:** FPG evaluation criteria, methodologies, budget templates

**Vector Structure:**
- 1 vector per requirement (not split by section like Collection 1)
- Metadata: requirement_type (criterion | methodology | budget), fund_name, category

**Quality:** 0.87 semantic similarity (tested)

**Use Cases:**
- Retrieve evaluation criteria (for quality alignment)
- Retrieve research methodologies (SMART, Logic Model, etc.)
- Retrieve budget templates (standard FPG categories)

---

## 🎯 RAG Strategy: Hybrid Approach

### Strategy Comparison

| Strategy | Pros | Cons | Decision |
|----------|------|------|----------|
| **Section-by-Section** | Highly relevant per section | 5 semantic searches (cost/latency) | ❌ Too slow |
| **Upfront (Single Query)** | Fast, 1 search | Less targeted per section | ⚠️ Good but not optimal |
| **Hybrid (Recommended)** | Best relevance + efficiency | Moderate complexity | ✅ **CHOSEN** |

### Hybrid Approach Details

**Phase 1: Upfront Retrieval (before generation)**
- Query: User's project description
- Target: `fpg_real_winners` collection
- Retrieve: Top-3 most similar grants (all 4 sections per grant)
- Purpose: General context about similar successful projects

**Phase 2: Section-Specific Retrieval (during generation)**
- Retrieve targeted examples for key sections:
  - **Problem**: Retrieve top-2 "problem" vectors from fpg_real_winners
  - **Solution**: Retrieve top-2 "solution" vectors from fpg_real_winners
  - **Implementation**: Retrieve top-2 "methodology" vectors from fpg_requirements_gigachat
  - **Budget**: Retrieve top-2 "budget" vectors (from both collections)
  - **Impact**: Retrieve top-2 "kpi" vectors from fpg_real_winners

**Total Queries:** 1 (upfront) + 5 (section-specific) = 6 semantic searches per grant

---

## 🏗️ Architecture Design

### New Module: `shared/llm/rag_retriever.py`

```python
class QdrantRAGRetriever:
    """
    RAG retriever for WriterAgent using GigaChat Embeddings + Qdrant

    Collections:
    - fpg_real_winners: Real FPG grants (problem, solution, kpi, budget)
    - fpg_requirements_gigachat: Criteria, methodologies, budget templates
    """

    def __init__(self, qdrant_client, embeddings_client):
        """Initialize with Qdrant client and GigaChat Embeddings client"""
        self.qdrant = qdrant_client
        self.embeddings = embeddings_client

    def retrieve_similar_grants(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """
        Upfront retrieval: Find top-k most similar grants

        Args:
            query_text: Project description
            top_k: Number of grants to retrieve (default: 3)

        Returns:
            List of grant metadata with all sections
        """

    def retrieve_section_examples(
        self,
        section_name: str,  # "problem" | "solution" | "kpi" | "budget"
        query_text: str,
        top_k: int = 2
    ) -> List[str]:
        """
        Section-specific retrieval from fpg_real_winners

        Args:
            section_name: Section type to retrieve
            query_text: Query for semantic search
            top_k: Number of examples (default: 2)

        Returns:
            List of text examples with metadata
        """

    def retrieve_requirements(
        self,
        requirement_type: str,  # "criterion" | "methodology" | "budget"
        query_text: str,
        top_k: int = 2
    ) -> List[str]:
        """
        Retrieve requirements/methodologies/templates

        Args:
            requirement_type: Type of requirement
            query_text: Query for semantic search
            top_k: Number of requirements (default: 2)

        Returns:
            List of requirement descriptions
        """
```

### Helper Functions

```python
def format_grant_for_prompt(grant_data: Dict) -> str:
    """
    Format retrieved grant for prompt injection

    Returns formatted string like:
    ---
    ПРИМЕР УСПЕШНОЙ ЗАЯВКИ:
    Проект: {title}
    Организация: {organization}
    Год: {year}, Сумма: {amount} руб.

    Проблема: {problem}
    Решение: {solution}
    ---
    """

def format_requirements_for_prompt(requirements: List[Dict]) -> str:
    """
    Format requirements/methodologies for prompt injection

    Returns formatted string like:
    ---
    РЕКОМЕНДУЕМЫЕ МЕТОДОЛОГИИ:
    1. SMART-цели: Specific, Measurable, Achievable, Relevant, Time-bound
       Пример: "Провести 50 мероприятий для 1000 участников до 31.12.2025"

    2. Логическая модель: Вход → Процесс → Выход → Результат → Эффект
    ---
    """
```

---

## 🔌 Integration Points in WriterAgent

### 1. Initialization (`__init__`)

```python
from shared.llm.rag_retriever import QdrantRAGRetriever

class WriterAgent:
    def __init__(self, gigachat_auth_key=None, claude_api_key=None):
        # Existing initialization...

        # NEW: Initialize RAG retriever
        try:
            from qdrant_client import QdrantClient
            from shared.llm.gigachat_embeddings_client import GigaChatEmbeddingsClient

            self.qdrant_client = QdrantClient(":memory:")  # Or production URL
            self.embeddings_client = GigaChatEmbeddingsClient()
            self.rag_retriever = QdrantRAGRetriever(
                self.qdrant_client,
                self.embeddings_client
            )
            logger.info("✅ WriterAgent: RAG retriever initialized")
        except Exception as e:
            logger.warning(f"⚠️ WriterAgent: RAG retriever disabled - {e}")
            self.rag_retriever = None
```

### 2. Modified `_generate_application_content_async()`

**Step 0: Upfront RAG Retrieval (NEW)**
```python
# NEW: Retrieve similar successful grants for general context
similar_grants = []
if self.rag_retriever:
    try:
        similar_grants = self.rag_retriever.retrieve_similar_grants(
            query_text=description,
            top_k=3
        )
        logger.info(f"✅ RAG: Retrieved {len(similar_grants)} similar grants")
    except Exception as e:
        logger.warning(f"⚠️ RAG: Failed to retrieve grants - {e}")

# Format similar grants for prompt injection
rag_context = ""
if similar_grants:
    rag_context = "\n\nПРИМЕРЫ УСПЕШНЫХ ПРОЕКТОВ:\n\n"
    for grant in similar_grants:
        rag_context += format_grant_for_prompt(grant) + "\n"
```

**Step 3: Problem Generation (MODIFIED)**
```python
# NEW: Retrieve problem examples
problem_examples = []
if self.rag_retriever:
    try:
        problem_examples = self.rag_retriever.retrieve_section_examples(
            section_name="problem",
            query_text=f"{project_name}: {description}",
            top_k=2
        )
    except Exception as e:
        logger.warning(f"⚠️ RAG: Failed to retrieve problem examples - {e}")

# MODIFIED: Enhanced prompt with RAG context
problem_prompt = f"""Ты - эксперт по грантовым заявкам.

ПРОЕКТ: {project_name}
ОПИСАНИЕ: {description}

{rag_context if similar_grants else ""}

{"ПРИМЕРЫ ОПИСАНИЯ ПРОБЛЕМЫ:" if problem_examples else ""}
{chr(10).join(f"{i+1}. {ex}" for i, ex in enumerate(problem_examples))}

Напиши детальное описание ПРОБЛЕМЫ для грантовой заявки ({int(500*word_multiplier)}-{int(1000*word_multiplier)} слов).

Опиши:
- В чём суть проблемы и её актуальность?
- Кого и как она затрагивает? (целевая аудитория, масштаб)
- Какие негативные последствия если её не решить?
- Почему существующие решения не работают?

Используй примеры выше для вдохновения, но НЕ копируй текст. Создай ОРИГИНАЛЬНОЕ описание.

Стиль: формальный, убедительный, с фактами и цифрами."""
```

**Similarly for other sections:**
- Solution: Retrieve "solution" examples
- Implementation: Retrieve "methodology" requirements
- Budget: Retrieve "budget" templates
- Impact: Retrieve "kpi" examples

---

## 📐 Prompt Engineering Strategy

### General Principles
1. **Context First**: Place RAG examples at the top of prompt
2. **Explicit Instruction**: "Используй примеры для вдохновения, но НЕ копируй"
3. **Maintain Originality**: Emphasize creating unique content
4. **Format Consistency**: Use clear separators (---, numbered lists)

### Example RAG Context Format

```
ПРИМЕРЫ УСПЕШНЫХ ПРОЕКТОВ:

---
ПРИМЕР 1: Развитие молодежного спорта в Ярославской области
Организация: Спортивный фонд Ярославия
Год: 2023, Сумма: 2,500,000 руб., Категория: Физическая культура

Проблема:
В Ярославской области наблюдается снижение физической активности среди молодежи 14-25 лет.
По данным регионального Минспорта, лишь 32% молодых людей регулярно занимаются спортом...

Решение:
Создание сети доступных спортивных площадок и организация бесплатных секций по 5 видам спорта...
---

ПРИМЕР 2: Киноклуб "Педагогика кино" в школах
Организация: Фонд развития кино
Год: 2024, Сумма: 1,800,000 руб., Категория: Культура

Проблема:
Современные школьники испытывают дефицит медиаграмотности и критического мышления при просмотре контента...
---

Теперь создай ОРИГИНАЛЬНОЕ описание проблемы для ТВОЕГО проекта, используя примеры выше как референс для структуры и стиля.
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/test_rag_retriever.py

def test_retrieve_similar_grants():
    """Test upfront retrieval of similar grants"""
    retriever = QdrantRAGRetriever(qdrant_client, embeddings_client)

    query = "Проект по развитию молодежного предпринимательства"
    grants = retriever.retrieve_similar_grants(query, top_k=3)

    assert len(grants) == 3
    assert "title" in grants[0]
    assert "problem" in grants[0]

def test_retrieve_section_examples():
    """Test section-specific retrieval"""
    retriever = QdrantRAGRetriever(qdrant_client, embeddings_client)

    examples = retriever.retrieve_section_examples(
        section_name="problem",
        query_text="Молодежная безработица",
        top_k=2
    )

    assert len(examples) == 2
    assert len(examples[0]) > 100  # Reasonable text length
```

### Integration Tests
```python
# tests/test_writer_agent_rag.py

async def test_writer_agent_with_rag():
    """Test WriterAgent generates with RAG enhancement"""
    agent = WriterAgent()

    user_answers = {
        "project_name": "Школа молодых ученых",
        "description": "Создание научного клуба для школьников",
        "budget": "1,500,000 руб."
    }

    result = await agent.write_application_async({
        "user_answers": user_answers,
        "research_data": {},
        "selected_grant": {}
    })

    assert result["status"] == "success"
    assert "ПРИМЕР" in result.get("rag_debug", "")  # Check RAG was used
```

### A/B Testing
**Compare quality with vs without RAG:**

| Metric | Without RAG | With RAG | Target |
|--------|-------------|----------|--------|
| ReviewerAgent Score | 6.5 | ? | 7.5+ |
| Problem detail (chars) | 800 | ? | 1200+ |
| Solution specificity | Generic | ? | Concrete |
| Budget structure | Basic | ? | FPG-aligned |
| KPI measurability | Weak | ? | SMART |

**Test Dataset:** 10 different project types (education, healthcare, sports, culture, etc.)

---

## 📊 Success Metrics

### Phase 4 Goals

| Metric | Current (no RAG) | Target (with RAG) | How to Measure |
|--------|------------------|-------------------|----------------|
| **Quality Score** | 6.5/10 | 7.5+/10 | ReviewerAgent scoring |
| **Problem Depth** | 800 chars | 1200+ chars | Character count |
| **Solution Specificity** | Generic | Concrete | Manual review |
| **Budget Alignment** | 60% FPG-like | 85%+ FPG-like | Template matching |
| **KPI Measurability** | 50% SMART | 80%+ SMART | SMART criteria check |
| **Generation Time** | 60s | <90s | Latency measurement |

### Quality Improvement Formula
```
Improvement = (RAG_score - Baseline_score) / Baseline_score * 100%

Target: +15% quality improvement
Acceptable: +10% improvement
Failure threshold: <5% improvement
```

---

## 🚀 Implementation Plan

### Step 1: Implement RAG Retriever ✅ (Current Task)
- [ ] Create `shared/llm/rag_retriever.py`
- [ ] Implement `QdrantRAGRetriever` class
- [ ] Implement helper functions
- [ ] Unit tests for retriever

### Step 2: Integrate into WriterAgent
- [ ] Add RAG initialization in `__init__`
- [ ] Modify `_generate_application_content_async()`
- [ ] Update prompts for 5 key sections
- [ ] Add error handling (graceful degradation)

### Step 3: Testing
- [ ] Unit tests for RAG retriever
- [ ] Integration tests for WriterAgent
- [ ] Manual testing with 5 different projects
- [ ] Quality comparison (with vs without RAG)

### Step 4: A/B Comparison
- [ ] Generate 10 grants WITHOUT RAG (baseline)
- [ ] Generate same 10 grants WITH RAG (test)
- [ ] ReviewerAgent scoring for all 20 grants
- [ ] Statistical analysis (mean, median, improvement %)

### Step 5: Documentation
- [ ] Update `STATUS.md` with Phase 4 results
- [ ] Create `RAG_RESULTS.md` with metrics
- [ ] Commit to git with detailed message

---

## 🛡️ Risk Mitigation

### Risk 1: RAG Retrieval Fails
**Mitigation:** Graceful degradation - if RAG fails, use original prompts without examples

```python
if self.rag_retriever:
    try:
        examples = self.rag_retriever.retrieve_section_examples(...)
    except Exception as e:
        logger.warning(f"⚠️ RAG failed, continuing without examples: {e}")
        examples = []
```

### Risk 2: Token Limit Exceeded
**Mitigation:** Truncate RAG context if total prompt > 12,000 chars (GigaChat limit)

```python
if len(final_prompt) > 12000:
    logger.warning(f"⚠️ Prompt too long ({len(final_prompt)} chars), truncating RAG context")
    rag_context = rag_context[:5000] + "...(truncated)"
```

### Risk 3: Quality Degradation
**Mitigation:** If A/B testing shows <5% improvement, rollback RAG integration

### Risk 4: Latency Increase
**Mitigation:** If generation time exceeds 90s, reduce top_k from 3 to 2

---

## 📝 Next Steps

1. **NOW:** Implement `rag_retriever.py` module
2. **THEN:** Integrate into WriterAgent
3. **FINALLY:** Run A/B testing and measure improvement

**Estimated Time:** 3-4 hours
**Token Budget:** 0 (inference only, no training)
**Expected Quality Gain:** +15-20%

---

**Document Status:** ✅ DESIGN COMPLETE
**Next Document:** `RAG_RESULTS.md` (after A/B testing)
