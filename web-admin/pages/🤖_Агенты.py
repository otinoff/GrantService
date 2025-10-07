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

# PATH SETUP - CRITICAL: Import setup_paths FIRST before any project imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # Add web-admin to path
import setup_paths  # Centralized path configuration

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
    from utils.postgres_helper import execute_query, execute_update
except ImportError as e:
    st.warning(f"⚠️ postgres_helper not available: {e}")
    execute_query = None
    execute_update = None

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

# AI Agent Settings
try:
    from utils.agent_settings import (
        get_agent_settings,
        save_agent_settings,
        is_claude_code_enabled,
        get_interviewer_mode
    )
    AGENT_SETTINGS_AVAILABLE = True
except ImportError as e:
    logger_warning = f"Agent settings not available: {e}"
    # Will show warning in UI later
    AGENT_SETTINGS_AVAILABLE = False

# Prompt Manager
try:
    from utils.prompt_manager import (
        get_agent_prompts,
        get_prompt_by_key,
        save_prompt,
        set_default_prompt,
        format_prompt as format_prompt_template
    )
    PROMPT_MANAGER_AVAILABLE = True
    PROMPT_MANAGER_ERROR = None
except ImportError as e:
    PROMPT_MANAGER_AVAILABLE = False
    PROMPT_MANAGER_ERROR = str(e)

# Stage Tracker
try:
    from utils.stage_tracker import (
        format_stage_badge,
        format_stage_progress_compact,
        get_stage_emoji,
        get_stage_name,
        get_stage_progress,
        get_stage_info,
        update_stage
    )
    STAGE_TRACKER_AVAILABLE = True
except ImportError as e:
    STAGE_TRACKER_AVAILABLE = False
    # logger not available yet at this point in imports

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

# Interview Questions Functions
def get_interview_questions():
    """Get all interview questions from database"""
    if not execute_query:
        return []
    try:
        result = execute_query("""
            SELECT id, question_number, question_text, field_name, question_type,
                   options, hint_text, is_required, is_active, created_at, updated_at
            FROM interview_questions
            ORDER BY question_number
        """)
        return result if result else []
    except Exception as e:
        logger.error(f"Error getting interview questions: {e}")
        return []

def update_interview_question(question_id, **kwargs):
    """Update interview question fields"""
    if not execute_update:
        raise Exception("execute_update not available")

    # Build UPDATE query dynamically based on provided kwargs
    valid_fields = ['question_text', 'hint_text', 'question_type', 'field_name',
                    'is_required', 'is_active', 'question_number', 'options']

    update_fields = []
    values = []

    for field, value in kwargs.items():
        if field in valid_fields:
            update_fields.append(f"{field} = %s")
            values.append(value)

    if not update_fields:
        raise Exception("No valid fields to update")

    # Add updated_at timestamp
    update_fields.append("updated_at = NOW()")

    # Add question_id at the end for WHERE clause
    values.append(question_id)

    query = f"""
        UPDATE interview_questions
        SET {', '.join(update_fields)}
        WHERE id = %s
    """

    try:
        execute_update(query, tuple(values))
        return True
    except Exception as e:
        logger.error(f"Error updating question {question_id}: {e}")
        raise

