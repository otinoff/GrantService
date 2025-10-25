#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show sample anketa from Iteration 41"""

import psycopg2
import json

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='root',
    database='grantservice'
)

cur = conn.cursor()
cur.execute("""
    SELECT anketa_id, interview_data
    FROM sessions
    WHERE telegram_id = 999999997 AND status = 'completed'
    ORDER BY id DESC
    LIMIT 1
""")

row = cur.fetchone()
anketa_id = row[0]
interview_data = json.loads(row[1]) if isinstance(row[1], str) else row[1]

# Маппинг полей на русские вопросы
questions = {
    'project_name': 'Как называется ваш проект?',
    'organization': 'Подтвердите название вашей организации',
    'region': 'Подтвердите регион реализации',
    'problem': 'Опишите подробно социальную проблему',
    'solution': 'Опишите ваше решение этой проблемы',
    'goals': 'Перечислите конкретные цели проекта',
    'activities': 'Опишите основные мероприятия проекта',
    'results': 'Опишите ожидаемые результаты проекта',
    'budget': 'Укажите общий бюджет проекта в рублях',
    'budget_breakdown': 'Распределите бюджет по категориям'
}

print("=" * 100)
print(f"ГОТОВАЯ АНКЕТА: {anketa_id}")
print("=" * 100)
print()

for field_name, answer in interview_data.items():
    question = questions.get(field_name, field_name)

    print(f"📋 ВОПРОС: {question}")
    print("-" * 100)
    print(f"💬 ОТВЕТ:")
    print(answer)
    print()
    print("=" * 100)
    print()

conn.close()

print(f"\n✅ Всего полей в анкете: {len(interview_data)}")
print(f"✅ Средняя длина ответа: {sum(len(v) for v in interview_data.values()) // len(interview_data)} символов")
