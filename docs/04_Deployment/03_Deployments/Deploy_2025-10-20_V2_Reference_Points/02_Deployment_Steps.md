# Deployment Guide - Reference Points Framework V2

**Date:** 2025-10-20
**Target:** Production server 5.35.88.251
**Status:** ✅ Ready for deployment

---

## Prerequisites

- [x] Code pushed to GitHub (commit a9d7f88)
- [x] Qdrant running on production (localhost:6333)
- [x] knowledge_sections collection loaded
- [x] Telegram bot service configured

---

## Option 1: Automated Deployment (Recommended)

### On Production Server:

```bash
# SSH to server
ssh root@5.35.88.251

# Navigate to repo
cd /var/GrantService

# Pull latest
git pull origin master

# Run deployment script
chmod +x deploy_v2_to_production.sh
./deploy_v2_to_production.sh
```

This script will:
1. Pull latest code
2. Check dependencies
3. Verify files
4. Check Qdrant
5. Restart bot

---

## Option 2: Manual Deployment

### Step 1: Pull Code

```bash
ssh root@5.35.88.251
cd /var/GrantService
git pull origin master
```

### Step 2: Verify Files

```bash
# Check framework files
ls -la agents/reference_points/
ls -la agents/interactive_interviewer_agent_v2.py
ls -la telegram-bot/telegram_interactive_interview.py
ls -la telegram-bot/handlers/interactive_interview_handler.py
```

Expected output: All files present

### Step 3: Check Dependencies

```bash
pip list | grep qdrant-client
```

If missing:
```bash
pip install qdrant-client
```

### Step 4: Verify Qdrant

```bash
# Check Qdrant health
curl http://localhost:6333/healthz

# Check collection
curl http://localhost:6333/collections/knowledge_sections | jq '.result.status'
```

Expected: `"green"`

If collection missing:
```bash
python load_fpg_to_production.py
```

### Step 5: Restart Bot

```bash
systemctl restart grantservice-bot
systemctl status grantservice-bot
```

### Step 6: Check Logs

```bash
tail -f /var/log/grantservice-bot.log
```

Look for:
- `✅ InteractiveInterviewerAgentV2 initialized`
- `[OK] Qdrant connected`
- No errors

---

## Testing on Production

### Test 1: Bot Starts Successfully

```bash
systemctl status grantservice-bot
```

Expected: `active (running)`

### Test 2: Qdrant Connection

In bot logs:
```
[OK] Qdrant connected: localhost:6333
```

### Test 3: Start Interview

In Telegram:
```
/start
[Press: 🆕 Интервью V2 (Adaptive)]
```

Expected: Interview starts with first question

### Test 4: Complete Interview

Answer 10-15 questions, verify:
- Questions are contextual
- Progress shown every 3 questions
- Max 5 follow-up questions
- Audit score at the end

---

## Rollback Plan

If something goes wrong:

```bash
# Revert to previous version
cd /var/GrantService
git log --oneline | head -5  # Find previous commit
git revert HEAD

# Restart
systemctl restart grantservice-bot
```

---

## Monitoring

### Check Logs

```bash
# Live logs
tail -f /var/log/grantservice-bot.log

# Errors only
grep -i error /var/log/grantservice-bot.log

# Last 100 lines
tail -100 /var/log/grantservice-bot.log
```

### Check Qdrant Performance

```bash
curl http://localhost:6333/collections/knowledge_sections | jq '.result'
```

Monitor:
- `points_count` - should be 31
- `indexed_vectors_count` - should match points_count
- `status` - should be "green"

### Check Bot Performance

```bash
# Check if bot is running
systemctl is-active grantservice-bot

# Check resource usage
top -p $(pgrep -f telegram-bot)
```

---

## Common Issues

### Issue 1: Qdrant Connection Failed

**Symptoms:** `⚠️ Qdrant unavailable`

**Fix:**
```bash
systemctl start qdrant
systemctl status qdrant
```

### Issue 2: Module Not Found

**Symptoms:** `ModuleNotFoundError: No module named 'reference_points'`

**Fix:**
```bash
cd /var/GrantService
ls agents/reference_points/__init__.py
# If missing, pull again
git pull origin master
```

### Issue 3: Bot Won't Start

**Symptoms:** `systemctl status grantservice-bot` shows failed

**Fix:**
```bash
# Check logs
journalctl -u grantservice-bot -n 50

# Check Python errors
python telegram-bot/main.py  # Run manually to see errors
```

### Issue 4: V2 Button Not Appearing

**Symptoms:** Menu doesn't show V2 option

**Fix:**
```bash
# Verify main.py has integration
grep -n "start_interview_v2" telegram-bot/main.py

# If missing, pull again
git pull origin master
systemctl restart grantservice-bot
```

---

## Success Criteria

✅ Bot starts without errors
✅ Qdrant connected
✅ V2 interview button visible
✅ Interview starts and completes
✅ Audit score generated
✅ Data saved to database

---

## Post-Deployment

### Week 1: Monitor

- Check logs daily
- Track completion rates
- Monitor audit scores
- Collect user feedback

### Week 2: Analyze

- Compare V1 vs V2 metrics
- Audit score distribution
- Interview time
- User satisfaction

### Month 1: Optimize

- Adjust priorities if needed
- Fine-tune questions
- Update reference points
- Improve based on feedback

---

## Support

**If issues persist:**

1. Check documentation:
   - `IMPLEMENTATION_SUMMARY.md`
   - `TELEGRAM_INTEGRATION_GUIDE.md`
   - `QDRANT_SETUP_PRODUCTION.md`

2. Contact:
   - Nikolay Stepanov
   - Email: otinoff@gmail.com

---

**Created:** 2025-10-20
**Version:** 1.0
**Ready for deployment:** ✅ YES
