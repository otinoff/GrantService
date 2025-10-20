#!/usr/bin/env python3
"""Check actual data causing migration errors"""
import sqlite3

SQLITE_DB = r'C:\SnowWhiteAI\GrantService\data\grantservice.db'

conn = sqlite3.connect(SQLITE_DB)
cursor = conn.cursor()

print("=== Checking problematic data ===")
print()

# 1. Check sessions table
print("1. SESSIONS table:")
cursor.execute("SELECT id, status, current_step FROM sessions")
sessions = cursor.fetchall()
for row in sessions:
    sid, status, step = row
    status_len = len(status) if status else 0
    step_len = len(step) if step else 0
    if status_len > 20 or step_len > 50:
        print(f"  [PROBLEM] ID={sid}: status={status} (len={status_len}), step={step} (len={step_len})")
    else:
        print(f"  [OK] ID={sid}: status_len={status_len}, step_len={step_len}")
print()

# 2. Check researcher_research
print("2. RESEARCHER_RESEARCH table:")
cursor.execute("SELECT id, research_type FROM researcher_research")
research = cursor.fetchall()
for row in research:
    rid, rtype = row
    rtype_len = len(rtype) if rtype else 0
    if rtype_len > 50:
        print(f"  [PROBLEM] ID={rid}: research_type={rtype} (len={rtype_len})")
    else:
        print(f"  [OK] ID={rid}: type_len={rtype_len}")
print()

# 3. Check auth_logs structure
print("3. AUTH_LOGS structure:")
cursor.execute("PRAGMA table_info(auth_logs)")
columns = cursor.fetchall()
print("  Columns:")
for col in columns:
    print(f"    - {col[1]} {col[2]}")
print()

# 4. Check auth_logs primary key
cursor.execute("SELECT * FROM auth_logs")
auth_rows = cursor.fetchall()
print(f"  Total rows: {len(auth_rows)}")
print()

cursor.close()
conn.close()
