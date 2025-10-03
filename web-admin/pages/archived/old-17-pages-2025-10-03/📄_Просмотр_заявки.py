#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application View page - Detailed view of a single grant application
"""

import streamlit as st
import sys
import os
import json
from datetime import datetime

# Authorization check
try:
    from utils.auth import is_user_authorized
    if not is_user_authorized():
        st.error("⛔ Не авторизован. Перейдите на страницу 🔐 Вход")
        st.stop()
except ImportError as e:
    st.error(f"❌ Ошибка импорта модуля авторизации: {e}")
    st.stop()

# Database imports
try:
    from data.database import GrantServiceDatabase
    DATABASE_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Ошибка импорта базы данных: {e}")
    DATABASE_AVAILABLE = False

# Настройка страницы
st.set_page_config(
    page_title="📄 Просмотр заявки",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

def show_application_details(application_number: str):
    """Показывает детальную информацию о заявке"""
    if not DATABASE_AVAILABLE:
        st.error("❌ База данных недоступна")
        return
    
    db = GrantServiceDatabase()
    app = db.get_application_by_number(application_number)
    
    if not app:
        st.error(f"❌ Заявка #{application_number} не найдена")
        return
    
    # Заголовок
    st.title(f"📄 Заявка #{app['application_number']}")
    st.markdown("---")
    
    # Основная информация
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_emoji = {
            'draft': '📝',
            'submitted': '📤',
            'approved': '✅',
            'rejected': '❌'
        }.get(app.get('status', 'draft'), '📝')
        
        st.metric("Статус", f"{status_emoji} {app.get('status', 'draft')}")
    
    with col2:
        st.metric("Оценка качества", f"{app.get('quality_score', 0):.1f}/10")
    
    with col3:
        st.metric("LLM провайдер", app.get('llm_provider', 'Unknown'))
    
    with col4:
        created_date = app.get('created_at', '')
        if created_date:
            try:
                date_obj = datetime.fromisoformat(created_date)
                formatted_date = date_obj.strftime("%d.%m.%Y %H:%M")
            except:
                formatted_date = created_date
        else:
            formatted_date = "Неизвестно"
        st.metric("Дата создания", formatted_date)
    
    # Дополнительная техническая информация
    with st.expander("🔧 Техническая информация", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Модель", app.get('model_used', 'Unknown'))
        
        with col2:
            st.metric("Время обработки", f"{app.get('processing_time', 0):.2f} сек")
        
        with col3:
            st.metric("Токенов использовано", app.get('tokens_used', 0))
        
        with col4:
            st.metric("Автор", app.get('admin_user', 'Unknown'))
        
        if app.get('grant_fund'):
            st.metric("Грантодатель", app['grant_fund'])
        
        if app.get('requested_amount'):
            st.metric("Запрашиваемая сумма", f"{app['requested_amount']:,.0f} ₽")
        
        if app.get('project_duration'):
            st.metric("Длительность проекта", f"{app['project_duration']} мес.")
    
    # Содержание заявки
    st.subheader("📋 Содержание заявки")
    
    content = app.get('content', {})
    
    if not content:
        # Если нет content, пробуем разобрать content_json
        try:
            content = json.loads(app.get('content_json', '{}'))
        except:
            content = {}
    
    if content:
        # Определяем порядок разделов для лучшего отображения
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
        
        # Показываем разделы в определенном порядке
        for section_key in section_order:
            if section_key in content and content[section_key]:
                section_name = section_names.get(section_key, section_key.title())
                
                with st.expander(section_name, expanded=True):
                    st.write(content[section_key])
        
        # Показываем остальные разделы, которых нет в порядке
        other_sections = set(content.keys()) - set(section_order)
        for section_key in sorted(other_sections):
            if content[section_key]:
                with st.expander(f"📄 {section_key.title()}", expanded=False):
                    st.write(content[section_key])
    
    else:
        st.warning("⚠️ Содержание заявки недоступно")
        
        # Показываем краткое описание если есть
        if app.get('summary'):
            st.subheader("📝 Краткое описание")
            st.write(app['summary'])
    
    # Действия с заявкой
    st.markdown("---")
    st.subheader("🔧 Действия")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("✏️ Изменить статус", use_container_width=True):
            change_status_section(app)
    
    with col2:
        if st.button("📥 Экспорт JSON", use_container_width=True):
            export_application_json(app)
    
    with col3:
        if st.button("📋 Копировать текст", use_container_width=True):
            copy_application_text(content)
    
    with col4:
        if st.button("🔗 Поделиться", use_container_width=True):
            share_application(app['application_number'])
    
    with col5:
        if st.button("🔙 К списку", use_container_width=True):
            st.switch_page("pages/📄_Грантовые_заявки.py")

def change_status_section(app):
    """Секция для изменения статуса заявки"""
    st.subheader("✏️ Изменение статуса")
    
    current_status = app.get('status', 'draft')
    
    new_status = st.selectbox(
        "Новый статус",
        ["draft", "submitted", "approved", "rejected"],
        index=["draft", "submitted", "approved", "rejected"].index(current_status),
        format_func=lambda x: {
            "draft": "📝 Черновик",
            "submitted": "📤 Отправлена",
            "approved": "✅ Одобрена",
            "rejected": "❌ Отклонена"
        }.get(x, x)
    )
    
    reason = st.text_area(
        "Комментарий (необязательно)",
        placeholder="Укажите причину изменения статуса..."
    )
    
    if st.button("💾 Сохранить изменения", type="primary"):
        if DATABASE_AVAILABLE:
            db = GrantServiceDatabase()
            success = db.update_application_status(app['application_number'], new_status)
            
            if success:
                st.success(f"✅ Статус изменен на: {new_status}")
                st.rerun()
            else:
                st.error("❌ Ошибка изменения статуса")

def export_application_json(app):
    """Экспорт заявки в JSON"""
    export_data = {
        'application_number': app['application_number'],
        'title': app['title'],
        'status': app['status'],
        'created_at': app['created_at'],
        'content': app.get('content', {}),
        'quality_score': app['quality_score'],
        'technical_info': {
            'llm_provider': app.get('llm_provider'),
            'model_used': app.get('model_used'),
            'processing_time': app.get('processing_time'),
            'tokens_used': app.get('tokens_used')
        }
    }
    
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="📥 Скачать JSON",
        data=json_str.encode('utf-8'),
        file_name=f"grant_application_{app['application_number']}.json",
        mime="application/json"
    )

def copy_application_text(content):
    """Копирование текста заявки"""
    if not content:
        st.warning("⚠️ Нет содержания для копирования")
        return
    
    # Формируем текст заявки
    text_parts = []
    
    section_names = {
        'title': 'НАЗВАНИЕ ПРОЕКТА',
        'summary': 'КРАТКОЕ ОПИСАНИЕ',
        'problem': 'ОПИСАНИЕ ПРОБЛЕМЫ',
        'solution': 'ПРЕДЛАГАЕМОЕ РЕШЕНИЕ',
        'implementation': 'ПЛАН РЕАЛИЗАЦИИ',
        'budget': 'БЮДЖЕТ ПРОЕКТА',
        'timeline': 'ВРЕМЕННЫЕ РАМКИ',
        'team': 'КОМАНДА ПРОЕКТА',
        'impact': 'ОЖИДАЕМЫЙ РЕЗУЛЬТАТ',
        'sustainability': 'УСТОЙЧИВОСТЬ ПРОЕКТА'
    }
    
    for key, value in content.items():
        if value:
            section_title = section_names.get(key, key.upper())
            text_parts.append(f"{section_title}\n{'='*len(section_title)}\n{value}\n")
    
    full_text = '\n'.join(text_parts)
    
    st.text_area(
        "📋 Текст заявки для копирования",
        value=full_text,
        height=300,
        help="Выделите весь текст (Ctrl+A) и скопируйте (Ctrl+C)"
    )

def share_application(application_number):
    """Поделиться ссылкой на заявку"""
    # Генерируем ссылку (в реальной системе это была бы полная ссылка)
    share_url = f"http://localhost:8501/📄_Просмотр_заявки?app={application_number}"
    
    st.text_input(
        "🔗 Ссылка для доступа к заявке",
        value=share_url,
        help="Скопируйте эту ссылку для предоставления доступа к заявке"
    )
    
    # QR код (если нужно)
    st.info("💡 В будущих версиях здесь будет QR-код для быстрого доступа")

def main():
    """Главная функция страницы"""
    # Проверяем, передан ли номер заявки
    try:
        query_params = st.query_params  # Streamlit >= 1.30
    except AttributeError:
        query_params = st.experimental_get_query_params()  # Streamlit < 1.30
    
    if 'app' in query_params:
        application_number = query_params['app']
    elif 'selected_application' in st.session_state:
        application_number = st.session_state.selected_application
    else:
        # Показываем форму для ввода номера заявки
        st.title("📄 Просмотр грантовой заявки")
        st.markdown("---")
        
        application_number = st.text_input(
            "Введите номер заявки",
            placeholder="GA-20241201-ABCD1234",
            help="Введите полный номер заявки для просмотра"
        )
        
        if st.button("🔍 Найти заявку", type="primary"):
            if application_number:
                show_application_details(application_number)
            else:
                st.warning("⚠️ Введите номер заявки")
        
        # Ссылка на список заявок
        st.markdown("---")
        st.info("💡 Или перейдите к [списку всех заявок](📄_Грантовые_заявки)")
        
        return
    
    # Если номер заявки есть, показываем детали
    if application_number:
        show_application_details(application_number)

if __name__ == "__main__":
    main()

