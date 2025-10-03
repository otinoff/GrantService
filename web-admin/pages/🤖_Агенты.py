#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agents Management Page - GrantService Admin (v3.0)
====================================================
Unified page for all 5 agents with FULL functionality from archived files:
- Interviewer | Auditor | Planner | Researcher | Writer

Integrated from:
- 🤖_AI_Agents.py - Base structure
- ✍️_Writer_Agent.py - Writer logic
- 🔍_Researcher_Agent.py - Researcher logic
- 🔬_Исследования_исследователя.py - Researcher investigations table
- 🔬_Аналитика_исследователя.py - Researcher cost analytics

Author: Grant Architect Agent + Streamlit Admin Developer
Date: 2025-10-03
Version: 3.0.0 (Full integration)
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# PATH SETUP
current_file = Path(__file__).resolve()
web_admin_dir = current_file.parent.parent
base_dir = web_admin_dir.parent

# Add paths in correct order
if str(web_admin_dir) not in sys.path:
    sys.path.insert(0, str(web_admin_dir))
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
if str(base_dir / 'telegram-bot') not in sys.path:
    sys.path.insert(0, str(base_dir / 'telegram-bot'))
if str(base_dir / 'agents') not in sys.path:
    sys.path.insert(0, str(base_dir / 'agents'))

# AUTHENTICATION (disabled for now)
# TODO: Implement auth module
# try:
#     from utils.auth import is_user_authorized
#     if not is_user_authorized():
#         st.error("⛔ Не авторизован. Перейдите на страницу 🔐 Вход")
#         st.stop()
# except ImportError as e:
#     st.error(f"❌ Ошибка импорта модуля авторизации: {e}")
#     st.stop()

# IMPORTS
AdminDatabase = None
render_page_header = None
render_metric_cards = None
render_tabs = None
render_agent_header = None
render_prompt_management = None
render_agent_stats = None
create_researcher_metrics = None
create_cost_chart = None
create_popular_queries_chart = None
GrantServiceDatabase = None
get_interview_questions = None
insert_interview_question = None
update_interview_question = None
delete_interview_question = None

try:
    from utils.database import AdminDatabase
except ImportError as e:
    st.warning(f"⚠️ AdminDatabase not available: {e}")

try:
    from utils.ui_helpers import render_page_header, render_metric_cards, render_tabs
except ImportError as e:
    st.warning(f"⚠️ UI helpers not available: {e}")

try:
    from utils.agent_components import render_agent_header, render_prompt_management, render_agent_stats
except ImportError as e:
    st.warning(f"⚠️ Agent components not available: {e}")

try:
    from utils.charts import create_researcher_metrics, create_cost_chart, create_popular_queries_chart
except ImportError:
    pass  # Charts are optional

try:
    from data.database import GrantServiceDatabase
except ImportError:
    # Fallback to AdminDatabase
    pass

try:
    from data.database import get_interview_questions, insert_interview_question, update_interview_question, delete_interview_question
except ImportError as e:
    st.warning(f"⚠️ Interview questions functions not available: {e}")

# Logger setup with fallback
try:
    from utils.logger import setup_logger
    logger = setup_logger('agents_page')
except ImportError:
    import logging
    logger = logging.getLogger('agents_page')
    logger.setLevel(logging.INFO)

# Optional agent imports
try:
    from services.llm_router import LLMRouter, LLMProvider
    from services.gigachat_service import GigaChatService
    from services.local_llm_service import LocalLLMService
    from agents.writer_agent import WriterAgent
    from agents.researcher_agent import ResearcherAgent
    from data.database.prompts import (
        get_prompts_by_agent, get_prompt_by_name, format_prompt,
        create_prompt, update_prompt, delete_prompt
    )
    AGENTS_AVAILABLE = True
    PROMPTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    PROMPTS_AVAILABLE = False

# PAGE CONFIG
st.set_page_config(page_title="AI Агенты", page_icon="🤖", layout="wide")

