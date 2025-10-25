# 🎯 DEPLOYMENT RESUME PLAN
## Четкий план для продолжения работы

**Дата создания:** 2025-10-24 10:55
**Статус:** ✅ CODE READY - AWAITING GIT PUSH
**Production Server:** 5.35.88.251 (Beget VPS)

---

## ✅ ЧТО УЖЕ СДЕЛАНО

### 1. Database Migration - ГОТОВА ✅

**Файл:** `C:\SnowWhiteAI\GrantService\database\migrations\014_update_grants_for_production_writer.sql`

**Что делает:**
- Makes `research_id` NULLABLE в таблице `grants`
- Добавляет 9 новых колонок для ProductionWriter
- Создает 4 новых индекса
- Обновляет constraint для status

**Статус:** ✅ Файл создан, добавлен в git staging

---

### 2. ProductionWriter Code - ГОТОВ ✅

**Файл:** `C:\SnowWhiteAI\GrantService\agents\production_writer.py` (19 KB)

**Что умеет:**
- Генерирует 10 секций
- ~44,000 символов за ~130 секунд
- Qdrant integration (5.35.88.251:6333)
- 100% FPG compliance
- Работает БЕЗ Researcher

**Статус:** ✅ Скопирован из `C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\lib\production_writer.py`, добавлен в git staging

---

### 3. Dependencies - ГОТОВЫ ✅

**Файл:** `C:\SnowWhiteAI\GrantService\requirements_production_writer.txt`

**Содержит:**
```
qdrant-client==1.7.0
sentence-transformers==2.2.2
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

**Статус:** ✅ Создан, добавлен в git staging

---

### 4. Deployment Script - ГОТОВ ✅

**Файл:** `C:\SnowWhiteAI\GrantService\deploy_production_writer.sh` (executable)

**Что делает:**
1. Backup PostgreSQL database
2. Apply migration 014
3. Install dependencies (requirements_production_writer.txt)
4. Verify ProductionWriter import
5. Verify Qdrant connection
6. Restart services (grantservice-bot, grantservice-admin)

**Статус:** ✅ Создан, chmod +x, добавлен в git staging

---

### 5. Documentation - ГОТОВА ✅

**Файлы:**
- `C:\SnowWhiteAI\GrantService\DEPLOYMENT_READY.md` - deployment guide
- `C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\DEPLOYMENT_DONE.md` - summary
- `C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\DEPLOYMENT_GAP_ANALYSIS.md` - gap analysis

**Статус:** ✅ Все документы созданы

---

## 🎯 ЧТО НУЖНО СДЕЛАТЬ ДАЛЬШЕ

### STEP 1: Git Commit & Push (2 минуты)

**Где:** `C:\SnowWhiteAI\GrantService`

**Git Status:**
```
Changes to be committed:
  new file:   DEPLOYMENT_READY.md
  new file:   agents/production_writer.py
  new file:   database/migrations/014_update_grants_for_production_writer.sql
  new file:   deploy_production_writer.sh
  new file:   requirements_production_writer.txt
```

**Команды:**

```bash
cd C:\SnowWhiteAI\GrantService

# Commit
git commit -m "feat: Add ProductionWriter for automated grant generation

- Add production_writer.py (19 KB) to agents/
  * Generates 10-section grants (~44K chars in ~130s)
  * Qdrant integration for FPG requirements
  * 100% FPG compliance
  * No Researcher required

- Migration 014: Update grants table
  * Make research_id nullable (allows ProductionWriter)
  * Add 9 new columns for metrics
  * Add 4 new indexes for performance

- Add deployment automation
  * requirements_production_writer.txt
  * deploy_production_writer.sh
  * DEPLOYMENT_READY.md

Tested locally: 44,553 chars, 130s, 0 errors
Ready for production: 5.35.88.251
"

# Push (triggers GitHub Actions)
git push origin main
```

**Что произойдет:**
- GitHub Actions автоматически задеплоит код (~30 секунд)
- Код появится на 5.35.88.251 в `/var/GrantService/`
- Сервисы перезапустятся

---

### STEP 2: Manual Migration on Server (10 минут)

**ВАЖНО:** GitHub Actions НЕ выполняет миграции БД!

**Команды:**

```bash
# SSH на production
ssh root@5.35.88.251

# Navigate to project
cd /var/GrantService

# Check files are there
ls -lh agents/production_writer.py
ls -lh deploy_production_writer.sh

# Run deployment script
./deploy_production_writer.sh

# Expected output:
# [Step 1/4] Applying database migration...
# ✓ Backup created
# ✓ Migration applied
# [Step 2/4] Installing dependencies...
# ✓ Dependencies installed
# [Step 3/4] Verifying ProductionWriter...
# ✓ ProductionWriter imported successfully
# ✓ Qdrant connected: 1 collections
# [Step 4/4] Restarting services...
# ✓ Services restarted
# ✅ ProductionWriter Deployed!
```

**Если скрипт не сработает, выполнить вручную:**

```bash
# Backup БД
PGPASSWORD=$DB_PASSWORD pg_dump -h localhost -p 5434 -U grantservice -d grantservice > backup_$(date +%Y%m%d_%H%M%S).sql

