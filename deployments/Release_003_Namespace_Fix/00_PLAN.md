# Release XXX: [Feature/Fix Name]

**Release Number:** XXX
**Release Date:** YYYY-MM-DD
**Deployed By:** [Name]
**Status:** 📅 PLANNED | 🚀 IN PROGRESS | ✅ DEPLOYED | ❌ ROLLED BACK

---

## 🎯 Goal

[Brief description of what this release does and why]

**Current State:**
- [What's the situation now?]
- [What problem are we solving?]

**Target State:**
- [What will be achieved after deployment?]
- [How will it improve the system?]

---

## 📦 What's Being Deployed

### Code Changes
- **Branch:** [branch-name]
- **Commits:** [commit-hash-range or count]
- **Files Changed:** [number] files
- **Lines Changed:** +[added] -[removed]

### Features/Fixes
1. [Feature/Fix 1]
2. [Feature/Fix 2]
3. [...]

### Dependencies
- [ ] Database migrations
- [ ] Environment variables
- [ ] External services (Qdrant, etc.)
- [ ] New Python packages

---

## 🔍 Testing Status

### Localhost Tests
- [ ] Smoke tests passed
- [ ] Integration tests passed
- [ ] E2E tests passed

### Manual Testing
- [ ] Feature tested manually
- [ ] Edge cases covered
- [ ] Error handling verified

---

## 📋 Deployment Steps

1. **Backup:**
   ```bash
   # Backup database
   pg_dump grantservice > backup_YYYY-MM-DD.sql

   # Backup code
   cd /root/GrantService && git archive HEAD > backup_YYYY-MM-DD.tar
   ```

2. **Stop Bot:**
   ```bash
   systemctl stop grantservice-bot
   ```

3. **Pull Changes:**
   ```bash
   cd /root/GrantService
   git pull origin master
   ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run Migrations:**
   ```bash
   # If database changes
   psql grantservice < data/migrations/XXX_migration.sql
   ```

6. **Start Bot:**
   ```bash
   systemctl start grantservice-bot
   systemctl status grantservice-bot
   ```

7. **Verify:**
   - Check logs: `tail -f /var/log/grantservice/bot.log`
   - Test basic functionality

---

## 🔙 Rollback Plan

If deployment fails:

```bash
# Stop bot
systemctl stop grantservice-bot

# Revert code
cd /root/GrantService
git reset --hard [previous-commit-hash]

# Restore database (if needed)
psql grantservice < backup_YYYY-MM-DD.sql

# Restart bot
systemctl start grantservice-bot
```

---

## ⚠️ Risks

1. **[Risk 1]**
   - Probability: LOW | MEDIUM | HIGH
   - Impact: LOW | MEDIUM | HIGH
   - Mitigation: [How to handle]

2. **[Risk 2]**
   - ...

---

## 📊 Success Criteria

- [ ] Bot starts successfully
- [ ] No errors in logs
- [ ] Critical features working (interview, audit, writer)
- [ ] Database connections stable
- [ ] No user complaints within 24 hours

---

**Related:**
- Iteration: [Link to iteration if applicable]
- Git Tag: `release-XXX`
- Production Server: `ssh root@5.35.88.251`
