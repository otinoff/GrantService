#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления колонки total_questions в таблицу sessions
"""

import sys
import os
import sqlite3

# Добавляем путь к модулям
if os.name == 'nt':  # Windows
    sys.path.append('C:\\SnowWhiteAI\\GrantService')
    DB_PATH = 'C:\\SnowWhiteAI\\GrantService\\data\\grant_service.db'
else:  # Linux/Ubuntu
    sys.path.append('/var/GrantService')
    DB_PATH = '/var/GrantService/data/grant_service.db'

def add_total_questions_column():
    """Добавить колонку total_questions в таблицу sessions"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Проверяем, существует ли уже колонка
            cursor.execute("PRAGMA table_info(sessions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'total_questions' not in columns:
                print("Добавляем колонку total_questions...")
                
                # Добавляем колонку
                cursor.execute("""
                    ALTER TABLE sessions 
                    ADD COLUMN total_questions INTEGER DEFAULT 14
                """)
                
                # Обновляем существующие записи
                cursor.execute("""
                    UPDATE sessions 
                    SET total_questions = 14 
                    WHERE total_questions IS NULL
                """)
                
                conn.commit()
                print("[OK] Колонка total_questions успешно добавлена")
            else:
                print("[INFO] Колонка total_questions уже существует")
            
            # Проверяем результат
            cursor.execute("PRAGMA table_info(sessions)")
            columns = cursor.fetchall()
            print("\nСтруктура таблицы sessions:")
            for col in columns:
                print(f"  {col[1]} - {col[2]}")
                
    except Exception as e:
        print(f"[ERROR] Ошибка при добавлении колонки: {e}")
        return False
    
    return True

if __name__ == "__main__":
    add_total_questions_column()