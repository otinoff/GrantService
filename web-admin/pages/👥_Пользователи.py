#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Users Management Page - GrantService Admin (v2.0)
Full integration: Все пользователи | Анкеты | Поиск
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import pandas as pd
import json

# PATH SETUP
sys.path.insert(0, str(Path(__file__).parent.parent))
import setup_paths

# IMPORTS
try:
    from utils.database import AdminDatabase
    from utils.ui_helpers import render_page_header, render_metric_cards, render_tabs, show_error_message
    from utils.logger import setup_logger
    from data.database import (
        get_all_users_progress,
        get_questions_with_answers,
        export_user_form,
        get_total_users,
        GrantServiceDatabase
    )
except ImportError as e:
    st.error(f"Error importing: {e}")
    st.stop()

# PAGE CONFIG
st.set_page_config(page_title="Пользователи", page_icon="👥", layout="wide")
logger = setup_logger('users_page')

# DATABASE
import os

# NOTE: Migrated to PostgreSQL - hardcoded SQLite paths removed
# Database access now via postgres_helper.execute_query()

@st.cache_resource
def get_database():
    return AdminDatabase()

@st.cache_resource
def get_grant_database():
    # PostgreSQL - параметры из переменных окружения
    return GrantServiceDatabase()

db = get_database()
grant_db = get_grant_database()

# DATA FUNCTIONS
@st.cache_data(ttl=60)
def get_users_metrics():
    """Получить метрики пользователей"""
    try:
        users_progress = get_all_users_progress()
        total = get_total_users()
        completed = len([u for u in users_progress if u['progress']['status'] == 'completed'])
        in_progress = len([u for u in users_progress if u['progress']['status'] == 'in_progress'])
        avg_prog = sum([u['progress']['progress_percent'] for u in users_progress]) / len(users_progress) if users_progress else 0

        return {
            'total_users': total,
            'completed_users': completed,
            'in_progress_users': in_progress,
            'avg_progress': avg_prog,
            'users_progress': users_progress
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}", exc_info=True)
        return {
            'total_users': 0,
            'completed_users': 0,
            'in_progress_users': 0,
            'avg_progress': 0,
            'users_progress': []
        }

@st.cache_data(ttl=60)
def get_all_questionnaires():
    """Получить все анкеты из сессий"""
    try:
        from utils.postgres_helper import execute_query

        # Fixed: JOIN by telegram_id, not by id
        results = execute_query("""
            SELECT s.*, u.username, u.first_name, u.last_name
            FROM sessions s
            LEFT JOIN users u ON s.telegram_id = u.telegram_id
            WHERE s.anketa_id IS NOT NULL
            ORDER BY s.started_at DESC
            LIMIT 100
        """)

        all_anketas = []
        if results:
            for row in results:
                anketa_data = dict(row)

                # Convert datetime objects to strings for JSON serialization (caching)
                for key, value in anketa_data.items():
                    if isinstance(value, datetime):
                        anketa_data[key] = value.isoformat()

                # Get interview answers - from JSONB field in sessions table
                interview_data_raw = anketa_data.get('interview_data')

                if interview_data_raw and isinstance(interview_data_raw, dict):
                    # Get active questions to map field_name to question_text
                    questions = execute_query("""
                        SELECT question_number, question_text, field_name
                        FROM interview_questions
                        WHERE is_active = true
                        ORDER BY question_number
                    """)

                    # Create field_name -> question_text mapping
                    field_to_question = {}
                    if questions:
                        for q in questions:
                            field_to_question[q['field_name']] = q['question_text']

                    # Convert interview_data from {field_name: answer} to {question_text: answer}
                    interview_dict = {}
                    for i, (field_name, answer) in enumerate(interview_data_raw.items(), 1):
                        # Get full question text
                        q_text = field_to_question.get(field_name, field_name)

                        # Format: "Вопрос N: Full question text"
                        key = f"Вопрос {i}: {q_text}"
                        interview_dict[key] = answer

                    anketa_data['interview_data'] = interview_dict
                else:
                    anketa_data['interview_data'] = {}

                all_anketas.append(anketa_data)

        return all_anketas
    except Exception as e:
        logger.error(f"Error getting questionnaires: {e}", exc_info=True)
        return []

