# Iteration 39: RL Optimization & Production Corpus

**Date:** 2025-10-25
**Status:** 🚀 PLANNED
**Iteration:** 39 - RL Optimization

---

## 🎯 OBJECTIVE

**Goal:** Generate production corpus (100 anketas), collect audit data, analyze correlations, and optimize generator parameters using RL principles.

**Success Criteria:**
- ✅ 100 synthetic anketas generated
- ✅ 100 anketas audited (collect reward signals)
- ✅ Correlation analysis complete (quality_level, region, topic → score)
- ✅ Grid search for temperature optimization
- ✅ Updated generator with optimal parameters

---

## 📊 PHASES

### Phase 1: Production Generation (100 Anketas)
**Duration:** ~15-20 minutes
**Token Cost:** ~150,000 tokens (GigaChat Lite)

**Distribution:**
- Low quality: 20 anketas (20%)
- Medium quality: 50 anketas (50%)
- High quality: 30 anketas (30%)

**Regions:** Random from 12 regions (Moscow, St.Petersburg, Kemerovo, etc.)
**Topics:** Random from 10 topics (youth, culture, education, etc.)

**Command:**
```bash
# Via Telegram bot:
/generate_synthetic_anketa 100

# Or Python script:
python -c "
from agents.anketa_synthetic_generator import AnketaSyntheticGenerator
# ... generate 100 anketas
"
```

---

### Phase 2: Batch Audit (100 Anketas)
**Duration:** ~30-40 minutes
**Token Cost:** ~200,000 tokens (GigaChat Max)

**Collect Data:**
- `average_score` (0-10) ← PRIMARY REWARD SIGNAL
- `approval_status` ('approved', 'needs_revision', 'rejected')
- Individual scores: relevance, clarity, feasibility, impact, budget

**Command:**
```bash
# Via Telegram bot:
/batch_audit_anketas 100
```

---

### Phase 3: Data Analysis & Correlations
**Duration:** ~30 minutes

**Analyze:**
1. **Quality Level Impact:**
   - Average score for `quality='low'`: ?
   - Average score for `quality='medium'`: ?
   - Average score for `quality='high'`: ?

2. **Region Impact:**
   - Best performing region: ?
   - Worst performing region: ?
   - Correlation: region → score

3. **Topic Impact:**
   - Best performing topic: ?
   - Worst performing topic: ?
   - Correlation: topic → score

4. **Temperature Impact:**
   - Current: temperature = 0.8
   - Hypothesis: Lower temperature → higher quality scores?
   - Need grid search to verify

**SQL Queries:**
```sql
-- Average score by quality level
SELECT
    s.interview_data->>'quality_target' as quality,
    AVG(ar.average_score) as avg_score,
    COUNT(*) as count
FROM sessions s
JOIN auditor_results ar ON s.id = ar.session_id
WHERE s.interview_data->>'synthetic' = 'true'
GROUP BY s.interview_data->>'quality_target'
ORDER BY avg_score DESC;

-- Average score by region
SELECT
    s.interview_data->>'region' as region,
    AVG(ar.average_score) as avg_score,
    COUNT(*) as count
FROM sessions s
JOIN auditor_results ar ON s.id = ar.session_id
WHERE s.interview_data->>'synthetic' = 'true'
GROUP BY s.interview_data->>'region'
ORDER BY avg_score DESC;

-- Average score by topic
-- (Similar query for topic analysis)
```

---

### Phase 4: Grid Search (Temperature Optimization)
**Duration:** ~1-2 hours
**Token Cost:** ~50,000 tokens (testing)

**Hypothesis:**
- Current: `temperature = 0.8`
- Grid: `[0.3, 0.5, 0.7, 0.9, 1.1]`
- Quality levels: `['low', 'medium', 'high']`

**Experiment:**
For each combination:
1. Generate 5 anketas with `(temperature, quality_level)`
2. Audit all 5
3. Record average score
4. Find optimal temperature per quality level

**Expected Result:**
```python
optimal_params = {
    'low': {'temperature': 0.7, 'avg_score': 6.5},
    'medium': {'temperature': 0.5, 'avg_score': 7.8},
    'high': {'temperature': 0.3, 'avg_score': 8.9}
}
```

---

### Phase 5: Update Generator
**Duration:** 10 minutes

