#!/usr/bin/env python3
"""Recreate database with fixed schema and run migration"""
import psycopg2
import subprocess
import sys

PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',  # Connect to postgres DB first
    'user': 'postgres',
    'password': 'root'
}

print("=" * 60)
print("STEP 1: Dropping and recreating grantservice database")
print("=" * 60)
print()

conn = psycopg2.connect(**PG_CONFIG)
conn.autocommit = True
cursor = conn.cursor()

# Drop database
try:
    cursor.execute("DROP DATABASE IF EXISTS grantservice;")
    print("[OK] Dropped grantservice database")
except Exception as e:
    print(f"[WARN] Could not drop database: {e}")

# Create database
try:
    cursor.execute("CREATE DATABASE grantservice;")
    print("[OK] Created grantservice database")
except Exception as e:
    print(f"[ERROR] Could not create database: {e}")
    sys.exit(1)

cursor.close()
conn.close()

print()
print("=" * 60)
print("STEP 2: Applying schema with fixed VARCHAR limits")
print("=" * 60)
print()

# Connect to grantservice and apply schema
PG_CONFIG['database'] = 'grantservice'
conn = psycopg2.connect(**PG_CONFIG)
cursor = conn.cursor()

try:
    with open('migrations/001_initial_postgresql_schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    cursor.execute(schema_sql)
    conn.commit()
    print("[OK] Schema applied successfully")
except Exception as e:
    print(f"[ERROR] Could not apply schema: {e}")
    sys.exit(1)

cursor.close()
conn.close()

print()
print("=" * 60)
print("STEP 3: Running migration")
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

result = subprocess.run(cmd)
sys.exit(result.returncode)
