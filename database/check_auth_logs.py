#!/usr/bin/env python3
"""Check auth_logs for duplicate IDs"""
import sqlite3

SQLITE_DB = r'C:\SnowWhiteAI\GrantService\data\grantservice.db'

conn = sqlite3.connect(SQLITE_DB)
cursor = conn.cursor()

print("=== AUTH_LOGS Analysis ===")
print()

# Get all auth_logs data
cursor.execute("SELECT * FROM auth_logs ORDER BY id")
rows = cursor.fetchall()

print(f"Total rows: {len(rows)}")
print()

# Get column names
cursor.execute("PRAGMA table_info(auth_logs)")
columns = [col[1] for col in cursor.fetchall()]

print(f"Columns: {', '.join(columns)}")
print()

# Show all rows
print("Data:")
for row in rows:
    print(f"  {dict(zip(columns, row))}")
print()

# Check for duplicate IDs
cursor.execute("SELECT id, COUNT(*) as cnt FROM auth_logs GROUP BY id HAVING cnt > 1")
dupes = cursor.fetchall()

if dupes:
    print("[ERROR] Duplicate IDs:")
    for dupe in dupes:
        print(f"  ID {dupe[0]}: {dupe[1]} times")
else:
    print("[OK] No duplicate IDs in SQLite")

cursor.close()
conn.close()
