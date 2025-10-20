#!/usr/bin/env python3
"""Fix auth_logs migration with proper user_id mapping"""
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

print("=== Fixing auth_logs migration ===")
print()

# Connect to PostgreSQL
pg_conn = psycopg2.connect(**PG_CONFIG)
pg_cursor = pg_conn.cursor()

# Get telegram_id -> id mapping from PostgreSQL users
pg_cursor.execute("SELECT id, telegram_id FROM users")
users_map = {row[1]: row[0] for row in pg_cursor.fetchall()}  # {telegram_id: id}

print(f"Found {len(users_map)} users in PostgreSQL:")
for tg_id, user_id in users_map.items():
    print(f"  telegram_id={tg_id} -> users.id={user_id}")
print()

# Get data from SQLite
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_cursor = sqlite_conn.cursor()

sqlite_cursor.execute("SELECT * FROM auth_logs ORDER BY id")
rows = sqlite_cursor.fetchall()

print(f"Migrating {len(rows)} auth_logs rows...")
print()

migrated = 0
skipped = 0

for row in rows:
    id, user_id_or_telegram_id, action, ip_address, user_agent, success, error_message, created_at = row

    # Try to map telegram_id to users.id
    if user_id_or_telegram_id in users_map:
        pg_user_id = users_map[user_id_or_telegram_id]
        print(f"[MAPPED] telegram_id={user_id_or_telegram_id} -> users.id={pg_user_id}")
    elif user_id_or_telegram_id in [uid for uid in users_map.values()]:
        # Already a valid users.id
        pg_user_id = user_id_or_telegram_id
        print(f"[OK] Using users.id={pg_user_id}")
    else:
        # User not found, set to NULL
        pg_user_id = None
        print(f"[WARN] User not found for {user_id_or_telegram_id}, setting to NULL")

    try:
        pg_cursor.execute("""
            INSERT INTO auth_logs (user_id, action, ip_address, user_agent, success, error_message, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (pg_user_id, action, ip_address, user_agent, bool(success), error_message, created_at))
        migrated += 1
    except Exception as e:
        print(f"[ERROR] Row {id}: {e}")
        skipped += 1

pg_conn.commit()
pg_cursor.close()
pg_conn.close()
sqlite_cursor.close()
sqlite_conn.close()

print()
print(f"Done! Migrated: {migrated}, Skipped: {skipped}")
