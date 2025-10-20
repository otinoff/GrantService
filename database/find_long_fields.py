#!/usr/bin/env python3
"""Find fields with values longer than VARCHAR limit"""
import sqlite3

SQLITE_DB = r'C:\SnowWhiteAI\GrantService\data\grantservice.db'

conn = sqlite3.connect(SQLITE_DB)
cursor = conn.cursor()

print("=== Finding problematic VARCHAR fields ===")
print()

# 1. Check all sessions fields for VARCHAR limits
print("1. SESSIONS table - checking all VARCHAR fields:")
cursor.execute("PRAGMA table_info(sessions)")
columns_info = cursor.fetchall()

varchar_limits = {
    'current_step': 50,
    'status': 30,
    'completion_status': 20,
    'anketa_id': 20,
    'project_name': 300
}

for col_info in columns_info:
    col_name = col_info[1]
    if col_name in varchar_limits:
        limit = varchar_limits[col_name]
        cursor.execute(f"SELECT id, {col_name}, LENGTH({col_name}) as len FROM sessions WHERE LENGTH({col_name}) > {limit}")
        rows = cursor.fetchall()
        if rows:
            print(f"  [ERROR] {col_name} (limit={limit}):")
            for row in rows:
                print(f"    ID {row[0]}: '{row[1]}' (len={row[2]})")
        else:
            print(f"  [OK] {col_name} (limit={limit})")
print()

# 2. Check researcher_research VARCHAR fields
print("2. RESEARCHER_RESEARCH table:")
cursor.execute("PRAGMA table_info(researcher_research)")
columns_info = cursor.fetchall()

varchar_limits_rr = {
    'research_id': 50,
    'anketa_id': 20,
    'username': 100,
    'first_name': 100,
    'last_name': 100,
    'research_type': 50,
    'llm_provider': 50,
    'model': 50,
    'status': 30
}

for col_info in columns_info:
    col_name = col_info[1]
    if col_name in varchar_limits_rr:
        limit = varchar_limits_rr[col_name]
        cursor.execute(f"SELECT id, {col_name}, LENGTH({col_name}) as len FROM researcher_research WHERE {col_name} IS NOT NULL AND LENGTH({col_name}) > {limit}")
        rows = cursor.fetchall()
        if rows:
            print(f"  [ERROR] {col_name} (limit={limit}):")
            for row in rows:
                print(f"    ID {row[0]}: '{row[1]}' (len={row[2]})")
        else:
            print(f"  [OK] {col_name} (limit={limit})")
print()

# 3. Check auth_logs for duplicate primary keys
print("3. AUTH_LOGS - checking for duplicate IDs:")
cursor.execute("SELECT id, COUNT(*) as cnt FROM auth_logs GROUP BY id HAVING cnt > 1")
rows = cursor.fetchall()
if rows:
    print(f"  [ERROR] Duplicate IDs found:")
    for row in rows:
        print(f"    ID {row[0]}: appears {row[1]} times")
else:
    print(f"  [OK] No duplicate IDs")
print()

cursor.close()
conn.close()