# Apply migration
PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5434 -U grantservice -d grantservice \
  -f database/migrations/014_update_grants_for_production_writer.sql

# Install dependencies
source venv/bin/activate
pip install -r requirements_production_writer.txt

# Restart services
sudo systemctl restart grantservice-bot
sudo systemctl restart grantservice-admin
```

---

### STEP 3: Verify Deployment (3 минуты)

**Команды:**

```bash
# Still on production server (5.35.88.251)

# 1. Check migration applied
PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5434 -U grantservice -d grantservice -c "\d grants"

# Expected: research_id | character varying(100) | | (nullable)

# 2. Check ProductionWriter imports
python3 -c "from agents.production_writer import ProductionWriter; print('✓ ProductionWriter OK')"

# Expected: ✓ ProductionWriter OK

# 3. Check Qdrant connection
python3 -c "
from qdrant_client import QdrantClient
client = QdrantClient(host='5.35.88.251', port=6333)
collections = client.get_collections()
print(f'✓ Qdrant: {len(collections.collections)} collections')
"

# Expected: ✓ Qdrant: 1 collections

# 4. Check services running
sudo systemctl status grantservice-bot
sudo systemctl status grantservice-admin

# Expected: Both active (running)
```

---

### STEP 4: Telegram Bot Integration (1 час) - СЛЕДУЮЩАЯ ЗАДАЧА

**ВАЖНО:** ProductionWriter готов, но НЕ интегрирован в Telegram Bot!

**Что нужно сделать:**

#### 4.1. Создать grant_handler.py

```bash
# На production сервере
cd /var/GrantService/telegram-bot/handlers
nano grant_handler.py

# Код находится в:
# C:\SnowWhiteAI\GrantService_Project\01_Projects\2025-10-20_Bootcamp_GrantService\CORRECTED_PRODUCTION_DEPLOYMENT.md
# Phase 3, Section 3.1
```

#### 4.2. Найти DB wrapper класс

```bash
# Найти где находится DB класс
cd /var/GrantService
find . -name "*.py" -type f -exec grep -l "class.*DB\|class.*Database" {} \; | grep -v "__pycache__" | grep -v "venv"

# Обычно в:
# - database/db_manager.py
# - core/database.py
# - shared/database.py
```

#### 4.3. Добавить DB methods

```python
# В DB wrapper класс добавить:

def get_anketa_by_id(self, anketa_id: str) -> Dict:
    """Load anketa from sessions table by anketa_id"""
    # SQL: SELECT interview_data FROM sessions WHERE anketa_id = ?

def save_grant(
    self,
    grant_id: str,
    anketa_id: str,
    user_id: int,
    grant_content: str,
    character_count: int,
    word_count: int,
    duration_seconds: float,
    sections_generated: int = 10,
    qdrant_queries: int = 0,
    llm_provider: str = 'gigachat'
) -> int:
    """Save grant to grants table"""
    # INSERT INTO grants (...) VALUES (...) RETURNING id
```

#### 4.4. Зарегистрировать handler

```python
# В telegram-bot/unified_bot.py

from handlers.grant_handler import register_grant_handlers

def main():
    # ... existing code ...

    # Register grant handlers
    register_grant_handlers(application)

    # ... existing code ...
```

#### 4.5. Test

```
# В Telegram Bot
/generate_grant <test_anketa_id>

# Expected:
# ⏳ Генерирую грантовую заявку...
# ✅ Заявка готова! (через ~130 секунд)
# 📄 [Файл grant_<id>.md]
```

---

## 🔧 КРИТИЧНЫЕ ПАРАМЕТРЫ

### Production Server

| Parameter | Value |
|-----------|-------|
| **Server IP** | 5.35.88.251 |
| **Project Path** | /var/GrantService/ |
| **PostgreSQL** | localhost:5434 |
| **Database** | grantservice |
| **User** | grantservice |
| **Qdrant** | 5.35.88.251:6333 |
| **Streamlit Port** | 8550 |

### Services

| Service | Name |
|---------|------|
| **Bot** | grantservice-bot.service |
| **Admin** | grantservice-admin.service |

### Environment Variables (should exist in config/.env)

```bash
# Qdrant
QDRANT_HOST=5.35.88.251
QDRANT_PORT=6333

# GigaChat
GIGACHAT_CREDENTIALS=<base64>
GIGACHAT_SCOPE=GIGACHAT_API_PERS

# PostgreSQL
DB_PASSWORD=<password>
DB_HOST=localhost
DB_PORT=5434
DB_NAME=grantservice
DB_USER=grantservice

