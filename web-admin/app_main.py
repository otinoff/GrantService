#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GrantService Admin Panel - Main Application
Главный файл приложения с поддержкой многостраничной навигации
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Настройка страницы должна быть первой
st.set_page_config(
    page_title="GrantService Admin Panel",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add paths for imports
current_file = Path(__file__).resolve()
web_admin_dir = current_file.parent  # web-admin directory
base_dir = web_admin_dir.parent  # GrantService directory

# Add to sys.path if not already there
if str(web_admin_dir) not in sys.path:
    sys.path.insert(0, str(web_admin_dir))
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

# Import modules using importlib for better reliability
import importlib.util

# First, check if there's a token in the URL
try:
    query_params = st.query_params  # Streamlit >= 1.30
except AttributeError:
    query_params = st.experimental_get_query_params()  # Streamlit < 1.30
token_from_url = query_params.get('token', [None])[0] if isinstance(query_params.get('token', None), list) else query_params.get('token', None)

# Debug output in sidebar
if token_from_url:
    st.sidebar.success(f"🔑 Получен токен из URL: {token_from_url[:20]}...")
    
    # Try to validate the token
    try:
        # Import validate_login_token
        auth_file = web_admin_dir / "utils" / "auth.py"
        spec = importlib.util.spec_from_file_location("auth", str(auth_file))
        if spec and spec.loader:
            auth_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(auth_module)
            validate_login_token = auth_module.validate_login_token
            check_user_access = auth_module.check_user_access
            
            # Validate the token
            user_data = validate_login_token(token_from_url)
            if user_data:
                st.sidebar.success(f"✅ Токен валиден для пользователя {user_data.get('telegram_id')}")
                
                # Check access
                has_access = check_user_access(user_data.get('telegram_id'))
                if has_access:
                    # Save to session
                    st.session_state['auth_token'] = token_from_url
                    st.session_state['user'] = user_data
                    st.sidebar.success("✅ Авторизация успешна!")
                    
                    # Clear token from URL for security
                    try:
                        st.query_params.clear()  # Streamlit >= 1.30
                    except AttributeError:
                        st.experimental_set_query_params()  # Streamlit < 1.30
                    
                    # Reload the page
                    st.rerun()
                else:
                    st.error("❌ Доступ запрещен для данного пользователя")
            else:
                st.sidebar.error("❌ Недействительный или истекший токен")
    except Exception as e:
        st.sidebar.error(f"❌ Ошибка проверки токена: {e}")

# Authorization check
try:
    # Try direct import first
    from utils.auth import is_user_authorized
except ImportError:
    # Fallback to importlib
    auth_file = web_admin_dir / "utils" / "auth.py"
    spec = importlib.util.spec_from_file_location("auth", str(auth_file))
    if spec and spec.loader:
        auth_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auth_module)
        is_user_authorized = auth_module.is_user_authorized
    else:
        st.error("❌ Не удалось загрузить модуль авторизации / Failed to load auth module")
        st.stop()

# Check authorization
if not is_user_authorized():
    # Show impressive login page
    auth_pages_file = web_admin_dir / "auth_pages.py"
    spec = importlib.util.spec_from_file_location("auth_pages", str(auth_pages_file))
    if spec and spec.loader:
        auth_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(auth_module)
            # Call the impressive login page function
            if hasattr(auth_module, 'show_impressive_login_page'):
                auth_module.show_impressive_login_page()
            else:
                st.error("⛔ Не авторизован / Not authorized")
                st.info("Пожалуйста, используйте бота для получения токена / Please use the bot to get a token")
        except Exception as e:
            st.error(f"❌ Ошибка загрузки страницы входа: {e}")
            st.info("Пожалуйста, используйте бота @GrantServiceHelperBot для получения токена")
    else:
        st.error("⛔ Не авторизован / Not authorized")
        st.info("Пожалуйста, используйте бота для получения токена / Please use the bot to get a token")
    st.stop()

# If authorized, show main page
st.title("🏛️ GrantService Admin Panel")

# Show user info
if 'user' in st.session_state:
    user = st.session_state['user']
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.metric("👤 Пользователь", user.get('username', 'Unknown'))
    
    with col2:
        st.metric("📱 Telegram ID", user.get('telegram_id', 'Unknown'))
    
    with col3:
        if st.button("🚪 Выйти"):
            # Clear session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

st.divider()

# Main content
st.markdown("""
## 📍 Навигация

Используйте боковое меню слева для перехода между разделами:

- **🏠 Главная** - Основные метрики и статус системы
- **👥 Пользователи** - Управление пользователями
- **📄 Грантовые заявки** - Просмотр и управление заявками
- **📊 Аналитика** - Детальная статистика
- **❓ Вопросы интервью** - Настройка вопросов
- **🤖 AI Agents** - Управление ИИ-агентами
- И другие разделы...

### 🎯 Быстрые действия

""")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Перейти к метрикам", use_container_width=True):
        st.switch_page("pages/🏠_Главная.py")

with col2:
    if st.button("👥 Управление пользователями", use_container_width=True):
        st.switch_page("pages/👥_Пользователи.py")

with col3:
    if st.button("📄 Грантовые заявки", use_container_width=True):
        st.switch_page("pages/📄_Грантовые_заявки.py")

# Info section
with st.expander("ℹ️ Информация о системе", expanded=False):
    st.info("""
    **GrantService Admin Panel v2.0**
    
    Система управления грантовыми заявками с поддержкой:
    - Автоматического создания заявок
    - ИИ-агентов для анализа
    - Детальной аналитики
    - Управления пользователями
    
    Разработчик: Андрей Отинов
    """)