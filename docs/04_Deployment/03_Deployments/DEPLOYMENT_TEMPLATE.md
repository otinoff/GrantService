# Deployment Template

**Дата:** YYYY-MM-DD
**Deploy #:** X
**Название:** Deploy Name
**Статус:** 📋 PLANNED / 🔄 IN PROGRESS / ✅ COMPLETED / ⚠️ PARTIAL / ❌ FAILED

---

## 00_Plan.md - План деплоя

### Что деплоим:
- [ ] Component 1
- [ ] Component 2
- [ ] Component 3

### Зачем деплоим:
- Причина 1
- Причина 2

### Риски:
| Риск | Вероятность | Impact | Митигация |
|------|------------|--------|-----------|
| Risk 1 | High/Medium/Low | High/Medium/Low | Mitigation plan |
| Risk 2 | High/Medium/Low | High/Medium/Low | Mitigation plan |

### Success Criteria:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

### Estimated Time:
- Preparation: X hours
- Execution: X minutes
- Testing: X minutes
- **Total:** X hours

---

## 01_Pre_Deploy_Checklist.md - Чеклист перед деплоем

### Code & Tests:
- [ ] Все unit tests пройдены
- [ ] Все integration tests пройдены
- [ ] E2E tests пройдены (если есть)
- [ ] Manual testing выполнено
- [ ] Code review пройден
- [ ] Код запушен в GitHub (commit: xxxxxx)

### Infrastructure:
- [ ] Production server доступен
- [ ] Backup создан
- [ ] Disk space проверен
- [ ] Dependencies установлены

### Documentation:
- [ ] Deployment plan готов
- [ ] Rollback plan готов
- [ ] Changelog обновлен
- [ ] Team уведомлена

### Monitoring:
- [ ] Logs настроены
- [ ] Alerts настроены
- [ ] Metrics dashboard готов

---

## 02_Deployment_Steps.md - Пошаговая инструкция

### Step 1: Pre-Deployment Backup
```bash
ssh root@SERVER_IP
cd /var/GrantService
git branch backup-$(date +%Y%m%d-%H%M%S)
git status
```

### Step 2: Pull Latest Code
```bash
git fetch origin
git pull origin master
git log --oneline -5  # Verify commits
```

### Step 3: Check Dependencies
```bash
pip list | grep PACKAGE_NAME
# If missing:
pip install PACKAGE_NAME
```

### Step 4: Run Pre-Deploy Checks
```bash
python pre_deploy_check.py
```

### Step 5: Restart Services
```bash
systemctl restart grantservice-bot
systemctl status grantservice-bot
```

### Step 6: Verify Deployment
```bash
# Check logs
tail -f /var/log/grantservice-bot.log

# Check health
curl http://localhost:PORT/health
```

---

## 03_Deployment_Report.md - Отчет после деплоя

### Deployment Summary:
- **Date:** YYYY-MM-DD HH:MM
- **Duration:** X minutes
- **Deployed by:** Name
- **Commit:** xxxxxxx
- **Status:** ✅ SUCCESS / ⚠️ PARTIAL / ❌ FAILED

### Components Deployed:
- ✅ Component 1
- ✅ Component 2
- ❌ Component 3 (failed, see issues)

### Tests Results:
| Test | Result | Time | Notes |
|------|--------|------|-------|
| Service Start | ✅ PASS | 5s | OK |
| Health Check | ✅ PASS | 1s | OK |
| Feature Test | ✅ PASS | 10s | OK |

### Performance Metrics:
- Metric 1: X (before) → Y (after)
- Metric 2: X (before) → Y (after)

### Issues Encountered:
1. **Issue 1**
   - Symptom: Description
   - Cause: Root cause
   - Solution: How fixed
   - Status: ✅ FIXED / ⚠️ WORKAROUND / ❌ UNRESOLVED

### Next Steps:
- [ ] Monitor for X hours
- [ ] Collect metrics
- [ ] User feedback

---

## 04_Post_Deploy_Tests.md - Результаты тестов

### Smoke Tests:
- [ ] Service running
- [ ] Health endpoint responds
- [ ] Logs show no errors

### Functional Tests:
- [ ] Feature 1 works
- [ ] Feature 2 works
- [ ] Feature 3 works

### Integration Tests:
- [ ] Database connection
- [ ] External API connections
- [ ] Message queue

### Performance Tests:
- [ ] Response time < X ms
- [ ] Memory usage < X MB
- [ ] CPU usage < X%

### User Acceptance Tests:
- [ ] Test scenario 1
- [ ] Test scenario 2
- [ ] Test scenario 3

---

## 05_Rollback_Plan.md - План отката

### When to Rollback:
- Critical errors in logs
- Service crashes repeatedly
- Data corruption detected
- Performance degradation > 50%

### Rollback Steps:

#### Step 1: Stop Current Version
```bash
ssh root@SERVER_IP
systemctl stop grantservice-bot
```

#### Step 2: Revert Code
```bash
cd /var/GrantService
git log --oneline | head -10
git revert HEAD  # Or git checkout PREVIOUS_COMMIT
```

#### Step 3: Restart with Previous Version
```bash
systemctl start grantservice-bot
systemctl status grantservice-bot
```

#### Step 4: Verify Rollback
```bash
tail -f /var/log/grantservice-bot.log
# Verify service is healthy
```

#### Step 5: Post-Rollback Actions
- [ ] Notify team
- [ ] Document what went wrong
- [ ] Create bug report
- [ ] Plan fix

### Rollback Time Estimate:
- Expected: X minutes
- Maximum: Y minutes

### Backup Locations:
- Code: Git branch `backup-YYYYMMDD-HHMMSS`
- Database: `/backups/db_backup_YYYYMMDD.sql`
- Config: `/backups/config_backup_YYYYMMDD.tar.gz`

---

## Monitoring & Logs

### Log Locations:
- Service logs: `/var/log/grantservice-bot.log`
- System logs: `journalctl -u grantservice-bot`
- Application logs: `/var/GrantService/logs/`

### Monitoring Commands:
```bash
# Watch logs in real-time
tail -f /var/log/grantservice-bot.log

# Check for errors
grep -i error /var/log/grantservice-bot.log | tail -20

# Check service status
systemctl status grantservice-bot

# Check resource usage
top -p $(pgrep -f telegram-bot)
```

### Metrics to Monitor:
- [ ] Error rate
- [ ] Response time
- [ ] Memory usage
- [ ] CPU usage
- [ ] Request count
- [ ] Active users

---

**Template Version:** 1.0
**Created:** 2025-10-23
**Last Updated:** 2025-10-23
