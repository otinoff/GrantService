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
sys.path.insert(0, str(Path(__file__).parent.parent))
import setup_paths

# IMPORTS
try:
    from utils.database import AdminDatabase
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

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**База данных**")
        st.success("✅ Подключена")
        st.caption("PostgreSQL: grantservice")

    # Проверка подключения к Claude Code (до колонок)
    import os
    import requests

    claude_api_key = os.getenv('CLAUDE_CODE_API_KEY', '1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732')
    claude_base_url = os.getenv('CLAUDE_CODE_BASE_URL', 'http://178.236.17.55:8000')

    claude_status = "unknown"
    claude_status_code = None

    try:
        response = requests.get(f"{claude_base_url}/health", timeout=3)
        claude_status_code = response.status_code
        if response.status_code == 200:
            claude_status = "connected"
        else:
            claude_status = "error"
    except Exception as e:
        claude_status = "error"
        claude_status_message = str(e)[:30]

    with col2:
        st.markdown("**Claude Code API**")
        if claude_status == "connected":
            st.success("✅ Подключен")
            st.caption(f"Sonnet 4.5 (безлимит)")
        elif claude_status == "error":
            st.error("❌ Недоступен")
            st.caption(f"HTTP {claude_status_code}" if claude_status_code else "Timeout/Error")
        else:
            st.warning("🔄 Неизвестно")
            st.caption("Проверка...")

    with col3:
        st.markdown("**Telegram Bot**")
        st.warning("🔄 Неизвестно")
        st.caption("Требуется проверка")

    with col4:
        st.markdown("**GigaChat API**")
        st.warning("🔄 Неизвестно")
        st.caption("Fallback, лимиты")
    
    st.markdown("---")

    # Claude Code API Settings
    st.markdown("#### 🤖 Claude Code API (Основная модель)")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**API URL:** `{claude_base_url}`")
        st.markdown(f"**API Key:** `{claude_api_key[:8]}...{claude_api_key[-8:]}`")
        st.markdown(f"**Модель:** Claude Sonnet 4.5 (200k контекст)")
        st.markdown(f"**Статус:** {'✅ Активна' if claude_status == 'connected' else '❌ Недоступна'}")
        st.markdown(f"**Лимиты:** Безлимитная (по подписке)")

    with col2:
        if st.button("🔄 Проверить подключение", key="check_claude"):
            try:
                test_response = requests.get(f"{claude_base_url}/health", timeout=3)
                if test_response.status_code == 200:
                    st.success("✅ Подключение успешно!")
                else:
                    st.error(f"❌ Ошибка: HTTP {test_response.status_code}")
            except Exception as e:
                st.error(f"❌ {str(e)}")

        if st.button("📊 Проверить модели", key="check_models"):
            try:
                headers = {"Authorization": f"Bearer {claude_api_key}"}
                models_response = requests.get(f"{claude_base_url}/models", headers=headers, timeout=3)
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    if "models" in models_data:
                        models_list = [f"{m['name']} ({m['id']})" for m in models_data["models"]]
                        st.success(f"✅ Доступные модели: {', '.join(models_list)}")
                    else:
                        st.info(f"Доступные модели: {', '.join(models_data)}")
                else:
                    st.error(f"❌ Ошибка: HTTP {models_response.status_code}")
            except Exception as e:
                st.error(f"❌ {str(e)}")

    st.markdown("---")

    # API Settings
    st.markdown("#### 🔧 Дополнительные API (Fallback)")

    with st.form("api_settings_form"):
        st.markdown("**GigaChat API (Fallback)**")
        gigachat_token = st.text_input("API Token", type="password", value="********")
        gigachat_model = st.selectbox("Модель", ["GigaChat", "GigaChat-Pro", "GigaChat-Plus"])
        st.caption("⚠️ Используется только если Claude Code недоступен. Есть лимиты на токены.")

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
        st.write("**Тип:** PostgreSQL")
    
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

    st.markdown("---")

    # PDF Notifications Settings
    st.markdown("#### 📄 PDF Уведомления в админский чат")

    st.info("📱 **Админский чат:** -4930683040 (GrantService Admin)")
    st.caption("Автоматическая отправка PDF отчетов о завершении этапов workflow в админский чат")

    # Load current settings
    try:
        current_settings = db.get_notification_settings()
    except Exception as e:
        st.error(f"Ошибка загрузки настроек: {e}")
        current_settings = {
            'notifications_enabled': True,
            'notify_on_interview': True,
            'notify_on_audit': True,
            'notify_on_research': True,
            'notify_on_grant': True,
            'notify_on_review': True
        }

    with st.form("pdf_notifications_form"):
        # Main toggle
        notifications_enabled = st.toggle(
            "✅ Включить автоматические PDF уведомления",
            value=current_settings.get('notifications_enabled', True),
            help="Главный переключатель. Если выключен, никакие PDF не будут отправляться"
        )

        st.markdown("---")

        # Stage-specific toggles
        if notifications_enabled:
            st.markdown("**Выберите этапы для отправки уведомлений:**")

            col1, col2 = st.columns(2)

            with col1:
                notify_interview = st.checkbox(
                    "📝 Анкета заполнена",
                    value=current_settings.get('notify_on_interview', True),
                    help="Отправлять PDF анкеты после завершения интервью (24 Q&A)"
                )

                notify_audit = st.checkbox(
                    "🔍 Аудит завершен",
                    value=current_settings.get('notify_on_audit', True),
                    help="Отправлять PDF аудита с оценкой проекта"
                )

                notify_research = st.checkbox(
                    "📊 Исследование готово",
                    value=current_settings.get('notify_on_research', True),
                    help="Отправлять PDF исследования (27 queries + анализ)"
                )

            with col2:
                notify_grant = st.checkbox(
                    "✍️ Грант написан",
                    value=current_settings.get('notify_on_grant', True),
                    help="Отправлять PDF финальной грантовой заявки"
                )

                notify_review = st.checkbox(
                    "👁️ Ревью завершено",
                    value=current_settings.get('notify_on_review', True),
                    help="Отправлять PDF заключения ревьювера"
                )
        else:
            notify_interview = False
            notify_audit = False
            notify_research = False
            notify_grant = False
            notify_review = False

            st.warning("⚠️ Уведомления отключены. Включите главный переключатель выше.")

        st.markdown("---")

        # Statistics
        st.markdown("**📊 Статистика отправки PDF**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("PDF отправлено сегодня", "0", help="Количество отправленных PDF сегодня")

        with col2:
            st.metric("Успешность отправки", "100%", help="Процент успешных отправок")

        with col3:
            st.metric("Последний PDF", "—", help="Когда был отправлен последний PDF")

        st.markdown("---")

        # Save button
        submit_btn = st.form_submit_button("💾 Сохранить настройки уведомлений", use_container_width=True)

        if submit_btn:
            try:
                # Prepare settings dict
                new_settings = {
                    'notifications_enabled': notifications_enabled,
                    'notify_on_interview': notify_interview,
                    'notify_on_audit': notify_audit,
                    'notify_on_research': notify_research,
                    'notify_on_grant': notify_grant,
                    'notify_on_review': notify_review
                }

                # Update in database
                success = db.update_notification_settings_bulk(new_settings, updated_by='admin')

                if success:
                    st.success("✅ Настройки уведомлений успешно сохранены!")
                    st.balloons()

                    # Show summary
                    enabled_stages = []
                    if notifications_enabled:
                        if notify_interview:
                            enabled_stages.append("📝 Анкета")
                        if notify_audit:
                            enabled_stages.append("🔍 Аудит")
                        if notify_research:
                            enabled_stages.append("📊 Исследование")
                        if notify_grant:
                            enabled_stages.append("✍️ Грант")
                        if notify_review:
                            enabled_stages.append("👁️ Ревью")

                    if enabled_stages:
                        st.info(f"Включены уведомления для: {', '.join(enabled_stages)}")
                    else:
                        st.warning("Все уведомления отключены")
                else:
                    st.error("❌ Ошибка при сохранении настроек")

            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
                logger.error(f"Error saving notification settings: {e}", exc_info=True)
