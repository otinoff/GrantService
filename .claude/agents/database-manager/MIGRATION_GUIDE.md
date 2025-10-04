# 🗄️ PostgreSQL Migration Guide

**GrantService Database Migration: SQLite → PostgreSQL**

Complete guide for migrating from SQLite to PostgreSQL, starting with local Windows development environment.

---

## 📋 Table of Contents

1. [Why PostgreSQL?](#why-postgresql)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Local Windows Setup](#phase-1-local-windows-setup)
4. [Phase 2: Data Migration](#phase-2-data-migration)
5. [Phase 3: Application Update](#phase-3-application-update)
6. [Phase 4: Production Deployment](#phase-4-production-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Plan](#rollback-plan)

---

## Why PostgreSQL?

### Critical Issues with SQLite (Production)
- ❌ **File Deletion Vulnerability**: Production БД удалилась во время deployment
- ❌ **Concurrent Access**: Блокируется при записи, проблемы с admin panel + bot
- ❌ **Deployment Complexity**: Файл в `data/` может быть случайно перемещен/удален

### Benefits of PostgreSQL
- ✅ **Separate Service**: БД не в папке приложения, защищена от git operations
- ✅ **Concurrent Access**: Множество клиентов работают одновременно без блокировок
- ✅ **Better Backup**: pg_dump создает consistent backup'ы
- ✅ **JSONB Performance**: Нативная поддержка JSON с индексами
- ✅ **Production Ready**: Enterprise-grade надежность
- ✅ **Full-text Search**: Built-in возможности поиска

---

## Prerequisites

### Required Software
- **Windows 10/11** (for local testing)
- **Python 3.9+** with pip
- **Git** (already installed)
- **PostgreSQL 15+** (will install)

### Required Python Packages
```bash
pip install psycopg2-binary sqlalchemy
```

### Current Database Backup
```bash
# Create backup of current SQLite DB
cp data/grantservice.db data/grantservice_backup_$(date +%Y%m%d).db
```

---

## Phase 1: Local Windows Setup

### Step 1.1: Install PostgreSQL on Windows

#### Download PostgreSQL
1. Visit: https://www.postgresql.org/download/windows/
2. Download **PostgreSQL 15** (or latest) Windows installer
3. Run installer `postgresql-15-windows-x64.exe`

#### Installation Settings
- **Installation Directory**: `C:\Program Files\PostgreSQL\15`
- **Data Directory**: `C:\Program Files\PostgreSQL\15\data`
- **Port**: `5432` (default)
- **Locale**: `English, United States`

#### Set Password
**⚠️ ВАЖНО**: Запомните password для пользователя `postgres`!
```
Suggested password: grantservice_local_2025
```

#### Components to Install
- ✅ PostgreSQL Server
- ✅ pgAdmin 4 (GUI tool)
- ✅ Stack Builder (optional)
- ✅ Command Line Tools

#### Add to PATH (if not automatic)
```powershell
# Add PostgreSQL bin to PATH
setx PATH "%PATH%;C:\Program Files\PostgreSQL\15\bin"
```

### Step 1.2: Verify Installation

```powershell
# Check PostgreSQL version
psql --version
# Should output: psql (PostgreSQL) 15.x

# Check PostgreSQL service is running
Get-Service -Name postgresql*
# Status should be: Running
```

### Step 1.3: Create Database

#### Option A: Using psql (Command Line)
```powershell
# Connect to PostgreSQL as postgres user
psql -U postgres

# Inside psql:
CREATE DATABASE grantservice;
CREATE USER grantservice_user WITH PASSWORD 'local_dev_password_2025';
GRANT ALL PRIVILEGES ON DATABASE grantservice TO grantservice_user;

# Exit psql
\q
```

#### Option B: Using pgAdmin 4 (GUI)
1. Open **pgAdmin 4** from Start Menu
2. Connect to `PostgreSQL 15` server (enter postgres password)
3. Right-click **Databases** → **Create** → **Database**
   - Name: `grantservice`
   - Owner: `postgres`
4. Right-click **Login/Group Roles** → **Create** → **Login/Group Role**
   - Name: `grantservice_user`
   - Password: `local_dev_password_2025`
   - Privileges: ✅ Can login
   - Member of: ✅ Connect to database

### Step 1.4: Create Schema

```powershell
# Navigate to migrations folder
cd C:\SnowWhiteAI\GrantService\database\migrations

# Apply PostgreSQL schema
psql -U grantservice_user -d grantservice -f 001_initial_postgresql_schema.sql

# Enter password when prompted: local_dev_password_2025
```

#### Verify Schema Creation
```sql
-- Connect to database
psql -U grantservice_user -d grantservice

-- List all tables
\dt

-- Should see 19 tables:
-- users, sessions, grants, etc.

-- Exit
\q
```

---

## Phase 2: Data Migration

### Step 2.1: Prepare Migration Script

```powershell
# Navigate to project root
cd C:\SnowWhiteAI\GrantService

# Install required Python package
pip install psycopg2-binary
```

### Step 2.2: Run Migration

```powershell
# Run migration script
python database/migrations/migrate_sqlite_to_postgresql.py ^
    --sqlite-db "C:\SnowWhiteAI\GrantService\data\grantservice.db" ^
    --pg-host localhost ^
    --pg-database grantservice ^
    --pg-user grantservice_user ^
    --pg-password local_dev_password_2025
```

#### Expected Output
```
============================================================
SQLite to PostgreSQL Migration
GrantService Database
============================================================
Started at: 2025-10-03 20:00:00

Connecting to databases...
✓ Connected to SQLite: C:\SnowWhiteAI\GrantService\data\grantservice.db
✓ Connected to PostgreSQL: grantservice

Migrating table: users
------------------------------------------------------------
  → Found 4 rows to migrate
  → Inserted 4/4 rows
  → Reset sequence for users.id
  ✓ Successfully migrated 4 rows

Migrating table: sessions
------------------------------------------------------------
  → Found 16 rows to migrate
  → Inserted 16/16 rows
  → Reset sequence for sessions.id
  ✓ Successfully migrated 16 rows

[... migration continues for all tables ...]

============================================================
Verifying migration...
============================================================
✓ users                          SQLite:      4 | PostgreSQL:      4
✓ sessions                       SQLite:     16 | PostgreSQL:     16
✓ interview_questions            SQLite:     24 | PostgreSQL:     24
[... all tables verified ...]

============================================================
MIGRATION SUMMARY
============================================================

Total rows migrated: 120
Tables processed: 18

Successful: 18
Skipped (empty): 0
Errors: 0

Completed at: 2025-10-03 20:00:45
Total duration: 45.23 seconds

✓ Migration completed successfully!
```

### Step 2.3: Verify Data

```sql
-- Connect to PostgreSQL
psql -U grantservice_user -d grantservice

-- Check user count
SELECT COUNT(*) FROM users;
-- Expected: 4

-- Check sessions count
SELECT COUNT(*) FROM sessions;
-- Expected: 16

-- View users
SELECT telegram_id, username, first_name FROM users;

-- View recent sessions
SELECT id, anketa_id, telegram_id, completion_status FROM sessions ORDER BY created_at DESC LIMIT 5;

-- Test JSONB query (new capability!)
SELECT telegram_id, interview_data->'project_name' as project_name
FROM sessions
WHERE interview_data IS NOT NULL
LIMIT 5;

-- Exit
\q
```

---

## Phase 3: Application Update

### Step 3.1: Update Database Connection Configuration

#### Create `.env` file for local PostgreSQL
```bash
# Location: C:\SnowWhiteAI\GrantService\.env.local

# PostgreSQL Connection (Local Development)
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=grantservice
DB_USER=grantservice_user
DB_PASSWORD=local_dev_password_2025

# SQLAlchemy Connection String
DATABASE_URL=postgresql://grantservice_user:local_dev_password_2025@localhost:5432/grantservice
```

### Step 3.2: Create Database Adapter Module

Create `data/database/connection.py`:
```python
"""
Database Connection Manager
Supports both SQLite (legacy) and PostgreSQL (new)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional

class DatabaseConnection:
    """Universal database connection manager"""

    def __init__(self):
        self.db_type = os.getenv('DB_TYPE', 'sqlite')
        self.engine = None
        self.SessionLocal = None
        self._setup_connection()

    def _setup_connection(self):
        """Setup database connection based on environment"""
        if self.db_type == 'postgresql':
            # PostgreSQL connection
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                # Build from components
                host = os.getenv('DB_HOST', 'localhost')
                port = os.getenv('DB_PORT', '5432')
                database = os.getenv('DB_NAME', 'grantservice')
                user = os.getenv('DB_USER', 'grantservice_user')
                password = os.getenv('DB_PASSWORD', '')

                db_url = f'postgresql://{user}:{password}@{host}:{port}/{database}'

            self.engine = create_engine(
                db_url,
                pool_pre_ping=True,  # Check connection before using
                pool_size=10,        # Connection pool size
                max_overflow=20,     # Extra connections if needed
                echo=False           # Set True for SQL logging
            )

        else:
            # SQLite connection (fallback/legacy)
            if os.name == 'nt':  # Windows
                db_path = "C:/SnowWhiteAI/GrantService/data/grantservice.db"
            else:  # Linux
                db_path = "/var/GrantService/data/grantservice.db"

            db_url = f'sqlite:///{db_path}'
            self.engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False} if self.db_type == 'sqlite' else {}
            )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False


# Global instance
db_connection = DatabaseConnection()


def get_db() -> Session:
    """Dependency for getting DB session"""
    db = db_connection.get_session()
    try:
        yield db
    finally:
        db.close()
```

### Step 3.3: Update launcher.py

```python
# Add to launcher.py (beginning of file)

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables based on platform
if os.name == 'nt':  # Windows - use local PostgreSQL
    env_file = Path(__file__).parent / '.env.local'
else:  # Linux - use production PostgreSQL
    env_file = Path(__file__).parent / '.env.production'

if env_file.exists():
    load_dotenv(env_file)
    print(f"[OK] Loaded environment from {env_file.name}")
else:
    print(f"[WARNING] No .env file found, using defaults")

# Test database connection
from data.database.connection import db_connection

if db_connection.test_connection():
    print(f"[OK] Connected to {os.getenv('DB_TYPE', 'sqlite').upper()} database")
else:
    print(f"[ERROR] Database connection failed!")
    sys.exit(1)
```

### Step 3.4: Test Admin Panel

```powershell
# Start admin panel
python launcher.py

# Expected output:
# [OK] Loaded environment from .env.local
# [OK] Connected to POSTGRESQL database
# [OK] Database synced successfully
# ...
# [OK] Streamlit server started at http://localhost:8550
```

#### Verify Pages
1. **Dashboard** (http://localhost:8550) - Should show 4 users
2. **👥 Пользователи** - Should list all 4 users
3. **📄 Гранты** - Should show grant applications
4. **📊 Аналитика** - Should show statistics

---

## Phase 4: Production Deployment

### Step 4.1: Install PostgreSQL on Production Server

```bash
# SSH to production
ssh root@5.35.88.251

# Update package list
apt update

# Install PostgreSQL
apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Check status
systemctl status postgresql
```

### Step 4.2: Create Production Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE grantservice;
CREATE USER grantservice_user WITH PASSWORD 'STRONG_PRODUCTION_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE grantservice TO grantservice_user;

# Exit
\q
```

### Step 4.3: Apply Schema on Production

```bash
# Copy schema file to production
scp database/migrations/001_initial_postgresql_schema.sql root@5.35.88.251:/tmp/

# SSH to production
ssh root@5.35.88.251

# Apply schema
psql -U grantservice_user -d grantservice -f /tmp/001_initial_postgresql_schema.sql
```

### Step 4.4: Migrate Production Data

```bash
# On production server
cd /var/GrantService

# Install psycopg2
pip3 install psycopg2-binary

# Run migration
python3 database/migrations/migrate_sqlite_to_postgresql.py \
    --sqlite-db /var/GrantService/data/grantservice.db \
    --pg-host localhost \
    --pg-database grantservice \
    --pg-user grantservice_user \
    --pg-password STRONG_PRODUCTION_PASSWORD_HERE
```

### Step 4.5: Update Production Configuration

```bash
# Create production .env
cat > /var/GrantService/.env.production <<EOF
# PostgreSQL Connection (Production)
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=grantservice
DB_USER=grantservice_user
DB_PASSWORD=STRONG_PRODUCTION_PASSWORD_HERE

# SQLAlchemy Connection String
DATABASE_URL=postgresql://grantservice_user:STRONG_PRODUCTION_PASSWORD_HERE@localhost:5432/grantservice
EOF

# Secure the file
chmod 600 /var/GrantService/.env.production
```

### Step 4.6: Update Systemd Service

```bash
# Edit service file
nano /etc/systemd/system/grantservice-admin.service

# Add environment file:
[Service]
...
EnvironmentFile=/var/GrantService/.env.production
...

# Reload daemon
systemctl daemon-reload

# Restart services
systemctl restart grantservice-admin
systemctl restart grantservice-bot

# Check status
systemctl status grantservice-admin
```

### Step 4.7: Verify Production

```bash
# Check PostgreSQL connection
psql -U grantservice_user -d grantservice -c "SELECT COUNT(*) FROM users;"

# Check admin panel logs
journalctl -u grantservice-admin -n 50 --no-pager

# Test admin panel
curl -I https://grantservice.onff.ru/

# Run headless tests
bash scripts/quick_pages_check.sh
```

---

## Troubleshooting

### Issue: PostgreSQL service won't start

**Windows:**
```powershell
# Check Windows Event Viewer
eventvwr.msc

# Restart service
net stop postgresql-x64-15
net start postgresql-x64-15
```

**Linux:**
```bash
# Check logs
journalctl -u postgresql -n 50

# Check data directory permissions
ls -la /var/lib/postgresql/15/main/

# Restart service
systemctl restart postgresql
```

### Issue: Can't connect to PostgreSQL

```bash
# Check if PostgreSQL is listening
netstat -an | grep 5432

# Windows: Check pg_hba.conf
notepad "C:\Program Files\PostgreSQL\15\data\pg_hba.conf"

# Linux: Check pg_hba.conf
nano /etc/postgresql/15/main/pg_hba.conf

# Add line for local connections:
host    grantservice    grantservice_user    127.0.0.1/32    md5

# Reload PostgreSQL
pg_ctl reload
# or
systemctl reload postgresql
```

### Issue: Migration script fails with "relation already exists"

```sql
-- Drop and recreate database
DROP DATABASE IF EXISTS grantservice;
CREATE DATABASE grantservice;
GRANT ALL PRIVILEGES ON DATABASE grantservice TO grantservice_user;
```

### Issue: JSONB conversion errors

```python
# Check specific table
SELECT id, column_name FROM table_name WHERE column_name::text LIKE '%error%';

# Manually fix invalid JSON
UPDATE table_name
SET column_name = '{}'
WHERE column_name IS NULL OR column_name = '';
```

---

## Rollback Plan

### If Migration Fails Locally

1. **Keep SQLite**: Just don't update `.env.local`
2. **Continue using SQLite** until PostgreSQL is working

### If Migration Fails on Production

```bash
# 1. Stop services
systemctl stop grantservice-admin
systemctl stop grantservice-bot

# 2. Remove .env.production
rm /var/GrantService/.env.production

# 3. Revert systemd service
# Remove EnvironmentFile line from service

# 4. Restart with SQLite
systemctl daemon-reload
systemctl start grantservice-admin
systemctl start grantservice-bot

# 5. Verify
curl -I https://grantservice.onff.ru/
```

### Keep SQLite Backup

```bash
# Production SQLite backup location
/var/GrantService/data/grantservice_data_safe/grantservice.db

# If need to restore
cp /var/GrantService/data/grantservice_data_safe/grantservice.db \
   /var/GrantService/data/grantservice.db
```

---

## Performance Tuning

### PostgreSQL Configuration

```bash
# Edit postgresql.conf
nano /etc/postgresql/15/main/postgresql.conf

# Recommended settings for small VPS:
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB

# Restart PostgreSQL
systemctl restart postgresql
```

### Vacuum and Analyze

```bash
# Regular maintenance
psql -U grantservice_user -d grantservice -c "VACUUM ANALYZE;"

# Setup automatic vacuum (already enabled by default in PostgreSQL 15)
```

---

## Next Steps

After successful migration:

1. ✅ **Monitor Performance**: Use pgAdmin 4 or `pg_stat_statements`
2. ✅ **Setup Backups**: Create daily pg_dump script
3. ✅ **Update Documentation**: Mark SQLite as deprecated
4. ✅ **Remove SQLite Code**: Clean up old connection logic (after 1 month of stable operation)
5. ✅ **Optimize Queries**: Use EXPLAIN ANALYZE for slow queries

---

## Backup Strategy (PostgreSQL)

### Daily Backup Script

```bash
#!/bin/bash
# Location: /var/GrantService/scripts/backup_postgresql.sh

BACKUP_DIR="/var/GrantService/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/grantservice_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U grantservice_user -d grantservice -F c -f $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "✓ Backup created: ${BACKUP_FILE}.gz"
```

### Restore from Backup

```bash
# Restore from backup
gunzip grantservice_backup_20251003_120000.sql.gz
pg_restore -U grantservice_user -d grantservice -c grantservice_backup_20251003_120000.sql
```

---

**Migration Guide Version:** 1.0
**Last Updated:** 2025-10-03
**Author:** Database Manager Agent
**Status:** Ready for Local Testing
