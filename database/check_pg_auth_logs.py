#!/usr/bin/env python3
"""Check PostgreSQL auth_logs"""
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

# Get all data
cursor.execute("SELECT * FROM auth_logs ORDER BY id")
rows = cursor.fetchall()

print(f"PostgreSQL auth_logs: {len(rows)} rows")
print()

if rows:
    print("Data:")
    for row in rows:
        print(f"  {row}")
else:
    print("Empty!")

cursor.close()
conn.close()
