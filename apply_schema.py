#!/usr/bin/env python3
"""Apply PostgreSQL schema"""

import psycopg2

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
    print("[*] Applying schema (this may take 30-60 seconds)...")

    # Defer constraints to avoid FK errors during table creation
    cursor.execute("SET CONSTRAINTS ALL DEFERRED;")

    # Split by statement and execute one by one
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
    total = len(statements)

    for i, stmt in enumerate(statements, 1):
        if i % 10 == 0:
            print(f"[*] Processing statement {i}/{total}...")
        try:
            cursor.execute(stmt)
        except Exception as e:
            # Skip if already exists
            if 'already exists' in str(e).lower():
                pass
            else:
                print(f"[ERROR] Statement {i}: {stmt[:100]}...")
                raise

    conn.commit()
    print("[OK] Schema applied successfully!")

    # Check tables created
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
    table_count = cursor.fetchone()[0]
    print(f"[OK] Created {table_count} tables")

except Exception as e:
    conn.rollback()
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
