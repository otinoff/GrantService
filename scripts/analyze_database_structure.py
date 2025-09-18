#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для детального анализа структуры базы данных и получения подсказок
"""

import sqlite3
import os
import json

def analyze_database_structure():
    """Анализирует структуру базы данных и выводит подсказки"""
    
    # Путь к базе данных
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'grantservice.db')
    
    print("=" * 80)
    print("ДЕТАЛЬНЫЙ АНАЛИЗ СТРУКТУРЫ БАЗЫ ДАННЫХ")
    print("=" * 80)
    print(f"\nФайл БД: {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        print("[ERROR] ФАЙЛ БАЗЫ ДАННЫХ НЕ НАЙДЕН!")
        return
    
    print(f"[OK] Файл существует, размер: {os.path.getsize(db_path):,} байт")
    
    # Подключаемся к базе
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Структура таблицы interview_questions
    print("\n" + "=" * 80)
    print("1. СТРУКТУРА ТАБЛИЦЫ interview_questions:")
    print("-" * 80)
    
    cursor.execute("PRAGMA table_info(interview_questions)")
    columns = cursor.fetchall()
    
    print("Колонки в таблице:")
    for col in columns:
        print(f"  - {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else 'NULL':<10} default={col[4]}")
    
    # 2. Все вопросы с подсказками
    print("\n" + "=" * 80)
    print("2. ВСЕ ВОПРОСЫ С ПОДСКАЗКАМИ:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            id,
            question_number,
            question_text,
            field_name,
            question_type,
            hint_text,
            is_active,
            is_required
        FROM interview_questions 
        ORDER BY question_number
    """)
    
    questions = cursor.fetchall()
    
    active_questions = 0
    inactive_questions = 0
    questions_with_hints = 0
    questions_without_hints = 0
    
    for row in questions:
        q_id = row['id']
        q_num = row['question_number']
        q_text = row['question_text']
        field_name = row['field_name']
        q_type = row['question_type']
        hint = row['hint_text']
        is_active = row['is_active']
        is_required = row['is_required']
        
        status = "АКТИВЕН" if is_active else "НЕАКТИВЕН"
        required = "ОБЯЗАТЕЛЬНЫЙ" if is_required else "НЕОБЯЗАТЕЛЬНЫЙ"
        
        print(f"\nВопрос ID {q_id}:")
        print(f"  Номер: {q_num}")
        print(f"  Текст: {q_text}")
        print(f"  Поле: {field_name}")
        print(f"  Тип: {q_type}")
        print(f"  Статус: {status}")
        print(f"  Обязательность: {required}")
        
        if hint and hint.strip():
            print(f"  Подсказка: {hint}")
            if is_active:
                questions_with_hints += 1
        else:
            print(f"  Подсказка: [НЕТ]")
            if is_active:
                questions_without_hints += 1
        
        if is_active:
            active_questions += 1
        else:
            inactive_questions += 1
    
    # 3. Только активные вопросы
    print("\n" + "=" * 80)
    print("3. ТОЛЬКО АКТИВНЫЕ ВОПРОСЫ:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            question_number,
            question_text,
            hint_text,
            field_name
        FROM interview_questions 
        WHERE is_active = 1
        ORDER BY question_number
    """)
    
    active_questions_data = cursor.fetchall()
    
    print(f"Активных вопросов: {len(active_questions_data)}")
    print("\nПодробная информация по активным вопросам:")
    
    for i, row in enumerate(active_questions_data, 1):
        q_num = row['question_number']
        q_text = row['question_text'][:60] + "..." if len(row['question_text']) > 60 else row['question_text']
        hint = row['hint_text']
        field_name = row['field_name']
        
        print(f"\n{i}. Вопрос {q_num}:")
        print(f"   Текст: {q_text}")
        print(f"   Поле: {field_name}")
        if hint and hint.strip():
            hint_preview = hint[:100] + "..." if len(hint) > 100 else hint
            print(f"   Подсказка: {hint_preview}")
        else:
            print(f"   Подсказка: [НЕТ]")
    
    # 4. Статистика
    print("\n" + "=" * 80)
    print("4. СТАТИСТИКА:")
    print("-" * 80)
    print(f"Всего вопросов: {len(questions)}")
    print(f"Активных вопросов: {active_questions}")
    print(f"Неактивных вопросов: {inactive_questions}")
    print(f"Активных вопросов с подсказками: {questions_with_hints}")
    print(f"Активных вопросов БЕЗ подсказок: {questions_without_hints}")
    
    # 5. Другие таблицы
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
        print(f"[WARNING] Найдено {questions_without_hints} активных вопросов БЕЗ подсказок")
        print("   Рекомендуется добавить подсказки для всех активных вопросов")
    else:
        print("[OK] Все активные вопросы имеют подсказки")
    
    print("\n[INFO] Для проверки отображения в Telegram боте:")
    print("   1. Убедитесь, что бот использует функцию get_interview_questions()")
    print("   2. Проверьте, правильно ли обрабатывается hint_text в коде бота")
    print("   3. Убедитесь, что база данных на сервере обновлена")

if __name__ == "__main__":
    analyze_database_structure()