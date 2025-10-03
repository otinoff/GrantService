"""
Pipeline Dashboard - Main Working Page for Grant Service Admin
=================================================================

This page provides a comprehensive view of all grant applications
moving through the 6-stage pipeline:
1. Interview (24 questions)
2. Auditor (quality assessment)
3. Planner (structure generation)
4. Researcher (data enrichment)
5. Writer (grant text generation)
6. Delivery (send to user)

Author: Grant Architect Agent
Date: 2025-10-01
Version: 1.0.0 (MVP)
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path

# =============================================================================
# AUTHENTICATION
# =============================================================================

try:
    from utils.auth import is_user_authorized
    if not is_user_authorized():
        st.error("⛔ Не авторизован. Перейдите на страницу 🔐 Вход")
        st.stop()
except ImportError as e:
    st.error(f"❌ Ошибка импорта модуля авторизации: {e}")
    st.stop()

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

@st.cache_resource
def get_db_connection():
    """Establish database connection"""
    db_path = Path(__file__).parent.parent.parent / "data" / "grantservice.db"
    return sqlite3.connect(str(db_path), check_same_thread=False)

# =============================================================================
# DATA FETCHING FUNCTIONS
# =============================================================================

def get_pipeline_overview():
    """Get counts for each pipeline stage"""
    conn = get_db_connection()

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

    df = pd.read_sql_query(query, conn)
    return df.iloc[0].to_dict()

def get_active_applications():
    """Get all active applications with their current stage"""
    conn = get_db_connection()

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
    LIMIT 50
    """

    df = pd.read_sql_query(query, conn)
    return df

def get_conversion_funnel():
    """Calculate conversion rates between stages"""
    conn = get_db_connection()

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

    df = pd.read_sql_query(query, conn)
    return df.iloc[0].to_dict()

# =============================================================================
# ACTION FUNCTIONS
# =============================================================================

def trigger_audit(session_id):
    """Trigger auditor agent for a completed interview"""
    # TODO: Implement actual auditor trigger
    # For now, just show a message
    st.info(f"🚀 Запуск Auditor Agent для session_id={session_id}")
    st.info("⚠️ MVP: Интеграция с агентами в разработке")

def trigger_planner(audit_id):
    """Trigger planner agent for approved audit"""
    st.info(f"🚀 Запуск Planner Agent для audit_id={audit_id}")
    st.info("⚠️ MVP: Интеграция с агентами в разработке")

def trigger_researcher(planner_id):
    """Trigger researcher agent for completed plan"""
    st.info(f"🚀 Запуск Researcher Agent для planner_id={planner_id}")
    st.info("⚠️ MVP: Интеграция с агентами в разработке")

def trigger_writer(research_id):
    """Trigger writer agent for completed research"""
    st.info(f"🚀 Запуск Writer Agent для research_id={research_id}")
    st.info("⚠️ MVP: Интеграция с агентами в разработке")

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_pipeline_overview_cards(overview):
    """Render overview cards for each pipeline stage"""

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="📝 Interview",
            value=overview['interview_in_progress'],
            delta=f"+{overview['interview_completed']} completed"
        )

    with col2:
        st.metric(
            label="✅ Audit",
            value=overview['audit_approved'],
            delta=f"{overview['audit_needs_revision']} need revision"
        )

    with col3:
        st.metric(
            label="📐 Planning",
            value=overview['planning_done'],
            delta=f"{overview['planning_incomplete']} incomplete"
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            label="🔍 Research",
            value=overview['research_completed'],
            delta=f"{overview['research_processing']} processing"
        )

    with col5:
        st.metric(
            label="✍️ Writing",
            value=overview['writing_completed'],
            delta=f"{overview['writing_draft']} draft"
        )

    with col6:
        st.metric(
            label="📤 Delivered",
            value=overview['delivered'],
            delta=None
        )

def render_conversion_funnel(funnel):
    """Render conversion funnel chart"""

    stages = ['Started', 'Interview', 'Audit', 'Approved', 'Planned', 'Research', 'Written', 'Delivered']
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
            conv = (counts[i] / counts[i-1]) * 100
            conversions.append(f"{conv:.1f}%")
        else:
            conversions.append("N/A")

    # Create dataframe
    df_funnel = pd.DataFrame({
        'Stage': stages[1:],
        'Count': counts[1:],
        'Conversion': conversions
    })

    st.dataframe(df_funnel, use_container_width=True)

def get_stage_emoji(stage):
    """Get emoji for pipeline stage"""
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

