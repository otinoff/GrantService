#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Применение миграции 002: добавление UNIQUE constraint
"""

import psycopg2
import os

os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'
os.environ['PGDATABASE'] = 'grantservice'
os.environ['PGUSER'] = 'postgres'
os.environ['PGPASSWORD'] = 'root'

print("="*80)
print("МИГРАЦИЯ 002: Добавление UNIQUE constraint на user_answers")
print("="*80)

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='grantservice',
        user='postgres',
        password='root'
    )
    conn.autocommit = False
    cursor = conn.cursor()

    print("\n[1/4] Проверка наличия дубликатов...")
    cursor.execute("""
        SELECT session_id, question_id, COUNT(*)
        FROM user_answers
        GROUP BY session_id, question_id
        HAVING COUNT(*) > 1;
    """)

    duplicates = cursor.fetchall()

    if duplicates:
        print(f"[ERROR] Найдено {len(duplicates)} дубликатов!")
        for dup in duplicates[:5]:
            print(f"  session_id={dup[0]}, question_id={dup[1]}, count={dup[2]}")
        print("\nНеобходимо удалить дубликаты перед добавлением constraint")
        cursor.close()
        conn.close()
        exit(1)
    else:
        print("[OK] Дубликатов не найдено")

    print("\n[2/4] Проверка существования constraint...")
    cursor.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
            AND table_name = 'user_answers'
            AND constraint_name = 'unique_session_question';
    """)

    existing = cursor.fetchone()

    if existing:
        print("[WARN] Constraint 'unique_session_question' уже существует")
        cursor.close()
        conn.close()
        print("\n[OK] Миграция уже применена")
        exit(0)
    else:
        print("[OK] Constraint не существует, можно добавлять")

    print("\n[3/4] Добавление UNIQUE constraint...")
    cursor.execute("""
        ALTER TABLE user_answers
        ADD CONSTRAINT unique_session_question
        UNIQUE (session_id, question_id);
    """)
    print("[OK] Constraint добавлен")

    print("\n[4/4] Добавление комментария...")
    cursor.execute("""
        COMMENT ON CONSTRAINT unique_session_question ON user_answers IS
        'Предотвращает дубликаты ответов: один пользователь может ответить на вопрос только один раз в рамках сессии';
    """)
    print("[OK] Комментарий добавлен")

    # Коммитим изменения
    conn.commit()

    print("\n" + "="*80)
    print("МИГРАЦИЯ 002 УСПЕШНО ПРИМЕНЕНА")
    print("="*80)

    # Проверяем результат
    print("\nПроверка результата:")
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
        print(f"[OK] {result[1]}: {result[0]}")
        print(f"     Колонки: {result[2]}")

    cursor.close()
    conn.close()

    print("\n[SUCCESS] Баг #1 исправлен!")
    print("          Теперь невозможно добавить дублирующийся ответ на вопрос\n")

except Exception as e:
    print(f"\n[ERROR] Ошибка миграции: {e}")
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    exit(1)
