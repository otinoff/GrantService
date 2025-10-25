# Pre-Deploy Checklist - Deploy #5 (Iteration 26)

**Date:** 2025-10-23
**Deploy:** Iteration 26 - Hardcoded Question #2
**Status:** 🔄 IN PROGRESS

---

## Code & Tests ✅

### Unit Tests:
- [x] All unit tests passed locally
- [x] No failing tests in test suite
- [x] Test coverage maintained

### Integration Tests:
- [x] Integration tests passed (6/6 = 100%)
  - [x] test_basic_interview
  - [x] test_hardcoded_question
  - [x] test_callback_with_none
  - [x] test_reference_points_completion
  - [x] test_audit_score_generation
  - [x] test_no_duplicate_questions

### E2E Tests:
- [x] E2E test passed (test_real_anketa_e2e.py)
  - [x] Duration: 108.22s
  - [x] Questions sent: 10
  - [x] Fields collected: 11
  - [x] Audit score: 8.46/10
  - [x] Question #2 instant (<0.1s)

### Manual Testing:
- [x] Tested manually in production bot
- [x] User confirmation: "работает" ✅
- [x] No crashes observed
- [x] Question flow correct

### Code Quality:
- [ ] Code review пройден (self-review completed)
- [x] No TODO/FIXME comments в критичных местах
- [x] No debug/console.log statements
- [x] Code follows project conventions

---

## Git & Version Control ✅

### Code Push:
- [ ] Код запушен в GitHub
- [ ] Commit message: "feat: Iteration 26 - Hardcode question #2 for instant response"
- [ ] Branch: master
- [ ] Commit hash: [TO BE ADDED]

### Git Status:
- [ ] No uncommitted changes
- [ ] No merge conflicts
- [ ] All changes tracked

```bash
# Run before deploy:
cd C:\SnowWhiteAI\GrantService
git status
git log --oneline -5
git push origin master
```

---

## Infrastructure Checks 🔧

### Production Server:
- [ ] Server accessible via SSH
  ```bash
  ssh root@5.35.88.251
  # Expected: successful connection
  ```

- [ ] Server disk space OK (>2GB free)
  ```bash
  df -h /var/GrantService
  # Expected: >2GB available
  ```

- [ ] Server load OK (load < 2.0)
  ```bash
  uptime
  # Expected: load average < 2.0
  ```

### Services Status:
- [ ] grantservice-bot running
  ```bash
  systemctl status grantservice-bot
  # Expected: active (running)
  ```

- [ ] Qdrant running
  ```bash
  systemctl status qdrant
  curl http://localhost:6333/healthz
  # Expected: {"status":"ok"}
  ```

- [ ] PostgreSQL running
  ```bash
  systemctl status postgresql
  # Expected: active (running)
  ```

### Dependencies:
- [x] No new Python packages required
- [x] Existing packages compatible
- [ ] Python version check (3.9+)
  ```bash
  python3 --version
  # Expected: Python 3.9+
  ```

---

## Backup & Safety 🛡️

### Create Backup:
- [ ] Git branch backup created
  ```bash
  cd /var/GrantService
  git branch backup-20251023-$(date +%H%M%S)
  git branch -a | grep backup
  ```

- [ ] Database backup created (if needed)
  ```bash
  # Not required for this deploy (no DB changes)
  ```

- [ ] Config files backup (if needed)
  ```bash
  # Not required for this deploy (no config changes)
  ```

### Rollback Plan Ready:
- [x] Rollback steps documented (05_Rollback_Plan.md)
- [x] Rollback time estimated: <5 minutes
- [x] Rollback risk: LOW

---

## Documentation 📚

### Deployment Docs:
- [x] 00_Plan.md created ✅
- [x] 01_Pre_Deploy_Checklist.md (this file) ✅
- [ ] 02_Deployment_Steps.md ready
- [ ] 03_Deployment_Report.md template ready
- [ ] 04_Post_Deploy_Tests.md ready
- [x] 05_Rollback_Plan.md created (next)

### Feature Docs:
- [x] Iteration 26 documentation complete
  - [x] 00_Plan.md
  - [x] 01_Design.md
  - [x] 02_Implementation.md
  - [x] 03_Tests.md
  - [x] 04_Integration_Test_Report.md
  - [x] 05_Performance_Analysis.md
  - [x] 06_E2E_Test_Report.md

### Index Updates:
- [x] INTERVIEWER_ITERATION_INDEX.md updated
- [ ] DEPLOYMENT_INDEX.md to be updated after deploy

---

## Communication & Timing 📢

### Team Notification:
- [ ] Team notified in Telegram
- [ ] Deployment time communicated
- [ ] Expected downtime communicated (~2 min)

### Timing:
- [ ] Deploy time chosen (recommend: late evening/night)
- [ ] User activity checked (low activity time)
- [ ] No major events/demos planned

**Recommended deploy time:** 23:00-02:00 MSK (low traffic)

---

## Monitoring Setup 📊

### Logs:
- [ ] Log access verified
  ```bash
  tail -f /var/log/grantservice-bot.log
  # Should show recent activity
  ```

- [ ] Log rotation configured
  ```bash
  ls -lh /var/log/grantservice-bot.log*
  # Should not be too large
  ```

### Metrics:
- [ ] Metrics dashboard accessible (if exists)
- [ ] Alert rules configured (if exists)
- [ ] Monitoring plan ready (1 hour watch)

### Test Accounts:
- [ ] Test user account ready
- [ ] Test scenarios prepared
  1. Start interview
  2. Answer question #1 (name)
  3. Verify question #2 instant
  4. Complete full interview

---

## Final Checks ⚡

### Pre-Deployment:
- [ ] All checklists above completed
- [ ] No blockers identified
- [ ] Deployment window confirmed
- [ ] Team ready

### Go/No-Go Decision:
- [ ] **GO** - All green, ready to deploy
- [ ] **NO-GO** - Issues found, need to resolve

### Issues Found:
```
[List any issues found during checklist]

No issues found ✅
```

---

## Deployment Command Preview:

```bash
# Connect to server
ssh root@5.35.88.251

# Navigate to repo
cd /var/GrantService

# Create backup branch
git branch backup-20251023-$(date +%H%M%S)

# Pull latest
git fetch origin
git pull origin master

# Verify files changed
git diff HEAD@{1} HEAD --stat

# Restart service
systemctl restart grantservice-bot

# Check status
systemctl status grantservice-bot

# Watch logs
tail -f /var/log/grantservice-bot.log
```

---

## Sign-Off ✍️

### Checklist Completed By:
- **Name:** Claude Code AI Assistant
- **Date:** 2025-10-23
- **Time:** [TO BE FILLED]

### Approved for Deployment:
- [ ] All items checked
- [ ] No blockers
- [ ] Ready to proceed

**Status:** 🔄 AWAITING FINAL ITEMS
**Next Step:** Complete remaining [ ] items, then proceed to 02_Deployment_Steps.md

---

**Created:** 2025-10-23
**Last Updated:** 2025-10-23
