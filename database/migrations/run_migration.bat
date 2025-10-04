@echo off
REM SQLite to PostgreSQL Migration Script (Windows)
REM GrantService Database Migration

echo ============================================================
echo SQLite to PostgreSQL Migration
echo ============================================================

REM Set PostgreSQL connection parameters
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=grantservice
set PGUSER=postgres
set PGPASSWORD=root

REM Set SQLite database path
set SQLITE_DB=C:\SnowWhiteAI\GrantService\data\grantservice.db

echo.
echo Configuration:
echo   SQLite DB: %SQLITE_DB%
echo   PostgreSQL Host: %PGHOST%:%PGPORT%
echo   PostgreSQL DB: %PGDATABASE%
echo   PostgreSQL User: %PGUSER%
echo.

REM Run migration script
python migrate_sqlite_to_postgresql.py ^
    --sqlite-db "%SQLITE_DB%" ^
    --pg-host %PGHOST% ^
    --pg-port %PGPORT% ^
    --pg-database %PGDATABASE% ^
    --pg-user %PGUSER% ^
    --pg-password %PGPASSWORD%

echo.
echo Migration completed!
pause
