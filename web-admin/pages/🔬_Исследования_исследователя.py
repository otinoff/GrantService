#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница для просмотра исследований Researcher Agent
"""

import streamlit as st
import sys
import os
from datetime import datetime
import json

import streamlit as st
import sys
import os

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

# Проверка авторизации
from web_admin.utils.auth import is_user_authorized

if not is_user_authorized():
    # Импортируем страницу входа
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "login_page", 
        "/var/GrantService/web-admin/pages/🔐_Вход.py"
    )
    login_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(login_module)
    login_module.show_login_page()
    st.stop()
# Добавляем путь к проекту
sys.path.append('/var/GrantService')

from data.database.models import GrantServiceDatabase
from utils.logger import setup_logger

# Инициализация базы данных
db = GrantServiceDatabase()

# Инициализация логгера
logger = setup_logger('researcher_research')

st.set_page_config(
    page_title="🔬 Исследования исследователя",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок страницы
st.title("🔬 Исследования исследователя")

# Инициализация БД
try:
    db_instance = db
    logger.info("✅ База данных успешно инициализирована")
except Exception as e:
    st.error(f"❌ Ошибка подключения к базе данных: {e}")
    logger.critical(f"Критическая ошибка БД: {e}", exc_info=True)
    st.stop()

# Боковая панель с фильтрами
st.sidebar.title("🎯 Фильтры")

# Фильтр по статусу
status_filter = st.sidebar.selectbox(
    "Статус",
    ["Все статусы", "completed", "pending", "processing", "error"],
    key="status_filter"
)

# Фильтр по периоду
period_filter = st.sidebar.selectbox(
    "Период",
    ["Все время", "Сегодня", "Неделя", "Месяц"],
    key="period_filter"
)

# Фильтр по LLM провайдеру
provider_filter = st.sidebar.selectbox(
    "LLM провайдер",
    ["Все", "perplexity", "gigachat", "ollama"],
    key="provider_filter"
)

# Фильтр по пользователю
user_filter = st.sidebar.text_input(
    "Пользователь (username или ID)",
    placeholder="Введите username или telegram_id",
    key="user_filter"
)

# Основная область контента
st.subheader("📊 Статистика исследований")

try:
    # Получаем статистику
    stats = db_instance.get_research_statistics()
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Всего исследований",
                value=stats.get('total_research', 0)
            )
        
        with col2:
            completed = stats.get('status_distribution', {}).get('completed', 0)
            st.metric(
                label="Завершенных",
                value=completed
            )
        
        with col3:
            pending = stats.get('status_distribution', {}).get('pending', 0)
            st.metric(
                label="В обработке",
                value=pending
            )
        
        with col4:
            error = stats.get('status_distribution', {}).get('error', 0)
            st.metric(
                label="Ошибок",
                value=error
            )
        
        # Распределение по провайдерам
        st.subheader("📈 Распределение по провайдерам")
        provider_dist = stats.get('provider_distribution', {})
        
        if provider_dist:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**По провайдерам:**")
                for provider, count in provider_dist.items():
                    st.write(f"• {provider}: {count}")
            
            with col2:
                st.write("**Топ пользователи:**")
                top_users = stats.get('top_users', {})
                for user, count in list(top_users.items())[:5]:
                    st.write(f"• @{user}: {count}")
    
except Exception as e:
    st.error(f"❌ Ошибка получения статистики: {e}")
    logger.error(f"Ошибка получения статистики: {e}")

# Список исследований
st.subheader("📋 Список исследований")

try:
    # Получаем все исследования
    all_research = db_instance.get_all_research(limit=100)
    
    if not all_research:
        st.info("🔍 Исследования не найдены")
    else:
        # Применяем фильтры
        filtered_research = all_research
        
        if status_filter != "Все статусы":
            filtered_research = [r for r in filtered_research if r['status'] == status_filter]
        
        if provider_filter != "Все":
            filtered_research = [r for r in filtered_research if r['llm_provider'] == provider_filter]
        
        if user_filter:
            user_filter_lower = user_filter.lower()
            filtered_research = [r for r in filtered_research 
                               if (r.get('username', '').lower().find(user_filter_lower) != -1 or 
                                   str(r.get('user_id', '')).find(user_filter) != -1)]
        
        # Отображаем количество отфильтрованных результатов
        st.write(f"**Найдено исследований: {len(filtered_research)}**")
        
        # Отображаем исследования
        for research in filtered_research:
            with st.expander(f"🔬 {research['research_id']} - {research.get('username', 'Unknown')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID исследования:** {research['research_id']}")
                    st.write(f"**ID анкеты:** {research['anketa_id']}")
                    st.write(f"**Пользователь:** @{research.get('username', 'N/A')} ({research.get('first_name', '')} {research.get('last_name', '')})")
                    st.write(f"**Telegram ID:** {research['user_id']}")
                    st.write(f"**Статус:** {research['status']}")
                
                with col2:
                    st.write(f"**LLM провайдер:** {research['llm_provider']}")
                    st.write(f"**Модель:** {research.get('model', 'N/A')}")
                    st.write(f"**Тип исследования:** {research.get('research_type', 'comprehensive')}")
                    st.write(f"**Создано:** {research['created_at']}")
                    if research.get('completed_at'):
                        st.write(f"**Завершено:** {research['completed_at']}")
                
                # Метаданные
                if research.get('metadata'):
                    metadata = research['metadata']
                    st.write("**Метаданные:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"• Токенов: {metadata.get('tokens_used', 0)}")
                    with col2:
                        st.write(f"• Время: {metadata.get('processing_time_seconds', 0)} сек")
                    with col3:
                        st.write(f"• Стоимость: {metadata.get('cost', 0.0)} ₽")
                
                # Результаты исследования
                if research.get('research_results'):
                    st.write("**Результаты исследования:**")
                    st.text_area(
                        "Содержание",
                        value=research['research_results'],
                        height=200,
                        key=f"results_{research['id']}"
                    )
                
                # Кнопки действий
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("📄 Просмотр анкеты", key=f"view_anketa_{research['id']}"):
                        st.session_state.selected_anketa_id = research['anketa_id']
                        st.rerun()
                
                with col2:
                    if st.button("📊 Детали", key=f"details_{research['id']}"):
                        st.session_state.selected_research_id = research['research_id']
                        st.rerun()
                
                with col3:
                    if st.button("📋 Копировать ID", key=f"copy_{research['id']}"):
                        st.code(research['research_id'])
                        st.success("ID скопирован!")
                
                with col4:
                    if st.button("💾 Экспорт", key=f"export_{research['id']}"):
                        st.session_state.selected_research_export = research['research_id']
                        st.rerun()

except Exception as e:
    st.error(f"❌ Ошибка получения исследований: {e}")
    logger.error(f"Ошибка получения исследований: {e}")

# Детальный просмотр исследования
if 'selected_research_id' in st.session_state:
    st.subheader("📊 Детальный просмотр исследования")
    
    try:
        research = db_instance.get_research_by_id(st.session_state.selected_research_id)
        
        if research:
            st.json(research)
        else:
            st.error("Исследование не найдено")
            
    except Exception as e:
        st.error(f"❌ Ошибка получения деталей исследования: {e}")

# Просмотр связанной анкеты
if 'selected_anketa_id' in st.session_state:
    st.subheader("📄 Связанная анкета")
    
    try:
        anketa = db_instance.get_session_by_anketa_id(st.session_state.selected_anketa_id)
        
        if anketa:
            st.write(f"**ID анкеты:** {anketa['anketa_id']}")
            st.write(f"**Пользователь:** @{anketa.get('username', 'N/A')} ({anketa.get('first_name', '')} {anketa.get('last_name', '')})")
            st.write(f"**Статус:** {anketa['status']}")
            st.write(f"**Создано:** {anketa['started_at']}")
            
            if anketa.get('interview_data'):
                st.write("**Данные интервью:**")
                st.json(anketa['interview_data'])
        else:
            st.error("Анкета не найдена")
            
    except Exception as e:
        st.error(f"❌ Ошибка получения анкеты: {e}")

# Экспорт исследования
if 'selected_research_export' in st.session_state:
    st.subheader("💾 Экспорт исследования")
    
    try:
        research = db_instance.get_research_by_id(st.session_state.selected_research_export)
        
        if research:
            # Получаем связанную анкету
            anketa = db_instance.get_session_by_anketa_id(research['anketa_id'])
            
            # Формируем данные для экспорта
            export_data = {
                "research_id": research['research_id'],
                "anketa_id": research['anketa_id'],
                "user": {
                    "username": research.get('username'),
                    "first_name": research.get('first_name'),
                    "last_name": research.get('last_name'),
                    "telegram_id": research['user_id']
                },
                "research_info": {
                    "status": research['status'],
                    "llm_provider": research['llm_provider'],
                    "model": research.get('model'),
                    "research_type": research.get('research_type'),
                    "created_at": research['created_at'],
                    "completed_at": research.get('completed_at')
                },
                "metadata": research.get('metadata', {}),
                "research_results": research.get('research_results', ''),
                "logs": research.get('logs', ''),
                "anketa_data": anketa.get('interview_data', {}) if anketa else {}
            }
            
            # Выбор формата экспорта
            export_format = st.selectbox(
                "Выберите формат экспорта:",
                ["JSON", "TXT", "Markdown"],
                key="export_format"
            )
            
            if export_format == "JSON":
                # JSON экспорт
                json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 Скачать JSON",
                    data=json_data,
                    file_name=f"research_{research['research_id']}.json",
                    mime="application/json"
                )
                
                # Показываем превью
                st.subheader("📄 Превью JSON:")
                st.json(export_data)
            
            elif export_format == "TXT":
                # TXT экспорт
                txt_content = f"""ИССЛЕДОВАНИЕ: {research['research_id']}
