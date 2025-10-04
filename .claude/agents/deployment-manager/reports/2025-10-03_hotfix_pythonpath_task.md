# Hotfix Deployment Task: PYTHONPATH Configuration
**Date**: 2025-10-03
**Priority**: CRITICAL
**Type**: Configuration hotfix (no code push needed)
**Delegated by**: Project Orchestrator

---

## 🚨 Critical Issue to Fix

**Problem**: ModuleNotFoundError on Beget VPS preventing Admin Panel from running
```
ModuleNotFoundError: No module named 'utils.database'
```

**Root Cause**: systemd service missing PYTHONPATH environment variable

**Solution**: Add PYTHONPATH to systemd service configuration

---

## 📋 Your Task Checklist

### Step 1: Create Configuration Backup
```bash
# Connect to server
ssh root@5.35.88.251

# Backup current service file
cp /etc/systemd/system/grantservice-admin.service \
   /etc/systemd/system/grantservice-admin.service.backup.$(date +%Y%m%d_%H%M%S)
```

### Step 2: Locate Project Paths
```bash
# Find actual project location
find /home -name "GrantService" -type d 2>/dev/null
# OR
find /var -name "GrantService" -type d 2>/dev/null

# Verify structure
ls -la [PROJECT_PATH]/
ls -la [PROJECT_PATH]/web-admin/
ls -la [PROJECT_PATH]/data/

# Note the exact paths for next step
```

### Step 3: Edit systemd Service
```bash
# Edit the service file
nano /etc/systemd/system/grantservice-admin.service

# ADD this line in [Service] section (adjust paths based on Step 2):
Environment="PYTHONPATH=/var/GrantService:/var/GrantService/web-admin:/var/GrantService/data"
# OR if project is in /home:
Environment="PYTHONPATH=/home/username/GrantService:/home/username/GrantService/web-admin:/home/username/GrantService/data"

# Ensure these are also set:
Environment="STREAMLIT_SERVER_PORT=8550"
Environment="STREAMLIT_SERVER_ADDRESS=0.0.0.0"
```

### Step 4: Reload and Restart Service
```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Restart the service
sudo systemctl restart grantservice-admin

# Check status
sudo systemctl status grantservice-admin --no-pager
```

### Step 5: Verify No Import Errors
```bash
# Check recent logs (should NOT see ModuleNotFoundError)
sudo journalctl -u grantservice-admin -n 100 --no-pager | grep -i "modulenotfounderror"
# Expected: No output (no errors)

# Check service is running
sudo journalctl -u grantservice-admin -n 50 --no-pager

# Look for successful startup messages
```

### Step 6: Test Admin Panel
```bash
# Check port is listening
ss -tulpn | grep 8550

# Test HTTP response
curl -I http://localhost:8550
# Expected: HTTP/1.1 200 OK or redirect

# Test from external (if nginx proxy configured)
curl -I https://grantservice.onff.ru/
# Expected: HTTP/2 200 or similar
```

### Step 7: Verify setup_paths.py is Present
```bash
# The fix includes new file that should be on server
ls -la [PROJECT_PATH]/web-admin/setup_paths.py
# Should exist and be readable
```

---

## ✅ Success Criteria

1. ✅ systemd service has PYTHONPATH environment variable
2. ✅ Service restarts without errors
3. ✅ NO ModuleNotFoundError in journalctl logs
4. ✅ Port 8550 is listening
5. ✅ HTTP requests return 200 OK
6. ✅ Admin panel loads without import errors

---

## ❌ Rollback Plan (if needed)

If something goes wrong:
```bash
# Restore backup
cp /etc/systemd/system/grantservice-admin.service.backup.* \
   /etc/systemd/system/grantservice-admin.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart grantservice-admin
```

---

## 📝 Report Template

After completion, create report at:
`.claude/agents/deployment-manager/reports/2025-10-03_pythonpath_deployment.md`

```markdown
# PYTHONPATH Hotfix Deployment Report
**Date**: 2025-10-03
**Time**: HH:MM
**Status**: ✅ SUCCESS / ❌ FAILED

## Changes Applied
- [x] Backup created: filename
- [x] Project path identified: /path/to/GrantService
- [x] PYTHONPATH added: value
- [x] Service reloaded and restarted

## Verification Results
- Service Status: Active (running)
- Import Errors: None found
- Port 8550: Listening
- HTTP Test: 200 OK
- Uptime: X minutes

## Issues Encountered
None / Description

## Rollback Needed
No / Yes (reason)

## Next Steps
- Monitor for 15 minutes
- Check user reports
```

---

## 🔍 Debug Commands (if needed)

```bash
# Full Python path check
ssh root@5.35.88.251 "cd /var/GrantService/web-admin && python3 -c 'import sys; print(sys.path)'"

# Test imports manually
ssh root@5.35.88.251 "cd /var/GrantService/web-admin && python3 -c 'import setup_paths; from utils.database import AdminDatabase; print(\"OK\")'"

# Check if virtual environment is used
ssh root@5.35.88.251 "which python3"
ssh root@5.35.88.251 "ls -la /home/*/venv/bin/python3"
```

---

## 📚 Reference Documents

- **Fix Report**: `.claude/agents/streamlit-admin-developer/reports/2025-10-03_import_fix_report.md`
- **Setup Guide**: `web-admin/HOSTING_SETUP.md`
- **New Module**: `web-admin/setup_paths.py`

---

## ⚠️ Important Notes

1. This is a CONFIGURATION-ONLY change - no code deployment needed
2. The code fixes are already on server from previous deployment
3. We only need to set PYTHONPATH environment variable
4. This is a critical fix - Admin Panel won't work without it
5. Create backup BEFORE making changes

---

**Good luck! Report back with results.**

*Delegated by: Project Orchestrator*
*Priority: CRITICAL - Complete ASAP*