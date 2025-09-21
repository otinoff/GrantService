#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
General analytics page for GrantService admin panel
"""

import streamlit as st
import sys
import os

# Simple imports without path manipulation
# The environment will be set up by the launcher

# Authorization check
try:
    from utils.auth import is_user_authorized
    if not is_user_authorized():
        st.error("⛔ Не авторизован / Not authorized")
        st.info("Пожалуйста, используйте бота для получения токена / Please use the bot to get a token")
        st.stop()
except ImportError as e:
    st.error(f"❌ Ошибка импорта / Import error: {e}")
    st.info("Запустите через launcher.py / Run via launcher.py")
    st.stop()

General analytics page for GrantService admin panel
"""

import streamlit as st
import sys
import pandas as pd
from datetime import datetime, timedelta

import streamlit as st
import sys
import os

# Добавляем пути кроссплатформенно
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService
sys.path.insert(0, grandparent_dir)  # Для импорта config и data
sys.path.insert(0, parent_dir)  # Для импорта utils

# Проверка авторизации
from utils.auth import is_user_authorized

if not is_user_authorized():
    # Импортируем страницу входа
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "login_page",
        os.path.join(current_dir, "🔐_Вход.py")
    )
    login_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(login_module)
    login_module.show_login_page()
    st.stop()

from utils.database import AdminDatabase
from utils.charts import create_metrics_cards, create_daily_chart

# Отображение общей аналитики
st.title("📊 Общая аналитика")

# Инициализация БД
db = AdminDatabase()

# Получение статистики
stats = db.get_basic_stats()
daily_stats = db.get_daily_stats(days=30)

# Основные метрики
st.subheader("📈 Основные метрики")
create_metrics_cards(stats)

# Графики
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Активность по дням")
    create_daily_chart(daily_stats, "Сессии за последние 30 дней")

with col2:
    st.subheader("📈 Конверсия")
    # Здесь можно добавить график конверсии
    st.info("График конверсии")

# Детальная статистика
st.subheader("📋 Детальная статистика")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Среднее время сессии", "12 мин")
    st.metric("Пиковая нагрузка", "45 сессий/час")

with col2:
    st.metric("Успешные заявки", f"{stats.get('completed_apps', 0)}")
    st.metric("Отклоненные заявки", "23")

with col3:
    st.metric("Средний рейтинг", "4.8/5")
    st.metric("Время ответа", "2.3 сек")

# Экспорт данных
st.subheader("📤 Экспорт данных")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Экспорт статистики"):
        # Создаем DataFrame для экспорта
        stats_df = pd.DataFrame([stats])
        csv = stats_df.to_csv(index=False)
        st.download_button(
            label="Скачать CSV",
            data=csv,
            file_name=f"analytics_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📈 Экспорт графиков"):
        # Здесь можно добавить экспорт графиков
        st.info("Экспорт графиков") 