def format_time_ago(dt_string: str) -> str:
    """Форматировать время 'X назад'"""
    if not dt_string:
        return "N/A"
    try:
        last_activity = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        time_diff = datetime.now(last_activity.tzinfo) - last_activity

        if time_diff.days > 0:
            return f"{time_diff.days} дн. назад"
        elif time_diff.seconds > 3600:
            return f"{time_diff.seconds // 3600} ч. назад"
        else:
            return f"{time_diff.seconds // 60} мин. назад"
    except:
        return dt_string

def format_datetime_kemerovo(dt_value) -> str:
    """Форматировать дату/время в GMT+7 (Кемеровское время) без секунд"""
    if not dt_value:
        return "Не указано"

    try:
        # Parse datetime
        if isinstance(dt_value, str):
            # Remove 'Z' and parse
            dt_str = dt_value.replace('Z', '')
            dt = datetime.fromisoformat(dt_str)
        elif isinstance(dt_value, datetime):
            dt = dt_value
        else:
            return str(dt_value)

        # If datetime is naive (no timezone info), assume it's already in Kemerovo time (GMT+7)
        # PostgreSQL TIMESTAMP WITHOUT TIME ZONE stores local server time
        if dt.tzinfo is None:
            # Already in Kemerovo time, just format
            dt_kemerovo = dt
        else:
            # Has timezone info, convert to GMT+7
            kemerovo_tz = timezone(timedelta(hours=7))
            dt_kemerovo = dt.astimezone(kemerovo_tz)

        # Format: "07 октября 2025, 20:16"  (without seconds)
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

        day = dt_kemerovo.day
        month = months[dt_kemerovo.month - 1]
        year = dt_kemerovo.year
        hour = dt_kemerovo.hour
        minute = dt_kemerovo.minute

        return f"{day:02d} {month} {year}, {hour:02d}:{minute:02d}"

    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return str(dt_value)

def render_user_card(user: Dict):
    """Отобразить карточку пользователя"""
    telegram_id = user['telegram_id']
    progress = user['progress']
    current_question = user.get('current_question_info', {})

    # Определяем цвет статуса
    status_colors = {
        'completed': '🟢',
        'in_progress': '🟡',
        'not_started': '🔵'
    }
    status_color = status_colors.get(progress['status'], '⚪')

    # Создаем прогресс-бар
    progress_bar_length = 20
    filled_length = int(progress_bar_length * progress['progress_percent'] / 100)
    progress_bar = "█" * filled_length + "░" * (progress_bar_length - filled_length)

    # Имя пользователя
    user_display_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
    if user.get('username'):
        user_display_name += f" (@{user['username']})"
    if not user_display_name:
        user_display_name = f"Пользователь {telegram_id}"

    with st.expander(f"{status_color} {user_display_name}"):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**Telegram ID:** {telegram_id}")

            # Прогресс-бар
            progress_text = f"**Прогресс:** {progress_bar} {progress['answered_questions']}/{progress['total_questions']} ({progress['progress_percent']}%)"
            st.write(progress_text)

            # Текущий вопрос
            if progress['status'] == 'completed':
                st.success("✅ Анкета полностью заполнена")
            elif progress['status'] == 'in_progress' and current_question:
                q_num = current_question.get('question_number', '')
                q_text = current_question.get('question_text', '')
                if q_text:
                    st.write(f"**Текущий вопрос #{q_num}:** {q_text[:100]}...")
            else:
                st.info("📝 Анкета не начата")

            # Последняя активность
            if user.get('last_activity'):
                activity_text = format_time_ago(user['last_activity'])
                st.write(f"**Последняя активность:** {activity_text}")

        with col2:
            if st.button("📋 Все ответы", key=f"answers_{telegram_id}"):
                st.session_state.selected_user = telegram_id
                st.session_state.view_mode = 'answers'
                st.rerun()

            if st.button("📊 Прогресс", key=f"progress_{telegram_id}"):
                st.session_state.selected_user = telegram_id
                st.session_state.view_mode = 'progress'
                st.rerun()

            if st.button("💾 Экспорт", key=f"export_{telegram_id}"):
                try:
                    export_text = export_user_form(telegram_id)

                    # Формируем имя файла
                    file_name = f"anketa_{telegram_id}"
                    if user_display_name and user_display_name != f"Пользователь {telegram_id}":
                        clean_name = "".join(c for c in user_display_name if c.isalnum() or c in (' ', '-', '_')).strip()
                        clean_name = clean_name.replace(' ', '_')
                        if clean_name:
                            file_name = f"anketa_{clean_name}"

                    file_name += f"_{datetime.now().strftime('%Y%m%d')}.txt"

                    st.download_button(
                        label="📥 Скачать анкету",
                        data=export_text,
                        file_name=file_name,
                        mime="text/plain",
                        key=f"download_{telegram_id}"
                    )
                except Exception as e:
                    logger.error(f"Error exporting user form: {e}", exc_info=True)
                    st.error(f"❌ Ошибка экспорта: {e}")

