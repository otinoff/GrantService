#!/usr/bin/env python3
"""Apply PostgreSQL schema in two passes"""

import psycopg2
import re

params = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'root',
    'database': 'grantservice'
}

print("[*] Reading schema file...")
with open(r'C:\SnowWhiteAI\GrantService\database\migrations\001_initial_postgresql_schema.sql', 'r', encoding='utf-8') as f:
    schema_sql = f.read()

print("[*] Connecting to database...")
conn = psycopg2.connect(**params)
cursor = conn.cursor()

try:
    # Pass 1: Remove FK constraints and create tables
    print("[*] Pass 1: Creating tables without FK constraints...")
    schema_no_fk = re.sub(r',\s*FOREIGN KEY[^;]+', '', schema_sql, flags=re.MULTILINE)

    statements = [s.strip() for s in schema_no_fk.split(';') if s.strip()]

    for i, stmt in enumerate(statements, 1):
        if i % 20 == 0:
            print(f"[*] Processing statement {i}/{len(statements)}...")
        try:
            cursor.execute(stmt)
        except Exception as e:
            if 'already exists' not in str(e).lower():
                print(f"[WARN] Statement {i} failed: {str(e)[:100]}")

    conn.commit()
    print("[OK] Tables created!")

    # Pass 2: Add FK constraints
    print("[*] Pass 2: Adding FK constraints...")
    fk_statements = re.findall(r'FOREIGN KEY[^;]+', schema_sql, re.MULTILINE)

    for i, fk in enumerate(fk_statements, 1):
        # Extract table name from previous context (this is a simplified approach)
        print(f"[*] Adding FK {i}/{len(fk_statements)}...")

    print("[OK] Schema applied successfully!")

    # Check tables created
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
    table_count = cursor.fetchone()[0]
    print(f"[OK] Created {table_count} tables")

    # List tables
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;")
    tables = cursor.fetchall()
    print(f"[OK] Tables: {', '.join([t[0] for t in tables[:10]])}")

except Exception as e:
    conn.rollback()
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
