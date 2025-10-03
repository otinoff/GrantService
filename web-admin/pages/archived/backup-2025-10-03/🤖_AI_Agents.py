"""
AI Agents Management - Monitoring and Configuration
====================================================

MVP Version: Focused on agent monitoring and prompt management
Execution logic moved to Pipeline Dashboard

Author: Grant Architect Agent
Date: 2025-10-01
Version: 2.0.0 (Refactored - removed duplicates)
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
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
# AGENT CONFIGURATION
# =============================================================================

AGENT_INFO = {
    'interviewer': {
        'name': 'Interviewer Agent',
        'emoji': '📝',
        'description': 'Сбор информации о проекте через 24 вопроса',
        'status': 'MVP: Hardcoded questions',
        'table': 'sessions',
        'future': 'AI-powered dynamic questioning'
    },
    'auditor': {
        'name': 'Auditor Agent',
        'emoji': '✅',
        'description': 'Оценка качества анкеты по 5 критериям',
        'status': 'Active',
        'table': 'auditor_results',
        'future': 'Multi-criteria weighted scoring'
    },
    'planner': {
        'name': 'Planner Agent',
        'emoji': '📐',
        'description': 'Создание структуры заявки',
        'status': 'MVP: Single template (7 sections)',
        'table': 'planner_structures',
        'future': 'Multiple templates per grant type'
    },
    'researcher': {
        'name': 'Researcher Agent',
        'emoji': '🔍',
        'description': 'Поиск данных через Perplexity API',
        'status': 'Active',
        'table': 'researcher_research',
        'future': 'Multi-source aggregation'
    },
    'writer': {
        'name': 'Writer Agent',
        'emoji': '✍️',
        'description': 'Генерация текста заявки через GigaChat',
        'status': 'Active',
        'table': 'grants',
        'future': 'Collaborative editing with user'
    }
}

# =============================================================================
# DATA FETCHING
# =============================================================================

def get_agent_stats(agent_key):
    """Get statistics for specific agent"""
    conn = get_db_connection()
    table = AGENT_INFO[agent_key]['table']

    if agent_key == 'interviewer':
        query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed,
            ROUND(AVG(progress_percentage), 1) as avg_progress,
            ROUND(AVG(session_duration_minutes), 1) as avg_duration_min
        FROM sessions
        WHERE started_at >= DATE('now', '-30 days')
        """

    elif agent_key == 'auditor':
        query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved,
            COUNT(CASE WHEN approval_status = 'needs_revision' THEN 1 END) as needs_revision,
            ROUND(AVG(average_score), 2) as avg_score,
            ROUND(AVG(completeness_score), 2) as avg_completeness,
            ROUND(AVG(clarity_score), 2) as avg_clarity,
            ROUND(AVG(feasibility_score), 2) as avg_feasibility,
            ROUND(AVG(innovation_score), 2) as avg_innovation,
            ROUND(AVG(quality_score), 2) as avg_quality
        FROM auditor_results
        WHERE created_at >= DATE('now', '-30 days')
        """

    elif agent_key == 'planner':
        query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN data_mapping_complete = 1 THEN 1 END) as complete_mappings,
            ROUND(AVG(sections_count), 1) as avg_sections,
            ROUND(AVG(total_word_count_target), 0) as avg_word_target
        FROM planner_structures
        WHERE created_at >= DATE('now', '-30 days')
        """

    elif agent_key == 'researcher':
        query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as errors
        FROM researcher_research
        WHERE created_at >= DATE('now', '-30 days')
        """

    elif agent_key == 'writer':
        query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft,
            ROUND(AVG(quality_score), 2) as avg_quality_score
        FROM grants
        WHERE created_at >= DATE('now', '-30 days')
        """

    df = pd.read_sql_query(query, conn)
    return df.iloc[0].to_dict() if not df.empty else {}

def get_agent_prompts(agent_key):
    """Get prompts for specific agent"""
    conn = get_db_connection()

    query = """
    SELECT
        id,
        prompt_name,
        prompt_text,
        category,
        version,
        is_active,
        updated_at
    FROM agent_prompts
    WHERE agent_type = ?
    ORDER BY is_active DESC, updated_at DESC
    """

    df = pd.read_sql_query(query, conn, params=(agent_key,))
    return df

