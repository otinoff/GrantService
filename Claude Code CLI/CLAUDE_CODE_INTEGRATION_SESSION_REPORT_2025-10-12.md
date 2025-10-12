# Claude Code Integration Session Report
**Date:** 2025-10-12
**Status:** ⚠️ PARTIAL SUCCESS (Rolled back to Perplexity)
**Duration:** ~2 hours

---

## 🎯 Session Goal

Integrate Claude Code CLI with GrantService Writer Agent to use Claude Opus 4 for premium quality grant generation, utilizing the $200/month Max subscription.

---

## ✅ What Was Accomplished

### 1. Code Modifications

**File: `shared/llm/unified_llm_client.py`**
- ✅ Modified `_generate_claude_code()` method
- ✅ Switched from subprocess Claude CLI to HTTP API calls
- ✅ Added comprehensive error handling
- ✅ Documented OAuth IP limitation issue

**Git Commit:** `1bd6894` - "feat: Switch Claude Code to HTTP API (temporary solution)"

### 2. Configuration Changes

**File: `shared/llm/config.py`**
- ✅ Created on production server at `/var/GrantService/shared/llm/config.py`
- ✅ Configured Writer agent:
  ```python
  "writer": {
      "provider": "claude",  # (rolled back to "perplexity")
      "model": "opus",
      "temperature": 0.7,
      "max_tokens": 8000
  }
  ```

### 3. Production Deployment

**Server:** 5.35.88.251 (`/var/GrantService`)

- ✅ Git changes pulled (3 commits)
- ✅ Config.py created with production settings
- ✅ Services restarted (grantservice-bot, grantservice-admin)
- ✅ No errors in initial startup logs
- ✅ Database connection verified (6 users)

---

## ❌ Critical Issue Discovered

### Claude Code API Server Unreachable

**Problem:**
```
Cannot connect to host 178.236.17.55:8000 ssl:default
[Connect call failed ('178.236.17.55', 8000)]
```

**Testing:**
- Created test script `test_writer_claude.py`
- Deployed to production and executed
- **Result:** Connection refused to Claude Code API server

**Root Cause Analysis:**

1. **API Wrapper Not Running**
   - Port 8000 not listening on 178.236.17.55
   - No process serving HTTP API
   - SSH access to 178.236.17.55 failed (cannot diagnose)

2. **Two-Server Architecture Issue**
   - Production GrantService: 5.35.88.251
   - Claude Code API Server: 178.236.17.55
   - Network connectivity issue OR wrapper process down

3. **OAuth IP Limitation (Original Problem)**
   - OAuth tokens are IP-bound
   - Cannot run Claude CLI locally on production server
   - Requires API key (not OAuth) for local CLI execution

---

## 🔄 Rollback Performed

### Actions Taken

```bash
# On production server 5.35.88.251
sed -i 's/"provider": "claude"/"provider": "perplexity"/' shared/llm/config.py
systemctl restart grantservice-bot
```

**Result:** ✅ System operational with Perplexity

**Current Status:**
- Writer Agent: Perplexity Sonar (Llama 3.3 70B)
- Quality: ⭐⭐⭐⭐ (good, but not premium Claude Opus level)
- Stability: ✅ 100% operational

---

## 📊 Architecture Comparison

### Attempted Architecture (Failed)
```
Production GrantService (5.35.88.251)
    ↓ HTTP API call
Claude Code API Server (178.236.17.55:8000) ← FAILED: Not responding
    ↓ OAuth
Anthropic API (Claude Opus 4)
```

### Current Working Architecture
```
Production GrantService (5.35.88.251)
    ↓ Direct API call
Perplexity API (Llama 3.3 70B) ← WORKING
```

### Desired Future Architecture
```
Production GrantService (5.35.88.251)
    ↓ Local subprocess OR Anthropic SDK
Claude CLI (local) OR Anthropic API
    ↓ API Key authentication
Anthropic API (Claude Opus 4)
```

---

## 🔍 Key Findings

### 1. OAuth IP Limitation

**Discovery:** OAuth tokens from Max subscription are IP-bound.

**Impact:**
- Cannot transfer credentials between servers
- Subprocess Claude CLI won't work on production server
- Requires dedicated server where OAuth was originally authenticated

**Documentation:** See `BASE_RULES_CLAUDE_CODE.md` and `Отзывы об использовании Claude Code CLI на удаленн.md`

