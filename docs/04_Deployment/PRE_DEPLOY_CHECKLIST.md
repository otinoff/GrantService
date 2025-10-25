# Pre-Deploy Checklist - GrantService

**Purpose:** Ensure stability before production deployment
**Methodology:** Project Evolution Methodology (Гомеостаз principle)

---

## ✅ CODE QUALITY

- [ ] All tests pass locally (`pytest tests/`)
- [ ] No hardcoded secrets or credentials
- [ ] Error handling for all external APIs (GigaChat, PostgreSQL, Qdrant)
- [ ] Code review completed (if team >1)
- [ ] No console.log or debug statements

---

## ✅ DATABASE

- [ ] Migration SQL tested on local DB first
- [ ] Backup created before migration
- [ ] Rollback SQL prepared
- [ ] No breaking schema changes (or coordinated with bot restart)

---

## ✅ CONFIGURATION

- [ ] Environment variables checked (.env or system env)
- [ ] GigaChat credentials valid (Client ID: 967330d4-e5ab-4fca-a8e8-12a7d510d249)
- [ ] PostgreSQL connection working (port 5434)
- [ ] Qdrant connection working (5.35.88.251:6333)

---

## ✅ GIT

- [ ] Git commit created with clear message format:
  ```
  feat: Iteration XX - Brief description

  Details:
  - Change 1
  - Change 2

  Deploy: #XX
  ```
- [ ] Git pushed to GitHub (master branch)
- [ ] No uncommitted changes left

---

## ✅ DEPLOYMENT

- [ ] Production server accessible (SSH: root@5.35.88.251)
- [ ] Services can be restarted without downtime
- [ ] Rollback plan documented and tested
- [ ] Team notified about deployment window

---

## ✅ TESTING

- [ ] Smoke test plan ready (manual steps to verify)
- [ ] User acceptance criteria defined
- [ ] Test user account ready (telegram_id: 5032079932)

---

## ✅ MONITORING

- [ ] Logs accessible (`journalctl -u grantservice-bot`)
- [ ] Error tracking enabled
- [ ] Performance metrics tracked (if available)

---

## ✅ COMMUNICATION

- [ ] Team notified about deployment
- [ ] Users notified if breaking changes
- [ ] Documentation updated (README, CLAUDE.md)

---

## ✅ SBER500 BOOTCAMP (if using GigaChat)

- [ ] Token tracking enabled
- [ ] Statistics collection working
- [ ] Report generation ready

---

## 🚀 DEPLOYMENT STEPS

1. SSH to production:
   ```bash
   ssh -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251
   ```

2. Pull code:
   ```bash
   cd /var/GrantService
   git pull origin master
   ```

3. Apply DB migration (if any):
   ```bash
   PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' psql -h localhost -p 5434 -U grantservice -d grantservice -f database/migrations/XXX.sql
   ```

4. Restart bot:
   ```bash
   sudo systemctl restart grantservice-bot
   sudo systemctl status grantservice-bot --no-pager
   ```

5. Check logs:
   ```bash
   sudo journalctl -u grantservice-bot -f -n 50
   ```

6. Smoke test:
   - Send `/start` to bot
   - Test new feature
   - Verify no errors in logs

---

## 🔄 ROLLBACK PROCEDURE

If deployment fails:

1. Revert Git:
   ```bash
   git revert HEAD
   git push origin master
   ```

2. Or checkout previous commit:
   ```bash
   git checkout <previous-commit-hash>
   ```

3. Rollback DB (if migration applied):
   ```bash
   psql ... -f database/migrations/XXX_rollback.sql
   ```

4. Restart bot

---

## 📊 POST-DEPLOY

After successful deployment:

- [ ] Smoke test passed
- [ ] No errors in logs (first 5 minutes)
- [ ] Users can interact with bot normally
- [ ] Update DORA Metrics (deployment logged)
- [ ] Mark deployment as successful in Iteration report

---

**Template Version:** 1.0
**Created:** 2025-10-25 (Iteration 36)
**Last Updated:** 2025-10-25