Анкета: {research['anketa_id']}
Пользователь: @{research.get('username', 'N/A')} ({research.get('first_name', '')} {research.get('last_name', '')})
Telegram ID: {research['user_id']}

ИНФОРМАЦИЯ ОБ ИССЛЕДОВАНИИ:
Статус: {research['status']}
LLM провайдер: {research['llm_provider']}
Модель: {research.get('model', 'N/A')}
Тип исследования: {research.get('research_type', 'comprehensive')}
Создано: {research['created_at']}
Завершено: {research.get('completed_at', 'N/A')}

МЕТАДАННЫЕ:
{json.dumps(research.get('metadata', {}), ensure_ascii=False, indent=2)}

РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ:
{research.get('research_results', 'Нет данных')}

ЛОГИ ПРОЦЕССА:
{research.get('logs', 'Нет логов')}

ДАННЫЕ АНКЕТЫ:
{json.dumps(anketa.get('interview_data', {}), ensure_ascii=False, indent=2) if anketa else 'Анкета не найдена'}
"""
                
                st.download_button(
                    label="📥 Скачать TXT",
                    data=txt_content,
                    file_name=f"research_{research['research_id']}.txt",
                    mime="text/plain"
                )
                
                # Показываем превью
                st.subheader("📄 Превью TXT:")
                st.text_area("Содержание", value=txt_content, height=400, key="txt_preview")
            
            elif export_format == "Markdown":
                # Markdown экспорт
                md_content = f"""# Исследование: {research['research_id']}

