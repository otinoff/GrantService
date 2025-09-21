#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки новых заявок и сессий
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

db_path = Path(__file__).parent.parent / 'data' / 'grantservice.db'

print("=" * 60)
print("CHECKING FOR NEW APPLICATIONS AND SESSIONS")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Проверяем последние сессии
print("\nRECENT SESSIONS (last 7 days):")
cursor.execute("""
    SELECT id, telegram_id, anketa_id, status, 
           questions_answered, total_questions,
           started_at, completed_at
    FROM sessions 
    WHERE datetime(started_at) >= datetime('now', '-7 days')
    ORDER BY started_at DESC
    LIMIT 10
""")

sessions = cursor.fetchall()
if sessions:
    for s in sessions:
        status = s[3] if s[3] else "unknown"
        progress = f"{s[4] or 0}/{s[5] or 0}" if s[4] is not None else "N/A"
        completed = "YES" if s[7] else "NO"
        print(f"  ID {s[0]}: Status={status}, Progress={progress}, Completed={completed}")
        print(f"       Started: {s[6]}, Anketa: {s[2] or 'None'}")
else:
    print("  No recent sessions found")

# 2. Проверяем последние грантовые заявки
print("\nLATEST GRANT APPLICATIONS:")
cursor.execute("""
    SELECT id, application_number, title, status, created_at 
    FROM grant_applications 
    ORDER BY created_at DESC 
    LIMIT 5
""")

apps = cursor.fetchall()
if apps:
    for app in apps:
        print(f"  ID {app[0]}: {app[1]} - Status: {app[3]}")
        print(f"       Created: {app[4]}")
else:
    print("  No applications found")

# 3. Проверяем сессии без заявок
print("\nCOMPLETED SESSIONS WITHOUT APPLICATIONS:")
cursor.execute("""
    SELECT s.id, s.telegram_id, s.anketa_id, s.completed_at,
           u.username, u.first_name, u.last_name
    FROM sessions s
    LEFT JOIN users u ON s.telegram_id = u.telegram_id
    LEFT JOIN grant_applications ga ON s.id = ga.session_id
    WHERE s.status = 'completed' 
          AND s.completed_at IS NOT NULL
          AND ga.id IS NULL
    ORDER BY s.completed_at DESC
    LIMIT 10
""")

orphan_sessions = cursor.fetchall()
if orphan_sessions:
    print("  Found completed sessions without grant applications:")
    for s in orphan_sessions:
        user_info = f"{s[4]} ({s[5]} {s[6]})" if s[4] else f"ID {s[1]}"
        print(f"  Session {s[0]}: User={user_info}, Anketa={s[2]}")
        print(f"       Completed: {s[3]}")
else:
    print("  All completed sessions have applications")

# 4. Проверяем сегодняшние сессии
print("\nTODAY'S SESSIONS:")
cursor.execute("""
    SELECT COUNT(*) FROM sessions 
    WHERE date(started_at) = date('now')
""")
today_count = cursor.fetchone()[0]
print(f"  Sessions started today: {today_count}")

# 5. Проверяем последние изменения в таблицах
print("\nLATEST DATABASE ACTIVITY:")
for table in ['sessions', 'grant_applications', 'users']:
    cursor.execute(f"""
        SELECT MAX(CASE 
            WHEN updated_at IS NOT NULL THEN updated_at 
            WHEN created_at IS NOT NULL THEN created_at
            ELSE NULL
        END) as last_update
        FROM {table}
        WHERE last_update IS NOT NULL
    """)
    result = cursor.fetchone()
    if result and result[0]:
        print(f"  {table}: Last update - {result[0]}")
    else:
        # Альтернативный запрос для таблиц без updated_at
        cursor.execute(f"""
            SELECT MAX(created_at) FROM {table} 
            WHERE created_at IS NOT NULL
        """)
        result = cursor.fetchone()
        if result and result[0]:
            print(f"  {table}: Last created - {result[0]}")

conn.close()

print("\n" + "=" * 60)
print("DIAGNOSIS:")
print("-" * 60)
print("If you see completed sessions without applications,")
print("the bot is not calling save_grant_application() after interview.")
print("Check telegram-bot/handlers/ for the save logic.")
print("=" * 60)