# Admin notifications
ADMIN_GROUP_ID=-4930683040
TELEGRAM_BOT_ID=8057176426
```

---

## 📊 DEPLOYMENT CHECKLIST

### Pre-Deployment ✅

- [x] Migration 014 created
- [x] ProductionWriter copied to agents/
- [x] Dependencies documented (requirements_production_writer.txt)
- [x] Deployment script created (deploy_production_writer.sh)
- [x] Documentation created (DEPLOYMENT_READY.md)
- [x] Files added to git staging (5 files)

### Deployment ⏳

- [ ] Git commit executed
- [ ] Git push executed (triggers GitHub Actions)
- [ ] GitHub Actions completed successfully
- [ ] SSH to production server
- [ ] Deployment script executed
- [ ] Migration 014 applied to database
- [ ] Dependencies installed
- [ ] Services restarted

### Verification ⏳

- [ ] Migration verified (\d grants shows research_id nullable)
- [ ] ProductionWriter imports successfully
- [ ] Qdrant connection verified
- [ ] Services running (systemctl status)
- [ ] Logs clean (no errors)

### Integration ⏳

- [ ] grant_handler.py created
- [ ] DB methods added
- [ ] Handler registered in unified_bot.py
- [ ] Manual test: /generate_grant <test_id>
- [ ] Grant generated successfully
- [ ] File sent to user
- [ ] Admin notification sent

---

## 🚨 ROLLBACK PLAN

Если что-то пошло не так:

```bash
# 1. SSH на production
ssh root@5.35.88.251
cd /var/GrantService

# 2. Restore database
BACKUP=$(ls -t database/backups/grantservice_backup_*.sql | head -1)
PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5434 -U grantservice -d grantservice < "$BACKUP"

# 3. Rollback code
git log --oneline -5
git reset --hard <previous_commit_hash>

# 4. Restart services
sudo systemctl restart grantservice-bot grantservice-admin

# 5. Verify
sudo systemctl status grantservice-bot
```

---

## 📞 QUICK COMMANDS REFERENCE

### SSH Access
```bash
ssh root@5.35.88.251
cd /var/GrantService
```

### Check Services
```bash
sudo systemctl status grantservice-bot
sudo systemctl status grantservice-admin
journalctl -u grantservice-bot -f
```

### Check Database
```bash
PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5434 -U grantservice -d grantservice
```

### Check Qdrant
```bash
curl http://5.35.88.251:6333/collections/knowledge_sections
```

### Check ProductionWriter
```bash
cd /var/GrantService
source venv/bin/activate
python3 -c "from agents.production_writer import ProductionWriter; print('OK')"
```

---

## 📚 DOCUMENTATION FILES

### In GrantService repo (C:\SnowWhiteAI\GrantService):

- `DEPLOYMENT_READY.md` - Deployment guide (в Git staging)
- `agents/production_writer.py` - ProductionWriter code (в Git staging)
- `database/migrations/014_update_grants_for_production_writer.sql` - Migration (в Git staging)
- `deploy_production_writer.sh` - Deployment script (в Git staging)
- `requirements_production_writer.txt` - Dependencies (в Git staging)

### In GrantService_Project (Documentation):

- `DEPLOYMENT_RESUME_PLAN.md` - THIS FILE (resume plan)
- `DEPLOYMENT_DONE.md` - Summary of what's done
- `DEPLOYMENT_GAP_ANALYSIS.md` - Gap analysis
- `CORRECTED_PRODUCTION_DEPLOYMENT.md` - Full deployment plan
- `DEPLOYMENT_SUMMARY.md` - Quick reference
- `AUDIT_CORRECTIONS.md` - What was corrected
- `reports/Iteration_31_FINAL_REPORT.md` - Full report

---

## ⏱️ ESTIMATED TIME

| Task | Time | Type |
|------|------|------|
| Git commit & push | 2 min | Manual |
| GitHub Actions | 30 sec | Auto |
| SSH to server | 1 min | Manual |
| Run deployment script | 10 min | Auto (script) |
| Verify deployment | 3 min | Manual |
| **TOTAL** | **~17 min** | |

**Bot Integration:** +1 час (следующая задача)

---

## 🎯 IMMEDIATE NEXT ACTION

**После перезапуска Claude, выполни:**

```bash
cd C:\SnowWhiteAI\GrantService

# Check git status
git status

# Should see 5 files in "Changes to be committed"

# Commit
git commit -m "feat: Add ProductionWriter for automated grant generation"

# Push
git push origin main

# Then SSH to server and run deployment script
```

---

## ✅ SUCCESS INDICATORS

После deployment проверь:

1. ✅ Migration applied: `research_id` nullable in grants table
2. ✅ ProductionWriter imports: `from agents.production_writer import ProductionWriter`
3. ✅ Qdrant connected: curl http://5.35.88.251:6333/collections/knowledge_sections
4. ✅ Services running: `systemctl status grantservice-bot grantservice-admin`
5. ✅ No errors in logs: `journalctl -u grantservice-bot -n 50`

---

**Created:** 2025-10-24 10:55
**Status:** ✅ READY TO RESUME - START WITH GIT PUSH
**Next:** Git commit & push → SSH migration → Verify → Bot integration
