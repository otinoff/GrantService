#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Questions management page for GrantService admin panel
"""

import streamlit as st
import sys
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

from utils.database import AdminDatabase
from data.database import get_interview_questions, insert_interview_question, update_interview_question, delete_interview_question

# Отображение управления вопросами
st.title("❓ Управление вопросами интервью")

# Инициализация БД
db = AdminDatabase()

# Получение вопросов
questions = get_interview_questions()

# Создание нового вопроса
st.subheader("➕ Создать новый вопрос")

with st.form("new_question_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        question_text = st.text_area("Текст вопроса", height=100, key="new_question")
        question_type = st.selectbox(
            "Тип вопроса",
            ["text", "choice", "number", "date"],
            key="new_type"
        )
        order_num = st.number_input("Порядок", min_value=1, value=1, key="new_order")
    
    with col2:
        is_required = st.checkbox("Обязательный", value=True, key="new_required")
        is_active = st.checkbox("Активен", value=True, key="new_active")
        
        # Дополнительные поля для выбора
        if question_type == "choice":
            options = st.text_area(
                "Варианты ответов (по одному на строку)",
                height=100,
                key="new_options"
            )
        else:
            options = ""
    
    submitted = st.form_submit_button("Создать вопрос")
    
    if submitted:
        if question_text:
            try:
                insert_interview_question(
                    question_text=question_text,
                    question_type=question_type,
                    order_num=order_num,
                    is_required=is_required,
                    is_active=is_active,
                    options=options if options else None
                )
                st.success("✅ Вопрос создан успешно!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Ошибка создания вопроса: {e}")
        else:
            st.error("❌ Заполните текст вопроса")

# Список существующих вопросов
st.subheader("📋 Существующие вопросы")

if questions:
    # Сортируем по порядку
    questions.sort(key=lambda x: x['question_number'])
    
    for i, question in enumerate(questions):
        with st.expander(f"Вопрос {question['question_number']}: {question['question_text'][:50]}..."):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Текст:** {question['question_text']}")
                st.write(f"**Тип:** {question['question_type']}")
                
                if question.get('options'):
                    st.write("**Варианты ответов:**")
                    options_list = question['options'].split('\n')
                    for option in options_list:
                        if option.strip():
                            st.write(f"• {option.strip()}")
            
            with col2:
                required_icon = "🔴" if question['is_required'] else "⚪"
                active_icon = "🟢" if question['is_active'] else "🔴"
                
                st.write(f"{required_icon} **Обязательный:** {'Да' if question['is_required'] else 'Нет'}")
                st.write(f"{active_icon} **Активен:** {'Да' if question['is_active'] else 'Нет'}")
                st.write(f"**ID:** {question['id']}")
                st.write(f"**Создан:** {question['created_at']}")
            
            # Кнопки управления
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✏️ Редактировать", key=f"edit_q_{question['id']}"):
                    st.session_state.editing_question = question['id']
                    st.rerun()
            
            with col2:
                if st.button("🔄 Переключить статус", key=f"toggle_q_{question['id']}"):
                    try:
                        new_status = not question['is_active']
                        update_interview_question(
                            question['id'],
                            is_active=new_status
                        )
                        st.success("✅ Статус обновлен!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ошибка обновления: {e}")
            
            with col3:
                if st.button("🗑️ Удалить", key=f"delete_q_{question['id']}"):
                    try:
                        delete_interview_question(question['id'])
                        st.success("✅ Вопрос удален!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ошибка удаления: {e}")
            
            # Форма редактирования
            if st.session_state.get('editing_question') == question['id']:
                st.subheader("✏️ Редактирование вопроса")
                
                with st.form(f"edit_q_form_{question['id']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_text = st.text_area(
                            "Текст вопроса",
                            value=question['question_text'],
                            height=100,
                            key=f"edit_q_text_{question['id']}"
                        )
                        edit_type = st.selectbox(
                            "Тип",
                            ["text", "choice", "number", "date"],
                            index=["text", "choice", "number", "date"].index(question['question_type']),
                            key=f"edit_q_type_{question['id']}"
                        )
                        edit_order = st.number_input(
                            "Порядок",
                            min_value=1,
                            value=question['question_number'],
                            key=f"edit_q_order_{question['id']}"
                        )
                    
                    with col2:
                        edit_required = st.checkbox(
                            "Обязательный",
                            value=question['is_required'],
                            key=f"edit_q_required_{question['id']}"
                        )
                        edit_active = st.checkbox(
                            "Активен",
                            value=question['is_active'],
                            key=f"edit_q_active_{question['id']}"
                        )
                        
                        # Дополнительные поля для выбора
                        if edit_type == "choice":
                            edit_options = st.text_area(
                                "Варианты ответов (по одному на строку)",
                                value=question.get('options', ''),
                                height=100,
                                key=f"edit_q_options_{question['id']}"
                            )
                        else:
                            edit_options = ""
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.form_submit_button("💾 Сохранить"):
                            try:
                                update_interview_question(
                                    question['id'],
                                    question_text=edit_text,
                                    question_type=edit_type,
                                    order_num=edit_order,
                                    is_required=edit_required,
                                    is_active=edit_active,
                                    options=edit_options if edit_options else None
                                )
                                st.success("✅ Вопрос обновлен!")
                                del st.session_state.editing_question
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Ошибка обновления: {e}")
                    
                    with col2:
                        if st.form_submit_button("❌ Отмена"):
                            del st.session_state.editing_question
                            st.rerun()
else:
    st.info("📝 Нет вопросов для интервью")

# Импорт/Экспорт
st.subheader("📤 Импорт/Экспорт")

col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Экспорт вопросов"):
        if questions:
            # Создаем JSON для экспорта
            export_data = {
                "questions": questions,
                "export_date": datetime.now().isoformat()
            }
            
            st.download_button(
                label="Скачать JSON",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"interview_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.warning("Нет вопросов для экспорта")

with col2:
    uploaded_file = st.file_uploader("📤 Импорт вопросов", type=['json'])
    
    if uploaded_file is not None:
        try:
            import_data = json.load(uploaded_file)
            
            if st.button("📥 Импортировать"):
                imported_count = 0
                
                for question_data in import_data.get('questions', []):
                    try:
                        insert_interview_question(
                            question_text=question_data['question_text'],
                            question_type=question_data['question_type'],
                            order_num=question_data['question_number'],
                            is_required=question_data['is_required'],
                            is_active=question_data['is_active'],
                            options=question_data.get('options')
                        )
                        imported_count += 1
                    except Exception as e:
                        st.error(f"Ошибка импорта вопроса: {e}")
                
                st.success(f"✅ Импортировано {imported_count} вопросов!")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {e}") 