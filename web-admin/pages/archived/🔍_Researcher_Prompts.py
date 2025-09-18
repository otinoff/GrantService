#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Researcher prompts management page for GrantService admin panel
"""

import streamlit as st
import sys
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

from utils.database import AdminDatabase
from data.database import insert_agent_prompt, update_agent_prompt, delete_agent_prompt

# Отображение управления промптами исследователя
st.title("🔍 Управление промптами исследователя")

# Инициализация БД
db = AdminDatabase()

# Получение промптов
prompts = db.db.get_agent_prompts('researcher')

# Создание нового промпта
st.subheader("➕ Создать новый промпт")

with st.form("new_prompt_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        prompt_name = st.text_input("Название промпта", key="new_name")
        prompt_type = st.selectbox(
            "Тип промпта",
            ["task", "system", "context"],
            key="new_type"
        )
        order_num = st.number_input("Порядок", min_value=1, value=1, key="new_order")
    
    with col2:
        temperature = st.slider("Температура", 0.0, 2.0, 0.7, 0.1, key="new_temp")
        
        # Выбор модели Perplexity с ограничениями токенов
        model_name = st.selectbox(
            "Модель Perplexity",
            ["sonar", "sonar-pro", "reasoning-pro"],
            help="sonar: до 4K токенов, sonar-pro: до 32K токенов, reasoning-pro: до 32K токенов",
            key="new_model"
        )
        
        # Динамические ограничения токенов в зависимости от модели
        if model_name == "sonar":
            max_tokens = st.number_input(
                "Макс. токенов", 
                min_value=100, 
                max_value=4000, 
                value=2000, 
                help="sonar: максимум 4,000 токенов",
                key="new_tokens"
            )
        elif model_name == "sonar-pro":
            max_tokens = st.number_input(
                "Макс. токенов", 
                min_value=100, 
                max_value=32000, 
                value=4000, 
                help="sonar-pro: максимум 32,000 токенов",
                key="new_tokens"
            )
        else:  # reasoning-pro
            max_tokens = st.number_input(
                "Макс. токенов", 
                min_value=100, 
                max_value=32000, 
                value=4000, 
                help="reasoning-pro: максимум 32,000 токенов",
                key="new_tokens"
            )
    
    prompt_content = st.text_area(
        "Содержание промпта",
        height=200,
        placeholder="Введите содержание промпта...",
        key="new_content"
    )
    
    is_active = st.checkbox("Активен", value=True, key="new_active")
    
    submitted = st.form_submit_button("Создать промпт")
    
    if submitted:
        if prompt_name and prompt_content:
            try:
                insert_agent_prompt(
                    agent_type='researcher',
                    prompt_name=prompt_name,
                    prompt_content=prompt_content,
                    prompt_type=prompt_type,
                    order_num=order_num,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model_name=model_name,
                    is_active=is_active
                )
                st.success("✅ Промпт создан успешно!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Ошибка создания промпта: {e}")
        else:
            st.error("❌ Заполните все обязательные поля")

# Список существующих промптов
st.subheader("📋 Существующие промпты")

if prompts:
    # Фильтр по типу
    prompt_types = list(set([p['prompt_type'] for p in prompts]))
    selected_type = st.selectbox("Фильтр по типу", ["Все"] + prompt_types)
    
    if selected_type != "Все":
        filtered_prompts = [p for p in prompts if p['prompt_type'] == selected_type]
    else:
        filtered_prompts = prompts
    
    # Сортируем по порядку
    filtered_prompts.sort(key=lambda x: x['order_num'])
    
    for i, prompt in enumerate(filtered_prompts):
        with st.expander(f"{prompt['prompt_name']} ({prompt['prompt_type']})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Содержание:**")
                st.code(prompt['prompt_content'])
                
                st.write(f"**Параметры:**")
                params_text = f"Температура: {prompt['temperature']}, "
                params_text += f"Макс. токенов: {prompt['max_tokens']}, "
                params_text += f"Модель: {prompt['model_name']}, "
                params_text += f"Порядок: {prompt['order_num']}"
                st.info(params_text)
            
            with col2:
                status_color = "🟢" if prompt['is_active'] else "🔴"
                st.write(f"{status_color} **Статус:** {'Активен' if prompt['is_active'] else 'Неактивен'}")
                
                st.write(f"**ID:** {prompt['id']}")
                st.write(f"**Создан:** {prompt['created_at']}")
                st.write(f"**Обновлен:** {prompt['updated_at']}")
            
            # Кнопки управления
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✏️ Редактировать", key=f"edit_{prompt['id']}"):
                    st.session_state.editing_prompt = prompt['id']
                    st.rerun()
            
            with col2:
                if st.button("🔄 Переключить статус", key=f"toggle_{prompt['id']}"):
                    try:
                        new_status = not prompt['is_active']
                        update_agent_prompt(
                            prompt['id'],
                            is_active=new_status
                        )
                        st.success("✅ Статус обновлен!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ошибка обновления: {e}")
            
            with col3:
                if st.button("🗑️ Удалить", key=f"delete_{prompt['id']}"):
                    try:
                        delete_agent_prompt(prompt['id'])
                        st.success("✅ Промпт удален!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ошибка удаления: {e}")
            
            # Форма редактирования
            if st.session_state.get('editing_prompt') == prompt['id']:
                st.subheader("✏️ Редактирование промпта")
                
                with st.form(f"edit_form_{prompt['id']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_name = st.text_input("Название", value=prompt['prompt_name'], key=f"edit_name_{prompt['id']}")
                        edit_type = st.selectbox(
                            "Тип",
                            ["task", "system", "context"],
                            index=["task", "system", "context"].index(prompt['prompt_type']),
                            key=f"edit_type_{prompt['id']}"
                        )
                        edit_order = st.number_input("Порядок", min_value=1, value=prompt['order_num'], key=f"edit_order_{prompt['id']}")
                    
                    with col2:
                        edit_temp = st.slider("Температура", 0.0, 2.0, prompt['temperature'], 0.1, key=f"edit_temp_{prompt['id']}")
                        edit_tokens = st.number_input("Макс. токенов", min_value=100, value=prompt['max_tokens'], key=f"edit_tokens_{prompt['id']}")
                        edit_model = st.text_input("Модель", value=prompt['model_name'], key=f"edit_model_{prompt['id']}")
                    
                    edit_content = st.text_area(
                        "Содержание",
                        value=prompt['prompt_content'],
                        height=200,
                        key=f"edit_content_{prompt['id']}"
                    )
                    
                    edit_active = st.checkbox("Активен", value=prompt['is_active'], key=f"edit_active_{prompt['id']}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.form_submit_button("💾 Сохранить"):
                            try:
                                update_agent_prompt(
                                    prompt['id'],
                                    prompt_name=edit_name,
                                    prompt_content=edit_content,
                                    prompt_type=edit_type,
                                    order_num=edit_order,
                                    temperature=edit_temp,
                                    max_tokens=edit_tokens,
                                    model_name=edit_model,
                                    is_active=edit_active
                                )
                                st.success("✅ Промпт обновлен!")
                                del st.session_state.editing_prompt
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Ошибка обновления: {e}")
                    
                    with col2:
                        if st.form_submit_button("❌ Отмена"):
                            del st.session_state.editing_prompt
                            st.rerun()
else:
    st.info("📝 Нет промптов для исследователя")

# Импорт/Экспорт
st.subheader("📤 Импорт/Экспорт")

col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Экспорт промптов"):
        if prompts:
            # Создаем JSON для экспорта
            export_data = {
                "prompts": prompts,
                "export_date": datetime.now().isoformat()
            }
            
            st.download_button(
                label="Скачать JSON",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"researcher_prompts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.warning("Нет промптов для экспорта")

with col2:
    uploaded_file = st.file_uploader("📤 Импорт промптов", type=['json'])
    
    if uploaded_file is not None:
        try:
            import_data = json.load(uploaded_file)
            
            if st.button("📥 Импортировать"):
                imported_count = 0
                
                for prompt_data in import_data.get('prompts', []):
                    try:
                        insert_agent_prompt(
                            agent_type='researcher',
                            prompt_name=prompt_data['prompt_name'],
                            prompt_content=prompt_data['prompt_content'],
                            prompt_type=prompt_data['prompt_type'],
                            order_num=prompt_data['order_num'],
                            temperature=prompt_data['temperature'],
                            max_tokens=prompt_data['max_tokens'],
                            model_name=prompt_data['model_name'],
                            is_active=prompt_data['is_active']
                        )
                        imported_count += 1
                    except Exception as e:
                        st.error(f"Ошибка импорта промпта: {e}")
                
                st.success(f"✅ Импортировано {imported_count} промптов!")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {e}") 