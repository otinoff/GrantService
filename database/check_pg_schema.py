#!/usr/bin/env python3
"""Check PostgreSQL schema for sessions table"""
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

print("=== PostgreSQL Schema Check ===")
print()

# Check sessions table structure
print("1. SESSIONS table structure:")
cursor.execute("""
    SELECT column_name, data_type, character_maximum_length, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'sessions'
    ORDER BY ordinal_position;
""")
columns = cursor.fetchall()
for col in columns:
    name, dtype, max_len, nullable = col
    len_str = f"({max_len})" if max_len else ""
    print(f"  {name:25s} {dtype}{len_str:15s} NULL={nullable}")
print()

# Check if sessions has any data
cursor.execute("SELECT COUNT(*) FROM sessions")
count = cursor.fetchone()[0]
print(f"2. Current rows in sessions: {count}")
print()

# Check researcher_research structure
print("3. RESEARCHER_RESEARCH table structure:")
cursor.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'researcher_research'
    ORDER BY ordinal_position;
""")
columns = cursor.fetchall()
for col in columns:
    name, dtype, max_len = col
    len_str = f"({max_len})" if max_len else ""
    print(f"  {name:25s} {dtype}{len_str}")
print()

# Check auth_logs primary key
print("4. AUTH_LOGS primary key:")
cursor.execute("""
    SELECT a.attname
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = 'auth_logs'::regclass AND i.indisprimary;
""")
pk = cursor.fetchall()
for p in pk:
    print(f"  Primary key: {p[0]}")
print()

cursor.close()
conn.close()
