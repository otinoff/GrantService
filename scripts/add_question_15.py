#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления вопроса 15 о грантовых направлениях
"""

import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).parent.parent / 'data' / 'grantservice.db'

print("=" * 60)
print("ADDING QUESTION 15 - GRANT DIRECTIONS")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Сначала сдвигаем все вопросы после 14 на один вперед
print("\n[STEP 1] Shifting questions 15+ to 16+...")
cursor.execute("""
    UPDATE interview_questions 
    SET question_number = question_number + 1 
    WHERE question_number >= 15
""")
print(f"✓ Shifted {cursor.rowcount} questions")

# Грантовые направления
grant_directions = [
    "Поддержка проектов в области науки, образования, просвещения",
    "Развитие институтов гражданского общества",  
    "Развитие общественной дипломатии и поддержка соотечественников",
    "Поддержка социально значимых инициатив и проектов",
    "Развитие культуры и искусства",
    "Поддержка проектов в сфере благотворительности и поддержки уязвимых групп",
    "Поддержка проектов в области охраны окружающей среды и устойчивого развития",
    "Развитие молодежных инициатив и проектов",
    "Поддержка и развитие спорта и массового физкультурного движения",
    "Поддержка инновационных и технологических проектов в общественной сфере",
    "Развитие региональных инициатив и проектов"
]

# Создаем новый вопрос 15
print("\n[STEP 2] Creating new question 15...")

question_text = "Выберите грантовое направление для вашей заявки согласно Методическим рекомендациям Фонда президентских грантов 2025 года"
field_name = "grant_direction"
question_type = "select"
options = json.dumps(grant_directions, ensure_ascii=False)
hint_text = "Выберите одно из 11 направлений, которое наиболее точно соответствует тематике вашего проекта. Это направление будет использовано при формировании заявки."

cursor.execute("""
    INSERT INTO interview_questions (
        question_number, 
        question_text, 
        field_name, 
        question_type, 
        options, 
        hint_text, 
        is_required, 
        is_active
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    15,
    question_text,
    field_name,
    question_type,
    options,
    hint_text,
    1,  # is_required
    1   # is_active
))

print(f"✓ Question 15 added successfully")

# Проверяем результат
print("\n[STEP 3] Verifying results...")
cursor.execute("""
    SELECT question_number, question_text, is_active 
    FROM interview_questions 
    WHERE question_number BETWEEN 14 AND 16
    ORDER BY question_number
""")

print("\nQuestions 14-16:")
for row in cursor.fetchall():
    status = "ACTIVE" if row[2] else "INACTIVE"
    print(f"  Q{row[0]}: [{status}] {row[1][:60]}...")

# Проверяем общее количество активных вопросов
cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = 1")
active_count = cursor.fetchone()[0]
print(f"\nTotal active questions: {active_count}")

# Проверяем общее количество вопросов
cursor.execute("SELECT COUNT(*) FROM interview_questions")
total_count = cursor.fetchone()[0]
print(f"Total questions in database: {total_count}")

conn.commit()
conn.close()

print("\n" + "=" * 60)
print("SUCCESS! Question 15 about grant directions has been added.")
print("All other questions have been shifted accordingly.")
print("=" * 60)