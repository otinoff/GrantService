#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления версии базы данных
"""

import sqlite3
import os
from datetime import datetime

def add_db_version():
    """Добавляет версию базы данных"""
    
    # Путь к базе данных
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'grantservice.db')
    
    print("=" * 60)
    print("ДОБАВЛЕНИЕ ВЕРСИ БАЗЫ ДАННЫХ")
    print("=" * 60)
    print(f"\nФайл БД: {os.path.abspath(db_path)}")
    
    # Подключаемся к базе
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаем таблицу для версий (если её нет)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS db_version (
            id INTEGER PRIMARY KEY,
            version TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Добавляем текущую версию
    version = f"1.4.{datetime.now().strftime('%Y%m%d%H%M')}"
    timestamp = datetime.now().isoformat()
    
    # Проверяем, есть ли уже запись
    cursor.execute("SELECT COUNT(*) FROM db_version")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Вставляем новую запись
        cursor.execute("""
            INSERT INTO db_version (version, updated_at) 
            VALUES (?, ?)
        """, (version, timestamp))
        print(f"[+] Добавлена новая версия: {version}")
    else:
        # Обновляем существующую запись
        cursor.execute("""
            UPDATE db_version 
            SET version = ?, updated_at = ?
            WHERE id = 1
        """, (version, timestamp))
        print(f"[+] Обновлена версия: {version}")
    
    # Сохраняем изменения
    conn.commit()
    
    # Проверяем результат
    cursor.execute("SELECT version, updated_at FROM db_version WHERE id = 1")
    result = cursor.fetchone()
    if result:
        print(f"[OK] Текущая версия базы: {result[0]}")
        print(f"[OK] Дата обновления: {result[1]}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("[OK] ВЕРСИЯ БАЗЫ ДАННЫХ ОБНОВЛЕНА!")
    print("=" * 60)

if __name__ == "__main__":
    add_db_version()