def render_user_details():
    """Отобразить детали выбранного пользователя"""
    if 'selected_user' not in st.session_state:
        return

    user_id = st.session_state.selected_user
    view_mode = st.session_state.get('view_mode', 'answers')

    # Получаем данные пользователя
    metrics = get_users_metrics()
    users_progress = metrics['users_progress']
    selected_user_data = next((u for u in users_progress if u['telegram_id'] == user_id), None)

    if not selected_user_data:
        st.error("Пользователь не найден")
        return

    user_display_name = f"{selected_user_data.get('first_name', '')} {selected_user_data.get('last_name', '')}".strip()
    if selected_user_data.get('username'):
        user_display_name += f" (@{selected_user_data['username']})"
    if not user_display_name:
        user_display_name = f"Пользователь {user_id}"

    magnifier_emoji = "🔍"
    st.subheader(f"{magnifier_emoji} {user_display_name}")

    # Навигация
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📋 Ответы", disabled=(view_mode == 'answers')):
            st.session_state.view_mode = 'answers'
            st.rerun()
    with col2:
        if st.button("📊 Прогресс", disabled=(view_mode == 'progress')):
            st.session_state.view_mode = 'progress'
            st.rerun()
    with col3:
        if st.button("📈 Статистика", disabled=(view_mode == 'stats')):
            st.session_state.view_mode = 'stats'
            st.rerun()
    with col4:
        if st.button("❌ Закрыть"):
            del st.session_state.selected_user
            if 'view_mode' in st.session_state:
                del st.session_state.view_mode
            st.rerun()

    st.divider()

    try:
        if view_mode == 'answers':
            # Показываем все вопросы с ответами
            questions_with_answers = get_questions_with_answers(user_id)

            for qa in questions_with_answers:
                with st.container():
                    if qa['answered']:
                        st.success(f"✅ **Вопрос {qa['question_number']}:** {qa['question_text']}")
                        st.write(f"**Ответ:** {qa['answer']}")
                    else:
                        st.warning(f"❓ **Вопрос {qa['question_number']}:** {qa['question_text']}")
                        st.write("**Ответ:** _(не заполнено)_")

                    if qa.get('hint_text'):
                        st.caption(f"💡 Подсказка: {qa['hint_text']}")

                    st.divider()

        elif view_mode == 'progress':
            # Визуальный прогресс-бар
            progress = selected_user_data['progress']

            # Большой прогресс-бар
            progress_percent = progress['progress_percent']
            progress_text = f"Прогресс: {progress['answered_questions']}/{progress['total_questions']} ({progress_percent}%)"
            st.progress(progress_percent / 100, text=progress_text)

            # Детальная информация
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Отвечено вопросов", progress['answered_questions'])
            with col2:
                st.metric("Всего вопросов", progress['total_questions'])
            with col3:
                st.metric("Текущий вопрос", progress['current_question'])

            # Показываем прогресс по каждому вопросу
            clipboard_emoji = "📋"
            st.subheader(f"{clipboard_emoji} Детальный прогресс")

            questions_with_answers = get_questions_with_answers(user_id)

            for qa in questions_with_answers:
                col1, col2 = st.columns([1, 4])

                with col1:
                    if qa['answered']:
                        st.success(f"✅ #{qa['question_number']}")
                    else:
                        st.error(f"❌ #{qa['question_number']}")

                with col2:
                    st.write(qa['question_text'])

        elif view_mode == 'stats':
            # Статистика пользователя
            progress = selected_user_data['progress']

            chart_emoji = "📈"
            st.subheader(f"{chart_emoji} Статистика заполнения")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Общая информация:**")
                st.write(f"• Дата регистрации: {selected_user_data.get('registration_date', 'N/A')}")
                st.write(f"• Последняя активность: {selected_user_data.get('last_activity', 'N/A')}")
                st.write(f"• Статус анкеты: {progress['status']}")

            with col2:
                st.write("**Прогресс:**")
                st.write(f"• Завершено: {progress['progress_percent']}%")
                remaining = progress['total_questions'] - progress['answered_questions']
                st.write(f"• Осталось вопросов: {remaining}")

                if progress['status'] == 'in_progress':
                    st.write(f"• Следующий вопрос: #{progress['current_question']}")

    except Exception as e:
        logger.error(f"Error in user detail view: {e}", exc_info=True)
        st.error(f"❌ Ошибка отображения данных: {e}")

