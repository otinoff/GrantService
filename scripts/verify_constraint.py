#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая проверка что UNIQUE constraint установлен
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, database='grantservice',
    user='postgres', password='root'
)
cursor = conn.cursor()

print("="*80)
print("ПРОВЕРКА: UNIQUE constraint на user_answers")
print("="*80)

# Проверяем constraint
cursor.execute("""
    SELECT
        tc.constraint_name,
        tc.constraint_type,
        string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
    WHERE tc.table_schema = 'public'
        AND tc.table_name = 'user_answers'
        AND tc.constraint_name = 'unique_session_question'
    GROUP BY tc.constraint_name, tc.constraint_type;
""")

result = cursor.fetchone()

if result:
    print(f"\n[OK] Constraint найден:")
    print(f"  Название: {result[0]}")
    print(f"  Тип: {result[1]}")
    print(f"  Колонки: {result[2]}")
    print("\n[SUCCESS] БАГ #1 ИСПРАВЛЕН!")
    print("          Дубликаты ответов теперь невозможны")
else:
    print("\n[ERROR] Constraint НЕ найден!")
    print("        Миграция не применена или откатилась")

# Проверяем что в БД нет дубликатов
cursor.execute("""
    SELECT session_id, question_id, COUNT(*)
    FROM user_answers
    GROUP BY session_id, question_id
    HAVING COUNT(*) > 1;
""")

dups = cursor.fetchall()

if dups:
    print(f"\n[WARN] Найдено {len(dups)} дубликатов в данных:")
    for d in dups[:3]:
        print(f"  session_id={d[0]}, question_id={d[1]}, count={d[2]}")
else:
    print(f"\n[OK] Дубликатов в данных НЕ найдено")

# Считаем всего записей
cursor.execute("SELECT COUNT(*) FROM user_answers;")
total = cursor.fetchone()[0]
print(f"\nВсего записей в user_answers: {total}")

cursor.close()
conn.close()

print("\n" + "="*80 + "\n")
