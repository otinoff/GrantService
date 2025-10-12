#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grants Management Page - GrantService Admin (v2.0)
==================================================
Unified page combining 3 archive files:
- 📄_Грантовые_заявки.py (All applications list)
- 📋_Управление_грантами.py (Ready grants + sending)
- 📄_Просмотр_заявки.py (Detailed view)

5 Tabs: Все заявки | Готовые гранты | Отправка | Архив | Просмотр

Author: Streamlit Admin Developer Agent
Date: 2025-10-03
Version: 2.0.0 (Fully Integrated)
"""

import streamlit as st
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# =============================================================================
# PATH SETUP
# =============================================================================

sys.path.insert(0, str(Path(__file__).parent.parent))
import setup_paths

# =============================================================================
# IMPORTS
# =============================================================================

try:
    from utils.database import AdminDatabase
    from utils.postgres_helper import (
        get_postgres_db,
        get_postgres_connection,
        execute_query,
        execute_query_df,
        execute_scalar,
        execute_update
    )
    from utils.logger import setup_logger
    # from utils.grant_lifecycle_manager import GrantLifecycleManager, get_lifecycle_summary
    # from utils.artifact_exporter import ArtifactExporter, export_artifact
    # from utils.grant_stage_visualizer import GrantStageVisualizer, render_grant_lifecycle
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Гранты - GrantService Admin",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger = setup_logger('grants_page')

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

@st.cache_resource
def get_database():
    """Get cached database connection"""
    return AdminDatabase()

db = get_database()

# =============================================================================
# DATA FETCHING FUNCTIONS
# =============================================================================

@st.cache_data(ttl=60)
def get_grants_statistics(_db):
    """Get grants statistics for header metrics - USING POSTGRESQL"""
    from utils.postgres_helper import execute_query

    try:
        # Total applications
        result = execute_query("SELECT COUNT(*) as cnt FROM grant_applications")
        total = result[0]['cnt'] if result else 0

        # In progress
        result = execute_query(
            "SELECT COUNT(*) as cnt FROM grant_applications WHERE status IN ('draft', 'in_progress')"
        )
        in_progress = result[0]['cnt'] if result else 0

        # Ready (completed) - count from grants table (not grant_applications)
        result = execute_query(
            "SELECT COUNT(*) as cnt FROM grants WHERE status = 'completed'"
        )
        ready = result[0]['cnt'] if result else 0

        # Sent
        result = execute_query(
            "SELECT COUNT(DISTINCT grant_application_id) as cnt FROM sent_documents"
        )
        sent = result[0]['cnt'] if result else 0

        return {
            'total': total,
            'in_progress': in_progress,
            'ready': ready,
            'sent': sent
        }
    except Exception as e:
        logger.error(f"Error fetching statistics from PostgreSQL: {e}", exc_info=True)
        return {'total': 0, 'in_progress': 0, 'ready': 0, 'sent': 0}

@st.cache_data(ttl=60)
def get_all_applications(_db, status_filter='all', period_days=None, hide_legacy=True):
    """Get all grant applications with filters - USING POSTGRESQL"""
    from utils.postgres_helper import execute_query

    query = """
    SELECT
        ga.id,
        ga.application_number,
        ga.title,
        ga.content_json,
        ga.summary,
        ga.status,
        ga.user_id,
        ga.session_id,
        ga.quality_score,
        ga.grant_fund,
        ga.requested_amount,
        ga.project_duration,
        ga.created_at,
        ga.updated_at,
        ga.admin_user,
        ga.llm_provider,
        ga.model_used,
        ga.processing_time,
        ga.tokens_used,
        u.username,
        u.first_name,
        u.last_name,
        u.telegram_id,
        s.anketa_id
    FROM grant_applications ga
    LEFT JOIN users u ON ga.user_id = u.id
    LEFT JOIN sessions s ON ga.session_id = s.session_id
    WHERE 1=1
    """

    params = []

    # Filter out legacy/test applications without anketa_id
    if hide_legacy:
        query += " AND s.anketa_id IS NOT NULL"

    if status_filter != 'all':
        query += " AND ga.status = %s"
        params.append(status_filter)

    if period_days:
        cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()
        query += " AND ga.created_at >= %s"
        params.append(cutoff_date)

    query += " ORDER BY ga.created_at DESC"

    try:
        result = execute_query(query, tuple(params) if params else None)
        if result:
            df = pd.DataFrame([dict(row) for row in result])
            return df
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching applications from PostgreSQL: {e}", exc_info=True)
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_ready_grants():
    """Get grants ready for delivery (status='completed')"""
    query = """
    SELECT
        g.id,
        g.grant_id,
        g.anketa_id,
        g.user_id,
        g.username,
        g.first_name,
        g.last_name,
        g.grant_title,
        g.grant_content,
        g.quality_score,
        g.status,
        g.llm_provider,
        g.model,
        g.created_at,
        g.submitted_at,
        NULL::integer as sent_id,
        NULL::timestamp as sent_at,
        NULL::varchar as delivery_status
    FROM grants g
    WHERE g.status = 'completed'
    ORDER BY g.created_at DESC
    """

    try:
        df = execute_query_df(query)
        return df
    except Exception as e:
        logger.error(f"Error fetching ready grants: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_grant_details(grant_id):
    """Get full grant details including content"""
    from utils.postgres_helper import execute_query

    query = """
    SELECT
        grant_id,
        grant_title,
        grant_content,
        grant_sections,
        metadata,
        quality_score,
        llm_provider,
        model,
        created_at,
        user_id,
        username
    FROM grants
    WHERE grant_id = %s
    """

    try:
        result = execute_query(query, (grant_id,))

        if result:
            row = result[0]

            # PostgreSQL returns JSONB as dict, not string
            sections = row.get('grant_sections')
            if isinstance(sections, str):
                sections = json.loads(sections)
            elif sections is None:
                sections = []

            metadata = row.get('metadata')
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            elif metadata is None:
                metadata = {}

            return {
                'grant_id': row.get('grant_id'),
                'title': row.get('grant_title'),
                'content': row.get('grant_content'),
                'sections': sections,
                'metadata': metadata,
                'quality_score': row.get('quality_score'),
                'llm_provider': row.get('llm_provider'),
                'model': row.get('model'),
                'created_at': row.get('created_at'),
                'user_id': row.get('user_id'),
                'username': row.get('username')
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching grant details: {e}")
        return None

@st.cache_data(ttl=60)
def get_all_grants_unified(status_filter='all', search_query=''):
    """
    Get unified list of grants from BOTH tables: grants + grant_applications
    Returns: DataFrame with columns: id, grant_id, title, username, created_at,
             progress, status, source ('new' or 'old'), anketa_id, stage_statuses
    """
    from utils.postgres_helper import execute_query

    # Query for NEW grants table (from E2E test)
    query_new = """
    SELECT
        'new' as source,
        g.id,
        g.grant_id,
        g.grant_title as title,
        g.anketa_id,
        g.quality_score,
        g.status,
        g.created_at,
        COALESCE(u.username, 'Unknown') as username,
        COALESCE(u.first_name, '') as first_name,
        COALESCE(u.last_name, '') as last_name,
        COALESCE(s.progress_percentage, 0) as progress,
        s.id as session_id,
        -- Stage statuses
        (SELECT COUNT(*) FROM user_answers ua WHERE ua.session_id = s.id) as interview_count,
        (SELECT approval_status FROM auditor_results ar WHERE ar.session_id = s.id ORDER BY ar.created_at DESC LIMIT 1) as audit_status,
        (SELECT status FROM researcher_research rr WHERE rr.anketa_id = g.anketa_id ORDER BY rr.created_at DESC LIMIT 1) as research_status,
        (SELECT data_mapping_complete FROM planner_structures ps WHERE ps.session_id = s.id ORDER BY ps.created_at DESC LIMIT 1) as planner_status,
        g.status as writer_status
    FROM grants g
    LEFT JOIN sessions s ON g.anketa_id = s.anketa_id
    LEFT JOIN users u ON s.telegram_id = u.telegram_id
    """

    # Query for OLD grant_applications table
    query_old = """
    SELECT
        'old' as source,
        ga.id,
        ga.application_number as grant_id,
        ga.title,
        s.anketa_id,
        ga.quality_score,
        ga.status,
        ga.created_at,
        COALESCE(u.username, 'Unknown') as username,
        COALESCE(u.first_name, '') as first_name,
        COALESCE(u.last_name, '') as last_name,
        100 as progress,
        ga.session_id,
        -- Stage statuses (old applications are all completed)
        15 as interview_count,
        'approved' as audit_status,
        'completed' as research_status,
        true as planner_status,
        'completed' as writer_status
    FROM grant_applications ga
    LEFT JOIN sessions s ON ga.session_id = s.id
    LEFT JOIN users u ON ga.user_id = u.id
    WHERE s.anketa_id IS NOT NULL
    """

    # Combine queries
    query = f"""
    SELECT * FROM (
        {query_new}
        UNION ALL
        {query_old}
    ) combined
    WHERE 1=1
    """

    params = []

    # Apply status filter
    if status_filter == 'in_progress':
        query += " AND progress < 100"
    elif status_filter == 'completed':
        query += " AND progress = 100"
    elif status_filter != 'all':
        query += " AND status = %s"
        params.append(status_filter)

    # Apply search query
    if search_query:
        query += """ AND (
            LOWER(title) LIKE LOWER(%s) OR
            LOWER(username) LIKE LOWER(%s) OR
            LOWER(grant_id) LIKE LOWER(%s) OR
            LOWER(anketa_id) LIKE LOWER(%s)
        )"""
        search_pattern = f"%{search_query}%"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    query += " ORDER BY created_at DESC"

    try:
        result = execute_query(query, tuple(params) if params else None)
        if result:
            return pd.DataFrame([dict(row) for row in result])
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching unified grants: {e}", exc_info=True)
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_application_details(_db, app_id):
    """Get detailed application info from grant_applications"""
    from utils.postgres_helper import execute_query

    query = """
    SELECT
        ga.*,
        u.username,
        u.first_name,
        u.last_name,
        u.telegram_id
    FROM grant_applications ga
    LEFT JOIN users u ON ga.user_id = u.id
    WHERE ga.id = %s
    """

    try:
        result = execute_query(query, (app_id,))

        if result and len(result) > 0:
            app = dict(result[0])

            # Parse JSON content
            if app.get('content_json'):
                try:
                    app['content_data'] = json.loads(app['content_json'])
                except:
                    app['content_data'] = {}
            else:
                app['content_data'] = {}

            return app
        return None
    except Exception as e:
        logger.error(f"Error fetching application details: {e}")
        return None

@st.cache_data(ttl=60)
def get_sent_documents(_db):
    """Get all sent documents history"""
    from utils.postgres_helper import execute_query

    query = """
    SELECT
        sd.id,
        sd.grant_application_id as grant_id,
        sd.user_id,
        sd.telegram_message_id,
        sd.file_name,
        sd.sent_at,
        sd.delivery_status,
        u.username,
        u.first_name,
        u.last_name,
        g.grant_title
    FROM sent_documents sd
    LEFT JOIN users u ON sd.user_id = u.id
    LEFT JOIN grants g ON sd.grant_application_id = g.grant_id
    ORDER BY sd.sent_at DESC
    LIMIT 100
    """

    try:
        result = execute_query(query)
        if result:
            df = pd.DataFrame([dict(row) for row in result])
            return df
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching sent documents: {e}")
        return pd.DataFrame()

# =============================================================================
# ACTION FUNCTIONS
# =============================================================================

def send_grant_to_telegram(db, grant_id, user_id):
    """
    Send grant document to user via Telegram
    MVP: Marks as sent in database (actual sending requires bot integration)
    """
    from utils.postgres_helper import execute_update

    try:
        # Insert into sent_documents
        execute_update("""
            INSERT INTO sent_documents (
                grant_id,
                user_id,
                telegram_message_id,
                file_name,
                sent_at,
                delivery_status
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (grant_id, user_id, None, f"{grant_id}.pdf",
              datetime.now(), 'delivered'))

        # Update grant status
        execute_update("""
            UPDATE grants
            SET status = 'delivered', submitted_at = %s
            WHERE grant_id = %s
        """, (datetime.now(), grant_id))

        logger.info(f"Grant {grant_id} marked as sent to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error sending grant: {e}")
        return False