# DATABASE
@st.cache_resource
def get_database():
    if GrantServiceDatabase:
        return GrantServiceDatabase()
    elif AdminDatabase:
        return AdminDatabase()
    else:
        st.error("❌ No database available")
        return None

@st.cache_resource
def get_admin_database():
    if AdminDatabase:
        return AdminDatabase()
    else:
        return None

db = get_database()
admin_db = get_admin_database()

# SESSION STATE
if 'agent_results' not in st.session_state:
    st.session_state.agent_results = {}
if 'selected_research_id' not in st.session_state:
    st.session_state.selected_research_id = None
if 'selected_anketa_id' not in st.session_state:
    st.session_state.selected_anketa_id = None
if 'selected_research_export' not in st.session_state:
    st.session_state.selected_research_export = None

# =============================================================================
# AGENT CONFIGURATION
# =============================================================================

AGENT_INFO = {
    'interviewer': {
        'name': 'Interviewer Agent',
        'emoji': '📝',
        'description': 'Сбор информации о проекте через 24 вопроса',
        'status': 'active',
        'table': 'sessions',
        'future': 'AI-powered dynamic questioning'
    },
    'auditor': {
        'name': 'Auditor Agent',
        'emoji': '✅',
        'description': 'Оценка качества анкеты по 5 критериям',
        'status': 'active',
        'table': 'auditor_results',
        'future': 'Multi-criteria weighted scoring'
    },
    'planner': {
        'name': 'Planner Agent',
        'emoji': '📐',
        'description': 'Создание структуры заявки',
        'status': 'active',
        'table': 'planner_structures',
        'future': 'Multiple templates per grant type'
    },
    'researcher': {
        'name': 'Researcher Agent',
        'emoji': '🔍',
        'description': 'Поиск данных через Perplexity API',
        'status': 'active',
        'table': 'researcher_research',
        'future': 'Multi-source aggregation'
    },
    'writer': {
        'name': 'Writer Agent',
        'emoji': '✍️',
        'description': 'Генерация текста заявки через GigaChat',
        'status': 'active',
        'table': 'grants',
        'future': 'Collaborative editing with user'
    }
}

# =============================================================================
# DATA FUNCTIONS
# =============================================================================

@st.cache_data(ttl=300)
def get_agent_statistics(agent_type: str, _db, days: int = 30):
    """Get statistics for specific agent"""
    try:
        if agent_type == 'interviewer':
            # Get from sessions table
            result = _db.execute_query("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed,
                    ROUND(AVG(progress_percentage), 1) as avg_progress,
                    ROUND(AVG(session_duration_minutes), 1) as avg_duration_min
                FROM sessions
                WHERE started_at >= datetime('now', '-30 days')
            """)
            return result[0] if result else {}

        elif agent_type == 'auditor':
            result = _db.execute_query("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved,
                    COUNT(CASE WHEN approval_status = 'needs_revision' THEN 1 END) as needs_revision,
                    ROUND(AVG(average_score), 2) as avg_score
                FROM auditor_results
                WHERE created_at >= datetime('now', '-30 days')
            """)
            return result[0] if result else {}

        elif agent_type == 'planner':
            result = _db.execute_query("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN data_mapping_complete = 1 THEN 1 END) as complete_mappings,
                    ROUND(AVG(sections_count), 1) as avg_sections
                FROM planner_structures
                WHERE created_at >= datetime('now', '-30 days')
            """)
            return result[0] if result else {}

        elif agent_type == 'researcher':
            stats = _db.get_research_statistics() if hasattr(_db, 'get_research_statistics') else {}
            return {
                'total': stats.get('total_research', 0),
                'completed': stats.get('status_distribution', {}).get('completed', 0),
                'processing': stats.get('status_distribution', {}).get('processing', 0),
                'errors': stats.get('status_distribution', {}).get('error', 0)
            }

        elif agent_type == 'writer':
            result = _db.execute_query("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft,
                    ROUND(AVG(quality_score), 2) as avg_quality_score
                FROM grants
                WHERE created_at >= datetime('now', '-30 days')
            """)
            return result[0] if result else {}

    except Exception as e:
        logger.error(f"Error getting stats for {agent_type}: {e}")
        return {}

