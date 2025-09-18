#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки подсказок на сервере
"""

import sqlite3
import os
import sys

def check_hints_on_server():
    """Проверяет подсказки на сервере"""
    
    # Путь к базе данных на сервере
    db_path = '/var/GrantService/data/grantservice.db'
    
    print("=" * 60)
    print("ПРОВЕРКА ПОДСКАЗОК НА СЕРВЕРЕ")
    print("=" * 60)
    print(f"\nФайл БД: {db_path}")
    
    # Проверяем существование файла
    if not os.path.exists(db_path):
        print("❌ ФАЙЛ БАЗЫ ДАННЫХ НЕ НАЙДЕН НА СЕРВЕРЕ!")
        print("Пожалуйста, убедитесь, что база данных загружена на сервер.")
        return
    
    print(f"✅ Файл существует, размер: {os.path.getsize(db_path):,} байт")
    
    # Подключаемся к базе
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Получаем все активные вопросы
        cursor.execute("""
            SELECT question_number, question_text, hint_text, field_name
            FROM interview_questions 
            WHERE is_active = 1 
            ORDER BY question_number
        """)
        
        questions = cursor.fetchall()
        
        print(f"\nНайдено активных вопросов: {len(questions)}")
        print("-" * 60)
        
        # Проверяем каждый вопрос
        for i, row in enumerate(questions, 1):
            q_num = row['question_number']
            q_text = row['question_text'][:50] + "..." if len(row['question_text']) > 50 else row['question_text']
            hint = row['hint_text']
            field_name = row['field_name']
            
            if hint and hint.strip():
                hint_preview = hint[:80] + "..." if len(hint) > 80 else hint
                print(f"\nВопрос {q_num:2}: [+] ЕСТЬ ПОДСКАЗКА")
                print(f"  Текст: {q_text}")
                print(f"  Подсказка: {hint_preview}")
                print(f"  Поле: {field_name}")
            else:
                print(f"\nВопрос {q_num:2}: [-] НЕТ ПОДСКАЗКИ!")
                print(f"  Текст: {q_text}")
                print(f"  Поле: {field_name}")
        
        # Статистика
        questions_with_hints = sum(1 for row in questions if row['hint_text'] and row['hint_text'].strip())
        questions_without_hints = len(questions) - questions_with_hints
        
        print("\n" + "=" * 60)
        print("СТАТИСТИКА:")
        print("-" * 60)
        print(f"[+] Вопросов с подсказками: {questions_with_hints}")
        print(f"[-] Вопросов БЕЗ подсказок: {questions_without_hints}")
        print(f"[*] Всего активных вопросов: {len(questions)}")
        
        conn.close()
        
        # Рекомендации
        print("\n" + "=" * 60)
        print("РЕКОМЕНДАЦИИ:")
        print("-" * 60)
        
        if questions_without_hints > 0:
            print("⚠️  Найдены вопросы без подсказок!")
            print("   Рекомендуется обновить базу данных на сервере.")
        else:
            print("✅ Все вопросы имеют подсказки!")
            
        if questions_with_hints > 0:
            print("\n💡 Проверьте, правильно ли отображаются подсказки в Telegram боте.")
            print("   Если подсказки не отображаются, возможно проблема в коде бота.")
        
    except Exception as e:
        print(f"❌ ОШИБКА ПОДКЛЮЧЕНИЯ К БАЗЕ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_hints_on_server()