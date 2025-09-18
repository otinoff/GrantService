#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления проблем с авторизацией в боте
"""

import os
import sys

# Добавляем путь к модулю БД
sys.path.append('/var/GrantService')

from data.database import db, auth_manager, UserRole

def fix_authorization():
    """Исправляет проблемы с авторизацией"""
    
    # ID администраторов (обновите, если нужно добавить свой ID)
    admin_ids = [
        826960528,   # Администратор 1
        591630092,   # Администратор 2  
        5032079932,  # Администратор 3
    ]
    
    print("Начинаем исправление авторизации...")
    
    # Добавляем администраторов в БД с ролью ADMIN
    for admin_id in admin_ids:
        try:
            # Добавляем пользователя с ролью администратора
            success = auth_manager.add_user(
                user_id=admin_id,
                role=UserRole.ADMIN
            )
            if success:
                print(f"✅ Администратор {admin_id} добавлен с ролью ADMIN")
            else:
                # Пробуем обновить роль, если пользователь уже существует
                update_success = auth_manager.update_user_role(
                    user_id=admin_id,
                    new_role=UserRole.ADMIN
                )
                if update_success:
                    print(f"✅ Роль администратора {admin_id} обновлена на ADMIN")
                else:
                    print(f"⚠️ Администратор {admin_id} уже существует с правильной ролью")
        except Exception as e:
            print(f"❌ Ошибка при добавлении администратора {admin_id}: {e}")
    
    print("\n📊 Текущие пользователи в БД:")
    print("=" * 50)
    
    # Показываем всех пользователей с ролями
    try:
        # Получаем всех пользователей из БД
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, role FROM auth_users ORDER BY role, user_id")
        users = cursor.fetchall()
        
        if users:
            for user in users:
                user_id, role = user
                print(f"ID: {user_id}, Роль: {role}")
        else:
            print("Нет пользователей в БД")
            
        conn.close()
    except Exception as e:
        print(f"Ошибка при получении списка пользователей: {e}")
    
    print("\n✅ Исправление авторизации завершено!")
    print("\n⚠️ ВАЖНО: Перезапустите бота для применения изменений:")
    print("sudo systemctl restart grantservice-bot")

if __name__ == "__main__":
    fix_authorization()