**Update `AnketaSyntheticGenerator.__init__()`:**
```python
# Before:
self.llm = UnifiedLLMClient(
    provider='gigachat',
    model=self.llm_model,
    temperature=0.8  # Fixed
)

# After:
OPTIMAL_TEMPERATURES = {
    'low': 0.7,
    'medium': 0.5,
    'high': 0.3
}

temperature = OPTIMAL_TEMPERATURES.get(quality_level, 0.8)

self.llm = UnifiedLLMClient(
    provider='gigachat',
    model=self.llm_model,
    temperature=temperature  # Dynamic!
)
```

---

## 📈 TOKEN BUDGET

| Phase | Model | Tokens | Cost (approx) |
|-------|-------|--------|---------------|
| Phase 1: Generation (100) | GigaChat Lite | ~150,000 | ~15 руб |
| Phase 2: Audit (100) | GigaChat Max | ~200,000 | ~200 руб |
| Phase 4: Grid Search (75) | GigaChat Lite + Max | ~50,000 | ~50 руб |
| **TOTAL** | | **~400,000** | **~265 руб** |

**Excellent for Sber500 demonstration!**

---

## 📁 FILES TO CREATE

1. **`analysis_iteration_39.py`** - Data analysis script
2. **`grid_search_temperature.py`** - Grid search experiment
3. **`01_PRODUCTION_RUN.md`** - Production generation log
4. **`02_AUDIT_RESULTS.md`** - Audit results summary
5. **`03_CORRELATION_ANALYSIS.md`** - Analysis findings
6. **`04_GRID_SEARCH_RESULTS.md`** - Temperature optimization results
7. **`05_SUMMARY.md`** - Final iteration summary

---

## 🔬 RL FOUNDATIONS (Future Iterations)

This iteration establishes **data collection** for RL:

**Current Status:**
- ✅ Reward signal: `average_score`
- ✅ State: `(quality_level, region, topic)`
- ✅ Action: `(temperature, max_tokens, prompt_variant)`

**Future Iterations (40+):**
- Iteration 40: Implement Policy Gradient (REINFORCE)
- Iteration 41: Multi-armed Bandit for prompt selection
- Iteration 42: PPO for fine-tuning generation strategy

---

## 📝 TESTING PLAN

**Before Production Run:**
1. ✅ Iteration 38 tests passed (6/6)
2. ✅ Git commit created
3. ✅ System stable

**During Production:**
1. Monitor generation progress (log every 10 anketas)
2. Check for JSON truncation errors (retry should handle)
3. Verify database writes

**After Audit:**
1. Verify all 100 anketas audited
2. Check average score distribution
3. No major outliers (score < 3.0 or > 9.5)

---

## 🎯 SUCCESS METRICS

**Generation:**
- ✅ 100 anketas generated successfully
- ✅ < 5% JSON truncation errors (handled by retry)
- ✅ All saved to database

**Audit:**
- ✅ 100 anketas audited
- ✅ Average score: 6.5-8.5 (realistic)
- ✅ Distribution: 60% approved, 30% needs_revision, 10% rejected

**Analysis:**
- ✅ Clear correlation: quality_level → score
- ✅ Identified best/worst regions
- ✅ Identified best/worst topics

**Optimization:**
- ✅ Optimal temperature found per quality_level
- ✅ Score improvement: +0.5-1.0 after optimization

---

## 🚀 NEXT STEPS (Iteration 40)

**After Iteration 39:**
1. Implement dynamic temperature selection
2. Add prompt variant selection
3. Implement simple Gradient Bandit for exploration/exploitation
4. A/B testing: old vs optimized generator

---

**Created:** 2025-10-25
**Status:** PLANNED
**Ready to Execute:** ✅ YES

---

## 📌 QUICK START

```bash
# 1. Generate 100 anketas
/generate_synthetic_anketa 100

# 2. Audit 100 anketas
/batch_audit_anketas 100

# 3. Run analysis
python analysis_iteration_39.py

# 4. Grid search
python grid_search_temperature.py

# 5. Review results
cat 05_SUMMARY.md
```

**Estimated Time:** 2-3 hours total
**Token Usage:** ~400K tokens
**Cost:** ~265 руб

**LET'S GO! 🚀**
