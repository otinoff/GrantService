# PostgreSQL 18 Installation Complete ✅

**Date**: 2025-10-04
**Server**: 5.35.88.251
**Status**: Successfully installed and configured

---

## 📊 Installation Summary

### PostgreSQL Version
- **Version**: PostgreSQL 18.0 (Ubuntu 18.0-1.pgdg22.04+3)
- **Port**: 5434
- **Cluster**: 18/main
- **Status**: ✅ Running

### Database Configuration
- **Database Name**: `grantservice`
- **Database Owner**: `postgres`
- **Encoding**: UTF8
- **Collation**: en_US.UTF-8

### Database User
- **Username**: `grantservice`
- **Password**: `jPsGn%Nt%q#THnUB&&cqo*1Q`
- **Privileges**: ALL on database `grantservice`

### Superuser (postgres)
- **Username**: `postgres`
- **Password**: `UVIA8wA3p2kV6x3ucDB7RQJu`
- **Role**: Superuser

---

## 🗄️ Database Schema

### Tables Created: 18

1. **users** - System users with Telegram authentication
2. **sessions** - User sessions and progress tracking
3. **interview_questions** - Questionnaire configuration
4. **user_answers** - User responses to questions
5. **grant_applications** - Grant applications
6. **grants** - Final grant documents
7. **agent_prompts** - AI agent configurations
8. **auditor_results** - Audit results
9. **planner_structures** - Plan structures
10. **researcher_research** - Research data
11. **researcher_logs** - Research logs
12. **sent_documents** - Document tracking
13. **auth_logs** - Authentication logs
14. **page_permissions** - Page access permissions
15. **prompt_categories** - Prompt categories
16. **prompt_versions** - Prompt versions
17. **db_version** - Database version tracking
18. **db_timestamps** - Database timestamps

### Extensions Installed
- `uuid-ossp` - UUID generation
- `pg_trgm` - Full-text search support

---

## 🔐 Authentication Configuration

### pg_hba.conf Settings
```
# Local connections
local   all             postgres                peer
local   all             all                     scram-sha-256

# IPv4 connections
host    all             all             127.0.0.1/32      scram-sha-256
host    all             all             0.0.0.0/0         scram-sha-256

# IPv6 connections
host    all             all             ::1/128           scram-sha-256
```

### postgresql.conf
- `listen_addresses = '*'` - Listen on all network interfaces

---

## 🔌 Connection Details

### Connection String (URL-encoded)
```
postgresql://grantservice:jPsGn%25Nt%25q%23THnUB%26%26cqo%2A1Q@localhost:5434/grantservice
```

### Connection Parameters
```python
host='localhost'
port=5434
database='grantservice'
user='grantservice'
password='jPsGn%Nt%q#THnUB&&cqo*1Q'
```

### psql Command Line
```bash
# As grantservice user
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'
psql -h localhost -p 5434 -U grantservice -d grantservice

# As postgres superuser
export PGPASSWORD='UVIA8wA3p2kV6x3ucDB7RQJu'
psql -h localhost -p 5434 -U postgres -d grantservice
```

---

## 📝 config/.env Configuration

The following PostgreSQL settings have been added to `/var/GrantService/config/.env`:

```bash
# PostgreSQL Database Configuration
DATABASE_URL=postgresql://grantservice:jPsGn%25Nt%25q%23THnUB%26%26cqo%2A1Q@localhost:5434/grantservice
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5434
DB_NAME=grantservice
DB_USER=grantservice
DB_PASSWORD=jPsGn%Nt%q#THnUB&&cqo*1Q
```

---

## ✅ Verification Tests

### Connection Test
```bash
✓ PostgreSQL connection successful!
✓ Version: PostgreSQL 18.0
✓ Tables created: 18
✓ Users table accessible
✓ Connection test PASSED!
```

### Test Script (Python)
```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5434,
    database='grantservice',
    user='grantservice',
    password='jPsGn%Nt%q#THnUB&&cqo*1Q'
)

cursor = conn.cursor()
cursor.execute('SELECT count(*) FROM users')
print(f'User count: {cursor.fetchone()[0]}')
cursor.close()
conn.close()
```

---

## 🚀 Next Steps

### 1. Migrate Data from SQLite (if needed)
```bash
# Backup SQLite database
cp data/grantservice.db data/grantservice.db.backup

# Run migration script
python scripts/migrate_sqlite_to_postgresql.py
```

### 2. Update Application Code
Ensure all database connections use PostgreSQL:
- `data/database/models.py` - Use PostgreSQL connection
- `telegram-bot/` - Update database calls
- `web-admin/` - Update database calls

### 3. Test Application
```bash
# Test bot
cd telegram-bot
python main.py

# Test admin panel
cd web-admin
streamlit run app_main.py
```

### 4. Restart Services
```bash
sudo systemctl restart grantservice-bot
sudo systemctl restart grantservice-admin
```

---

## 🔧 Maintenance Commands

### Check PostgreSQL Status
```bash
systemctl status postgresql@18-main
pg_lsclusters
```

### Backup Database
```bash
# Backup
export PGPASSWORD='jPsGn%Nt%q#THnUB&&cqo*1Q'
pg_dump -h localhost -p 5434 -U grantservice grantservice > backup_$(date +%Y%m%d).sql

# Restore
psql -h localhost -p 5434 -U grantservice grantservice < backup_20251004.sql
```

### Monitor Connections
```bash
# Show active connections
export PGPASSWORD='UVIA8wA3p2kV6x3ucDB7RQJu'
psql -h localhost -p 5434 -U postgres -c "SELECT * FROM pg_stat_activity WHERE datname='grantservice';"
```

### View Logs
```bash
tail -f /var/log/postgresql/postgresql-18-main.log
```

---

## 🔐 Security Notes

**IMPORTANT**:
- ✅ Passwords are generated with 24 characters using secure random generator
- ✅ Passwords contain uppercase, lowercase, digits, and special characters
- ✅ Connection uses scram-sha-256 authentication (secure)
- ⚠️ Passwords are stored in `/var/GrantService/config/.env` (protected, not in Git)
- ⚠️ Backup file: `/var/GrantService/config/.env.backup`

**DO NOT**:
- ❌ Commit config/.env to Git
- ❌ Share passwords in plain text
- ❌ Use these passwords for other services

---

## 📞 Connection Info Summary

| Parameter | Value |
|-----------|-------|
| Host | localhost |
| Port | 5434 |
| Database | grantservice |
| User | grantservice |
| Password | `jPsGn%Nt%q#THnUB&&cqo*1Q` |
| URL | `postgresql://grantservice:jPsGn%25Nt%25q%23THnUB%26%26cqo%2A1Q@localhost:5434/grantservice` |

---

## 🎯 PostgreSQL Cluster Status

```
Ver  Cluster  Port  Status  Owner     Data directory
15   main     5433  online  postgres  /var/lib/postgresql/15/main
16   main     5432  online  postgres  /var/lib/postgresql/16/main
18   main     5434  online  postgres  /var/lib/postgresql/18/main  ⬅️ GrantService
```

---

**Installation completed successfully on**: 2025-10-04
**Installed by**: deployment-manager agent (Claude Code)
**Server**: root@5.35.88.251

✅ **PostgreSQL 18 is ready for use!**