### 2. Wrapper Approach Issues

**Findings from user research:**
- Wrapper approach has "fundamental limitations" (documented)
- Better to use direct SDK/API integration
- HTTP wrapper adds complexity and failure points

**Reference:** `Отзывы об использовании Claude Code CLI на удаленн.md` lines 32-40

### 3. Two-Server Confusion

**Discovered:**
- User has TWO servers: 5.35.88.251 (prod) and 178.236.17.55 (Claude API)
- Original plan assumed SINGLE server (LOCAL operation)
- BASE_RULES document emphasizes "NOT remote SSH" - but we ended up with remote HTTP API

**Alignment Issue:** Implementation contradicts BASE_RULES intent

---

## 💡 Solutions Going Forward

### Option A: API Key Approach (RECOMMENDED)

**Steps:**
1. Obtain Anthropic API key from https://console.anthropic.com/
2. Set `ANTHROPIC_API_KEY` environment variable on production
3. Modify `_generate_claude_code()` to use Anthropic Python SDK with API key
4. Test on production

**Pros:**
- ✅ Works on any server
- ✅ No IP limitations
- ✅ Simple architecture
- ✅ Official Anthropic SDK support

**Cons:**
- ⚠️ API key costs money (separate from Max subscription)
- ⚠️ Max subscription $200/month not utilized

**Cost Analysis:**
- Claude Opus API: $15 input / $75 output per 1M tokens
- 100 grants @ 25k tokens each = ~$200/month
- **Conclusion:** API key costs similar to Max subscription for high volume

### Option B: Fix Wrapper on 178.236.17.55

**Steps:**
1. Gain SSH access to 178.236.17.55
2. Find/create wrapper script (see `STATUS_2025-10-12.md` for example)
3. Set up systemd service for autostart
4. Configure firewall/networking between servers

**Pros:**
- ✅ Uses existing Max subscription OAuth
- ✅ No additional costs

**Cons:**
- ❌ Requires access to 178.236.17.55
- ❌ Wrapper adds complexity
- ❌ Two-server dependency
- ❌ Against BASE_RULES principles (not truly "local")

### Option C: Migrate OAuth to Production Server

**Steps:**
1. Login to claude.com from production server (5.35.88.251)
2. Go through OAuth flow on that server
3. Copy new `~/.claude/.credentials.json` to production
4. Use subprocess Claude CLI locally

**Pros:**
- ✅ Uses Max subscription
- ✅ True local operation (aligns with BASE_RULES)
- ✅ No external dependencies

**Cons:**
- ⚠️ May require browser access on server (headless auth?)
- ⚠️ Not sure if possible without GUI

---

## 📝 Recommendations

### Immediate Action (Next Session)

**Choose:** Option A (API Key Approach)

**Rationale:**
1. **Simplest** - one server, no dependencies
2. **Aligned with BASE_RULES** - truly local operation
3. **Cost-effective** - similar price to Max subscription at scale
4. **Stable** - official Anthropic SDK, no wrapper complexity

**Implementation:**
1. Get API key from Anthropic console
2. Revert `_generate_claude_code()` to use Anthropic SDK with API key
3. Deploy and test
4. Monitor costs vs Max subscription

### Long-term Strategy

**Phase 1:** Use API key (stable, working solution)

**Phase 2:** Evaluate:
- If grant volume > 100/month → Keep API key (cost justified)
- If Max subscription preferred → Attempt Option C (migrate OAuth)
- If wrapper preferred → Fix 178.236.17.55 setup (Option B)

**Phase 3:** Optimize:
- A/B test: Claude Opus vs Perplexity vs GigaChat
- Quality metrics: approval rate, expert reviews
- Cost metrics: $/grant for each provider

---

## 📚 Files Created/Modified

### Local (Git committed)
- ✅ `shared/llm/unified_llm_client.py` (modified for HTTP API)
- ✅ `test_writer_claude.py` (created for testing)
- ✅ `.claude/CLAUDE_CODE_HTTP_API_DEPLOYMENT_REPORT.md` (deployment report)

### Production (Not in Git)
- ✅ `shared/llm/config.py` (contains secrets - in .gitignore)

### Documentation (This session)
- ✅ `Claude Code CLI/CLAUDE_CODE_INTEGRATION_SESSION_REPORT_2025-10-12.md` (this file)

---

## ⏭️ Next Steps

