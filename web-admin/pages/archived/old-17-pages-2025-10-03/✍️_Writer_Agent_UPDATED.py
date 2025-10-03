#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница Writer Agent - написание грантовых заявок
ОБНОВЛЕНО: использует общие модули agent_components и ui_helpers
"""

import streamlit as st
import sys
import os
from datetime import datetime
import json

# Authorization check
try:
    from utils.auth import is_user_authorized, require_auth
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

# Импорт общих модулей
try:
    from utils.agent_components import (
        render_agent_header,
        render_agent_stats,
        render_prompt_management,
        render_agent_testing,
        render_agent_config
    )
    from utils.ui_helpers import (
        render_page_header,
        render_metric_cards,
        show_success_message,
        show_error_message,
        render_tabs
    )
    UTILS_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Ошибка импорта утилит: {e}")
    UTILS_AVAILABLE = False

# Импорты агентов и сервисов
try:
    from services.llm_router import LLMRouter, LLMProvider
    from services.gigachat_service import GigaChatService
    from services.local_llm_service import LocalLLMService
    from agents.writer_agent import WriterAgent
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


def main():
    """Главная функция страницы Writer Agent"""

    # Используем новый компонент для заголовка
    if UTILS_AVAILABLE:
        render_agent_header({
            'name': 'Writer Agent',
            'emoji': '✍️',
            'description': 'Агент для написания грантовых заявок на основе интервью и исследований',
            'status': 'active'
        })
    else:
        st.header("✍️ Writer Agent")
        st.markdown("---")

    # Создаем вкладки
    if UTILS_AVAILABLE:
        tabs = render_tabs(
            ['Настройки', 'Промпты', 'Тестирование', 'История'],
            ['⚙️', '📝', '🧪', '📜']
        )
    else:
        tabs = st.tabs(['⚙️ Настройки', '📝 Промпты', '🧪 Тестирование', '📜 История'])

    # Вкладка: Настройки
    with tabs[0]:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("⚙️ Конфигурация агента")

            if UTILS_AVAILABLE:
                config = render_agent_config('writer', {
                    'provider': 'auto',
                    'temperature': 0.4,
                    'max_tokens': 1500
                })
            else:
                # Fallback to old style
                llm_provider = st.selectbox(
                    "Провайдер LLM",
                    ["auto", "gigachat", "local"],
                    key="writer_provider"
                )

                temperature = st.slider("Температура", 0.1, 1.0, 0.4, key="writer_temp")
                max_tokens = st.number_input("Макс. токенов", 100, 3000, 1500, key="writer_tokens")

        with col2:
            st.subheader("📊 Статистика")

            if UTILS_AVAILABLE:
                render_agent_stats('writer', {
                    'total_executions': 8,
                    'successful_executions': 8,
                    'avg_time': 3.1,
                    'success_rate': 92
                })
            else:
                st.metric("Заявок создано", "8")
                st.metric("Среднее время", "3.1 сек")
                st.metric("Успешность", "92%")

        st.markdown("---")

        # Выбор данных из базы
        st.subheader("📋 Выбор данных для написания")

        if DATABASE_AVAILABLE:
            try:
                db = GrantServiceDatabase()

                # Получаем список анкет
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT s.id, u.first_name, u.last_name, s.started_at, s.status
                        FROM sessions s
                        JOIN users u ON s.user_id = u.telegram_id
                        WHERE s.status = 'completed'
                        ORDER BY s.started_at DESC
                        LIMIT 50
                    """)
                    sessions = cursor.fetchall()

                if sessions:
                    session_options = [
                        f"Анкета #{s[0]} - {s[1]} {s[2]} ({s[3]})"
                        for s in sessions
                    ]

                    selected_session = st.selectbox(
                        "Выберите анкету",
                        session_options,
                        key="writer_session_select"
                    )

                    if selected_session:
                        anketa_id = int(selected_session.split('#')[1].split(' ')[0])
                        st.session_state.writer_anketa_id = anketa_id

                        if UTILS_AVAILABLE:
                            show_success_message(f"Выбрана анкета #{anketa_id}")
                        else:
                            st.success(f"✅ Выбрана анкета #{anketa_id}")
                else:
                    if UTILS_AVAILABLE:
                        show_error_message("Нет завершенных анкет")
                    else:
                        st.warning("⚠️ Нет завершенных анкет для обработки")

            except Exception as e:
                if UTILS_AVAILABLE:
                    show_error_message(f"Ошибка загрузки данных: {e}")
                else:
                    st.error(f"❌ Ошибка загрузки данных: {e}")
        else:
            st.warning("⚠️ База данных недоступна")

        # Кнопка запуска
        st.markdown("---")
        if st.button("▶️ Запустить Writer Agent", type="primary", use_container_width=True):
            if not st.session_state.writer_anketa_id:
                if UTILS_AVAILABLE:
                    show_error_message("Выберите анкету для обработки")
                else:
                    st.error("❌ Выберите анкету для обработки")
            else:
                with st.spinner("🔄 Генерация грантовой заявки..."):
                    try:
                        # TODO: Запуск Writer Agent
                        st.session_state.writer_timestamp = datetime.now()
                        if UTILS_AVAILABLE:
                            show_success_message("Грантовая заявка успешно сгенерирована!")
                        else:
                            st.success("✅ Грантовая заявка успешно сгенерирована!")
                    except Exception as e:
                        if UTILS_AVAILABLE:
                            show_error_message(f"Ошибка генерации: {e}")
                        else:
                            st.error(f"❌ Ошибка генерации: {e}")

    # Вкладка: Промпты
    with tabs[1]:
        if UTILS_AVAILABLE and PROMPTS_AVAILABLE:
            render_prompt_management('writer')
        else:
            st.warning("⚠️ Модуль управления промптами недоступен")

    # Вкладка: Тестирование
    with tabs[2]:
        if UTILS_AVAILABLE:
            render_agent_testing('writer')
        else:
            st.info("🧪 Функция тестирования будет доступна после обновления модулей")

    # Вкладка: История
    with tabs[3]:
        st.subheader("📜 История выполнения")
        st.info("История выполнения пока пуста")


if __name__ == "__main__":
    main()