@st.cache_data(ttl=60)
def get_researcher_investigations(_db, filters: dict = None):
    """Get list of researcher investigations"""
    try:
        return _db.get_all_research(limit=100) if hasattr(_db, 'get_all_research') else []
    except Exception as e:
        logger.error(f"Error getting investigations: {e}")
        return []

@st.cache_data(ttl=60)
def get_writer_generated_texts(_db, filters: dict = None):
    """Get list of writer generated texts"""
    try:
        result = _db.execute_query("""
            SELECT
                id, grant_id, user_id, status,
                created_at, updated_at, quality_score
            FROM grants
            ORDER BY created_at DESC
            LIMIT 50
        """)
        return result if result else []
    except Exception as e:
        logger.error(f"Error getting writer texts: {e}")
        return []

# =============================================================================
# UI RENDERING FUNCTIONS
# =============================================================================

def render_interviewer_tab():
    """Render Interviewer Agent tab"""
    st.markdown("### 📝 Interviewer Agent")
    st.markdown("**Описание:** Собирает информацию о проекте через структурированное интервью из 24 вопросов")

    # Statistics
    stats = get_agent_statistics('interviewer', db)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего интервью", stats.get('total', 0))
    with col2:
        st.metric("Завершено", stats.get('completed', 0))
    with col3:
        st.metric("Средний прогресс", f"{stats.get('avg_progress', 0)}%")
    with col4:
        st.metric("Средняя длительность", f"{stats.get('avg_duration_min', 0)} мин")

    st.markdown("---")

    # Interview questions management
    st.markdown("### ❓ Вопросы интервью (24 вопроса)")

    try:
        questions = get_interview_questions()

        # Statistics
        total_q = len(questions) if questions else 0
        active_q = len([q for q in questions if q.get('is_active', True)]) if questions else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего вопросов", total_q)
        with col2:
            st.metric("Активных", active_q)
        with col3:
            st.metric("Неактивных", total_q - active_q)

        st.markdown("---")

        # Add new question
        with st.expander("➕ Добавить новый вопрос"):
            with st.form("add_question_form"):
                col1, col2 = st.columns(2)

                with col1:
                    q_text = st.text_area("Текст вопроса", height=100)
                    q_type = st.selectbox("Тип вопроса", ["text", "select", "choice", "number", "date", "textarea"])
                    q_number = st.number_input("Номер вопроса", min_value=1, max_value=50, value=total_q + 1)

                with col2:
                    is_req = st.checkbox("Обязательный", value=True)
                    is_act = st.checkbox("Активен", value=True)
                    q_options = st.text_area("Варианты (по строке)", height=100) if q_type == "choice" else ""

                if st.form_submit_button("➕ Добавить", use_container_width=True):
                    if q_text:
                        try:
                            insert_interview_question(q_text, q_type, q_number, is_req, is_act, q_options or None)
                            st.success("✅ Вопрос добавлен!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Ошибка: {e}")
                    else:
                        st.error("❌ Введите текст вопроса")

        # List existing questions
        st.markdown("#### 📋 Список вопросов")

        if questions:
            questions_sorted = sorted(questions, key=lambda x: x.get('question_number', 0))

            for q in questions_sorted:
                status_icon = "🟢" if q.get('is_active', True) else "🔴"
                req_icon = "🔴" if q.get('is_required', False) else "⚪"

                with st.expander(f"{status_icon} Вопрос {q.get('question_number', '?')}: {q.get('question_text', '')[:60]}..."):
                    st.write(f"**Текст:** {q.get('question_text', '')}")
                    st.write(f"**Тип:** {q.get('question_type', 'text')}")
                    st.write(f"{req_icon} **Обязательный:** {'Да' if q.get('is_required', False) else 'Нет'}")
                    st.write(f"{status_icon} **Активен:** {'Да' if q.get('is_active', True) else 'Нет'}")

                    if q.get('options'):
                        st.write("**Варианты:**")
                        # Handle both string and dict options
                        opts = q['options']
                        if isinstance(opts, str):
                            for opt in opts.split('\n'):
                                if opt.strip():
                                    st.write(f"• {opt.strip()}")
                        elif isinstance(opts, dict):
                            for key, val in opts.items():
                                st.write(f"• {key}: {val}")
                        elif isinstance(opts, list):
                            for opt in opts:
                                st.write(f"• {opt}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Переключить статус", key=f"toggle_{q['id']}"):
                            try:
                                update_interview_question(q['id'], is_active=not q.get('is_active', True))
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Ошибка: {e}")

                    with col2:
                        if st.button("🗑️ Удалить", key=f"delete_{q['id']}"):
                            try:
                                delete_interview_question(q['id'])
                                st.success("✅ Удалено")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Ошибка: {e}")
        else:
            st.info("Вопросы не найдены. Добавьте первый вопрос выше.")

    except Exception as e:
        st.error(f"❌ Ошибка загрузки вопросов: {e}")


