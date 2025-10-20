#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply Migration 006 via web-admin postgres_helper
"""
import sys
import os

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

# Add web-admin to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.postgres_helper import execute_query, execute_update

def main():
    print("="*60)
    print("Migration 006: Stage Tracking System")
    print("="*60)

    migration_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'database', 'migrations', '006_add_stage_tracking.sql'
    )

    print(f"\n[*] Reading migration file...")
    print(f"    Path: {migration_path}")

    try:
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        print(f"    Size: {len(migration_sql)} bytes")

        print("\n[*] Executing migration via postgres_helper...")

        # Execute migration (use execute_update for DDL/DML without results)
        execute_update(migration_sql)

        print("[OK] Migration executed!")

        # Verify
        print("\n[*] Verification:")

        result = execute_query(
            "SELECT COUNT(*) as total, COUNT(current_stage) as with_stage FROM sessions"
        )

        if result:
            total, with_stage = result[0]
            print(f"    Sessions: {total} total, {with_stage} with current_stage")

        # Check recent sessions
        result = execute_query(
            """
            SELECT anketa_id, current_stage, agents_passed
            FROM sessions
            WHERE anketa_id IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 3
            """
        )

        if result:
            print("\n[*] Recent sessions:")
            for row in result:
                anketa_id, stage, agents = row
                print(f"    - {anketa_id}: {stage}")

        # Check functions
        result = execute_query(
            "SELECT COUNT(*) FROM pg_proc WHERE proname IN ('update_session_stage', 'get_stage_progress')"
        )

        if result and result[0][0] == 2:
            print("\n[OK] Helper functions created")

        print("\n" + "="*60)
        print("[SUCCESS] Migration 006 completed!")
        print("="*60)
        print("\nNext steps:")
        print("1. Restart Streamlit (Ctrl+C then python launcher.py)")
        print("2. Refresh browser (F5)")
        print("3. Check 'AI Agenty' page")

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
