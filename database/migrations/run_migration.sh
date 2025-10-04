#!/bin/bash
# SQLite to PostgreSQL Migration Script (Linux/Mac)
# GrantService Database Migration

echo "============================================================"
echo "SQLite to PostgreSQL Migration"
echo "============================================================"

# Set PostgreSQL connection parameters
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=grantservice
export PGUSER=postgres
export PGPASSWORD=root

# Set SQLite database path
SQLITE_DB="C:\SnowWhiteAI\GrantService\data\grantservice.db"

echo ""
echo "Configuration:"
echo "  SQLite DB: $SQLITE_DB"
echo "  PostgreSQL Host: $PGHOST:$PGPORT"
echo "  PostgreSQL DB: $PGDATABASE"
echo "  PostgreSQL User: $PGUSER"
echo ""

# Run migration script
python3 migrate_sqlite_to_postgresql.py \
    --sqlite-db "$SQLITE_DB" \
    --pg-host $PGHOST \
    --pg-port $PGPORT \
    --pg-database $PGDATABASE \
    --pg-user $PGUSER \
    --pg-password $PGPASSWORD

echo ""
echo "Migration completed!"
