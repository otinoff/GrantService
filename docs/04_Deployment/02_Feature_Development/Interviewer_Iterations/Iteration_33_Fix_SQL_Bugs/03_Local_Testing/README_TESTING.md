# Iteration 33 - Testing Guide

**Date:** 2025-10-24
**Status:** Ready to test
**Deploy:** #7

---

## 🎯 Что Тестируем

### Fixes в Iteration 33:
1. ✅ ProductionWriter использует GigaChat-Max (tokens by package)
2. ✅ Database methods используют правильные колонки
3. ✅ Grant Handler проверяет правильные поля

### Critical Tests:
- [ ] GigaChat model = "GigaChat-Max"
- [ ] get_latest_completed_anketa() работает с telegram_id
- [ ] Grant generation работает end-to-end
- [ ] Нет SQL errors в логах

---

## 📂 Test Files

```
Iteration_33/03_Local_Testing/
├── test_iteration_33_local.py       ← Local test script
└── README_TESTING.md                ← This file

Deploy_07/02_Production_Testing/
└── test_iteration_33_production.py  ← Production test script
```

---

## 🖥️ LOCAL TESTING

### Prerequisites:

```bash
# Python 3.10+
python --version

# Dependencies installed
cd C:\SnowWhiteAI\GrantService
pip install -r requirements.txt

# Access to production database (5.35.88.251:5434)
```

### Run Local Test:

```bash
cd C:\SnowWhiteAI\GrantService_Project\Development\02_Feature_Development\Interviewer_Iterations\Iteration_33_Fix_SQL_Bugs\03_Local_Testing

python test_iteration_33_local.py
```

### Test Flow:

```
1. Test Database Methods (30 seconds)
   ├─ get_latest_completed_anketa()
   ├─ get_latest_grant_for_user()
   └─ get_user_grants()

2. Test ProductionWriter Init (10 seconds)
   ├─ Model = GigaChat-Max?
   └─ Expert Agent initialized?

3. Test Grant Generation (OPTIONAL - 60-180 seconds)
   ├─ Get anketa
   ├─ Generate grant via ProductionWriter
   ├─ Verify in database
   └─ Check metrics
```

### Expected Results:

```
✅ Database Methods:
  ✅ get_latest_completed_anketa: PASS (or NO_DATA)
  ✅ get_latest_grant_for_user: PASS (or NO_DATA)
  ✅ get_user_grants: PASS

✅ ProductionWriter Initialization:
  ✅ model_check: PASS (GigaChat-Max)
  ✅ expert_agent: PASS
  ✅ initialization: PASS

✅ Grant Generation (if run):
  ✅ anketa_retrieval: PASS
  ✅ generation: PASS
  ✅ database_save: PASS
  📊 duration_seconds: 60-180
  📊 character_count: 30000+
```

---

## 🌐 PRODUCTION TESTING

### Prerequisites:

```bash
# SSH access to production
ssh -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251

# Services running
systemctl status grantservice-bot
```

### Copy Test Script to Production:

**Option A: Git (preferred)**
```bash
# On local machine
cd C:\SnowWhiteAI\GrantService_Project
git add Development/03_Deployment/Deploy_07_SQL_Fixes/02_Production_Testing/
git commit -m "test: Add production E2E test for Deploy #7"
git push origin master

# On production server
ssh root@5.35.88.251
cd /var/GrantService
git pull origin master
```

**Option B: SCP**
```bash
# From local Windows
scp -i "C:\Users\Андрей\.ssh\id_rsa" ^
  "C:\SnowWhiteAI\GrantService_Project\Development\03_Deployment\Deploy_07_SQL_Fixes\02_Production_Testing\test_iteration_33_production.py" ^
  root@5.35.88.251:/var/GrantService/tests/
```

### Run Production Test:

```bash
# SSH to production
ssh -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251

# Go to project dir
cd /var/GrantService

# Activate virtualenv
source venv/bin/activate

# Run test
python tests/test_iteration_33_production.py

# Or directly without venv (using system python)
python3 tests/test_iteration_33_production.py
```

### Test Results Location:

```bash
# Logs directory
/var/GrantService/logs/e2e_test_deploy07.log
/var/GrantService/logs/deploy07_test_results_*.log

# View results
tail -f /var/GrantService/logs/e2e_test_deploy07.log
```

---

## 🧪 Test Scenarios

### Scenario 1: Quick Smoke Test (2 minutes)

**Goal:** Verify fixes without full generation

```bash
# Local or Production
python test_iteration_33_[local|production].py

# When prompted for full generation:
Run full grant generation? [y/N]: N

# Check results:
✅ Model = GigaChat-Max
✅ SQL queries work
✅ No errors
```

**Success Criteria:**
- Model check: PASS
- All SQL queries: PASS or NO_DATA
- No exceptions

---

### Scenario 2: Full E2E Test (3-5 minutes)

**Goal:** Complete grant generation test