def insert_interview_question(question_text, question_type, question_number,
                               is_required, is_active, options=None):
    """Insert new interview question"""
    if not execute_update:
        raise Exception("execute_update not available")

    query = """
        INSERT INTO interview_questions
        (question_text, question_type, question_number, is_required, is_active, options)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    try:
        execute_update(query, (question_text, question_type, question_number,
                               is_required, is_active, options))
        return True
    except Exception as e:
        logger.error(f"Error inserting question: {e}")
        raise

def delete_interview_question(question_id):
    """Delete interview question"""
    if not execute_update:
        raise Exception("execute_update not available")

    query = "DELETE FROM interview_questions WHERE id = %s"

    try:
        execute_update(query, (question_id,))
        return True
    except Exception as e:
        logger.error(f"Error deleting question {question_id}: {e}")
        raise

@st.cache_data(ttl=300)
def get_agent_statistics(agent_type: str, _db, days: int = 30):
    """Get statistics for specific agent"""
    try:
        if agent_type == 'interviewer':
            # Get from sessions table
            result = execute_query("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed,
                    ROUND(AVG(progress_percentage), 1) as avg_progress,
                    ROUND(AVG(session_duration_minutes), 1) as avg_duration_min
                FROM sessions
                WHERE started_at >= NOW() - INTERVAL '30 days'
            """)
            return result[0] if result else {}

        elif agent_type == 'auditor':
            result = execute_query("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved,
                    COUNT(CASE WHEN approval_status = 'needs_revision' THEN 1 END) as needs_revision,
                    ROUND(AVG(average_score), 2) as avg_score
                FROM auditor_results
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
            return result[0] if result else {}

        elif agent_type == 'planner':
            result = execute_query("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN data_mapping_complete = TRUE THEN 1 END) as complete_mappings,
                    ROUND(AVG(sections_count), 1) as avg_sections
                FROM planner_structures
                WHERE created_at >= NOW() - INTERVAL '30 days'
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
            result = execute_query("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft,
                    ROUND(AVG(quality_score), 2) as avg_quality_score
                FROM grants
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
            return result[0] if result else {}

        elif agent_type == 'reviewer':
            # Reviewer uses same data as auditor
            result = execute_query("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved,
                    COUNT(CASE WHEN approval_status = 'needs_revision' THEN 1 END) as needs_revision,
                    ROUND(AVG(average_score), 2) as avg_score
                FROM auditor_results
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
            return result[0] if result else {}

        # Default fallback
        return {}

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
        result = execute_query("""
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
    """Render Interviewer Agent tab with sub-tabs"""
    st.markdown("### 📝 Interviewer Agent")
    st.markdown("**Описание:** Собирает информацию о проекте через структурированное интервью из 24 вопросов")

    # SUB-TABS for Interviewer
    interviewer_subtabs = ["Статистика", "Интервью"]
    interviewer_icons = ["📊", "💬"]

    tab1, tab2 = st.tabs([f"{icon} {name}" for icon, name in zip(interviewer_icons, interviewer_subtabs)])

    # TAB 1: Statistics
    with tab1:
        render_interviewer_statistics()

    # TAB 2: Interviews
    with tab2:
        render_interviewer_interviews()


def render_interviewer_statistics():
    """Render Interviewer statistics sub-tab"""
    st.markdown("#### 📊 Статистика Interviewer")

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

                    # Show hint_text if exists
                    if q.get('hint_text'):
                        st.info(f"💡 **Подсказка:** {q.get('hint_text')}")

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

                    # Edit form toggle
                    if f"edit_mode_{q['id']}" not in st.session_state:
                        st.session_state[f"edit_mode_{q['id']}"] = False

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✏️ Редактировать", key=f"edit_{q['id']}"):
                            st.session_state[f"edit_mode_{q['id']}"] = not st.session_state[f"edit_mode_{q['id']}"]
                            st.rerun()

                    with col2:
                        if st.button("🔄 Переключить статус", key=f"toggle_{q['id']}"):
                            try:
                                update_interview_question(q['id'], is_active=not q.get('is_active', True))
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Ошибка: {e}")

                    with col3:
                        if st.button("🗑️ Удалить", key=f"delete_{q['id']}"):
                            try:
                                delete_interview_question(q['id'])
                                st.success("✅ Удалено")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Ошибка: {e}")

                    # Edit form (shown when edit button is clicked)
                    if st.session_state.get(f"edit_mode_{q['id']}", False):
                        st.markdown("---")
                        st.markdown("##### ✏️ Редактирование вопроса")

                        with st.form(key=f"edit_form_{q['id']}"):
                            edit_question_number = st.number_input(
                                "Номер вопроса",
                                min_value=1,
                                max_value=100,
                                value=q.get('question_number', 1),
                                key=f"edit_num_{q['id']}"
                            )

                            edit_question_text = st.text_area(
                                "Текст вопроса",
                                value=q.get('question_text', ''),
                                height=100,
                                key=f"edit_text_{q['id']}"
                            )

                            edit_hint_text = st.text_area(
                                "Подсказка (hint_text)",
                                value=q.get('hint_text', ''),
                                height=80,
                                help="Необязательное поле - подсказка для пользователя",
                                key=f"edit_hint_{q['id']}"
                            )

                            edit_question_type = st.selectbox(
                                "Тип вопроса",
                                options=['text', 'textarea', 'number', 'select', 'multiselect', 'date'],
                                index=['text', 'textarea', 'number', 'select', 'multiselect', 'date'].index(q.get('question_type', 'text')),
                                key=f"edit_type_{q['id']}"
                            )

                            edit_field_name = st.text_input(
                                "Название поля (field_name)",
                                value=q.get('field_name', ''),
                                help="Техническое название поля для хранения ответа",
                                key=f"edit_field_{q['id']}"
                            )

                            col_req, col_active = st.columns(2)
                            with col_req:
                                edit_is_required = st.checkbox(
                                    "Обязательный вопрос",
                                    value=q.get('is_required', False),
                                    key=f"edit_req_{q['id']}"
                                )
                            with col_active:
                                edit_is_active = st.checkbox(
                                    "Активен",
                                    value=q.get('is_active', True),
                                    key=f"edit_active_{q['id']}"
                                )

                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                submit_edit = st.form_submit_button("💾 Сохранить изменения", use_container_width=True)
                            with col_cancel:
                                cancel_edit = st.form_submit_button("❌ Отмена", use_container_width=True)

                            if submit_edit:
                                try:
                                    update_interview_question(
                                        q['id'],
                                        question_number=edit_question_number,
                                        question_text=edit_question_text,
                                        hint_text=edit_hint_text if edit_hint_text else None,
                                        question_type=edit_question_type,
                                        field_name=edit_field_name if edit_field_name else None,
                                        is_required=edit_is_required,
                                        is_active=edit_is_active
                                    )
                                    st.session_state[f"edit_mode_{q['id']}"] = False
                                    st.success("✅ Вопрос обновлен!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Ошибка: {e}")

                            if cancel_edit:
                                st.session_state[f"edit_mode_{q['id']}"] = False
                                st.rerun()
        else:
            st.info("Вопросы не найдены. Добавьте первый вопрос выше.")

    except Exception as e:
        st.error(f"❌ Ошибка загрузки вопросов: {e}")

    # Prompt management
    if PROMPT_MANAGER_AVAILABLE:
        render_agent_prompts('interviewer', 'Interviewer Agent')

    # AI Agent Settings
    if AGENT_SETTINGS_AVAILABLE:
        render_interviewer_settings()


def render_interviewer_interviews():
    """Render Interviewer interviews list"""
    st.markdown("#### 💬 Завершенные интервью")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Статус",
            ["Все", "completed", "in_progress", "draft"],
            key="interviewer_status_filter"
        )

    with col2:
        period_filter = st.selectbox(
            "Период",
            ["Все время", "Сегодня", "Неделя", "Месяц"],
            key="interviewer_period_filter"
        )

    with col3:
        limit = st.number_input(
            "Показать записей",
            min_value=10,
            max_value=100,
            value=20,
            key="interviewer_limit"
        )

    st.markdown("---")

    # Get interviews from sessions table
    try:
        query = """
            SELECT
                s.id as session_id,
                s.user_id,
                u.username,
                s.anketa_id,
                s.current_question,
                s.answers_json,
                s.status,
                s.created_at,
                s.updated_at,
                COUNT(DISTINCT jsonb_object_keys(s.answers_json)) as answered_questions
            FROM sessions s
            LEFT JOIN users u ON s.user_id = u.telegram_id
            WHERE s.answers_json IS NOT NULL
            GROUP BY s.id, s.user_id, u.username, s.anketa_id, s.current_question, s.answers_json, s.status, s.created_at, s.updated_at
            ORDER BY s.updated_at DESC
            LIMIT %s
        """

        interviews = execute_query(query, (limit,), fetch=True) or []

        # Apply filters
        if status_filter != "Все":
            interviews = [i for i in interviews if i.get('status') == status_filter]

        # Display count
        st.write(f"**Найдено интервью: {len(interviews)}**")

        if not interviews:
            st.info("💬 Интервью не найдены")
            return

        # Display interviews
        for interview in interviews:
            status_emoji = "✅" if interview.get('status') == 'completed' else "🔄" if interview.get('status') == 'in_progress' else "📝"
            username = interview.get('username', 'Unknown')
            session_id = interview.get('session_id', 'N/A')
            anketa_id = interview.get('anketa_id', 'N/A')
            answered = interview.get('answered_questions', 0)

            # Format title with anketa_id if available
            title = f"{status_emoji} 📋 {anketa_id} - @{username} ({answered}/24 ответов)" if anketa_id != 'N/A' else f"{status_emoji} Интервью #{session_id} - @{username} ({answered}/24 ответов)"

            with st.expander(title):
                col1, col2 = st.columns(2)

                with col1:
                    if anketa_id != 'N/A':
                        st.write(f"**📋 Anketa ID:** `{anketa_id}`")
                    st.write(f"**ID сессии:** {session_id}")
                    st.write(f"**Пользователь:** @{username}")
                    st.write(f"**Telegram ID:** {interview.get('user_id', 'N/A')}")
                    st.write(f"**Статус:** {interview.get('status', 'N/A')}")

                with col2:
                    st.write(f"**Текущий вопрос:** {interview.get('current_question', 0)}")
                    st.write(f"**Отвечено:** {answered}/24")
                    st.write(f"**Создано:** {interview.get('created_at', 'N/A')}")
                    st.write(f"**Обновлено:** {interview.get('updated_at', 'N/A')}")

                # Show answers
                if interview.get('answers_json'):
                    st.markdown("**Ответы:**")
                    answers = interview['answers_json']
                    if isinstance(answers, dict):
                        for q_num, answer in sorted(answers.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
                            st.text(f"Q{q_num}: {answer[:100]}..." if len(str(answer)) > 100 else f"Q{q_num}: {answer}")

    except Exception as e:
        logger.error(f"Error loading interviews: {e}")
        st.error(f"❌ Ошибка загрузки интервью: {e}")


def render_auditor_tab():
    """Render Auditor Agent tab with sub-tabs"""
    st.markdown("### ✅ Auditor Agent (Аналитик)")
    st.markdown("**Описание:** Проверяет качество заполнения анкеты и оценивает проект по 5 критериям (шкала 1-10)")

    # SUB-TABS for Auditor
    auditor_subtabs = ["Статистика", "Проверки"]
    auditor_icons = ["📊", "✅"]

    tab1, tab2 = st.tabs([f"{icon} {name}" for icon, name in zip(auditor_icons, auditor_subtabs)])

    # TAB 1: Statistics
    with tab1:
        render_auditor_statistics()

    # TAB 2: Audits
    with tab2:
        render_auditor_audits()


def render_auditor_statistics():
    """Render Auditor statistics sub-tab"""
    st.markdown("#### 📊 Статистика Auditor")

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

    # Prompt management
    if PROMPT_MANAGER_AVAILABLE:
        render_agent_prompts('auditor', 'Auditor Agent')

    # AI Agent Settings
    if AGENT_SETTINGS_AVAILABLE:
        render_generic_agent_settings('auditor', 'Auditor Agent')


def render_auditor_audits():
    """Render Auditor audits list"""
    st.markdown("#### ✅ Проверки и оценки")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Статус",
            ["Все", "approved", "needs_revision", "rejected"],
            key="auditor_status_filter"
        )

    with col2:
        period_filter = st.selectbox(
            "Период",
            ["Все время", "Сегодня", "Неделя", "Месяц"],
            key="auditor_period_filter"
        )

    with col3:
        limit = st.number_input(
            "Показать записей",
            min_value=10,
            max_value=100,
            value=20,
            key="auditor_limit"
        )

    st.markdown("---")

    # Get audits from grant_applications table
    try:
        query = """
            SELECT
                ga.id as application_id,
                ga.user_id,
                u.username,
                ga.anketa_data,
                ga.audit_score,
                ga.audit_feedback,
                ga.status,
                ga.created_at,
                ga.updated_at
            FROM grant_applications ga
            LEFT JOIN users u ON ga.user_id = u.telegram_id
            WHERE ga.audit_score IS NOT NULL
            ORDER BY ga.updated_at DESC
            LIMIT %s
        """

        audits = execute_query(query, (limit,), fetch=True) or []

        # Apply filters
        if status_filter != "Все":
            audits = [a for a in audits if a.get('status') == status_filter]

        # Display count
        st.write(f"**Найдено проверок: {len(audits)}**")

        if not audits:
            st.info("✅ Проверки не найдены")
            return

        # Display audits
        for audit in audits:
            status_emoji = "✅" if audit.get('status') == 'approved' else "⚠️" if audit.get('status') == 'needs_revision' else "❌"
            username = audit.get('username', 'Unknown')
            application_id = audit.get('application_id', 'N/A')
            score = audit.get('audit_score', 0)

            with st.expander(f"{status_emoji} Проверка #{application_id} - @{username} (Балл: {score}/10)"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**ID заявки:** {application_id}")
                    st.write(f"**Пользователь:** @{username}")
                    st.write(f"**Telegram ID:** {audit.get('user_id', 'N/A')}")
                    st.write(f"**Статус:** {audit.get('status', 'N/A')}")

                with col2:
                    st.write(f"**Балл аудита:** {score}/10")
                    st.write(f"**Создано:** {audit.get('created_at', 'N/A')}")
                    st.write(f"**Обновлено:** {audit.get('updated_at', 'N/A')}")

                # Show feedback
                if audit.get('audit_feedback'):
                    st.markdown("**Заключение аудитора:**")
                    st.text_area(
                        "Feedback",
                        value=audit['audit_feedback'],
                        height=150,
                        key=f"feedback_{application_id}",
                        disabled=True,
                        label_visibility="collapsed"
                    )

                # Show anketa summary
                if audit.get('anketa_data'):
                    st.markdown("**Данные анкеты:**")
                    anketa = audit['anketa_data']
                    if isinstance(anketa, dict):
                        st.json(anketa)

    except Exception as e:
        logger.error(f"Error loading audits: {e}")
        st.error(f"❌ Ошибка загрузки проверок: {e}")


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

    # Prompt management
    if PROMPT_MANAGER_AVAILABLE:
        render_agent_prompts('planner', 'Planner Agent')

    # AI Agent Settings
    if AGENT_SETTINGS_AVAILABLE:
        render_generic_agent_settings('planner', 'Planner Agent')


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

    # Prompt management
    if PROMPT_MANAGER_AVAILABLE:
        try:
            render_agent_prompts('researcher', 'Researcher Agent')
        except Exception as e:
            st.error(f"Ошибка загрузки промптов: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.warning(f"⚠️ Prompt Manager недоступен: {PROMPT_MANAGER_ERROR}")

    # AI Agent Settings
    if AGENT_SETTINGS_AVAILABLE:
        render_generic_agent_settings('researcher', 'Researcher Agent')


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

    # Prompt management
    if PROMPT_MANAGER_AVAILABLE:
        render_agent_prompts('writer', 'Writer Agent')

    # AI Agent Settings
    if AGENT_SETTINGS_AVAILABLE:
        render_writer_settings()


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

        # Format created_at - handle both datetime and string
        created_at = text.get('created_at', 'N/A')
        if created_at != 'N/A':
            created_at_str = str(created_at)[:10] if created_at else 'N/A'
        else:
            created_at_str = 'N/A'

        with st.expander(f"{status_emoji} Грант {grant_id} - {created_at_str}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**ID гранта:** {grant_id}")
                st.write(f"**Пользователь:** {text.get('user_id', 'N/A')}")
                st.write(f"**Статус:** {text['status']}")

            with col2:
                st.write(f"**Оценка качества:** {text.get('quality_score', 'N/A')}/10")
                st.write(f"**Создано:** {str(text.get('created_at', 'N/A'))}")
                st.write(f"**Обновлено:** {str(text.get('updated_at', 'N/A'))}")

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


def render_reviewer_tab():
    """Render Reviewer Agent tab with sub-tabs"""
    st.markdown("### 🔎 Reviewer Agent (Рецензент)")
    st.markdown("**Описание:** Делает финальный аудит готовой заявки на соответствие требованиям фонда президентских грантов и дает предварительное заключение")

    # SUB-TABS for Reviewer
    reviewer_subtabs = ["Статистика", "Рецензии"]
    reviewer_icons = ["📊", "🔎"]

    tab1, tab2 = st.tabs([f"{icon} {name}" for icon, name in zip(reviewer_icons, reviewer_subtabs)])

    # TAB 1: Statistics
    with tab1:
        render_reviewer_statistics()

    # TAB 2: Reviews
    with tab2:
        render_reviewer_reviews()


def render_reviewer_statistics():
    """Render Reviewer statistics sub-tab"""
    st.markdown("#### 📊 Статистика Reviewer")

    # Statistics
    stats = get_agent_statistics('reviewer', db)

    # Safety check: if stats is None, use empty dict
    if stats is None:
        stats = {}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего рецензий", stats.get('total', 0))
    with col2:
        st.metric("Одобрено", stats.get('approved', 0))
    with col3:
        st.metric("На доработку", stats.get('needs_revision', 0))
    with col4:
        st.metric("Средняя оценка", f"{stats.get('avg_score', 0)}/10")

    st.markdown("---")

    # Review criteria
    st.markdown("### 📋 Критерии рецензирования")

    criteria = {
        'Соответствие требованиям фонда': 'Насколько заявка соответствует формальным требованиям фонда президентских грантов',
        'Качество текста': 'Грамотность, структура, логика изложения',
        'Обоснованность бюджета': 'Детализация и обоснованность статей бюджета',
        'Социальная значимость': 'Значимость проекта для целевой аудитории и общества',
        'Реалистичность реализации': 'Выполнимость проекта в заявленные сроки с указанной командой'
    }

    for criterion, description in criteria.items():
        with st.expander(f"📌 {criterion}"):
            st.markdown(f"**{description}**")
            st.markdown("- Оценка от 1 до 10")
            st.markdown("- Влияет на финальное решение о подаче заявки")

    st.markdown("---")

    # Prompt management
    if PROMPT_MANAGER_AVAILABLE:
        render_agent_prompts('reviewer', 'Reviewer Agent')

    # AI Agent Settings
    if AGENT_SETTINGS_AVAILABLE:
        render_generic_agent_settings('reviewer', 'Reviewer Agent')


def render_reviewer_reviews():
    """Render Reviewer reviews list"""
    st.markdown("#### 🔎 Рецензии готовых заявок")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Статус",
            ["Все", "approved", "needs_revision", "rejected"],
            key="reviewer_status_filter"
        )

    with col2:
        period_filter = st.selectbox(
            "Период",
            ["Все время", "Сегодня", "Неделя", "Месяц"],
            key="reviewer_period_filter"
        )

    with col3:
        limit = st.number_input(
            "Показать записей",
            min_value=10,
            max_value=100,
            value=20,
            key="reviewer_limit"
        )

    st.markdown("---")

    # Get reviews from grants table
    try:
        query = """
            SELECT
                g.grant_id,
                g.user_id,
                u.username,
                g.grant_name,
                g.review_score,
                g.review_feedback,
                g.final_status,
                g.created_at,
                g.updated_at
            FROM grants g
            LEFT JOIN users u ON g.user_id = u.telegram_id
            WHERE g.review_score IS NOT NULL
            ORDER BY g.updated_at DESC
            LIMIT %s
        """

        reviews = execute_query(query, (limit,), fetch=True) or []

        # Apply filters
        if status_filter != "Все":
            reviews = [r for r in reviews if r.get('final_status') == status_filter]

        # Display count
        st.write(f"**Найдено рецензий: {len(reviews)}**")

        if not reviews:
            st.info("🔎 Рецензии не найдены")
            return

        # Display reviews
        for review in reviews:
            status_emoji = "✅" if review.get('final_status') == 'approved' else "⚠️" if review.get('final_status') == 'needs_revision' else "❌"
            username = review.get('username', 'Unknown')
            grant_id = review.get('grant_id', 'N/A')
            grant_name = review.get('grant_name', 'Без названия')
            score = review.get('review_score', 0)

            with st.expander(f"{status_emoji} {grant_id} - {grant_name[:50]}... (Оценка: {score}/10)"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**ID гранта:** {grant_id}")
                    st.write(f"**Название:** {grant_name}")
                    st.write(f"**Пользователь:** @{username}")
                    st.write(f"**Telegram ID:** {review.get('user_id', 'N/A')}")

                with col2:
                    st.write(f"**Оценка рецензента:** {score}/10")
                    st.write(f"**Статус:** {review.get('final_status', 'N/A')}")
                    st.write(f"**Создано:** {review.get('created_at', 'N/A')}")
                    st.write(f"**Обновлено:** {review.get('updated_at', 'N/A')}")

                # Show review feedback
                if review.get('review_feedback'):
                    st.markdown("**Заключение рецензента:**")
                    st.text_area(
                        "Review",
                        value=review['review_feedback'],
                        height=200,
                        key=f"review_{grant_id}",
                        disabled=True,
                        label_visibility="collapsed"
                    )

                # Action buttons
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("📄 Заявка", key=f"view_grant_{grant_id}"):
                        st.session_state.selected_grant_id = grant_id
                        st.rerun()

                with col2:
                    if st.button("📋 ID", key=f"copy_grant_{grant_id}"):
                        st.code(grant_id)
                        st.success("ID показан!")

                with col3:
                    if st.button("💾 Экспорт", key=f"export_review_{grant_id}"):
                        st.info("Экспорт рецензии (интеграция в процессе)")

    except Exception as e:
        logger.error(f"Error loading reviews: {e}")
        st.error(f"❌ Ошибка загрузки рецензий: {e}")


# =============================================================================
# AI AGENT SETTINGS UI COMPONENTS
# =============================================================================

def render_interviewer_settings():
    """Render Interviewer Agent settings UI"""
    if not AGENT_SETTINGS_AVAILABLE:
        st.warning("⚠️ Настройки агентов временно недоступны")
        return

    st.markdown("---")
    st.markdown("### ⚙️ Настройки режима интервью")

    # Get current settings
    current_settings = get_agent_settings('interviewer')
    current_mode = current_settings.get('mode', 'structured')

    # Mode selection
    mode_icon_structured = "📋"
    mode_icon_ai = "🤖"

    mode = st.radio(
        "Режим работы интервьюера:",
        options=['structured', 'ai_powered'],
        format_func=lambda x: {
            'structured': f'{mode_icon_structured} Структурированный (24 фиксированных вопроса)',
            'ai_powered': f'{mode_icon_ai} AI-Powered (адаптивные вопросы через Claude Code)'
        }[x],
        index=0 if current_mode == 'structured' else 1,
        key='interviewer_mode_select'
    )

    # Info about selected mode
    if mode == 'structured':
        st.info("📋 **Структурированный режим:** Пользователь отвечает на 24 фиксированных вопроса из таблицы interview_questions")
    else:
        st.info("🤖 **AI-Powered режим:** Claude Code генерирует адаптивные вопросы на основе ответов пользователя")

    # Save and Reset buttons
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("💾 Сохранить", key='save_interviewer'):
            if execute_update:
                try:
                    success = save_agent_settings('interviewer', mode=mode)
                    if success:
                        st.success("✅ Настройки сохранены!")
                        st.rerun()
                    else:
                        st.error("❌ Ошибка сохранения")
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
            else:
                st.error("⚠️ execute_update недоступен")

    with col2:
        if st.button("🔄 Сбросить", key='reset_interviewer'):
            if execute_update:
                try:
                    success = save_agent_settings('interviewer', mode='structured')
                    if success:
                        st.success("✅ Сброшено к structured режиму")
                        st.rerun()
                    else:
                        st.error("❌ Ошибка сброса")
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
            else:
                st.error("⚠️ execute_update недоступен")


def render_writer_settings():
    """Render Writer Agent settings UI"""
    if not AGENT_SETTINGS_AVAILABLE:
        st.warning("⚠️ Настройки агентов временно недоступны")
        return

    st.markdown("---")
    st.markdown("### ⚙️ Настройки генератора текста")

    # Get current settings
    current_settings = get_agent_settings('writer')
    current_provider = current_settings.get('provider', 'claude_code')  # Default: Claude Code
    config_data = current_settings.get('config', {})

    # Provider selection
    gigachat_icon = "🇷🇺"
    claude_icon = "🇺🇸"

    provider = st.radio(
        "LLM Провайдер:",
        options=['gigachat', 'claude_code'],
        format_func=lambda x: {
            'gigachat': f'{gigachat_icon} GigaChat (русский текст, быстро)',
            'claude_code': f'{claude_icon} Claude Code (аналитика + структура)'
        }[x],
        index=0 if current_provider == 'gigachat' else 1,
        key='writer_provider'
    )

    # Temperature slider
    temperature = st.slider(
        "Temperature (креативность):",
        min_value=0.0,
        max_value=1.0,
        value=config_data.get('temperature', 0.7),
        step=0.1,
        key='writer_temperature',
        help="0.0 = точный, 1.0 = креативный"
    )

    # Save button
    if st.button("💾 Сохранить", key='save_writer'):
        if execute_update:
            try:
                success = save_agent_settings(
                    'writer',
                    provider=provider,
                    config={'temperature': temperature}
                )
                if success:
                    st.success("✅ Настройки Writer сохранены!")
                    st.rerun()
                else:
                    st.error("❌ Ошибка сохранения")
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
        else:
            st.error("⚠️ execute_update недоступен")


def render_agent_prompts(agent_name: str, display_name: str):
    """
    Render prompt management UI for an agent

    Args:
        agent_name: Agent identifier (auditor, planner, writer, researcher)
        display_name: Human-readable name for display
    """
    if not PROMPT_MANAGER_AVAILABLE:
        st.info("📝 Система управления промптами временно недоступна")
        return

    st.markdown("---")
    st.markdown(f"### 📝 Промпты {display_name}")

    try:
        # Get all prompts for this agent
        prompts = get_agent_prompts(agent_name)

        if not prompts:
            st.info(f"Промпты для {display_name} пока не добавлены")
            return

        # Group prompts by type
        prompts_by_type = {}
        for prompt in prompts:
            prompt_type = prompt.get('prompt_type', 'general')
            if prompt_type not in prompts_by_type:
                prompts_by_type[prompt_type] = []
            prompts_by_type[prompt_type].append(prompt)

        # Display prompts grouped by type
        for prompt_type, type_prompts in prompts_by_type.items():
            st.markdown(f"#### 📄 {prompt_type.replace('_', ' ').title()}")

            for prompt in type_prompts:
                prompt_key = prompt.get('prompt_key', '')
                is_default = prompt.get('is_default', False)
                version = prompt.get('version', 1)

                default_badge = " 🌟 [DEFAULT]" if is_default else ""
                version_badge = f"v{version}"

                with st.expander(f"📋 {prompt_key} {version_badge}{default_badge}"):
                    # Metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Провайдер:** {prompt.get('llm_provider', 'N/A')}")
                    with col2:
                        st.write(f"**Модель:** {prompt.get('model', 'N/A') or 'default'}")
                    with col3:
                        st.write(f"**Использований:** {prompt.get('usage_count', 0)}")

                    col4, col5, col6 = st.columns(3)
                    with col4:
                        st.write(f"**Temperature:** {prompt.get('temperature', 0.7)}")
                    with col5:
                        st.write(f"**Max tokens:** {prompt.get('max_tokens', 4000)}")
                    with col6:
                        avg_score = prompt.get('avg_score')
                        score_text = f"{avg_score:.2f}" if avg_score else "N/A"
                        st.write(f"**Средняя оценка:** {score_text}")

                    # Description
                    if prompt.get('prompt_description'):
                        st.info(prompt.get('prompt_description'))

                    # Variables
                    variables = prompt.get('variables')
                    if variables:
                        if isinstance(variables, str):
                            try:
                                variables = json.loads(variables)
                            except:
                                variables = None

                        if variables:
                            st.markdown("**Переменные промпта:**")
                            st.json(variables)

                    # Prompt text editor
                    st.markdown("**Текст промпта:**")
                    prompt_text = st.text_area(
                        "Редактировать промпт:",
                        value=prompt.get('prompt_text', ''),
                        height=300,
                        key=f"edit_{prompt_key}",
                        help="Используйте {variable_name} для подстановки переменных"
                    )

                    # Action buttons
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if st.button("💾 Сохранить", key=f"save_{prompt_key}"):
                            try:
                                # Save updated prompt (increments version)
                                new_id = save_prompt(
                                    agent_name=agent_name,
                                    prompt_type=prompt.get('prompt_type'),
                                    prompt_text=prompt_text,
                                    prompt_key=prompt_key,
                                    description=prompt.get('prompt_description'),
                                    variables=variables,
                                    llm_provider=prompt.get('llm_provider', 'gigachat'),
                                    model=prompt.get('model'),
                                    temperature=float(prompt.get('temperature', 0.7)),
                                    max_tokens=int(prompt.get('max_tokens', 4000)),
                                    is_default=is_default,
                                    updated_by='admin'
                                )

                                if new_id:
                                    st.success(f"✅ Промпт сохранен! (v{version + 1})")
                                    st.rerun()
                                else:
                                    st.error("❌ Ошибка сохранения")
                            except Exception as e:
                                st.error(f"❌ Ошибка: {e}")

                    with col2:
                        if not is_default:
                            if st.button("🌟 Сделать default", key=f"default_{prompt_key}"):
                                try:
                                    success = set_default_prompt(prompt_key)
                                    if success:
                                        st.success("✅ Установлен как default!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Ошибка")
                                except Exception as e:
                                    st.error(f"❌ Ошибка: {e}")

                    with col3:
                        if st.button("📊 Тест", key=f"test_{prompt_key}"):
                            st.info("Тестирование промптов будет реализовано в следующей версии")

                    with col4:
                        if st.button("📜 История", key=f"history_{prompt_key}"):
                            st.info(f"История версий: v1 → v{version}")

    except Exception as e:
        st.error(f"❌ Ошибка загрузки промптов: {e}")
        import traceback
        st.code(traceback.format_exc())


def render_generic_agent_settings(agent_name: str, display_name: str):
    """
    Render universal agent settings UI for Auditor/Planner/Researcher

    Args:
        agent_name: Agent identifier (auditor, planner, researcher)
        display_name: Human-readable name for display
    """
    if not AGENT_SETTINGS_AVAILABLE:
        st.warning("⚠️ Настройки агентов временно недоступны")
        return

    st.markdown("---")
    st.markdown(f"### ⚙️ Настройки {display_name}")

    # Get current settings
    current_settings = get_agent_settings(agent_name)
    current_provider = current_settings.get('provider', 'claude_code')  # Default: Claude Code
    config_data = current_settings.get('config', {})

    # Provider select
    gigachat_icon = "🇷🇺"
    claude_icon = "🇺🇸"

    provider = st.selectbox(
        "LLM Провайдер:",
        options=['gigachat', 'claude_code'],
        format_func=lambda x: f'{gigachat_icon} GigaChat' if x == 'gigachat' else f'{claude_icon} Claude Code',
        index=0 if current_provider == 'gigachat' else 1,
        key=f'{agent_name}_provider'
    )

    # Temperature slider
    temperature = st.slider(
        "Temperature:",
        min_value=0.0,
        max_value=1.0,
        value=config_data.get('temperature', 0.5),
        step=0.1,
        key=f'{agent_name}_temperature',
        help="Контроль креативности агента"
    )

    # Save button
    if st.button("💾 Сохранить", key=f'save_{agent_name}'):
        if execute_update:
            try:
                success = save_agent_settings(
                    agent_name,
                    provider=provider,
                    config={'temperature': temperature}
                )
                if success:
                    st.success(f"✅ Настройки {display_name} сохранены!")
                    st.rerun()
                else:
                    st.error("❌ Ошибка сохранения")
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
        else:
            st.error("⚠️ execute_update недоступен")


# =============================================================================
# MAIN PAGE
# =============================================================================

def render_stage_summary():
    """Render stage funnel summary"""
    st.markdown("### 🔄 Воронка обработки заявок")

    try:
        # Get all active sessions with anketa_id
        query = """
            SELECT
                anketa_id,
                COALESCE(current_stage, 'interviewer') as current_stage,
                COALESCE(agents_passed, ARRAY[]::TEXT[]) as agents_passed,
                username,
                created_at,
                stage_updated_at
            FROM sessions s
            LEFT JOIN users u ON s.user_id = u.telegram_id
            WHERE anketa_id IS NOT NULL
              AND status != 'archived'
            ORDER BY COALESCE(stage_updated_at, created_at) DESC
            LIMIT 10
        """

        sessions = execute_query(query, fetch=True) or []

        if sessions:
            # Show summary metrics
            col1, col2, col3, col4, col5 = st.columns(5)

            # Count by stage
            stage_counts = {'interviewer': 0, 'auditor': 0, 'researcher': 0, 'writer': 0, 'reviewer': 0}
            for session in sessions:
                stage = session.get('current_stage', 'interviewer')
                if stage in stage_counts:
                    stage_counts[stage] += 1

            with col1:
                st.metric("📝 Interviewer", stage_counts['interviewer'])
            with col2:
                st.metric("✅ Auditor", stage_counts['auditor'])
            with col3:
                st.metric("🔍 Researcher", stage_counts['researcher'])
            with col4:
                st.metric("✍️ Writer", stage_counts['writer'])
            with col5:
                st.metric("🔎 Reviewer", stage_counts['reviewer'])

            st.markdown("---")

            # Show recent sessions with stage badges
            st.markdown("#### 📋 Последние заявки в обработке")

            for session in sessions[:5]:
                anketa_id = session.get('anketa_id')
                current_stage = session.get('current_stage', 'interviewer')
                agents_passed = session.get('agents_passed', [])
                username = session.get('username', 'Unknown')

                if STAGE_TRACKER_AVAILABLE:
                    # Use stage tracker for nice badge
                    badge = format_stage_progress_compact(anketa_id, current_stage, agents_passed)
                    st.markdown(f"**{badge}** - @{username}")
                else:
                    # Fallback display
                    stage_emoji = {'interviewer': '📝', 'auditor': '✅', 'researcher': '🔍', 'writer': '✍️', 'reviewer': '🔎'}.get(current_stage, '❓')
                    st.markdown(f"**{stage_emoji} {anketa_id}** - Stage: {current_stage} - @{username}")

        else:
            st.info("📋 Нет активных заявок в обработке")

    except Exception as e:
        logger.error(f"Error rendering stage summary: {e}")
        st.warning(f"⚠️ Ошибка загрузки воронки: {e}")


def main():
    """Main page rendering"""
    if render_page_header:
        render_page_header("AI Агенты", "🤖", "Управление всеми AI агентами системы")
    else:
        st.title("🤖 AI Агенты")
        st.markdown("Управление всеми AI агентами системы")

    # Stage funnel summary
    render_stage_summary()

    st.markdown("---")

    # MAIN TABS (5 agents, Planner hidden)
    agent_tabs = ["Interviewer", "Auditor", "Researcher", "Writer", "Reviewer"]
    agent_icons = ["📝", "✅", "🔍", "✍️", "🔎"]

    tab1, tab2, tab3, tab4, tab5 = st.tabs([f"{icon} {name}" for icon, name in zip(agent_icons, agent_tabs)])

    with tab1:
        render_interviewer_tab()

    with tab2:
        render_auditor_tab()

    with tab3:
        render_researcher_tab()

    with tab4:
        render_writer_tab()

    with tab5:
        render_reviewer_tab()

    # Planner tab hidden temporarily
    # with tab6:
    #     render_planner_tab()

    # Footer
    st.markdown("---")
    st.caption("AI Agents v3.0.0 | Полная интеграция функционала из 5 архивных файлов")
    st.caption("Запуск агентов выполняется через Pipeline Dashboard")


if __name__ == "__main__":
    main()
