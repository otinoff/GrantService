# Windows Encoding Fix for pytest

**Problem:** `UnicodeEncodeError: 'charmap' codec can't encode character` when running pytest on Windows

**Date:** 2025-10-26
**Iteration:** 46
**Status:** ✅ FIXED

---

## 🐛 The Problem

When running pytest on Windows with UTF-8 content (русский текст, emoji 🚀), you get:

```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680' in position 39: character maps to <undefined>
```

**Root Cause:**
- Windows console defaults to `cp1251` encoding (Cyrillic)
- Python logging/stdout tries to output UTF-8 characters (emoji, special chars)
- `cp1251` can't encode many Unicode characters

**Common scenarios:**
- Emoji in log messages (🚀, ✅, ⚠️)
- Russian text in assertions/output
- Special Unicode characters in test data

---

## ✅ The Solution

Add this to `tests/conftest.py` **before any imports**:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest configuration and shared fixtures
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ===== WINDOWS ENCODING FIX =====
# Fix for UnicodeEncodeError on Windows console (cp1251)
# This ensures UTF-8 is used for stdout/stderr
if sys.platform == 'win32':
    import io
    # Wrap stdout and stderr with UTF-8 encoding
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'  # Replace unencodable chars instead of crashing
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding='utf-8',
        errors='replace'
    )
    # Set environment variable for subprocess
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Настройка логирования для тестов
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s',
    # Force UTF-8 encoding for file handlers
    encoding='utf-8',
    force=True  # Override existing handlers
)

# ... rest of conftest.py
```

---

## 🧪 Testing the Fix

**Before fix:**
```bash
$ python -m pytest tests/ -v
...
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680' ❌
```

**After fix:**
```bash
$ python -m pytest tests/ -v
...
[INFO] web_admin: 🚀 GrantService Web Admin - система логирования v2.0 запущена ✅
[INFO] database: 📝 Логирование инициализировано ✅
```

---

## 📋 Key Points

1. **Must be early in conftest.py** - before other modules import logging
2. **Only on Windows** - `if sys.platform == 'win32'`
3. **errors='replace'** - replaces unencodable chars with `?` instead of crashing
4. **PYTHONIOENCODING** - affects subprocess calls (pytest workers, etc.)
5. **logging.basicConfig(encoding='utf-8', force=True)** - ensures file handlers use UTF-8

---

## 🔍 Alternative Solutions

### Option 1: Set Windows Console to UTF-8 (Temporary)

```bash
# In CMD before running pytest
chcp 65001
python -m pytest tests/ -v
```

**Pros:** No code changes
**Cons:** Must run every session, affects entire console

### Option 2: Environment Variable (Session-wide)

```bash
# PowerShell
$env:PYTHONIOENCODING = "utf-8"
python -m pytest tests/ -v

# CMD
set PYTHONIOENCODING=utf-8
python -m pytest tests/ -v
```

**Pros:** No code changes
**Cons:** Must set for each session

### Option 3: pytest.ini Configuration

```ini
# pytest.ini
[pytest]
log_cli = true
log_cli_level = INFO
# Unfortunately, pytest doesn't have encoding config for console output
```

**Verdict:** ❌ Does not solve the problem

---

## 🏆 Best Practice (Recommended)

Use **Solution from above** (`conftest.py` fix) because:

✅ Works automatically for all developers
✅ No manual steps required
✅ CI/CD friendly (works in GitHub Actions, GitLab CI, etc.)
✅ Platform-specific (doesn't affect Linux/macOS)
✅ Graceful degradation (`errors='replace'` prevents crashes)

---

## 📚 References

- [Python io.TextIOWrapper](https://docs.python.org/3/library/io.html#io.TextIOWrapper)
- [PEP 529 - Change Windows filesystem encoding to UTF-8](https://peps.python.org/pep-0529/)
- [pytest Issue #2815 - UnicodeEncodeError on Windows](https://github.com/pytest-dev/pytest/issues/2815)

---

## ✅ Checklist for GrantService Project

- [x] Add Windows encoding fix to `tests/conftest.py`
- [x] Test with emoji and Russian text in logs
- [x] Verify pytest runs without encoding errors
- [x] Document fix in `docs/WINDOWS_ENCODING_FIX.md`
- [x] Add to `docs/TESTING-METHODOLOGY-GRANTSERVICE.md` (Phase 1)
- [ ] Add to project README.md (optional)
- [ ] Notify team in Telegram/Slack (optional)

---

**Fixed in:** Iteration 46 (2025-10-26)
**Tested on:** Windows 11, Python 3.12.2, pytest 7.4.3
**Status:** ✅ Production-ready
