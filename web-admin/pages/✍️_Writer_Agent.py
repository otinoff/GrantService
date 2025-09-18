#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница Writer Agent - написание грантовых заявок
"""

import streamlit as st
import sys
import os
from datetime import datetime
import json

import streamlit as st
import sys
import os

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

# Проверка авторизации
from web_admin.utils.auth import is_user_authorized

if not is_user_authorized():
    # Импортируем страницу входа
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "login_page", 
        "/var/GrantService/web-admin/pages/🔐_Вход.py"
    )
    login_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(login_module)
    login_module.show_login_page()
    st.stop()
# Добавляем пути к модулям
sys.path.append('/var/GrantService/telegram-bot')
sys.path.append('/var/GrantService/data')
sys.path.append('/var/GrantService')

# Импорты агентов и сервисов
try:
    from services.llm_router import LLMRouter, LLMProvider
    from services.gigachat_service import GigaChatService
    from services.local_llm_service import LocalLLMService
    # Импорт агентов из общей папки
    sys.path.append('/var/GrantService/agents')
    from agents.writer_agent import WriterAgent
    from database.prompts import (
        get_prompts_by_agent, get_prompt_by_name, format_prompt,
        create_prompt, update_prompt, delete_prompt, get_all_categories
    )
    # Импорт базы данных для работы с анкетами
    from data.database.models import GrantServiceDatabase
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
    page_title="✍️ Writer Agent",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация сессии
if 'agent_results' not in st.session_state:
    st.session_state.agent_results = {}
if 'writer_timestamp' not in st.session_state:
    st.session_state.writer_timestamp = None
if 'writer_anketa_id' not in st.session_state:
    st.session_state.writer_anketa_id = None
if 'writer_research_id' not in st.session_state:
    st.session_state.writer_research_id = None

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
    """Главная функция страницы Writer Agent"""
    st.header("✍️ Writer Agent")
    st.markdown("---")
    
    # Настройки
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("⚙️ Настройки агента")
        
        llm_provider = st.selectbox(
            "Провайдер LLM",
            ["auto", "gigachat", "local"],
            key="writer_provider"
        )
        
        if llm_provider == "local":
            model = st.selectbox("Локальная модель", ["qwen2.5:3b", "qwen2.5:7b"], key="writer_local_model")
        elif llm_provider == "gigachat":
            model = st.selectbox("GigaChat модель", ["GigaChat", "GigaChat-Pro"], key="writer_giga_model")
        else:
            model = "auto"
        
        temperature = st.slider("Температура", 0.1, 1.0, 0.4, key="writer_temp")
        max_tokens = st.number_input("Макс. токенов", 100, 3000, 1500, key="writer_tokens")
    
    with col2:
        st.subheader("📊 Статистика")
        st.metric("Заявок создано", "8")
        st.metric("Среднее время", "3.1 сек")
        st.metric("Успешность", "92%")
    
    # Выбор данных из базы
    st.subheader("📋 Выбор данных для написания")
    
    if DATABASE_AVAILABLE:
        try:
            # Инициализируем базу данных
            db_instance = GrantServiceDatabase()
            
            # Получаем список анкет с исследованиями
            all_sessions = db_instance.get_all_sessions(limit=1000)
            anketas_with_research = []
            
            for session in all_sessions:
                if session.get('anketa_id'):
                    # Проверяем есть ли исследования для этой анкеты
                    research_list = db_instance.get_research_by_anketa_id(session['anketa_id'])
                    if research_list:
                        anketas_with_research.append({
                            'session': session,
                            'research': research_list[0]  # Берем первое исследование
                        })
            
            if anketas_with_research:
                # Создаем список для выбора
                anketa_options = []
                for item in anketas_with_research:
                    session = item['session']
                    research = item['research']
                    user_display = session.get('username', f"ID:{session['telegram_id']}")
                    date_str = session.get('started_at', 'Unknown')[:10] if session.get('started_at') else 'Unknown'
                    status = research.get('status', 'unknown')
                    anketa_options.append(f"{session['anketa_id']} - {user_display} ({date_str}) [{status}]")
                
                selected_anketa_display = st.selectbox(
                    "Выберите анкету с исследованием:",
                    ["--- Выберите анкету ---"] + anketa_options,
                    key="selected_anketa_writer"
                )
                
                if selected_anketa_display and selected_anketa_display != "--- Выберите анкету ---":
                    # Извлекаем anketa_id из выбранного варианта
                    selected_anketa_id = selected_anketa_display.split(' - ')[0]
                    
                    # Находим выбранные данные
                    selected_data = next((item for item in anketas_with_research 
                                        if item['session']['anketa_id'] == selected_anketa_id), None)
                    
                    if selected_data:
                        session = selected_data['session']
                        research = selected_data['research']
                        
                        # Показываем информацию о выбранных данных
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            user_display = session.get('username', f"ID:{session['telegram_id']}")
                            st.info(f"**👤 Пользователь:** {user_display}")
                        with col2:
                            st.info(f"**📋 Анкета:** {session['anketa_id']}")
                        with col3:
                            st.info(f"**🔬 Исследование:** {research['research_id']}")
                        
                        # Кнопка написания гранта
                        if st.button("✍️ Написать грант", type="primary", key="write_grant_btn"):
                            if AGENTS_AVAILABLE:
                                with st.spinner("✍️ Пишу грант на основе выбранных данных..."):
                                    try:
                                        # Формируем данные для писателя
                                        combined_data = f"""📋 АНКЕТА: {session['anketa_id']}
