# Lessons Learned: Critical Data Deletion Incident

## 📋 Incident Summary

**Date**: 2025-10-03
**Severity**: CRITICAL
**Impact**: Production admin panel completely broken - all pages showing ImportError
**Duration**: ~2 hours (detection to full resolution)
**Root Cause**: Physical deletion of all Python module files in `data/database/` directory on production server

---

## 🔴 Incident Timeline

### Initial Symptoms (16:00 UTC)
- Admin panel pages returning HTTP 200 but showing blank content
- Error message: `Error importing: No module named 'utils.database'`
- All 6 pages affected: Dashboard, Grants, Users, Analytics, Agents, Settings

### Investigation Phase (16:05-16:25 UTC)

#### Initial Hypothesis: PYTHONPATH Misconfiguration
```bash
# Checked systemd service configuration
cat /etc/systemd/system/grantservice-admin.service

# ✅ PYTHONPATH was correctly set:
Environment="PYTHONPATH=/var/GrantService:/var/GrantService/web-admin:/var/GrantService/data:..."
```

**Result**: PYTHONPATH was correct - hypothesis rejected

#### Second Hypothesis: Import Chain Error
```python
# Traced import chain:
app_main.py
  → utils/database.py
    → from data.database import GrantServiceDatabase  # FAILS HERE
```

Checked `utils/database.py` - imports looked correct.

#### Discovery of Root Cause (16:20 UTC)
```bash
# Checked local environment (Windows)
$ ls data/database/
__init__.py  agents.py  auth.py  interview.py  models.py  prompts.py
researcher.py  sessions.py  user_progress.py  users.py  ✅

# Checked production environment (Linux)
$ ssh root@5.35.88.251 "ls /var/GrantService/data/database/"
user_progress.py  ❌ ONLY THIS FILE!

# Git status revealed the truth
$ ssh root@5.35.88.251 "cd /var/GrantService && git status data/database/"
deleted:    data/database/__init__.py
deleted:    data/database/models.py
deleted:    data/database/auth.py
deleted:    data/database/agents.py
deleted:    data/database/interview.py
deleted:    data/database/researcher.py
deleted:    data/database/sessions.py
deleted:    data/database/users.py
deleted:    data/database/prompts.py
```

**🔑 KEY INSIGHT**: Files were physically deleted from filesystem, not just corrupted or misconfigured.

---

## 🎯 Root Cause Analysis

### What Happened

**All critical Python module files in `data/database/` were deleted from production server, except `user_progress.py`.**

### Missing Files
```
data/database/
├── __init__.py          ❌ DELETED (makes directory a Python module)
├── models.py            ❌ DELETED (contains GrantServiceDatabase class)
├── auth.py              ❌ DELETED
├── agents.py            ❌ DELETED
├── interview.py         ❌ DELETED
├── researcher.py        ❌ DELETED
├── sessions.py          ❌ DELETED
├── users.py             ❌ DELETED
├── prompts.py           ❌ DELETED
└── user_progress.py     ✅ SURVIVED
```

### Why System Failed

1. **Missing `__init__.py`**: Directory no longer recognized as Python package
2. **Missing `models.py`**: Core `GrantServiceDatabase` class unavailable
3. **Import chain broken**: All pages depend on these modules

### Why PYTHONPATH Couldn't Help

```python
# PYTHONPATH tells Python WHERE to look for modules
sys.path = [..., '/var/GrantService/data', ...]

# But if files don't physically exist, Python can't import them
from data.database import GrantServiceDatabase  # ❌ File not found!
```

**You can't import files that don't exist, no matter how correct your PYTHONPATH is.**

---

## ✅ Resolution

### Immediate Fix (16:25 UTC)
```bash
# Restore deleted files from git repository
cd /var/GrantService
git restore data/database/

# Verify restoration
ls data/database/
# ✅ All 10 files now present

# Clear Python cache to ensure clean imports
find . -type d -name '__pycache__' -exec rm -rf {} +
find . -type f -name '*.pyc' -delete

# Restart service with fresh imports
systemctl restart grantservice-admin
```

