#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузить анкету Натальи в локальную БД PostgreSQL
"""

import psycopg2
import json
import sys
from pathlib import Path
from datetime import datetime

def load_anketa():
    """Загрузить анкету в БД"""

    # Read anketa
    anketa_file = Path(__file__).parent.parent / "test_data" / "natalia_anketa_20251012.json"
    print(f"Reading anketa from: {anketa_file}")

    with open(anketa_file, 'r', encoding='utf-8') as f:
        anketa_data = json.load(f)

    anketa_id = anketa_data.get('anketa_id')
    print(f"Anketa ID: {anketa_id}")

    # Connect to local DB
    print("\nConnecting to local PostgreSQL...")
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='grantservice',
        user='postgres',
        password='root',
        client_encoding='utf8'
    )
    print("[OK] Connected!")

    cursor = conn.cursor()

    # Check if anketa already exists
    cursor.execute("""
        SELECT anketa_id, status, started_at
        FROM sessions
        WHERE anketa_id = %s;
    """, (anketa_id,))
    existing = cursor.fetchone()

    if existing:
        print(f"\n[WARNING] Anketa {anketa_id} already exists:")
        print(f"  Status: {existing[1]}")
        print(f"  Started: {existing[2]}")

        user_input = input("\nOverwrite? (y/n): ")
        if user_input.lower() != 'y':
            print("Cancelled.")
            cursor.close()
            conn.close()
            return False

        # Delete existing
        cursor.execute("DELETE FROM sessions WHERE anketa_id = %s;", (anketa_id,))
        print(f"[OK] Deleted existing anketa")

    # Insert new anketa
    print(f"\nInserting anketa {anketa_id}...")

    insert_query = """
        INSERT INTO sessions (
            anketa_id,
            telegram_id,
            interview_data,
            status,
            current_stage,
            project_name,
            started_at,
            last_activity,
            completion_status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
    """

    # Extract project name from interview data
    interview_data = anketa_data.get('interview_data', {})
    project_name = interview_data.get('project_name', 'Стрельба из лука - спортивно-патриотическое воспитание')

    cursor.execute(insert_query, (
        anketa_data.get('anketa_id'),
        826960528,  # Natalia_bruzzzz real telegram_id
        json.dumps(interview_data),
        'completed',
        'completed',
        project_name,
        datetime.now(),
        datetime.now(),
        'completed'
    ))

    conn.commit()
    print("[OK] Anketa inserted successfully!")

    # Verify
    cursor.execute("""
        SELECT anketa_id, status, project_name,
               LENGTH(interview_data::text) as interview_size
        FROM sessions
        WHERE anketa_id = %s;
    """, (anketa_id,))
    result = cursor.fetchone()

    print(f"\n[VERIFY] Anketa in database:")
    print(f"  Anketa ID: {result[0]}")
    print(f"  Status: {result[1]}")
    print(f"  Project: {result[2]}")
    print(f"  Interview data: {result[3]} chars")

    cursor.close()
    conn.close()

    print("\n[SUCCESS] Ready for E2E test!")
    return True

if __name__ == "__main__":
    success = load_anketa()
    sys.exit(0 if success else 1)
