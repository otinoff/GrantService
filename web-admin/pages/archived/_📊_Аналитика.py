#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analytics Page - GrantService Admin (v3.0)
Comprehensive analytics: Общая | Агенты | Логи
Интеграция из 📊_Общая_аналитика.py + 📋_Мониторинг_логов.py
"""

import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# PATH SETUP - Import setup_paths FIRST
sys.path.insert(0, str(Path(__file__).parent.parent))
import setup_paths

# IMPORTS
try:
    from utils.database import AdminDatabase
    from utils.postgres_helper import (
        execute_query,
        execute_query_df,
        execute_scalar,
        execute_update
    )
    from utils.logger import setup_logger, get_log_stats
    from utils.charts import create_daily_chart, create_metrics_cards
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.info("Please run via launcher.py")
    st.stop()

# PAGE CONFIG
st.set_page_config(page_title="Аналитика", page_icon="📊", layout="wide")
logger = setup_logger('analytics_page')

# DATABASE
@st.cache_resource
def get_database():
    """Get cached database instance"""
    return AdminDatabase()

db = get_database()

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_system_metrics(_db):
    """Load system metrics with caching"""
    try:
        stats = _db.get_basic_stats()

        # Calculate additional metrics
        total_users = stats.get('total_users', 0)
        completed_apps = stats.get('completed_apps', 0)

        return {
            'total_users': total_users,
            'completed_grants': completed_apps,
            'avg_nps': 0,  # TODO: implement NPS
            'conversion_rate': stats.get('conversion_rate', 0),
            'avg_processing_cost': 0,  # TODO: implement
            'avg_processing_time': 0,  # TODO: implement
            'recent_sessions': stats.get('recent_sessions', 0)
        }
    except Exception as e:
        logger.error(f"Error loading system metrics: {e}", exc_info=True)
        return {
            'total_users': 0,
            'completed_grants': 0,
            'avg_nps': 0,
            'conversion_rate': 0,
            'avg_processing_cost': 0,
            'avg_processing_time': 0,
            'recent_sessions': 0
        }

@st.cache_data(ttl=300)
def load_conversion_funnel(_db):
    """Load conversion funnel data"""
    try:
        # Funnel stages: Registration -> Interview -> Audit -> Plan -> Research -> Text -> Submit
        # Get counts for each stage
        total_users = execute_scalar("SELECT COUNT(*) FROM users") or 0

        # Mock data for now - TODO: implement real stage tracking
        funnel_data = {
            'stages': [
                'Регистрация',
                'Интервью',
                'Аудит',
                'План',
                'Исследование',
                'Текст',
                'Отправка'
            ],
            'counts': [
                total_users,
                int(total_users * 0.85),
                int(total_users * 0.72),
                int(total_users * 0.65),
                int(total_users * 0.58),
                int(total_users * 0.52),
                int(total_users * 0.45)
            ]
        }

        return funnel_data
    except Exception as e:
        logger.error(f"Error loading conversion funnel: {e}", exc_info=True)
        return {
            'stages': ['Регистрация'],
            'counts': [0]
        }

@st.cache_data(ttl=300)
def load_daily_dynamics(_db, days=30):
    """Load daily dynamics for last N days"""
    try:
        daily_stats = _db.get_daily_stats(days=days)
        return daily_stats
    except Exception as e:
        logger.error(f"Error loading daily dynamics: {e}", exc_info=True)
        return {}

@st.cache_data(ttl=300)
def load_agents_statistics(_db):
    """Load statistics for all AI agents"""
    try:
        # TODO: implement real agent tracking
        agents_data = {
            'Interviewer': {
                'total_runs': 0,
                'successful_runs': 0,
                'avg_time': 0,
                'avg_cost': 0,
                'tokens_used': 0
            },
            'Auditor': {
                'total_runs': 0,
                'successful_runs': 0,
                'avg_time': 0,
                'avg_cost': 0,
                'avg_score': 0
            },
            'Planner': {
                'total_runs': 0,
                'successful_runs': 0,
                'avg_time': 0,
                'avg_cost': 0
            },
            'Researcher': {
                'total_runs': 0,
                'successful_runs': 0,
                'avg_time': 0,
                'avg_cost': 0,
                'tokens_used': 0
            },
            'Writer': {
                'total_runs': 0,
                'successful_runs': 0,
                'avg_time': 0,
                'avg_cost': 0,
                'avg_text_length': 0
            }
        }

        return agents_data
    except Exception as e:
        logger.error(f"Error loading agents statistics: {e}", exc_info=True)
        return {}

@st.cache_data(ttl=30)  # Cache for 30 seconds (pseudo real-time)
def load_logs(log_level='ALL', limit=100, search_text=None):
    """Load system logs"""
    try:
        log_stats = get_log_stats()

        if not log_stats.get('files'):
            return []

        # Find main log file
        log_dir = log_stats.get('log_directory')
        main_log_file = None

        for file_info in log_stats['files']:
            if 'grantservice.log' in file_info['name'].lower() or 'main.log' in file_info['name'].lower():
                main_log_file = file_info['name']
                break

        if not main_log_file and log_stats['files']:
            # Use first log file
            main_log_file = log_stats['files'][0]['name']

        if not main_log_file:
            return []

        log_path = os.path.join(log_dir, main_log_file)

        # Read log file
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # Take last N lines
        recent_lines = lines[-limit:] if len(lines) > limit else lines

        # Filter by log level
        if log_level != 'ALL':
            filtered_lines = []
            for line in recent_lines:
                if f" - {log_level} - " in line:
                    filtered_lines.append(line)
            recent_lines = filtered_lines

        # Filter by search text
        if search_text:
            filtered_lines = []
            for line in recent_lines:
                if search_text.lower() in line.lower():
                    filtered_lines.append(line)
            recent_lines = filtered_lines

        return recent_lines

    except Exception as e:
        logger.error(f"Error loading logs: {e}", exc_info=True)
        return []

def analyze_log_errors(log_lines):
    """Analyze errors in logs"""
    errors = []
    warnings = []

    for line in log_lines:
        if " - ERROR - " in line or " - CRITICAL - " in line:
            # Extract error message
            parts = line.split(" - ERROR - ") if " - ERROR - " in line else line.split(" - CRITICAL - ")
            if len(parts) > 1:
                errors.append(parts[1].strip())
        elif " - WARNING - " in line:
            parts = line.split(" - WARNING - ")
            if len(parts) > 1:
                warnings.append(parts[1].strip())

    # Deduplicate
    unique_errors = list(set(errors))
    unique_warnings = list(set(warnings))

    return {
        'total_errors': len(errors),
        'unique_errors': len(unique_errors),
        'total_warnings': len(warnings),
        'unique_warnings': len(unique_warnings),
        'error_list': unique_errors[:10],  # Top 10
        'warning_list': unique_warnings[:10]
    }

# =============================================================================
# MAIN PAGE
# =============================================================================

# Header
chart_emoji = "📊"
st.title(f"{chart_emoji} Аналитика")
st.markdown("Комплексная аналитика системы: общая статистика, AI агенты, логи")

st.markdown("---")

# TABS
tab1, tab2, tab3 = st.tabs([
    "📊 Общая аналитика",
    "🤖 Аналитика агентов",
    "📋 Логи системы"
])

# =============================================================================
# TAB 1: GENERAL ANALYTICS
# =============================================================================
with tab1:
    st.markdown("### 📊 Общая аналитика системы")

    # Load metrics
    metrics = load_system_metrics(db)

    # Metrics Dashboard (6 cards)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Всего пользователей", metrics['total_users'])
        st.metric("Завершенных грантов", metrics['completed_grants'])

    with col2:
        st.metric("Средний NPS", f"{metrics['avg_nps']}/10")
        conversion_emoji = "📈"
        st.metric(f"{conversion_emoji} Конверсия", f"{metrics['conversion_rate']}%")

    with col3:
        st.metric("Средняя стоимость", f"${metrics['avg_processing_cost']:.2f}")
        clock_emoji = "⏱️"
        st.metric(f"{clock_emoji} Среднее время", f"{metrics['avg_processing_time']} ч")

    st.markdown("---")

    # Conversion Funnel
    st.markdown("#### 📊 Воронка конверсии")

    funnel_data = load_conversion_funnel(db)

    fig_funnel = go.Figure(go.Funnel(
        y=funnel_data['stages'],
        x=funnel_data['counts'],
        textposition="inside",
        textinfo="value+percent initial",
        marker={
            "color": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]
        }
    ))

    fig_funnel.update_layout(
        title="Воронка пользователей по этапам",
        height=500
    )

    st.plotly_chart(fig_funnel, use_container_width=True)

    st.markdown("---")

    # Daily Dynamics
    st.markdown("#### 📈 Динамика по времени")

    col1, col2 = st.columns([1, 1])

    with col1:
        period_days = st.selectbox(
            "Период",
            [7, 14, 30, 60, 90],
            format_func=lambda x: f"Последние {x} дней",
            index=2
        )

    with col2:
        metric_type = st.selectbox(
            "Метрика",
            ["Сессии", "Пользователи", "Гранты"]
        )

    daily_data = load_daily_dynamics(db, days=period_days)

    if daily_data:
        # Create DataFrame
        df_daily = pd.DataFrame(list(daily_data.items()), columns=['Дата', 'Количество'])
        df_daily['Дата'] = pd.to_datetime(df_daily['Дата'])
        df_daily = df_daily.sort_values('Дата')

        # Create line chart
        fig_daily = px.line(
            df_daily,
            x='Дата',
            y='Количество',
            title=f"{metric_type} за последние {period_days} дней",
            markers=True
        )

        fig_daily.update_layout(
            xaxis_title="Дата",
            yaxis_title="Количество",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig_daily, use_container_width=True)
    else:
        st.info("Нет данных для отображения динамики")

    st.markdown("---")

    # Top Statistics
    st.markdown("#### 🏆 Топ-статистика")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Самые активные пользователи (Top 10)**")
        st.info("TODO: Реализовать запрос топ пользователей")

    with col2:
        st.markdown("**Распределение по часам дня**")
        st.info("TODO: Реализовать анализ активности по часам")

    st.markdown("---")

    # Export
    st.markdown("#### 📥 Экспорт данных")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Экспорт статистики в CSV", use_container_width=True):
            stats_df = pd.DataFrame([metrics])
            csv = stats_df.to_csv(index=False)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            st.download_button(
                label="💾 Скачать CSV",
                data=csv,
                file_name=f"analytics_stats_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col2:
        if st.button("📈 Экспорт графиков", use_container_width=True):
            st.info("Экспорт графиков доступен через Plotly (кнопка 📷 на графике)")

# =============================================================================
# TAB 2: AGENTS ANALYTICS
# =============================================================================
with tab2:
    st.markdown("### 🤖 Аналитика по AI агентам")

    # Load agents data
    agents_data = load_agents_statistics(db)

    # Overall Metrics
    col1, col2, col3, col4 = st.columns(4)

    total_runs = sum(agent.get('total_runs', 0) for agent in agents_data.values())
    total_successful = sum(agent.get('successful_runs', 0) for agent in agents_data.values())
    total_cost = sum(agent.get('avg_cost', 0) for agent in agents_data.values())
    avg_time = sum(agent.get('avg_time', 0) for agent in agents_data.values()) / max(len(agents_data), 1)

    with col1:
        lightning_emoji = "⚡"
        st.metric(f"{lightning_emoji} Всего выполнений", total_runs)

    with col2:
        clock_emoji = "⏱️"
        st.metric(f"{clock_emoji} Среднее время", f"{avg_time:.1f} мин")

    with col3:
        success_rate = (total_successful / max(total_runs, 1)) * 100
        checkmark_emoji = "✅"
        st.metric(f"{checkmark_emoji} Успешных", f"{success_rate:.1f}%")

    with col4:
        money_emoji = "💰"
        st.metric(f"{money_emoji} Расходы", f"${total_cost:.2f}")

    st.markdown("---")

    # Agent Selector
    st.markdown("#### 🔍 Детальная статистика по агенту")

    agent_name = st.selectbox(
        "Выберите агента",
        ["Все"] + list(agents_data.keys())
    )

    if agent_name == "Все":
        # Show comparison charts

        # Agent comparison table
        st.markdown("**Сравнительная таблица агентов**")

        agent_df = pd.DataFrame([
            {
                'Агент': name,
                'Всего запусков': data.get('total_runs', 0),
                'Успешных': data.get('successful_runs', 0),
                'Успешность %': f"{(data.get('successful_runs', 0) / max(data.get('total_runs', 1), 1)) * 100:.1f}",
                'Среднее время (мин)': data.get('avg_time', 0),
                'Средняя стоимость ($)': f"{data.get('avg_cost', 0):.2f}",
                'Токены': data.get('tokens_used', 0)
            }
            for name, data in agents_data.items()
        ])

        st.dataframe(agent_df, use_container_width=True)

        st.markdown("---")

        # Agent comparison charts
        col1, col2 = st.columns(2)

        with col1:
            # Processing time comparison
            st.markdown("**⏱️ Время обработки по агентам**")

            time_data = pd.DataFrame([
                {'Агент': name, 'Время (мин)': data.get('avg_time', 0)}
                for name, data in agents_data.items()
            ])

            fig_time = px.bar(
                time_data,
                x='Агент',
                y='Время (мин)',
                color='Время (мин)',
                color_continuous_scale='Blues'
            )

            st.plotly_chart(fig_time, use_container_width=True)

        with col2:
            # Cost comparison
            st.markdown("**💰 Расходы по агентам**")

            cost_data = pd.DataFrame([
                {'Агент': name, 'Стоимость': data.get('avg_cost', 0)}
                for name, data in agents_data.items()
            ])

            fig_cost = px.pie(
                cost_data,
                values='Стоимость',
                names='Агент',
                title='Распределение расходов'
            )

            st.plotly_chart(fig_cost, use_container_width=True)

    else:
        # Show specific agent details
        agent_info = agents_data.get(agent_name, {})

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Всего запусков", agent_info.get('total_runs', 0))
            st.metric("Успешных запусков", agent_info.get('successful_runs', 0))

        with col2:
            success_pct = (agent_info.get('successful_runs', 0) / max(agent_info.get('total_runs', 1), 1)) * 100
            st.metric("Успешность", f"{success_pct:.1f}%")
            st.metric("Среднее время", f"{agent_info.get('avg_time', 0):.1f} мин")

        with col3:
            st.metric("Средняя стоимость", f"${agent_info.get('avg_cost', 0):.2f}")
            st.metric("Токены использовано", agent_info.get('tokens_used', 0))

        if agent_name == "Auditor":
            st.metric("Средняя оценка", f"{agent_info.get('avg_score', 0):.1f}/10")

        if agent_name == "Writer":
            st.metric("Средняя длина текста", f"{agent_info.get('avg_text_length', 0)} символов")

    st.markdown("---")

    # Provider Comparison (for Researcher)
    st.markdown("#### 💰 Сравнение провайдеров LLM")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**GigaChat**")
        st.metric("Запросов", 0)
        st.metric("Стоимость", "$0.00")
        st.metric("Среднее время", "0 сек")

    with col2:
        st.markdown("**GPT-4**")
        st.metric("Запросов", 0)
        st.metric("Стоимость", "$0.00")
        st.metric("Среднее время", "0 сек")

# =============================================================================
# TAB 3: SYSTEM LOGS
# =============================================================================
with tab3:
    st.markdown("### 📋 Мониторинг логов системы (Real-time)")

    # Log Controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        log_level = st.selectbox(
            "Уровень логов",
            ["ALL", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )

    with col2:
        auto_refresh = st.checkbox("🔄 Автообновление (30 сек)", value=False)

    with col3:
        search_text = st.text_input("🔍 Поиск по тексту")

    with col4:
        lines_count = st.number_input(
            "Количество строк",
            min_value=10,
            max_value=1000,
            value=100,
            step=10
        )

    st.markdown("---")

    # Log Files Info
    log_stats = get_log_stats()

    if not log_stats.get('error'):
        col1, col2, col3 = st.columns(3)

        with col1:
            folder_emoji = "📁"
            st.metric(f"{folder_emoji} Папка логов", "")
            st.code(log_stats.get('log_directory', 'N/A'))

        with col2:
            st.metric("Файлов логов", len(log_stats.get('files', [])))

        with col3:
            total_size = log_stats.get('total_size', 0)
            total_size_mb = total_size / (1024 * 1024)
            st.metric("Общий размер", f"{total_size_mb:.1f} MB")

    st.markdown("---")

    # Load and display logs
    st.markdown("#### 📄 Логи системы")

    if st.button("🔄 Обновить логи", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    log_lines = load_logs(log_level=log_level, limit=lines_count, search_text=search_text)

    if log_lines:
        # Error analysis
        error_analysis = analyze_log_errors(log_lines)

        if error_analysis['total_errors'] > 0 or error_analysis['total_warnings'] > 0:
            col1, col2 = st.columns(2)

            with col1:
                if error_analysis['total_errors'] > 0:
                    error_emoji = "❌"
                    st.error(f"{error_emoji} Найдено ошибок: {error_analysis['total_errors']} (уникальных: {error_analysis['unique_errors']})")

            with col2:
                if error_analysis['total_warnings'] > 0:
                    warning_emoji = "⚠️"
                    st.warning(f"{warning_emoji} Найдено предупреждений: {error_analysis['total_warnings']} (уникальных: {error_analysis['unique_warnings']})")

        # Display logs with color coding
        log_container = st.container()

        with log_container:
            log_text = ""

            for line in log_lines:
                # Color coding based on level
                if " - ERROR - " in line or " - CRITICAL - " in line:
                    red_circle = "🔴"
                    log_text += f"{red_circle} {line}"
                elif " - WARNING - " in line:
                    yellow_circle = "🟡"
                    log_text += f"{yellow_circle} {line}"
                elif " - INFO - " in line:
                    green_circle = "🟢"
                    log_text += f"{green_circle} {line}"
                elif " - DEBUG - " in line:
                    blue_circle = "🔵"
                    log_text += f"{blue_circle} {line}"
                else:
                    white_circle = "⚪"
                    log_text += f"{white_circle} {line}"

            st.code(log_text, language=None)

        info_emoji = "📊"
        st.info(f"{info_emoji} Отображено: {len(log_lines)} строк")

    else:
        st.info("📝 Нет записей соответствующих фильтру или логи недоступны")

    st.markdown("---")

    # Error Analysis Detail
    if log_lines:
        st.markdown("#### ⚠️ Анализ ошибок")

        error_analysis = analyze_log_errors(log_lines)

        if error_analysis['error_list']:
            st.markdown("**Топ-10 уникальных ошибок:**")
            for i, error in enumerate(error_analysis['error_list'], 1):
                st.code(f"{i}. {error}", language=None)
        else:
            checkmark_emoji = "✅"
            st.success(f"{checkmark_emoji} Ошибок не обнаружено")

    st.markdown("---")

    # Log Actions
    st.markdown("#### 🛠️ Действия с логами")

    col1, col2, col3 = st.columns(3)

    with col1:
        download_emoji = "📥"
        if st.button(f"{download_emoji} Скачать логи", use_container_width=True):
            if log_lines:
                log_content = "".join(log_lines)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                st.download_button(
                    label="💾 Скачать TXT",
                    data=log_content,
                    file_name=f"grantservice_logs_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.warning("Нет логов для скачивания")

    with col2:
        trash_emoji = "🗑️"
        if st.button(f"{trash_emoji} Очистить логи", use_container_width=True):
            warning_emoji = "⚠️"
            st.warning(f"{warning_emoji} Функция очистки логов временно отключена для безопасности")

    with col3:
        test_emoji = "🧪"
        if st.button(f"{test_emoji} Создать тестовую ошибку", use_container_width=True):
            logger.error("🧪 Тестовая ошибка для проверки логирования")
            logger.warning("⚠️ Тестовое предупреждение")
            logger.info("ℹ️ Тестовое информационное сообщение")
            checkmark_emoji = "✅"
            st.success(f"{checkmark_emoji} Тестовые сообщения созданы. Обновите страницу для просмотра.")

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")

footer_text = "Страница аналитики обновлена"
rocket_emoji = "🚀"
st.info(f"{rocket_emoji} {footer_text} | Интеграция из архивных файлов завершена")

# Auto-refresh logic for logs tab
if auto_refresh and st.session_state.get('selected_tab') == 2:
    import time
    time.sleep(30)
    st.rerun()

# Log page view
logger.info("📊 Analytics page loaded successfully")
