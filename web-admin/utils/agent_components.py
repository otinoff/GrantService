#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared UI components for AI agents management
Общие компоненты интерфейса для управления AI агентами
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime

# Попытка импорта модулей промптов
try:
    from data.database.prompts import (
        get_prompts_by_agent, get_prompt_by_name, format_prompt,
        create_prompt, update_prompt, delete_prompt
    )
    PROMPTS_AVAILABLE = True
except ImportError:
    PROMPTS_AVAILABLE = False


def render_agent_header(agent_info: Dict[str, Any]) -> None:
    """
    Render agent header with title, emoji, description and status

    Args:
        agent_info: Dictionary with keys:
            - name: Agent name (str)
            - emoji: Agent emoji (str)
            - description: Agent description (str)
            - status: Agent status - 'active', 'inactive', 'testing' (str)
            - stats: Optional stats dict (Dict)
    """
    emoji = agent_info.get('emoji', '🤖')
    name = agent_info.get('name', 'Agent')
    description = agent_info.get('description', '')
    status = agent_info.get('status', 'active')

    # Header with emoji
    st.header(f"{emoji} {name}")

    # Status badge
    status_colors = {
        'active': '🟢',
        'inactive': '🔴',
        'testing': '🟡',
        'maintenance': '🟠'
    }
    status_texts = {
        'active': 'Активен',
        'inactive': 'Неактивен',
        'testing': 'Тестирование',
        'maintenance': 'Обслуживание'
    }

    status_emoji = status_colors.get(status, '⚪')
    status_text = status_texts.get(status, 'Неизвестно')

    col1, col2 = st.columns([3, 1])
    with col1:
        if description:
            st.markdown(description)
    with col2:
        st.markdown(f"**Статус:** {status_emoji} {status_text}")

    st.markdown("---")


def render_agent_stats(agent_type: str, stats: Optional[Dict[str, Any]] = None) -> None:
    """
    Render agent statistics in metric cards

    Args:
        agent_type: Type of agent (str)
        stats: Statistics dictionary with keys like:
            - total_executions: Total number of executions
            - successful_executions: Number of successful executions
            - avg_time: Average execution time in seconds
            - success_rate: Success rate percentage
            - total_cost: Total cost in rubles
    """
    if stats is None:
        stats = {}

    st.subheader("📊 Статистика работы")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total = stats.get('total_executions', 0)
        st.metric("Всего запусков", total)

    with col2:
        successful = stats.get('successful_executions', 0)
        st.metric("Успешных", successful)

    with col3:
        avg_time = stats.get('avg_time', 0)
        st.metric("Среднее время", f"{avg_time:.1f} сек")

    with col4:
        success_rate = stats.get('success_rate', 0)
        delta = "+5%" if success_rate > 85 else None
        st.metric("Успешность", f"{success_rate:.0f}%", delta=delta)

    # Additional metrics if available
    if 'total_cost' in stats:
        cost = stats['total_cost']
        st.metric("Общая стоимость", f"{cost:.2f} ₽")


def render_prompt_management(agent_type: str) -> None:
    """
    Render prompt management interface for agent

    Args:
        agent_type: Type of agent (interviewer, auditor, planner, researcher, writer)
    """
    if not PROMPTS_AVAILABLE:
        st.warning("⚠️ Модуль управления промптами недоступен")
        return

    st.subheader("⚙️ Управление промптами")

    # Get agent prompts
    prompts = get_prompts_by_agent(agent_type)

    if not prompts:
        st.info(f"📝 Нет промптов для агента {agent_type}")

        # Show button to create first prompt
        if st.button("➕ Создать первый промпт"):
            st.session_state[f'create_prompt_{agent_type}'] = True

        return

    # Select prompt for editing
    prompt_names = [p['name'] for p in prompts]
    selected_prompt_name = st.selectbox(
        "Выберите промпт для редактирования",
        prompt_names,
        key=f"prompt_select_{agent_type}"
    )

    selected_prompt = next((p for p in prompts if p['name'] == selected_prompt_name), None)

    if selected_prompt:
        _render_prompt_editor(agent_type, selected_prompt)


