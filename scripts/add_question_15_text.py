#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления вопроса 15 о грантовых направлениях (текстовый ввод номера)
"""

import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).parent.parent / 'data' / 'grantservice.db'

print("=" * 60)
print("UPDATING QUESTION 15 - GRANT DIRECTIONS (TEXT INPUT)")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Сначала удаляем старый вопрос 15 если есть
print("\n[STEP 1] Removing old question 15...")
cursor.execute("DELETE FROM interview_questions WHERE question_number = 15")
print(f"✓ Removed {cursor.rowcount} old question(s)")

# Грантовые направления с номерами
grant_directions_text = """Выберите грантовое направление для вашей заявки (введите номер от 1 до 11):

1. Поддержка проектов в области науки, образования, просвещения
2. Развитие институтов гражданского общества  
3. Развитие общественной дипломатии и поддержка соотечественников
4. Поддержка социально значимых инициатив и проектов
5. Развитие культуры и искусства
6. Поддержка проектов в сфере благотворительности и поддержки уязвимых групп
7. Поддержка проектов в области охраны окружающей среды и устойчивого развития
8. Развитие молодежных инициатив и проектов
9. Поддержка и развитие спорта и массового физкультурного движения
10. Поддержка инновационных и технологических проектов в общественной сфере
11. Развитие региональных инициатив и проектов

Введите только номер направления (например: 5)"""

# Словарь для преобразования номера в название
directions_mapping = {
    "1": "Поддержка проектов в области науки, образования, просвещения",
    "2": "Развитие институтов гражданского общества",
    "3": "Развитие общественной дипломатии и поддержка соотечественников",
    "4": "Поддержка социально значимых инициатив и проектов",
    "5": "Развитие культуры и искусства",
    "6": "Поддержка проектов в сфере благотворительности и поддержки уязвимых групп",
    "7": "Поддержка проектов в области охраны окружающей среды и устойчивого развития",
    "8": "Развитие молодежных инициатив и проектов",
    "9": "Поддержка и развитие спорта и массового физкультурного движения",
    "10": "Поддержка инновационных и технологических проектов в общественной сфере",
    "11": "Развитие региональных инициатив и проектов"
}

# Создаем новый вопрос 15
print("\n[STEP 2] Creating new question 15...")

field_name = "grant_direction"
question_type = "text"  # Текстовый тип для ввода номера
options = json.dumps(directions_mapping, ensure_ascii=False)  # Сохраняем маппинг в options
hint_text = "Внимательно прочитайте все 11 направлений и введите только номер выбранного направления (от 1 до 11)"

# Правила валидации - число от 1 до 11
validation_rules = json.dumps({
    "type": "number_range",
    "min": 1,
    "max": 11,
    "message": "Пожалуйста, введите число от 1 до 11"
}, ensure_ascii=False)

cursor.execute("""
    INSERT INTO interview_questions (
        question_number, 
        question_text, 
        field_name, 
        question_type, 
        options, 
        hint_text, 
        validation_rules,
        is_required, 
        is_active
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    15,
    grant_directions_text,
    field_name,
    question_type,
    options,
    hint_text,
    validation_rules,
    1,  # is_required
    1   # is_active
))

print(f"✓ Question 15 added successfully")

# Проверяем результат
print("\n[STEP 3] Verifying results...")
cursor.execute("""
    SELECT question_number, question_text, question_type, is_active 
    FROM interview_questions 
    WHERE question_number = 15
""")

row = cursor.fetchone()
if row:
    print(f"\nQuestion 15:")
    print(f"  Number: {row[0]}")
    print(f"  Type: {row[2]}")
    print(f"  Active: {'YES' if row[3] else 'NO'}")
    print(f"  Text preview: {row[1][:100]}...")

# Проверяем общее количество активных вопросов
cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = 1")
active_count = cursor.fetchone()[0]
print(f"\nTotal active questions: {active_count}")

conn.commit()
conn.close()

print("\n" + "=" * 60)
print("SUCCESS!")
print("Question 15 has been updated to show numbered list.")
print("User will enter a number, but the direction name will be saved.")
print("=" * 60)

print("\nIMPORTANT: The bot needs to be updated to:")
print("1. Display the full question text with numbered list")
print("2. Accept number input (1-11)")
print("3. Convert number to direction name before saving")
print("4. Save the direction NAME (not number) to database")