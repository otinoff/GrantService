#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки содержимого базы данных на сервере
"""

import sqlite3
import os
from datetime import datetime

def check_database_content():
    """Проверяет содержимое базы данных на сервере"""
    
    # Путь к базе данных на сервере
    db_path = '/var/GrantService/data/grantservice.db'
    
    print("=" * 80)
    print("ПРОВЕРКА СОДЕРЖИМОГО БАЗЫ ДАННЫХ НА СЕРВЕРЕ")
    print("=" * 80)
    print(f"Файл БД: {db_path}")
    
    # Проверяем существование файла
    if not os.path.exists(db_path):
        print("❌ ФАЙЛ БАЗЫ ДАННЫХ НЕ НАЙДЕН!")
        return
    
    # Дата модификации
    mtime = os.path.getmtime(db_path)
    mod_time = datetime.fromtimestamp(mtime)
    print(f"Дата модификации: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Подключаемся к базе
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Получаем активные вопросы
        cursor.execute("""
            SELECT question_number, question_text, hint_text, field_name, question_type
            FROM interview_questions 
            WHERE is_active = 1 
            ORDER BY question_number
        """)
        
        questions = cursor.fetchall()
        
        print(f"\nНайдено активных вопросов: {len(questions)}")
        print("-" * 80)
        
        # Проверяем каждый вопрос
        for i, row in enumerate(questions, 1):
            q_num = row['question_number']
            q_text = row['question_text']
            hint_text = row['hint_text']
            field_name = row['field_name']
            q_type = row['question_type']
            
            print(f"\n{i}. Вопрос {q_num}:")
            print(f"   Текст: {q_text[:60]}{'...' if len(q_text) > 60 else ''}")
            print(f"   Поле: {field_name}")
            print(f"   Тип: {q_type}")
            
            if hint_text and hint_text.strip():
                hint_preview = hint_text[:80] + "..." if len(hint_text) > 80 else hint_text
                print(f"   Подсказка: {hint_preview}")
                print(f"   ✅ [OK] Подсказка присутствует")
            else:
                print(f"   Подсказка: [НЕТ]")
                print(f"   ❌ [ERROR] Подсказка отсутствует!")
        
        # Статистика
        questions_with_hints = sum(1 for row in questions if row['hint_text'] and row['hint_text'].strip())
        questions_without_hints = len(questions) - questions_with_hints
        
        print("\n" + "=" * 80)
        print("СТАТИСТИКА:")
        print("-" * 80)
        print(f"Всего активных вопросов: {len(questions)}")
        print(f"Вопросов с подсказками: {questions_with_hints}")
        print(f"Вопросов БЕЗ подсказок: {questions_without_hints}")
        
        if questions_without_hints == 0:
            print("\n🎉 ВСЕ АКТИВНЫЕ ВОПРОСЫ ИМЕЮТ ПОДСКАЗКИ!")
            print("Если в Telegram боте подсказки не отображаются, проблема в коде бота.")
        else:
            print(f"\n❌ НАЙДЕНО {questions_without_hints} ВОПРОСОВ БЕЗ ПОДСКАЗОК!")
            print("Нужно обновить базу данных.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ ОШИБКА ПОДКЛЮЧЕНИЯ К БАЗЕ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_content()