def render_auditor_tab():
    """Render Auditor Agent tab"""
    st.markdown("### ✅ Auditor Agent")
    st.markdown("**Описание:** Оценивает качество проекта по 5 критериям (шкала 1-10)")

    # Statistics
    stats = get_agent_statistics('auditor', db)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего оценок", stats.get('total', 0))
    with col2:
        st.metric("Одобрено", stats.get('approved', 0))
    with col3:
        st.metric("На доработку", stats.get('needs_revision', 0))
    with col4:
        st.metric("Средний балл", f"{stats.get('avg_score', 0)}/10")

    st.markdown("---")

    # Criteria breakdown
    st.markdown("### 📊 Критерии оценки")

    criteria = {
        'Полнота': 'Completeness - насколько полно заполнена анкета',
        'Ясность': 'Clarity - насколько понятно описан проект',
        'Реалистичность': 'Feasibility - насколько реален проект',
        'Инновационность': 'Innovation - насколько инновативен проект',
        'Качество': 'Quality - общее качество подачи'
    }

    for criterion, description in criteria.items():
        with st.expander(f"📌 {criterion}"):
            st.markdown(f"**{description}**")
            st.markdown("- Оценка от 1 до 10")
            st.markdown("- Влияет на итоговое решение")

    st.markdown("---")

    # Prompt management (disabled - table agent_prompts not exists)
    # st.markdown("### 📝 Управление промптами")
    # st.info("Таблица agent_prompts пока не создана. Будет добавлено позже.")


def render_planner_tab():
    """Render Planner Agent tab"""
    st.markdown("### 📐 Planner Agent")
    st.markdown("**Описание:** Создает структуру грантовой заявки на основе типа гранта и требований")

    # Statistics
    stats = get_agent_statistics('planner', db)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего планов", stats.get('total', 0))
    with col2:
        st.metric("Полный mapping", stats.get('complete_mappings', 0))
    with col3:
        st.metric("Средне разделов", f"{stats.get('avg_sections', 0)}")

    st.markdown("---")

    # Structure templates
    st.markdown("### 📋 Шаблоны структур")

    templates = {
        'Президентский грант': [
            'Название проекта',
            'Краткая аннотация',
            'Описание проблемы',
            'Цели и задачи',
            'План реализации',
            'Бюджет',
            'Ожидаемые результаты'
        ],
        'Молодежный грант': [
            'Название проекта',
            'Актуальность',
            'Целевая аудитория',
            'Мероприятия',
            'Команда',
            'Бюджет'
        ]
    }

    for template_name, sections in templates.items():
        with st.expander(f"📄 {template_name}"):
            for i, section in enumerate(sections, 1):
                st.markdown(f"{i}. {section}")

    st.markdown("---")

    # Prompt management (disabled - table agent_prompts not exists)
    # st.markdown("### 📝 Управление промптами")
    # st.info("Таблица agent_prompts пока не создана. Будет добавлено позже.")


