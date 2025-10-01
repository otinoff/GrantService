#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница для просмотра анкет пользователей
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

import streamlit as st
import sys
import os
from datetime import datetime
import json

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

from data.database.models import GrantServiceDatabase
from utils.logger import setup_logger

# Инициализация базы данных
db = GrantServiceDatabase()

# Инициализация логгера
logger = setup_logger('user_anketas')

st.set_page_config(
    page_title="📋 Анкеты пользователей",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок страницы
st.title("📋 Анкеты пользователей")

# Инициализация БД
try:
    db_instance = db
    logger.info("✅ База данных успешно инициализирована")
except Exception as e:
    st.error(f"❌ Ошибка подключения к базе данных: {e}")
    logger.critical(f"Критическая ошибка БД: {e}", exc_info=True)
    st.stop()

# Боковая панель с фильтрами
st.sidebar.title("🎯 Фильтры")

# Фильтр по статусу
status_filter = st.sidebar.selectbox(
    "Статус",
    ["Все статусы", "completed", "active", "pending"],
    key="status_filter"
)

# Фильтр по периоду
period_filter = st.sidebar.selectbox(
    "Период",
    ["Все время", "Сегодня", "Неделя", "Месяц"],
    key="period_filter"
)

# Фильтр по пользователю
user_filter = st.sidebar.text_input(
    "Пользователь (username или ID)",
    placeholder="Введите username или telegram_id",
    key="user_filter"
)

# Основная область контента
st.subheader("📊 Статистика анкет")

try:
    # Получаем все сессии с анкетами
    with db_instance.connect() as conn:
        cursor = conn.cursor()
        
        # Общее количество анкет
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE anketa_id IS NOT NULL")
        total_anketas = cursor.fetchone()[0]
        
        # По статусам
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM sessions 
            WHERE anketa_id IS NOT NULL
            GROUP BY status
        """)
        status_counts = dict(cursor.fetchall())
        
        # По пользователям
        cursor.execute("""
            SELECT u.username, COUNT(*) 
            FROM sessions s
            LEFT JOIN users u ON s.telegram_id = u.telegram_id
            WHERE s.anketa_id IS NOT NULL
            GROUP BY u.username
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        user_counts = dict(cursor.fetchall())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Всего анкет",
            value=total_anketas
        )
    
    with col2:
        completed = status_counts.get('completed', 0)
        st.metric(
            label="Завершенных",
            value=completed
        )
    
    with col3:
        active = status_counts.get('active', 0)
        st.metric(
            label="Активных",
            value=active
        )
    
    with col4:
        pending = status_counts.get('pending', 0)
        st.metric(
            label="В процессе",
            value=pending
        )
    
    # Топ пользователи
    if user_counts:
        st.subheader("👥 Топ пользователи")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**По количеству анкет:**")
            for user, count in list(user_counts.items())[:5]:
                if user:
                    st.write(f"• @{user}: {count}")
                else:
                    st.write(f"• Без username: {count}")
    
except Exception as e:
    st.error(f"❌ Ошибка получения статистики: {e}")
    logger.error(f"Ошибка получения статистики: {e}")

# Список анкет
st.subheader("📋 Список анкет")

