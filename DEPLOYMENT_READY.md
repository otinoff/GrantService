# 🚀 PRODUCTION WRITER - READY FOR DEPLOYMENT
**Date:** 2025-10-24
**Server:** 5.35.88.251 (Beget VPS)
**Status:** ✅ CODE READY - MANUAL DEPLOYMENT REQUIRED

---

## 📦 ЧТО ПОДГОТОВЛЕНО

### ✅ Code Files

| File | Location | Size | Status |
|------|----------|------|--------|
| production_writer.py | `agents/` | 19 KB | ✅ Ready |
| 014_update_grants_for_production_writer.sql | `database/migrations/` | ~5 KB | ✅ Ready |
| requirements_production_writer.txt | root | 400 bytes | ✅ Ready |
| deploy_production_writer.sh | root | ~2 KB | ✅ Ready |
| DEPLOYMENT_READY.md | root | (this file) | ✅ Ready |

### ✅ Migration Summary

**Migration 014** modifies `grants` table:
- ✅ Makes `research_id` NULLABLE (allows ProductionWriter without Researcher)
- ✅ Adds 9 new columns:
  - `character_count` (grant length)
  - `word_count` (word count)
  - `sections_generated` (default 10)
  - `duration_seconds` (generation time)
  - `qdrant_queries` (vector DB queries count)
  - `sent_to_user_at` (when sent to user)
  - `admin_notified_at` (when admins notified)
  - `user_approved` (approval flag)
  - `approved_at` (approval timestamp)
- ✅ Adds 4 new indexes
- ✅ Updates status constraint (adds 'pending', 'sent_to_user')

---

## 🚀 DEPLOYMENT ИНСТРУКЦИИ

### Вариант 1: Автоматический deployment (GitHub Actions)

```bash
# Локально
cd C:\SnowWhiteAI\GrantService

# 1. Проверить изменения
git status

# Должно показать:
# - agents/production_writer.py
# - database/migrations/014_update_grants_for_production_writer.sql
# - requirements_production_writer.txt
# - deploy_production_writer.sh
# - DEPLOYMENT_READY.md

# 2. Commit changes
git add agents/production_writer.py
git add database/migrations/014_update_grants_for_production_writer.sql
git add requirements_production_writer.txt
git add deploy_production_writer.sh
git add DEPLOYMENT_READY.md

git commit -m "feat: Add ProductionWriter for automated grant generation

- Add production_writer.py (19 KB) to agents/
- Migration 014: Update grants table for ProductionWriter
  - Make research_id nullable
  - Add 9 new columns for metrics tracking
  - Add 4 new indexes
- Add requirements_production_writer.txt
- Add deploy_production_writer.sh automated deployment script

ProductionWriter generates grants without Researcher phase:
- 10 sections
- ~44,000 characters
- ~130 seconds generation time
- Qdrant integration for FPG requirements
- 100% FPG compliance

Ready for production deployment on 5.35.88.251
"

# 3. Push to trigger GitHub Actions
git push origin main

# GitHub Actions will automatically:
# ✓ Stop services
# ✓ Pull latest code
# ✓ Restore config/.env
# ✓ Start services

# 4. Manual migration on server (GitHub Actions doesn't run migrations)
ssh root@5.35.88.251
cd /var/GrantService
./deploy_production_writer.sh
```

---

### Вариант 2: Manual deployment (без GitHub Actions)

```bash
# 1. SSH на production
ssh root@5.35.88.251

# 2. Navigate to project
cd /var/GrantService

# 3. Pull latest code
git pull origin main

# 4. Run deployment script
./deploy_production_writer.sh

# Script will:
# ✓ Backup database
# ✓ Apply migration 014
# ✓ Install dependencies
# ✓ Verify ProductionWriter
# ✓ Restart services
```

---

## 🧪 POST-DEPLOYMENT TESTING

### Test 1: Verify Migration

```bash
# SSH на production
ssh root@5.35.88.251

# Check grants table structure
PGPASSWORD=${DB_PASSWORD} psql -h localhost -p 5434 -U grantservice -d grantservice -c "\d grants"

# Expected: research_id is nullable, new columns exist
```

### Test 2: Verify ProductionWriter Import

```bash
cd /var/GrantService
source venv/bin/activate

python3 -c "
from agents.production_writer import ProductionWriter
print('✓ ProductionWriter imported successfully')
"
```

### Test 3: Verify Qdrant Connection

```bash
python3 -c "
from qdrant_client import QdrantClient
client = QdrantClient(host='5.35.88.251', port=6333)
collections = client.get_collections()
print(f'✓ Qdrant: {len(collections.collections)} collections')
print([c.name for c in collections.collections])
"

# Expected: ['knowledge_sections']
```

### Test 4: Check Services Status

```bash
sudo systemctl status grantservice-bot
sudo systemctl status grantservice-admin

# Both should be active (running)
```

---

## ⚠️ ВАЖНО: Telegram Bot Integration

**ProductionWriter готов, но НЕ ИНТЕГРИРОВАН в Telegram Bot!**

Нужно выполнить:

### Step 1: Создать grant_handler.py

```bash
# На production сервере
cd /var/GrantService/telegram-bot/handlers
nano grant_handler.py

# Скопировать код из:
# C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\CORRECTED_PRODUCTION_DEPLOYMENT.md
# Phase 3, Section 3.1
```

