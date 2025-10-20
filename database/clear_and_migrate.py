#!/usr/bin/env python3
"""Clear PostgreSQL tables and run migration"""
import psycopg2
import subprocess
import sys

PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'grantservice',
    'user': 'postgres',
    'password': 'root'
}

print("=" * 60)
print("STEP 1: Clearing PostgreSQL tables")
print("=" * 60)
print()

conn = psycopg2.connect(**PG_CONFIG)
cursor = conn.cursor()

# List of tables to clear (in reverse dependency order)
tables_to_clear = [
    'sent_documents',
    'researcher_research',
    'grant_applications',
    'researcher_logs',
    'planner_structures',
    'auditor_results',
    'auth_logs',
    'user_answers',
    'sessions',
    'prompt_versions',
    'agent_prompts',
    'prompt_categories',
    'interview_questions',
    'users',
    'page_permissions'
]

for table in tables_to_clear:
    try:
        cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
        print(f"[OK] Cleared {table}")
    except Exception as e:
        print(f"[WARN] Could not clear {table}: {e}")

conn.commit()
cursor.close()
conn.close()

print()
print("=" * 60)
print("STEP 2: Running migration")
print("=" * 60)
print()

# Run migration
cmd = [
    'python',
    'migrations/migrate_sqlite_to_postgresql.py',
    '--sqlite-db', r'C:\SnowWhiteAI\GrantService\data\grantservice.db',
    '--pg-host', 'localhost',
    '--pg-port', '5432',
    '--pg-database', 'grantservice',
    '--pg-user', 'postgres',
    '--pg-password', 'root'
]

result = subprocess.run(cmd, capture_output=False)
sys.exit(result.returncode)
