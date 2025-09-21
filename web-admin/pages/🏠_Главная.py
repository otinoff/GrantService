#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard page for GrantService admin panel
Кроссплатформенная версия с автоматическим определением ОС
"""

import streamlit as st
import sys
import os
import requests
import logging
from datetime import datetime
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

# First, check if there's a token in the URL
try:
    query_params = st.query_params  # Streamlit >= 1.30
except AttributeError:
    query_params = st.experimental_get_query_params()  # Streamlit < 1.30
token_from_url = query_params.get('token', [None])[0] if isinstance(query_params.get('token', None), list) else query_params.get('token', None)

# Debug output
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
else:
    st.sidebar.info("ℹ️ Токен не найден в URL")

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

# Check authorization - if token was just validated, user should be authorized now
if not is_user_authorized():
    # Import and show impressive login page
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

# Import utilities
try:
    # Import database
    try:
        from utils.database import AdminDatabase
    except ImportError:
        database_file = web_admin_dir / "utils" / "database.py"
        spec = importlib.util.spec_from_file_location("database", str(database_file))
        if spec and spec.loader:
            database_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(database_module)
            AdminDatabase = database_module.AdminDatabase
    
    # Import charts
    try:
        from utils.charts import create_metrics_cards, create_daily_chart
    except ImportError:
        charts_file = web_admin_dir / "utils" / "charts.py"
        spec = importlib.util.spec_from_file_location("charts", str(charts_file))
        if spec and spec.loader:
            charts_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(charts_module)
            create_metrics_cards = charts_module.create_metrics_cards
            create_daily_chart = charts_module.create_daily_chart
    
    # Import logger
    try:
        from utils.logger import setup_logger, log_exception, log_performance
    except ImportError:
        logger_file = web_admin_dir / "utils" / "logger.py"
        spec = importlib.util.spec_from_file_location("logger", str(logger_file))
        if spec and spec.loader:
            logger_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(logger_module)
            setup_logger = logger_module.setup_logger
            log_exception = logger_module.log_exception
            log_performance = logger_module.log_performance

except Exception as e:
    st.error(f"❌ Ошибка импорта утилит / Utilities import error: {e}")
    st.info("Проверьте установку зависимостей / Check dependencies installation")
    st.stop()

# Инициализация логгера с полным покрытием
logger = setup_logger('main_page', level=logging.INFO)

# Отображение главной страницы
st.title("🏆 ГрантСервис - Главная панель")

# Инициализация БД с обработкой ошибок
@log_exception(logger, "Ошибка инициализации базы данных")
def init_database():
    return AdminDatabase()

try:
    db = init_database()
    logger.info("✅ База данных успешно инициализирована")
except Exception as e:
    st.error(f"❌ Ошибка подключения к базе данных: {e}")
    logger.critical(f"Критическая ошибка БД: {e}", exc_info=True)
    st.stop()

# Получение статуса бота
st.subheader("📊 Статус системы")

col1, col2 = st.columns(2)

@log_performance(logger)
def check_telegram_bot():
    """Проверка статуса Telegram бота"""
    response = requests.get(
        f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN', '7685915842:AAGcW0kgtljyIob8enM3zvFSLuZ-BZzcPOo')}/getMe",
        timeout=5
    )
    return response

with col1:
    try:
        response = check_telegram_bot()
        if response.status_code == 200:
            st.success("✅ Telegram бот работает")
            bot_info = response.json()['result']
            st.info(f"Бот: @{bot_info['username']}")
            logger.info(f"Telegram bot @{bot_info['username']} online")
        else:
            st.error("❌ Telegram бот не отвечает")
            logger.warning(f"Telegram bot offline: HTTP {response.status_code}")
    except requests.exceptions.Timeout:
        logger.error("Telegram bot connection timeout", exc_info=True)
        st.error("❌ Таймаут подключения к боту (>5 сек)")
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram bot request error: {e}", exc_info=True)
        st.error(f"❌ Ошибка сети при подключении к боту")
    except Exception as e:
        logger.error(f"Telegram bot unexpected error: {e}", exc_info=True)
        st.error(f"❌ Неожиданная ошибка: {e}")

with col2:
    st.success("✅ Nginx прокси работает")
    st.info("admin.grantservice.ru → Streamlit админка")
    logger.info("Nginx proxy to Streamlit admin panel active")

# Основные метрики
st.subheader("📈 Основные метрики")

@log_performance(logger)
def get_metrics():
    """Получение основных метрик"""
    return db.get_basic_stats()

try:
    stats = get_metrics()
    create_metrics_cards(stats)
    logger.info(f"Metrics loaded: {stats['total_users']} users, {stats['recent_sessions']} sessions")
except Exception as e:
    logger.error(f"Error loading metrics: {e}", exc_info=True)
    st.error("❌ Ошибка загрузки метрик")
    # Показываем пустые метрики
    stats = {"total_users": 0, "recent_sessions": 0, "completed_apps": 0, "conversion_rate": 0}
    create_metrics_cards(stats)

# График активности
st.subheader("📊 Активность по дням")

@log_performance(logger)
def get_daily_activity():
    """Получение данных активности по дням"""
    return db.get_daily_stats(days=7)

try:
    daily_stats = get_daily_activity()
    create_daily_chart(daily_stats, "Сессии за последние 7 дней")
    logger.info(f"Daily stats loaded for {len(daily_stats)} days")
except Exception as e:
    logger.error(f"Error loading daily stats: {e}", exc_info=True)
    st.error("❌ Ошибка загрузки статистики по дням")

# Последние сессии
st.subheader("🕒 Последние сессии")

@log_performance(logger)
def get_recent_sessions():
    """Получение последних сессий"""
    return db.get_user_sessions(limit=10)

try:
    recent_sessions = get_recent_sessions()
    logger.info(f"Loaded {len(recent_sessions) if recent_sessions else 0} recent sessions")
except Exception as e:
    logger.error(f"Error loading recent sessions: {e}", exc_info=True)
    st.error("❌ Ошибка загрузки последних сессий")
    recent_sessions = []

if recent_sessions:
    for session in recent_sessions:
        with st.expander(f"Сессия {session['id']} - {session['started_at']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Пользователь:** {session['telegram_id']}")
                st.write(f"**Статус:** {session['status']}")
            with col2:
                st.write(f"**Создана:** {session['started_at']}")
                if session['completed_at']:
                    st.write(f"**Завершена:** {session['completed_at']}")
else:
    st.info("Нет данных о сессиях")

# Информация о системе
st.subheader("ℹ️ Информация о системе")

col1, col2, col3 = st.columns(3)

with col1:
    st.info(f"**Версия:** 2.0")
    st.info(f"**Дата:** {datetime.now().strftime('%d.%m.%Y')}")

with col2:
    st.info(f"**Время:** {datetime.now().strftime('%H:%M:%S')}")
    st.info("**Статус:** Активен")

with col3:
    st.info("**Разработчик:** Андрей Отинов")
    st.info("**Домен:** grantservice.onff.ru")

# Завершающий лог страницы
logger.info("🏠 Главная страница успешно загружена")