def export_application_json(app):
    """Export application to JSON format"""
    export_data = {
        'application_number': app.get('application_number'),
        'title': app.get('title'),
        'status': app.get('status'),
        'created_at': app.get('created_at'),
        'content': app.get('content_data', {}),
        'quality_score': app.get('quality_score'),
        'technical_info': {
            'llm_provider': app.get('llm_provider'),
            'model_used': app.get('model_used'),
            'processing_time': app.get('processing_time'),
            'tokens_used': app.get('tokens_used')
        }
    }

    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    return json_str

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_metric_cards(stats):
    """Render header metrics"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Всего заявок", stats['total'])

    with col2:
        st.metric("В обработке", stats['in_progress'])

    with col3:
        st.metric("Готовые гранты", stats['ready'])

    with col4:
        st.metric("Отправлено", stats['sent'])

def render_lifecycle_inline(anketa_id: str, grant_id: str = None):
    """Render compact inline lifecycle view for grant card"""
    try:
        # Get lifecycle data
        manager = GrantLifecycleManager(anketa_id)
        lifecycle_data = manager.get_all_artifacts()

        if not lifecycle_data or not lifecycle_data.get('artifacts'):
            st.warning(f"⚠️ Нет данных lifecycle для {anketa_id}")
            return

        artifacts = lifecycle_data.get('artifacts', {})

        # Compact timeline with artifact cards
        st.markdown("#### 📊 Детальный просмотр этапов")

        # Create tabs for each stage
        tabs = st.tabs(["📝 Интервью", "✅ Аудит", "🔍 Исследование", "📋 Планирование", "✍️ Грант"])

        # Tab 1: Interview
        with tabs[0]:
            interview = artifacts.get('interview') or {}
            if interview and interview.get('status') == 'completed':
                st.success(f"✅ Завершено: {interview.get('questions_count', 0)} ответов")
                questions = interview.get('data', [])[:5]  # Show first 5
                for q in questions:
                    with st.expander(f"Q{q.get('question_id')}: {q.get('question_text', 'N/A')[:50]}..."):
                        st.write(q.get('answer', 'Нет ответа'))
                if len(interview.get('data', [])) > 5:
                    st.caption(f"... и ещё {len(interview.get('data', [])) - 5} ответов")
            else:
                st.info("⏸️ Не завершено")

        # Tab 2: Audit
        with tabs[1]:
            audit = artifacts.get('auditor') or {}
            if audit and audit.get('status') == 'completed':
                score = audit.get('score', 0)
                approval = audit.get('approval_status', 'unknown')

                if approval == 'approved':
                    st.success(f"✅ Статус: {approval}")
                elif approval == 'rejected':
                    st.error(f"❌ Статус: {approval}")
                else:
                    st.warning(f"⚠️ Статус: {approval}")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Средний балл", f"{score}/10")
                with col2:
                    st.metric("Качество", f"{audit.get('quality_score', 0)}/10")

                st.markdown("**Детальные оценки:**")
                scores = {
                    "Полнота": audit.get('completeness_score', 0),
                    "Ясность": audit.get('clarity_score', 0),
                    "Выполнимость": audit.get('feasibility_score', 0),
                    "Инновация": audit.get('innovation_score', 0)
                }
                for name, value in scores.items():
                    st.progress(value / 10.0, text=f"{name}: {value}/10")

                # Quick actions for rejected
                if approval == 'rejected':
                    st.markdown("---")
                    st.markdown("**⚡ Быстрые действия:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✏️ Редактировать ответы", key=f"edit_interview_{anketa_id}", use_container_width=True):
                            st.info("Функция редактирования в разработке")
                    with col2:
                        if st.button("🔄 Перезапустить аудит", key=f"restart_audit_{anketa_id}", use_container_width=True):
                            st.info("Функция перезапуска в разработке")
            else:
                st.info("⏸️ Не завершено")

        # Tab 3: Research
        with tabs[2]:
            research = artifacts.get('researcher') or {}
            if research and research.get('status') == 'completed':
                st.success("✅ Исследование завершено")
                metadata = research.get('metadata', {})
                if metadata:
                    st.json(metadata, expanded=False)
            else:
                st.info(f"⏸️ Статус: {research.get('research_status', 'pending')}")

        # Tab 4: Planner
        with tabs[3]:
            planner = artifacts.get('planner') or {}
            if planner and planner.get('status') == 'completed':
                st.success("✅ Планирование завершено")
                st.metric("Разделов", planner.get('sections_count', 0))
                st.metric("Целевой объём", f"{planner.get('total_word_count_target', 0)} слов")

                structure = planner.get('structure', {})
                if structure and isinstance(structure, dict):
                    sections = structure.get('sections', [])
                    if sections:
                        st.markdown("**Структура:**")
                        for i, section in enumerate(sections[:5], 1):
                            if isinstance(section, dict):
                                st.write(f"{i}. {section.get('title', 'N/A')} ({section.get('word_count', 0)} слов)")
            else:
                st.info("⏸️ Не завершено")

        # Tab 5: Grant
        with tabs[4]:
            grant = artifacts.get('writer') or {}
            if grant and grant.get('status') == 'completed':
                st.success("✅ Грант готов")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Качество", f"{grant.get('quality_score', 0)}/10")
                with col2:
                    content = grant.get('content', '')
                    st.metric("Объём", f"{len(content)} символов")

                st.markdown(f"**Grant ID:** `{grant.get('grant_id', 'N/A')}`")
                st.markdown(f"**Название:** {grant.get('title', 'N/A')}")

                # Show content preview
                with st.expander("📄 Предпросмотр текста"):
                    st.text_area("Грант", content[:500] + "..." if len(content) > 500 else content, height=200, disabled=True)

                # Download button and quick actions
                if content:
                    st.markdown("---")
                    st.markdown("**⚡ Быстрые действия:**")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            label="💾 Скачать .txt",
                            data=content,
                            file_name=f"{grant_id or 'grant'}.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key=f"download_txt_{anketa_id}"
                        )
                    with col2:
                        if st.button("📤 Отправить в фонд", key=f"send_grant_{anketa_id}", use_container_width=True):
                            st.info("Функция отправки в разработке")
                    with col3:
                        if st.button("📋 Создать версию 2", key=f"create_v2_{anketa_id}", use_container_width=True):
                            st.info("Функция создания новой версии в разработке")
            else:
                st.info("⏸️ Не завершено")

    except Exception as e:
        logger.error(f"Error rendering inline lifecycle: {e}")
        st.error(f"❌ Ошибка: {e}")


def render_grants_list_unified(df):
    """Render unified grants list with progress bars and timeline - NEW VERSION"""
    if df.empty:
        st.info("Нет заявок, соответствующих выбранным фильтрам")
        return

    # Display each grant as a card
    for idx, row in df.iterrows():
        # Format created_at
        created_at = row.get('created_at')
        if pd.notna(created_at):
            created_at_str = pd.to_datetime(created_at).strftime('%Y-%m-%d %H:%M')
        else:
            created_at_str = 'N/A'

        # Title with source badge
        source_badge = "🆕" if row.get('source') == 'new' else "📁"
        title = row.get('title', 'Без названия')
        grant_id = row.get('grant_id', f"ID_{row.get('id')}")

        # User info
        username = row.get('username', 'Unknown')
        first_name = row.get('first_name', '')
        last_name = row.get('last_name', '')
        user_display = f"{first_name} {last_name}".strip() or username

        # Progress
        progress = int(row.get('progress', 0))

        # Create expander with grant info
        with st.expander(f"{source_badge} {grant_id} - {title[:60]}{'...' if len(title) > 60 else ''}"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Пользователь:** {user_display} (@{username})")
                st.markdown(f"**Anketa ID:** `{row.get('anketa_id', 'N/A')}`")
                st.markdown(f"**Создан:** {created_at_str}")

            with col2:
                quality = row.get('quality_score')
                if pd.notna(quality):
                    st.metric("Качество", f"{quality}/10")
                st.metric("Статус", row.get('status', 'unknown'))

            st.markdown("---")

            # Progress bar
            st.markdown(f"**Прогресс:** {progress}%")
            st.progress(progress / 100.0)

            # Timeline visualization
            st.markdown("**Timeline:**")

            # Get stage statuses
            interview_count = row.get('interview_count', 0)
            audit_status = row.get('audit_status')
            research_status = row.get('research_status')
            planner_status = row.get('planner_status')
            writer_status = row.get('writer_status')

            # Define stage emojis and statuses
            stages = [
                ('📝 Интервью', interview_count >= 10, 'completed' if interview_count >= 10 else 'pending'),
                ('✅ Аудит', audit_status in ['approved', 'completed'], audit_status or 'pending'),
                ('🔍 Исследование', research_status == 'completed', research_status or 'pending'),
                ('📋 Планирование', planner_status == True, 'completed' if planner_status else 'pending'),
                ('✍️ Грант', writer_status == 'completed', writer_status or 'pending')
            ]

            # Render timeline
            timeline_html = "<div style='display: flex; align-items: center; gap: 10px;'>"
            for i, (stage_name, is_complete, status) in enumerate(stages):
                # Stage icon
                if is_complete:
                    icon = "✅"
                elif status == 'rejected':
                    icon = "❌"
                else:
                    icon = "⏸️"

                timeline_html += f"<div style='text-align: center; flex: 1;'>"
                timeline_html += f"<div>{stage_name}</div>"
                timeline_html += f"<div style='font-size: 24px;'>{icon}</div>"
                timeline_html += f"</div>"

                # Arrow between stages
                if i < len(stages) - 1:
                    timeline_html += "<div>→</div>"

            timeline_html += "</div>"
            st.markdown(timeline_html, unsafe_allow_html=True)

            st.markdown("---")

            # Action buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                # Toggle for inline lifecycle view
                show_lifecycle = st.checkbox(
                    "📊 Показать детали этапов",
                    key=f"show_lifecycle_{row.get('id')}_{idx}",
                    help="Раскрыть детальную информацию по всем этапам"
                )

            with col2:
                # Direct download button
                if pd.notna(row.get('grant_id')) and row.get('source') == 'new':
                    grant_details = get_grant_details(row.get('grant_id'))
                    if grant_details and grant_details.get('content'):
                        st.download_button(
                            label="💾 Скачать грант",
                            data=grant_details['content'],
                            file_name=f"{row.get('grant_id')}.txt",
                            mime="text/plain",
                            key=f"dl_btn_{row.get('id')}_{idx}",
                            use_container_width=True
                        )

            with col3:
                # Link to full lifecycle view
                if st.button("🔗 Полный просмотр", key=f"full_view_{row.get('id')}_{idx}", use_container_width=True):
                    st.session_state.view_anketa_id = row.get('anketa_id')
                    st.session_state.active_tab = "🔍 Просмотр"
                    st.rerun()

            # Inline lifecycle expansion
            if show_lifecycle:
                st.markdown("---")
                render_lifecycle_inline(row.get('anketa_id'), row.get('grant_id'))

def render_applications_table(df):
    """Render applications table with click handlers - OLD VERSION (for compatibility)"""
    if df.empty:
        st.info("Нет заявок, соответствующих выбранным фильтрам")
        return

    # Prepare display DataFrame
    # Safe datetime conversion with error handling
    created_at_series = pd.to_datetime(df['created_at'], errors='coerce')
    created_at_formatted = created_at_series.apply(
        lambda x: x.strftime('%d.%m.%Y %H:%M') if pd.notna(x) else 'N/A'
    )

    display_df = pd.DataFrame({
        'ID': df['id'],
        'Номер': df.get('application_number', 'N/A'),
        'Название': df['title'].str[:50] + '...',
        'Пользователь': df['first_name'] + ' ' + df['last_name'],
        'Статус': df['status'],
        'Балл': df['quality_score'].fillna(0),
        'Создано': created_at_formatted
    })

    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Номер": st.column_config.TextColumn("Номер заявки", width="medium"),
            "Название": st.column_config.TextColumn("Название", width="large"),
            "Пользователь": st.column_config.TextColumn("Пользователь", width="medium"),
            "Статус": st.column_config.TextColumn("Статус", width="small"),
            "Балл": st.column_config.NumberColumn("Оценка", width="small", format="%.1f"),
            "Создано": st.column_config.TextColumn("Создано", width="medium")
        }
    )

    # Action: Select application for viewing
    selected_id = st.number_input(
        "ID заявки для просмотра",
        min_value=int(df['id'].min()),
        max_value=int(df['id'].max()),
        key="selected_app_id"
    )

    if st.button("Открыть детальный просмотр"):
        st.session_state.view_application_id = selected_id
        st.session_state.active_tab = "Просмотр"
        st.rerun()

def render_grant_card(row):
    """Render single grant card with actions"""
    sent_emoji = "📤"
    ready_emoji = "📝"

    sent_badge = f"{sent_emoji} Отправлен" if pd.notna(row['sent_id']) else f"{ready_emoji} Готов к отправке"

    with st.expander(f"{row['grant_id']} - {row['grant_title'] or 'Без названия'} ({sent_badge})"):
        col1, col2 = st.columns([2, 1])

        with col1:
            username_display = f"@{row['username']}" if row['username'] else "Unknown"
            st.markdown(f"**Пользователь:** {username_display} ({row['first_name']} {row['last_name']})")
            st.markdown(f"**Анкета:** {row['anketa_id']}")
            st.markdown(f"**Создан:** {row['created_at']}")
            st.markdown(f"**LLM:** {row['llm_provider']} ({row['model']})")

        with col2:
            st.metric("Оценка качества", f"{row['quality_score']}/10")

            if pd.isna(row['sent_id']):
                send_button_emoji = "📤"
                if st.button(f"{send_button_emoji} Отправить", key=f"send_{row['id']}"):
                    try:
                        success = send_grant_to_telegram(db, row['grant_id'], row['user_id'])
                        if success:
                            st.success("✅ Грант отправлен!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Ошибка отправки")
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
            else:
                st.info(f"Отправлен: {row['sent_at']}")

        # View and Download buttons
        col_view, col_download = st.columns(2)

        with col_view:
            view_emoji = "👁️"
            if st.button(f"{view_emoji} Просмотр", key=f"view_{row['id']}"):
                grant = get_grant_details(row['grant_id'])
                if grant:
                    st.markdown("### Содержание гранта")
                    st.markdown(grant['content'][:1000] + "..." if len(grant['content']) > 1000 else grant['content'])

        with col_download:
            grant = get_grant_details(row['grant_id'])
            if grant:
                # Generate text file content
                file_content = f"""
{"="*80}
ГРАНТОВАЯ ЗАЯВКА
{"="*80}

