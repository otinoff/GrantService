#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главная страница AI Агентов GrantService
"""

import streamlit as st
import sys
import os
from datetime import datetime

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
    from agents.researcher_agent import ResearcherAgent
    from agents.writer_agent import WriterAgent
    from agents.auditor_agent import AuditorAgent
    from agents.interviewer_agent import InterviewerAgent
    from agents.grant_crew import GrantCrew
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
    page_title="🤖 AI Агенты GrantService",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация сессии
if 'agent_results' not in st.session_state:
    st.session_state.agent_results = {}
if 'current_agent' not in st.session_state:
    st.session_state.current_agent = "researcher"

def main():
    """Главная функция страницы"""
    st.title("🤖 AI Агенты GrantService")
    st.markdown("---")
    
    # Боковое меню для выбора агента
    st.sidebar.title("🎯 Выберите агента")
    
    selected_agent = st.sidebar.selectbox(
        "Агент",
        [
            "📊 Статус LLM",
            "🔍 Researcher Agent",
            "✍️ Writer Agent", 
            "🔍 Auditor Agent",
            "💬 Interviewer Agent",
            "📋 Готовые гранты"
        ],
        index=0
    )
    
    # Общие настройки
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Общие настройки")
    
    default_provider = st.sidebar.selectbox(
        "Провайдер по умолчанию",
        ["auto", "gigachat", "local"],
        help="Auto: автоматический выбор, GigaChat: облачный, Local: локальный"
    )
    
    # Переключение между агентами
    if selected_agent == "📊 Статус LLM":
        st.info("📊 Перейдите на страницу 'Статус LLM' для просмотра статуса провайдеров")
        st.markdown("**Доступные провайдеры:**")
        st.write("- **GigaChat**: Облачный провайдер от Сбера")
        st.write("- **Local**: Локальные модели (Ollama)")
        st.write("- **Auto**: Автоматический выбор лучшего провайдера")
        
    elif selected_agent == "🔍 Researcher Agent":
        st.info("🔍 Перейдите на страницу 'Researcher Agent' для проведения исследований")
        st.markdown("**Функции Researcher Agent:**")
        st.write("- Исследование анкет пользователей")
        st.write("- Анализ рынка и конкурентов")
        st.write("- Поиск грантовых возможностей")
        st.write("- Генерация рекомендаций")
        
    elif selected_agent == "✍️ Writer Agent":
        st.info("✍️ Перейдите на страницу 'Writer Agent' для написания грантов")
        st.markdown("**Функции Writer Agent:**")
        st.write("- Написание грантовых заявок")
        st.write("- Структурирование контента")
        st.write("- Адаптация под требования фондов")
        st.write("- Автоматическое заполнение форм")
        
    elif selected_agent == "🔍 Auditor Agent":
        st.info("🔍 Перейдите на страницу 'Auditor Agent' для проверки заявок")
        st.markdown("**Функции Auditor Agent:**")
        st.write("- Проверка качества заявок")
        st.write("- Анализ соответствия требованиям")
        st.write("- Оценка полноты информации")
        st.write("- Рекомендации по улучшению")
        
    elif selected_agent == "💬 Interviewer Agent":
        st.info("💬 Перейдите на страницу 'Interviewer Agent' для создания вопросов")
        st.markdown("**Функции Interviewer Agent:**")
        st.write("- Создание вопросов для интервью")
        st.write("- Адаптация под профиль пользователя")
        st.write("- Генерация персонализированных вопросов")
        st.write("- Оптимизация процесса сбора данных")
        
    elif selected_agent == "📋 Готовые гранты":
        st.info("📋 Перейдите на страницу 'Готовые гранты' для просмотра созданных грантов")
        st.markdown("**Функции страницы грантов:**")
        st.write("- Просмотр всех созданных грантов")
        st.write("- Фильтрация по статусу и дате")
        st.write("- Экспорт и отправка грантов")
        st.write("- Управление статусами")
    
    # Информация о системе
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ Информация")
    st.sidebar.info("""
    **GrantService AI Agents**
    
    Система автоматической подготовки грантовых заявок с помощью ИИ-агентов.
    
    Каждый агент специализируется на своей области и может работать с разными LLM провайдерами.
    
    **Процесс работы:**
    1. Interviewer → создает вопросы
    2. Researcher → исследует анкеты
    3. Writer → пишет гранты
    4. Auditor → проверяет качество
    """)
    
    # Статистика системы
    st.markdown("---")
    st.subheader("📊 Статистика системы")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Доступно агентов", "5")
    
    with col2:
        st.metric("LLM провайдеров", "3")
    
    with col3:
        st.metric("Статус системы", "🟢 Работает")
    
    with col4:
        if DATABASE_AVAILABLE:
            st.metric("База данных", "🟢 Подключена")
        else:
            st.metric("База данных", "🔴 Ошибка")

if __name__ == "__main__":
    main()
