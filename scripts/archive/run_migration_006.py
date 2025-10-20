#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply Migration 006: Stage Tracking System
Simple direct SQL execution without encoding issues
"""
import sys

# Исправление кодировки для Windows терминала
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ psycopg2 not installed. Installing...")
    os.system('pip install psycopg2-binary')
    import psycopg2

def main():
    print("="*60)
    print("Migration 006: Stage Tracking System")
    print("="*60)

    # Connection parameters
    conn_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'grantservice',
        'user': 'postgres',
        'password': '1256',
        'client_encoding': 'UTF8'
    }

    try:
        print("\n[*] Connecting to database...")
        conn = psycopg2.connect(**conn_params)
        conn.set_client_encoding('UTF8')
        cur = conn.cursor()

        print("[OK] Connected successfully!")

        # Read migration file with UTF-8 encoding
        migration_path = os.path.join(
            os.path.dirname(__file__),
            'database', 'migrations', '006_add_stage_tracking.sql'
        )

        print(f"\n[*] Reading migration file: {migration_path}")

        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        print(f"    File size: {len(migration_sql)} bytes")

        # Execute migration
        print("\n[*] Executing migration...")
        cur.execute(migration_sql)
        conn.commit()

        print("[OK] Migration executed successfully!")

        # Verify results
        print("\n[*] Verification:")

        # Check sessions table
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(current_stage) as with_stage
            FROM sessions
        """)
        total, with_stage = cur.fetchone()
        print(f"    Sessions: {total} total, {with_stage} with current_stage")

        # Check recent sessions
        cur.execute("""
            SELECT anketa_id, current_stage, agents_passed
            FROM sessions
            WHERE anketa_id IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 3
        """)

        print("\n[*] Recent sessions with stage tracking:")
        for row in cur.fetchall():
            anketa_id, stage, agents = row
            print(f"    - {anketa_id}: {stage}, passed={agents}")

        # Test helper function
        print("\n[*] Testing helper functions:")
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc
                WHERE proname = 'update_session_stage'
            )
        """)
        if cur.fetchone()[0]:
            print("    [OK] Function update_session_stage() created")

        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc
                WHERE proname = 'get_stage_progress'
            )
        """)
        if cur.fetchone()[0]:
            print("    [OK] Function get_stage_progress() created")

        cur.close()
        conn.close()

        print("\n" + "="*60)
        print("[SUCCESS] Migration 006 completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Restart Streamlit admin panel")
        print("2. Check 'AI Agenty' page for stage funnel")
        print("3. Look for anketa_id in interview lists")

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

        if 'conn' in locals():
            conn.rollback()
            conn.close()

        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
