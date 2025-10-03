"""
Grant Management - Unified Page for Ready Grants
=================================================

Combines functionality from:
- 📋_Готовые_гранты.py (viewing grants)
- 📤_Отправка_грантов.py (sending to users)

Three tabs: Ready Grants | Send to Telegram | Archive

Author: Grant Architect Agent
Date: 2025-10-01
Version: 1.0.0 (Unified)
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import json

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
# DATA FETCHING
# =============================================================================

def get_ready_grants(status_filter='completed'):
    """Get grants ready for delivery"""
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
        g.quality_score,
        g.status,
        g.llm_provider,
        g.model,
        g.created_at,
        g.submitted_at,
        -- Check if already sent
        sd.id as sent_id,
        sd.sent_at,
        sd.delivery_status
    FROM grants g
    LEFT JOIN sent_documents sd ON g.grant_id = sd.grant_id
    WHERE g.status = ?
    ORDER BY g.created_at DESC
    """

    df = pd.read_sql_query(query, conn, params=(status_filter,))
    return df

def get_grant_details(grant_id):
    """Get full grant content"""
    conn = get_db_connection()

    query = """
    SELECT
        grant_id,
        grant_title,
        grant_content,
        grant_sections,
        metadata,
        quality_score,
        created_at
    FROM grants
    WHERE grant_id = ?
    """

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
            'created_at': row[6]
        }
    return None

def send_grant_to_telegram(grant_id, user_id):
    """Send grant document to user via Telegram"""
    # TODO: Implement actual Telegram sending logic
    # For MVP: just mark as sent in database

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert into sent_documents
    cursor.execute("""
        INSERT INTO sent_documents (
            grant_id,
            user_id,
            telegram_message_id,
            file_name,
            sent_at,
            delivery_status
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'delivered')
    """, (grant_id, user_id, None, f"{grant_id}.pdf"))

    # Update grant status
    cursor.execute("""
        UPDATE grants
        SET status = 'delivered', submitted_at = CURRENT_TIMESTAMP
        WHERE grant_id = ?
    """, (grant_id,))

    conn.commit()
    return True

def get_sent_documents():
    """Get all sent documents"""
    conn = get_db_connection()

    query = """
    SELECT
        sd.id,
        sd.grant_id,
        sd.user_id,
        u.username,
        u.first_name,
        u.last_name,
        g.grant_title,
        sd.file_name,
        sd.sent_at,
        sd.delivery_status
    FROM sent_documents sd
    LEFT JOIN users u ON sd.user_id = u.telegram_id
    LEFT JOIN grants g ON sd.grant_id = g.grant_id
    ORDER BY sd.sent_at DESC
    LIMIT 100
    """

    df = pd.read_sql_query(query, conn)
    return df

# =============================================================================
# UI COMPONENTS - TAB 1: READY GRANTS
# =============================================================================

def render_ready_grants_tab():
    """Render the Ready Grants tab"""
    st.header("📋 Готовые гранты")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status = st.selectbox(
            "Статус",
            ['completed', 'delivered', 'submitted', 'approved', 'rejected']
        )

    with col2:
        quality_min = st.slider("Минимальная оценка качества", 0, 10, 0)

    with col3:
        show_sent = st.checkbox("Показать отправленные", value=False)

    # Fetch grants
    df_grants = get_ready_grants(status)

    if not df_grants.empty:
        # Apply filters
        df_grants = df_grants[df_grants['quality_score'] >= quality_min]

        if not show_sent:
            df_grants = df_grants[df_grants['sent_id'].isna()]

        st.info(f"Найдено грантов: {len(df_grants)}")

        # Display grants
        for idx, row in df_grants.iterrows():
            sent_badge = "📤 Отправлен" if not pd.isna(row['sent_id']) else "📝 Готов к отправке"

            with st.expander(f"{row['grant_id']} - {row['grant_title'] or 'Без названия'} ({sent_badge})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Пользователь:** @{row['username']} ({row['first_name']} {row['last_name']})")
                    st.markdown(f"**Анкета:** {row['anketa_id']}")
                    st.markdown(f"**Создан:** {row['created_at']}")
                    st.markdown(f"**LLM:** {row['llm_provider']} ({row['model']})")

                with col2:
                    st.metric("Оценка качества", f"{row['quality_score']}/10")

                    if pd.isna(row['sent_id']):
                        if st.button("📤 Отправить", key=f"send_{row['id']}"):
                            try:
                                send_grant_to_telegram(row['grant_id'], row['user_id'])
                                st.success("✅ Грант отправлен!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка отправки: {e}")
                    else:
                        st.info(f"Отправлен: {row['sent_at']}")

                # View grant content
                if st.button("👁️ Просмотр содержания", key=f"view_{row['id']}"):
                    grant = get_grant_details(row['grant_id'])
                    if grant:
                        st.markdown("### Содержание гранта")
                        st.markdown(grant['content'])

                        if grant['sections']:
                            st.markdown("### Разделы")
                            for section in grant['sections']:
                                with st.expander(section.get('title', 'Без названия')):
                                    st.markdown(section.get('content', ''))
    else:
        st.info("📭 Нет готовых грантов")

