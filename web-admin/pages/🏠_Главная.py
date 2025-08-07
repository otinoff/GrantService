#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard page for GrantService admin panel
"""

import streamlit as st
import sys
import os
import requests
from datetime import datetime

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

from utils.database import AdminDatabase
from utils.charts import create_metrics_cards, create_daily_chart
from utils.logger import setup_logger

# Инициализация логгера
logger = setup_logger('main_page')

# Отображение главной страницы
st.title("🏆 ГрантСервис - Главная панель")

# Инициализация БД
db = AdminDatabase()

# Получение статуса бота
st.subheader("📊 Статус системы")

col1, col2 = st.columns(2)

with col1:
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN', '7685915842:AAGcW0kgtljyIob8enM3zvFSLuZ-BZzcPOo')}/getMe",
            timeout=5
        )
        if response.status_code == 200:
            st.success("✅ Telegram бот работает")
            bot_info = response.json()['result']
            st.info(f"Бот: @{bot_info['username']}")
        else:
            st.error("❌ Telegram бот не отвечает")
    except Exception as e:
        logger.error(f"Telegram bot connection error: {e}", exc_info=True)
        st.error(f"❌ Ошибка подключения к боту: {e}")

with col2:
    try:
        # Проверка FastAPI
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code == 200:
            st.success("✅ FastAPI сервер работает")
        else:
            st.warning("⚠️ FastAPI сервер недоступен")
    except:
        st.warning("⚠️ FastAPI сервер недоступен")

# Основные метрики
st.subheader("📈 Основные метрики")

stats = db.get_basic_stats()
create_metrics_cards(stats)

# График активности
st.subheader("📊 Активность по дням")

daily_stats = db.get_daily_stats(days=7)
create_daily_chart(daily_stats, "Сессии за последние 7 дней")

# Последние сессии
st.subheader("🕒 Последние сессии")

recent_sessions = db.get_user_sessions(limit=10)

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