```bash
python test_iteration_33_[local|production].py

# When prompted:
Run full grant generation? [y/N]: y

# Wait 60-180 seconds...
```

**Success Criteria:**
- Anketa retrieved: ✅
- Grant generated: ✅ (30K+ characters)
- Grant saved to DB: ✅
- Duration: 60-180 seconds
- No errors in logs

---

### Scenario 3: Telegram Bot Test (5 minutes)

**Goal:** Test via actual bot commands

```bash
# 1. Open Telegram
# 2. Find @grant_service_bot
# 3. Send commands:

/start
# Complete interview (10+ questions)

/generate_grant
# Wait 60-180 seconds

/get_grant
# Should display grant

/list_grants
# Should list grants
```

**Success Criteria:**
- Interview completes: ✅
- Grant generates: ✅
- No SQL errors in logs
- Grant displayed correctly

**Check logs:**
```bash
ssh root@5.35.88.251
sudo journalctl -u grantservice-bot --since "5 minutes ago" | grep -i error
```

---

## 📊 Verification Checklist

### After Local Test:

- [ ] Model = GigaChat-Max confirmed
- [ ] No SQL "column does not exist" errors
- [ ] Database methods return data (or NO_DATA if no grants)
- [ ] ProductionWriter initializes successfully

### After Production Test:

- [ ] Services running stable
- [ ] No errors in bot logs
- [ ] Test script completed successfully
- [ ] Grant generation works (if tested)

### After Bot Test:

- [ ] Interview completes
- [ ] /generate_grant works
- [ ] /get_grant displays grant
- [ ] /list_grants shows grants
- [ ] No errors in journalctl

---

## 🐛 Troubleshooting

### Error: "column user_id does not exist"

**Status:** ❌ SHOULD NOT HAPPEN (fixed in Iteration 33)

**If you see this:**
```bash
# Check deployed code version
cd /var/GrantService
git log -1

# Should see commit d653c24 (Iteration 33 fixes)
# If not:
git pull origin master
sudo systemctl restart grantservice-bot
```

### Error: Model is "GigaChat" instead of "GigaChat-Max"

**Status:** ❌ SHOULD NOT HAPPEN (fixed in Iteration 33)

**If you see this:**
```python
# Check production_writer.py line 188
# Should be:
self.llm_client = UnifiedLLMClient(provider=llm_provider, model="GigaChat-Max")

# If wrong:
cd /var/GrantService
git pull origin master
sudo systemctl restart grantservice-bot
```

### Error: Database connection failed

**Check database:**
```bash
# On production
systemctl status postgresql

# Test connection
PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q' psql -h localhost -p 5434 -U grantservice -d grantservice -c "SELECT 1;"
```

### Error: Qdrant connection failed

**Check Qdrant:**
```bash
# Check if Qdrant is running
curl http://5.35.88.251:6333/collections

# Should return JSON with collections
```

---

## 📝 Test Results Template

```markdown
# Test Results - Iteration 33

**Date:** 2025-10-24
**Tester:** [Your Name]
**Environment:** [Local / Production]

## Local Test Results:

- [ ] Model Configuration: [PASS / FAIL]
- [ ] Database Methods: [PASS / FAIL]
- [ ] Grant Generation: [PASS / FAIL / SKIPPED]

## Production Test Results:

- [ ] Model Configuration: [PASS / FAIL]
- [ ] SQL Queries: [PASS / FAIL]
- [ ] Grant Generation: [PASS / FAIL / SKIPPED]

## Bot Test Results:

- [ ] Interview: [PASS / FAIL]
- [ ] /generate_grant: [PASS / FAIL]
- [ ] /get_grant: [PASS / FAIL]
- [ ] /list_grants: [PASS / FAIL]

## Issues Found:

[List any issues]

## Overall Status:

✅ PASS / ❌ FAIL

## Notes:

[Any additional notes]
```

---

## 🔗 Related Documentation

- **Iteration 33 Plan:** `Iteration_33/01_Plan.md`
- **Implementation Complete:** `Iteration_33/02_Implementation_Complete.md`
- **Deploy #7 Info:** `Deploy_07/01_Deploy_Info.md`
- **Workflow Algorithm:** `Development/ITERATION_WORKFLOW_ALGORITHM.md`

---

## 📞 Quick Commands

### Local:
```bash
cd C:\SnowWhiteAI\GrantService_Project\Development\02_Feature_Development\Interviewer_Iterations\Iteration_33_Fix_SQL_Bugs\03_Local_Testing
python test_iteration_33_local.py
```

### Production:
```bash
ssh -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251
cd /var/GrantService
python3 tests/test_iteration_33_production.py
```

### Check Logs:
```bash
ssh -i "C:\Users\Андрей\.ssh\id_rsa" root@5.35.88.251
sudo journalctl -u grantservice-bot -f
```

---

**Status:** ✅ READY TO TEST
**Next:** Run tests and document results
