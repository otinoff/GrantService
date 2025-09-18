#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для проверки прав доступа к страницам админки
"""

import streamlit as st
import sys
import os
from functools import wraps

sys.path.append('/var/GrantService')
from data.database import auth_manager, UserRole

class PageAuth:
    """Класс для управления авторизацией страниц"""
    
    @staticmethod
    def check_page_access(page_name: str) -> bool:
        """Проверить доступ к странице"""
        if 'user_data' not in st.session_state:
            return False
        
        user_id = st.session_state.user_data.get('telegram_id')
        if not user_id:
            return False
        
        return auth_manager.can_access_page(user_id, page_name)
    
    @staticmethod
    def require_page_access(page_name: str):
        """Декоратор для требования доступа к странице"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not PageAuth.check_page_access(page_name):
                    st.error(f"❌ У вас нет доступа к странице '{page_name}'")
                    st.stop()
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def require_admin():
        """Декоратор для страниц только для администраторов"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if 'user_data' not in st.session_state:
                    st.error("❌ Требуется авторизация")
                    st.stop()
                
                user_id = st.session_state.user_data.get('telegram_id')
                if not auth_manager.is_admin(user_id):
                    st.error("❌ Эта страница доступна только администраторам")
                    st.stop()
                    
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def require_editor():
        """Декоратор для страниц редакторов"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if 'user_data' not in st.session_state:
                    st.error("❌ Требуется авторизация")
                    st.stop()
                
                user_id = st.session_state.user_data.get('telegram_id')
                if not auth_manager.can_edit_content(user_id):
                    st.error("❌ Эта страница доступна только редакторам и администраторам")
                    st.stop()
                    
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def get_user_role_badge() -> str:
        """Получить badge с ролью пользователя"""
        if 'user_data' not in st.session_state:
            return ""
        
        user_id = st.session_state.user_data.get('telegram_id')
        if not user_id:
            return ""
        
        role = auth_manager.get_user_role(user_id)
        
        role_badges = {
            UserRole.ADMIN.value: "👑 Администратор",
            UserRole.EDITOR.value: "✏️ Редактор",
            UserRole.VIEWER.value: "👁️ Наблюдатель",
            UserRole.USER.value: "👤 Пользователь"
        }
        
        return role_badges.get(role, "👤 Пользователь")
    
    @staticmethod
    def show_access_denied_message(required_role: str = None):
        """Показать сообщение об отказе в доступе"""
        st.error("❌ Доступ запрещен")
        
        if required_role:
            st.info(f"Для доступа к этой странице требуется роль: **{required_role}**")
        
        st.markdown("""
        ### Что вы можете сделать:
        
        1. **Обратитесь к администратору** для получения необходимых прав
        2. **Проверьте свою роль** в настройках профиля
        3. **Вернитесь на главную страницу** и выберите доступный раздел
        """)
        
        if st.button("🏠 На главную"):
            st.switch_page("pages/📊_Главная.py")
    
    @staticmethod
    def get_accessible_pages() -> list:
        """Получить список доступных страниц для текущего пользователя"""
        if 'user_data' not in st.session_state:
            return []
        
        user_id = st.session_state.user_data.get('telegram_id')
        if not user_id:
            return []
        
        return auth_manager.get_accessible_pages(user_id)
    
    @staticmethod
    def show_navigation_sidebar():
        """Показать навигацию с учетом прав доступа"""
        with st.sidebar:
            st.markdown("## 🧭 Навигация")
            
            # Показываем роль пользователя
            badge = PageAuth.get_user_role_badge()
            if badge:
                st.markdown(f"**{badge}**")
                st.markdown("---")
            
            # Получаем доступные страницы
            accessible_pages = PageAuth.get_accessible_pages()
            
            # Группы страниц
            page_groups = {
                "📊 Аналитика": [
                    ("dashboard", "📊 Главная", "pages/📊_Главная.py"),
                    ("analytics", "📈 Аналитика", "pages/📈_Аналитика.py"),
                    ("export", "📥 Экспорт", "pages/📥_Экспорт_данных.py"),
                ],
                "✏️ Управление контентом": [
                    ("questions", "❓ Вопросы", "pages/❓_Вопросы_интервью.py"),
                    ("prompts", "🤖 Промпты", "pages/🤖_Промпты_агентов.py"),
                    ("agents", "👥 Агенты", "pages/👥_Агенты.py"),
                    ("applications", "📋 Заявки", "pages/📋_Заявки.py"),
                ],
                "⚙️ Администрирование": [
                    ("users", "👤 Пользователи", "pages/👤_Пользователи.py"),
                    ("settings", "⚙️ Настройки", "pages/⚙️_Настройки.py"),
                    ("logs", "📜 Логи", "pages/📜_Логи.py"),
                ],
            }
            
            # Показываем доступные страницы по группам
            for group_name, pages in page_groups.items():
                # Проверяем, есть ли доступные страницы в группе
                group_accessible = [p for p in pages if p[0] in accessible_pages]
                
                if group_accessible:
                    st.markdown(f"### {group_name}")
                    for page_key, page_title, page_file in group_accessible:
                        if st.button(page_title, key=f"nav_{page_key}"):
                            st.switch_page(page_file)
                    st.markdown("")

# Функции для использования в страницах
def check_auth():
    """Базовая проверка авторизации"""
    if 'user_data' not in st.session_state:
        st.error("❌ Требуется авторизация")
        st.markdown("""
        ### Как войти в систему:
        1. Откройте Telegram бота @GrantServiceBot
        2. Выполните команду `/login` или `/admin`
        3. Перейдите по полученной ссылке
        """)
        st.stop()
    
    return st.session_state.user_data

def check_role(required_role: UserRole):
    """Проверка роли пользователя"""
    user_data = check_auth()
    user_id = user_data.get('telegram_id')
    
    user_role = auth_manager.get_user_role(user_id)
    
    # Проверяем иерархию ролей
    role_hierarchy = {
        UserRole.USER.value: 0,
        UserRole.VIEWER.value: 1,
        UserRole.EDITOR.value: 2,
        UserRole.ADMIN.value: 3
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role.value, 999)
    
    if user_level < required_level:
        PageAuth.show_access_denied_message(required_role.value)
        st.stop()
    
    return user_data

# Экспортируем для удобства использования
require_admin = PageAuth.require_admin
require_editor = PageAuth.require_editor
require_page_access = PageAuth.require_page_access