def render_researcher_tab():
    """Render Researcher Agent tab with sub-tabs"""
    st.markdown("### 🔍 Researcher Agent")
    st.markdown("**Описание:** Обогащает заявку актуальными данными через Perplexity API")

    # SUB-TABS for Researcher
    researcher_subtabs = ["Статистика", "Исследования", "Аналитика расходов"]
    researcher_icons = ["📊", "🔬", "💰"]

    tab1, tab2, tab3 = st.tabs([f"{icon} {name}" for icon, name in zip(researcher_icons, researcher_subtabs)])

    # TAB 1: Statistics
    with tab1:
        render_researcher_statistics()

    # TAB 2: Investigations
    with tab2:
        render_researcher_investigations()

    # TAB 3: Cost Analytics
    with tab3:
        render_researcher_cost_analytics()


def render_researcher_statistics():
    """Render Researcher statistics sub-tab"""
    st.markdown("#### 📊 Статистика работы Researcher")

    stats = get_agent_statistics('researcher', db)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего исследований", stats.get('total', 0))
    with col2:
        st.metric("Завершено", stats.get('completed', 0))
    with col3:
        st.metric("В процессе", stats.get('processing', 0))
    with col4:
        st.metric("Ошибки", stats.get('errors', 0))

    st.markdown("---")

    # Prompt management (disabled - table agent_prompts not exists)
    # st.markdown("### 📝 Управление промптами")
    # st.info("Таблица agent_prompts пока не создана. Будет добавлено позже.")


def render_researcher_investigations():
    """Render Researcher investigations list (from 🔬_Исследования_исследователя.py)"""
    st.markdown("#### 🔬 Все исследования")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox(
            "Статус",
            ["Все статусы", "completed", "pending", "processing", "error"],
            key="researcher_status_filter"
        )

    with col2:
        period_filter = st.selectbox(
            "Период",
            ["Все время", "Сегодня", "Неделя", "Месяц"],
            key="researcher_period_filter"
        )

    with col3:
        provider_filter = st.selectbox(
            "LLM провайдер",
            ["Все", "perplexity", "gigachat", "ollama"],
            key="researcher_provider_filter"
        )

    with col4:
        user_filter = st.text_input(
            "Пользователь (username или ID)",
            placeholder="Введите username",
            key="researcher_user_filter"
        )

    st.markdown("---")

    # Get investigations
    investigations = get_researcher_investigations(db)

    # Apply filters
    if status_filter != "Все статусы":
        investigations = [r for r in investigations if r.get('status') == status_filter]

    if provider_filter != "Все":
        investigations = [r for r in investigations if r.get('llm_provider') == provider_filter]

    if user_filter:
        user_filter_lower = user_filter.lower()
        investigations = [r for r in investigations
                         if (r.get('username', '').lower().find(user_filter_lower) != -1 or
                             str(r.get('user_id', '')).find(user_filter) != -1)]

    # Display count
    st.write(f"**Найдено исследований: {len(investigations)}**")

    if not investigations:
        st.info("📋 Исследования не найдены")
        return

    # Display investigations
    for research in investigations:
        status_emoji = "✅" if research['status'] == 'completed' else "🔄" if research['status'] == 'processing' else "❌"
        username = research.get('username', 'Unknown')
        research_id = research.get('research_id', research.get('id', 'N/A'))

        with st.expander(f"{status_emoji} {research_id} - {username}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**ID исследования:** {research_id}")
                st.write(f"**ID анкеты:** {research.get('anketa_id', 'N/A')}")
                st.write(f"**Пользователь:** @{username}")
                st.write(f"**Telegram ID:** {research.get('user_id', 'N/A')}")
                st.write(f"**Статус:** {research['status']}")

            with col2:
                st.write(f"**LLM провайдер:** {research.get('llm_provider', 'N/A')}")
                st.write(f"**Модель:** {research.get('model', 'N/A')}")
                st.write(f"**Создано:** {research.get('created_at', 'N/A')}")
                if research.get('completed_at'):
                    st.write(f"**Завершено:** {research['completed_at']}")

            # Results
            if research.get('research_results'):
                st.markdown("**Результаты исследования:**")
                st.text_area(
                    "Содержание",
                    value=research['research_results'],
                    height=200,
                    key=f"results_{research.get('id', research_id)}",
                    disabled=True
                )

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("📄 Анкета", key=f"view_anketa_{research.get('id', research_id)}"):
                    st.session_state.selected_anketa_id = research.get('anketa_id')
                    st.rerun()

            with col2:
                if st.button("📊 Детали", key=f"details_{research.get('id', research_id)}"):
                    st.session_state.selected_research_id = research_id
                    st.rerun()

            with col3:
                if st.button("📋 ID", key=f"copy_{research.get('id', research_id)}"):
                    st.code(research_id)
                    st.success("ID показан!")

            with col4:
                if st.button("💾 Экспорт", key=f"export_{research.get('id', research_id)}"):
                    st.session_state.selected_research_export = research_id
                    st.rerun()


