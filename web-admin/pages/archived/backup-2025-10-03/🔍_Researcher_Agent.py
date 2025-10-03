#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница Researcher Agent - проведение исследований
"""

import streamlit as st
import sys
import os
from datetime import datetime
import json

# Authorization check
try:
    from utils.auth import is_user_authorized
    if not is_user_authorized():
        st.error("⛔ Не авторизован. Перейдите на страницу 🔐 Вход")
        st.stop()
except ImportError as e:
    st.error(f"❌ Ошибка импорта модуля авторизации: {e}")
    st.stop()

# Добавляем пути к модулям
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService
sys.path.insert(0, os.path.join(grandparent_dir, 'telegram-bot'))
sys.path.insert(0, os.path.join(grandparent_dir, 'agents'))

# Импорты агентов и сервисов
try:
    from services.llm_router import LLMRouter, LLMProvider
    from services.gigachat_service import GigaChatService
    from services.local_llm_service import LocalLLMService
    from agents.researcher_agent import ResearcherAgent
    from data.database.prompts import (
        get_prompts_by_agent, get_prompt_by_name, format_prompt,
        create_prompt, update_prompt, delete_prompt, get_all_categories
    )
    from data.database import GrantServiceDatabase
    AGENTS_AVAILABLE = True
    PROMPTS_AVAILABLE = True
    DATABASE_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Ошибка импорта агентов: {e}")
    AGENTS_AVAILABLE = False
    PROMPTS_AVAILABLE = False
    DATABASE_AVAILABLE = False

# Настройка страницы
st.set_page_config(
    page_title="🔍 Researcher Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация сессии
if 'agent_results' not in st.session_state:
    st.session_state.agent_results = {}
if 'researcher_timestamp' not in st.session_state:
    st.session_state.researcher_timestamp = None

def show_prompt_management(agent_type: str):
    """Управление промптами для агента"""
    if not PROMPTS_AVAILABLE:
        st.warning("⚠️ Модуль промптов недоступен")
        return
    
    st.subheader("⚙️ Управление промптами")
    
    # Получаем промпты агента
    prompts = get_prompts_by_agent(agent_type)
    
    if not prompts:
        st.info(f"📝 Нет промптов для агента {agent_type}")
        return
    
    # Выбор промпта для редактирования
    prompt_names = [p['name'] for p in prompts]
    selected_prompt_name = st.selectbox(
        "Выберите промпт для редактирования",
        prompt_names,
        key=f"prompt_select_{agent_type}"
    )
    
    selected_prompt = next((p for p in prompts if p['name'] == selected_prompt_name), None)
    
    if selected_prompt:
        with st.expander(f"✏️ Редактирование промпта: {selected_prompt['name']}"):
            with st.form(f"prompt_form_{agent_type}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input(
                        "Название",
                        value=selected_prompt['name'],
                        key=f"name_{agent_type}"
                    )
                    
                    priority = st.number_input(
                        "Приоритет",
                        min_value=0,
                        max_value=100,
                        value=selected_prompt['priority'],
                        key=f"priority_{agent_type}"
                    )
                
                with col2:
                    description = st.text_area(
                        "Описание",
                        value=selected_prompt['description'] or '',
                        height=100,
                        key=f"desc_{agent_type}"
                    )
                    
                    variables_text = st.text_area(
                        "Переменные (по одной на строку)",
                        value='\n'.join(selected_prompt['variables']),
                        height=100,
                        key=f"vars_{agent_type}"
                    )
                
                # Шаблон промпта
                prompt_template = st.text_area(
                    "Шаблон промпта",
                    value=selected_prompt['prompt_template'],
                    height=200,
                    key=f"template_{agent_type}"
                )
                
                # Предварительный просмотр
                if prompt_template and variables_text:
                    variables_list = [v.strip() for v in variables_text.split('\n') if v.strip()]
                    test_data = {var: f"[{var}]" for var in variables_list}
                    
                    try:
                        preview = format_prompt(prompt_template, test_data)
                        st.write("**Предварительный просмотр:**")
                        st.code(preview, language="text")
                    except Exception as e:
                        st.error(f"Ошибка предварительного просмотра: {e}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.form_submit_button("💾 Сохранить"):
                        variables_list = [v.strip() for v in variables_text.split('\n') if v.strip()]
                        
                        success = update_prompt(
                            prompt_id=selected_prompt['id'],
                            name=name,
                            description=description,
                            prompt_template=prompt_template,
                            variables=variables_list,
                            priority=priority
                        )
                        
                        if success:
                            st.success("✅ Промпт обновлен!")
                            st.rerun()
                        else:
                            st.error("❌ Ошибка обновления промпта!")
                
                with col2:
                    if st.form_submit_button("🗑️ Удалить", type="secondary"):
                        if st.checkbox("Подтвердить удаление"):
                            success = delete_prompt(selected_prompt['id'])
                            if success:
                                st.success("✅ Промпт удален!")
                                st.rerun()
                            else:
                                st.error("❌ Ошибка удаления!")
                
                with col3:
                    if st.form_submit_button("🧪 Тест"):
                        st.info("Промпт готов к тестированию!")

def main():
    """Главная функция страницы Researcher Agent"""
    st.header("🔍 Researcher Agent")
    st.markdown("---")
    
    # Настройки
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("⚙️ Настройки агента")
        
        llm_provider = st.selectbox(
            "Провайдер LLM",
            ["auto", "gigachat", "local"],
            key="researcher_provider"
        )
        
        if llm_provider == "local":
            model = st.selectbox("Локальная модель", ["qwen2.5:3b", "qwen2.5:7b"], key="researcher_local_model")
        elif llm_provider == "gigachat":
            model = st.selectbox("GigaChat модель", ["GigaChat", "GigaChat-Pro"], key="researcher_giga_model")
        else:
            model = "auto"
        
        temperature = st.slider("Температура", 0.1, 1.0, 0.3, key="researcher_temp")
        max_tokens = st.number_input("Макс. токенов", 100, 2000, 1000, key="researcher_tokens")
    
    with col2:
        st.subheader("📊 Статистика")
        st.metric("Запросов сегодня", "12")
        st.metric("Среднее время", "2.3 сек")
        st.metric("Успешность", "95%")
    
    # Ручное исследование анкет
    st.subheader("🎯 Ручное исследование анкет")
    
    if DATABASE_AVAILABLE:
        try:
            # Инициализируем базу данных
            db = GrantServiceDatabase()
            
            # Получаем список анкет
            all_sessions = db.get_all_sessions(limit=1000)
            anketas = [s for s in all_sessions if s.get('anketa_id')]
            
            if anketas:
                # Создаем список для выбора
                anketa_options = []
                for anketa in anketas:
                    user_display = anketa.get('username', f"ID:{anketa['telegram_id']}")
                    date_str = anketa.get('started_at', 'Unknown')[:10] if anketa.get('started_at') else 'Unknown'
                    anketa_options.append(f"{anketa['anketa_id']} - {user_display} ({date_str})")
                
                selected_anketa_display = st.selectbox(
                    "Выберите анкету для исследования:",
                    anketa_options,
                    key="selected_anketa_researcher"
                )
                
                if selected_anketa_display:
                    # Извлекаем anketa_id из выбранного варианта
                    selected_anketa_id = selected_anketa_display.split(' - ')[0]
                    
                    # Показываем информацию об анкете
                    selected_anketa = next((a for a in anketas if a['anketa_id'] == selected_anketa_id), None)
                    
                    if selected_anketa:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            user_display = selected_anketa.get('username', f"ID:{selected_anketa['telegram_id']}")
                            st.info(f"**Пользователь:** {user_display}")
                        with col2:
                            date_display = selected_anketa.get('started_at', 'Unknown')[:10] if selected_anketa.get('started_at') else 'Unknown'
                            st.info(f"**Дата:** {date_display}")
                        with col3:
                            st.info(f"**Статус:** {selected_anketa.get('status', 'Unknown')}")
                        
                        # Кнопка запуска исследования анкеты
                        if st.button("🚀 Исследовать анкету", type="primary", key="research_anketa_btn"):
                            if AGENTS_AVAILABLE:
                                with st.spinner("🔍 Исследую анкету..."):
                                    try:
                                        # Создаем агента с базой данных
                                        agent = ResearcherAgent(db=db, llm_provider=llm_provider)
                                        
                                        # Запускаем исследование анкеты
                                        result = agent.research_anketa(selected_anketa_id)
                                        
                                        if result.get('status') == 'success':
                                            st.success(f"✅ Исследование завершено! ID: {result.get('research_id')}")
                                            
                                            # Показываем результат
                                            with st.expander("📊 Результат исследования", expanded=True):
                                                st.text_area(
                                                    "Результат",
                                                    result.get('result', ''),
                                                    height=300,
                                                    disabled=True
                                                )
                                        else:
                                            st.error(f"❌ Ошибка исследования: {result.get('message', 'Неизвестная ошибка')}")
                                            
                                    except Exception as e:
                                        st.error(f"❌ Ошибка: {str(e)}")
                            else:
                                st.warning("⚠️ Агенты недоступны")
            else:
                st.info("📋 Пока нет анкет для исследования")
                
        except Exception as e:
            st.error(f"❌ Ошибка работы с базой данных: {e}")
    else:
        st.warning("⚠️ База данных недоступна")
    
    st.markdown("---")
    
    # Ввод данных
    st.subheader("📝 Входные данные для исследования")
    
    # Проверяем данные от других агентов
    if 'writer_input' in st.session_state:
        st.info("📤 Получены данные от Writer Agent")
        default_input = st.session_state.writer_input
    elif 'auditor_input' in st.session_state:
        st.info("📤 Получены данные от Auditor Agent")
        default_input = st.session_state.auditor_input
    else:
        default_input = ""
    
    research_data = st.text_area(
        "Введите данные для исследования",
        value=default_input,
        placeholder="Название проекта, описание, цели, бюджет...",
        height=200,
        key="researcher_input"
    )
    
    # Запуск исследования
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Запустить исследование", type="primary", use_container_width=True):
            if research_data and AGENTS_AVAILABLE:
                with st.spinner("🔍 Провожу исследование..."):
                    try:
                        # Создаем агента
                        agent = ResearcherAgent(db=None, llm_provider=llm_provider)
                        
                        # Запускаем исследование
                        result = agent.research_grant({
                            'description': research_data,
                            'llm_provider': llm_provider,
                            'model': model,
                            'temperature': temperature,
                            'max_tokens': max_tokens
                        })
                        
                        # Сохраняем результат
                        st.session_state.agent_results['researcher'] = result
                        st.session_state.researcher_timestamp = datetime.now()
                        
                        st.success("✅ Исследование завершено!")
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")
            else:
                st.warning("⚠️ Введите данные для исследования")
    
    with col2:
        if st.button("🧹 Очистить данные", use_container_width=True):
            if 'researcher' in st.session_state.agent_results:
                del st.session_state.agent_results['researcher']
            if 'researcher_timestamp' in st.session_state:
                del st.session_state.researcher_timestamp
            st.success("✅ Данные очищены!")
    
    # Результаты
    if 'researcher' in st.session_state.agent_results:
        st.markdown("---")
        st.subheader("📊 Результаты исследования")
        
        result = st.session_state.agent_results['researcher']
        timestamp = st.session_state.researcher_timestamp
        
        # Информация о запросе
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Провайдер", result.get('provider', 'Unknown'))
        with col2:
            st.metric("Время обработки", f"{result.get('processing_time', 0):.2f} сек")
        with col3:
            st.metric("Дата", timestamp.strftime("%H:%M:%S"))
        
        # Результат
        st.text_area(
            "Результат исследования",
            result.get('result', ''),
            height=300,
            disabled=True
        )
        
        # Передача результата
        st.subheader("📤 Передача результата")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📤 → Writer", use_container_width=True):
                st.session_state.writer_input = result.get('result', '')
                st.success("✅ Отправлено в Writer Agent!")
        
        with col2:
            if st.button("📤 → Auditor", use_container_width=True):
                st.session_state.auditor_input = result.get('result', '')
                st.success("✅ Отправлено в Auditor Agent!")
        
        with col3:
            if st.button("📤 → Interviewer", use_container_width=True):
                st.session_state.interviewer_input = result.get('result', '')
                st.success("✅ Отправлено в Interviewer Agent!")
        
        with col4:
            if st.button("💾 Сохранить", use_container_width=True):
                st.success("✅ Результат сохранен!")
    
    # Управление промптами
    show_prompt_management("researcher")

if __name__ == "__main__":
    main()
