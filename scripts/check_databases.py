#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки баз данных бота и Streamlit
"""

import sqlite3
import os
import sys

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_database(db_path, name):
    """Проверить базу данных и вывести информацию о токенах"""
    print(f"\n{'='*60}")
    print(f"Проверка {name}")
    print(f"Путь: {db_path}")
    print(f"Существует: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        print(f"Размер: {os.path.getsize(db_path)} байт")
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем наличие таблицы users
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    # Считаем пользователей
                    cursor.execute("SELECT COUNT(*) FROM users")
                    total_users = cursor.fetchone()[0]
                    print(f"Всего пользователей: {total_users}")
                    
                    # Считаем пользователей с токенами
                    cursor.execute("SELECT COUNT(*) FROM users WHERE login_token IS NOT NULL")
                    users_with_tokens = cursor.fetchone()[0]
                    print(f"Пользователей с токенами: {users_with_tokens}")
                    
                    # Выводим информацию о пользователях с токенами
                    if users_with_tokens > 0:
                        cursor.execute("""
                            SELECT telegram_id, username, first_name, 
                                   SUBSTR(login_token, 1, 50) as token_preview
                            FROM users 
                            WHERE login_token IS NOT NULL
                            LIMIT 5
                        """)
                        
                        print("\nПользователи с токенами:")
                        for row in cursor.fetchall():
                            telegram_id, username, first_name, token_preview = row
                            print(f"  - ID: {telegram_id}, Username: {username}, Имя: {first_name}")
                            print(f"    Токен: {token_preview}...")
                else:
                    print("ERROR: Таблица users не найдена!")
                    
        except Exception as e:
            print(f"ERROR: Ошибка при чтении БД: {e}")
    else:
        print("ERROR: Файл базы данных не существует!")

def main():
    """Главная функция"""
    print("ПРОВЕРКА БАЗ ДАННЫХ GRANTSERVICE")
    print("="*60)
    
    # База данных бота (основная)
    bot_db_path = "C:/SnowWhiteAI/GrantService/telegram-bot/data/grantservice.db"
    check_database(bot_db_path, "База данных бота")
    
    # База данных в /var/GrantService (Linux-стиль путь)
    var_db_path = "/var/GrantService/data/grantservice.db"
    if os.path.exists(var_db_path):
        check_database(var_db_path, "База данных в /var/GrantService")
    
    # База данных в корне проекта - определяем путь в зависимости от ОС
    if os.name == 'nt':  # Windows
        root_db_path = "C:/SnowWhiteAI/GrantService/data/grantservice.db"
    else:  # Linux/Unix
        root_db_path = "/var/GrantService/data/grantservice.db"
    
    if os.path.exists(root_db_path):
        check_database(root_db_path, "База данных в корне проекта")
    
    # База данных Streamlit (локальная)
    streamlit_db_path = "C:/SnowWhiteAI/GrantService/grantservice.db"
    if os.path.exists(streamlit_db_path):
        check_database(streamlit_db_path, "База данных Streamlit (локальная)")
    
    # Поиск всех файлов grantservice.db в проекте
    print(f"\n{'='*60}")
    print("Поиск всех файлов grantservice.db в проекте:")
    project_root = "C:/SnowWhiteAI/GrantService"
    
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file == "grantservice.db":
                full_path = os.path.join(root, file)
                size = os.path.getsize(full_path)
                print(f"  - {full_path} ({size} байт)")

if __name__ == "__main__":
    main()