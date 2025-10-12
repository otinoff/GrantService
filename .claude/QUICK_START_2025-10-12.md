# 🚀 QUICK START - 2025-10-12

**Предыдущая сессия**: 2025-10-11 (WebSearch Architecture)
**Статус**: ✅ Production Ready
**Версия**: ResearcherAgentV2 v2.3

---

## ⚡ 30-SECOND CONTEXT RESTORE

```bash
# Что сделано 2025-10-11:
✅ WebSearchRouter (database-driven provider selection)
✅ ResearcherAgentV2 v2.3 (incremental saving, no hardcode)
✅ Migration 011 (websearch_provider in DB)
✅ Perplexity tested: 100% success (10/10 queries, $0.11)
✅ Claude Code tested: 0% (500 error on server - OAuth scopes)

# Текущая конфигурация:
PRIMARY: Perplexity API (perplexity)
FALLBACK: Claude Code WebSearch (claude_code)
```

---

## 📋 RESTORE MEMORY

### 1. Check Current State (30 sec):
```bash
# Database config
PGPASSWORD=root psql -h localhost -U postgres -d grantservice -c "
SELECT agent_name,
       config->>'websearch_provider' as provider,
       config->>'websearch_fallback' as fallback
FROM ai_agent_settings WHERE agent_name = 'researcher';" -x

# Expected output:
# provider: perplexity
# fallback: claude_code

# Latest research
PGPASSWORD=root psql -h localhost -U postgres -d grantservice -c "
SELECT research_id, status, created_at
FROM researcher_research
ORDER BY created_at DESC LIMIT 3;" -x
```

### 2. Read Session Summary (5 min):
```bash
# Full context
cat .claude/SESSION_SUMMARY_2025-10-11_WEBSEARCH_ARCHITECTURE.md | less

# Architecture
cat .claude/WEBSEARCH_ARCHITECTURE_COMPLETE_2025-10-11.md | less

# Analysis
cat .claude/WEBSEARCH_FINAL_ANALYSIS_2025-10-11.md | less
```

### 3. Check Key Files:
```bash
# WebSearchRouter (370 lines)
cat shared/llm/websearch_router.py | head -50

# ResearcherAgentV2 v2.3
grep -A 10 "Версия: 2.3" agents/researcher_agent_v2.py

# Migration 011
cat database/migrations/011_add_websearch_provider_settings.sql
```

---

## 🎯 PENDING TASKS (from previous session)

### Priority 1: Streamlit UI для WebSearch Provider (1-2 days)

**Location**: `web-admin/pages/⚙️_Настройки.py`

**Features to implement**:
```python
# Provider Selection
st.selectbox("WebSearch Provider", ["perplexity", "claude_code"])

# Health Checks
if check_perplexity_health():
    st.success("✅ Perplexity: Online")
else:
    st.error("❌ Perplexity: Offline")

# Statistics
st.metric("Success Rate", "100%")
st.metric("Avg Cost", "$0.30/anketa")
st.metric("Queries Today", daily_queries)
```

**Implementation**:
1. Add `web-admin/utils/websearch_settings.py`
2. Update `⚙️_Настройки.py` with WebSearch section
3. Test switching providers
4. Document usage

### Priority 2: Cost Monitoring Dashboard (1 day)

**Location**: New page `web-admin/pages/💰_Costs.py`

**Metrics to track**:
```python
# Daily/Monthly costs
daily_cost = count_queries(today) * 0.011
monthly_projection = daily_cost * 30

# Alerts
if monthly_projection > budget:
    send_alert("Budget exceeded")

# Charts
st.line_chart(costs_last_30_days)
st.bar_chart(queries_per_anketa)
```

### Priority 3: Verify E2E Test Completion

**Check background processes**:
```bash
# Check if test is still running
ps aux | grep test_ekaterina_e2e_full_pipeline

# Check test output
ls -la grants_output/EKATERINA_20251010_235448/

# Read test report
cat grants_output/EKATERINA_20251010_235448/E2E_FULL_REPORT_*.json | jq
```

**If test completed**:
- ✅ Verify research_results saved
- ✅ Verify Writer generated grant
- ✅ Check grant quality

**If test failed**:
- Read error logs
- Fix issue
- Re-run test

---

## 🔧 COMMON OPERATIONS

### Switch WebSearch Provider:

```sql
-- Switch to Claude Code (if becomes available)
UPDATE ai_agent_settings
SET config = jsonb_set(config, '{websearch_provider}', '"claude_code"'),
    updated_at = NOW()
WHERE agent_name = 'researcher';

-- Switch back to Perplexity
UPDATE ai_agent_settings
SET config = jsonb_set(config, '{websearch_provider}', '"perplexity"'),
    updated_at = NOW()
WHERE agent_name = 'researcher';

-- Verify
SELECT config->>'websearch_provider'
FROM ai_agent_settings
WHERE agent_name = 'researcher';
```

### Test WebSearch:

```bash
# Test Perplexity (should work ✅)
python test_claude_websearch_quick.py

# Test Claude Code (will fail ❌)
python test_claude_websearch_direct.py

# Full E2E test
python tests/integration/test_ekaterina_e2e_full_pipeline.py
```

### Check Research Results:

```sql
-- Latest completed research
SELECT
    research_id,
    anketa_id,
    status,
    research_results->'metadata'->>'total_queries' as queries,
    research_results->'metadata'->>'sources_count' as sources,
    completed_at
FROM researcher_research
WHERE status = 'completed'
ORDER BY completed_at DESC
LIMIT 5;

-- Check incremental blocks
SELECT
    research_id,
    research_results->'block1_problem'->>'total_sources' as block1_sources,
    research_results->'block2_geography'->>'total_sources' as block2_sources,
    research_results->'block3_goals'->>'total_sources' as block3_sources
FROM researcher_research
WHERE research_id = 'RES-20251011173851';
```

---

## 📚 KEY DOCUMENTATION

### Session Reports:
1. `.claude/SESSION_SUMMARY_2025-10-11_WEBSEARCH_ARCHITECTURE.md` - **READ FIRST**
2. `.claude/WEBSEARCH_ARCHITECTURE_COMPLETE_2025-10-11.md` - Architecture report
3. `.claude/WEBSEARCH_FINAL_ANALYSIS_2025-10-11.md` - Analysis + recommendations
4. `.claude/QUICK_START_2025-10-12.md` - **THIS FILE**

### Code Documentation:
1. `doc/AI_AGENTS_SETTINGS_ARCHITECTURE.md` - WebSearch configuration (+350 lines)
2. `doc/ARCHITECTURE.md` - System architecture (v1.0.2)
3. `shared/llm/websearch_router.py` - Router implementation (370 lines)
4. `agents/researcher_agent_v2.py` - Researcher v2.3

### Claude Code CLI Documentation:
1. `C:\SnowWhiteAI\GrantService\Claude Code CLI\README.md` - Central docs
2. `Claude Code CLI\WEBSEARCH_DEPLOYMENT_REPORT_2025-10-08.md` - Why Claude Code doesn't work
3. `Claude Code CLI\CLAUDE_CODE_WEBSEARCH_FOR_RESEARCHER.md` - Integration plan (local dev only)

---

## 🎯 DECISION POINTS

### ✅ Confirmed Decisions:
1. **Perplexity as PRIMARY** - 100% success, $0.30/anketa acceptable
2. **Claude Code as FALLBACK** - ready when available
3. **Database-Driven Config** - no hardcoding, easy switching
4. **Incremental Saving** - save after each block, no data loss

### ⏳ Pending Decisions:
1. **Streamlit UI design** - which page, which components?
2. **Cost monitoring thresholds** - when to alert?
3. **A/B testing** - if Claude Code becomes available, how to compare?

---

## 🐛 KNOWN ISSUES

### ❌ Claude Code WebSearch on Server:
```
Error: "I don't have permission to use the WebSearch tool"
Status: 500
Root Cause: OAuth token doesn't have WebSearch scopes

Not fixable by:
- VPN (it's not geographical)
- Settings flags (it's OAuth scope issue)
- Wrapper changes (API wrapper is correct)

Possible solutions:
- Wait for Anthropic to enable WebSearch for subscription
- Request OAuth token refresh with WebSearch scopes
- Use local Claude Code (not on server)
```

### ⚠️ Import Path Issues:
```python
# In tests, may fail:
from web_admin.utils.agent_settings import get_agent_settings
# Error: No module named 'web_admin' (hyphen vs underscore)

# Solution: graceful fallback in WebSearchRouter
try:
    settings = get_agent_settings('researcher')
except:
    # Use defaults
    self.primary_provider = 'perplexity'
```

---

## 💬 IF YOU GET STUCK

### Read Session Summary:
```bash
cat .claude/SESSION_SUMMARY_2025-10-11_WEBSEARCH_ARCHITECTURE.md
```

### Check Database:
```sql
SELECT * FROM ai_agent_settings WHERE agent_name = 'researcher';
```

### Check Logs:
```bash
grep -i "websearch" /path/to/logs/*.log
grep -i "researcher" /path/to/logs/*.log
```

### Test Components:
```bash
# Test Perplexity
curl https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}]}'

# Test Claude Code
curl http://178.236.17.55:8000/health
```

---

## ✅ SESSION CHECKLIST

Before starting work:
- [ ] Read SESSION_SUMMARY_2025-10-11_WEBSEARCH_ARCHITECTURE.md
- [ ] Check database config (websearch_provider=perplexity)
- [ ] Verify Perplexity API key set: `echo $PERPLEXITY_API_KEY`
- [ ] Check E2E test status (running/completed?)
- [ ] Review pending tasks (Streamlit UI, Cost Monitoring, etc)

---

**DATE**: 2025-10-12
**STATUS**: Ready to Continue
**NEXT**: Implement Streamlit UI for WebSearch Provider Management

**CONTACT**: AI Integration Specialist