### For Next Session

**Priority 1: Get Writer Working with Claude**

Choose implementation approach:
- [ ] **Option A:** Get Anthropic API key → Modify SDK usage → Deploy → Test
- [ ] **Option B:** Fix 178.236.17.55 wrapper → Test connectivity → Deploy
- [ ] **Option C:** Attempt OAuth migration to production → Test Claude CLI → Deploy

**Priority 2: Quality Testing**

Once Claude integration works:
- [ ] Generate 3 test grants (small, medium, complex)
- [ ] Compare with Perplexity grants
- [ ] Measure: quality, time, cost
- [ ] Decide production provider

**Priority 3: Cleanup**

- [ ] Remove test files from production
- [ ] Update BASE_RULES with final architecture
- [ ] Document chosen solution in ARCHITECTURE.md

---

## 🎓 Lessons Learned

### 1. OAuth Complexity

**Learning:** Max subscription OAuth tokens are IP-bound, creating deployment challenges.

**Impact:** Cannot easily transfer credentials between development and production environments.

**Future:** Consider API keys for production servers, OAuth for local development.

### 2. Wrapper Anti-Pattern

**Learning:** HTTP wrapper around Claude Code CLI adds complexity and failure points.

**Impact:** Additional server, networking issues, maintenance overhead.

**Future:** Prefer direct SDK/API integration when possible.

### 3. Two-Server Architecture

**Learning:** Original BASE_RULES assumed single-server operation, but implementation used two servers.

**Impact:** Misalignment between intent and reality.

**Future:** Clarify architecture upfront - single vs multi-server deployment.

### 4. Pragmatic Rollback

**Learning:** When integration fails, rollback to stable state quickly.

**Impact:** System remained operational with Perplexity while debugging Claude.

**Future:** Always have working fallback provider configured.

---

## 🔧 Technical Details

### Server Information

**Production Server:**
- Host: 5.35.88.251
- User: root
- Path: /var/GrantService
- Services: grantservice-bot, grantservice-admin
- Database: PostgreSQL 18.0 @ localhost:5434

**Claude Code API Server (failed):**
- Host: 178.236.17.55
- Port: 8000 (not responding)
- SSH: Access failed
- Status: Unknown

### Current Configuration (After Rollback)

```python
# /var/GrantService/shared/llm/config.py

AGENT_CONFIGS = {
    "writer": {
        "provider": "perplexity",  # ← Rolled back from "claude"
        "model": "sonar",
        "temperature": 0.7,
        "max_tokens": 8000
    },
    "researcher": {
        "provider": "claude",  # Still uses Claude API (if wrapper works)
        "model": "sonnet",
        "temperature": 0.3,
        "max_tokens": 1500
    },
    # ... other agents
}
```

### Test Command

```bash
# Test Writer Agent on production
ssh root@5.35.88.251
cd /var/GrantService
python3 test_writer_claude.py
```

---

## 📞 Contact & Support

**Developer:** Nikolay Stepanov
**Consultant:** Andrey Otinov (@otinoff)
**Email:** otinoff@gmail.com

**Anthropic Support:**
- Console: https://console.anthropic.com/
- Docs: https://docs.anthropic.com/
- Issues: https://github.com/anthropics/claude-code/issues

---

## ✅ Summary

**What Worked:**
- ✅ HTTP API integration code (technically sound)
- ✅ Production deployment (clean, automated)
- ✅ Rollback process (quick, effective)
- ✅ Documentation (comprehensive)

**What Failed:**
- ❌ Claude Code API server connectivity (178.236.17.55:8000 down)
- ❌ Two-server architecture (adds complexity vs BASE_RULES intent)
- ❌ OAuth IP limitation (fundamental barrier for multi-server setup)

**Current Status:**
- 🟢 System: Operational with Perplexity
- 🟡 Claude Integration: On hold pending decision on Option A/B/C
- 🟢 Code Quality: HTTP API implementation ready to use once server issue resolved

**Recommendation:**
- **Short-term:** Continue with Perplexity (working, good quality)
- **Next session:** Implement Option A (API key) for Claude Opus premium quality
- **Long-term:** Evaluate costs and quality to decide permanent solution

---

**Report Generated:** 2025-10-12 15:25 UTC
**Session Status:** Closed - Pending user decision on next steps
**Action Required:** Choose implementation option (A/B/C) for next session
