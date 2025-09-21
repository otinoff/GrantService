#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки пользователей в базе данных
"""

import sqlite3
import os
import sys

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.database import db

def check_users():
    """Проверить пользователей в базе данных"""
    print("="*60)
    print("ПРОВЕРКА ПОЛЬЗОВАТЕЛЕЙ В БАЗЕ ДАННЫХ")
    print("="*60)
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем таблицу users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            print(f"\n[USERS] Всего пользователей: {total_users}")
            
            # Проверяем пользователей с токенами
            cursor.execute("SELECT COUNT(*) FROM users WHERE login_token IS NOT NULL")
            users_with_tokens = cursor.fetchone()[0]
            print(f"[TOKENS] Пользователей с токенами: {users_with_tokens}")
            
            # Показываем всех пользователей
            print("\n[LIST] Все пользователи:")
            cursor.execute("""
                SELECT telegram_id, username, first_name, last_name, login_token
                FROM users
                ORDER BY telegram_id
            """)
            
            users = cursor.fetchall()
            if users:
                for user in users:
                    telegram_id, username, first_name, last_name, login_token = user
                    print(f"  - Telegram ID: {telegram_id}")
                    print(f"    Username: {username}")
                    print(f"    Имя: {first_name} {last_name}")
                    print(f"    Токен: {login_token}")
                    print()
            else:
                print("  Нет пользователей в базе данных")
                
    except Exception as e:
        print(f"[ERROR] Ошибка проверки базы данных: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_users()