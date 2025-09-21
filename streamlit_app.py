#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GrantService Admin Panel - Streamlit Application
Авторизация через токен из Telegram бота
Кроссплатформенная версия
"""

import streamlit as st
import sys
import os
import time
from datetime import datetime, timedelta
import json

# Импортируем кроссплатформенную конфигурацию путей
from config import paths

# Импортируем модули БД
from data.database import db, auth_manager
from data.database.auth import UserRole

# Настройка страницы
st.set_page_config(
    page_title="GrantService Admin",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_token_from_url():
    """Проверить токен из URL параметров"""
    query_params = st.query_params
    token = query_params.get('token')
    
    if token:
        # Проверяем токен
        user_data = db.validate_login_token(token)
        if user_data:
            # Сохраняем данные пользователя в сессии
            st.session_state['authenticated'] = True
            st.session_state['user_data'] = user_data
            st.session_state['token'] = token
            
            # Логируем успешный вход
            auth_manager.log_auth_action(
                user_id=user_data['id'],
                action='login_success',
                success=True
            )
            
            # Отправляем уведомление в Telegram о входе (асинхронно)
            try:
                import requests
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                if bot_token and user_data.get('telegram_id'):
                    notification_text = f"""
🔔 *Уведомление о входе*

✅ Вы успешно вошли в админ-панель GrantService

📅 Время входа: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
🌐 IP: {st.session_state.get('remote_ip', 'Unknown')}

