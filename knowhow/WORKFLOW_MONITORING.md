# Workflow Monitoring - Progressive Checks

**Дата:** 2025-10-29
**Источник:** Iteration 64 - E2E Workflow Testing
**Статус:** ✅ Best Practice

---

## 🎯 Проблема

При запуске долгого workflow (15-25 минут):
- ❌ Ждём 5+ минут чтобы узнать что упало на старте
- ❌ Теряем время на повторные запуски
- ❌ Не видим прогресс

---

## ✅ Решение: Progressive Monitoring

### Strategy: Exponential Backoff Checks

```python
CHECK_INTERVALS = [
    10,    # 10 seconds - Fast fail (imports, DB connection)
    30,    # 30 seconds - Initialization complete
    60,    # 1 minute   - First cycle started
    120,   # 2 minutes  - First cycle progress
    300,   # 5 minutes  - Multiple cycles
]
```

---

## 📋 Implementation

### Option 1: Manual Checks (Simple)

```bash
# Launch workflow
ssh root@5.35.88.251 "cd /var/GrantService && \
  export PGHOST=localhost && \
  export PGPORT=5434 && \
  export PGDATABASE=grantservice && \
  export PGUSER=grantservice && \
  export PGPASSWORD='...' && \
  source venv/bin/activate && \
  nohup python scripts/e2e_synthetic_workflow.py --cycles 5 > /tmp/e2e.log 2>&1 &"

# Check 1: 10 seconds (Fast fail)
sleep 10
ssh root@5.35.88.251 "tail -50 /tmp/e2e.log | grep -E '(ERROR|Traceback|CRITICAL)'"
if [ $? -eq 0 ]; then
  echo "❌ FAILED at initialization!"
  exit 1
fi

# Check 2: 1 minute (Progress started)
sleep 50  # 10s already passed
ssh root@5.35.88.251 "tail -100 /tmp/e2e.log | grep -E '(CYCLE|STEP|✅)'"

# Check 3: 5 minutes (Multiple cycles)
sleep 240  # 1m already passed
ssh root@5.35.88.251 "tail -200 /tmp/e2e.log | grep 'CYCLE'"

# Final check: Process completed
ssh root@5.35.88.251 "ps aux | grep e2e_synthetic_workflow.py | grep -v grep"
```

### Option 2: Automated Script (Advanced)

```python
#!/usr/bin/env python3
"""
scripts/monitor_workflow.py - Progressive workflow monitoring
"""
import time
import subprocess
import sys

CHECK_INTERVALS = [10, 30, 60, 120, 300]  # seconds

def check_logs(log_path: str, check_num: int) -> bool:
    """Check logs for errors and progress"""
    cmd = f"ssh root@5.35.88.251 'tail -100 {log_path}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    logs = result.stdout

    # Check for errors
    if any(err in logs for err in ['ERROR', 'Traceback', 'CRITICAL', 'Failed']):
        print(f"❌ CHECK {check_num}: Errors found!")
        print(logs[-500:])  # Last 500 chars
        return False

    # Check for progress
    if check_num == 1:
        if "Initializing" not in logs:
            print(f"⚠️  CHECK {check_num}: Not started yet...")
            return False
    elif check_num == 2:
        if "CYCLE" not in logs:
            print(f"⚠️  CHECK {check_num}: No cycles started...")
            return False
    elif check_num >= 3:
        cycle_count = logs.count("CYCLE")
        print(f"✅ CHECK {check_num}: {cycle_count} cycles in progress")

    return True

def main():
    log_path = "/tmp/e2e_FINAL_v3.log"

    print("🚀 Starting progressive workflow monitoring...")
    print(f"📊 Check intervals: {CHECK_INTERVALS}")

    start_time = time.time()

    for i, interval in enumerate(CHECK_INTERVALS, 1):
        time.sleep(interval if i == 1 else interval - CHECK_INTERVALS[i-2])

        elapsed = int(time.time() - start_time)
        print(f"\n⏱️  CHECK {i} at {elapsed}s:")

        if not check_logs(log_path, i):
            print(f"❌ Workflow monitoring stopped at check {i}")
            sys.exit(1)

    print("\n✅ All checks passed! Workflow running normally.")
    print("💡 Continue monitoring manually or wait for completion.")

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Terminal 1: Launch workflow
python scripts/e2e_synthetic_workflow.py --cycles 5

# Terminal 2: Monitor progress
python scripts/monitor_workflow.py
```