### Verification (16:30 UTC)
```bash
# Check for import errors in logs
journalctl -u grantservice-admin --since '1 minute ago' | grep ImportError
# ✅ No errors found

# Verify all pages responding
curl -I https://grantservice.onff.ru/👥_Пользователи
# HTTP/1.1 200 OK ✅

curl -I https://grantservice.onff.ru/📄_Гранты
# HTTP/1.1 200 OK ✅

# All 6 pages tested - all returning 200 ✅
```

---

## 🛡️ Preventive Measures Implemented

### 1. GitHub Actions Workflow File Verification

**Added to `.github/workflows/deploy-grantservice.yml`** (Lines 99-146):

```yaml
# ========================================
# КРИТИЧЕСКАЯ ПРОВЕРКА: Verify critical files exist
# ========================================
echo "Verifying critical Python modules..."
MISSING_FILES=0

# Проверка data/database/ модулей
if [ ! -f "data/database/__init__.py" ]; then
  echo "✗ ERROR: data/database/__init__.py is MISSING!"
  MISSING_FILES=1
else
  echo "✓ data/database/__init__.py exists"
fi

if [ ! -f "data/database/models.py" ]; then
  echo "✗ ERROR: data/database/models.py is MISSING!"
  MISSING_FILES=1
else
  echo "✓ data/database/models.py exists"
fi

if [ ! -f "data/database/auth.py" ]; then
  echo "✗ ERROR: data/database/auth.py is MISSING!"
  MISSING_FILES=1
else
  echo "✓ data/database/auth.py exists"
fi

# Если файлы отсутствуют - восстанавливаем из git
if [ $MISSING_FILES -eq 1 ]; then
  echo "⚠️  CRITICAL: Missing core Python modules detected!"
  echo "Restoring from git repository..."
  git restore data/database/

  # Повторная проверка
  if [ -f "data/database/models.py" ]; then
    echo "✓ Files successfully restored from git"
  else
    echo "✗ FATAL: Cannot restore critical files - deployment ABORTED"
    exit 1
  fi
fi

# Очистка Python кэша для чистого импорта
echo "Clearing Python cache..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
echo "✓ Python cache cleared"
```

**Benefits**:
- ✅ Detects missing files before service restart
- ✅ Automatically restores from git if possible
- ✅ Aborts deployment if restoration fails
- ✅ Clears Python cache to prevent import issues

### 2. Headless Browser Testing

**Created `scripts/headless_check.py`**:
- Uses Playwright to test all 6 admin pages
- Checks HTTP status, expected content, and error messages
- Runs after every deployment to verify functionality

**Created `scripts/quick_pages_check.sh`**:
- Fast curl-based health checks
- No dependencies beyond curl
- Can run on any system

**Updated `.claude/agents/deployment-manager.md`**:
- Added headless testing to deployment workflow
- Automated post-deployment verification

### 3. Enhanced Monitoring

**Added to deployment workflow**:
```bash
# Финальная проверка БД
echo "Verifying production database..."
if [ -f "data/grantservice.db" ]; then
  DB_SIZE=$(du -h data/grantservice.db | cut -f1)
  echo "✓ Production database intact: $DB_SIZE"
else
  echo "✗ ERROR: Production database missing after update!"
  if [ -f "data/grantservice.db.backup" ]; then
    echo "Restoring from backup..."
    cp data/grantservice.db.backup data/grantservice.db
    echo "✓ Database restored from backup"
  fi
fi
```

---

## 📚 Key Lessons

### Technical Lessons

1. **PYTHONPATH ≠ File Existence**
   - Correct Python path doesn't help if files don't physically exist
   - Always verify file presence, not just configuration

2. **Git is Your Safety Net**
   - Git repository preserved all deleted files
   - `git restore` is faster and safer than backup restoration
   - Always check `git status` to detect unexpected deletions

3. **Python Import Cache Issues**
   - `__pycache__` directories can mask import problems
   - Always clear cache after file restoration: `find . -type d -name '__pycache__' -exec rm -rf {} +`