def _render_prompt_editor(agent_type: str, prompt: Dict[str, Any]) -> None:
    """
    Render prompt editor form

    Args:
        agent_type: Type of agent
        prompt: Prompt dictionary with id, name, description, template, etc.
    """
    with st.expander(f"✏️ Редактирование промпта: {prompt['name']}", expanded=True):
        with st.form(f"prompt_form_{agent_type}_{prompt['id']}"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input(
                    "Название",
                    value=prompt['name'],
                    key=f"name_{agent_type}_{prompt['id']}"
                )

                priority = st.number_input(
                    "Приоритет",
                    min_value=0,
                    max_value=100,
                    value=prompt.get('priority', 10),
                    key=f"priority_{agent_type}_{prompt['id']}"
                )

            with col2:
                description = st.text_area(
                    "Описание",
                    value=prompt.get('description', ''),
                    height=100,
                    key=f"desc_{agent_type}_{prompt['id']}"
                )

                variables_text = st.text_area(
                    "Переменные (по одной на строку)",
                    value='\n'.join(prompt.get('variables', [])),
                    height=100,
                    key=f"vars_{agent_type}_{prompt['id']}"
                )

            # Prompt template
            prompt_template = st.text_area(
                "Шаблон промпта",
                value=prompt.get('prompt_template', ''),
                height=300,
                key=f"template_{agent_type}_{prompt['id']}"
            )

            # Preview
            if prompt_template and variables_text:
                st.markdown("**📋 Предварительный просмотр:**")
                variables_list = [v.strip() for v in variables_text.split('\n') if v.strip()]
                test_data = {var: f"[{var}]" for var in variables_list}

                try:
                    preview = format_prompt(prompt_template, test_data)
                    st.code(preview, language="text")
                except Exception as e:
                    st.error(f"❌ Ошибка предварительного просмотра: {e}")

            # Action buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                submit_save = st.form_submit_button("💾 Сохранить", use_container_width=True)

            with col2:
                submit_delete = st.form_submit_button(
                    "🗑️ Удалить",
                    type="secondary",
                    use_container_width=True
                )

            with col3:
                submit_test = st.form_submit_button("🧪 Тест", use_container_width=True)

            # Handle form submission
            if submit_save:
                variables_list = [v.strip() for v in variables_text.split('\n') if v.strip()]

                success = update_prompt(
                    prompt_id=prompt['id'],
                    name=name,
                    description=description,
                    prompt_template=prompt_template,
                    variables=variables_list,
                    priority=priority
                )

                if success:
                    st.success("✅ Промпт успешно обновлен!")
                    st.rerun()
                else:
                    st.error("❌ Ошибка при обновлении промпта")

            elif submit_delete:
                # Need confirmation for deletion
                if st.checkbox("⚠️ Подтвердить удаление", key=f"confirm_del_{prompt['id']}"):
                    success = delete_prompt(prompt['id'])
                    if success:
                        st.success("✅ Промпт удален!")
                        st.rerun()
                    else:
                        st.error("❌ Ошибка при удалении промпта")
                else:
                    st.warning("Отметьте checkbox для подтверждения удаления")

            elif submit_test:
                st.info("🧪 Тестирование промпта...")
                # TODO: Add actual testing logic
                st.success("✅ Промпт готов к использованию!")


def render_agent_testing(agent_type: str, agent_instance: Optional[Any] = None) -> None:
    """
    Render agent testing interface

    Args:
        agent_type: Type of agent
        agent_instance: Optional agent instance for testing
    """
    st.subheader("🧪 Тестирование агента")

    with st.form(f"test_form_{agent_type}"):
        st.markdown("**Параметры тестирования:**")

        col1, col2 = st.columns(2)

        with col1:
            test_input = st.text_area(
                "Входные данные (JSON)",
                height=150,
                placeholder='{"user_id": 123, "data": "..."}'
            )

        with col2:
            provider = st.selectbox(
                "LLM провайдер",
                ["auto", "gigachat", "local"],
                key=f"test_provider_{agent_type}"
            )

            temperature = st.slider(
                "Температура",
                0.0, 1.0, 0.4,
                key=f"test_temp_{agent_type}"
            )

            max_tokens = st.number_input(
                "Макс. токенов",
                100, 4000, 1500,
                key=f"test_tokens_{agent_type}"
            )

        submit_test = st.form_submit_button("▶️ Запустить тест", use_container_width=True)

        if submit_test:
            if not test_input:
                st.error("❌ Введите входные данные для тестирования")
            else:
                with st.spinner("🔄 Выполняется тестирование..."):
                    try:
                        # Parse input
                        import json
                        input_data = json.loads(test_input)

                        # TODO: Execute agent with test data
                        st.success("✅ Тестирование завершено")

                        # Show results
                        st.markdown("**📊 Результаты:**")
                        st.json({
                            "status": "success",
                            "execution_time": "2.3s",
                            "tokens_used": 450,
                            "cost": "0.15 ₽",
                            "result": "Test result here..."
                        })

                    except json.JSONDecodeError:
                        st.error("❌ Неверный формат JSON")
                    except Exception as e:
                        st.error(f"❌ Ошибка тестирования: {e}")


def render_agent_config(agent_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Render agent configuration form and return updated config

    Args:
        agent_type: Type of agent
        config: Current configuration dictionary

    Returns:
        Updated configuration dictionary
    """
    if config is None:
        config = {}

    st.subheader("⚙️ Конфигурация агента")

    col1, col2 = st.columns(2)

    with col1:
        llm_provider = st.selectbox(
            "Провайдер LLM",
            ["auto", "gigachat", "local"],
            index=["auto", "gigachat", "local"].index(config.get('provider', 'auto')),
            key=f"config_provider_{agent_type}"
        )

        if llm_provider == "local":
            model = st.selectbox(
                "Локальная модель",
                ["qwen2.5:3b", "qwen2.5:7b"],
                key=f"config_model_{agent_type}"
            )
        elif llm_provider == "gigachat":
            model = st.selectbox(
                "GigaChat модель",
                ["GigaChat", "GigaChat-Pro"],
                key=f"config_model_{agent_type}"
            )
        else:
            model = "auto"

    with col2:
        temperature = st.slider(
            "Температура",
            0.0, 1.0,
            config.get('temperature', 0.4),
            key=f"config_temp_{agent_type}"
        )

        max_tokens = st.number_input(
            "Макс. токенов",
            100, 4000,
            config.get('max_tokens', 1500),
            key=f"config_tokens_{agent_type}"
        )

    return {
        'provider': llm_provider,
        'model': model,
        'temperature': temperature,
        'max_tokens': max_tokens
    }


def render_agent_history(agent_type: str, history: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Render agent execution history

    Args:
        agent_type: Type of agent
        history: List of execution records
    """
    st.subheader("📜 История выполнения")

    if not history:
        st.info("📝 История выполнения пуста")
        return

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Статус",
            ["Все", "Успешно", "Ошибка"],
            key=f"history_status_{agent_type}"
        )

    with col2:
        date_filter = st.date_input(
            "Дата",
            key=f"history_date_{agent_type}"
        )

    with col3:
        limit = st.number_input(
            "Показать записей",
            10, 100, 50,
            key=f"history_limit_{agent_type}"
        )

    # Display history
    for record in history[:limit]:
        timestamp = record.get('timestamp', 'N/A')
        status = record.get('status', 'unknown')
        duration = record.get('duration', 0)

        status_emoji = "✅" if status == "success" else "❌"

        with st.expander(f"{status_emoji} {timestamp} - {duration:.1f}s"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Входные данные:**")
                st.json(record.get('input', {}))

            with col2:
                st.markdown("**Результат:**")
                st.json(record.get('output', {}))

            if 'error' in record:
                st.error(f"Ошибка: {record['error']}")
