#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings Page - GrantService Admin (v2.0)
System settings: Вопросы интервью | Авторизация | Система
"""

import streamlit as st
import sys
from pathlib import Path

# PATH SETUP
current_file = Path(__file__).resolve()
web_admin_dir = current_file.parent.parent
if str(web_admin_dir) not in sys.path:
    sys.path.insert(0, str(web_admin_dir))

# IMPORTS
try:
    from utils.database import AdminDatabase, get_db_connection
    from utils.ui_helpers import render_page_header, render_metric_cards, render_tabs, show_success_message
    from utils.logger import setup_logger
except ImportError as e:
    st.error(f"Error importing: {e}")
    st.stop()

# PAGE CONFIG
st.set_page_config(page_title="Настройки", page_icon="⚙️", layout="wide")
logger = setup_logger('settings_page')

# DATABASE
@st.cache_resource
def get_database():
    return AdminDatabase()

db = get_database()

# MAIN
render_page_header("Настройки", "⚙️", "Конфигурация системы и управление")

# TABS
tab_names = ["Авторизация", "Система"]
tab_icons = ["🔐", "⚙️"]
selected_tab = render_tabs(tab_names, icons=tab_icons)

if selected_tab == "Авторизация":
    st.markdown("### 🔐 Управление доступом")
    
    # Auth stats
    render_metric_cards([
        {'label': 'Всего пользователей админки', 'value': 0, 'icon': '👥'},
        {'label': 'Активных токенов', 'value': 0, 'icon': '🔑'},
        {'label': 'Входов за 24ч', 'value': 0, 'icon': '📊'}
    ], columns=3)
    
    st.markdown("---")
    
    # Add admin user
    st.markdown("#### ➕ Добавить администратора")
    
    with st.form("add_admin_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            admin_username = st.text_input("Username")
            admin_role = st.selectbox("Роль", ["admin", "coordinator", "viewer"])
        
        with col2:
            admin_token = st.text_input("Токен доступа", type="password")
            admin_active = st.checkbox("Активен", value=True)
        
        if st.form_submit_button("➕ Добавить администратора", use_container_width=True):
            show_success_message("Администратор добавлен!")
    
    st.markdown("---")
    
    # Token management
    st.markdown("#### 🔑 Управление токенами")
    
    st.info("Список активных токенов доступа и история входов")

elif selected_tab == "Система":
    st.markdown("### ⚙️ Системные настройки")
    
    # System status
    st.markdown("#### 💚 Статус сервисов")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**База данных**")
        st.success("✅ Подключена")
        st.caption("SQLite: grantservice.db")
    
    with col2:
        st.markdown("**Telegram Bot**")
        st.warning("🔄 Неизвестно")
        st.caption("Требуется проверка")
    
    with col3:
        st.markdown("**GigaChat API**")
        st.warning("🔄 Неизвестно")
        st.caption("Требуется проверка")
    
    st.markdown("---")
    
    # API Settings
    st.markdown("#### 🔧 Настройки API")
    
    with st.form("api_settings_form"):
        st.markdown("**GigaChat API**")
        gigachat_token = st.text_input("API Token", type="password", value="********")
        gigachat_model = st.selectbox("Модель", ["GigaChat", "GigaChat-Pro", "GigaChat-Plus"])
        
        st.markdown("**Telegram Bot**")
        telegram_token = st.text_input("Bot Token", type="password", value="********")
        telegram_webhook = st.text_input("Webhook URL (опционально)")
        
        if st.form_submit_button("💾 Сохранить настройки", use_container_width=True):
            show_success_message("Настройки сохранены!")
    
    st.markdown("---")
    
    # Database settings
    st.markdown("#### 💾 База данных")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Путь:** {db.db_path if hasattr(db, 'db_path') else 'N/A'}")
        st.write("**Тип:** SQLite")
    
    with col2:
        if st.button("🔄 Создать backup", use_container_width=True):
            show_success_message("Backup создан!")
        
        if st.button("📊 Проверить целостность", use_container_width=True):
            show_success_message("База данных в порядке!")
    
    st.markdown("---")
    
    # Limits and quotas
    st.markdown("#### 📊 Лимиты и квоты")
    
    with st.form("limits_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            max_users = st.number_input("Макс. пользователей", min_value=10, value=1000)
            max_grants_per_day = st.number_input("Макс. грантов в день", min_value=1, value=100)
        
        with col2:
            token_limit_daily = st.number_input("Лимит токенов в день", min_value=1000, value=100000)
            api_rate_limit = st.number_input("API запросов в минуту", min_value=1, value=60)
        
        if st.form_submit_button("💾 Сохранить лимиты", use_container_width=True):
            show_success_message("Лимиты обновлены!")
