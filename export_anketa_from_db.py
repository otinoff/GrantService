#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Anketa from Database

Exports anketa.txt file from database session.
Usage:
    python export_anketa_from_db.py <session_id>
    python export_anketa_from_db.py 607
"""

import sys
import os
import psycopg2
import json
sys.path.insert(0, ".")

from shared.telegram_utils.file_generators import generate_anketa_txt

def export_anketa(session_id: int, output_file: str = None):
    """Export anketa from database session."""

    print(f"\nExporting anketa for session ID: {session_id}")
    print("="*60)

    # Connect to database
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="grantservice",
        user="postgres",
        password="root"
    )
    cursor = conn.cursor()

    # Get session data from database
    query = """
        SELECT
            id,
            anketa_id,
            telegram_id,
            project_name,
            interview_data,
            answers_data,
            started_at,
            completed_at
        FROM sessions
        WHERE id = %s
    """

    cursor.execute(query, (session_id,))
    result = cursor.fetchall()

    if not result:
        print(f"ERROR: Session {session_id} not found!")
        return None

    session = result[0]

    print(f"Anketa ID: {session[1]}")
    print(f"Telegram ID: {session[2]}")
    print(f"Project Name: {session[3] or '(не указано)'}")
    print(f"Started: {session[6]}")
    print(f"Completed: {session[7]}")
    print()

    # Get interview data (answers)
    interview_data = session[4] or {}
    answers_data = session[5] or {}

    if not interview_data and not answers_data:
        print("WARNING: No interview data found!")
        return None

    print(f"Interview data keys: {list(interview_data.keys())}")
    print(f"Answers data keys: {list(answers_data.keys())}")
    print()

    # Prepare data for anketa generation
    anketa_data = {
        'anketa_id': session[1],
        'project_name': session[3] or 'Проект без названия',
        'answers_data': interview_data,  # Use interview_data as answers
        'interview_data': interview_data,
        'completed_at': str(session[7]) if session[7] else str(session[6])
    }

    # Generate anketa.txt
    anketa_txt = generate_anketa_txt(anketa_data)

    # Save to file
    if output_file is None:
        output_file = f"anketa_{session_id}_from_db.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(anketa_txt)

    print(f"✅ Anketa exported to: {output_file}")
    print(f"   File size: {len(anketa_txt)} characters")
    print()

    # Show preview
    print("Preview (first 500 chars):")
    print("-"*60)
    print(anketa_txt[:500])
    print("...")
    print("-"*60)

    # Close database connection
    cursor.close()
    conn.close()

    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_anketa_from_db.py <session_id>")
        print("\nExample:")
        print("  python export_anketa_from_db.py 607")
        print("\nRecent sessions:")

        # Show recent sessions
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="grantservice",
            user="postgres",
            password="root"
        )
        cursor = conn.cursor()

        query = """
            SELECT id, telegram_id, anketa_id, project_name, completion_status, started_at
            FROM sessions
            ORDER BY started_at DESC
            LIMIT 5
        """
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            print("\nID  | Telegram ID | Anketa ID                        | Status      | Started At")
            print("-"*90)
            for row in results:
                print(f"{row[0]:<4}| {row[1]:<12}| {row[2]:<33}| {row[4]:<12}| {row[5]}")

        cursor.close()
        conn.close()

        sys.exit(1)

    session_id = int(sys.argv[1])
    export_anketa(session_id)