## Основная информация
- **Анкета:** {research['anketa_id']}
- **Пользователь:** @{research.get('username', 'N/A')} ({research.get('first_name', '')} {research.get('last_name', '')})
- **Telegram ID:** {research['user_id']}

## Информация об исследовании
- **Статус:** {research['status']}
- **LLM провайдер:** {research['llm_provider']}
- **Модель:** {research.get('model', 'N/A')}
- **Тип исследования:** {research.get('research_type', 'comprehensive')}
- **Создано:** {research['created_at']}
- **Завершено:** {research.get('completed_at', 'N/A')}

## Метаданные
```json
{json.dumps(research.get('metadata', {}), ensure_ascii=False, indent=2)}
```

## Результаты исследования
{research.get('research_results', 'Нет данных')}

## Логи процесса
```
{research.get('logs', 'Нет логов')}
```

## Данные анкеты
```json
{json.dumps(anketa.get('interview_data', {}), ensure_ascii=False, indent=2) if anketa else 'Анкета не найдена'}
```
"""
                
                st.download_button(
                    label="📥 Скачать Markdown",
                    data=md_content,
                    file_name=f"research_{research['research_id']}.md",
                    mime="text/markdown"
                )
                
                # Показываем превью
                st.subheader("📄 Превью Markdown:")
                st.markdown(md_content)
            
            # Кнопка закрытия
            if st.button("❌ Закрыть экспорт"):
                del st.session_state.selected_research_export
                st.rerun()
                
        else:
            st.error("Исследование не найдено")
            
    except Exception as e:
        st.error(f"❌ Ошибка экспорта: {e}")
        logger.error(f"Ошибка экспорта: {e}")

# Информация в боковой панели
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Информация")
st.sidebar.info("""
**Исследования Researcher Agent**

Эта страница показывает все исследования, проведенные Researcher Agent на основе анкет пользователей.

**Структура ID:**
- Анкета: `#AN-YYYYMMDD-username-001`
- Исследование: `#RS-YYYYMMDD-username-001-AN-anketa_id`

**Связи:**
- Каждое исследование привязано к конкретной анкете
- Анкета и исследование передаются писателю как единый пакет

**Экспорт:**
- JSON: полные данные в структурированном формате
- TXT: читаемый текстовый формат
- Markdown: форматированный документ
""")
