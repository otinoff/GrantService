#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard - Main Working Page for GrantService Admin
=====================================================

Объединяет функционал:
- 🏠 Главная страница (метрики, здоровье системы)
- 🎯 Pipeline Dashboard (6-этапный пайплайн заявок)

Author: Streamlit Admin Developer Agent
Date: 2025-10-03
Version: 2.0.0 (Refactored)
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import json

# =============================================================================
# PATH SETUP
# =============================================================================

sys.path.insert(0, str(Path(__file__).parent.parent))
import setup_paths

# =============================================================================
# IMPORTS
# =============================================================================

try:
    from utils.database import AdminDatabase, get_db_connection
    from utils.ui_helpers import (
        render_page_header,
        render_metric_cards,
        render_tabs,
        render_status_badge,
        render_info_card,
        show_success_message,
        show_error_message
    )
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Dashboard - GrantService Admin",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

@st.cache_resource
def get_database():
    """Get database connection"""
    return AdminDatabase()

db = get_database()

# =============================================================================
# DATA FETCHING FUNCTIONS
# =============================================================================

@st.cache_data(ttl=60)
def get_dashboard_metrics() -> Dict[str, Any]:
    """Get main dashboard metrics"""
    conn = get_db_connection()

    metrics = {
        'total_users': 0,
        'active_users_7d': 0,
        'total_applications': 0,
        'applications_in_progress': 0,
        'completed_grants': 0,
        'completion_rate': 0.0,
        'avg_completion_time_hours': 0.0,
        'active_today': 0
    }

    try:
        # Total users
        result = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        metrics['total_users'] = result[0] if result else 0

        # Active users (last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        result = conn.execute(
            "SELECT COUNT(DISTINCT telegram_id) FROM sessions WHERE last_activity >= ?",
            (seven_days_ago,)
        ).fetchone()
        metrics['active_users_7d'] = result[0] if result else 0

        # Total applications
        result = conn.execute("SELECT COUNT(*) FROM grant_applications").fetchone()
        metrics['total_applications'] = result[0] if result else 0

        # Applications in progress
        result = conn.execute(
            "SELECT COUNT(*) FROM grant_applications WHERE status IN ('draft', 'in_progress')"
        ).fetchone()
        metrics['applications_in_progress'] = result[0] if result else 0

        # Completed grants
        result = conn.execute(
            "SELECT COUNT(*) FROM grant_applications WHERE status = 'completed'"
        ).fetchone()
        metrics['completed_grants'] = result[0] if result else 0

        # Completion rate
        if metrics['total_applications'] > 0:
            metrics['completion_rate'] = (
                metrics['completed_grants'] / metrics['total_applications'] * 100
            )

        # Active today
        today = datetime.now().date().isoformat()
        result = conn.execute(
            "SELECT COUNT(DISTINCT telegram_id) FROM sessions WHERE DATE(last_activity) = ?",
            (today,)
        ).fetchone()
        metrics['active_today'] = result[0] if result else 0

    except Exception as e:
        st.error(f"Error fetching metrics: {e}")

    return metrics


