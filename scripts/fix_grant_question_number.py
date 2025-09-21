#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для изменения номера вопроса grant_direction с 25 на 15
"""

import sys
import os
import io

# Установка UTF-8 для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import db

def fix_grant_question_number():
    """Изменить номер вопроса grant_direction с 25 на 15"""
    
    try:
        with db.connect() as conn:
            cursor = conn.cursor()
            
            print("="*60)
            print("ИЗМЕНЕНИЕ НОМЕРА ВОПРОСА GRANT_DIRECTION")
            print("="*60)
            
            # Находим вопрос с grant_direction
            cursor.execute("""
                SELECT id, question_number, field_name, question_text 
                FROM interview_questions 
                WHERE field_name = 'grant_direction'
            """)
            
            grant_question = cursor.fetchone()
            if grant_question:
                q_id, q_num, field, text = grant_question
                print(f"\n[INFO] Найден вопрос:")
                print(f"  ID: {q_id}")
                print(f"  Текущий номер: {q_num}")
                print(f"  Поле: {field}")
                print(f"  Текст: {text[:50]}...")
                
                if q_num == 25:
                    # Меняем номер с 25 на 15
                    print("\n[ACTION] Изменение номера с 25 на 15...")
                    
                    cursor.execute("""
                        UPDATE interview_questions 
                        SET question_number = 15
                        WHERE id = ?
                    """, (q_id,))
                    
                    conn.commit()
                    print("[SUCCESS] Номер вопроса успешно изменен на 15!")
                    
                elif q_num == 15:
                    print("\n[INFO] Вопрос уже имеет номер 15")
                else:
                    print(f"\n[WARNING] Вопрос имеет номер {q_num}")
                    print("[ACTION] Изменение номера на 15...")
                    
                    cursor.execute("""
                        UPDATE interview_questions 
                        SET question_number = 15
                        WHERE id = ?
                    """, (q_id,))
                    
                    conn.commit()
                    print("[SUCCESS] Номер вопроса изменен на 15!")
                
                # Проверяем результат
                print("\n" + "="*60)
                print("ПРОВЕРКА РЕЗУЛЬТАТА")
                print("="*60)
                
                cursor.execute("""
                    SELECT question_number, field_name, question_type
                    FROM interview_questions 
                    WHERE is_active = 1
                    ORDER BY question_number
                """)
                
                questions = cursor.fetchall()
                print(f"\nВсего активных вопросов: {len(questions)}")
                print("\nПорядок вопросов:")
                for q in questions:
                    marker = " <-- grant_direction" if q[1] == 'grant_direction' else ""
                    print(f"  №{q[0]:2} - {q[1]:30} ({q[2]}){marker}")
                
            else:
                print("\n[ERROR] Вопрос с field_name='grant_direction' не найден!")
                print("[INFO] Возможно, вопрос еще не добавлен в базу")
                print("[ACTION] Запустите сначала скрипт add_grant_direction_question.py")
                
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_grant_question_number()