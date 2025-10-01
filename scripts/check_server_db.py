#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки базы данных на сервере
"""

import os
import sqlite3
import json
from datetime import datetime

def check_database_details():
    """Детальная проверка состояния базы данных"""
    db_path = "data/grant_service.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 ДЕТАЛЬНАЯ ПРОВЕРКА БАЗЫ ДАННЫХ")
        print("=" * 60)
        
        # Информация о файле
        stat = os.stat(db_path)
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        size_mb = stat.st_size / (1024 * 1024)
        
        print(f"📁 Файл БД:")
        print(f"  - Путь: {os.path.abspath(db_path)}")
        print(f"  - Размер: {size_mb:.2f} MB")
        print(f"  - Последнее изменение: {mod_time}")
        print()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Таблицы в БД: {', '.join(tables)}")
        print()
        
        # Проверяем вопросы
        if 'questions' in tables:
            print("❓ АНАЛИЗ ВОПРОСОВ:")
            
            # Общее количество
            cursor.execute("SELECT COUNT(*) FROM questions")
            total_questions = cursor.fetchone()[0]
            print(f"  - Всего вопросов: {total_questions}")
            
            # Активные вопросы
            cursor.execute("SELECT COUNT(*) FROM questions WHERE is_active = 1")
            active_questions = cursor.fetchone()[0]
            print(f"  - Активных вопросов: {active_questions}")
            
            # Вопросы с подсказками
            cursor.execute("SELECT COUNT(*) FROM questions WHERE hint_text IS NOT NULL AND hint_text != ''")
            questions_with_hints = cursor.fetchone()[0]
            print(f"  - Вопросов с подсказками: {questions_with_hints}")
            
            # Проверяем структуру таблицы questions
            cursor.execute("PRAGMA table_info(questions)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"  - Колонки таблицы: {', '.join(columns)}")
            
            # Показываем несколько активных вопросов
            cursor.execute("""
                SELECT question_number, question_text, hint_text, is_active 
                FROM questions 
                WHERE is_active = 1 
                ORDER BY question_number 
                LIMIT 5
            """)
            active_sample = cursor.fetchall()
            
            print("  - Первые 5 активных вопросов:")
            for q_num, q_text, hint, active in active_sample:
                hint_status = "✅" if hint else "❌"
                print(f"    {q_num}. {q_text[:50]}... | Подсказка: {hint_status}")
            print()
        
        # Проверяем заявки
        if 'grant_applications' in tables:
            print("📋 АНАЛИЗ ЗАЯВОК:")
            cursor.execute("SELECT COUNT(*) FROM grant_applications")
            total_apps = cursor.fetchone()[0]
            print(f"  - Всего заявок: {total_apps}")
            
            # Последние заявки
            cursor.execute("""
                SELECT application_number, title, created_at 
                FROM grant_applications 
                ORDER BY created_at DESC 
                LIMIT 3
            """)
            recent_apps = cursor.fetchall()
            print("  - Последние заявки:")
            for app_num, title, created in recent_apps:
                print(f"    {app_num}: {title} ({created})")
            print()
        
        # Проверяем пользователей
        if 'users' in tables:
            print("👥 АНАЛИЗ ПОЛЬЗОВАТЕЛЕЙ:")
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            print(f"  - Всего пользователей: {total_users}")
            print()
        
        # Проверяем сессии
        if 'sessions' in tables:
            print("🔄 АНАЛИЗ СЕССИЙ:")
            cursor.execute("SELECT COUNT(*) FROM sessions")
            total_sessions = cursor.fetchone()[0]
            print(f"  - Всего сессий: {total_sessions}")
            
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'completed'")
            completed_sessions = cursor.fetchone()[0]
            print(f"  - Завершенных сессий: {completed_sessions}")
            print()
        
        conn.close()
        
        print("✅ Проверка базы данных завершена")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_database_details()