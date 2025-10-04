# Hosting Setup Guide - Python Path Configuration
**Version**: 1.0.0
**Date**: 2025-10-03
**Author**: Streamlit Admin Developer Agent

## Overview

This document explains how to configure `PYTHONPATH` for GrantService web-admin on hosting environments (Beget VPS, etc.) to resolve `ModuleNotFoundError` issues.

## Problem Context

**Error**: `ModuleNotFoundError: No module named 'utils.database'`

**Root Cause**: Python cannot find project modules because `sys.path` doesn't include required directories. This happens because:
1. Streamlit multipage apps run each page as separate process
2. Each process needs correct `PYTHONPATH` configured
3. Hosting environments don't automatically set project paths

## Solution Architecture

We use **dual approach** for maximum reliability:

1. **Local Development**: `setup_paths.py` module (code-based)
2. **Production Hosting**: `PYTHONPATH` environment variable (system-level)

### Why Dual Approach?

- **setup_paths.py**: Works immediately, no configuration needed
- **PYTHONPATH**: More reliable on hosting, survives process restarts
- **Combined**: Ensures imports work in all scenarios

---

## Setup Instructions

### 🖥️ For Beget VPS (or similar hosting)

#### Step 1: Identify Project Paths

SSH into your server and locate your project:

```bash
# Example paths (adjust to your actual paths):
PROJECT_ROOT="/home/username/GrantService"
WEB_ADMIN_DIR="/home/username/GrantService/web-admin"
DATA_DIR="/home/username/GrantService/data"
```

#### Step 2: Configure systemd Service

Edit your systemd service file (e.g., `/etc/systemd/system/grantservice-admin.service`):

```ini
[Unit]
Description=GrantService Admin Panel
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/username/GrantService/web-admin
# CRITICAL: Set PYTHONPATH environment variable
Environment="PYTHONPATH=/home/username/GrantService:/home/username/GrantService/web-admin:/home/username/GrantService/data"
Environment="STREAMLIT_SERVER_PORT=8550"
Environment="STREAMLIT_SERVER_ADDRESS=0.0.0.0"
# Optional: Enable debug mode
# Environment="GRANTSERVICE_DEBUG=1"
ExecStart=/home/username/venv/bin/streamlit run app_main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Key Points**:
- `PYTHONPATH` includes all required directories separated by `:`
- Paths are absolute (not relative)
- `WorkingDirectory` points to `web-admin/`

#### Step 3: Reload systemd and Restart Service

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Restart service
sudo systemctl restart grantservice-admin

# Check status
sudo systemctl status grantservice-admin

# View logs
sudo journalctl -u grantservice-admin -f
```

#### Step 4: Verify Setup

Check if paths are correct:

```bash
# SSH into server
ssh user@your-server

# Activate virtualenv
source ~/venv/bin/activate

# Test imports manually
cd ~/GrantService/web-admin
python3 -c "import sys; sys.path.insert(0, '.'); import setup_paths; print('✅ setup_paths OK')"
python3 -c "import sys; sys.path.insert(0, '.'); import setup_paths; from utils.database import AdminDatabase; print('✅ Imports OK')"
```

---

### 🐳 For Docker Deployment

If using Docker, add `PYTHONPATH` to your `Dockerfile` or `docker-compose.yml`:

#### Dockerfile:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . /app

# Set PYTHONPATH
ENV PYTHONPATH="/app:/app/web-admin:/app/data"

RUN pip install -r requirements.txt

WORKDIR /app/web-admin
CMD ["streamlit", "run", "app_main.py", "--server.port=8550"]
```

#### docker-compose.yml:
```yaml
version: '3.8'
services:
  admin-panel:
    build: .
    ports:
      - "8550:8550"
    environment:
      - PYTHONPATH=/app:/app/web-admin:/app/data
      - STREAMLIT_SERVER_PORT=8550
    volumes:
      - ./data:/app/data
    restart: always
```

---

### 💻 For Local Development

Local development uses `setup_paths.py` (already configured). No additional steps needed!

**To enable debug mode** (see path setup details):
```bash
# Linux/Mac
export GRANTSERVICE_DEBUG=1
streamlit run app_main.py