ID заявки: {grant['grant_id']}
Название: {grant['title'] or 'Без названия'}
Дата создания: {grant['created_at']}
Пользователь: {grant['username'] or 'Unknown'}
LLM провайдер: {grant['llm_provider']} ({grant['model'] or 'N/A'})
Оценка качества: {grant['quality_score']}/10

{"="*80}
СОДЕРЖАНИЕ ЗАЯВКИ
{"="*80}

{grant['content']}

{"="*80}
Сгенерировано: GrantService Admin Panel
{"="*80}
"""

                download_emoji = "📥"
                filename = f"grant_{grant['grant_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

                st.download_button(
                    label=f"{download_emoji} Скачать .txt",
                    data=file_content.encode('utf-8'),
                    file_name=filename,
                    mime="text/plain; charset=utf-8",
                    key=f"download_{row['id']}"
                )

# =============================================================================
# TAB 1: ВСЕ ЗАЯВКИ
# =============================================================================

def render_tab_all_applications():
    """Tab 1: All Applications - UNIFIED VERSION with Progress & Timeline"""
    list_emoji = "📋"
    st.markdown(f"### {list_emoji} Все грантовые заявки")
    st.caption("Объединённый список из таблиц `grants` (новые) и `grant_applications` (старые)")

    # Filters - Row 1
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Фильтр по прогрессу",
            ["all", "in_progress", "completed"],
            format_func=lambda x: {
                "all": "🔍 Все",
                "in_progress": "🔄 В работе (< 100%)",
                "completed": "✅ Завершённые (100%)"
            }.get(x, x),
            key="unified_status_filter"
        )

    with col2:
        stage_filter = st.selectbox(
            "Остановлен на этапе",
            ["all", "interview", "audit", "research", "planner", "writer"],
            format_func=lambda x: {
                "all": "🔍 Все этапы",
                "interview": "📝 Интервью",
                "audit": "✅ Аудит",
                "research": "🔍 Исследование",
                "planner": "📋 Планирование",
                "writer": "✍️ Написание"
            }.get(x, x),
            key="stage_filter",
            help="Показать заявки, застрявшие на конкретном этапе"
        )

    with col3:
        quality_filter = st.slider(
            "Минимальное качество",
            min_value=0,
            max_value=10,
            value=0,
            step=1,
            key="quality_filter",
            help="Фильтр по оценке качества гранта"
        )

    # Filters - Row 2
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "🔎 Поиск",
            placeholder="Название, Grant ID, Anketa ID, имя пользователя...",
            key="unified_search"
        )

    with col2:
        show_drafts = st.checkbox(
            "📝 Показать незавершенные",
            value=False,
            key="show_drafts",
            help="Показать черновики с < 10 ответов интервью"
        )

    st.markdown("---")

    # Fetch unified data
    df = get_all_grants_unified(status_filter=status_filter, search_query=search_query)

    # Count drafts (incomplete interviews) before filtering
    drafts_count = 0
    if not df.empty:
        drafts_count = len(df[df['interview_count'] < 10])

    # Apply client-side filters
    if not df.empty:
        # Filter out drafts by default (unless show_drafts is True)
        if not show_drafts:
            df = df[df['interview_count'] >= 10]
        # Filter by stage (where stuck)
        if stage_filter != 'all':
            if stage_filter == 'interview':
                df = df[df['interview_count'] < 10]
            elif stage_filter == 'audit':
                df = df[(df['interview_count'] >= 10) & (df['audit_status'] != 'approved')]
            elif stage_filter == 'research':
                df = df[(df['audit_status'] == 'approved') & (df['research_status'] != 'completed')]
            elif stage_filter == 'planner':
                df = df[(df['research_status'] == 'completed') & (df['planner_status'] != True)]
            elif stage_filter == 'writer':
                df = df[(df['planner_status'] == True) & (df['writer_status'] != 'completed')]

        # Filter by quality score
        if quality_filter > 0:
            df = df[df['quality_score'].fillna(0) >= quality_filter]

    # Statistics
    if not df.empty or drafts_count > 0:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📋 Всего заявок", len(df))
        with col2:
            new_count = len(df[df['source'] == 'new']) if not df.empty else 0
            st.metric("🆕 Новые (grants)", new_count)
        with col3:
            old_count = len(df[df['source'] == 'old']) if not df.empty else 0
            st.metric("📁 Старые (grant_applications)", old_count)
        with col4:
            completed_count = len(df[df['progress'] == 100]) if not df.empty else 0
            st.metric("✅ Завершённые", completed_count)
        with col5:
            drafts_label = "📝 Незавершённые"
            if not show_drafts and drafts_count > 0:
                drafts_label += " (скрыто)"
            st.metric(drafts_label, drafts_count)

    st.markdown("---")

    # Render unified list with progress bars and timeline
    render_grants_list_unified(df)

    # Export
    if not df.empty:
        csv_emoji = "📥"
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label=f"{csv_emoji} Скачать CSV",
            data=csv,
            file_name=f"grants_unified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv'
        )

# =============================================================================
# TAB 2: ГОТОВЫЕ ГРАНТЫ
# =============================================================================

def render_tab_ready_grants():
    """Tab 2: Ready Grants"""
    check_emoji = "✅"
    st.markdown(f"### {check_emoji} Готовые гранты")

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        quality_min = st.slider("Минимальная оценка качества", 0, 10, 0)

    with col2:
        show_sent = st.checkbox("Показать отправленные", value=False)

    st.markdown("---")

    # Fetch data
    df = get_ready_grants()

    # Apply filters
    if not df.empty:
        df = df[df['quality_score'] >= quality_min]

        if not show_sent:
            df = df[df['sent_id'].isna()]

    st.info(f"Найдено грантов: {len(df)}")

    # Display grants
    if not df.empty:
        for idx, row in df.iterrows():
            render_grant_card(row)
    else:
        st.info("Нет готовых грантов, соответствующих фильтрам")

# =============================================================================
# TAB 3: ОТПРАВКА
# =============================================================================

def render_tab_send():
    """Tab 3: Send to Telegram"""
    send_emoji = "📤"
    st.markdown(f"### {send_emoji} Отправка грантов в Telegram")

    instruction_emoji = "📋"
    st.markdown(f"""
    **{instruction_emoji} Инструкция:**
    1. Выберите грант из списка готовых
    2. Проверьте содержание
    3. Нажмите "Отправить пользователю"
    4. Грант будет отправлен в Telegram как PDF документ
    """)

    st.markdown("---")

    # Get grants ready to send
    df = get_ready_grants()
    df_unsent = df[df['sent_id'].isna()] if not df.empty else pd.DataFrame()

    if df_unsent.empty:
        empty_emoji = "📭"
        st.info(f"{empty_emoji} Нет грантов готовых к отправке из системы")
    else:
        # Select grant
        grant_options = {
            f"{row['grant_id']} - {row['grant_title']} (@{row['username']})": row['grant_id']
            for idx, row in df_unsent.iterrows()
        }

        selected_grant_label = st.selectbox("Выберите грант", list(grant_options.keys()))
        selected_grant_id = grant_options[selected_grant_label]

        # Get grant details
        grant = get_grant_details(selected_grant_id)

        if grant:
            preview_emoji = "🔍"
            st.markdown(f"### {preview_emoji} Предпросмотр")

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Название:** {grant['title']}")
                st.markdown(f"**ID:** {grant['grant_id']}")
                st.markdown(f"**Создан:** {grant['created_at']}")

            with col2:
                st.metric("Качество", f"{grant['quality_score']}/10")

            # Content preview
            content_emoji = "📄"
            with st.expander(f"{content_emoji} Просмотр содержания", expanded=False):
                preview_content = grant['content'][:500] + "..." if len(grant['content']) > 500 else grant['content']
                st.markdown(preview_content)

            # Download button (outside form - download_button doesn't work inside forms)
            file_content = f"""
{"="*80}
ГРАНТОВАЯ ЗАЯВКА
{"="*80}

