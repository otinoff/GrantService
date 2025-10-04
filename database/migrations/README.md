# SQLite to PostgreSQL Migration Guide

## Quick Start (No Password Prompt!)

### Windows
```bash
cd database\migrations
run_migration.bat
```

### Linux/Mac
```bash
cd database/migrations
chmod +x run_migration.sh
./run_migration.sh
```

## What These Scripts Do

The migration scripts automatically:
1. Connect to SQLite database (`data/grantservice.db`)
2. Connect to PostgreSQL database (`grantservice` on localhost)
3. Migrate all tables in correct order (respecting foreign keys)
4. Convert data types (JSON → JSONB, INTEGER → BOOLEAN)
5. Verify migration success
6. Generate detailed log file

**No password prompts** - credentials are pre-configured in the scripts!

## Configuration

Edit the scripts if you need to change connection settings:

### In `run_migration.bat` (Windows)
```batch
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=grantservice
set PGUSER=postgres
set PGPASSWORD=root
```

### In `run_migration.sh` (Linux/Mac)
```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=grantservice
export PGUSER=postgres
export PGPASSWORD=root
```

## Manual Migration

If you prefer to run manually:

```bash
python migrate_sqlite_to_postgresql.py \
    --sqlite-db C:\SnowWhiteAI\GrantService\data\grantservice.db \
    --pg-host localhost \
    --pg-port 5432 \
    --pg-database grantservice \
    --pg-user postgres \
    --pg-password root
```

## Quick PostgreSQL Access

Connect to PostgreSQL without password prompt:

### Windows
```bash
cd database
psql_connect.bat
```

### Linux/Mac
```bash
cd database
chmod +x psql_connect.sh
./psql_connect.sh
```

## Troubleshooting

### "Cannot connect to PostgreSQL"
1. Ensure PostgreSQL is running:
   ```bash
   # Windows
   net start postgresql-x64-14

   # Linux
   sudo systemctl status postgresql
   ```

2. Verify database exists:
   ```sql
   psql -U postgres -c "\l"
   ```

3. Create database if needed:
   ```sql
   psql -U postgres -c "CREATE DATABASE grantservice;"
   ```

### "Permission denied"
Make sure PostgreSQL user `postgres` has password `root`:
```sql
ALTER USER postgres PASSWORD 'root';
```

### "Table already exists"
Drop tables before migration:
```sql
psql -U postgres -d grantservice -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

## Migration Output

The script creates a log file: `migration_YYYYMMDD_HHMMSS.log`

Successful output shows:
```
✓ Successfully migrated X rows
✓ users                           SQLite:    100 | PostgreSQL:    100
✓ sessions                        SQLite:     50 | PostgreSQL:     50
...
✓ Migration completed successfully!
```

## Tables Migration Order

1. users
2. interview_questions
3. sessions
4. user_answers
5. prompt_categories
6. agent_prompts
7. prompt_versions
8. researcher_logs
9. grant_applications
10. researcher_research
11. grants
12. auditor_results
13. planner_structures
14. auth_logs
15. page_permissions
16. sent_documents
17. db_version
18. db_timestamps

Foreign key dependencies are automatically handled!