# Windows
set GRANTSERVICE_DEBUG=1
streamlit run app_main.py
```

---

## Verification & Troubleshooting

### ✅ Test 1: Verify setup_paths.py

```python
# In Python REPL or script:
import sys
sys.path.insert(0, '/path/to/web-admin')
import setup_paths

info = setup_paths.setup_project_paths()
print(f"Status: {info['status']}")
print(f"Paths added: {info['paths_added']}")
```

### ✅ Test 2: Verify imports

```python
import sys
sys.path.insert(0, '/path/to/web-admin')
import setup_paths

results = setup_paths.verify_imports()
for module, status in results.items():
    print(f"{module}: {status}")
```

Expected output:
```
utils.database: OK
data.database: OK
utils.ui_helpers: OK
```

### ❌ Common Issues

#### Issue 1: Still getting ModuleNotFoundError

**Solution**:
1. Check PYTHONPATH in systemd service is correct
2. Restart service after changes: `sudo systemctl restart grantservice-admin`
3. Check logs: `sudo journalctl -u grantservice-admin -n 50`

#### Issue 2: Works locally but fails on hosting

**Solution**:
1. Verify absolute paths in systemd service (not relative like `./`)
2. Ensure user has read permissions to all directories
3. Check virtualenv path in `ExecStart` is correct

#### Issue 3: Imports work in main file but fail in pages/

**Solution**:
1. Ensure each page imports `setup_paths` BEFORE any project imports
2. Check page has: `sys.path.insert(0, str(Path(__file__).parent.parent))`
3. Verify Streamlit version supports multipage apps (>= 1.10.0)

---

## File Changes Summary

All files updated to use centralized path setup:

### Created:
- `web-admin/setup_paths.py` - Centralized path configuration module

### Modified:
- `web-admin/app_main.py` - Main application entry point
- `web-admin/pages/🤖_Агенты.py` - Agents page
- `web-admin/pages/📊_Аналитика.py` - Analytics page
- `web-admin/pages/📄_Гранты.py` - Grants page
- `web-admin/pages/👥_Пользователи.py` - Users page
- `web-admin/pages/🎯_Dashboard.py` - Dashboard page
- `web-admin/pages/⚙️_Настройки.py` - Settings page
- `web-admin/utils/database.py` - Database utilities

### Pattern Used:
```python
# OLD (removed):
current_file = Path(__file__).resolve()
web_admin_dir = current_file.parent.parent
if str(web_admin_dir) not in sys.path:
    sys.path.insert(0, str(web_admin_dir))

# NEW (all files):
sys.path.insert(0, str(Path(__file__).parent.parent))
import setup_paths
```

---

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `PYTHONPATH` | Python module search paths | `/home/user/GrantService:/home/user/GrantService/web-admin` |
| `GRANTSERVICE_DEBUG` | Enable debug output for path setup | `1` (enabled) or `0` (disabled) |
| `STREAMLIT_SERVER_PORT` | Admin panel port | `8550` |
| `STREAMLIT_SERVER_ADDRESS` | Bind address | `0.0.0.0` (all interfaces) |

---

## Maintenance

### When Adding New Pages

1. Copy template:
```python
import streamlit as st
import sys
from pathlib import Path

# PATH SETUP - ALWAYS FIRST!
sys.path.insert(0, str(Path(__file__).parent.parent))
import setup_paths

# Now safe to import project modules
from utils.database import AdminDatabase
```

2. No changes needed to systemd service

### When Deploying Updates

```bash
# Pull latest code
cd ~/GrantService
git pull

# Restart service (PYTHONPATH persists)
sudo systemctl restart grantservice-admin

# Verify
sudo systemctl status grantservice-admin
```

---

## Additional Resources

- **Setup Paths Module**: `web-admin/setup_paths.py`
- **Import Fix Report**: `.claude/agents/streamlit-admin-developer/reports/2025-10-03_import_fix_report.md`
- **Deployment Guide**: `doc/DEPLOYMENT.md`
- **Systemd Service**: Check your hosting docs for service file location

---

## Support

If you encounter import errors:

1. Enable debug mode: `GRANTSERVICE_DEBUG=1`
2. Check logs: `sudo journalctl -u grantservice-admin -f`
3. Verify paths: Run verification tests above
4. Contact: Streamlit Admin Developer Agent

---

**Last Updated**: 2025-10-03
**Version**: 1.0.0
**Status**: ✅ Tested on Beget VPS