try:
    # Получаем все сессии с анкетами
    with db_instance.connect() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.*, u.username, u.first_name, u.last_name
            FROM sessions s
            LEFT JOIN users u ON s.telegram_id = u.telegram_id
            WHERE s.anketa_id IS NOT NULL
            ORDER BY s.created_at DESC
            LIMIT 100
        """)
        
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        all_anketas = []
        for row in results:
            anketa_data = dict(zip(columns, row))
            
            # Парсим JSON поля
            if anketa_data.get('interview_data'):
                try:
                    anketa_data['interview_data'] = json.loads(anketa_data['interview_data'])
                except:
                    anketa_data['interview_data'] = {}
            
            all_anketas.append(anketa_data)
    
    if not all_anketas:
        st.info("🔍 Анкеты не найдены")
    else:
        # Применяем фильтры
        filtered_anketas = all_anketas
        
        if status_filter != "Все статусы":
            filtered_anketas = [a for a in filtered_anketas if a['status'] == status_filter]
        
        if user_filter:
            user_filter_lower = user_filter.lower()
            filtered_anketas = [a for a in filtered_anketas 
                              if (a.get('username', '').lower().find(user_filter_lower) != -1 or 
                                  str(a.get('telegram_id', '')).find(user_filter) != -1)]
        
        # Отображаем количество отфильтрованных результатов
        st.write(f"**Найдено анкет: {len(filtered_anketas)}**")
        
        # Отображаем анкеты
        for anketa in filtered_anketas:
            with st.expander(f"📋 {anketa['anketa_id']} - {anketa.get('username', 'Unknown')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID анкеты:** {anketa['anketa_id']}")
                    st.write(f"**Пользователь:** @{anketa.get('username', 'N/A')} ({anketa.get('first_name', '')} {anketa.get('last_name', '')})")
                    st.write(f"**Telegram ID:** {anketa['telegram_id']}")
                    st.write(f"**Статус:** {anketa['status']}")
                    st.write(f"**Создано:** {anketa['started_at']}")
                
                with col2:
                    st.write(f"**Завершено:** {anketa.get('completed_at', 'N/A')}")
                    st.write(f"**Сообщений:** {anketa.get('total_messages', 0)}")
                    st.write(f"**AI запросов:** {anketa.get('ai_requests_count', 0)}")
                    st.write(f"**Название проекта:** {anketa.get('project_name', 'N/A')}")
                
                # Данные интервью
                if anketa.get('interview_data'):
                    st.write("**Данные интервью:**")
                    
                    # Показываем первые несколько вопросов
                    interview_data = anketa['interview_data']
                    if isinstance(interview_data, dict):
                        for i, (key, value) in enumerate(list(interview_data.items())[:5]):
                            st.write(f"• **{key}:** {value}")
                        
                        if len(interview_data) > 5:
                            st.write(f"... и еще {len(interview_data) - 5} вопросов")
                    
                    # Полные данные в раскрывающемся блоке
                    with st.expander("📄 Полные данные интервью"):
                        st.json(interview_data)
                
                # Кнопки действий
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔬 Исследования", key=f"research_{anketa['id']}"):
                        st.session_state.selected_anketa_for_research = anketa['anketa_id']
                        st.rerun()
                
                with col2:
                    if st.button("📊 Детали", key=f"details_{anketa['id']}"):
                        st.session_state.selected_anketa_details = anketa['anketa_id']
                        st.rerun()
                
                with col3:
                    if st.button("📋 Копировать ID", key=f"copy_{anketa['id']}"):
                        st.code(anketa['anketa_id'])
                        st.success("ID скопирован!")

except Exception as e:
    st.error(f"❌ Ошибка получения анкет: {e}")
    logger.error(f"Ошибка получения анкет: {e}")

# Просмотр исследований для анкеты
if 'selected_anketa_for_research' in st.session_state:
    st.subheader("🔬 Исследования для анкеты")
    
    try:
        research_list = db_instance.get_research_by_anketa_id(st.session_state.selected_anketa_for_research)
        
        if research_list:
            st.write(f"**Найдено исследований: {len(research_list)}**")
            
            for research in research_list:
                with st.expander(f"🔬 {research['research_id']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID исследования:** {research['research_id']}")
                        st.write(f"**Провайдер:** {research['llm_provider']}")
                        st.write(f"**Модель:** {research.get('model', 'N/A')}")
                        st.write(f"**Статус:** {research['status']}")
                    
                    with col2:
                        st.write(f"**Создано:** {research['created_at']}")
                        st.write(f"**Завершено:** {research.get('completed_at', 'N/A')}")
                        
                        if research.get('metadata'):
                            metadata = research['metadata']
                            st.write(f"**Токенов:** {metadata.get('tokens_used', 0)}")
                            st.write(f"**Время:** {metadata.get('processing_time_seconds', 0)} сек")
                    
                    # Результаты исследования
                    if research.get('research_results'):
                        st.write("**Результаты:**")
                        st.text_area(
                            "Содержание",
                            value=research['research_results'],
                            height=150,
                            key=f"research_results_{research['id']}"
                        )
        else:
            st.info("🔍 Исследования для этой анкеты не найдены")
            
    except Exception as e:
        st.error(f"❌ Ошибка получения исследований: {e}")

# Детальный просмотр анкеты
if 'selected_anketa_details' in st.session_state:
    st.subheader("📊 Детальный просмотр анкеты")
    
    try:
        anketa = db_instance.get_session_by_anketa_id(st.session_state.selected_anketa_details)
        
        if anketa:
            st.json(anketa)
        else:
            st.error("Анкета не найдена")
            
    except Exception as e:
        st.error(f"❌ Ошибка получения деталей анкеты: {e}")

# Информация в боковой панели
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Информация")
st.sidebar.info("""
**Анкеты пользователей**

Эта страница показывает все анкеты, созданные пользователями через Telegram бота.

**Структура ID:**
- Анкета: `#AN-YYYYMMDD-username-001`

**Процесс:**
1. Пользователь проходит интервью в Telegram боте
2. Создается анкета с уникальным ID
3. Researcher Agent проводит исследование на основе анкеты
4. Анкета и исследование передаются писателю как единый пакет
""")
