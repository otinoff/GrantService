#!/usr/bin/env python3
"""
Скрипт для установки администраторских прав пользователю
"""

import sys
import os
import sqlite3

# Добавляем путь к модулям
sys.path.insert(0, 'C:\\SnowWhiteAI\\GrantService')

from data.database import auth_manager

def set_admin(telegram_id: int, username: str = None):
    """Установить права администратора для пользователя"""
    
    print(f"Устанавливаем права администратора для пользователя {telegram_id}")
    
    # Устанавливаем роль админа
    auth_manager.set_user_role(telegram_id, 'admin')
    
    # Добавляем все разрешения
    auth_manager.add_user_permission(telegram_id, 'full_access')
    auth_manager.add_user_permission(telegram_id, 'manage_users')
    auth_manager.add_user_permission(telegram_id, 'view_analytics')
    auth_manager.add_user_permission(telegram_id, 'edit_data')
    
    # Логируем действие
    auth_manager.log_auth_action(
        user_id=telegram_id,
        action='grant_admin_role',
        success=True,
        details=f"Admin role granted to {username or telegram_id}"
    )
    
    print(f"✅ Права администратора установлены для пользователя {telegram_id}")
    
    # Показываем текущие права
    role = auth_manager.get_user_role(telegram_id)
    permissions = auth_manager.get_user_permissions(telegram_id)
    
    print(f"\nТекущая роль: {role}")
    print(f"Разрешения: {', '.join(permissions) if permissions else 'нет'}")

if __name__ == "__main__":
    # Устанавливаем права для Андрея (theperipherals)
    set_admin(5032079932, "theperipherals")
    
    print("\nДля установки прав другому пользователю используйте:")
    print("python set_admin.py TELEGRAM_ID")
    
    # Если переданы аргументы командной строки
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
            set_admin(user_id)
        except ValueError:
            print(f"Ошибка: {sys.argv[1]} не является корректным Telegram ID")