# MAIN
render_page_header("Пользователи", "👥", "Управление пользователями и анкетами")

try:
    metrics = get_users_metrics()

    # TABS
    tab1, tab2, tab3 = st.tabs(["📋 Все пользователи", "📝 Анкеты", "🔍 Поиск"])

    with tab1:

        users_emoji = "👥"
        st.markdown(f"### {users_emoji} Все пользователи")

        # Метрики
        render_metric_cards([
            {'label': 'Всего', 'value': metrics['total_users'], 'icon': '👥'},
            {'label': 'Завершили', 'value': metrics['completed_users'], 'icon': '✅'},
            {'label': 'В процессе', 'value': metrics['in_progress_users'], 'icon': '🟡'},
            {'label': 'Средний %', 'value': f"{round(metrics['avg_progress'],1)}%", 'icon': '📊'}
        ], columns=4)

        # Фильтры
        search_emoji = "🔍"
        st.subheader(f"{search_emoji} Фильтры и поиск")

        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Статус анкеты",
                ["Все", "Завершено", "В процессе", "Не начато"]
            )

        with col2:
            search_user = st.text_input("Поиск по Telegram ID", placeholder="Введите ID пользователя")

        with col3:
            sort_by = st.selectbox(
                "Сортировка",
                ["По последней активности", "По прогрессу", "По дате регистрации"]
            )

        # Фильтруем пользователей
        filtered_users = metrics['users_progress'].copy()

        # Фильтр по статусу
        if status_filter != "Все":
            status_map = {
                "Завершено": "completed",
                "В процессе": "in_progress",
                "Не начато": "not_started"
            }
            filtered_users = [u for u in filtered_users if u['progress']['status'] == status_map[status_filter]]

        # Поиск по ID
        if search_user:
            filtered_users = [u for u in filtered_users if search_user in str(u['telegram_id'])]

        # Сортировка
        if sort_by == "По прогрессу":
            filtered_users.sort(key=lambda x: x['progress']['progress_percent'], reverse=True)
        elif sort_by == "По дате регистрации":
            filtered_users.sort(key=lambda x: x.get('registration_date', ''), reverse=True)
        else:
            filtered_users.sort(key=lambda x: x.get('last_activity', ''), reverse=True)

        # Отображение пользователей
        if filtered_users:
            list_emoji = "📋"
            st.subheader(f"{list_emoji} Список пользователей ({len(filtered_users)})")

            for user in filtered_users:
                render_user_card(user)
        else:
            st.info("📝 Нет пользователей, соответствующих фильтрам")

        # Детализация выбранного пользователя
        render_user_details()

    with tab2:
        form_emoji = "📝"
        st.markdown(f"### {form_emoji} Анкеты")

        # Получаем все анкеты
        all_anketas = get_all_questionnaires()

        if not all_anketas:
            st.info("🔍 Анкеты не найдены")
        else:
            # Статистика
            stats_emoji = "📊"
            st.subheader(f"{stats_emoji} Статистика анкет")

            status_counts = {}
            for anketa in all_anketas:
                status = anketa.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Всего анкет", len(all_anketas))

            with col2:
                completed = status_counts.get('completed', 0)
                st.metric("Завершенных", completed)

            with col3:
                active = status_counts.get('active', 0)
                st.metric("Активных", active)

            with col4:
                pending = status_counts.get('pending', 0)
                st.metric("В процессе", pending)

            # Фильтры
            st.subheader("🎯 Фильтры")

            col1, col2 = st.columns(2)

            with col1:
                anketa_status_filter = st.selectbox(
                    "Статус",
                    ["Все статусы", "completed", "active", "pending"],
                    key="anketa_status_filter"
                )

            with col2:
                anketa_user_filter = st.text_input(
                    "Пользователь (username или ID)",
                    placeholder="Введите username или telegram_id",
                    key="anketa_user_filter"
                )

            # Применяем фильтры
            filtered_anketas = all_anketas

            if anketa_status_filter != "Все статусы":
                filtered_anketas = [a for a in filtered_anketas if a.get('status') == anketa_status_filter]

            if anketa_user_filter:
                user_filter_lower = anketa_user_filter.lower()
                filtered_anketas = [a for a in filtered_anketas
                                  if (a.get('username', '').lower().find(user_filter_lower) != -1 or
                                      str(a.get('telegram_id', '')).find(anketa_user_filter) != -1)]

            # Отображаем количество отфильтрованных результатов
            st.write(f"**Найдено анкет: {len(filtered_anketas)}**")

            # Отображаем анкеты
            for anketa in filtered_anketas:
                anketa_id = anketa.get('anketa_id', 'N/A')
                username = anketa.get('username', 'Unknown')

                form_icon = "📋"
                with st.expander(f"{form_icon} {anketa_id} - {username}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**ID анкеты:** {anketa_id}")
                        first_name = anketa.get('first_name', '')
                        last_name = anketa.get('last_name', '')
                        user_full = f"@{username} ({first_name} {last_name})"
                        st.write(f"**Пользователь:** {user_full}")
                        st.write(f"**Telegram ID:** {anketa.get('telegram_id')}")
                        st.write(f"**Статус:** {anketa.get('status')}")
                        st.write(f"**Создано:** {anketa.get('started_at', 'N/A')}")

                    with col2:
                        st.write(f"**Завершено:** {anketa.get('completed_at', 'N/A')}")
                        st.write(f"**Сообщений:** {anketa.get('total_messages', 0)}")
                        st.write(f"**AI запросов:** {anketa.get('ai_requests_count', 0)}")
                        st.write(f"**Название проекта:** {anketa.get('project_name', 'N/A')}")

                    # Данные интервью
                    interview_data = anketa.get('interview_data', {})
                    if interview_data:
                        st.write("**Данные интервью:**")

                        if isinstance(interview_data, dict):
                            for i, (key, value) in enumerate(list(interview_data.items())[:5]):
                                st.write(f"• **{key}:** {value}")

                            if len(interview_data) > 5:
                                remaining = len(interview_data) - 5
                                st.write(f"... и еще {remaining} вопросов")

                        # Полные данные в раскрывающемся блоке
                        with st.expander("📄 Полные данные интервью"):
                            st.json(interview_data)

                    # Кнопки действий
                    col1, col2 = st.columns(2)

                    with col1:
                        copy_emoji = "📋"
                        if st.button(f"{copy_emoji} Копировать ID", key=f"copy_{anketa.get('id')}"):
                            st.code(anketa_id)
                            st.success("ID скопирован!")

                    with col2:
                        # Prepare TXT export data (simplified - no intermediate button)
                        txt_lines = []
                        txt_lines.append("=" * 80)
                        txt_lines.append(f"АНКЕТА {anketa_id}")  # Removed # prefix
                        txt_lines.append("=" * 80)
                        txt_lines.append("")
                        txt_lines.append(f"Пользователь: @{anketa.get('username', 'Unknown')}")
                        txt_lines.append(f"Имя: {anketa.get('first_name', '')} {anketa.get('last_name', '')}")
                        txt_lines.append(f"Telegram ID: {anketa.get('telegram_id', 'N/A')}")
                        txt_lines.append(f"Статус: {anketa.get('status', 'N/A')}")
                        txt_lines.append(f"Создано: {format_datetime_kemerovo(anketa.get('started_at'))}")
                        txt_lines.append(f"Завершено: {format_datetime_kemerovo(anketa.get('completed_at'))}")
                        txt_lines.append(f"Название проекта: {anketa.get('project_name', 'N/A')}")
                        txt_lines.append("")
                        txt_lines.append("-" * 80)
                        txt_lines.append("ВОПРОСЫ И ОТВЕТЫ")
                        txt_lines.append("-" * 80)
                        txt_lines.append("")

                        if interview_data:
                            for question, answer in interview_data.items():
                                txt_lines.append(question)
                                txt_lines.append(f"Ответ: {answer}")
                                txt_lines.append("")
                        else:
                            txt_lines.append("Нет данных интервью")

                        txt_lines.append("=" * 80)
                        txt_data = "\n".join(txt_lines)

                        # Direct download button - no intermediate step
                        st.download_button(
                            label="📥 Скачать TXT",
                            data=txt_data.encode('utf-8'),
                            file_name=f"anketa_{anketa_id}.txt",
                            mime="text/plain",
                            key=f"download_txt_{anketa.get('id')}"
                        )

    with tab3:
        search_icon = "🔍"
        st.markdown(f"### {search_icon} Расширенный поиск")

        with st.form("advanced_search"):
            col1, col2 = st.columns(2)

            with col1:
                search_telegram_id = st.text_input("Telegram ID")
                search_username = st.text_input("Username")
                search_email = st.text_input("Email")

            with col2:
                search_date_from = st.date_input("Дата регистрации (от)")
                search_date_to = st.date_input("Дата регистрации (до)")
                search_status = st.selectbox("Статус анкеты", ["Все", "Завершено", "В процессе", "Не начато"])

            col3, col4 = st.columns(2)

            with col3:
                search_progress_from = st.number_input("Прогресс от (%)", min_value=0, max_value=100, value=0)

            with col4:
                search_progress_to = st.number_input("Прогресс до (%)", min_value=0, max_value=100, value=100)

            submitted = st.form_submit_button("🔍 Искать")

            if submitted:
                # Применяем фильтры поиска
                search_results = metrics['users_progress'].copy()

                if search_telegram_id:
                    search_results = [u for u in search_results if search_telegram_id in str(u['telegram_id'])]

                if search_username:
                    search_results = [u for u in search_results
                                    if u.get('username') and search_username.lower() in u['username'].lower()]

                if search_status != "Все":
                    status_map = {
                        "Завершено": "completed",
                        "В процессе": "in_progress",
                        "Не начато": "not_started"
                    }
                    search_results = [u for u in search_results
                                    if u['progress']['status'] == status_map[search_status]]

                # Фильтр по прогрессу
                search_results = [u for u in search_results
                                if search_progress_from <= u['progress']['progress_percent'] <= search_progress_to]

                # Отображаем результаты
                if search_results:
                    st.success(f"Найдено пользователей: {len(search_results)}")

                    # Создаем DataFrame для экспорта
                    df_data = []
                    for user in search_results:
                        df_data.append({
                            'Telegram ID': user['telegram_id'],
                            'Username': user.get('username', 'N/A'),
                            'Имя': user.get('first_name', 'N/A'),
                            'Фамилия': user.get('last_name', 'N/A'),
                            'Прогресс %': user['progress']['progress_percent'],
                            'Статус': user['progress']['status'],
                            'Последняя активность': user.get('last_activity', 'N/A')
                        })

                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True)

                    # Экспорт в CSV
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Экспорт в CSV",
                        data=csv,
                        file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

                    # Показываем карточки пользователей
                    for user in search_results:
                        render_user_card(user)
                else:
                    st.info("🔍 Пользователи не найдены по заданным критериям")

except Exception as e:
    logger.error(f"Critical error in users page: {e}", exc_info=True)
    st.error(f"❌ Критическая ошибка загрузки страницы: {e}")