@st.cache_data(ttl=60)
def get_pipeline_overview() -> Dict[str, int]:
    """Get counts for each pipeline stage from actual database schema"""
    conn = get_db_connection()

    stats = {
        'interview_in_progress': 0,
        'interview_completed': 0,
        'audit_pending': 0,
        'audit_approved': 0,
        'audit_needs_revision': 0,
        'planning_done': 0,
        'planning_incomplete': 0,
        'research_completed': 0,
        'research_processing': 0,
        'writing_completed': 0,
        'writing_draft': 0,
        'delivered': 0
    }

    try:
        query = """
        SELECT
            -- Stage 1: Interview
            COUNT(CASE WHEN s.completion_status = 'in_progress' THEN 1 END) as interview_in_progress,
            COUNT(CASE WHEN s.completion_status = 'completed' THEN 1 END) as interview_completed,

            -- Stage 2: Audit
            COUNT(CASE WHEN ar.approval_status = 'pending' THEN 1 END) as audit_pending,
            COUNT(CASE WHEN ar.approval_status = 'approved' THEN 1 END) as audit_approved,
            COUNT(CASE WHEN ar.approval_status = 'needs_revision' THEN 1 END) as audit_needs_revision,

            -- Stage 3: Planner
            COUNT(CASE WHEN ps.id IS NOT NULL THEN 1 END) as planning_done,
            COUNT(CASE WHEN ps.data_mapping_complete = 0 THEN 1 END) as planning_incomplete,

            -- Stage 4: Research
            COUNT(CASE WHEN rr.status = 'completed' THEN 1 END) as research_completed,
            COUNT(CASE WHEN rr.status = 'processing' THEN 1 END) as research_processing,

            -- Stage 5: Writing
            COUNT(CASE WHEN g.status = 'completed' THEN 1 END) as writing_completed,
            COUNT(CASE WHEN g.status = 'draft' THEN 1 END) as writing_draft,

            -- Stage 6: Delivery
            COUNT(CASE WHEN g.status = 'delivered' THEN 1 END) as delivered
        FROM sessions s
        LEFT JOIN auditor_results ar ON s.id = ar.session_id
        LEFT JOIN planner_structures ps ON s.id = ps.session_id
        LEFT JOIN researcher_research rr ON s.anketa_id = rr.anketa_id
        LEFT JOIN grants g ON s.anketa_id = g.anketa_id
        WHERE s.started_at >= DATE('now', '-30 days')
        """

        result = conn.execute(query).fetchone()
        if result:
            stats = dict(zip(stats.keys(), result))

    except Exception as e:
        st.error(f"Error fetching pipeline overview: {e}")

    return stats


@st.cache_data(ttl=60)
def get_conversion_funnel() -> Dict[str, int]:
    """Calculate conversion rates between stages"""
    conn = get_db_connection()

    funnel = {
        'started': 0,
        'completed_interview': 0,
        'audited': 0,
        'approved': 0,
        'planned': 0,
        'researched': 0,
        'written': 0,
        'delivered': 0
    }

    try:
        query = """
        SELECT
            COUNT(*) as started,
            COUNT(CASE WHEN s.completion_status = 'completed' THEN 1 END) as completed_interview,
            COUNT(CASE WHEN ar.id IS NOT NULL THEN 1 END) as audited,
            COUNT(CASE WHEN ar.approval_status = 'approved' THEN 1 END) as approved,
            COUNT(CASE WHEN ps.id IS NOT NULL THEN 1 END) as planned,
            COUNT(CASE WHEN rr.id IS NOT NULL THEN 1 END) as researched,
            COUNT(CASE WHEN g.id IS NOT NULL THEN 1 END) as written,
            COUNT(CASE WHEN g.status = 'delivered' THEN 1 END) as delivered
        FROM sessions s
        LEFT JOIN auditor_results ar ON s.id = ar.session_id
        LEFT JOIN planner_structures ps ON s.id = ps.session_id
        LEFT JOIN researcher_research rr ON s.anketa_id = rr.anketa_id
        LEFT JOIN grants g ON s.anketa_id = g.anketa_id
        WHERE s.started_at >= DATE('now', '-30 days')
        """

        result = conn.execute(query).fetchone()
        if result:
            funnel = dict(zip(funnel.keys(), result))

    except Exception as e:
        st.error(f"Error fetching conversion funnel: {e}")

    return funnel


