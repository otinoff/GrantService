#!/usr/bin/env python3
"""Final migration verification"""
import sqlite3
import psycopg2

SQLITE_DB = r'C:\SnowWhiteAI\GrantService\data\grantservice.db'

PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'grantservice',
    'user': 'postgres',
    'password': 'root'
}

print("=" * 60)
print("FINAL MIGRATION VERIFICATION")
print("=" * 60)
print()

# Connect to databases
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_cursor = sqlite_conn.cursor()

pg_conn = psycopg2.connect(**PG_CONFIG)
pg_cursor = pg_conn.cursor()

# Get all tables from SQLite
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables = [row[0] for row in sqlite_cursor.fetchall()]

print(f"Comparing {len(tables)} tables...")
print()

total_sqlite = 0
total_pg = 0
matches = 0
mismatches = 0

for table in tables:
    # Count SQLite rows
    try:
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]
    except:
        sqlite_count = 0

    # Count PostgreSQL rows
    try:
        pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        pg_count = pg_cursor.fetchone()[0]
    except:
        pg_count = 0

    total_sqlite += sqlite_count
    total_pg += pg_count

    match = "[OK]" if sqlite_count == pg_count else "[WARN]"

    if sqlite_count == pg_count:
        matches += 1
    else:
        mismatches += 1

    if sqlite_count > 0 or pg_count > 0:
        print(f"{match} {table:30s} SQLite: {sqlite_count:4d} | PostgreSQL: {pg_count:4d}")

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total SQLite rows:    {total_sqlite}")
print(f"Total PostgreSQL rows: {total_pg}")
print(f"Matching tables:       {matches}")
print(f"Mismatched tables:     {mismatches}")
print()

if total_sqlite == total_pg:
    print("[SUCCESS] Migration completed successfully!")
    print(f"All {total_pg} rows migrated.")
else:
    print(f"[WARNING] {total_sqlite - total_pg} rows not migrated")

sqlite_cursor.close()
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()
