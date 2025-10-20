#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница для просмотра и управления готовыми грантами
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

import json

# Добавляем пути кроссплатформенно
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService
sys.path.insert(0, grandparent_dir)  # Для импорта config и data
sys.path.insert(0, parent_dir)  # Для импорта utils

from data.database.models import GrantServiceDatabase
from utils.logger import setup_logger

# Инициализация базы данных
db = GrantServiceDatabase()

# Инициализация логгера
logger = setup_logger('grants_page')

st.set_page_config(
    page_title="📋 Готовые гранты",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок страницы
st.title("📋 Готовые гранты")

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
    ["Все статусы", "draft", "completed", "submitted", "approved", "rejected"],
    key="status_filter"
)

# Фильтр по периоду
period_filter = st.sidebar.selectbox(
    "Период",
    ["Все время", "Сегодня", "Неделя", "Месяц"],
    key="period_filter"
)

# Фильтр по LLM провайдеру
provider_filter = st.sidebar.selectbox(
    "LLM провайдер",
    ["Все", "gigachat", "perplexity", "ollama"],
    key="provider_filter"
)

# Фильтр по пользователю
user_filter = st.sidebar.text_input(
    "Пользователь (username или ID)",
    placeholder="Введите username или telegram_id",
    key="user_filter"
)

# Основная область контента
st.subheader("📊 Статистика грантов")

try:
    # Получаем статистику грантов
    with db_instance.connect() as conn:
        cursor = conn.cursor()
        
        # Общее количество грантов
        cursor.execute("SELECT COUNT(*) FROM grants")
        total_grants = cursor.fetchone()[0]
        
        # По статусам
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM grants 
            GROUP BY status
        """)
        status_counts = dict(cursor.fetchall())
        
        # По пользователям
        cursor.execute("""
            SELECT username, COUNT(*) 
            FROM grants 
            WHERE username IS NOT NULL
            GROUP BY username
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        user_counts = dict(cursor.fetchall())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Всего грантов",
            value=total_grants
        )
    
    with col2:
        completed = status_counts.get('completed', 0)
        st.metric(
            label="Завершенных",
            value=completed
        )
    
    with col3:
        submitted = status_counts.get('submitted', 0)
        st.metric(
            label="Отправленных",
            value=submitted
        )
    
    with col4:
        approved = status_counts.get('approved', 0)
        st.metric(
            label="Одобренных",
            value=approved
        )
    
    # Топ пользователи
    if user_counts:
        st.subheader("👥 Топ пользователи")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**По количеству грантов:**")
            for user, count in list(user_counts.items())[:5]:
                if user:
                    st.write(f"• @{user}: {count}")
                else:
                    st.write(f"• Без username: {count}")
    
except Exception as e:
    st.error(f"❌ Ошибка получения статистики: {e}")
    logger.error(f"Ошибка получения статистики: {e}")

# Список грантов
st.subheader("📋 Список грантов")