@st.cache_data(ttl=60)
def get_active_applications(stage_filter: str = 'Все', limit: int = 50) -> pd.DataFrame:
    """Get all active applications with their current stage"""
    conn = get_db_connection()

    try:
        query = """
        SELECT
            s.id as session_id,
            s.anketa_id,
            s.telegram_id,
            u.username,
            u.first_name,
            u.last_name,
            s.project_name,
            s.progress_percentage,
            s.completion_status,
            s.started_at,
            s.last_activity,

            -- Audit info
            ar.id as audit_id,
            ar.average_score as audit_score,
            ar.approval_status as audit_status,

            -- Planner info
            ps.id as planner_id,
            ps.data_mapping_complete,

            -- Research info
            rr.id as research_id,
            rr.status as research_status,

            -- Grant info
            g.id as grant_id,
            g.status as grant_status,
            g.quality_score,

            -- Calculate current stage
            CASE
                WHEN g.status = 'delivered' THEN 'Delivered'
                WHEN g.id IS NOT NULL THEN 'Writing'
                WHEN rr.id IS NOT NULL THEN 'Research'
                WHEN ps.id IS NOT NULL THEN 'Planning'
                WHEN ar.id IS NOT NULL THEN 'Audit'
                WHEN s.completion_status = 'completed' THEN 'Audit Pending'
                ELSE 'Interview'
            END as current_stage

        FROM sessions s
        LEFT JOIN users u ON s.telegram_id = u.telegram_id
        LEFT JOIN auditor_results ar ON s.id = ar.session_id
        LEFT JOIN planner_structures ps ON s.id = ps.session_id
        LEFT JOIN researcher_research rr ON s.anketa_id = rr.anketa_id
        LEFT JOIN grants g ON s.anketa_id = g.anketa_id
        WHERE s.started_at >= DATE('now', '-30 days')
        ORDER BY s.last_activity DESC
        LIMIT ?
        """

        df = pd.read_sql_query(query, conn, params=(limit,))
        return df

    except Exception as e:
        st.error(f"Error fetching active applications: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_recent_activity(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent system activity"""
    conn = get_db_connection()

    activities = []

    try:
        # Get recent applications
        rows = conn.execute("""
            SELECT
                ga.id,
                ga.user_id,
                ga.current_stage,
                ga.status,
                ga.updated_at,
                u.full_name
            FROM grant_applications ga
            LEFT JOIN users u ON ga.user_id = u.id
            ORDER BY ga.updated_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

        for row in rows:
            activities.append({
                'id': row[0],
                'user_id': row[1],
                'user_name': row[5] or 'Unknown',
                'stage': row[2],
                'status': row[3],
                'timestamp': row[4]
            })

    except Exception as e:
        st.error(f"Error fetching activity: {e}")

    return activities


@st.cache_data(ttl=60)
def get_system_health() -> Dict[str, Any]:
    """Check system health status"""
    health = {
        'database': False,
        'telegram_bot': 'unknown',
        'gigachat_api': 'unknown'
    }

    try:
        # Check database
        conn = get_db_connection()
        conn.execute("SELECT 1").fetchone()
        health['database'] = True
    except:
        health['database'] = False

    # TODO: Add actual checks for Telegram bot and GigaChat API
    # For now, returning 'unknown'

    return health


# =============================================================================
# UI COMPONENTS
# =============================================================================

def get_stage_emoji(stage: str) -> str:
    """Get emoji for pipeline stage"""
    stage_emoji = "📊"
    emojis = {
        'Interview': '📝',
        'Audit Pending': '⏳',
        'Audit': '✅',
        'Planning': '📐',
        'Research': '🔍',
        'Writing': '✍️',
        'Delivered': '📤'
    }
    return emojis.get(stage, '❓')


def get_stage_color(stage: str) -> str:
    """Get color for pipeline stage"""
    colors = {
        'Interview': '#FFA500',
        'Audit Pending': '#FFD700',
        'Audit': '#4CAF50',
        'Planning': '#2196F3',
        'Research': '#9C27B0',
        'Writing': '#FF5722',
        'Delivered': '#00BCD4'
    }
    return colors.get(stage, '#808080')


def render_pipeline_view():
    """Render Pipeline View tab - full 6-stage pipeline"""

    # Header with refresh button
    col1, col2 = st.columns([6, 1])
    with col1:
        header_emoji = "📊"
        st.markdown(f"### {header_emoji} Pipeline Dashboard")
        st.markdown("6-этапный пайплайн обработки заявок")
    with col2:
        refresh_emoji = "🔄"
        if st.button(f"{refresh_emoji} Обновить", key="pipeline_refresh"):
            st.cache_data.clear()
            st.rerun()

    # Get pipeline overview
    overview = get_pipeline_overview()

    # Stage 1: Interview
    interview_total = overview['interview_in_progress'] + overview['interview_completed']

    # Stage 2: Audit
    audit_total = overview['audit_pending'] + overview['audit_approved'] + overview['audit_needs_revision']

    # Stage 3: Planning
    planning_total = overview['planning_done']

    # Stage 4: Research
    research_total = overview['research_completed'] + overview['research_processing']

    # Stage 5: Writing
    writing_total = overview['writing_completed'] + overview['writing_draft']

    # Stage 6: Delivery
    delivery_total = overview['delivered']

    # Calculate total
    total_in_pipeline = (interview_total + audit_total + planning_total +
                        research_total + writing_total + delivery_total)

    # Display 6 pipeline stage cards
    col1, col2, col3 = st.columns(3)

    with col1:
        interview_icon = "📝"
        st.metric(
            label=f"{interview_icon} Interview",
            value=interview_total,
            delta=f"{overview['interview_completed']} completed"
        )

    with col2:
        audit_icon = "✅"
        st.metric(
            label=f"{audit_icon} Audit",
            value=audit_total,
            delta=f"{overview['audit_approved']} approved"
        )

    with col3:
        planning_icon = "📐"
        st.metric(
            label=f"{planning_icon} Planning",
            value=planning_total,
            delta=f"{overview['planning_incomplete']} incomplete"
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        research_icon = "🔍"
        st.metric(
            label=f"{research_icon} Research",
            value=research_total,
            delta=f"{overview['research_completed']} completed"
        )

    with col5:
        writing_icon = "✍️"
        st.metric(
            label=f"{writing_icon} Writing",
            value=writing_total,
            delta=f"{overview['writing_completed']} completed"
        )

    with col6:
        delivery_icon = "📤"
        st.metric(
            label=f"{delivery_icon} Delivered",
            value=delivery_total,
            delta=None
        )

    st.markdown("---")

    # Conversion funnel
    funnel_emoji = "📈"
    st.markdown(f"#### {funnel_emoji} Воронка конверсии")

    funnel = get_conversion_funnel()

    # Create funnel dataframe
    stages = ['Started', 'Interview', 'Audited', 'Approved', 'Planned', 'Researched', 'Written', 'Delivered']
    counts = [
        funnel['started'],
        funnel['completed_interview'],
        funnel['audited'],
        funnel['approved'],
        funnel['planned'],
        funnel['researched'],
        funnel['written'],
        funnel['delivered']
    ]

    # Calculate conversion rates
    conversions = []
    for i in range(1, len(counts)):
        if counts[i-1] > 0:
            conv_rate = (counts[i] / counts[i-1]) * 100
            conversions.append(f"{conv_rate:.1f}%")
        else:
            conversions.append("N/A")

    # Display funnel table
    df_funnel = pd.DataFrame({
        'Stage': stages[1:],
        'Count': counts[1:],
        'Conversion': conversions
    })

    st.dataframe(df_funnel, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Filters
    filter_emoji = "🔍"
    st.markdown(f"#### {filter_emoji} Фильтры и поиск")

    col1, col2, col3 = st.columns(3)

    with col1:
        stages_list = ['Все', 'Interview', 'Audit Pending', 'Audit', 'Planning', 'Research', 'Writing', 'Delivered']
        selected_stage = st.selectbox(
            "Этап пайплайна",
            options=stages_list,
            key="pipeline_stage_filter"
        )

    with col2:
        period = st.selectbox(
            "Период",
            options=['За последние 30 дней', 'За последние 7 дней', 'За последние 14 дней', 'За сегодня'],
            key="pipeline_period_filter"
        )

    with col3:
        sort_by = st.selectbox(
            "Сортировка",
            options=['Последняя активность', 'Дата создания', 'Оценка Auditor'],
            key="pipeline_sort_filter"
        )

    st.markdown("---")

    # Applications list
    list_emoji = "📋"
    filter_text = selected_stage if selected_stage != 'Все' else 'Все этапы'
    st.markdown(f"#### {list_emoji} Активные заявки: {filter_text}")

    # Fetch applications
    df_apps = get_active_applications(stage_filter=selected_stage, limit=50)

    # Apply stage filter
    if selected_stage != 'Все':
        df_apps = df_apps[df_apps['current_stage'] == selected_stage]

    # Render applications
    if df_apps.empty:
        empty_emoji = "📭"
        st.info(f"{empty_emoji} Нет активных заявок за выбранный период")
    else:
        # Display count
        count_emoji = "🔢"
        st.caption(f"{count_emoji} Найдено заявок: {len(df_apps)}")

        # Render each application
        for idx, row in df_apps.iterrows():
            project_name = row['project_name'] if row['project_name'] else 'Без названия'
            anketa_id = row['anketa_id'] if row['anketa_id'] else f"Session {row['session_id']}"

            with st.expander(
                f"{get_stage_emoji(row['current_stage'])} {anketa_id} - {project_name} ({row['current_stage']})"
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    user_emoji = "👤"
                    username = row['username'] if row['username'] else 'unknown'
                    first_name = row['first_name'] if row['first_name'] else ''
                    last_name = row['last_name'] if row['last_name'] else ''
                    st.write(f"{user_emoji} **Пользователь:** @{username} ({first_name} {last_name})")

                    calendar_emoji = "📅"
                    st.write(f"{calendar_emoji} **Начало:** {row['started_at']}")
                    st.write(f"**Последняя активность:** {row['last_activity']}")

                    if row['audit_score']:
                        score_emoji = "⭐"
                        st.write(f"{score_emoji} **Оценка Auditor:** {row['audit_score']:.1f}/10 ({row['audit_status']})")

                    if row['quality_score']:
                        quality_emoji = "💎"
                        st.write(f"{quality_emoji} **Оценка качества гранта:** {row['quality_score']}/10")

                with col2:
                    st.write("**Текущий этап:**")
                    stage_color = get_stage_color(row['current_stage'])
                    stage_emoji = get_stage_emoji(row['current_stage'])
                    st.markdown(
                        f"<div style='background-color: {stage_color}; "
                        f"color: white; padding: 10px; border-radius: 5px; text-align: center;'>"
                        f"{stage_emoji} {row['current_stage']}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                    st.markdown("")

                    # Action buttons based on stage
                    if row['current_stage'] == 'Audit Pending' and not row['audit_id']:
                        play_emoji = "▶️"
                        if st.button(f"{play_emoji} Запустить Auditor", key=f"audit_{row['session_id']}"):
                            st.info(f"Запуск Auditor Agent для session_id={row['session_id']}")
                            st.info("MVP: Интеграция с агентами в разработке")

                    elif row['current_stage'] == 'Audit' and row['audit_status'] == 'approved' and not row['planner_id']:
                        play_emoji = "▶️"
                        if st.button(f"{play_emoji} Запустить Planner", key=f"plan_{row['session_id']}"):
                            st.info(f"Запуск Planner Agent для audit_id={row['audit_id']}")
                            st.info("MVP: Интеграция с агентами в разработке")

                    elif row['current_stage'] == 'Planning' and row['data_mapping_complete'] and not row['research_id']:
                        play_emoji = "▶️"
                        if st.button(f"{play_emoji} Запустить Researcher", key=f"research_{row['session_id']}"):
                            st.info(f"Запуск Researcher Agent для planner_id={row['planner_id']}")
                            st.info("MVP: Интеграция с агентами в разработке")

                    elif row['current_stage'] == 'Research' and row['research_status'] == 'completed' and not row['grant_id']:
                        play_emoji = "▶️"
                        if st.button(f"{play_emoji} Запустить Writer", key=f"write_{row['session_id']}"):
                            st.info(f"Запуск Writer Agent для research_id={row['research_id']}")
                            st.info("MVP: Интеграция с агентами в разработке")

                    # View details button
                    eye_emoji = "👁️"
                    if st.button(f"{eye_emoji} Просмотр", key=f"view_{row['session_id']}"):
                        st.info(f"Переход на страницу просмотра {anketa_id}")

    # Footer
    st.markdown("---")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    clock_emoji = "🕒"
    st.caption(f"{clock_emoji} Последнее обновление: {timestamp}")
    st.caption("Pipeline Dashboard v2.0.0 | Integrated from 🏠 Главная + 🎯 Pipeline Dashboard")


def render_system_tab():
    """Render System Health tab with full monitoring"""

    health_emoji = "💚"
    st.markdown(f"### {health_emoji} Здоровье системы")

    # Get system health
    health = get_system_health()

    # Display health status with detailed checks
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### База данных")
        if health['database']:
            success_emoji = "✅"
            st.success(f"{success_emoji} Работает")
            try:
                conn = get_db_connection()
                tables_count = len(conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall())
                st.info(f"Таблиц: {tables_count}")
            except:
                pass
        else:
            error_emoji = "❌"
            st.error(f"{error_emoji} Недоступна")

    with col2:
        st.markdown("#### Telegram Bot")
        try:
            import os
            import requests

            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if bot_token:
                response = requests.get(
                    f"https://api.telegram.org/bot{bot_token}/getMe",
                    timeout=5
                )
                if response.status_code == 200:
                    success_emoji = "✅"
                    st.success(f"{success_emoji} Работает")
                    bot_info = response.json()['result']
                    st.info(f"@{bot_info['username']}")
                else:
                    error_emoji = "❌"
                    st.error(f"{error_emoji} Не отвечает")
            else:
                warning_emoji = "⚠️"
                st.warning(f"{warning_emoji} Токен не настроен")
        except requests.exceptions.Timeout:
            timeout_emoji = "⏱️"
            st.error(f"{timeout_emoji} Таймаут (>5 сек)")
        except Exception as e:
            error_emoji = "❌"
            st.error(f"{error_emoji} Ошибка подключения")

    with col3:
        st.markdown("#### GigaChat API")
        unknown_emoji = "🔄"
        st.info(f"{unknown_emoji} Проверка не реализована")
        st.caption("TODO: Добавить проверку API")

    st.markdown("---")

    # Quick metrics
    metrics_emoji = "📊"
    st.markdown(f"### {metrics_emoji} Быстрые метрики")

    metrics = get_dashboard_metrics()

    # Display metrics in cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        users_emoji = "👥"
        st.metric(
            label=f"{users_emoji} Всего пользователей",
            value=metrics['total_users'],
            delta=f"+{metrics['active_today']} сегодня" if metrics['active_today'] > 0 else None
        )

    with col2:
        active_emoji = "📈"
        st.metric(
            label=f"{active_emoji} Активных за 7 дней",
            value=metrics['active_users_7d']
        )

    with col3:
        apps_emoji = "📋"
        st.metric(
            label=f"{apps_emoji} Всего заявок",
            value=metrics['total_applications'],
            delta=f"{metrics['applications_in_progress']} в работе"
        )

    with col4:
        grants_emoji = "✅"
        st.metric(
            label=f"{grants_emoji} Завершенных грантов",
            value=metrics['completed_grants'],
            delta=f"{metrics['completion_rate']:.1f}% completion"
        )

    st.markdown("---")

    # System info
    info_emoji = "ℹ️"
    st.markdown(f"### {info_emoji} Системная информация")

    col1, col2, col3 = st.columns(3)

    with col1:
        version_emoji = "🔢"
        st.info(f"{version_emoji} **Версия:** 2.0.0")
        date_emoji = "📅"
        st.info(f"{date_emoji} **Дата:** {datetime.now().strftime('%d.%m.%Y')}")

    with col2:
        time_emoji = "🕒"
        st.info(f"{time_emoji} **Время:** {datetime.now().strftime('%H:%M:%S')}")
        status_emoji = "🟢"
        st.info(f"{status_emoji} **Статус:** Активен")

    with col3:
        developer_emoji = "👨‍💻"
        st.info(f"{developer_emoji} **Разработчик:** Андрей Отинов")
        domain_emoji = "🌐"
        st.info(f"{domain_emoji} **Домен:** grantservice.onff.ru")

    st.markdown("---")

    # Environment info
    env_emoji = "🖥️"
    st.markdown(f"### {env_emoji} Окружение")

    try:
        import platform
        import sys

        env_info = {
            'Python': sys.version.split()[0],
            'Platform': platform.system(),
            'Architecture': platform.machine(),
            'Streamlit': st.__version__
        }

        cols = st.columns(4)
        for idx, (key, value) in enumerate(env_info.items()):
            with cols[idx]:
                st.metric(label=key, value=value)

    except Exception as e:
        st.error(f"Ошибка получения информации об окружении: {e}")


def render_activity_tab():
    """Render Recent Activity tab"""

    activity_emoji = "🕐"
    st.markdown(f"### {activity_emoji} Последняя активность")

    # Get recent activity
    activities = get_recent_activity(limit=20)

    if not activities:
        st.info("Нет активности за последнее время")
        return

    # Display activity list
    for activity in activities:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                user_emoji = "👤"
                st.markdown(f"{user_emoji} **{activity['user_name']}**")

            with col2:
                st.markdown(f"Этап: **{activity['stage']}**")

            with col3:
                render_status_badge(activity['status'])

            with col4:
                try:
                    timestamp = datetime.fromisoformat(activity['timestamp'])
                    time_str = timestamp.strftime("%d.%m.%Y %H:%M")
                    st.markdown(f"🕒 {time_str}")
                except:
                    st.markdown(f"🕒 {activity['timestamp']}")

            st.markdown("---")


# =============================================================================
# MAIN PAGE
# =============================================================================

def main():
    """Main page function"""

    # Page header
    render_page_header(
        title="Dashboard",
        icon="🎯",
        description="Главная панель управления GrantService"
    )

    # Get metrics for header cards
    metrics = get_dashboard_metrics()

    # Display header metrics
    header_metrics = [
        {
            'label': 'Пользователей',
            'value': metrics['total_users'],
            'delta': f"+{metrics['active_today']} сегодня",
            'icon': '👥'
        },
        {
            'label': 'Заявок в работе',
            'value': metrics['applications_in_progress'],
            'icon': '📋'
        },
        {
            'label': 'Готовых грантов',
            'value': metrics['completed_grants'],
            'icon': '✅'
        },
        {
            'label': 'Процент завершения',
            'value': f"{metrics['completion_rate']:.1f}%",
            'icon': '📈'
        }
    ]

    render_metric_cards(header_metrics, columns=4)

    st.markdown("---")

    # Tabs
    tab_names = ["Pipeline View", "Система", "Активность"]
    tab_icons = ["📊", "💚", "🕐"]

    selected_tab = render_tabs(tab_names, icons=tab_icons)

    if selected_tab == "Pipeline View":
        render_pipeline_view()
    elif selected_tab == "Система":
        render_system_tab()
    elif selected_tab == "Активность":
        render_activity_tab()


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    main()
