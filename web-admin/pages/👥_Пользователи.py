#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Users management page for GrantService admin panel - Progress-based approach
"""

import streamlit as st
import sys
import pandas as pd
from datetime import datetime, timedelta

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

from data.database import get_all_users_progress, get_questions_with_answers, export_user_form, get_total_users
from utils.logger import setup_logger

# Инициализация логгера
logger = setup_logger('users_page')

# Отображение управления пользователями
st.title("👥 Пользователи")

try:
    # Получаем всех пользователей с прогрессом
    users_progress = get_all_users_progress()
    total_users = get_total_users()
    
    # Подсчитываем статистику по прогрессу анкет
    completed_users = len([u for u in users_progress if u['progress']['status'] == 'completed'])
    in_progress_users = len([u for u in users_progress if u['progress']['status'] == 'in_progress'])
    not_started_users = len([u for u in users_progress if u['progress']['status'] == 'not_started'])
    
    avg_progress = sum([u['progress']['progress_percent'] for u in users_progress]) / len(users_progress) if users_progress else 0
    
    # Верхняя панель с метриками
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего пользователей", total_users)
    
    with col2:
        st.metric("Завершили анкету", completed_users, delta=f"{round((completed_users/total_users)*100, 1)}%" if total_users > 0 else "0%")
    
    with col3:
        st.metric("В процессе", in_progress_users)
    
    with col4:
        st.metric("Средний прогресс", f"{round(avg_progress, 1)}%")
    
    # Фильтры
    st.subheader("🔍 Фильтры и поиск")
    
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
    filtered_users = users_progress.copy()
    
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
        filtered_users.sort(key=lambda x: x['registration_date'] or '', reverse=True)
    else:  # По последней активности
        filtered_users.sort(key=lambda x: x['last_activity'] or '', reverse=True)
    
    # Отображение пользователей
    if filtered_users:
        st.subheader(f"📋 Список пользователей ({len(filtered_users)})")
        
        for user in filtered_users:
            telegram_id = user['telegram_id']
            progress = user['progress']
            current_question = user['current_question_info']
            
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
            user_display_name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip()
            if user['username']:
                user_display_name += f" (@{user['username']})"
            if not user_display_name:
                user_display_name = f"Пользователь {telegram_id}"
            
            with st.expander(f"{status_color} {user_display_name}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Telegram ID:** {telegram_id}")
                    
                    # Прогресс-бар
                    st.write(f"**Прогресс:** {progress_bar} {progress['answered_questions']}/{progress['total_questions']} ({progress['progress_percent']}%)")
                    
                    # Текущий вопрос
                    if progress['status'] == 'completed':
                        st.success("✅ Анкета полностью заполнена")
                    elif progress['status'] == 'in_progress':
                        st.write(f"**Текущий вопрос #{current_question['question_number']}:** {current_question['question_text'][:100]}...")
                    else:
                        st.info("📝 Анкета не начата")
                    
                    # Последняя активность
                    if user['last_activity']:
                        try:
                            last_activity = datetime.fromisoformat(user['last_activity'].replace('Z', '+00:00'))
                            time_diff = datetime.now(last_activity.tzinfo) - last_activity
                            
                            if time_diff.days > 0:
                                activity_text = f"{time_diff.days} дн. назад"
                            elif time_diff.seconds > 3600:
                                activity_text = f"{time_diff.seconds // 3600} ч. назад"
                            else:
                                activity_text = f"{time_diff.seconds // 60} мин. назад"
                            
                            st.write(f"**Последняя активность:** {activity_text}")
                        except:
                            st.write(f"**Последняя активность:** {user['last_activity']}")
                
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
                                # Очищаем имя от спецсимволов
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
    
    else:
        st.info("📝 Нет пользователей, соответствующих фильтрам")

    # Детализация выбранного пользователя
    if st.session_state.get('selected_user'):
        user_id = st.session_state.selected_user
        view_mode = st.session_state.get('view_mode', 'answers')
        
        # Находим данные пользователя
        selected_user_data = next((u for u in users_progress if u['telegram_id'] == user_id), None)
        
        if selected_user_data:
            user_display_name = f"{selected_user_data['first_name'] or ''} {selected_user_data['last_name'] or ''}".strip()
            if selected_user_data['username']:
                user_display_name += f" (@{selected_user_data['username']})"
            if not user_display_name:
                user_display_name = f"Пользователь {user_id}"
            
            st.subheader(f"🔍 {user_display_name}")
            
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
                            
                            if qa['hint_text']:
                                st.caption(f"💡 Подсказка: {qa['hint_text']}")
                            
                            st.divider()
                
                elif view_mode == 'progress':
                    # Визуальный прогресс-бар
                    progress = selected_user_data['progress']
                    
                    # Большой прогресс-бар
                    progress_percent = progress['progress_percent']
                    st.progress(progress_percent / 100, text=f"Прогресс: {progress['answered_questions']}/{progress['total_questions']} ({progress_percent}%)")
                    
                    # Детальная информация
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Отвечено вопросов", progress['answered_questions'])
                    with col2:
                        st.metric("Всего вопросов", progress['total_questions'])
                    with col3:
                        st.metric("Текущий вопрос", progress['current_question'])
                    
                    # Показываем прогресс по каждому вопросу
                    st.subheader("📋 Детальный прогресс")
                    
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
                    
                    st.subheader("📈 Статистика заполнения")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Общая информация:**")
                        st.write(f"• Дата регистрации: {selected_user_data['registration_date']}")
                        st.write(f"• Последняя активность: {selected_user_data['last_activity']}")
                        st.write(f"• Статус анкеты: {progress['status']}")
                    
                    with col2:
                        st.write("**Прогресс:**")
                        st.write(f"• Завершено: {progress['progress_percent']}%")
                        st.write(f"• Осталось вопросов: {progress['total_questions'] - progress['answered_questions']}")
                        
                        if progress['status'] == 'in_progress':
                            st.write(f"• Следующий вопрос: #{progress['current_question']}")
                
            except Exception as e:
                logger.error(f"Error in user detail view: {e}", exc_info=True)
                st.error(f"❌ Ошибка отображения данных: {e}")

except Exception as e:
    logger.error(f"Critical error in users page: {e}", exc_info=True)
    st.error("❌ Критическая ошибка загрузки страницы. Проверьте логи.")