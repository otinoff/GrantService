#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Helper Components for GrantService Admin Panel
Переиспользуемые UI компоненты для админ-панели
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, date
import pandas as pd


def render_page_header(title: str, icon: str = "", description: str = "") -> None:
    """
    Render standardized page header

    Args:
        title: Page title
        icon: Optional emoji icon
        description: Optional page description
    """
    if icon:
        st.title(f"{icon} {title}")
    else:
        st.title(title)

    if description:
        st.markdown(description)

    st.markdown("---")


def render_metric_cards(metrics: List[Dict[str, Any]], columns: int = 4) -> None:
    """
    Render metric cards in a grid

    Args:
        metrics: List of metric dictionaries with keys:
            - label: Metric label
            - value: Metric value
            - delta: Optional delta value
            - help: Optional help text
        columns: Number of columns in grid
    """
    cols = st.columns(columns)

    for idx, metric in enumerate(metrics):
        col_idx = idx % columns
        with cols[col_idx]:
            st.metric(
                label=metric.get('label', 'Metric'),
                value=metric.get('value', 0),
                delta=metric.get('delta'),
                help=metric.get('help')
            )


def render_filters(filters: List[Dict[str, Any]], key_prefix: str = "filter") -> Dict[str, Any]:
    """
    Render filter controls and return filter values

    Args:
        filters: List of filter configurations with keys:
            - type: 'select', 'multiselect', 'date', 'date_range', 'text', 'number'
            - label: Filter label
            - options: Options for select/multiselect
            - default: Default value
            - key: Optional unique key
        key_prefix: Prefix for session state keys

    Returns:
        Dictionary of filter values
    """
    filter_values = {}
    cols = st.columns(len(filters))

    for idx, filter_config in enumerate(filters):
        with cols[idx]:
            filter_type = filter_config.get('type', 'text')
            label = filter_config.get('label', 'Filter')
            key = filter_config.get('key', f"{key_prefix}_{idx}")

            if filter_type == 'select':
                value = st.selectbox(
                    label,
                    options=filter_config.get('options', []),
                    index=filter_config.get('default', 0),
                    key=key
                )

            elif filter_type == 'multiselect':
                value = st.multiselect(
                    label,
                    options=filter_config.get('options', []),
                    default=filter_config.get('default', []),
                    key=key
                )

            elif filter_type == 'date':
                value = st.date_input(
                    label,
                    value=filter_config.get('default', date.today()),
                    key=key
                )

            elif filter_type == 'date_range':
                value = st.date_input(
                    label,
                    value=filter_config.get('default', (date.today(), date.today())),
                    key=key
                )

            elif filter_type == 'text':
                value = st.text_input(
                    label,
                    value=filter_config.get('default', ''),
                    placeholder=filter_config.get('placeholder', ''),
                    key=key
                )

            elif filter_type == 'number':
                value = st.number_input(
                    label,
                    min_value=filter_config.get('min', 0),
                    max_value=filter_config.get('max', 100),
                    value=filter_config.get('default', 0),
                    key=key
                )

            else:
                value = None

            filter_values[key] = value

    return filter_values


def render_data_table(
    data: pd.DataFrame,
    column_config: Optional[Dict[str, Any]] = None,
    hide_index: bool = True,
    use_container_width: bool = True,
    height: Optional[int] = None
) -> None:
    """
    Render styled data table

    Args:
        data: DataFrame to display
        column_config: Streamlit column configuration
        hide_index: Hide DataFrame index
        use_container_width: Use full container width
        height: Optional table height
    """
    if data.empty:
        st.info("📭 Нет данных для отображения")
        return

    st.dataframe(
        data,
        column_config=column_config,
        hide_index=hide_index,
        use_container_width=use_container_width,
        height=height
    )


def render_info_card(title: str, content: str, icon: str = "ℹ️", type: str = "info") -> None:
    """
    Render information card with styling

    Args:
        title: Card title
        content: Card content
        icon: Icon emoji
        type: Card type - 'info', 'success', 'warning', 'error'
    """
    card_styles = {
        'info': ('🔵', st.info),
        'success': ('🟢', st.success),
        'warning': ('🟡', st.warning),
        'error': ('🔴', st.error)
    }

    emoji, func = card_styles.get(type, ('ℹ️', st.info))

    with st.container():
        st.markdown(f"### {icon} {title}")
        func(content)


def render_action_buttons(
    buttons: List[Dict[str, Any]],
    columns: Optional[int] = None,
    use_container_width: bool = False
) -> str:
    """
    Render action buttons in a row and return clicked button key

    Args:
        buttons: List of button configurations with keys:
            - label: Button label
            - key: Unique button key
            - type: Button type - 'primary', 'secondary'
            - icon: Optional icon
            - disabled: Optional disabled state
        columns: Number of columns (default: number of buttons)
        use_container_width: Use full column width

    Returns:
        Key of clicked button or empty string
    """
    num_cols = columns or len(buttons)
    cols = st.columns(num_cols)

    clicked_key = ""

    for idx, button in enumerate(buttons):
        col_idx = idx % num_cols
        with cols[col_idx]:
            label = button.get('label', 'Button')
            key = button.get('key', f'btn_{idx}')
            btn_type = button.get('type', 'secondary')
            icon = button.get('icon', '')
            disabled = button.get('disabled', False)

            full_label = f"{icon} {label}" if icon else label

            if st.button(
                full_label,
                key=key,
                type=btn_type,
                disabled=disabled,
                use_container_width=use_container_width
            ):
                clicked_key = key

    return clicked_key