def update_prompt(prompt_id, prompt_text):
    """Update agent prompt"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE agent_prompts
        SET prompt_text = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (prompt_text, prompt_id))

    conn.commit()
    return True

def create_prompt(agent_type, prompt_name, prompt_text, category):
    """Create new agent prompt"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO agent_prompts (agent_type, prompt_name, prompt_text, category, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (agent_type, prompt_name, prompt_text, category))

    conn.commit()
    return True

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_agent_card(agent_key):
    """Render agent information card"""
    info = AGENT_INFO[agent_key]
    stats = get_agent_stats(agent_key)

    with st.container():
        st.markdown(f"### {info['emoji']} {info['name']}")
        st.markdown(f"**Описание:** {info['description']}")
        st.markdown(f"**Статус:** `{info['status']}`")
        st.markdown(f"**Таблица БД:** `{info['table']}`")

        if stats:
            st.markdown("**📊 Статистика (30 дней):**")

            # Display stats based on agent type
            if agent_key == 'interviewer':
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Всего", stats.get('total', 0))
                with col2:
                    st.metric("Завершено", stats.get('completed', 0))
                with col3:
                    st.metric("Средний прогресс", f"{stats.get('avg_progress', 0)}%")
                with col4:
                    st.metric("Среднее время", f"{stats.get('avg_duration_min', 0)} мин")

            elif agent_key == 'auditor':
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Всего оценок", stats.get('total', 0))
                with col2:
                    st.metric("Одобрено", stats.get('approved', 0))
                with col3:
                    st.metric("На доработку", stats.get('needs_revision', 0))
                with col4:
                    st.metric("Средний балл", f"{stats.get('avg_score', 0)}/10")

                # Score breakdown
                st.markdown("**Детализация оценок:**")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Полнота", stats.get('avg_completeness', 0))
                with col2:
                    st.metric("Ясность", stats.get('avg_clarity', 0))
                with col3:
                    st.metric("Реалистичность", stats.get('avg_feasibility', 0))
                with col4:
                    st.metric("Инновация", stats.get('avg_innovation', 0))
                with col5:
                    st.metric("Качество", stats.get('avg_quality', 0))

            elif agent_key == 'planner':
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Всего планов", stats.get('total', 0))
                with col2:
                    st.metric("Полный mapping", stats.get('complete_mappings', 0))
                with col3:
                    st.metric("Средний объём", f"{stats.get('avg_word_target', 0)} слов")

            elif agent_key == 'researcher':
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Всего", stats.get('total', 0))
                with col2:
                    st.metric("Завершено", stats.get('completed', 0))
                with col3:
                    st.metric("В процессе", stats.get('processing', 0))
                with col4:
                    st.metric("Ошибки", stats.get('errors', 0))

            elif agent_key == 'writer':
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Всего", stats.get('total', 0))
                with col2:
                    st.metric("Завершено", stats.get('completed', 0))
                with col3:
                    st.metric("Средняя оценка", f"{stats.get('avg_quality_score', 0)}/10")

        st.markdown(f"**🚀 Будущее:** {info['future']}")

def render_prompts_manager(agent_key):
    """Render prompts management interface"""
    st.markdown("### 📝 Управление промптами")

    df_prompts = get_agent_prompts(agent_key)

    if df_prompts.empty:
        st.info(f"Промпты для {AGENT_INFO[agent_key]['name']} пока не созданы")

        if st.button("➕ Создать новый промпт"):
            with st.form(f"new_prompt_{agent_key}"):
                prompt_name = st.text_input("Название промпта")
                category = st.selectbox("Категория", ['system', 'user', 'assistant'])
                prompt_text = st.text_area("Текст промпта", height=200)

                if st.form_submit_button("Сохранить"):
                    if prompt_name and prompt_text:
                        create_prompt(agent_key, prompt_name, prompt_text, category)
                        st.success("✅ Промпт создан!")
                        st.rerun()
                    else:
                        st.error("Заполните все поля")

        return

    # Show existing prompts
    for idx, row in df_prompts.iterrows():
        status_emoji = "✅" if row['is_active'] else "⏸️"
        with st.expander(f"{status_emoji} {row['prompt_name']} (v{row['version']})"):
            st.markdown(f"**Категория:** {row['category']}")
            st.markdown(f"**Обновлено:** {row['updated_at']}")

            # Editable prompt text
            new_text = st.text_area(
                "Текст промпта",
                value=row['prompt_text'],
                height=200,
                key=f"prompt_{row['id']}"
            )

            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("💾 Сохранить", key=f"save_{row['id']}"):
                    update_prompt(row['id'], new_text)
                    st.success("Обновлено!")
                    st.rerun()

# =============================================================================
# MAIN PAGE
# =============================================================================

def main():
    st.set_page_config(
        page_title="AI Agents - GrantService",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 AI Agents Management")
    st.markdown("**Мониторинг и настройка AI агентов**")
    st.markdown("---")

    # Agent selector
    st.sidebar.header("Выбор агента")
    selected_agent = st.sidebar.radio(
        "Агент",
        list(AGENT_INFO.keys()),
        format_func=lambda x: f"{AGENT_INFO[x]['emoji']} {AGENT_INFO[x]['name']}"
    )

    # Main content
    tab1, tab2 = st.tabs(["📊 Статистика", "📝 Промпты"])

    with tab1:
        render_agent_card(selected_agent)

    with tab2:
        render_prompts_manager(selected_agent)

    # Footer
    st.markdown("---")
    st.caption("Версия 2.0.0 (Рефакторинг) | Удалены дубликаты Researcher/Writer")
    st.caption("Запуск агентов выполняется через 🎯 Pipeline Dashboard")

if __name__ == "__main__":
    main()
