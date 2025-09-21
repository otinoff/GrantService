#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления временной метки в базу данных
"""

import sqlite3
import os
from datetime import datetime

def add_timestamp_to_database():
    """Добавляет временную метку в базу данных"""
    
    # Путь к базе данных
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'grantservice.db')
    
    print("=" * 60)
    print("ДОБАВЛЕНИЕ ВРЕМЕННОЙ МЕТКИ В БАЗУ ДАННЫХ")
    print("=" * 60)
    print(f"\nФайл БД: {os.path.abspath(db_path)}")
    
    # Подключаемся к базе
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаем таблицу для меток времени (если её нет)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS db_timestamps (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Добавляем текущую временную метку
    current_timestamp = datetime.now().isoformat()
    description = f"Обновление подсказок для вопросов интервью - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Вставляем новую запись
    cursor.execute("""
        INSERT INTO db_timestamps (timestamp, description) 
        VALUES (?, ?)
    """, (current_timestamp, description))
    
    # Сохраняем изменения
    conn.commit()
    
    # Проверяем результат
    cursor.execute("""
        SELECT timestamp, description, created_at 
        FROM db_timestamps 
        ORDER BY id DESC 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if result:
        print(f"[+] Добавлена временная метка:")
        print(f"    Время: {result[0]}")
        print(f"    Описание: {result[1]}")
        print(f"    Создано: {result[2]}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("[OK] ВРЕМЕННАЯ МЕТКА ДОБАВЛЕНА В БАЗУ ДАННЫХ!")
    print("=" * 60)

if __name__ == "__main__":
    add_timestamp_to_database()