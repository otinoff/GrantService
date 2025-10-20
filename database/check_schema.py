#!/usr/bin/env python3
"""Check PostgreSQL schema"""
import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'grantservice',
    'user': 'postgres',
    'password': 'root'
}

conn = psycopg2.connect(**PG_CONFIG)
cursor = conn.cursor()

# Get all tables
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")
tables = cursor.fetchall()

print(f"Tables in grantservice database: {len(tables)}")
print()

if tables:
    for table in tables:
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  {table[0]:30s} - {count:6d} rows")
else:
    print("  [WARN] No tables found! Need to apply schema.")

cursor.close()
conn.close()
