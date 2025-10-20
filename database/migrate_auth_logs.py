#!/usr/bin/env python3
"""Manually migrate auth_logs"""
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

print("=== Migrating auth_logs manually ===")
print()

# Get data from SQLite
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_cursor = sqlite_conn.cursor()

sqlite_cursor.execute("SELECT * FROM auth_logs ORDER BY id")
rows = sqlite_cursor.fetchall()

print(f"Found {len(rows)} rows in SQLite")
print()

# Insert into PostgreSQL
pg_conn = psycopg2.connect(**PG_CONFIG)
pg_cursor = pg_conn.cursor()

for row in rows:
    id, user_id, action, ip_address, user_agent, success, error_message, created_at = row

    try:
        pg_cursor.execute("""
            INSERT INTO auth_logs (id, user_id, action, ip_address, user_agent, success, error_message, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (id, user_id, action, ip_address, user_agent, bool(success), error_message, created_at))
        print(f"[OK] Inserted row {id}")
    except Exception as e:
        print(f"[ERROR] Row {id}: {e}")

pg_conn.commit()

# Reset sequence
pg_cursor.execute("SELECT setval('auth_logs_id_seq', (SELECT MAX(id) FROM auth_logs), true)")
print()
print("[OK] Reset sequence")

pg_cursor.close()
pg_conn.close()
sqlite_cursor.close()
sqlite_conn.close()

print()
print("Done!")
