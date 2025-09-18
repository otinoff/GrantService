#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обновления вопросов - оставляем только первые 14 с подсказками
"""

import sqlite3
import pathlib
import sys

def update_to_14_questions(use_system_db=False):
    """Оставить активными только первые 14 вопросов"""
    
    if use_system_db:
        # Используем системную БД (для продакшена)
        db_path = "/var/GrantService/data/grantservice.db"
    else:
        # Используем локальную БД в папке проекта (для разработки)
        current_dir = pathlib.Path(__file__).parent.parent
        db_path = str(current_dir / "data" / "grantservice.db")
        
        # Если локальной БД нет, используем системную
        if not pathlib.Path(db_path).exists():
            db_path = "/var/GrantService/data/grantservice.db"
    
    print(f"Используется база данных: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Обновление вопросов...")
        
        # Деактивируем вопросы с 15 по 24
        cursor.execute("""
            UPDATE interview_questions 
            SET is_active = 0 
            WHERE question_number > 14
        """)
        
        deactivated = cursor.rowcount
        print(f"  Деактивировано вопросов: {deactivated}")
        
        # Убеждаемся, что первые 14 вопросов активны
        cursor.execute("""
            UPDATE interview_questions 
            SET is_active = 1 
            WHERE question_number <= 14
        """)
        
        activated = cursor.rowcount
        print(f"  Активировано вопросов: {activated}")
        
        conn.commit()
        
        # Проверяем результат
        cursor.execute("""
            SELECT question_number, 
                   CASE WHEN is_active = 1 THEN 'Активен' ELSE 'Неактивен' END as status,
                   CASE WHEN hint_text IS NOT NULL AND hint_text != '' THEN 'Есть подсказка' ELSE 'Нет подсказки' END as hint_status
            FROM interview_questions 
            ORDER BY question_number
        """)
        
        print("\nСтатус вопросов:")
        for row in cursor.fetchall():
            print(f"  Вопрос {row[0]:2d}: {row[1]:10s} | {row[2]}")
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = 1 AND hint_text IS NOT NULL AND hint_text != ''")
        hints_count = cursor.fetchone()[0]
        
        print(f"\nИтого:")
        print(f"  Активных вопросов: {active_count}")
        print(f"  Из них с подсказками: {hints_count}")
        
        if active_count == 14 and hints_count == 14:
            print("\nУспешно! Теперь активно 14 вопросов, все с подсказками.")
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    # Если передан аргумент --system, используем системную БД
    use_system = '--system' in sys.argv
    update_to_14_questions(use_system_db=use_system)