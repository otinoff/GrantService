# Post-Deployment Verification: Release XXX

**Release Number:** XXX
**Release Name:** [Feature/Fix Name]
**Verification Date:** YYYY-MM-DD
**Verification Time:** HH:MM
**Verified By:** [Name]

---

## 🎯 Verification Goals

1. **Smoke Tests:** Critical functionality works
2. **Regression Tests:** Existing features still work
3. **New Feature Tests:** New functionality works as expected
4. **Performance Tests:** No degradation in response times
5. **Stability Tests:** Bot remains stable over time

---

## ✅ Smoke Tests (Critical)

### Test 1: Bot is Running
**Time:** HH:MM

```bash
systemctl status grantservice-bot
```

**Expected:** Active (running)
**Actual:** [Paste status]
**Status:** ✅ PASS | ❌ FAIL
**Notes:**

---

### Test 2: Database Connection
**Time:** HH:MM

```bash
psql -U postgres -d grantservice -c "SELECT COUNT(*) FROM sessions;"
```

**Expected:** Returns count (no connection errors)
**Actual:** [Paste result]
**Status:** ✅ PASS | ❌ FAIL
**Notes:**

---

### Test 3: Bot Responds to /start
**Time:** HH:MM

**Actions:**
1. Open Telegram bot: `@GrantServiceBot`
2. Send `/start` command

**Expected Response:**
```
Привет! Я помогу вам создать грантовую заявку.
[Menu with buttons]
```

**Actual Response:**
```
[Paste actual response]
```

**Response Time:** [X] seconds
**Status:** ✅ PASS | ❌ FAIL
**Notes:**

---

### Test 4: Interview Start
**Time:** HH:MM

**Actions:**
1. Click "Начать интервью" or send command
2. Provide project name when asked

**Expected Response:**
```
Bot asks first interview question
```

**Actual Response:**
```
[Paste actual response]
```

**Response Time:** [X] seconds
**Status:** ✅ PASS | ❌ FAIL
**Notes:**

---

### Test 5: Complete Interview Question
**Time:** HH:MM

**Actions:**
1. Answer first question
2. Wait for next question or confirmation

**Expected Response:**
```
Bot acknowledges answer and asks next question
OR
Bot confirms completion if interview done
```

**Actual Response:**
```
[Paste actual response]
```

**Response Time:** [X] seconds
**Status:** ✅ PASS | ❌ FAIL
**Notes:**

---

## 🔄 Regression Tests (Existing Features)

### Test 6: InteractiveInterviewerAgentV2
**Time:** HH:MM

**Actions:**
1. Start new interview
2. Answer 3-5 questions
3. Observe question quality and context awareness

**Expected:**
- Questions are contextual
- No repetition
- Follow-ups make sense
- Database saves answers after each turn

**Actual:**
```
Question 1: [Paste]
Answer 1: [Paste]

Question 2: [Paste]
Answer 2: [Paste]

Question 3: [Paste]
Answer 3: [Paste]
```

**Status:** ✅ PASS | ❌ FAIL
**Issues:** [Any problems]

---

### Test 7: Auditor Agent (if applicable)
**Time:** HH:MM

**Actions:**
1. Complete interview
2. Wait for audit results

**Expected:**
- Audit completes successfully
- Provides feedback on interview answers
- Identifies gaps or issues

**Actual:**
```
[Paste audit results]
```

**Status:** ✅ PASS | ❌ FAIL | N/A
**Notes:**

---

### Test 8: Writer Agent (if applicable)
**Time:** HH:MM

**Actions:**
1. After successful audit
2. Trigger grant application generation

**Expected:**
- Writer generates application text
- Formatting is correct
- Content matches interview data

**Actual:**
```
[Paste sample of generated text or summary]
```

**Status:** ✅ PASS | ❌ FAIL | N/A
**Notes:**

---

## 🆕 New Feature Tests (Release-Specific)

### Test 9: [New Feature 1]
**Time:** HH:MM

**What's New:** [Brief description of new feature]

**Actions:**
[List test steps]

**Expected:**
[Expected behavior]

**Actual:**
```
[Paste actual results]
```

**Status:** ✅ PASS | ❌ FAIL | N/A
**Notes:**

---

### Test 10: [New Feature 2]
**Time:** HH:MM

**What's New:** [Brief description]

**Actions:**
[List test steps]

**Expected:**
[Expected behavior]

**Actual:**
```
[Paste actual results]
```

**Status:** ✅ PASS | ❌ FAIL | N/A
**Notes:**

---

## ⚡ Performance Tests

### Test 11: Response Times
**Time:** HH:MM

**Measurements:**

| Action | Expected | Actual | Status |
|--------|----------|--------|--------|
| /start command | < 2s | [X]s | ✅/❌ |
| First question | < 5s | [X]s | ✅/❌ |
| Answer processing | < 3s | [X]s | ✅/❌ |
| Interview completion | < 10s | [X]s | ✅/❌ |

**Overall Performance:** ✅ ACCEPTABLE | ⚠️ DEGRADED | ❌ UNACCEPTABLE
**Notes:**

---

### Test 12: Resource Usage
**Time:** HH:MM