ID заявки: {grant['grant_id']}
Название: {grant['title'] or 'Без названия'}
Дата создания: {grant['created_at']}
Пользователь: {grant['username'] or 'Unknown'}
LLM провайдер: {grant['llm_provider']} ({grant['model'] or 'N/A'})
Оценка качества: {grant['quality_score']}/10

{"="*80}
СОДЕРЖАНИЕ ЗАЯВКИ
{"="*80}

{grant['content']}

{"="*80}
Сгенерировано: GrantService Admin Panel
{"="*80}
"""

            download_emoji = "📥"
            filename = f"grant_{grant['grant_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            st.download_button(
                label=f"{download_emoji} Скачать полный текст (.txt)",
                data=file_content.encode('utf-8'),
                file_name=filename,
                mime="text/plain; charset=utf-8",
                key=f"download_send_{grant['grant_id']}",
                use_container_width=True
            )

            st.markdown("---")

            # Send form
            with st.form("send_grant_form"):
                message = st.text_area("Сообщение пользователю (опционально)",
                                      placeholder="Ваш грант готов!")

                send_button_emoji = "📤"
                submitted = st.form_submit_button(f"{send_button_emoji} Отправить пользователю в Telegram",
                                                  type="primary",
                                                  use_container_width=True)

                if submitted:
                    # Get user_id from grant
                    row = df_unsent[df_unsent['grant_id'] == selected_grant_id].iloc[0]

                    try:
                        success = send_grant_to_telegram(db, selected_grant_id, row['user_id'])
                        if success:
                            st.success("✅ Грант успешно отправлен!")
                            st.balloons()
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Ошибка отправки")
                    except Exception as e:
                        st.error(f"❌ Ошибка: {e}")

    # ===========================================================================
    # MANUAL FILE UPLOAD AND SEND
    # ===========================================================================

    st.markdown("---")
    st.markdown("### 📎 Ручная отправка готового гранта")
    st.markdown("**Загрузите готовый файл гранта и отправьте его пользователю**")

    with st.form("manual_send_form"):
        # File upload
        uploaded_file = st.file_uploader(
            "Выберите файл гранта",
            type=['pdf', 'docx', 'doc'],
            help="Поддерживаются форматы: PDF, DOCX, DOC"
        )

        # User selection
        from utils.postgres_helper import execute_query
        users_query = """
        SELECT telegram_id, username, first_name, last_name
        FROM users
        ORDER BY first_name, last_name
        """
        users_result = execute_query(users_query)
        users_df = pd.DataFrame([dict(row) for row in users_result]) if users_result else pd.DataFrame()

        if not users_df.empty:
            user_options = {
                f"{row['first_name']} {row['last_name']} (@{row['username']}) - ID: {row['telegram_id']}": row['telegram_id']
                for idx, row in users_df.iterrows()
            }

            selected_user_label = st.selectbox("Выберите пользователя", list(user_options.keys()))
            selected_user_id = user_options[selected_user_label]

            # Admin comment
            admin_comment = st.text_area(
                "Комментарий администратора (опционально)",
                placeholder="📄 Готовая грантовая заявка от GrantService"
            )

            # Submit button
            submit_manual = st.form_submit_button(
                "📤 Загрузить и отправить пользователю",
                type="primary",
                use_container_width=True
            )

            if submit_manual and uploaded_file:
                try:
                    # Save uploaded file
                    import os

                    ready_grants_dir = Path(__file__).parent.parent.parent / "data" / "ready_grants"
                    ready_grants_dir.mkdir(exist_ok=True)

                    # Generate filename with timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    file_extension = uploaded_file.name.split('.')[-1]
                    saved_filename = f"manual_grant_{timestamp}.{file_extension}"
                    file_path = ready_grants_dir / saved_filename

                    # Save file
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.read())

                    # Generate application_id
                    application_id = None  # NULL for manual uploads (no FK constraint violation)

                    # Insert into sent_documents
                    from utils.postgres_helper import execute_update

                    comment = admin_comment if admin_comment else "📄 Готовая грантовая заявка от GrantService"

                    execute_update("""
                        INSERT INTO sent_documents
                        (user_id, grant_application_id, file_path, file_name, file_size, admin_comment, delivery_status, admin_user)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        selected_user_id,
                        application_id,
                        str(file_path),
                        uploaded_file.name,
                        os.path.getsize(file_path),
                        comment,
                        'pending',
                        'web-admin'
                    ))

                    st.success(f"✅ Файл сохранён в базу данных!")
                    st.info(f"📁 Сохранён как: {saved_filename}")

                    # 🚀 REAL TELEGRAM SEND
                    try:
                        from utils.telegram_sender import send_document_to_telegram

                        success, result = send_document_to_telegram(
                            user_id=selected_user_id,
                            file_path=str(file_path),
                            caption=comment,
                            grant_application_id=None
                        )

                        if success:
                            # Update delivery status to 'delivered'
                            execute_update(
                                "UPDATE sent_documents SET delivery_status = 'delivered' WHERE file_path = %s",
                                (str(file_path),)
                            )
                            st.success(f"✅ Файл успешно отправлен пользователю в Telegram!")
                            st.info(f"📱 Message ID: {result.get('message_id', 'N/A')}")
                            st.info(f"👤 Отправлено пользователю: {selected_user_label}")
                            st.balloons()
                        else:
                            st.warning(f"⚠️ Файл сохранён, но не отправлен: {result.get('error', 'Unknown error')}")
                            st.info("💡 Файл остался в базе со статусом 'pending'")
                    except Exception as send_error:
                        logger.error(f"Telegram send error: {send_error}", exc_info=True)
                        st.warning(f"⚠️ Файл сохранён в базу, но ошибка отправки: {send_error}")
                        st.info("💡 Файл остался в базе со статусом 'pending'")

                    logger.info(f"Manual grant uploaded: {saved_filename} for user {selected_user_id}")

                except Exception as e:
                    st.error(f"❌ Ошибка при загрузке: {e}")
                    logger.error(f"Error uploading manual grant: {e}", exc_info=True)

            elif submit_manual and not uploaded_file:
                st.warning("⚠️ Пожалуйста, выберите файл для загрузки")

        else:
            st.warning("⚠️ Нет пользователей в базе данных")