### Step 2: Зарегистрировать handler в unified_bot.py

```python
# В telegram-bot/unified_bot.py

from handlers.grant_handler import register_grant_handlers

# В main():
def main():
    # ... existing code ...

    # Register grant handlers
    register_grant_handlers(application)

    # ... existing code ...
```

### Step 3: Добавить DB methods

```python
# В database wrapper (найти DB класс)

def get_anketa_by_id(self, anketa_id: str) -> Dict:
    """Load anketa by anketa_id from sessions table"""
    # Implementation...

def save_grant(
    self,
    grant_id: str,
    anketa_id: str,
    user_id: int,
    grant_content: str,
    character_count: int,
    ...
) -> int:
    """Save grant to grants table"""
    # Implementation...
```

### Step 4: Test Integration

```bash
# В Telegram Bot
/generate_grant <test_anketa_id>

# Expected:
# ✓ ProductionWriter generates grant
# ✓ Saved to grants table
# ✓ File sent to user
# ✓ Admin notification sent
```

---

## 📊 MONITORING ПОСЛЕ DEPLOYMENT

### Check Logs

```bash
# Bot logs
journalctl -u grantservice-bot -f | grep "ProductionWriter"

# Admin panel logs
journalctl -u grantservice-admin -f
```

### Check Database

```sql
-- Connect to PostgreSQL
PGPASSWORD=${DB_PASSWORD} psql -h localhost -p 5434 -U grantservice -d grantservice

-- Check grants created by ProductionWriter
SELECT
    grant_id,
    anketa_id,
    character_count,
    duration_seconds,
    sections_generated,
    qdrant_queries,
    status,
    created_at
FROM grants
WHERE research_id IS NULL  -- ProductionWriter grants
ORDER BY created_at DESC
LIMIT 10;

-- Check metrics
SELECT
    COUNT(*) as total_grants,
    AVG(character_count) as avg_chars,
    AVG(duration_seconds) as avg_duration,
    MIN(character_count) as min_chars,
    MAX(character_count) as max_chars
FROM grants
WHERE research_id IS NULL
  AND created_at > NOW() - INTERVAL '7 days';
```

---

## ✅ SUCCESS CRITERIA

После deployment проверить:

| Check | Expected | Command |
|-------|----------|---------|
| Migration applied | research_id nullable | `\d grants` в psql |
| ProductionWriter imported | No errors | `python3 -c "from agents.production_writer import ProductionWriter"` |
| Qdrant connected | knowledge_sections exists | `curl http://5.35.88.251:6333/collections/knowledge_sections` |
| Services running | active (running) | `systemctl status grantservice-bot` |

---

## 🚨 ROLLBACK PLAN

Если что-то пошло не так:

```bash
# 1. SSH на production
ssh root@5.35.88.251
cd /var/GrantService

# 2. Restore database from backup
BACKUP_FILE=$(ls -t database/backups/grantservice_backup_*.sql | head -1)
echo "Restoring from: $BACKUP_FILE"

PGPASSWORD=${DB_PASSWORD} psql -h localhost -p 5434 -U grantservice -d grantservice < "$BACKUP_FILE"

# 3. Rollback code
git log --oneline -5  # Find previous commit
git reset --hard <previous_commit_hash>

# 4. Restart services
sudo systemctl restart grantservice-bot
sudo systemctl restart grantservice-admin

# 5. Verify
sudo systemctl status grantservice-bot
```

---

## 📞 SUPPORT

### Если возникли проблемы:

1. **Check logs:**
   ```bash
   journalctl -u grantservice-bot -f
   ```

2. **Check migration:**
   ```bash
   PGPASSWORD=${DB_PASSWORD} psql -h localhost -p 5434 -U grantservice -d grantservice -c "\d grants"
   ```

3. **Check ProductionWriter:**
   ```bash
   python3 -c "from agents.production_writer import ProductionWriter; print('OK')"
   ```

4. **Rollback (см. выше)**

---

## 📚 DOCUMENTATION

- **Full Deployment Plan:** `C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\CORRECTED_PRODUCTION_DEPLOYMENT.md`
- **Gap Analysis:** `C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\DEPLOYMENT_GAP_ANALYSIS.md`
- **Iteration 31 Report:** `C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\reports\Iteration_31_FINAL_REPORT.md`
- **Test Results:** `C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\test_results\production_writer_*/`

---

## 🎯 NEXT STEPS (по приоритету)

### Priority 1: Deploy Database & Code (сейчас)

```bash
# Выбрать вариант deployment:
# Option 1: git push + manual migration
# Option 2: manual deployment

# Estimated time: 15-30 минут
```

### Priority 2: Telegram Bot Integration (после deployment)

```bash
# 1. Создать grant_handler.py
# 2. Добавить DB methods
# 3. Зарегистрировать handler
# 4. Test

# Estimated time: 1 час
```

### Priority 3: Testing & Monitoring (после integration)

```bash
# 1. Manual generation test
# 2. Check metrics
# 3. Monitor logs
# 4. User feedback

# Estimated time: 30 минут
```

**Total deployment time:** ~2 часа

---

**Prepared by:** Claude Code
**Date:** 2025-10-24
**Status:** ✅ CODE READY - AWAITING DEPLOYMENT
**Production Server:** 5.35.88.251 (Beget VPS)