Если это были не вы, немедленно используйте команду /revoke_access для отзыва токена!
"""
                    requests.post(
                        f'https://api.telegram.org/bot{bot_token}/sendMessage',
                        json={
                            'chat_id': user_data['telegram_id'],
                            'text': notification_text,
                            'parse_mode': 'Markdown'
                        },
                        timeout=5
                    )
            except:
                pass  # Не блокируем вход при ошибке отправки уведомления
            
            # Очищаем токен из URL для безопасности
            st.query_params.clear()
            
            return True
    
    return False

def login_with_token():
    """Страница входа через Telegram"""
    # Проверяем токен из URL при каждом обновлении
    if check_token_from_url():
        st.success("✅ Авторизация успешна!")
        time.sleep(1)
        st.rerun()
        return
    
    # Центрируем контент
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <style>
        .main-title {
            text-align: center;
            color: #1f77b4;
            margin-bottom: 30px;
        }
        .stButton > button {
            width: 100%;
            height: 60px;
            font-size: 20px;
            font-weight: bold;
            background-color: #0088cc;
            color: white;
            border-radius: 10px;
            border: none;
            margin-top: 20px;
        }
        .stButton > button:hover {
            background-color: #006699;
        }
        .info-box {
            background-color: #f0f8ff;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #0088cc;
        }
        .security-note {
            background-color: #fff3cd;
            border-radius: 5px;
            padding: 10px;
            margin-top: 20px;
            border-left: 4px solid #ffc107;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<h1 class="main-title">🏛️ GrantService Admin</h1>', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align: center; color: #666;">Вход через Telegram</h3>', unsafe_allow_html=True)
        
        # Информационный блок
        st.markdown("""
        <div class="info-box">
            <h4>🔐 Безопасная авторизация</h4>
            <p>Для входа в админ-панель используется ваш Telegram аккаунт.
            Никаких паролей запоминать не нужно!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Получаем имя бота из переменной окружения или используем правильное имя
        bot_username = os.getenv('TELEGRAM_BOT_USERNAME', 'GrantServiceHelperBot')
        
        # Кнопка для открытия Telegram бота
        telegram_url = f"https://t.me/{bot_username}?start=get_access"
        
        st.markdown(f"""
        ### 📱 Шаг 1: Откройте Telegram бот
        
        Нажмите кнопку ниже, чтобы открыть наш бот в Telegram:
        """)
        
        # Создаем HTML кнопку для открытия Telegram
        st.markdown(f"""
        <a href="{telegram_url}" target="_blank" style="text-decoration: none;">
            <button style="
                width: 100%;
                height: 60px;
                font-size: 20px;
                font-weight: bold;
                background-color: #0088cc;
                color: white;
                border-radius: 10px;
                border: none;
                cursor: pointer;
                margin: 10px 0;
            ">
                🚀 Открыть @{bot_username}
            </button>
        </a>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 🔗 Шаг 2: Получите ссылку для входа
        
        1. В боте автоматически выполнится команда `/get_access`
        2. Бот пришлет вам уникальную ссылку для входа
        3. Перейдите по ссылке - и вы в системе!
        """)
        
        # Автоматическое обновление страницы для проверки токена
        st.markdown("""
        ### ⏳ Ожидание авторизации...
        
        После получения ссылки в Telegram, перейдите по ней.
        Страница обновится автоматически.
        """)
        
        # Добавляем автообновление каждые 3 секунды
        st.markdown("""
        <script>
        setTimeout(function(){
            window.location.reload();
        }, 3000);
        </script>
        """, unsafe_allow_html=True)
        
        # Предупреждение о безопасности
        st.markdown("""
        <div class="security-note">
            <strong>🔒 Безопасность:</strong><br>
            • Токены действуют 24 часа<br>
            • Каждый токен уникален<br>
            • Привязка к вашему Telegram ID<br>
            • Не делитесь ссылками с другими
        </div>
        """, unsafe_allow_html=True)
        
        # Альтернативный способ - QR код (опционально)
        with st.expander("📷 Альтернативный способ - QR код"):
            import qrcode
            import io
            from PIL import Image
            
            # Генерируем QR код для Telegram ссылки
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(telegram_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Конвертируем в байты для отображения
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            
            st.image(buf, caption=f"Сканируйте QR код для открытия @{bot_username}", width=200)
            st.caption("Используйте камеру Telegram для сканирования")

def show_user_info():
    """Показать информацию о текущем пользователе"""
    user_data = st.session_state.get('user_data', {})
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.metric("👤 Пользователь", user_data.get('username', 'Unknown'))
        
    with col2:
        role = auth_manager.get_user_role(user_data.get('telegram_id'))
        role_emoji = {
            'admin': '👑',
            'editor': '✏️',
            'viewer': '👁️',
            'user': '👤'
        }.get(role, '👤')
        st.metric("🎭 Роль", f"{role_emoji} {role}")
        
    with col3:
        if st.button("🚪 Выйти", type="secondary"):
            # Очищаем сессию
            for key in ['authenticated', 'user_data', 'token']:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Логируем выход
            auth_manager.log_auth_action(
                user_id=user_data.get('id'),
                action='logout',
                success=True
            )
            
            st.rerun()

def main_dashboard():
    """Главная панель управления"""
    st.title("🏛️ GrantService Admin Panel")
    
    # Показываем информацию о пользователе
    show_user_info()
    
    st.divider()
    
    # Получаем роль пользователя
    user_data = st.session_state.get('user_data', {})
    user_role = auth_manager.get_user_role(user_data.get('telegram_id'))
    
    # Боковая панель с навигацией
    with st.sidebar:
        st.header("📍 Навигация")
        
        page = st.radio(
            "Выберите раздел:",
            options=[
                "📊 Дашборд",
                "📝 Анкеты",
                "👥 Пользователи",
                "❓ Вопросы",
                "📈 Аналитика"
            ]
        )
        
        if user_role == 'admin':
            st.divider()
            st.subheader("⚙️ Администрирование")
            
            admin_page = st.radio(
                "Админ-разделы:",
                options=[
                    "🔐 Управление доступом",
                    "📋 Логи авторизации",
                    "⚡ Системные настройки"
                ]
            )
    
    # Основной контент
    if page == "📊 Дашборд":
        show_dashboard()
    elif page == "📝 Анкеты":
        show_anketas()
    elif page == "👥 Пользователи":
        show_users()
    elif page == "❓ Вопросы":
        show_questions()
    elif page == "📈 Аналитика":
        show_analytics()
    
    # Админские разделы
    if user_role == 'admin' and 'admin_page' in locals():
        st.divider()
        if admin_page == "🔐 Управление доступом":
            show_access_management()
        elif admin_page == "📋 Логи авторизации":
            show_auth_logs()
        elif admin_page == "⚡ Системные настройки":
            show_system_settings()

def show_dashboard():
    """Показать дашборд"""
    st.header("📊 Общая статистика")
    
    # Метрики в колонках
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        from data.database import get_total_users
        total_users = get_total_users()
        st.metric("👥 Всего пользователей", total_users, "+12")
    
    with col2:
        from data.database import db
        sessions = db.get_all_sessions(limit=1000)
        completed = len([s for s in sessions if s.get('status') == 'completed'])
        st.metric("✅ Завершенных анкет", completed, "+3")
    
    with col3:
        active = len([s for s in sessions if s.get('status') == 'active'])
        st.metric("⏳ Активных сессий", active, "+1")
    
    with col4:
        # Считаем процент завершения
        if sessions:
            completion_rate = (completed / len(sessions)) * 100
            st.metric("📈 % завершения", f"{completion_rate:.1f}%", "+2.3%")
        else:
            st.metric("📈 % завершения", "0%")
    
    # График активности
    st.subheader("📈 Активность за последние 7 дней")
    
    # Здесь можно добавить график с помощью plotly или altair
    st.info("График активности будет добавлен в следующей версии")

def show_anketas():
    """Показать список анкет"""
    st.header("📝 Анкеты пользователей")
    
    from data.database import db
    
    # Фильтры
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Статус:",
            options=["Все", "Завершенные", "Активные", "Черновики"]
        )
    
    with col2:
        date_filter = st.date_input(
            "Дата от:",
            value=datetime.now() - timedelta(days=7)
        )
    
    with col3:
        search = st.text_input("Поиск по ID:")
    
    # Получаем анкеты
    sessions = db.get_all_sessions(limit=100)
    
    # Фильтруем
    if status_filter != "Все":
        status_map = {
            "Завершенные": "completed",
            "Активные": "active",
            "Черновики": "draft"
        }
        status = status_map.get(status_filter)
        if status:
            sessions = [s for s in sessions if s.get('status') == status]
    
    if search:
        sessions = [s for s in sessions if search.lower() in str(s.get('anketa_id', '')).lower()]
    
    # Показываем таблицу
    if sessions:
        st.dataframe(
            data=[{
                "ID": s.get('anketa_id', f"Session_{s.get('id')}"),
                "Пользователь": s.get('username', 'Unknown'),
                "Статус": s.get('status', 'unknown'),
                "Дата": s.get('started_at', ''),
                "Прогресс": f"{len(json.loads(s.get('interview_data', '{}')))} ответов"
            } for s in sessions],
            use_container_width=True
        )
    else:
        st.info("Анкеты не найдены")

