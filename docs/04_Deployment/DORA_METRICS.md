# DORA Metrics - GrantService

**Purpose:** Track software delivery performance
**Based on:** DevOps Research and Assessment (DORA)
**Status:** Tracking started 2025-10-25 (Iteration 36)

---

## 📊 THE 4 KEY METRICS

### 1. Deployment Frequency
**Definition:** How often we deploy to production
**Target:** ≥1 deploy per week
**Elite:** Multiple deploys per day

**Current:** Track below ↓

### 2. Lead Time for Changes
**Definition:** Time from commit to production
**Target:** <1 day
**Elite:** <1 hour

**Current:** Measure: commit timestamp → deploy timestamp

### 3. Change Failure Rate
**Definition:** % of deployments causing failures
**Target:** <15%
**Elite:** <5%

**Current:** Failed deploys / Total deploys

### 4. Time to Restore Service (MTTR)
**Definition:** Time to recover from failure
**Target:** <1 hour
**Elite:** <1 hour

**Current:** Bug reported → fix deployed

---

## 📋 DEPLOYMENT LOG

Log each deployment here:

| Date | Iteration | Commit | Success | Duration | MTTR | Notes |
|------|-----------|--------|---------|----------|------|-------|
| 2025-10-25 | 35 | abc123 | ✅ | - | - | Anketa Management + GigaChat switch |
| 2025-10-25 | 36 | def456 | ⏳ | - | - | Methodology Cleanup (in progress) |

**Template:**
```
| YYYY-MM-DD | XX | hash | ✅/❌ | Xh Xm | Xm | Description |
```

---

## 📈 METRICS CALCULATION

### Deployment Frequency
```
Count deployments in last 7 days / 7 = X per day
Count deployments in last 30 days / 30 = X per day
```

**Current (as of 2025-10-25):**
- Last 7 days: 1 deploy → 0.14 per day ⚠️ (below target)
- Last 30 days: [calculate]

**Target:** ≥0.14 per day (1 per week)

### Lead Time
```
Average(deploy_time - commit_time) for last 10 deploys
```

**Current:**
- Iteration 35: [track]
- Iteration 36: [track]

**Target:** <24 hours

### Change Failure Rate
```
Failed deploys / Total deploys * 100%
```

**Current:**
- Total deploys: 1
- Failed: 0
- **Rate: 0%** ✅ (excellent!)

**Target:** <15%

### MTTR
```
Average(fix_deployed_time - bug_reported_time) for last 10 incidents
```

**Current:**
- No incidents yet

**Target:** <60 minutes

---

## 🎯 IMPROVEMENT GOALS

### Short-term (1 month):
- [ ] Deploy frequency: 1 per week minimum
- [ ] Lead time: <24 hours
- [ ] Maintain 0% failure rate
- [ ] Setup automated MTTR tracking

### Medium-term (3 months):
- [ ] Deploy frequency: 2-3 per week
- [ ] Lead time: <12 hours
- [ ] Failure rate: <10%
- [ ] MTTR: <30 minutes

### Long-term (6 months):
- [ ] Deploy frequency: Daily
- [ ] Lead time: <4 hours
- [ ] Failure rate: <5%
- [ ] MTTR: <15 minutes (automated rollback)

---

## 🔄 REVIEW SCHEDULE

**Daily:** Quick check - any deployments today?
**Weekly:** Calculate all 4 metrics
**Monthly:** Trend analysis, improvement plan

---

## 📊 VISUALIZATION (Future)

Create dashboard with:
- Line charts for each metric over time
- Target lines
- Trend indicators (↗️ improving, ↘️ degrading)

**Tools to consider:**
- Grafana
- Streamlit dashboard
- Simple Python script + matplotlib

---

## 🚀 AUTOMATION IDEAS

### Automated Deployment Log:
```python
# In deployment script
log_deployment(
    iteration=36,
    commit=git_commit_hash(),
    timestamp=now(),
    status='success' | 'failed'
)
```

### Automated MTTR Tracking:
```python
# When bug reported
bug_id = create_incident(description)

# When fix deployed
close_incident(bug_id, fix_commit_hash)
# Automatically calculate MTTR
```

---

**Created:** 2025-10-25 (Iteration 36)
**Last Updated:** 2025-10-25
**Next Review:** 2025-11-01
