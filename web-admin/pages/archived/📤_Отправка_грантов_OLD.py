#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GrantService Admin Panel - Отправка готовых грантов пользователям
"""

import streamlit as st
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import traceback

# Добавляем пути для импортов
current_file = Path(__file__).resolve()
web_admin_dir = current_file.parent.parent
base_dir = web_admin_dir.parent

if str(web_admin_dir) not in sys.path:
    sys.path.insert(0, str(web_admin_dir))
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

# Импорты
try:
    from data.database.models import GrantServiceDatabase
    
    # Для импорта telegram_sender добавляем путь к utils
    utils_path = web_admin_dir / "utils"
    if str(utils_path) not in sys.path:
        sys.path.insert(0, str(utils_path))
    
    from telegram_sender import send_document_to_telegram
except ImportError as e:
    st.error(f"Ошибка импорта: {e}")
    st.error(f"Пути поиска: {sys.path[:3]}...")
    st.stop()

# Настройка страницы
st.set_page_config(
    page_title="📤 Отправка грантов",
    page_icon="📤",
    layout="wide"
)

st.title("📤 Отправка готовых грантов")
st.markdown("---")

# Инициализация базы данных
@st.cache_resource
def get_database():
    """Получить подключение к базе данных"""
    try:
        # Определяем путь к базе данных в зависимости от ОС
        if os.name == 'nt':  # Windows
            db_path = str(base_dir / "data" / "grantservice.db")
        else:  # Linux
            db_path = "/var/GrantService/data/grantservice.db"
        
        return GrantServiceDatabase(db_path)
    except Exception as e:
        st.error(f"Ошибка подключения к БД: {e}")
        return None

db = get_database()
if not db:
    st.stop()

# Функция для получения списка пользователей
@st.cache_data(ttl=300)  # Кэш на 5 минут
def get_users_list():
    """Получить список пользователей"""
    try:
        users = db.get_users_for_sending()
        return users
    except Exception as e:
        st.error(f"Ошибка получения пользователей: {e}")
        return []

# Функция для получения грантовых заявок
@st.cache_data(ttl=300)  # Кэш на 5 минут  
def get_applications_list():
    """Получить список грантовых заявок"""
    try:
        applications = db.get_all_applications(limit=200)
        return applications
    except Exception as e:
        st.error(f"Ошибка получения заявок: {e}")
        return []

# Функция для получения файлов из папки ready_grants
def get_ready_files():
    """Получить список готовых файлов"""
    try:
        ready_grants_dir = base_dir / "data" / "ready_grants"
        if not ready_grants_dir.exists():
            return []
        
        files = []
        for file_path in ready_grants_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.docx', '.doc', '.txt']:
                files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                })
        
        # Сортируем по времени изменения (новые сначала)
        files.sort(key=lambda x: x['modified'], reverse=True)
        return files
    except Exception as e:
        st.error(f"Ошибка получения файлов: {e}")
        return []

# Основной интерфейс
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("👥 Выбор получателя")
    
    # Получаем список пользователей
    users = get_users_list()
    
    if not users:
        st.warning("Пользователи не найдены")
        st.stop()
    
    # Создаем словарь для отображения
    user_options = {}
    for user in users:
        user_options[user['display_name']] = user['telegram_id']
    
    selected_user_name = st.selectbox(
        "Выберите пользователя:",
        options=list(user_options.keys()),
        help="Выберите пользователя для отправки документа"
    )
    
    selected_user_id = user_options[selected_user_name]
    
    # Показываем информацию о выбранном пользователе
    selected_user = next(u for u in users if u['telegram_id'] == selected_user_id)
    
    with st.expander("ℹ️ Информация о пользователе"):
        st.metric("Telegram ID", selected_user['telegram_id'])
        st.metric("Всего сессий", selected_user['total_sessions'])
        st.metric("Завершенных заявок", selected_user['completed_applications'])
        st.text(f"Последняя активность: {selected_user['last_active']}")

with col2:
    st.subheader("📄 Выбор документа")
    
    # Вкладки для разных источников документов
    tab1, tab2, tab3 = st.tabs(["🗂️ Готовые файлы", "📋 Из заявок", "📤 Загрузить новый"])
    
    selected_file_path = None
    selected_file_name = None
    selected_grant_id = None
    
    with tab1:
        # Готовые файлы из папки
        ready_files = get_ready_files()
        
        if ready_files:
            file_options = {}
            for file_info in ready_files:
                size_mb = file_info['size'] / (1024 * 1024)
                display_name = f"{file_info['name']} ({size_mb:.1f} MB)"
                file_options[display_name] = file_info
            
            selected_file_display = st.selectbox(
                "Выберите готовый файл:",
                options=list(file_options.keys()),
                help="Файлы из папки data/ready_grants"
            )
            
            if selected_file_display:
                selected_file_info = file_options[selected_file_display]
                selected_file_path = selected_file_info['path']
                selected_file_name = selected_file_info['name']
                
                st.success(f"✅ Выбран файл: {selected_file_name}")
        else:
            st.info("Готовые файлы не найдены в папке data/ready_grants")
    
    with tab2:
        # Файлы из существующих заявок
        applications = get_applications_list()
        
        if applications:
            app_options = {}
            for app in applications:
                display_name = f"{app['application_number']} - {app['title'][:50]}..."
                app_options[display_name] = app
            
            selected_app_display = st.selectbox(
                "Выберите заявку:",
                options=list(app_options.keys()),
                help="Заявки будут экспортированы в PDF"
            )
            
            if selected_app_display:
                selected_app = app_options[selected_app_display]
                selected_grant_id = selected_app['application_number']
                selected_file_name = f"{selected_grant_id}.pdf"
                
                st.success(f"✅ Выбрана заявка: {selected_grant_id}")
                st.info("💡 Заявка будет автоматически экспортирована в PDF при отправке")
        else:
            st.info("Грантовые заявки не найдены")
    
    with tab3:
        # Загрузка нового файла
        uploaded_file = st.file_uploader(
            "Загрузите документ:",
            type=['pdf', 'docx', 'doc', 'txt'],
            help="Поддерживаемые форматы: PDF, DOCX, DOC, TXT"
        )
        
        if uploaded_file:
            # Сохраняем загруженный файл во временную папку
            ready_grants_dir = base_dir / "data" / "ready_grants"
            ready_grants_dir.mkdir(exist_ok=True)
            
            temp_file_path = ready_grants_dir / uploaded_file.name
            
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            selected_file_path = str(temp_file_path)
            selected_file_name = uploaded_file.name
            
            st.success(f"✅ Файл загружен: {uploaded_file.name}")
            st.info(f"💾 Сохранен в: {temp_file_path}")

# Комментарий администратора
st.markdown("---")
st.subheader("💬 Комментарий к отправке")

admin_comment = st.text_area(
    "Добавьте комментарий (будет отправлен вместе с файлом):",
    value="📄 Готовая грантовая заявка от GrantService",
    height=100,
    help="Этот текст будет отправлен как подпись к документу"
)

# Кнопка отправки
st.markdown("---")

if st.button("📤 Отправить документ в Telegram", type="primary", use_container_width=True):
    if not (selected_file_path or selected_grant_id):
        st.error("❌ Выберите документ для отправки!")
    elif not admin_comment.strip():
        st.error("❌ Добавьте комментарий к отправке!")
    else:
        try:
            with st.spinner("📤 Отправляем документ..."):
                # Подготавливаем данные для отправки
                document_data = {
                    'user_id': selected_user_id,
                    'file_path': selected_file_path,
                    'file_name': selected_file_name,
                    'admin_comment': admin_comment,
                    'admin_user': 'web-admin',  # Можно добавить реальное имя админа
                    'grant_application_id': selected_grant_id
                }
                
                # Если размер файла известен, добавляем его
                if selected_file_path and os.path.exists(selected_file_path):
                    document_data['file_size'] = os.path.getsize(selected_file_path)
                
                # Сохраняем информацию о документе в БД
                document_id = db.save_sent_document(document_data)
                
                if document_id:
                    # Отправляем через Telegram
                    success, message = send_document_to_telegram(
                        user_id=selected_user_id,
                        file_path=selected_file_path,
                        caption=admin_comment,
                        grant_application_id=selected_grant_id
                    )
                    
                    if success:
                        # Обновляем статус в БД
                        db.update_document_delivery_status(
                            document_id=document_id,
                            status='sent',
                            telegram_message_id=message.get('message_id')
                        )
                        
                        st.success("✅ Документ успешно отправлен!")
                        st.balloons()
                        
                        # Показываем детали отправки
                        with st.expander("📋 Детали отправки"):
                            st.json({
                                'recipient': selected_user_name,
                                'telegram_id': selected_user_id,
                                'file_name': selected_file_name,
                                'document_id': document_id,
                                'sent_at': datetime.now().isoformat(),
                                'status': 'sent'
                            })
                    else:
                        # Обновляем статус ошибки в БД
                        db.update_document_delivery_status(
                            document_id=document_id,
                            status='failed',
                            error_message=str(message)
                        )
                        
                        st.error(f"❌ Ошибка отправки: {message}")
                else:
                    st.error("❌ Ошибка сохранения информации о документе")
                    
        except Exception as e:
            st.error(f"❌ Ошибка: {e}")
            st.error(f"Детали: {traceback.format_exc()}")

# История отправок
st.markdown("---")
st.subheader("📊 История отправок")

if st.button("🔄 Обновить список"):
    st.cache_data.clear()

# Показываем последние отправки
try:
    recent_documents = db.get_sent_documents(limit=10)
    
    if recent_documents:
        for doc in recent_documents:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.text(f"👤 {doc.get('first_name', '')} {doc.get('last_name', '')}")
                    if doc.get('username'):
                        st.caption(f"@{doc['username']}")
                
                with col2:
                    st.text(f"📄 {doc['file_name']}")
                    if doc.get('grant_title'):
                        st.caption(doc['grant_title'][:50] + "...")
                
                with col3:
                    status_emoji = {
                        'pending': '⏳',
                        'sent': '✅', 
                        'delivered': '📨',
                        'failed': '❌'
                    }
                    st.text(f"{status_emoji.get(doc['delivery_status'], '❓')} {doc['delivery_status']}")
                
                with col4:
                    st.caption(doc['sent_at'][:16])
                
                if doc.get('admin_comment'):
                    st.caption(f"💬 {doc['admin_comment'][:100]}...")
                
                st.divider()
    else:
        st.info("История отправок пуста")
        
except Exception as e:
    st.error(f"Ошибка загрузки истории: {e}")

# Информационная панель
with st.sidebar:
    st.subheader("ℹ️ Справка")
    
    st.markdown("""
    ### 📤 Как отправить грант
    
    1. **Выберите получателя** из списка пользователей
    2. **Выберите документ**:
       - Готовый файл из папки
       - Экспорт из заявки
       - Загрузка нового файла
    3. **Добавьте комментарий** для пользователя
    4. **Нажмите кнопку отправки**
    
    ### 📋 Поддерживаемые форматы
    - PDF
    - DOCX, DOC
    - TXT
    
    ### 🔍 Статусы доставки
    - ⏳ **pending** - в очереди
    - ✅ **sent** - отправлено
    - 📨 **delivered** - доставлено
    - ❌ **failed** - ошибка
    """)
    
    # Статистика
    st.markdown("---")
    st.subheader("📊 Статистика")
    
    try:
        total_users = len(get_users_list())
        total_apps = len(get_applications_list())
        total_files = len(get_ready_files())
        
        st.metric("👥 Пользователей", total_users)
        st.metric("📄 Заявок", total_apps)
        st.metric("🗂️ Готовых файлов", total_files)
        
    except Exception as e:
        st.error(f"Ошибка статистики: {e}")