def render_search_box(
    placeholder: str = "Поиск...",
    key: str = "search",
    on_change: Optional[Callable] = None
) -> str:
    """
    Render search input box

    Args:
        placeholder: Placeholder text
        key: Session state key
        on_change: Optional callback function

    Returns:
        Search query string
    """
    search_icon = "🔍"
    search_query = st.text_input(
        f"{search_icon} Поиск",
        placeholder=placeholder,
        key=key,
        on_change=on_change,
        label_visibility="collapsed"
    )

    return search_query.strip()


def render_pagination(
    total_items: int,
    items_per_page: int = 20,
    key: str = "pagination"
) -> tuple:
    """
    Render pagination controls

    Args:
        total_items: Total number of items
        items_per_page: Items per page
        key: Session state key prefix

    Returns:
        Tuple of (start_idx, end_idx)
    """
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

    col1, col2, col3 = st.columns([2, 3, 2])

    with col1:
        items_per_page = st.selectbox(
            "Записей на странице",
            [10, 20, 50, 100],
            index=1,
            key=f"{key}_per_page"
        )

    with col2:
        current_page = st.number_input(
            "Страница",
            min_value=1,
            max_value=total_pages,
            value=1,
            key=f"{key}_page"
        )

    with col3:
        st.write(f"Всего: {total_items} записей")

    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)

    return start_idx, end_idx


def render_status_badge(status: str, custom_colors: Optional[Dict[str, str]] = None) -> None:
    """
    Render status badge with color

    Args:
        status: Status text
        custom_colors: Optional custom color mapping
    """
    default_colors = {
        'active': '🟢',
        'inactive': '🔴',
        'pending': '🟡',
        'success': '🟢',
        'error': '🔴',
        'warning': '🟡',
        'info': '🔵'
    }

    colors = custom_colors or default_colors
    emoji = colors.get(status.lower(), '⚪')

    st.markdown(f"{emoji} **{status}**")


def render_expandable_section(
    title: str,
    content_func: Callable,
    icon: str = "📋",
    expanded: bool = False
) -> None:
    """
    Render expandable section with content

    Args:
        title: Section title
        content_func: Function that renders content when called
        icon: Section icon
        expanded: Initial expanded state
    """
    with st.expander(f"{icon} {title}", expanded=expanded):
        content_func()


def render_loading_spinner(message: str = "Загрузка...") -> Any:
    """
    Render loading spinner context manager

    Args:
        message: Loading message

    Returns:
        Streamlit spinner context manager
    """
    return st.spinner(message)


def show_success_message(message: str, duration: int = 3) -> None:
    """
    Show success message

    Args:
        message: Success message
        duration: Display duration in seconds
    """
    st.success(f"✅ {message}")


def show_error_message(message: str) -> None:
    """
    Show error message

    Args:
        message: Error message
    """
    st.error(f"❌ {message}")


def show_warning_message(message: str) -> None:
    """
    Show warning message

    Args:
        message: Warning message
    """
    st.warning(f"⚠️ {message}")


def show_info_message(message: str) -> None:
    """
    Show info message

    Args:
        message: Info message
    """
    st.info(f"ℹ️ {message}")


def confirm_action(message: str, key: str = "confirm") -> bool:
    """
    Show confirmation dialog

    Args:
        message: Confirmation message
        key: Unique key for checkbox

    Returns:
        True if confirmed
    """
    return st.checkbox(f"⚠️ {message}", key=key)


def render_json_viewer(data: Any, expanded: bool = False) -> None:
    """
    Render JSON data viewer

    Args:
        data: Data to display as JSON
        expanded: Show in expander if False
    """
    if expanded:
        st.json(data)
    else:
        with st.expander("📄 Просмотр JSON"):
            st.json(data)


def render_code_block(code: str, language: str = "python", show_line_numbers: bool = True) -> None:
    """
    Render code block with syntax highlighting

    Args:
        code: Code to display
        language: Programming language for syntax highlighting
        show_line_numbers: Show line numbers
    """
    st.code(code, language=language)


def render_download_button(
    data: Any,
    filename: str,
    label: str = "Скачать",
    mime_type: str = "text/csv",
    key: str = "download"
) -> None:
    """
    Render download button

    Args:
        data: Data to download
        filename: Downloaded filename
        label: Button label
        mime_type: MIME type
        key: Unique key
    """
    download_icon = "⬇️"
    st.download_button(
        label=f"{download_icon} {label}",
        data=data,
        file_name=filename,
        mime=mime_type,
        key=key
    )


def render_tabs(tab_names: List[str], icons: Optional[List[str]] = None) -> Any:
    """
    Render tabs with optional icons

    Args:
        tab_names: List of tab names
        icons: Optional list of emoji icons

    Returns:
        Streamlit tabs object
    """
    if icons and len(icons) == len(tab_names):
        tab_labels = [f"{icon} {name}" for icon, name in zip(icons, tab_names)]
    else:
        tab_labels = tab_names

    return st.tabs(tab_labels)
