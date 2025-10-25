#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick fix: Alter grant_applications.title to TEXT and restart Iteration 41
Date: 2025-10-25
"""

import psycopg2
import os

# PostgreSQL connection
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'

print("=" * 80)
print("FIXING DATABASE VARCHAR(500) LIMIT")
print("=" * 80)

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='root',
        database='grantservice'
    )

    cursor = conn.cursor()

    # Check current type
    print("\n1. Checking current grant_applications.title type...")
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'grant_applications' AND column_name = 'title';
    """)

    result = cursor.fetchone()
    print(f"   Current: {result}")

    # Alter column type to TEXT
    print("\n2. Altering grant_applications.title to TEXT...")
    cursor.execute("""
        ALTER TABLE grant_applications
        ALTER COLUMN title TYPE TEXT;
    """)

    conn.commit()
    print("   ✅ Column altered successfully!")

    # Verify change
    print("\n3. Verifying change...")
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'grant_applications' AND column_name = 'title';
    """)

    result = cursor.fetchone()
    print(f"   New: {result}")

    # Clean up failed sessions
    print("\n4. Cleaning up failed test sessions (472-481+)...")
    cursor.execute("""
        DELETE FROM grant_applications
        WHERE session_id IN (
            SELECT id FROM sessions WHERE telegram_id = 999999997 AND status = 'active'
        );
    """)

    cursor.execute("""
        DELETE FROM sessions
        WHERE telegram_id = 999999997 AND status = 'active';
    """)

    conn.commit()

    deleted_count = cursor.rowcount
    print(f"   ✅ Deleted {deleted_count} failed sessions")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("✅ DATABASE FIX COMPLETE!")
    print("=" * 80)
    print("\nReady to restart Iteration 41 with 100 realistic interviews!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