def show_users():
    """Показать список пользователей"""
    st.header("👥 Управление пользователями")
    
    # Проверяем права доступа
    user_data = st.session_state.get('user_data', {})
    user_role = auth_manager.get_user_role(user_data.get('telegram_id'))
    
    if user_role not in ['admin', 'editor']:
        st.warning("⚠️ У вас недостаточно прав для просмотра этого раздела")
        return
    
    # Здесь будет список пользователей
    st.info("Раздел в разработке")

def show_questions():
    """Показать вопросы интервью"""
    st.header("❓ Вопросы интервью")
    
    from data.database import get_interview_questions
    
    questions = get_interview_questions()
    
    if questions:
        for q in questions:
            with st.expander(f"Вопрос #{q['question_number']}: {q['field_name']}"):
                st.write(f"**Текст:** {q['question_text']}")
                if q.get('hint_text'):
                    st.info(f"💡 Подсказка: {q['hint_text']}")
                if q.get('question_type') == 'select' and q.get('options'):
                    st.write("**Варианты ответов:**")
                    try:
                        options = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
                        for opt in options:
                            st.write(f"- {opt.get('text', opt.get('value'))}")
                    except:
                        pass
    else:
        st.info("Вопросы не найдены")

def show_analytics():
    """Показать аналитику"""
    st.header("📈 Аналитика")
    
    # Проверяем права доступа  
    user_data = st.session_state.get('user_data', {})
    if not auth_manager.can_view_analytics(user_data.get('telegram_id')):
        st.warning("⚠️ У вас недостаточно прав для просмотра аналитики")
        return
    
    st.info("Раздел аналитики в разработке")

def show_access_management():
    """Управление доступом (только для админов)"""
    st.header("🔐 Управление доступом")
    
    # Список пользователей с ролями
    users = auth_manager.get_users_by_role('user')
    editors = auth_manager.get_users_by_role('editor')
    admins = auth_manager.get_users_by_role('admin')
    
    tab1, tab2, tab3 = st.tabs(["👤 Пользователи", "✏️ Редакторы", "👑 Администраторы"])
    
    with tab1:
        if users:
            for user in users:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"@{user.get('username', 'Unknown')} ({user.get('telegram_id')})")
                with col2:
                    st.write(f"Регистрация: {user.get('registration_date', '')[:10]}")
                with col3:
                    if st.button(f"Повысить", key=f"promote_{user['id']}"):
                        auth_manager.set_user_role(user['telegram_id'], 'editor')
                        st.success(f"Пользователь {user['username']} назначен редактором")
                        st.rerun()
        else:
            st.info("Нет пользователей с базовой ролью")
    
    with tab2:
        if editors:
            for user in editors:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"@{user.get('username', 'Unknown')} ({user.get('telegram_id')})")
                with col2:
                    if st.button(f"→ Admin", key=f"admin_{user['id']}"):
                        auth_manager.set_user_role(user['telegram_id'], 'admin')
                        st.rerun()
                with col3:
                    if st.button(f"→ User", key=f"demote_{user['id']}"):
                        auth_manager.set_user_role(user['telegram_id'], 'user')
                        st.rerun()
        else:
            st.info("Нет редакторов")
    
    with tab3:
        if admins:
            for user in admins:
                st.write(f"👑 @{user.get('username', 'Unknown')} ({user.get('telegram_id')})")
        else:
            st.info("Нет администраторов")

def show_auth_logs():
    """Показать логи авторизации"""
    st.header("📋 Логи авторизации")
    
    logs = auth_manager.get_auth_logs(limit=50)
    
    if logs:
        log_data = []
        for log in logs:
            log_data.append({
                "Время": log.get('created_at', ''),
                "Пользователь": log.get('username', f"ID: {log.get('user_id')}"),
                "Действие": log.get('action', ''),
                "Статус": "✅" if log.get('success') else "❌",
                "Ошибка": log.get('error_message', '')
            })
        
        st.dataframe(log_data, use_container_width=True)
    else:
        st.info("Логи не найдены")

def show_system_settings():
    """Системные настройки"""
    st.header("⚡ Системные настройки")
    
    st.info("Раздел системных настроек в разработке")

def main():
    """Главная функция приложения"""
    # Инициализация состояния сессии
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    # Проверяем токен из URL при первой загрузке
    if not st.session_state['authenticated']:
        check_token_from_url()
    
    # Проверяем авторизацию
    if not st.session_state['authenticated']:
        login_with_token()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()