# Iteration 1001: RAG Full Integration (FUTURE PLAN)

**Status:** 📅 PLANNED (not started)
**Priority:** MEDIUM
**Prerequisites:** Iteration 51 complete ✅
**Estimated Time:** 4-6 hours
**Assigned To:** TBD

---

## 🎯 Goal

Extend RAG (Retrieval Augmented Generation) to **all 10 sections** of WriterAgent, validate quality improvement through A/B testing.

**Current State (from Iteration 51):**
- ✅ RAG integrated for **problem section** only (proof of concept)
- ✅ RAG retriever module complete (3 retrieval methods)
- ✅ 60 high-quality vectors (42 grants + 18 requirements)

**Target State:**
- ✅ RAG integrated for **all 10 sections**
- ✅ A/B tested (10 projects with/without RAG)
- ✅ Measured quality improvement (ReviewerAgent scores)
- ✅ Production-ready persistent Qdrant

---

## 📊 Scope

### In Scope ✅
1. Extend RAG to 9 remaining sections:
   - solution (решение) - use solution examples
   - implementation (план реализации) - use methodologies
   - budget (бюджет) - use budget templates
   - timeline (временные рамки) - use implementation plans
   - team (команда проекта) - use team examples
   - impact (ожидаемый эффект) - use KPI examples
   - sustainability (устойчивость) - use impact examples
   - summary (краткое описание) - use all context
   - title (название) - use title examples

2. Setup persistent Qdrant (production-ready)
3. A/B testing framework
4. Quality measurement (ReviewerAgent integration)
5. Documentation + metrics

### Out of Scope ❌
- New embeddings collections (use existing 60 vectors)
- RL training (deferred to Iteration 1003)
- UI changes
- Database schema changes

---

## 📋 Tasks Breakdown

### Phase 1: Setup Persistent Qdrant (1 hour)
**Goal:** Switch from in-memory to persistent Qdrant

**Tasks:**
- [ ] Start Qdrant with Docker: `docker run -p 6333:6333 qdrant/qdrant`
- [ ] Update `writer_agent.py` to use `localhost:6333`
- [ ] Load collections: `load_fpg_to_qdrant.py` + `load_fpg_requirements_to_qdrant.py`
- [ ] Verify collections: 42 + 18 = 60 vectors
- [ ] Test semantic search (smoke test)

**Acceptance Criteria:**
- ✅ Qdrant running on localhost:6333
- ✅ Both collections loaded and searchable
- ✅ WriterAgent connects successfully

---

### Phase 2: Extend RAG to Solution Section (30 min)
**Goal:** Add RAG retrieval for solution generation

**Implementation:**
```python
# In _generate_application_content_async(), after problem generation:

# Get solution examples
solution_examples = []
if self.rag_retriever:
    solution_examples = self.rag_retriever.retrieve_section_examples(
        section_name="solution",
        query_text=f"{project_name}: {content['problem'][:500]}",
        top_k=2
    )

# Enhance solution prompt
solution_prompt = f"""...
{format_section_examples_for_prompt("solution", solution_examples)}

Напиши детальное описание РЕШЕНИЯ...
Используй примеры выше для вдохновения, но создай ОРИГИНАЛЬНОЕ решение.
"""
```

**Acceptance Criteria:**
- ✅ Solution generation uses RAG examples
- ✅ Prompt includes 2 solution examples
- ✅ Quality improves (manual check)

---

### Phase 3: Extend RAG to Implementation Section (30 min)
**Goal:** Add RAG retrieval for implementation (use methodologies)

**Implementation:**
```python
# Get methodology recommendations
methodologies = []
if self.rag_retriever:
    methodologies = self.rag_retriever.retrieve_requirements(
        requirement_type="methodology",
        query_text=f"План реализации проекта: {project_name}",
        top_k=2
    )

# Enhance implementation prompt with methodologies
```

**Acceptance Criteria:**
- ✅ Implementation uses methodologies (SMART, Logic Model)
- ✅ Prompt structured with research methods

---

### Phase 4: Extend RAG to Budget Section (30 min)
**Goal:** Add RAG retrieval for budget (use templates)

**Implementation:**
```python
# Get budget templates
budget_templates = []
if self.rag_retriever:
    budget_templates = self.rag_retriever.retrieve_requirements(
        requirement_type="budget",
        query_text=f"Бюджет проекта: {budget_amount}",
        top_k=2
    )

# Enhance budget prompt with standard FPG categories
```

**Acceptance Criteria:**
- ✅ Budget follows FPG structure
- ✅ All standard categories included

---

### Phase 5: Extend RAG to Impact Section (30 min)
**Goal:** Add RAG retrieval for impact (use KPI examples)

**Implementation:**
```python
# Get KPI examples
kpi_examples = []
if self.rag_retriever:
    kpi_examples = self.rag_retriever.retrieve_section_examples(
        section_name="kpi",
        query_text=f"Результаты проекта: {project_name}",
        top_k=2
    )

# Enhance impact prompt with measurable KPIs
```

**Acceptance Criteria:**
- ✅ Impact includes SMART KPIs
- ✅ Measurable results specified

---

### Phase 6: Extend RAG to Remaining 5 Sections (1 hour)
**Goal:** Add RAG to timeline, team, sustainability, summary, title

**Tasks:**
- [ ] Timeline - use implementation examples
- [ ] Team - use team structure examples
- [ ] Sustainability - use impact examples
- [ ] Summary - use all grant context
- [ ] Title - use title examples