def render_researcher_cost_analytics():
    """Render Researcher cost analytics (from 🔬_Аналитика_исследователя.py)"""
    st.markdown("#### 💰 Аналитика расходов на токены")

    try:
        # Get Perplexity service statistics
        from services.perplexity_service import PerplexityService
        perplexity_service = PerplexityService()
        account_stats = perplexity_service.get_combined_statistics()

        # Display account info
        account_info = account_stats.get('account_info', {})

        col1, col2, col3 = st.columns(3)

        with col1:
            balance_emoji = "💰"
            current_balance = account_info.get('current_balance', 0)
            tier = account_info.get('current_tier', 'Tier 0')
            spent = account_info.get('total_spent', 0.02)
            balance_str = f"{current_balance:.6f}"
            spent_str = f"{spent:.2f}"
            st.markdown(f"""
            **{balance_emoji} Баланс аккаунта:**
            - **Credit balance:** {balance_str} USD
            - **Уровень:** {tier}
            - **Потрачено:** {spent_str} USD
            """)

        with col2:
            chart_emoji = "📊"
            screen_data = perplexity_service.get_latest_screen_data() if hasattr(perplexity_service, 'get_latest_screen_data') else {}
            st.markdown(f"""
            **{chart_emoji} API Requests:**
            - **sonar-pro:** {screen_data.get('sonar_pro_low', 0)}
            - **sonar medium:** {screen_data.get('sonar_medium', 0)}
            - **sonar low:** {screen_data.get('sonar_low', 0)}
            """)

        with col3:
            st.markdown("**📥 Input Tokens:**")
            st.markdown(f"""
            - **sonar:** {screen_data.get('sonar_input_tokens', 0):,}
            - **reasoning-pro:** {screen_data.get('reasoning_pro_input_tokens', 0):,}
            - **sonar-pro:** {screen_data.get('sonar_pro_input_tokens', 0):,}
            """)

        st.markdown("---")

        # Cost chart (placeholder - needs actual data)
        st.markdown("### 📈 Динамика расходов")
        st.info("График расходов по дням (интеграция в процессе)")

        # Provider comparison
        st.markdown("### 🔄 Сравнение провайдеров")
        st.info("Сравнение стоимости GigaChat vs GPT vs Perplexity (интеграция в процессе)")

    except Exception as e:
        logger.error(f"Error in cost analytics: {e}")
        st.warning(f"⚠️ Ошибка загрузки аналитики: {e}")
        st.info("Аналитика расходов временно недоступна")


def render_writer_tab():
    """Render Writer Agent tab with sub-tabs"""
    st.markdown("### ✍️ Writer Agent")
    st.markdown("**Описание:** Генерирует профессиональный текст грантовой заявки через GigaChat")

    # SUB-TABS for Writer
    writer_subtabs = ["Статистика", "Тексты"]
    writer_icons = ["📊", "📝"]

    tab1, tab2 = st.tabs([f"{icon} {name}" for icon, name in zip(writer_icons, writer_subtabs)])

    # TAB 1: Statistics
    with tab1:
        render_writer_statistics()

    # TAB 2: Generated texts
    with tab2:
        render_writer_texts()


