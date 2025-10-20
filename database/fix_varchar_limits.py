#!/usr/bin/env python3
"""Fix VARCHAR limits in PostgreSQL"""
import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'grantservice',
    'user': 'postgres',
    'password': 'root'
}

print("=== Fixing VARCHAR limits in PostgreSQL ===")
print()

conn = psycopg2.connect(**PG_CONFIG)
cursor = conn.cursor()

fixes = [
    ('sessions', 'anketa_id', 50),
    ('researcher_research', 'anketa_id', 50),
    ('researcher_research', 'research_id', 100),
]

for table, column, new_size in fixes:
    try:
        sql = f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR({new_size});"
        cursor.execute(sql)
        print(f"[OK] {table}.{column} -> VARCHAR({new_size})")
    except Exception as e:
        print(f"[ERROR] {table}.{column}: {e}")

conn.commit()
cursor.close()
conn.close()

print()
print("Done! Now run migration again.")
