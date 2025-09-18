#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для анализа содержимого базы данных
"""

import sqlite3
import os

def analyze_database():
    """Анализирует содержимое базы данных"""
    
    # Путь к базе данных
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'grantservice.db')
    
    print("=" * 80)
    print("АНАЛИЗ БАЗЫ ДАННЫХ GRANTSERVICE")
    print("=" * 80)
    print(f"\nФайл БД: {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        print("ERROR: ФАЙЛ БАЗЫ ДАННЫХ НЕ НАЙДЕН!")
        return
    
    print(f"OK: Файл существует, размер: {os.path.getsize(db_path):,} байт")
    
    # Подключаемся к базе
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Проверяем структуру таблицы interview_questions
    print("\n" + "=" * 80)
    print("1. СТРУКТУРА ТАБЛИЦЫ interview_questions:")
    print("-" * 80)
    
    cursor.execute("PRAGMA table_info(interview_questions)")
    columns = cursor.fetchall()
    
    print("Колонки в таблице:")
    for col in columns:
        print(f"  - {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else 'NULL':<10} default={col[4]}")
    
    # Проверяем наличие колонки hint_text
    has_hint_column = any(col[1] == 'hint_text' for col in columns)
    if has_hint_column:
        print("\nOK: Колонка hint_text СУЩЕСТВУЕТ")
    else:
        print("\nERROR: Колонка hint_text НЕ НАЙДЕНА!")
    
    # 2. Анализируем вопросы
    print("\n" + "=" * 80)
    print("2. АНАЛИЗ ВОПРОСОВ:")
    print("-" * 80)
    
    # Общая статистика
    cursor.execute("SELECT COUNT(*) FROM interview_questions")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = 1")
    active = cursor.fetchone()[0]
    
    print(f"Всего вопросов: {total}")
    print(f"Активных вопросов: {active}")
    
    # 3. Детальный анализ активных вопросов
    print("\n" + "=" * 80)
    print("3. ДЕТАЛЬНЫЙ АНАЛИЗ АКТИВНЫХ ВОПРОСОВ:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            question_number,
            SUBSTR(question_text, 1, 60) as question,
            hint_text,
            question_type
        FROM interview_questions 
        WHERE is_active = 1
        ORDER BY question_number
    """)
    
    questions = cursor.fetchall()
    
    questions_with_hints = 0
    questions_without_hints = 0
    
    for q in questions:
        q_num = q[0]
        q_text = q[1]
        hint = q[2]
        q_type = q[3]
        
        if hint and hint.strip():
            hint_preview = hint[:50] + "..." if len(hint) > 50 else hint
            print(f"\nВопрос {q_num:2}: [+] ЕСТЬ ПОДСКАЗКА")
            print(f"  Текст: {q_text}...")
            print(f"  Подсказка: {hint_preview}")
            print(f"  Тип: {q_type}")
            questions_with_hints += 1
        else:
            print(f"\nВопрос {q_num:2}: [-] НЕТ ПОДСКАЗКИ")
            print(f"  Текст: {q_text}...")
            print(f"  Тип: {q_type}")
            questions_without_hints += 1
    
    # 4. Итоговая статистика
    print("\n" + "=" * 80)
    print("4. ИТОГОВАЯ СТАТИСТИКА:")
    print("-" * 80)
    print(f"[+] Вопросов с подсказками: {questions_with_hints}")
    print(f"[-] Вопросов БЕЗ подсказок: {questions_without_hints}")
    print(f"[*] Всего активных вопросов: {questions_with_hints + questions_without_hints}")
    
    # 5. Другие важные таблицы
    print("\n" + "=" * 80)
    print("5. ДРУГИЕ ТАБЛИЦЫ В БАЗЕ:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]:30} ({count} записей)")
    
    conn.close()
    
    # 6. Рекомендации
    print("\n" + "=" * 80)
    print("6. РЕКОМЕНДАЦИИ:")
    print("-" * 80)
    
    if questions_without_hints > 0:
        print(f"WARNING: Необходимо добавить подсказки для {questions_without_hints} вопросов")
        print("   Запустите: python scripts/update_hints_in_local_db.py")
    else:
        print("OK: Все вопросы имеют подсказки!")
    
    if not has_hint_column:
        print("CRITICAL ERROR: Отсутствует колонка hint_text!")
        print("   Необходимо обновить структуру БД")
    
    print("\n" + "=" * 80)
    print("АНАЛИЗ ЗАВЕРШЁН")
    print("=" * 80)

if __name__ == "__main__":
    analyze_database()