👤 Пользователь: @{session.get('username', 'N/A')} ({session.get('first_name', '')} {session.get('last_name', '')})
📅 Дата создания: {session.get('started_at', 'Unknown')[:10]}

🔬 ИССЛЕДОВАНИЕ: {research['research_id']}
🤖 Провайдер: {research['llm_provider']}
📊 Статус: {research['status']}
⏰ Завершено: {research.get('completed_at', 'N/A')}

📝 ДАННЫЕ АНКЕТЫ:
{json.dumps(session.get('interview_data', {}), ensure_ascii=False, indent=2)}

🔍 РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ:
{research.get('research_results', 'Нет данных')}

📋 ЛОГИ ПРОЦЕССА:
{research.get('logs', 'Нет логов')}
"""
                                        
                                        # Создаем агента с базой данных
                                        db = GrantServiceDatabase()
                                        agent = WriterAgent(db=db, llm_provider=llm_provider)
                                        
                                        # Запускаем написание гранта
                                        result = agent.write_application({
                                            'research_data': combined_data,
                                            'llm_provider': llm_provider,
                                            'model': model,
                                            'temperature': temperature,
                                            'max_tokens': max_tokens,
                                            'anketa_id': session['anketa_id'],
                                            'research_id': research['research_id']
                                        })
                                        
                                        # Сохраняем результат
                                        st.session_state.agent_results['writer'] = result
                                        st.session_state.writer_timestamp = datetime.now()
                                        st.session_state.writer_anketa_id = session['anketa_id']
                                        st.session_state.writer_research_id = research['research_id']
                                        
                                        st.success("✅ Грант написан!")
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"❌ Ошибка: {str(e)}")
                            else:
                                st.warning("⚠️ Агенты недоступны")
                        
                        # Превью данных
                        with st.expander("👁️ Превью данных", expanded=False):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**📋 Данные анкеты:**")
                                if session.get('interview_data'):
                                    st.json(session['interview_data'])
                                else:
                                    st.write("Нет данных")
                            
                            with col2:
                                st.write("**🔍 Результаты исследования:**")
                                st.text_area(
                                    "Содержание",
                                    research.get('research_results', 'Нет данных'),
                                    height=200,
                                    disabled=True
                                )
            else:
                st.info("📋 Пока нет анкет с завершенными исследованиями")
                
        except Exception as e:
            st.error(f"❌ Ошибка работы с базой данных: {e}")
    else:
        st.warning("⚠️ База данных недоступна")
    
    st.markdown("---")
    
    # Результаты написания гранта
    if 'writer' in st.session_state.agent_results:
        st.subheader("📄 Созданный грант")
        
        result = st.session_state.agent_results['writer']
        timestamp = st.session_state.writer_timestamp
        
        # Информация о созданном гранте
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Провайдер", result.get('provider', result.get('provider_used', 'Unknown')))
        with col2:
            st.metric("Время обработки", f"{result.get('processing_time', 0):.2f} сек")
        with col3:
            st.metric("Дата создания", timestamp.strftime("%H:%M:%S"))
        with col4:
            if 'application_number' in result:
                st.metric("Номер заявки", result['application_number'])
                st.success("✅ Грант сохранен в БД!")
            else:
                st.metric("Статус", "Создан")
        
        # Показываем созданный грант
        application = result.get('application', {})
        if application:
            st.subheader("📋 Содержание гранта")
            
            # Показываем каждый раздел гранта
            for section_key, section_content in application.items():
                section_name = {
                    'title': '📝 Название проекта',
                    'summary': '📋 Краткое описание',
                    'problem': '❗ Проблема',
                    'solution': '💡 Решение',
                    'implementation': '🛠️ План реализации',
                    'budget': '💰 Бюджет',
                    'timeline': '⏰ Временные рамки',
                    'team': '👥 Команда',
                    'impact': '🎯 Ожидаемый результат',
                    'sustainability': '♻️ Устойчивость'
                }.get(section_key, section_key.title())
                
                with st.expander(section_name, expanded=False):
                    st.write(section_content)
        else:
            st.text_area(
                "Созданный грант",
                result.get('result', 'Содержание гранта не найдено'),
                height=400,
                disabled=True
            )
        
        # Действия с созданным грантом
        st.subheader("📤 Действия с грантом")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📤 → Auditor", use_container_width=True):
                st.session_state.auditor_input = result.get('result', '')
                st.success("✅ Отправлено в Auditor Agent!")
        
        with col2:
            if st.button("📤 → Researcher", use_container_width=True):
                st.session_state.researcher_input = result.get('result', '')
                st.success("✅ Отправлено в Researcher Agent!")
        
        with col3:
            if st.button("💾 Сохранить", use_container_width=True):
                st.success("✅ Грант сохранен!")
        
        with col4:
            if st.button("🧹 Очистить", use_container_width=True):
                if 'writer' in st.session_state.agent_results:
                    del st.session_state.agent_results['writer']
                if 'writer_timestamp' in st.session_state:
                    del st.session_state.writer_timestamp
                if 'writer_anketa_id' in st.session_state:
                    del st.session_state.writer_anketa_id
                if 'writer_research_id' in st.session_state:
                    del st.session_state.writer_research_id
                st.success("✅ Данные очищены!")
                st.rerun()
    
    # Управление промптами
    show_prompt_management("writer")

if __name__ == "__main__":
    main()
