#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify dialog_history column was added successfully
"""

import psycopg2
import os

os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'

print("=" * 80)
print("VERIFYING DIALOG_HISTORY MIGRATION")
print("=" * 80)

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='root',
        database='grantservice'
    )

    cursor = conn.cursor()

    # Check column
    print("\nChecking sessions.dialog_history column...")
    cursor.execute("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'dialog_history';
    """)

    result = cursor.fetchone()
    if result:
        print(f"\n[SUCCESS] Column exists!")
        print(f"  Column name: {result[0]}")
        print(f"  Data type: {result[1]}")
        print(f"  Default: {result[2]}")
    else:
        print("\n[ERROR] Column not found!")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("MIGRATION VERIFICATION COMPLETE")
    print("=" * 80)

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
