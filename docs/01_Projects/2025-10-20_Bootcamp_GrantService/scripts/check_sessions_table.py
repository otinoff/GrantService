#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверить структуру таблицы sessions
"""

import psycopg2
import sys

def check_sessions_table():
    """Проверить структуру таблицы sessions"""

    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='grantservice',
        user='postgres',
        password='root',
        client_encoding='utf8'
    )

    cursor = conn.cursor()

    # Get columns
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'sessions'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()

    print("Table: sessions")
    print(f"Columns ({len(columns)}):\n")
    for col_name, data_type, max_length in columns:
        if max_length:
            print(f"  - {col_name}: {data_type}({max_length})")
        else:
            print(f"  - {col_name}: {data_type}")

    # Check if there are any records
    cursor.execute("SELECT COUNT(*) FROM sessions;")
    count = cursor.fetchone()[0]
    print(f"\nTotal records: {count}")

    # Show sample record if exists
    if count > 0:
        cursor.execute("""
            SELECT anketa_id, status
            FROM sessions
            LIMIT 1;
        """)
        sample = cursor.fetchone()
        print(f"\nSample anketa_id: {sample[0]}")
        print(f"Sample status: {sample[1]}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_sessions_table()
