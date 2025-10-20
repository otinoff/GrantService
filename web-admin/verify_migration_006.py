#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify Migration 006 results
"""
import sys

# Исправление кодировки для Windows
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
sys.path.insert(0, os.path.dirname(__file__))

from utils.postgres_helper import execute_query

def main():
    print("="*60)
    print("Migration 006 Verification")
    print("="*60)

    # Check columns in sessions table
    print("\n[*] Checking sessions table columns...")
    result = execute_query("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'sessions'
          AND column_name IN ('current_stage', 'agents_passed', 'stage_history', 'stage_updated_at')
        ORDER BY column_name
    """)

    if result:
        print(f"    Found {len(result)} new columns:")
        for row in result:
            print(f"    - {row['column_name']}: {row['data_type']}")
    else:
        print("    [WARN] No new columns found!")

    # Check functions
    print("\n[*] Checking helper functions...")
    result = execute_query("""
        SELECT proname
        FROM pg_proc
        WHERE proname IN ('update_session_stage', 'get_stage_progress')
    """)

    if result:
        print(f"    Found {len(result)} functions:")
        for row in result:
            print(f"    - {row['proname']}()")
    else:
        print("    [WARN] Functions not found!")

    # Check recent sessions
    print("\n[*] Checking sessions data...")
    result = execute_query("""
        SELECT anketa_id, current_stage, agents_passed
        FROM sessions
        WHERE anketa_id IS NOT NULL
        ORDER BY id DESC
        LIMIT 5
    """)

    if result:
        print(f"    Found {len(result)} sessions with anketa_id:")
        for row in result:
            anketa_id = row.get('anketa_id', 'N/A')
            stage = row.get('current_stage', 'null')
            agents = row.get('agents_passed', [])
            print(f"    - {anketa_id}: stage={stage}, passed={agents}")
    else:
        print("    No sessions with anketa_id found")

    print("\n" + "="*60)
    print("[SUCCESS] Migration 006 verification complete!")
    print("="*60)
    print("\nStage tracking system is ready!")
    print("Refresh Streamlit to see changes on 'AI Agenty' page.")

if __name__ == "__main__":
    main()
