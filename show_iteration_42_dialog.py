#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Display first completed Iteration 42 dialog with Q&A pairs
"""

import psycopg2
import json
import os

os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'

print("=" * 80)
print("ITERATION 42: FIRST DIALOG WITH Q&A PAIRS")
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

    # Get first completed session from Iteration 42
    print("\nSearching for completed Iteration 42 sessions...")
    cursor.execute("""
        SELECT id, anketa_id, dialog_history, interview_data
        FROM sessions
        WHERE telegram_id = 999999998
          AND status = 'completed'
          AND dialog_history IS NOT NULL
          AND dialog_history != '[]'::jsonb
        ORDER BY id ASC
        LIMIT 1
    """)

    row = cursor.fetchone()

    if not row:
        print("\n[INFO] No completed dialogs yet. Still running...")
        print("Check back in a few minutes!")
        cursor.close()
        conn.close()
        exit(0)

    session_id, anketa_id, dialog_history_json, interview_data_json = row

    # Parse JSON
    dialog_history = json.loads(dialog_history_json) if isinstance(dialog_history_json, str) else dialog_history_json
    interview_data = json.loads(interview_data_json) if isinstance(interview_data_json, str) else interview_data_json

    print(f"\n[SUCCESS] Found completed dialog!")
    print(f"Session ID: {session_id}")
    print(f"Anketa ID: {anketa_id}")
    print(f"Dialog messages: {len(dialog_history)}")

    # Display dialog
    print("\n" + "=" * 80)
    print("FULL DIALOG HISTORY (Question-Answer Pairs)")
    print("=" * 80)

    for i, message in enumerate(dialog_history, 1):
        role = message.get('role', 'unknown')
        text = message.get('text', '')
        timestamp = message.get('timestamp', '')

        if role == 'interviewer':
            print(f"\n[Q{i//2 + 1}] INTERVIEWER:")
            print(f"    {text}")
        elif role == 'user':
            print(f"\n[A{i//2}] USER:")
            # Truncate long answers for readability
            if len(text) > 500:
                print(f"    {text[:500]}...")
                print(f"    [... truncated, total {len(text)} chars]")
            else:
                print(f"    {text}")

    # Display collected interview data
    print("\n" + "=" * 80)
    print("COLLECTED INTERVIEW DATA")
    print("=" * 80)

    for field_name, value in interview_data.items():
        print(f"\n[FIELD] {field_name}:")
        if len(str(value)) > 300:
            print(f"  {str(value)[:300]}...")
        else:
            print(f"  {value}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("DIALOG DISPLAY COMPLETE")
    print("=" * 80)

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
