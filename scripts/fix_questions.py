#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления вопросов интервью
"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / 'data' / 'grantservice.db'

print("=" * 60)
print("FIXING INTERVIEW QUESTIONS")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Получаем текущий статус вопросов
cursor.execute("""
    SELECT question_number, question_text, is_active 
    FROM interview_questions 
    WHERE question_number >= 15
    ORDER BY question_number
""")

print("\nQuestions 15-24 status:")
for row in cursor.fetchall():
    status = "ACTIVE" if row[2] else "INACTIVE"
    print(f"  Q{row[0]}: {status} - {row[1][:50]}...")

# Активируем вопрос 15
print("\n[FIXING] Activating question 15...")
cursor.execute("""
    UPDATE interview_questions 
    SET is_active = 1 
    WHERE question_number = 15
""")

conn.commit()
print(f"✓ Question 15 activated")

# Проверяем результат
cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = 1")
active_count = cursor.fetchone()[0]
print(f"\nTotal active questions now: {active_count}")

conn.close()

print("\n" + "=" * 60)
print("DONE! Question 15 is now active.")
print("=" * 60)