#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка подсказок в вопросах интервью
"""

import sys
import os
import sqlite3

# Добавляем путь к модулю БД
import pathlib
current_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Путь к БД
db_path = current_dir / "data" / "grantservice.db"

def check_hints():
    """Проверить наличие подсказок в вопросах интервью"""
    
    print("=" * 60)
    print("  ПРОВЕРКА ПОДСКАЗОК В ВОПРОСАХ ИНТЕРВЬЮ")
    print("=" * 60)
    
    if not db_path.exists():
        print(f"ERROR: База данных не найдена: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы
        cursor.execute("PRAGMA table_info(interview_questions)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"\nКолонки таблицы interview_questions: {columns}")
        
        if 'hint_text' not in columns:
            print("ERROR: Колонка hint_text отсутствует в таблице!")
            return
        
        # Получаем все вопросы
        cursor.execute("""
            SELECT question_number, question_text, hint_text 
            FROM interview_questions 
            WHERE is_active = 1
            ORDER BY question_number
        """)
        
        questions = cursor.fetchall()
        print(f"\nНайдено активных вопросов: {len(questions)}")
        
        # Анализируем подсказки
        questions_without_hints = []
        questions_with_hints = []
        
        for q_num, q_text, hint in questions:
            if hint and hint.strip():
                questions_with_hints.append(q_num)
                print(f"  [OK] Вопрос {q_num}: есть подсказка ({len(hint)} символов)")
            else:
                questions_without_hints.append(q_num)
                print(f"  [!!] Вопрос {q_num}: НЕТ подсказки")
        
        print(f"\n=== СТАТИСТИКА ===")
        print(f"Всего вопросов: {len(questions)}")
        print(f"С подсказками: {len(questions_with_hints)}")
        print(f"Без подсказок: {len(questions_without_hints)}")
        
        if questions_without_hints:
            print(f"\nВопросы без подсказок: {questions_without_hints}")
        else:
            print("\nОтлично! Все вопросы имеют подсказки!")
            
        # Показываем примеры подсказок
        print(f"\n=== ПРИМЕРЫ ПОДСКАЗОК ===")
        cursor.execute("""
            SELECT question_number, question_text, hint_text 
            FROM interview_questions 
            WHERE is_active = 1 AND hint_text IS NOT NULL AND hint_text != ''
            ORDER BY question_number
            LIMIT 3
        """)
        
        for q_num, q_text, hint in cursor.fetchall():
            print(f"\nВопрос {q_num}: {q_text[:50]}...")
            print(f"Подсказка: {hint[:100]}...")
            
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_hints()