4. **Multipage Streamlit Apps**
   - Each page is a separate process with independent imports
   - Import errors affect all pages, not just one
   - Check logs: `journalctl -u service-name --since '1 minute ago'`

### Process Lessons

1. **Automated Verification is Critical**
   - Manual checks are slow and error-prone
   - Headless browser testing catches real user-facing issues
   - File verification should be part of every deployment

2. **Defense in Depth**
   - Multiple layers of protection: file checks + auto-restore + monitoring
   - Don't rely on single point of failure (e.g., just PYTHONPATH)

3. **Documentation During Crisis**
   - Document investigation steps as you go
   - Timeline helps identify patterns
   - Commands used become future runbooks

### Investigation Lessons

1. **Start with Facts, Not Assumptions**
   - We assumed PYTHONPATH was wrong
   - Actually files were deleted
   - Checking both local and production revealed the truth

2. **Compare Working vs Broken**
   - Local (working) had all files
   - Production (broken) missing files
   - Side-by-side comparison revealed root cause immediately

3. **Git Status is Diagnostic Gold**
   - `git status` showed all deleted files
   - Faster than manually comparing directories
   - Works even when files are deleted

---

## 🔍 Mystery: How Were Files Deleted?

**Still Unknown**: The exact mechanism that deleted the files.

### Possible Causes

1. **Manual Deletion** (accidental)
   ```bash
   rm -rf data/database/*  # Oops!
   ```

2. **Failed Git Operation**
   ```bash
   git checkout -- .  # Could delete tracked files
   git clean -fd      # Deletes untracked, but should preserve tracked
   ```

3. **Deployment Script Bug**
   - Previous version of deploy script?
   - Data migration gone wrong?

4. **Filesystem Issue**
   - Unlikely but possible corruption
   - Disk space issue causing file loss

### Investigation Commands Used
```bash
# Check git log for suspicious operations
git log --all --full-history -- data/database/

# Check bash history for rm commands
grep -i "rm.*database" ~/.bash_history

# Check system logs
journalctl --since '2025-10-02' | grep -i "database"
```

**Note**: Without finding the deletion mechanism, we can't guarantee it won't happen again. The preventive measures will mitigate, but not eliminate, the risk.

---

## 📋 Action Items for Future

### Short Term
- [x] Implement file verification in GitHub Actions
- [x] Add automated restoration
- [x] Add headless browser testing
- [x] Document this incident

### Medium Term
- [ ] Add file integrity monitoring (e.g., AIDE or Tripwire)
- [ ] Set up alerts for unexpected file deletions
- [ ] Create automated smoke tests that run every hour
- [ ] Add pre-deployment file checksums

### Long Term
- [ ] Consider immutable infrastructure (Docker containers)
- [ ] Implement blue-green deployment to test before switching
- [ ] Add comprehensive integration tests
- [ ] Set up centralized logging with alerting

---

## 🎓 Training Points

### For Developers
1. Always use `git status` to check for unexpected changes before deploying
2. Test deployments in staging environment that mirrors production
3. Keep local and production environments in sync for comparison

### For Operations
1. Monitor systemd service logs continuously
2. Set up alerts for service restarts or failures
3. Maintain regular file system backups separate from git

### For Everyone
1. Document unusual incidents immediately
2. Share lessons learned with team
3. Update runbooks based on real incidents

---

## 📞 Contacts

**Incident Lead**: Claude Code Assistant
**Reported By**: Project Owner
**Severity**: CRITICAL
**Status**: RESOLVED with preventive measures implemented

---

## 📎 Related Documentation

- `.github/workflows/deploy-grantservice.yml` - Enhanced deployment workflow
- `scripts/headless_check.py` - Automated UI testing
- `scripts/quick_pages_check.sh` - Fast health checks
- `.claude/agents/deployment-manager.md` - Deployment procedures
- `scripts/README_SYNC.md` - Deployment scripts documentation

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Next Review**: After next major deployment
