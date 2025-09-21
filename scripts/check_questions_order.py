#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки порядка вопросов в базе данных
"""

import sys
import os
import json

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import db

def check_questions_order():
    """Проверить порядок вопросов в БД"""
    
    try:
        with db.connect() as conn:
            cursor = conn.cursor()
            
            # Получаем все активные вопросы с сортировкой по номеру
            cursor.execute("""
                SELECT question_number, field_name, question_text, question_type, is_active
                FROM interview_questions 
                WHERE is_active = 1
                ORDER BY question_number
            """)
            
            questions = cursor.fetchall()
            
            print("="*80)
            print("АКТИВНЫЕ ВОПРОСЫ В БАЗЕ ДАННЫХ")
            print("="*80)
            print(f"\nВсего активных вопросов: {len(questions)}\n")
            
            # Проверяем последовательность номеров
            expected_number = 1
            gaps = []
            
            for q in questions:
                q_num, field, text, q_type, active = q
                
                # Проверяем пропуски в нумерации
                if q_num != expected_number:
                    for missing in range(expected_number, q_num):
                        gaps.append(missing)
                    expected_number = q_num
                
                # Выводим информацию о вопросе
                print(f"Вопрос №{q_num:2} | Тип: {q_type:10} | Поле: {field:30} | Текст: {text[:50]}...")
                
                expected_number += 1
            
            # Проверяем пропущенные номера
            if gaps:
                print("\n" + "="*80)
                print("⚠️ ВНИМАНИЕ: Обнаружены пропуски в нумерации!")
                print("="*80)
                print(f"Пропущенные номера: {', '.join(map(str, gaps))}")
                print(f"Всего пропусков: {len(gaps)}")
            
            # Проверяем неактивные вопросы
            cursor.execute("""
                SELECT question_number, field_name, question_text
                FROM interview_questions 
                WHERE is_active = 0
                ORDER BY question_number
            """)
            
            inactive = cursor.fetchall()
            if inactive:
                print("\n" + "="*80)
                print("НЕАКТИВНЫЕ ВОПРОСЫ")
                print("="*80)
                for q in inactive:
                    print(f"Вопрос №{q[0]:2} | {q[1]:30} | {q[2][:50]}...")
            
            # Проверка на дубликаты номеров
            cursor.execute("""
                SELECT question_number, COUNT(*) as cnt
                FROM interview_questions
                WHERE is_active = 1
                GROUP BY question_number
                HAVING COUNT(*) > 1
            """)
            
            duplicates = cursor.fetchall()
            if duplicates:
                print("\n" + "="*80)
                print("❌ ОШИБКА: Обнаружены дубликаты номеров!")
                print("="*80)
                for dup in duplicates:
                    print(f"Номер {dup[0]} встречается {dup[1]} раз(а)")
            
            # Проверяем вопрос №15 специально
            print("\n" + "="*80)
            print("ПРОВЕРКА ВОПРОСА №15")
            print("="*80)
            
            cursor.execute("""
                SELECT * FROM interview_questions 
                WHERE question_number = 15
            """)
            
            q15 = cursor.fetchone()
            if q15:
                print(f"✅ Вопрос №15 найден:")
                print(f"   ID: {q15[0]}")
                print(f"   Текст: {q15[2]}")
                print(f"   Field: {q15[3]}")
                print(f"   Тип: {q15[4] if len(q15) > 4 else 'text'}")
                print(f"   Активен: {'Да' if q15[7] else 'Нет'}")
            else:
                print("❌ Вопрос №15 НЕ найден в базе данных!")
            
            # Рекомендации по исправлению
            if gaps or duplicates:
                print("\n" + "="*80)
                print("📝 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ")
                print("="*80)
                
                if gaps:
                    print("\n1. Для исправления пропусков в нумерации:")
                    print("   - Перенумеруйте вопросы последовательно")
                    print("   - Или активируйте недостающие вопросы")
                    
                if duplicates:
                    print("\n2. Для исправления дубликатов:")
                    print("   - Измените номера дублирующихся вопросов")
                    print("   - Или деактивируйте лишние вопросы")
                    
                print("\n3. Можно запустить скрипт fix_questions_numbering.py для автоматического исправления")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_questions_order()