---

## 🎯 Check Points

### Check 1: 10 seconds - Fast Fail

**What to check:**
- ✅ Process started
- ✅ No import errors
- ✅ DB connection successful
- ✅ Environment variables loaded

**Example output:**
```
2025-10-29 02:37:25,329 - INFO - ✅ Created user 999999001
2025-10-29 02:37:25,380 - INFO - CYCLE 1
```

**Red flags:**
```
ModuleNotFoundError: No module named 'agents'
psycopg2.OperationalError: password authentication failed
KeyError: 'PGPASSWORD'
```

### Check 2: 30-60 seconds - Initialization

**What to check:**
- ✅ First cycle started
- ✅ LLM connection working
- ✅ File generation started

**Example output:**
```
2025-10-29 02:37:25,471 - INFO - ✅ Токен GigaChat получен успешно
2025-10-29 02:37:51,957 - INFO - ✅ Anketa generated
2025-10-29 02:37:51,958 - INFO - STEP 2: AUDIT
```

### Check 3: 2-5 minutes - Progress

**What to check:**
- ✅ Multiple cycles running
- ✅ Files being generated
- ✅ No stuck processes

**Example output:**
```
CYCLE 1 ✅
CYCLE 2 ⏳
```

---

## 📊 When to Use

### ✅ USE Progressive Monitoring:

1. **Development/Debug** - экономит время при отладке
2. **CI/CD Pipelines** - быстрый feedback
3. **Long workflows (>10 min)** - экономит время
4. **Production deployments** - проверка что не сломали
5. **New features** - проверка интеграции

### ⚠️  DON'T NEED if:

1. **Short tasks (<1 min)** - overhead больше пользы
2. **Stable workflows** - если 100 раз работало, не нужно
3. **Fire-and-forget jobs** - если результат не срочен

---

## 🔗 Integration with Testing

### pytest Integration

```python
# tests/integration/test_e2e_workflow_monitored.py
import pytest
import time
from scripts.monitor_workflow import check_logs

@pytest.mark.slow
def test_e2e_workflow_with_monitoring():
    """Test E2E workflow with progressive monitoring"""

    # Launch workflow
    process = launch_workflow()

    # Progressive checks
    checks = [10, 30, 60]
    for i, interval in enumerate(checks, 1):
        time.sleep(interval if i == 1 else interval - checks[i-2])

        assert check_logs(f"/tmp/e2e_test_{process.pid}.log", i), \
            f"Check {i} failed at {interval}s"

    # Wait for completion
    process.wait(timeout=1800)  # 30 min max

    # Verify results
    assert verify_25_files(), "Not all 25 files generated"
```

---

## 📚 Related Knowhow

- `knowhow/DEPLOYMENT_SSH_PRACTICES.md` - SSH monitoring
- `knowhow/ITERATION_WORKFLOW.md` - Development workflow
- `cradle/TESTING-METHODOLOGY.md` - Testing best practices

---

## 💡 Best Practices

1. **Use exponential backoff** - не проверяем слишком часто
2. **Check different things** - на каждом этапе свои метрики
3. **Fail fast** - если 10s check упал, stop immediately
4. **Log everything** - чтобы понять где упало
5. **Automate for CI/CD** - manual checks для dev, automated для prod

---

## 🎓 Example: Iteration 64

**Real case:**
```bash
# Check 1: 10s
✅ Process started, DB connected

# Check 2: 60s
✅ CYCLE 1 STEP 1 complete
⏳ STEP 2 (AUDIT) running

# Check 3: 5m
✅ CYCLE 2 complete
⏳ CYCLE 3 running

# Result:
Saved 15 minutes vs waiting blindly
```

---

**Автор:** Claude Code
**Дата:** 2025-10-29
**Iteration:** 64
**Impact:** Development efficiency (saves 5-15 min per debug cycle)
**Status:** ✅ Recommended practice
