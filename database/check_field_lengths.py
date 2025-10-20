#!/usr/bin/env python3
"""Check field lengths in SQLite that are causing migration errors"""
import sqlite3

SQLITE_DB = r'C:\SnowWhiteAI\GrantService\data\grantservice.db'

conn = sqlite3.connect(SQLITE_DB)
cursor = conn.cursor()

print("Checking problematic fields...")
print()

# Check sessions.status length
cursor.execute("SELECT id, status, LENGTH(status) as len FROM sessions WHERE LENGTH(status) > 20")
rows = cursor.fetchall()
if rows:
    print(f"sessions.status - values longer than VARCHAR(20):")
    for row in rows:
        print(f"  ID {row[0]}: '{row[1]}' (len={row[2]})")
    print()

# Check sessions.current_step length
cursor.execute("SELECT id, current_step, LENGTH(current_step) as len FROM sessions WHERE LENGTH(current_step) > 50")
rows = cursor.fetchall()
if rows:
    print(f"sessions.current_step - values longer than VARCHAR(50):")
    for row in rows:
        print(f"  ID {row[0]}: '{row[1]}' (len={row[2]})")
    print()

# Check researcher_research fields
cursor.execute("SELECT id, research_type, LENGTH(research_type) as len FROM researcher_research WHERE LENGTH(research_type) > 50")
rows = cursor.fetchall()
if rows:
    print(f"researcher_research.research_type - values longer than VARCHAR(50):")
    for row in rows:
        print(f"  ID {row[0]}: '{row[1]}' (len={row[2]})")
    print()

# Check auth_logs for duplicates
cursor.execute("SELECT username, COUNT(*) as cnt FROM auth_logs GROUP BY username HAVING cnt > 1")
rows = cursor.fetchall()
if rows:
    print(f"auth_logs - duplicate usernames:")
    for row in rows:
        print(f"  '{row[0]}': {row[1]} times")
    print()

cursor.close()
conn.close()
