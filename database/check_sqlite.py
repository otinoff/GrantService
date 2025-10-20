#!/usr/bin/env python3
"""Check SQLite database contents"""
import sqlite3
import os

SQLITE_DB = r'C:\SnowWhiteAI\GrantService\data\grantservice.db'

if not os.path.exists(SQLITE_DB):
    print(f"[ERROR] SQLite database not found: {SQLITE_DB}")
    exit(1)

conn = sqlite3.connect(SQLITE_DB)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()

print(f"Tables in SQLite database: {len(tables)}")
print()

total_rows = 0
for table in tables:
    table_name = table[0]
    if table_name == 'sqlite_sequence':
        continue

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    total_rows += count

    if count > 0:
        print(f"  {table_name:30s} - {count:6d} rows")

print()
print(f"Total rows to migrate: {total_rows}")

cursor.close()
conn.close()
