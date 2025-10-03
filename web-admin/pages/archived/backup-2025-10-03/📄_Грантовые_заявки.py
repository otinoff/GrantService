#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница просмотра грантовых заявок
Отображение всех заполненных грантовых заявок из базы данных
"""

import streamlit as st
import sys
import os
import json
from datetime import datetime
import pandas as pd

# Добавляем пути для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService
sys.path.insert(0, grandparent_dir)
sys.path.insert(0, parent_dir)

# Проверка авторизации
try:
    from utils.auth import is_user_authorized, get_current_user
    if not is_user_authorized():
        st.error("⛔ Не авторизован / Not authorized")
        st.info("Пожалуйста, войдите через бота / Please login via bot")
        st.stop()
except ImportError as e:
    st.error(f"❌ Ошибка импорта / Import error: {e}")
    st.stop()

# Прямое подключение к БД без импорта модулей
import sqlite3
from pathlib import Path

# Определяем путь к БД относительно текущего файла (кроссплатформенно)
current_file = Path(__file__).resolve()
db_path = current_file.parent.parent.parent / "data" / "grantservice.db"

# Проверяем существование файла БД
if not db_path.exists():
    st.error(f"❌ База данных не найдена по пути: {db_path}")
    st.stop()

# Заголовок страницы
st.set_page_config(
    page_title="Грантовые заявки",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Грантовые заявки")
st.markdown("---")

# Функция для получения заявок - прямой SQL запрос
def get_grant_applications():
    """Получить все грантовые заявки из БД"""
    try:
        # Прямое подключение к БД
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Получаем заявки с информацией о пользователях
        query = """
        SELECT
            ga.id,
            ga.application_number,
            ga.title,
            ga.content_json,
            ga.summary,
            ga.status,
            ga.user_id,
            ga.session_id,
            ga.quality_score,
            ga.grant_fund,
            ga.requested_amount,
            ga.project_duration,
            ga.created_at,
            ga.updated_at,
            ga.admin_user,
            ga.llm_provider,
            ga.model_used,
            ga.processing_time,
            ga.tokens_used
        FROM grant_applications ga
        ORDER BY ga.created_at DESC
        """
        
        cursor.execute(query)
        columns = [description[0] for description in cursor.description]
        applications = []
        
        for row in cursor.fetchall():
            app = dict(zip(columns, row))
            # Парсим JSON контент если он есть
            if app.get('content_json'):
                try:
                    app['content_data'] = json.loads(app['content_json'])
                except:
                    app['content_data'] = {}
            else:
                app['content_data'] = {}
                
            # Добавляем заглушки для полей пользователя
            app.setdefault('username', None)
            app.setdefault('first_name', None)
            app.setdefault('last_name', None)
            app.setdefault('telegram_id', None)
            
            applications.append(app)
        
        conn.close()
        return applications
        
    except Exception as e:
        st.error(f"Ошибка при получении заявок: {e}")
        st.error(f"Путь к БД: {db_path}")
        import traceback
        st.error(traceback.format_exc())
        return []

# Получаем заявки
applications = get_grant_applications()

# Статистика
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Всего заявок", len(applications))

with col2:
    draft_count = len([a for a in applications if a['status'] == 'draft'])
    st.metric("Черновики", draft_count)

with col3:
    completed_count = len([a for a in applications if a['status'] == 'completed'])
    st.metric("Завершенные", completed_count)

with col4:
    if applications:
        avg_score = sum(a['quality_score'] or 0 for a in applications) / len(applications)
        st.metric("Средний балл", f"{avg_score:.1f}")
    else:
        st.metric("Средний балл", "0.0")

st.markdown("---")

# Фильтры
st.subheader("🔍 Фильтры")
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    status_filter = st.selectbox(
        "Статус",
        ["Все"] + list(set(a['status'] for a in applications if a['status']))
    )

with filter_col2:
    user_filter = st.selectbox(
        "Пользователь",
        ["Все"] + list(set(f"{a['first_name']} {a['last_name']}" 
                          for a in applications 
                          if a['first_name'] or a['last_name']))
    )

with filter_col3:
    date_filter = st.date_input(
        "Дата создания (от)",
        value=None,
        format="DD.MM.YYYY"
    )

# Применяем фильтры
filtered_apps = applications

if status_filter != "Все":
    filtered_apps = [a for a in filtered_apps if a['status'] == status_filter]

if user_filter != "Все":
    filtered_apps = [a for a in filtered_apps 
                    if f"{a['first_name']} {a['last_name']}" == user_filter]

if date_filter:
    filtered_apps = [a for a in filtered_apps 
                    if a['created_at'] and 
                    datetime.fromisoformat(a['created_at']).date() >= date_filter]

st.markdown("---")

# Отображение заявок
if filtered_apps:
    st.subheader(f"📋 Найдено заявок: {len(filtered_apps)}")
    
    # Tabs для разных видов отображения
    tab1, tab2, tab3 = st.tabs(["📊 Таблица", "📇 Карточки", "📈 Аналитика"])
    
    with tab1:
        # Таблица заявок
        df_data = []
        for app in filtered_apps:
            df_data.append({
                "ID": app['id'],
                "Номер": app['application_number'],
                "Название": app['title'][:50] + "..." if len(app['title']) > 50 else app['title'],
                "Пользователь": f"{app['first_name']} {app['last_name']}" if app['first_name'] else "Не указан",
                "Статус": app['status'],
                "Балл": app['quality_score'] or 0,
                "Сумма": f"{app['requested_amount']:,.0f} ₽" if app['requested_amount'] else "-",
                "Создана": datetime.fromisoformat(app['created_at']).strftime("%d.%m.%Y %H:%M") if app['created_at'] else "-"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Кнопка экспорта
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Скачать CSV",
            data=csv,
            file_name=f"grant_applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv'
        )
    
    with tab2:
        # Отображение карточками
        for i, app in enumerate(filtered_apps):
            with st.expander(f"📄 {app['title']}", expanded=(i == 0)):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Номер заявки:** {app['application_number']}")
                    st.write(f"**Пользователь:** {app['first_name']} {app['last_name']}" 
                            if app['first_name'] else "Не указан")
                    
                    if app['summary']:
                        st.write("**Краткое описание:**")
                        st.info(app['summary'])
                    
                    if app['content_data']:
                        st.write("**Содержание заявки:**")
                        
                        # Отображаем ключевые поля из JSON
                        for key, value in app['content_data'].items():
                            if isinstance(value, dict):
                                st.write(f"**{key}:**")
                                for sub_key, sub_value in value.items():
                                    st.write(f"  • {sub_key}: {sub_value}")
                            elif isinstance(value, list):
                                st.write(f"**{key}:** {', '.join(str(v) for v in value)}")
                            else:
                                st.write(f"**{key}:** {value}")
                
                with col2:
                    # Метрики заявки
                    st.metric("Статус", app['status'])
                    if app['quality_score']:
                        st.metric("Качество", f"{app['quality_score']:.1f}/10")
                    if app['requested_amount']:
                        st.metric("Запрашиваемая сумма", f"{app['requested_amount']:,.0f} ₽")
                    if app['project_duration']:
                        st.metric("Длительность", f"{app['project_duration']} мес.")
                    
                    # Даты
                    st.caption(f"**Создана:** {datetime.fromisoformat(app['created_at']).strftime('%d.%m.%Y %H:%M')}" 
                              if app['created_at'] else "-")
                    st.caption(f"**Обновлена:** {datetime.fromisoformat(app['updated_at']).strftime('%d.%m.%Y %H:%M')}" 
                              if app['updated_at'] else "-")
                
                # Действия с заявкой
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    if st.button(f"📝 Редактировать", key=f"edit_{app['id']}"):
                        st.session_state[f'edit_mode_{app["id"]}'] = True
                        st.rerun()
                
                with action_col2:
                    if st.button(f"📄 Экспорт в Word", key=f"export_{app['id']}"):
                        st.info("Функция экспорта будет добавлена")
                
                with action_col3:
                    if app['status'] == 'draft':
                        if st.button(f"✅ Отправить", key=f"submit_{app['id']}"):
                            st.success("Заявка отправлена!")
    
    with tab3:
        # Аналитика
        st.subheader("📊 Аналитика заявок")
        
        # График по статусам
        status_counts = {}
        for app in applications:
            status = app['status'] or 'unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.write("**Распределение по статусам:**")
                chart_data = pd.DataFrame.from_dict(status_counts, orient='index', columns=['Количество'])
                st.bar_chart(chart_data)
            
            with chart_col2:
                st.write("**Динамика создания заявок:**")
                # Группируем по датам
                date_counts = {}
                for app in applications:
                    if app['created_at']:
                        date = datetime.fromisoformat(app['created_at']).date()
                        date_counts[date] = date_counts.get(date, 0) + 1
                
                if date_counts:
                    date_df = pd.DataFrame.from_dict(date_counts, orient='index', columns=['Заявки'])
                    date_df = date_df.sort_index()
                    st.line_chart(date_df)
        
        # Топ пользователей
        st.write("**Топ активных пользователей:**")
        user_counts = {}
        for app in applications:
            user_name = f"{app['first_name']} {app['last_name']}" if app['first_name'] else "Неизвестный"
            user_counts[user_name] = user_counts.get(user_name, 0) + 1
        
        if user_counts:
            sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for user, count in sorted_users:
                st.write(f"• {user}: {count} заявок")

else:
    st.info("🔍 Нет заявок, соответствующих выбранным фильтрам")

# Кнопка обновления
st.markdown("---")
if st.button("🔄 Обновить данные"):
    st.cache_data.clear()
    st.rerun()

# Информация о последнем обновлении
st.caption(f"Последнее обновление: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
