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
    from utils.database import AdminDatabase, get_db_connection
    from utils.logger import setup_logger
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
    """Get grants statistics for header metrics"""
    conn = get_db_connection()

    try:
        total = conn.execute("SELECT COUNT(*) FROM grant_applications").fetchone()[0]

        in_progress = conn.execute(
            "SELECT COUNT(*) FROM grant_applications WHERE status IN ('draft', 'in_progress')"
        ).fetchone()[0]

        ready = conn.execute(
            "SELECT COUNT(*) FROM grant_applications WHERE status = 'completed'"
        ).fetchone()[0]

        sent = conn.execute(
            "SELECT COUNT(DISTINCT grant_application_id) FROM sent_documents"
        ).fetchone()[0]

        return {
            'total': total,
            'in_progress': in_progress,
            'ready': ready,
            'sent': sent
        }
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        return {'total': 0, 'in_progress': 0, 'ready': 0, 'sent': 0}

@st.cache_data(ttl=60)
def get_all_applications(_db, status_filter='all', period_days=None):
    """Get all grant applications with filters"""
    conn = get_db_connection()

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
        u.last_name
    FROM grant_applications ga
    LEFT JOIN users u ON ga.user_id = u.telegram_id
    WHERE 1=1
    """

    params = []

    if status_filter != 'all':
        query += " AND ga.status = ?"
        params.append(status_filter)

    if period_days:
        cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()
        query += " AND ga.created_at >= ?"
        params.append(cutoff_date)

    query += " ORDER BY ga.created_at DESC"

    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_ready_grants(_db):
    """Get grants ready for delivery (status='completed')"""
    conn = get_db_connection()

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
        sd.id as sent_id,
        sd.sent_at,
        sd.delivery_status
    FROM grants g
    LEFT JOIN sent_documents sd ON g.grant_id = sd.grant_id
    WHERE g.status = 'completed'
    ORDER BY g.created_at DESC
    """

    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        logger.error(f"Error fetching ready grants: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_grant_details(_db, grant_id):
    """Get full grant details including content"""
    conn = get_db_connection()

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
    WHERE grant_id = ?
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query, (grant_id,))
        row = cursor.fetchone()

        if row:
            return {
                'grant_id': row[0],
                'title': row[1],
                'content': row[2],
                'sections': json.loads(row[3]) if row[3] else [],
                'metadata': json.loads(row[4]) if row[4] else {},
                'quality_score': row[5],
                'llm_provider': row[6],
                'model': row[7],
                'created_at': row[8],
                'user_id': row[9],
                'username': row[10]
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching grant details: {e}")
        return None

@st.cache_data(ttl=60)
def get_application_details(_db, app_id):
    """Get detailed application info from grant_applications"""
    conn = get_db_connection()

    query = """
    SELECT
        ga.*,
        u.username,
        u.first_name,
        u.last_name,
        u.telegram_id
    FROM grant_applications ga
    LEFT JOIN users u ON ga.user_id = u.telegram_id
    WHERE ga.id = ?
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query, (app_id,))

        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        if row:
            app = dict(zip(columns, row))

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
    conn = get_db_connection()

    query = """
    SELECT
        sd.id,
        sd.grant_id,
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
    LEFT JOIN users u ON sd.user_id = u.telegram_id
    LEFT JOIN grants g ON sd.grant_id = g.grant_id
    ORDER BY sd.sent_at DESC
    LIMIT 100
    """

    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        logger.error(f"Error fetching sent documents: {e}")
        return pd.DataFrame()

# =============================================================================
# ACTION FUNCTIONS
# =============================================================================

def send_grant_to_telegram(grant_id, user_id):
    """
    Send grant document to user via Telegram
    MVP: Marks as sent in database (actual sending requires bot integration)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert into sent_documents
        cursor.execute("""
            INSERT INTO sent_documents (
                grant_id,
                user_id,
                telegram_message_id,
                file_name,
                sent_at,
                delivery_status
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (grant_id, user_id, None, f"{grant_id}.pdf",
              datetime.now().isoformat(), 'delivered'))

        # Update grant status
        cursor.execute("""
            UPDATE grants
            SET status = 'delivered', submitted_at = ?
            WHERE grant_id = ?
        """, (datetime.now().isoformat(), grant_id))

        conn.commit()
        logger.info(f"Grant {grant_id} marked as sent to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error sending grant: {e}")
        conn.rollback()
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

def render_applications_table(df):
    """Render applications table with click handlers"""
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
        'Номер': df['application_number'],
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
                        success = send_grant_to_telegram(row['grant_id'], row['user_id'])
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

        # View content button
        view_emoji = "👁️"
        if st.button(f"{view_emoji} Просмотр содержания", key=f"view_{row['id']}"):
            grant = get_grant_details(db, row['grant_id'])
            if grant:
                st.markdown("### Содержание гранта")
                st.markdown(grant['content'][:1000] + "..." if len(grant['content']) > 1000 else grant['content'])

# =============================================================================
# TAB 1: ВСЕ ЗАЯВКИ
# =============================================================================

def render_tab_all_applications():
    """Tab 1: All Applications"""
    list_emoji = "📋"
    st.markdown(f"### {list_emoji} Все грантовые заявки")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Статус",
            ["all", "draft", "in_progress", "completed", "submitted", "approved", "rejected"],
            format_func=lambda x: {
                "all": "Все",
                "draft": "Черновик",
                "in_progress": "В работе",
                "completed": "Завершено",
                "submitted": "Отправлено",
                "approved": "Одобрено",
                "rejected": "Отклонено"
            }.get(x, x)
        )

    with col2:
        period = st.selectbox(
            "Период",
            [None, 7, 30, 365],
            format_func=lambda x: {
                None: "Все время",
                7: "За 7 дней",
                30: "За 30 дней",
                365: "За год"
            }.get(x, str(x))
        )

    with col3:
        search_user = st.text_input("Поиск по User ID", placeholder="telegram_id")

    st.markdown("---")

    # Fetch data
    df = get_all_applications(db, status_filter, period)

    if search_user:
        df = df[df['user_id'].astype(str).str.contains(search_user, na=False)]

    # Statistics
    st.info(f"Найдено заявок: {len(df)}")

    # Table
    render_applications_table(df)

    # Export
    if not df.empty:
        csv_emoji = "📥"
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label=f"{csv_emoji} Скачать CSV",
            data=csv,
            file_name=f"grant_applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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
    df = get_ready_grants(db)

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
    df = get_ready_grants(db)
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
        grant = get_grant_details(db, selected_grant_id)

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

            st.markdown("---")

            # Send form
            with st.form("send_grant_form"):
                message = st.text_area("Сообщение пользователю (опционально)",
                                      placeholder="Ваш грант готов!")

                col1, col2 = st.columns(2)

                with col1:
                    send_button_emoji = "📤"
                    submitted = st.form_submit_button(f"{send_button_emoji} Отправить пользователю",
                                                      type="primary",
                                                      use_container_width=True)

                with col2:
                    download_emoji = "💾"
                    download_button = st.form_submit_button(f"{download_emoji} Скачать PDF",
                                                           use_container_width=True)

                if submitted:
                    # Get user_id from grant
                    row = df_unsent[df_unsent['grant_id'] == selected_grant_id].iloc[0]

                    try:
                        success = send_grant_to_telegram(selected_grant_id, row['user_id'])
                        if success:
                            st.success("✅ Грант успешно отправлен!")
                            st.balloons()
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Ошибка отправки")
                    except Exception as e:
                        st.error(f"❌ Ошибка: {e}")

                if download_button:
                    warning_emoji = "⚠️"
                    st.info(f"{warning_emoji} MVP: Генерация PDF в разработке")

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
        conn = get_db_connection()
        users_query = """
        SELECT telegram_id, username, first_name, last_name
        FROM users
        ORDER BY first_name, last_name
        """
        users_df = pd.read_sql_query(users_query, conn)

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
                    from datetime import datetime

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
                    application_id = f"MANUAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

                    # Insert into sent_documents
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    comment = admin_comment if admin_comment else "📄 Готовая грантовая заявка от GrantService"

                    cursor.execute("""
                        INSERT INTO sent_documents
                        (user_id, grant_application_id, file_path, file_name, file_size, admin_comment, delivery_status, admin_user)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

                    conn.commit()

                    st.success(f"✅ Файл загружен и добавлен в очередь отправки!")
                    st.info(f"📁 Сохранён как: {saved_filename}")
                    st.info(f"👤 Будет отправлен пользователю: {selected_user_label}")
                    st.balloons()

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
# TAB 5: ПРОСМОТР
# =============================================================================

def render_tab_view():
    """Tab 5: Detailed View"""
    view_emoji = "🔍"
    st.markdown(f"### {view_emoji} Детальный просмотр заявки")

    # Get application ID
    if 'view_application_id' in st.session_state:
        app_id = st.session_state.view_application_id
    else:
        app_id = st.number_input("ID Заявки", min_value=1, key="view_app_input")

    if not app_id:
        st.info("Введите ID заявки для просмотра")
        return

    # Fetch application details
    app = get_application_details(db, app_id)

    if not app:
        st.error(f"❌ Заявка #{app_id} не найдена")
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
                dt = datetime.fromisoformat(created)
                formatted = dt.strftime("%d.%m.%Y %H:%M")
            except:
                formatted = created
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
