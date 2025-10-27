# Deployment Log: Release XXX

**Release Number:** XXX
**Release Name:** [Feature/Fix Name]
**Deployment Date:** YYYY-MM-DD
**Start Time:** HH:MM
**Deployed By:** [Name]

---

## 📋 Pre-Deployment

**Time:** HH:MM

### Checklist Verification
- [ ] All items in `01_PRE_DEPLOY_CHECKLIST.md` completed
- [ ] Go/No-Go decision: ✅ GO

### Backup Created
```bash
# Database backup
pg_dump grantservice > backup_YYYY-MM-DD_HHMM.sql
# Result: [File size, location]

# Code backup (git tag)
git tag -a release-XXX -m "Release XXX: [Feature Name]"
git push origin release-XXX
# Result: Tag created successfully
```

**Previous Commit Hash:** `[commit-hash]`
**Current Branch:** `master`

---

## 🛑 Step 1: Stop Bot

**Time:** HH:MM

```bash
ssh root@5.35.88.251
systemctl stop grantservice-bot
systemctl status grantservice-bot
```

**Output:**
```
[Paste output here]
```

**Status:** ✅ SUCCESS | ❌ FAILED
**Notes:** [Any observations]

---

## 📥 Step 2: Pull Changes

**Time:** HH:MM

```bash
cd /root/GrantService
git status
git fetch origin
git pull origin master
```

**Output:**
```
[Paste output here]
```

**Files Changed:** [Number] files
**Commits Pulled:** [commit-range]
**Status:** ✅ SUCCESS | ❌ FAILED
**Notes:** [Any conflicts, warnings]

---

## 📦 Step 3: Install Dependencies

**Time:** HH:MM

```bash
pip install -r requirements.txt
```

**Output:**
```
[Paste output here]
```

**New Packages Installed:** [List if any]
**Packages Updated:** [List if any]
**Status:** ✅ SUCCESS | ❌ FAILED
**Notes:** [Any warnings, errors]

---

## 🗄️ Step 4: Database Migration (If Needed)

**Time:** HH:MM

**Migration Required:** YES | NO

**If YES:**
```bash
# Run migration
psql -U postgres -d grantservice < data/migrations/XXX_migration.sql

# Verify migration
psql -U postgres -d grantservice -c "\dt"
```

**Output:**
```
[Paste output here]
```

**Tables Added/Modified:** [List]
**Status:** ✅ SUCCESS | ❌ FAILED | N/A
**Notes:** [Any issues]

---

## 🚀 Step 5: Start Bot

**Time:** HH:MM

```bash
systemctl start grantservice-bot
sleep 5
systemctl status grantservice-bot
```

**Output:**
```
[Paste output here]
```

**Status:** ✅ SUCCESS | ❌ FAILED
**PID:** [Process ID]
**Notes:** [Any startup warnings]

---

## 🔍 Step 6: Verify Logs

**Time:** HH:MM

```bash
tail -f /var/log/grantservice/bot.log
# Watch for 2-3 minutes
```

**Log Output (First 50 lines):**
```
[Paste relevant log lines here]
```

**Observations:**
- [ ] Bot started successfully
- [ ] Database connection established
- [ ] No errors in startup
- [ ] Telegram connection OK

**Status:** ✅ SUCCESS | ❌ FAILED
**Notes:** [Any warnings, errors]

---

## 🧪 Step 7: Basic Smoke Test

**Time:** HH:MM

### Test 1: Bot Responds to /start
```
User Action: Sent /start command
Bot Response: [Paste response]
Status: ✅ PASS | ❌ FAIL
```

### Test 2: Interview Start
```
User Action: Started interview
Bot Response: [Paste first question]
Status: ✅ PASS | ❌ FAIL
```

### Test 3: Answer Question
```
User Action: Provided answer
Bot Response: [Paste next question or completion]
Status: ✅ PASS | ❌ FAIL
```

**Overall Smoke Test:** ✅ PASS | ❌ FAIL
**Notes:** [Any issues]

---

## 📊 Deployment Summary

**Total Time:** [HH:MM] - [HH:MM] = [Duration]
**Overall Status:** ✅ SUCCESS | ⚠️ SUCCESS WITH WARNINGS | ❌ FAILED

### What Went Well
- [Item 1]
- [Item 2]

### Issues Encountered
- [Issue 1]: [How resolved]
- [Issue 2]: [How resolved]

### Follow-Up Actions
- [ ] [Action 1]
- [ ] [Action 2]

---

## 🔔 Notifications

**Time:** HH:MM

- [ ] Team notified (Telegram/Slack/Email)
- [ ] Users notified (if needed)
- [ ] Documentation updated

**Message Sent:**
```
[Paste notification message]
```

---

## 📈 Post-Deployment Monitoring

**Monitoring Period:** Next 24-48 hours

**Key Metrics to Watch:**
- [ ] Error rate in logs
- [ ] Response times
- [ ] User complaints
- [ ] Database performance
- [ ] Memory/CPU usage

**Next Check:** [Date/Time]

---

## 🔙 Rollback Information (If Needed)

**Rollback Trigger Conditions:**
- Critical errors in logs
- Bot not responding
- Database corruption
- User-facing failures

**Rollback Command (DO NOT RUN unless needed):**
```bash
# Stop bot
systemctl stop grantservice-bot

# Revert code
cd /root/GrantService
git reset --hard [previous-commit-hash]

# Restore database (if schema changed)
psql -U postgres -d grantservice < backup_YYYY-MM-DD_HHMM.sql

# Restart bot
systemctl start grantservice-bot
```

**Rollback Time Estimate:** [X] minutes

---

## ✅ Deployment Complete

**Completed By:** [Name]
**Completion Time:** HH:MM
**Next Steps:** Monitor for 24-48 hours, then proceed to `03_VERIFICATION.md`

---

**Signature:** _________________________
**Date:** _________________________