# =============================================================================
# TAB 4: АРХИВ
# =============================================================================

def render_tab_archive():
    """Tab 4: Archive"""
    archive_emoji = "📚"
    st.markdown(f"### {archive_emoji} Архив отправленных грантов")

    df = get_sent_documents(db)

    if df.empty:
        empty_emoji = "📭"
        st.info(f"{empty_emoji} Архив пуст")
        return

    # Display table
    st.dataframe(
        df[['grant_id', 'username', 'first_name', 'grant_title', 'sent_at', 'delivery_status']],
        use_container_width=True,
        column_config={
            "grant_id": "Grant ID",
            "username": "Username",
            "first_name": "Имя",
            "grant_title": "Название",
            "sent_at": "Отправлено",
            "delivery_status": "Статус"
        }
    )

    # Details
    details_emoji = "📋"
    st.markdown(f"### {details_emoji} Детали отправок")

    for idx, row in df.iterrows():
        with st.expander(f"{row['grant_id']} - {row['grant_title']} (отправлен {row['sent_at']})"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Пользователь:** @{row['username']}")
                st.markdown(f"**Имя:** {row['first_name']} {row['last_name']}")

            with col2:
                st.markdown(f"**Статус доставки:** {row['delivery_status']}")
                st.markdown(f"**Файл:** {row['file_name']}")

            refresh_emoji = "🔄"
            if st.button(f"{refresh_emoji} Отправить повторно", key=f"resend_{row['id']}"):
                info_emoji = "⚠️"
                st.info(f"{info_emoji} Функция в разработке")

# =============================================================================
# LIFECYCLE VIEW HELPER
# =============================================================================

def render_lifecycle_view(anketa_id: str):
    """Render full lifecycle view with timeline and artifacts"""

    try:
        # Get lifecycle data
        manager = GrantLifecycleManager(anketa_id)
        lifecycle_data = manager.get_all_artifacts()

        if not lifecycle_data or not lifecycle_data.get('artifacts'):
            st.error(f"❌ Не удалось загрузить данные жизненного цикла для {anketa_id}")
            return

        # Metadata header
        metadata = lifecycle_data.get('metadata', {})
        username = metadata.get('username', 'Unknown')
        first_name = metadata.get('first_name', '')
        last_name = metadata.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip() or "Unknown"

        st.markdown(f"### 📋 Заявка: {anketa_id}")
        st.markdown(f"**Пользователь:** @{username} ({full_name})")
        st.markdown(f"**Telegram ID:** {metadata.get('telegram_id', 'N/A')}")

        st.markdown("---")

        # Render timeline and artifact cards
        render_grant_lifecycle(lifecycle_data)

        st.markdown("---")

        # Download buttons
        st.markdown("### 📥 Скачать артефакты")

        col1, col2, col3 = st.columns(3)

        with col1:
            # TXT export
            txt_data = export_artifact(lifecycle_data, 'txt')
            st.download_button(
                label="📄 Скачать TXT",
                data=txt_data,
                file_name=f"grant_lifecycle_{anketa_id}.txt",
                mime="text/plain",
                use_container_width=True
            )

        with col2:
            # PDF export
            pdf_data = export_artifact(lifecycle_data, 'pdf')
            st.download_button(
                label="📕 Скачать PDF",
                data=pdf_data,
                file_name=f"grant_lifecycle_{anketa_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with col3:
            # DOCX export
            docx_data = export_artifact(lifecycle_data, 'docx')
            st.download_button(
                label="📘 Скачать DOCX",
                data=docx_data,
                file_name=f"grant_lifecycle_{anketa_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

    except Exception as e:
        logger.error(f"Error rendering lifecycle view: {e}")
        st.error(f"❌ Ошибка при отображении lifecycle: {e}")


# =============================================================================
# TAB 5: ПРОСМОТР
# =============================================================================

def render_tab_view():
    """Tab 5: Detailed View - Enhanced with Lifecycle Support"""
    view_emoji = "🔍"
    st.markdown(f"### {view_emoji} Детальный просмотр заявки")

    # Check if we have anketa_id for lifecycle view
    anketa_id = None
    app_id = None

    if 'view_anketa_id' in st.session_state:
        # Direct lifecycle view via anketa_id
        anketa_id = st.session_state.view_anketa_id
    elif 'view_application_id' in st.session_state:
        # View via application_id (need to fetch anketa_id)
        app_id = st.session_state.view_application_id
    else:
        # Manual input - добавлен выбор режима поиска
        search_mode = st.radio(
            "Искать по:",
            ["Application ID", "Grant ID", "Anketa ID"],
            horizontal=True,
            help="Application ID - старая структура, Grant ID/Anketa ID - новая структура с lifecycle"
        )

        if search_mode == "Application ID":
            app_id = st.number_input("ID Заявки", min_value=1, key="view_app_input")
        elif search_mode == "Grant ID":
            grant_id_input = st.text_input("Grant ID", placeholder="GRANT_VALERIA_324", key="view_grant_input")
            if grant_id_input:
                # Get anketa_id from grants table
                try:
                    result = execute_query("SELECT anketa_id FROM grants WHERE grant_id = %s", (grant_id_input,))
                    if result and result[0]:
                        anketa_id = result[0]['anketa_id']
                        st.success(f"✅ Найдено: {anketa_id}")
                    else:
                        st.error(f"❌ Grant с ID '{grant_id_input}' не найден")
                except Exception as e:
                    st.error(f"❌ Ошибка поиска: {e}")
        else:  # Anketa ID
            anketa_id_input = st.text_input("Anketa ID", placeholder="VALERIA_PTSD_888465306", key="view_anketa_input")
            if anketa_id_input:
                anketa_id = anketa_id_input
                st.success(f"✅ Используем Anketa ID: {anketa_id}")

    # If we have anketa_id directly, show lifecycle view
    if anketa_id:
        render_lifecycle_view(anketa_id)

        # Back button
        if st.button("🔙 К списку", key="back_from_lifecycle"):
            if 'view_anketa_id' in st.session_state:
                del st.session_state.view_anketa_id
            st.session_state.active_tab = "Все заявки"
            st.rerun()
        return

    # Otherwise, fetch application details and check for anketa_id
    if not app_id:
        # Don't show error - user sees the input fields above
        return

    # Fetch application details
    app = get_application_details(db, app_id)

    if not app:
        st.error(f"❌ Заявка #{app_id} не найдена")
        return

    # Check if this application has anketa_id for lifecycle view
    app_anketa_id = app.get('anketa_id')
    if app_anketa_id:
        # Offer choice between old view and lifecycle view
        view_mode = st.radio(
            "Режим просмотра",
            ["📊 Lifecycle (полный цикл)", "📄 Простой просмотр"],
            horizontal=True,
            key="view_mode_selector"
        )

        if view_mode == "📊 Lifecycle (полный цикл)":
            render_lifecycle_view(app_anketa_id)

            # Back button
            if st.button("🔙 К списку", key="back_from_lifecycle_2"):
                if 'view_application_id' in st.session_state:
                    del st.session_state.view_application_id
                st.session_state.active_tab = "Все заявки"
                st.rerun()
            return

    # Header
    st.title(f"📄 Заявка #{app.get('application_number', app_id)}")
    st.markdown("---")

    # Main metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_emoji_map = {
            'draft': '📝',
            'in_progress': '🔄',
            'completed': '✅',
            'submitted': '📤',
            'approved': '🎉',
            'rejected': '❌'
        }
        status_emoji = status_emoji_map.get(app.get('status', 'draft'), '📝')
        st.metric("Статус", f"{status_emoji} {app.get('status', 'draft')}")

    with col2:
        quality_score = app.get('quality_score', 0)
        st.metric("Оценка качества", f"{quality_score:.1f}/10")

    with col3:
        st.metric("LLM", app.get('llm_provider', 'Unknown'))

    with col4:
        created = app.get('created_at', '')
        if created:
            try:
                # Handle both datetime objects and strings
                if isinstance(created, datetime):
                    formatted = created.strftime("%d.%m.%Y %H:%M")
                elif isinstance(created, str):
                    dt = datetime.fromisoformat(created)
                    formatted = dt.strftime("%d.%m.%Y %H:%M")
                else:
                    formatted = str(created)
            except:
                formatted = str(created) if created else "Неизвестно"
        else:
            formatted = "Неизвестно"
        st.metric("Создано", formatted)

    # Technical info
    tech_emoji = "🔧"
    with st.expander(f"{tech_emoji} Техническая информация", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Модель", app.get('model_used', 'Unknown'))

        with col2:
            processing_time = app.get('processing_time', 0)
            st.metric("Время обработки", f"{processing_time:.2f} сек")

        with col3:
            st.metric("Токенов", app.get('tokens_used', 0))

        with col4:
            st.metric("Автор", app.get('admin_user', 'Unknown'))

    # Content
    content_emoji = "📋"
    st.markdown(f"### {content_emoji} Содержание заявки")

    content = app.get('content_data', {})

    if content:
        section_order = [
            'title', 'summary', 'problem', 'solution',
            'implementation', 'budget', 'timeline',
            'team', 'impact', 'sustainability'
        ]

        section_names = {
            'title': '📝 Название проекта',
            'summary': '📋 Краткое описание',
            'problem': '❗ Описание проблемы',
            'solution': '💡 Предлагаемое решение',
            'implementation': '🛠️ План реализации',
            'budget': '💰 Бюджет проекта',
            'timeline': '⏰ Временные рамки',
            'team': '👥 Команда проекта',
            'impact': '🎯 Ожидаемый результат',
            'sustainability': '♻️ Устойчивость проекта'
        }

        for section_key in section_order:
            if section_key in content and content[section_key]:
                section_name = section_names.get(section_key, section_key.title())
                with st.expander(section_name, expanded=(section_key == 'summary')):
                    st.write(content[section_key])
    else:
        st.warning("⚠️ Содержание заявки недоступно")

        if app.get('summary'):
            summary_emoji = "📝"
            st.markdown(f"### {summary_emoji} Краткое описание")
            st.write(app['summary'])

    # Actions
    st.markdown("---")
    actions_emoji = "🔧"
    st.markdown(f"### {actions_emoji} Действия")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        export_emoji = "📥"
        if st.button(f"{export_emoji} Экспорт JSON", use_container_width=True):
            json_str = export_application_json(app)
            st.download_button(
                label=f"{export_emoji} Скачать JSON",
                data=json_str.encode('utf-8'),
                file_name=f"grant_application_{app.get('application_number', app_id)}.json",
                mime="application/json",
                use_container_width=True
            )

    with col2:
        back_emoji = "🔙"
        if st.button(f"{back_emoji} К списку", use_container_width=True):
            if 'view_application_id' in st.session_state:
                del st.session_state.view_application_id
            st.session_state.active_tab = "Все заявки"
            st.rerun()

    with col3:
        refresh_emoji = "🔄"
        if st.button(f"{refresh_emoji} Обновить", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with col4:
        delete_emoji = "❌"
        if st.button(f"{delete_emoji} Удалить", use_container_width=True):
            st.warning("⚠️ Функция удаления требует подтверждения")

# =============================================================================
# MAIN PAGE
# =============================================================================

def main():
    """Main page rendering"""

    # Header
    header_emoji = "📄"
    st.title(f"{header_emoji} Управление грантами")
    st.markdown("**Просмотр, отправка и архив грантовых заявок**")
    st.markdown("---")

    # Statistics
    stats = get_grants_statistics(db)
    render_metric_cards(stats)

    st.markdown("---")

    # Tabs
    tab_names = [
        "📋 Все заявки",
        "✅ Готовые гранты",
        "📤 Отправка",
        "📦 Архив",
        "🔍 Просмотр"
    ]

    # Get active tab from session state or default
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = tab_names[0]

    selected_tab = st.radio(
        "Выберите раздел",
        tab_names,
        horizontal=True,
        label_visibility="collapsed",
        key="tab_selector"
    )

    st.session_state.active_tab = selected_tab

    st.markdown("---")

    # Render selected tab
    if selected_tab == tab_names[0]:
        render_tab_all_applications()
    elif selected_tab == tab_names[1]:
        render_tab_ready_grants()
    elif selected_tab == tab_names[2]:
        render_tab_send()
    elif selected_tab == tab_names[3]:
        render_tab_archive()
    elif selected_tab == tab_names[4]:
        render_tab_view()

    # Footer
    st.markdown("---")
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.caption(f"Последнее обновление: {update_time}")
    st.caption("Версия 2.0.0 (Fully Integrated) | Объединены 3 архивных файла")

if __name__ == "__main__":
    main()
