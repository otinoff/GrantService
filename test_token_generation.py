#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для генерации токена для конкретного пользователя
"""

import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.database import db

def test_token_generation():
    """Тест генерации токена для пользователя"""
    telegram_id = 5032079932
    
    print("="*60)
    print(f"ТЕСТ ГЕНЕРАЦИИ ТОКЕНА ДЛЯ ПОЛЬЗОВАТЕЛЯ {telegram_id}")
    print("="*60)
    
    # Проверяем текущее состояние пользователя
    print("\n1. Проверяем текущее состояние пользователя...")
    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT telegram_id, username, login_token 
            FROM users 
            WHERE telegram_id = ?
        """, (telegram_id,))
        result = cursor.fetchone()
        if result:
            print(f"   Найден пользователь: {result[1]} ({result[0]})")
            print(f"   Текущий токен: {result[2]}")
        else:
            print(f"   Пользователь с ID {telegram_id} не найден")
            return
    
    # Генерируем новый токен
    print("\n2. Генерируем новый токен...")
    token = db.get_or_create_login_token(telegram_id)
    if token:
        print(f"   Сгенерированный токен: {token}")
        print(f"   Длина токена: {len(token)} символов")
    else:
        print("   ❌ Ошибка генерации токена")
        return
    
    # Проверяем, что токен сохранился в БД
    print("\n3. Проверяем сохранение токена в БД...")
    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT login_token 
            FROM users 
            WHERE telegram_id = ?
        """, (telegram_id,))
        result = cursor.fetchone()
        if result and result[0] == token:
            print("   ✅ Токен успешно сохранен в базе данных")
        else:
            print("   ❌ Токен НЕ сохранен в базе данных")
            print(f"   Ожидаемый токен: {token}")
            print(f"   Фактический токен в БД: {result[0] if result else 'None'}")
    
    # Проверяем валидацию токена
    print("\n4. Проверяем валидацию токена...")
    user_data = db.validate_login_token(token)
    if user_data:
        print("   ✅ Токен успешно прошел валидацию")
        print(f"   Данные пользователя: {user_data}")
    else:
        print("   ❌ Токен НЕ прошел валидацию")
    
    print("\n" + "="*60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*60)

if __name__ == "__main__":
    test_token_generation()