try:
    # Получаем все гранты
    with db_instance.connect() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT g.*, s.username, s.first_name, s.last_name
            FROM grants g
            LEFT JOIN sessions s ON g.anketa_id = s.anketa_id
            ORDER BY g.created_at DESC
            LIMIT 100
        """)
        
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        all_grants = []
        for row in results:
            grant_data = dict(zip(columns, row))
            
            # Парсим JSON поля
            if grant_data.get('grant_sections'):
                try:
                    grant_data['grant_sections'] = json.loads(grant_data['grant_sections'])
                except:
                    grant_data['grant_sections'] = {}
            
            if grant_data.get('metadata'):
                try:
                    grant_data['metadata'] = json.loads(grant_data['metadata'])
                except:
                    grant_data['metadata'] = {}
            
            all_grants.append(grant_data)
    
    if not all_grants:
        st.info("🔍 Гранты не найдены")
    else:
        # Применяем фильтры
        filtered_grants = all_grants
        
        if status_filter != "Все статусы":
            filtered_grants = [g for g in filtered_grants if g['status'] == status_filter]
        
        if provider_filter != "Все":
            filtered_grants = [g for g in filtered_grants if g['llm_provider'] == provider_filter]
        
        if user_filter:
            user_filter_lower = user_filter.lower()
            filtered_grants = [g for g in filtered_grants 
                              if (g.get('username', '').lower().find(user_filter_lower) != -1 or 
                                  str(g.get('user_id', '')).find(user_filter) != -1)]
        
        # Отображаем количество отфильтрованных результатов
        st.write(f"**Найдено грантов: {len(filtered_grants)}**")
        
        # Отображаем гранты
        for grant in filtered_grants:
            with st.expander(f"📋 {grant['grant_id']} - {grant.get('username', 'Unknown')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID гранта:** {grant['grant_id']}")
                    st.write(f"**Анкета:** {grant['anketa_id']}")
                    st.write(f"**Исследование:** {grant['research_id']}")
                    st.write(f"**Пользователь:** @{grant.get('username', 'N/A')} ({grant.get('first_name', '')} {grant.get('last_name', '')})")
                    st.write(f"**Telegram ID:** {grant['user_id']}")
                    st.write(f"**Статус:** {grant['status']}")
                
                with col2:
                    st.write(f"**Название:** {grant.get('grant_title', 'N/A')}")
                    st.write(f"**LLM провайдер:** {grant['llm_provider']}")
                    st.write(f"**Модель:** {grant.get('model', 'N/A')}")
                    st.write(f"**Оценка качества:** {grant.get('quality_score', 0)}/10")
                    st.write(f"**Создан:** {grant['created_at']}")
                    if grant.get('submitted_at'):
                        st.write(f"**Отправлен:** {grant['submitted_at']}")
                
                # Содержание гранта
                if grant.get('grant_sections'):
                    st.write("**Содержание гранта:**")
                    
                    # Показываем первые несколько разделов
                    sections = grant['grant_sections']
                    if isinstance(sections, dict):
                        for i, (key, value) in enumerate(list(sections.items())[:3]):
                            st.write(f"• **{key}:** {value[:100]}..." if len(str(value)) > 100 else f"• **{key}:** {value}")
                        
                        if len(sections) > 3:
                            st.write(f"... и еще {len(sections) - 3} разделов")
                    
                    # Полные данные в раскрывающемся блоке
                    with st.expander("📄 Полное содержание гранта"):
                        st.json(sections)
                
                # Метаданные
                if grant.get('metadata'):
                    metadata = grant['metadata']
                    st.write("**Метаданные:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"• Токенов: {metadata.get('tokens_used', 0)}")
                    with col2:
                        st.write(f"• Время: {metadata.get('processing_time_seconds', 0)} сек")
                    with col3:
                        st.write(f"• Стоимость: {metadata.get('cost', 0.0)} ₽")
                
                # Кнопки действий
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("👁️ Просмотр", key=f"view_{grant['id']}"):
                        st.session_state.selected_grant_id = grant['grant_id']
                        st.rerun()
                
                with col2:
                    if st.button("✏️ Редактировать", key=f"edit_{grant['id']}"):
                        st.session_state.edit_grant_id = grant['grant_id']
                        st.rerun()
                
                with col3:
                    if st.button("📤 Отправить", key=f"submit_{grant['id']}"):
                        st.session_state.submit_grant_id = grant['grant_id']
                        st.rerun()
                
                with col4:
                    if st.button("💾 Экспорт", key=f"export_{grant['id']}"):
                        st.session_state.export_grant_id = grant['grant_id']
                        st.rerun()

except Exception as e:
    st.error(f"❌ Ошибка получения грантов: {e}")
    logger.error(f"Ошибка получения грантов: {e}")

# Детальный просмотр гранта
if 'selected_grant_id' in st.session_state:
    st.subheader("👁️ Детальный просмотр гранта")
    
    try:
        with db_instance.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM grants WHERE grant_id = ?", (st.session_state.selected_grant_id,))
            grant = cursor.fetchone()
            
            if grant:
                columns = [description[0] for description in cursor.description]
                grant_data = dict(zip(columns, grant))
                
                # Парсим JSON поля
                if grant_data.get('grant_sections'):
                    try:
                        grant_data['grant_sections'] = json.loads(grant_data['grant_sections'])
                    except:
                        grant_data['grant_sections'] = {}
                
                st.json(grant_data)
            else:
                st.error("Грант не найден")
                
    except Exception as e:
        st.error(f"❌ Ошибка получения деталей гранта: {e}")

# Информация в боковой панели
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Информация")
st.sidebar.info("""
**Готовые гранты**

Эта страница показывает все гранты, созданные Writer Agent на основе анкет и исследований.

**Структура ID:**
- Грант: `#GR-YYYYMMDD-username-001-AN-anketa_id`

**Статусы:**
- **draft** - черновик
- **completed** - завершен
- **submitted** - отправлен
- **approved** - одобрен
- **rejected** - отклонен

**Процесс:**
1. Анкета → Исследование → Грант
2. Грант создается Writer Agent
3. Может быть отправлен в фонд
4. Отслеживается статус рассмотрения
""")

if __name__ == "__main__":
    pass
