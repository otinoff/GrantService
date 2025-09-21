#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки и синхронизации токенов между ботом и Streamlit
"""

import sqlite3
import os
import sys
import time

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import db

def check_database_sync():
    """Проверить синхронизацию базы данных"""
    print("="*60)
    print("ПРОВЕРКА СИНХРОНИЗАЦИИ БАЗЫ ДАННЫХ")
    print("="*60)
    
    # Проверяем путь к БД
    print(f"\n[PATH] База данных: {db.db_path}")
    print(f"[FILE] Существует: {os.path.exists(db.db_path)}")
    
    if os.path.exists(db.db_path):
        print(f"[SIZE] Размер файла: {os.path.getsize(db.db_path)} байт")
        
        # Проверяем наличие пользователей с токенами
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
            
            # Показываем последние токены
            if users_with_tokens > 0:
                print("\n[LIST] Последние токены:")
                cursor.execute("""
                    SELECT telegram_id, username, 
                           SUBSTR(login_token, 1, 50) as token_preview
                    FROM users 
                    WHERE login_token IS NOT NULL
                    ORDER BY rowid DESC
                    LIMIT 5
                """)
                
                for row in cursor.fetchall():
                    telegram_id, username, token_preview = row
                    print(f"  - Telegram ID: {telegram_id}")
                    print(f"    Username: {username}")
                    print(f"    Токен: {token_preview}...")
                    
                    # Проверяем валидность токена
                    cursor.execute("""
                        SELECT login_token FROM users WHERE telegram_id = ?
                    """, (telegram_id,))
                    full_token = cursor.fetchone()[0]
                    
                    # Парсим токен
                    if '_' in full_token:
                        parts = full_token.split('_')
                        if len(parts) >= 3:
                            token_timestamp = int(parts[1])
                            current_time = int(time.time())
                            time_diff = current_time - token_timestamp
                            hours_passed = time_diff // 3600
                            
                            if time_diff < 86400:
                                print(f"    [OK] Токен действителен (создан {hours_passed} часов назад)")
                            else:
                                print(f"    [EXPIRED] Токен истек ({hours_passed} часов назад)")
                    elif full_token.startswith('token') and len(full_token) == 47:
                        # Формат без подчеркиваний
                        timestamp_str = full_token[5:15]
                        if timestamp_str.isdigit():
                            token_timestamp = int(timestamp_str)
                            current_time = int(time.time())
                            time_diff = current_time - token_timestamp
                            hours_passed = time_diff // 3600
                            
                            if time_diff < 86400:
                                print(f"    [OK] Токен действителен (создан {hours_passed} часов назад)")
                            else:
                                print(f"    [EXPIRED] Токен истек ({hours_passed} часов назад)")
                    print()
    else:
        print("[ERROR] База данных не найдена!")

def generate_test_token(telegram_id):
    """Сгенерировать тестовый токен для пользователя"""
    print("\n"+"="*60)
    print(f"ГЕНЕРАЦИЯ ТОКЕНА ДЛЯ ПОЛЬЗОВАТЕЛЯ {telegram_id}")
    print("="*60)
    
    try:
        token = db.get_or_create_login_token(telegram_id)
        if token:
            print(f"[OK] Токен успешно сгенерирован!")
            print(f"[TOKEN] {token}")
            print(f"\n[LINK] Ссылка для входа в Streamlit:")
            print(f"http://localhost:8501?token={token}")
        else:
            print("[ERROR] Ошибка генерации токена")
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Главная функция"""
    print("\nВыберите действие:")
    print("1. Проверить синхронизацию БД")
    print("2. Сгенерировать тестовый токен")
    print("3. Выход")
    
    choice = input("\nВведите номер действия (1-3): ")
    
    if choice == "1":
        check_database_sync()
    elif choice == "2":
        telegram_id = input("Введите Telegram ID пользователя: ")
        try:
            telegram_id = int(telegram_id)
            generate_test_token(telegram_id)
        except ValueError:
            print("[ERROR] Неверный формат Telegram ID")
    elif choice == "3":
        print("Выход...")
        return
    
    # Повторяем меню
    input("\nНажмите Enter для продолжения...")
    main()

if __name__ == "__main__":
    check_database_sync()
    print("\n" + "="*60)
    print("Для дополнительных действий запустите скрипт интерактивно:")
    print("python scripts/sync_token.py")