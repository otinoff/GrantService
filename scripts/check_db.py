#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки БД
"""

import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).parent.parent / 'data' / 'grantservice.db'

print("=" * 60)
print("DATABASE CHECK / ПРОВЕРКА БАЗЫ ДАННЫХ")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Проверяем количество заявок
cursor.execute("SELECT COUNT(*) FROM grant_applications")
total_applications = cursor.fetchone()[0]
print(f"\nGRANT APPLICATIONS: {total_applications}")

if total_applications > 0:
    cursor.execute("""
        SELECT id, application_number, title, status, created_at
        FROM grant_applications
        ORDER BY created_at DESC
        LIMIT 5
    """)
    print("\nLast 5 applications:")
    for row in cursor.fetchall():
        print(f"  ID {row[0]}: {row[1]} - {row[2][:40]}...")

# 2. Проверяем вопросы интервью
cursor.execute("SELECT COUNT(*) FROM interview_questions")
total_questions = cursor.fetchone()[0]
print(f"\nTOTAL QUESTIONS: {total_questions}")

cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = 1")
active_questions = cursor.fetchone()[0]
print(f"   Active: {active_questions}")

# Показываем все вопросы
cursor.execute("""
    SELECT question_number, question_text, is_active
    FROM interview_questions
    ORDER BY question_number
""")
print("\nQuestions list:")
for row in cursor.fetchall():
    status = "YES" if row[2] else "NO"
    print(f"  {row[0]:2d}. [Active: {status}] {row[1][:50]}...")

# Проверяем есть ли вопрос 15
cursor.execute("SELECT * FROM interview_questions WHERE question_number = 15")
q15 = cursor.fetchone()
if q15:
    print(f"\n[OK] Question 15 found: {q15[2][:50]}...")
else:
    print("\n[ERROR] Question 15 is missing!")

# 3. Проверяем последние сессии
cursor.execute("""
    SELECT COUNT(*) FROM sessions
    WHERE date(started_at) = date('now', 'localtime')
""")
today_sessions = cursor.fetchone()[0]
print(f"\nTODAY SESSIONS: {today_sessions}")

conn.close()

print("\n" + "=" * 60)