```bash
# Memory usage
free -h

# CPU usage
top -b -n 1 | grep grantservice

# Disk usage
df -h
```

**Results:**
```
[Paste output]
```

**Compared to Baseline:**
- Memory: SAME | INCREASED | DECREASED
- CPU: SAME | INCREASED | DECREASED
- Disk: SAME | INCREASED | DECREASED

**Status:** ✅ NORMAL | ⚠️ ELEVATED | ❌ CRITICAL
**Notes:**

---

## 🔍 Log Analysis

### Test 13: Error Rate
**Time:** HH:MM

```bash
# Check for errors in last 100 lines
tail -n 100 /var/log/grantservice/bot.log | grep -i error

# Check for critical errors
tail -n 100 /var/log/grantservice/bot.log | grep -i critical
```

**Errors Found:** [Number]
**Critical Errors:** [Number]

**Error Summary:**
```
[Paste any errors found, or "No errors found"]
```

**Status:** ✅ CLEAN | ⚠️ WARNINGS | ❌ ERRORS
**Notes:**

---

### Test 14: Warning Analysis
**Time:** HH:MM

```bash
# Check for warnings
tail -n 200 /var/log/grantservice/bot.log | grep -i warning
```

**Warnings Found:** [Number]

**Warning Summary:**
```
[Paste any warnings, or "No warnings found"]
```

**Status:** ✅ CLEAN | ⚠️ MINOR | ❌ CONCERNING
**Notes:**

---

## 🧪 Edge Cases & Error Handling

### Test 15: Invalid Input Handling
**Time:** HH:MM

**Actions:**
1. Send invalid command
2. Send empty message during interview
3. Send very long message (>4000 chars)

**Expected:** Bot handles gracefully with error messages

**Results:**
- Invalid command: ✅ PASS | ❌ FAIL
- Empty message: ✅ PASS | ❌ FAIL
- Long message: ✅ PASS | ❌ FAIL

**Notes:**

---

### Test 16: Concurrent Users (if applicable)
**Time:** HH:MM

**Actions:**
Simulate 2-3 users using bot simultaneously

**Expected:** All users receive responses, no conflicts

**Results:**
- User 1: ✅ PASS | ❌ FAIL
- User 2: ✅ PASS | ❌ FAIL
- User 3: ✅ PASS | ❌ FAIL

**Notes:**

---

## 📊 Verification Summary

**Total Tests:** [X]
**Passed:** [X]
**Failed:** [X]
**N/A:** [X]

**Critical Tests Status:**
- Smoke Tests (1-5): ✅ ALL PASS | ❌ SOME FAILED
- Regression Tests (6-8): ✅ ALL PASS | ❌ SOME FAILED
- New Features (9-10): ✅ ALL PASS | ❌ SOME FAILED

**Overall Verification:** ✅ PASS | ⚠️ PASS WITH WARNINGS | ❌ FAIL

---

## 🚨 Issues Found

### Issue 1: [Issue Title]
**Severity:** LOW | MEDIUM | HIGH | CRITICAL
**Description:** [What's wrong]
**Impact:** [How it affects users]
**Action:** [What needs to be done]
**Assigned To:** [Name]
**Due Date:** [Date]

### Issue 2: [Issue Title]
**Severity:** LOW | MEDIUM | HIGH | CRITICAL
**Description:**
**Impact:**
**Action:**
**Assigned To:**
**Due Date:**

---

## 📈 24-Hour Monitoring Results

**Monitoring Period:** [Start Date/Time] - [End Date/Time]

### Metrics Observed

**Stability:**
- Uptime: [X]% (expected: >99%)
- Crashes: [Number]
- Restarts: [Number]

**Performance:**
- Avg Response Time: [X]s
- Peak Response Time: [X]s
- Slowest Endpoint: [Which]

**Errors:**
- Total Errors: [Number]
- Error Rate: [X]%
- Most Common Error: [Type]

**User Activity:**
- Total Users: [Number]
- Interviews Started: [Number]
- Interviews Completed: [Number]
- Completion Rate: [X]%

**Status:** ✅ STABLE | ⚠️ CONCERNING | ❌ UNSTABLE

---

## ✅ Final Decision

**Deployment Status:** ✅ SUCCESS | ⚠️ SUCCESS WITH ISSUES | ❌ FAILED

### Recommendations

**If SUCCESS:**
- [ ] Continue monitoring for 48 hours
- [ ] Close deployment ticket
- [ ] Update release notes
- [ ] Archive deployment docs

**If SUCCESS WITH ISSUES:**
- [ ] Create tickets for non-critical issues
- [ ] Plan fixes for next release
- [ ] Continue intensive monitoring
- [ ] Update known issues documentation

**If FAILED:**
- [ ] Execute rollback plan (see `02_DEPLOYMENT_LOG.md`)
- [ ] Investigate root cause
- [ ] Fix issues in development
- [ ] Re-test before next deployment attempt

---

## 📝 Sign-Off

**Verified By:** _________________________
**Date/Time:** _________________________
**Next Review:** [Date/Time]

---

**Notes:**
[Any additional observations, recommendations, or follow-up actions]