**Acceptance Criteria:**
- ✅ All 10 sections use RAG
- ✅ No section left without examples

---

### Phase 7: A/B Testing Framework (1 hour)
**Goal:** Create framework to test with/without RAG

**Test Projects (10):**
1. Молодежное предпринимательство
2. Образовательная программа для школьников
3. Культурный центр для малых городов
4. Спортивная инфраструктура
5. Экологический проект (озеленение)
6. Социальная помощь пожилым
7. IT-образование для детей
8. Музейная выставка
9. Благоустройство дворов
10. Волонтерская программа

**Implementation:**
```python
# scripts/test_rag_ab.py

async def test_with_rag(project):
    agent = WriterAgent(db, rag_enabled=True)
    return await agent.write_application_async(project)

async def test_without_rag(project):
    agent = WriterAgent(db, rag_enabled=False)
    return await agent.write_application_async(project)

# Run A/B test for 10 projects
results = []
for project in test_projects:
    with_rag = await test_with_rag(project)
    without_rag = await test_without_rag(project)
    results.append({
        "project": project["name"],
        "with_rag": with_rag,
        "without_rag": without_rag
    })
```

**Acceptance Criteria:**
- ✅ 10 projects tested
- ✅ 20 applications generated (10 with RAG + 10 without)
- ✅ Results saved for analysis

---

### Phase 8: Quality Measurement (1 hour)
**Goal:** Measure quality improvement using ReviewerAgent

**Metrics:**
1. **ReviewerAgent Score** (0-10)
2. **Problem Detail** (char count)
3. **Solution Specificity** (manual review)
4. **Budget Structure** (FPG alignment %)
5. **KPI Measurability** (SMART criteria %)

**Implementation:**
```python
from agents.reviewer_agent import ReviewerAgent

reviewer = ReviewerAgent(db)

for result in results:
    # Score with RAG
    score_with = await reviewer.review_application_async(
        result["with_rag"]["application_content"]
    )

    # Score without RAG
    score_without = await reviewer.review_application_async(
        result["without_rag"]["application_content"]
    )

    result["scores"] = {
        "with_rag": score_with["score"],
        "without_rag": score_without["score"],
        "improvement": score_with["score"] - score_without["score"]
    }
```

**Acceptance Criteria:**
- ✅ All 20 applications scored
- ✅ Average improvement calculated
- ✅ Statistical significance checked (if sample size allows)

---

### Phase 9: Documentation (30 min)
**Goal:** Document results and production deployment

**Documents:**
- [ ] A/B Testing Results (`AB_TEST_RESULTS.md`)
- [ ] Quality Metrics Report (`QUALITY_METRICS.md`)
- [ ] Production Deployment Guide (update)
- [ ] Iteration 1001 Summary

**Acceptance Criteria:**
- ✅ All results documented
- ✅ Improvement % calculated
- ✅ Recommendations provided

---

## 📊 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Quality Improvement** | +15% | ReviewerAgent score diff |
| **Problem Detail** | +20% chars | Character count comparison |
| **Solution Specificity** | 80% concrete | Manual review (5-point scale) |
| **Budget Alignment** | 85% FPG-like | Template matching |
| **KPI Measurability** | 80% SMART | SMART criteria checklist |
| **Generation Time** | <90s | Latency measurement |

**Minimum Viable Success:** +10% quality improvement (ReviewerAgent score)

---

## 🚀 Deployment Plan

### Prerequisites
- ✅ Iteration 51 complete
- ✅ Docker installed (for Qdrant)
- ✅ GigaChat API access
- ✅ PostgreSQL running

### Steps
1. Start persistent Qdrant
2. Load collections (one-time)
3. Deploy updated WriterAgent
4. Monitor RAG retrieval logs
5. Collect metrics for 1 week

### Rollback Plan
- Keep old WriterAgent code as backup
- Flag to disable RAG: `rag_enabled=False`
- Revert to Iteration 51 state if quality degrades

---

## 🐛 Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Quality doesn't improve | HIGH | Keep RAG optional, A/B test first |
| Latency increases | MEDIUM | Cache retrieved examples |
| Qdrant downtime | MEDIUM | Graceful degradation (works without RAG) |
| Token costs increase | LOW | RAG uses minimal tokens (retrieval only) |

---

## 📝 Notes

- **Why not Phase 5 (RL)?** RL requires more time (8-10 hours) and should be separate iteration
- **Why 10 test projects?** Statistically significant sample (minimum 10 for t-test)
- **Why persistent Qdrant?** In-memory requires reload, not production-ready
- **Why all sections?** Proof of concept validated, time to go full integration

---

## 🔗 Related Iterations

- **Iteration 51:** AI Enhancement (RAG proof of concept) ✅ COMPLETE
- **Iteration 1003:** RL Training (optional, future)
- **Iteration 1002:** E2E Tests Complete (higher priority)

---

## ✅ Definition of Done

- [ ] RAG integrated for all 10 sections
- [ ] Persistent Qdrant setup and running
- [ ] 10 projects A/B tested
- [ ] Quality improvement measured (+10% minimum)
- [ ] Results documented
- [ ] Production deployed
- [ ] Metrics tracked for 1 week
- [ ] Code reviewed
- [ ] Git committed

---

**When to Start:** After Iteration 1002 (E2E Tests) or when WriterAgent quality is priority

**Owner:** TBD
**Status:** 📅 PLANNED