# =============================================================================
# UI COMPONENTS - TAB 2: SEND TO TELEGRAM
# =============================================================================

def render_send_tab():
    """Render the Send to Telegram tab"""
    st.header("📤 Отправка грантов в Telegram")

    st.markdown("""
    **Инструкция:**
    1. Выберите грант из списка готовых
    2. Проверьте содержание
    3. Нажмите "Отправить пользователю"
    4. Грант будет отправлен в Telegram как PDF документ
    """)

    # Get grants ready to send
    df_grants = get_ready_grants('completed')
    df_grants = df_grants[df_grants['sent_id'].isna()]  # Only unsent

    if df_grants.empty:
        st.info("📭 Нет грантов готовых к отправке")
        return

    # Select grant
    grant_options = {
        f"{row['grant_id']} - {row['grant_title']} (@{row['username']})": row['grant_id']
        for idx, row in df_grants.iterrows()
    }

    selected_grant_label = st.selectbox("Выберите грант", list(grant_options.keys()))
    selected_grant_id = grant_options[selected_grant_label]

    # Get grant details
    grant = get_grant_details(selected_grant_id)

    if grant:
        st.markdown("### Предпросмотр")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**Название:** {grant['title']}")
            st.markdown(f"**ID:** {grant['grant_id']}")
            st.markdown(f"**Создан:** {grant['created_at']}")

        with col2:
            st.metric("Качество", f"{grant['quality_score']}/10")

        # Show content preview
        with st.expander("📄 Просмотр содержания", expanded=False):
            st.markdown(grant['content'][:500] + "..." if len(grant['content']) > 500 else grant['content'])

        # Send button
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("📤 Отправить пользователю", type="primary"):
                # Get user_id from grant
                row = df_grants[df_grants['grant_id'] == selected_grant_id].iloc[0]

                try:
                    send_grant_to_telegram(selected_grant_id, row['user_id'])
                    st.success("✅ Грант успешно отправлен!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Ошибка отправки: {e}")

        with col2:
            if st.button("💾 Скачать PDF"):
                st.info("⚠️ MVP: Генерация PDF в разработке")

# =============================================================================
# UI COMPONENTS - TAB 3: ARCHIVE
# =============================================================================

def render_archive_tab():
    """Render the Archive tab"""
    st.header("📚 Архив отправленных грантов")

    df_sent = get_sent_documents()

    if df_sent.empty:
        st.info("📭 Архив пуст")
        return

    # Display sent documents
    st.dataframe(
        df_sent[['grant_id', 'username', 'first_name', 'grant_title', 'sent_at', 'delivery_status']],
        use_container_width=True
    )

    # Details expander
    st.markdown("### Детали отправок")

    for idx, row in df_sent.iterrows():
        with st.expander(f"{row['grant_id']} - {row['grant_title']} (отправлен {row['sent_at']})"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Пользователь:** @{row['username']}")
                st.markdown(f"**Имя:** {row['first_name']} {row['last_name']}")

            with col2:
                st.markdown(f"**Статус доставки:** {row['delivery_status']}")
                st.markdown(f"**Файл:** {row['file_name']}")

            if st.button("🔄 Отправить повторно", key=f"resend_{row['id']}"):
                st.info("⚠️ Функция в разработке")

# =============================================================================
# MAIN PAGE
# =============================================================================

def main():
    st.set_page_config(
        page_title="Grant Management - GrantService",
        page_icon="📋",
        layout="wide"
    )

    st.title("📋 Управление грантами")
    st.markdown("**Просмотр, отправка и архив готовых грантовых заявок**")
    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📋 Готовые гранты",
        "📤 Отправка в Telegram",
        "📚 Архив"
    ])

    with tab1:
        render_ready_grants_tab()

    with tab2:
        render_send_tab()

    with tab3:
        render_archive_tab()

    # Footer
    st.markdown("---")
    st.caption(f"Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("Версия 1.0.0 (Unified) | Объединение 📋_Готовые_гранты + 📤_Отправка_грантов")

if __name__ == "__main__":
    main()
