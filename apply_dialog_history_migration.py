#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply dialog_history migration to sessions table
Iteration 42 - Database Migration
"""

import psycopg2
import os

# PostgreSQL connection
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'

print("=" * 80)
print("APPLYING DIALOG_HISTORY MIGRATION")
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

    # Check if column already exists
    print("\n1. Checking if dialog_history column exists...")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'dialog_history';
    """)

    result = cursor.fetchone()
    if result:
        print(f"   ⚠️  Column already exists: {result}")
    else:
        print("   Column does not exist yet")

    # Add dialog_history column
    print("\n2. Adding dialog_history JSONB column...")
    cursor.execute("""
        ALTER TABLE sessions
        ADD COLUMN IF NOT EXISTS dialog_history JSONB DEFAULT '[]'::jsonb;
    """)

    conn.commit()
    print("   ✅ Column added successfully!")

    # Add comment
    print("\n3. Adding column comment...")
    cursor.execute("""
        COMMENT ON COLUMN sessions.dialog_history IS
        'Full conversation history with question-answer pairs. Structure: [{"role": "interviewer"|"user", "text": "...", "timestamp": "...", "field_name": "..."}]';
    """)

    conn.commit()
    print("   ✅ Comment added!")

    # Create GIN index for JSONB queries
    print("\n4. Creating GIN index for dialog_history...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_dialog_history ON sessions USING gin (dialog_history);
    """)

    conn.commit()
    print("   ✅ Index created!")

    # Verify change
    print("\n5. Verifying migration...")
    cursor.execute("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'dialog_history';
    """)

    result = cursor.fetchone()
    print(f"   Column: {result[0]}")
    print(f"   Type: {result[1]}")
    print(f"   Default: {result[2]}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 80)
    print("\nsessions.dialog_history JSONB column is ready for Iteration 42!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
