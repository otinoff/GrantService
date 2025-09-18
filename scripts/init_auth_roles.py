#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для инициализации ролей пользователей в системе GrantService
"""

import sys
import os
sys.path.append('/var/GrantService')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import db, auth_manager, UserRole

def init_auth_roles():
    """Инициализация ролей для существующих пользователей"""
    
    # Администраторы системы (замените на реальные Telegram ID)
    ADMIN_USERS = {
        393356583,  # Основной администратор
        # Добавьте других администраторов здесь
    }
    
    # Редакторы системы (замените на реальные Telegram ID)
    EDITOR_USERS = {
        123456789,  # Пример редактора
        # Добавьте других редакторов здесь
    }
    
    print("🔧 Инициализация ролей пользователей...")
    
    # Устанавливаем роли для администраторов
    for telegram_id in ADMIN_USERS:
        success = auth_manager.set_user_role(telegram_id, UserRole.ADMIN.value)
        if success:
            print(f"✅ Пользователь {telegram_id} назначен администратором")
        else:
            print(f"⚠️ Не удалось назначить администратора {telegram_id}")
    
    # Устанавливаем роли для редакторов
    for telegram_id in EDITOR_USERS:
        success = auth_manager.set_user_role(telegram_id, UserRole.EDITOR.value)
        if success:
            print(f"✅ Пользователь {telegram_id} назначен редактором")
        else:
            print(f"⚠️ Не удалось назначить редактора {telegram_id}")
    
    # Настраиваем права доступа к страницам админки
    print("\n🔧 Настройка прав доступа к страницам...")
    
    # Страницы только для администраторов
    admin_pages = [
        ("settings", "Настройки системы"),
        ("logs", "Системные логи"),
        ("users", "Управление пользователями"),
    ]
    
    for page_name, description in admin_pages:
        success = auth_manager.set_page_permissions(
            page_name=page_name,
            required_role=UserRole.ADMIN.value,
            description=description
        )
        if success:
            print(f"✅ Страница '{page_name}' - только для администраторов")
    
    # Страницы для редакторов и администраторов
    editor_pages = [
        ("questions", "Управление вопросами интервью"),
        ("prompts", "Управление промптами агентов"),
        ("agents", "Настройка агентов"),
        ("applications", "Просмотр заявок"),
    ]
    
    for page_name, description in editor_pages:
        success = auth_manager.set_page_permissions(
            page_name=page_name,
            required_role=UserRole.EDITOR.value,
            description=description
        )
        if success:
            print(f"✅ Страница '{page_name}' - для редакторов и администраторов")
    
    # Страницы доступные всем авторизованным пользователям
    viewer_pages = [
        ("dashboard", "Главная панель"),
        ("analytics", "Аналитика"),
        ("export", "Экспорт данных"),
    ]
    
    for page_name, description in viewer_pages:
        success = auth_manager.set_page_permissions(
            page_name=page_name,
            required_role=UserRole.VIEWER.value,
            description=description
        )
        if success:
            print(f"✅ Страница '{page_name}' - для всех авторизованных пользователей")
    
    print("\n✨ Инициализация ролей завершена!")
    
    # Показываем статистику
    print("\n📊 Статистика ролей:")
    
    for role in UserRole:
        users = auth_manager.get_users_by_role(role.value)
        print(f"  • {role.value}: {len(users)} пользователей")

if __name__ == "__main__":
    init_auth_roles()