def get_stage_color(stage):
    """Get color for pipeline stage"""
    colors = {
        'Interview': '#FFA500',        # Orange
        'Audit Pending': '#FFD700',    # Gold
        'Audit': '#4CAF50',            # Green
        'Planning': '#2196F3',         # Blue
        'Research': '#9C27B0',         # Purple
        'Writing': '#FF5722',          # Deep Orange
        'Delivered': '#00BCD4'         # Cyan
    }
    return colors.get(stage, '#808080')

def render_applications_table(df):
    """Render table of active applications with actions"""

    if df.empty:
        st.info("📭 Нет активных заявок за последние 30 дней")
        return

    for idx, row in df.iterrows():
        with st.expander(
            f"{get_stage_emoji(row['current_stage'])} {row['anketa_id']} - {row['project_name'] or 'Без названия'} ({row['current_stage']})"
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**Пользователь:** @{row['username'] or 'unknown'} ({row['first_name']} {row['last_name']})")
                st.write(f"**Начало:** {row['started_at']}")
                st.write(f"**Последняя активность:** {row['last_activity']}")

                if row['audit_score']:
                    st.write(f"**Оценка Auditor:** {row['audit_score']:.1f}/10 ({row['audit_status']})")

                if row['quality_score']:
                    st.write(f"**Оценка качества гранта:** {row['quality_score']}/10")

            with col2:
                st.write(f"**Текущий этап:**")
                st.markdown(
                    f"<div style='background-color: {get_stage_color(row['current_stage'])}; "
                    f"color: white; padding: 10px; border-radius: 5px; text-align: center;'>"
                    f"{get_stage_emoji(row['current_stage'])} {row['current_stage']}"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # Action buttons based on current stage
                if row['current_stage'] == 'Audit Pending' and row['audit_id'] is None:
                    if st.button(f"▶️ Запустить Auditor", key=f"audit_{row['session_id']}"):
                        trigger_audit(row['session_id'])

                elif row['current_stage'] == 'Audit' and row['audit_status'] == 'approved' and row['planner_id'] is None:
                    if st.button(f"▶️ Запустить Planner", key=f"plan_{row['session_id']}"):
                        trigger_planner(row['audit_id'])

                elif row['current_stage'] == 'Planning' and row['data_mapping_complete'] and row['research_id'] is None:
                    if st.button(f"▶️ Запустить Researcher", key=f"research_{row['session_id']}"):
                        trigger_researcher(row['planner_id'])

                elif row['current_stage'] == 'Research' and row['research_status'] == 'completed' and row['grant_id'] is None:
                    if st.button(f"▶️ Запустить Writer", key=f"write_{row['session_id']}"):
                        trigger_writer(row['research_id'])

                # View details button
                if st.button(f"👁️ Просмотр", key=f"view_{row['session_id']}"):
                    st.info(f"Переход на страницу просмотра {row['anketa_id']}")

# =============================================================================
# MAIN PAGE
# =============================================================================

def main():
    st.set_page_config(
        page_title="Pipeline Dashboard - GrantService",
        page_icon="🎯",
        layout="wide"
    )

    st.title("🎯 Pipeline Dashboard")
    st.markdown("**Главный рабочий экран администратора**")
    st.markdown("---")

    # Refresh button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Обновить"):
            st.rerun()

    # Overview Cards
    st.subheader("📊 Обзор по этапам (последние 30 дней)")
    overview = get_pipeline_overview()
    render_pipeline_overview_cards(overview)

    st.markdown("---")

    # Conversion Funnel
    st.subheader("📈 Воронка конверсии")
    funnel = get_conversion_funnel()
    render_conversion_funnel(funnel)

    st.markdown("---")

    # Active Applications
    st.subheader("📋 Активные заявки")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        stage_filter = st.selectbox(
            "Фильтр по этапу",
            ['Все', 'Interview', 'Audit Pending', 'Audit', 'Planning', 'Research', 'Writing', 'Delivered']
        )

    with col2:
        days_filter = st.selectbox(
            "Период",
            [7, 14, 30, 60, 90],
            index=2
        )

    with col3:
        sort_by = st.selectbox(
            "Сортировка",
            ['Последняя активность', 'Дата создания', 'Оценка Auditor']
        )

    # Fetch and filter applications
    df_apps = get_active_applications()

    if stage_filter != 'Все':
        df_apps = df_apps[df_apps['current_stage'] == stage_filter]

    # Render table
    render_applications_table(df_apps)

    # Footer
    st.markdown("---")
    st.caption(f"Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("MVP версия 1.0.0 | Hardcoded Interview Questions")

if __name__ == "__main__":
    main()
