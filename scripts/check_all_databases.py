#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки всех баз данных на сервере и их дат обновления
"""

import sqlite3
import os
import glob
from datetime import datetime

def check_all_databases():
    """Проверяет все базы данных на сервере"""
    
    print("=" * 80)
    print("ПРОВЕРКА ВСЕХ БАЗ ДАННЫХ НА СЕРВЕРЕ")
    print("=" * 80)
    
    # Возможные пути к базам данных
    possible_paths = [
        "/var/GrantService/data/grantservice.db",
        "/var/GrantService/grantservice.db",
        "/home/*/GrantService/data/grantservice.db",
        "/home/*/GrantService/grantservice.db",
        "/opt/GrantService/data/grantservice.db",
        "/opt/GrantService/grantservice.db"
    ]
    
    found_databases = []
    
    # Проверяем конкретные пути
    for path in possible_paths[:6]:  # Первые 6 путей без wildcard
        if os.path.exists(path):
            found_databases.append(path)
    
    # Проверяем пути с wildcard
    for pattern in possible_paths[6:]:  # Последние пути с wildcard
        matches = glob.glob(pattern)
        for match in matches:
            if os.path.exists(match):
                found_databases.append(match)
    
    print(f"Найдено баз данных: {len(found_databases)}")
    print("-" * 80)
    
    # Проверяем каждую базу данных
    for i, db_path in enumerate(found_databases, 1):
        print(f"\n{i}. База данных: {db_path}")
        print(f"   Путь существует: {os.path.exists(db_path)}")
        
        if os.path.exists(db_path):
            try:
                # Размер файла
                size = os.path.getsize(db_path)
                mtime = os.path.getmtime(db_path)
                mod_time = datetime.fromtimestamp(mtime)
                
                print(f"   Размер: {size:,} байт")
                print(f"   Дата модификации: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Подключаемся к базе и проверяем структуру
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Проверяем таблицы
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    ORDER BY name
                """)
                tables = cursor.fetchall()
                
                print(f"   Таблиц: {len(tables)}")
                
                # Проверяем таблицу interview_questions
                if any(table[0] == 'interview_questions' for table in tables):
                    cursor.execute("""
                        SELECT COUNT(*), 
                               COUNT(CASE WHEN is_active = 1 THEN 1 END),
                               COUNT(CASE WHEN hint_text IS NOT NULL AND hint_text != '' THEN 1 END),
                               COUNT(CASE WHEN is_active = 1 AND hint_text IS NOT NULL AND hint_text != '' THEN 1 END)
                        FROM interview_questions
                    """)
                    
                    counts = cursor.fetchone()
                    total_q = counts[0]
                    active_q = counts[1]
                    with_hints = counts[2]
                    active_with_hints = counts[3]
                    
                    print(f"   Вопросов всего: {total_q}")
                    print(f"   Активных вопросов: {active_q}")
                    print(f"   Вопросов с подсказками: {with_hints}")
                    print(f"   Активных с подсказками: {active_with_hints}")
                    
                    # Показываем примеры активных вопросов
                    cursor.execute("""
                        SELECT question_number, question_text, hint_text
                        FROM interview_questions 
                        WHERE is_active = 1
                        ORDER BY question_number
                        LIMIT 3
                    """)
                    
                    sample_questions = cursor.fetchall()
                    print("   Примеры активных вопросов:")
                    for q in sample_questions:
                        q_num, q_text, hint = q
                        hint_status = "ЕСТЬ" if hint and hint.strip() else "НЕТ"
                        print(f"     {q_num}. {hint_status} - {q_text[:50]}...")
                
                # Проверяем таблицу версий (если есть)
                if any(table[0] == 'db_version' for table in tables):
                    cursor.execute("""
                        SELECT version, updated_at 
                        FROM db_version 
                        ORDER BY id DESC 
                        LIMIT 1
                    """)
                    version_row = cursor.fetchone()
                    if version_row:
                        print(f"   Версия БД: {version_row[0]}")
                        print(f"   Обновлена: {version_row[1]}")
                
                conn.close()
                
            except Exception as e:
                print(f"   ❌ Ошибка проверки: {e}")
        
        print("-" * 40)
    
    # Если не найдено баз данных, проверим общие директории
    if not found_databases:
        print("\n❌ Не найдено баз данных по стандартным путям")
        print("Проверяем общие директории...")
        
        common_dirs = ["/var", "/home", "/opt", "/usr/local"]
        for dir_path in common_dirs:
            if os.path.exists(dir_path):
                print(f"   Проверка: {dir_path}")
                try:
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            if file == "grantservice.db":
                                full_path = os.path.join(root, file)
                                found_databases.append(full_path)
                                print(f"     ✅ Найдена: {full_path}")
                except PermissionError:
                    print(f"     🔒 Нет доступа: {dir_path}")

if __name__ == "__main__":
    check_all_databases()