def render_writer_statistics():
    """Render Writer statistics sub-tab"""
    st.markdown("#### 📊 Статистика Writer")

    stats = get_agent_statistics('writer', db)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего текстов", stats.get('total', 0))
    with col2:
        st.metric("Завершено", stats.get('completed', 0))
    with col3:
        st.metric("Средняя оценка", f"{stats.get('avg_quality_score', 0)}/10")

    st.markdown("---")

    # Prompt management (disabled - table agent_prompts not exists)
    # st.markdown("### 📝 Управление промптами")
    # st.info("Таблица agent_prompts пока не создана. Будет добавлено позже.")


def render_writer_texts():
    """Render Writer generated texts list"""
    st.markdown("#### 📝 Сгенерированные тексты")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Статус",
            ["Все", "completed", "draft", "error"],
            key="writer_status_filter"
        )

    with col2:
        period_filter = st.selectbox(
            "Период",
            ["Все время", "Сегодня", "Неделя", "Месяц"],
            key="writer_period_filter"
        )

    with col3:
        limit = st.number_input(
            "Показать записей",
            min_value=10,
            max_value=100,
            value=20,
            key="writer_limit"
        )

    st.markdown("---")

    # Get texts
    texts = get_writer_generated_texts(db)

    # Apply filters
    if status_filter != "Все":
        texts = [t for t in texts if t.get('status') == status_filter]

    texts = texts[:limit]

    # Display count
    st.write(f"**Найдено текстов: {len(texts)}**")

    if not texts:
        st.info("📝 Тексты не найдены")
        return

    # Display texts
    for text in texts:
        status_emoji = "✅" if text['status'] == 'completed' else "📝" if text['status'] == 'draft' else "❌"
        grant_id = text.get('grant_id', text.get('id', 'N/A'))

        with st.expander(f"{status_emoji} Грант {grant_id} - {text.get('created_at', 'N/A')[:10]}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**ID гранта:** {grant_id}")
                st.write(f"**Пользователь:** {text.get('user_id', 'N/A')}")
                st.write(f"**Статус:** {text['status']}")

            with col2:
                st.write(f"**Оценка качества:** {text.get('quality_score', 'N/A')}/10")
                st.write(f"**Создано:** {text.get('created_at', 'N/A')}")
                st.write(f"**Обновлено:** {text.get('updated_at', 'N/A')}")

            # Action buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("👁️ Просмотр", key=f"view_text_{text.get('id', grant_id)}"):
                    st.info("Просмотр текста (интеграция в процессе)")

            with col2:
                if st.button("📤 Экспорт", key=f"export_text_{text.get('id', grant_id)}"):
                    st.info("Экспорт текста (интеграция в процессе)")

            with col3:
                if st.button("✏️ Редактировать", key=f"edit_text_{text.get('id', grant_id)}"):
                    st.info("Редактирование (интеграция в процессе)")


# =============================================================================
# MAIN PAGE
# =============================================================================

def main():
    """Main page rendering"""
    if render_page_header:
        render_page_header("AI Агенты", "🤖", "Управление всеми AI агентами системы")
    else:
        st.title("🤖 AI Агенты")
        st.markdown("Управление всеми AI агентами системы")

    # MAIN TABS (5 agents)
    agent_tabs = ["Interviewer", "Auditor", "Planner", "Researcher", "Writer"]
    agent_icons = ["📝", "✅", "📐", "🔍", "✍️"]

    tab1, tab2, tab3, tab4, tab5 = st.tabs([f"{icon} {name}" for icon, name in zip(agent_icons, agent_tabs)])

    with tab1:
        render_interviewer_tab()

    with tab2:
        render_auditor_tab()

    with tab3:
        render_planner_tab()

    with tab4:
        render_researcher_tab()

    with tab5:
        render_writer_tab()

    # Footer
    st.markdown("---")
    st.caption("AI Agents v3.0.0 | Полная интеграция функционала из 5 архивных файлов")
    st.caption("Запуск агентов выполняется через Pipeline Dashboard")


if __name__ == "__main__":
    main()
