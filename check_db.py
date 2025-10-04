#!/usr/bin/env python3
"""Check database state"""

import psycopg2

params = {
    'host': 'localhost',
    'port': 5432,
    'user': 'grantservice_user',
    'password': 'grantservice2024',
    'database': 'grantservice'
}

conn = psycopg2.connect(**params)
cursor = conn.cursor()

print("[*] Checking existing tables...")
cursor.execute("""
    SELECT tablename
    FROM pg_tables
    WHERE schemaname='public'
    ORDER BY tablename;
""")
tables = cursor.fetchall()

if tables:
    print(f"[INFO] Found {len(tables)} tables:")
    for t in tables:
        print(f"  - {t[0]}")
else:
    print("[INFO] No tables found")

cursor.close()
conn.close()
