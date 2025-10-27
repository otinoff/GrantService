# Pre-Deployment Checklist: Release XXX

**Release Number:** XXX
**Release Name:** [Feature/Fix Name]
**Date:** YYYY-MM-DD
**Checked By:** [Name]

---

## ✅ Code Quality

- [ ] All tests passing locally
  ```bash
  pytest tests/
  ```
- [ ] No linting errors
  ```bash
  flake8 agents/ telegram-bot/
  ```
- [ ] Code reviewed (if working in team)
- [ ] Commit messages are clear and descriptive
- [ ] All TODOs addressed or documented

---

## ✅ Database

- [ ] Database migrations tested on localhost
- [ ] Backup strategy confirmed
  ```bash
  pg_dump grantservice > backup_YYYY-MM-DD.sql
  ```
- [ ] Migration scripts ready (if needed)
- [ ] Database schema changes documented
- [ ] Rollback SQL prepared (if schema changes)

---

## ✅ Dependencies

- [ ] `requirements.txt` updated (if new packages)
- [ ] All new dependencies compatible with production Python version
- [ ] No conflicting package versions
- [ ] External services ready (Qdrant, etc.)
- [ ] API keys/tokens valid and accessible

---

## ✅ Configuration

- [ ] Environment variables documented
- [ ] `.env` values verified for production
- [ ] No hardcoded credentials in code
- [ ] Logging configuration appropriate for production
- [ ] Debug mode disabled

---

## ✅ Testing

### Localhost Tests
- [ ] Smoke tests passed
  - [ ] Bot starts successfully
  - [ ] Database connection works
  - [ ] Interviewer agent works
  - [ ] Auditor agent works
  - [ ] Writer agent works
- [ ] Integration tests passed
- [ ] E2E tests passed (full flow)

### Manual Testing
- [ ] Tested happy path scenarios
- [ ] Tested edge cases
- [ ] Tested error handling
- [ ] Tested with real GigaChat/Claude API
- [ ] Performance acceptable (no timeouts)

---

## ✅ Documentation

- [ ] CHANGELOG updated
- [ ] README updated (if API changes)
- [ ] Architecture docs updated (if structure changes)
- [ ] Deployment plan documented (`00_PLAN.md`)
- [ ] Rollback procedure documented

---

## ✅ Production Environment

- [ ] Production server accessible
  ```bash
  ssh root@5.35.88.251
  ```
- [ ] Disk space sufficient
  ```bash
  df -h
  ```
- [ ] Production database accessible
- [ ] Systemd service file up to date
- [ ] Log rotation configured

---

## ✅ Backup & Rollback

- [ ] Database backup created
- [ ] Code backup created (git tag)
- [ ] Previous commit hash documented
- [ ] Rollback steps tested (dry run)
- [ ] Rollback window identified (time estimate)

---

## ✅ Communication

- [ ] Team notified about deployment time
- [ ] Users notified (if breaking changes)
- [ ] Maintenance window scheduled (if needed)
- [ ] Support team briefed (if applicable)

---

## ✅ Monitoring

- [ ] Log monitoring ready
  ```bash
  tail -f /var/log/grantservice/bot.log
  ```
- [ ] Error alerting configured
- [ ] Performance metrics baseline established
- [ ] Rollback triggers defined

---

## 🚨 Go/No-Go Decision

**Check ALL boxes before proceeding with deployment.**

### Critical Blockers (Must be YES)
- [ ] All tests passing
- [ ] Database backup created
- [ ] Rollback plan ready
- [ ] Production environment accessible

### Risk Assessment
- **Overall Risk Level:** LOW | MEDIUM | HIGH
- **Deployment Window:** [HH:MM] - [HH:MM]
- **Rollback Time Estimate:** [X] minutes

---

## 📝 Sign-Off

**Approved By:** _________________________
**Date/Time:** _________________________
**Status:** ✅ GO | ❌ NO-GO

---

**Notes:**
- If any critical item is unchecked, deployment should be postponed
- Medium/High risk deployments should be done during low-traffic hours
- Always have someone available for rollback if needed

---

**Next Step:** If all checks pass → Proceed to `02_DEPLOYMENT_LOG.md`
