#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница входа в админ панель GrantService
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add paths for imports
current_file = Path(__file__).resolve()
web_admin_dir = current_file.parent.parent  # web-admin directory
base_dir = web_admin_dir.parent  # GrantService directory

# Add to sys.path if not already there
if str(web_admin_dir) not in sys.path:
    sys.path.insert(0, str(web_admin_dir))
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

# Import modules using importlib for better reliability
import importlib.util

# Import required modules
try:
    # Try direct imports first
    from utils.auth import validate_login_token, check_user_access
except ImportError:
    # Fallback to importlib
    auth_file = web_admin_dir / "utils" / "auth.py"
    spec = importlib.util.spec_from_file_location("auth", str(auth_file))
    if spec and spec.loader:
        auth_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(auth_module)
            validate_login_token = auth_module.validate_login_token
            check_user_access = auth_module.check_user_access
        except Exception as e:
            st.error(f"❌ Ошибка загрузки модуля авторизации / Auth module load error: {e}")
            st.stop()
    else:
        st.error("❌ Не удалось найти модуль авторизации / Auth module not found")
        st.stop()

try:
    from data.database import GrantServiceDatabase
except ImportError:
    # Database import is not critical for login page
    pass

def show_login_page():
    """Отображение страницы входа"""
    st.title("🏆 ГрантСервис - Админ панель")
    st.markdown("### Управление системой создания грантовых заявок")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Добро пожаловать в ГрантСервис!**
        
        **Преимущества сервиса:**
        - ✅ Автоматическое создание грантовых заявок
        - ✅ ИИ-ассистент для анализа проектов
        - ✅ Быстрое создание заявок (15-20 минут)
        - ✅ Профессиональная структура документов
        - 🔒 Доступ только для авторизованных пользователей
        """)
    
    with col2:
        st.markdown("### 🔐 Вход в систему")
        
        # Проверяем токен в URL
        token = st.query_params.get('token', None)
        st.info(f"🔍 Получен токен из URL: {token[:20] if token else 'None'}")
        
        if token:
            # Пытаемся авторизоваться по токену
            st.info(f"🔍 Проверяем токен: {token[:20]}...")
            
            user = validate_login_token(token)
            st.info(f"👤 Получены данные пользователя: {user}")
            
            if user:
                st.info(f"👤 Найден пользователь: {user['telegram_id']}")
                st.info(f"📝 Имя: {user['first_name']}")
                st.info(f"✅ Активен: {user['is_active']}")
                
                has_access = check_user_access(user['telegram_id'])
                st.info(f"🔐 Проверка доступа: {'разрешен' if has_access else 'запрещен'}")
                
                if has_access:
                    st.success("✅ Авторизация успешна!")
                    # Сохраняем токен в сессии
                    st.session_state.auth_token = token
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("❌ Доступ запрещен для данного пользователя")
            else:
                st.error("❌ Недействительный или истекший токен")
        else:
            st.markdown("**🚀 Вход в админ панель:**")
            st.markdown("Для входа в админ панель необходимо получить ссылку от бота.")
            
            st.markdown("---")
            
            # Кнопка для доступа к боту
            st.markdown("**💬 Получить ссылку для входа:**")
            st.markdown("[Написать боту @grantservice_bot](https://t.me/grantservice_bot?start=login)")
            
            st.markdown("---")
            st.markdown("**Нет аккаунта?**")
            st.markdown("Обратитесь к администратору для получения доступа")

def main():
    """Главная функция страницы входа"""
    show_login_page()

if __name__ == "__main__":
    main()