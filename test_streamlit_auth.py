#!/usr/bin/env python3
"""
Тестовый скрипт для локального запуска Streamlit с системой авторизации
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Добавляем пути для импортов с логированием
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "data"))

# Логируем пути для отладки
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Current directory: {current_dir}")
logger.debug(f"Python paths: {sys.path[:3]}")

# Импортируем модули авторизации с обработкой ошибок
try:
    # Сначала пробуем импортировать database
    logger.debug("Trying to import database...")
    from database import auth_manager
    logger.debug("✓ Database imported successfully")
    
    # Теперь импортируем auth_pages напрямую (без web_admin префикса)
    logger.debug("Trying to import auth_pages...")
    # Добавляем путь к web-admin директории
    web_admin_path = current_dir / "web-admin"
    if web_admin_path not in sys.path:
        sys.path.insert(0, str(web_admin_path))
    
    from auth_pages import PageAuth, check_auth, check_role
    logger.debug("✓ Auth pages imported successfully")
    
except ImportError as e:
    st.error(f"❌ Ошибка импорта: {e}")
    st.error(f"Текущая директория: {current_dir}")
    st.error(f"Python пути: {sys.path[:5]}")
    
    # Показываем какие файлы существуют
    st.write("Проверка файлов:")
    if (current_dir / "data" / "database.py").exists():
        st.success("✓ data/database.py существует")
    else:
        st.error("✗ data/database.py НЕ найден")
        
    if (current_dir / "web-admin" / "auth_pages.py").exists():
        st.success("✓ web-admin/auth_pages.py существует")
    else:
        st.error("✗ web-admin/auth_pages.py НЕ найден")
    
    st.stop()

# Настройка страницы
st.set_page_config(
    page_title="GrantService Admin - Тест авторизации",
    page_icon="🔐",
    layout="wide"
)

def login_page():
    """Страница входа"""
    st.title("🔐 Вход в систему")
    
    with st.form("login_form"):
        st.write("### Тестовая авторизация")
        st.info("Используйте тестовые учетные записи:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.code("""
            Админ: 
            ID: 123456789
            Токен: admin_token
            """)
        
        with col2:
            st.code("""
            Редактор:
            ID: 987654321  
            Токен: editor_token
            """)
        
        user_id = st.text_input("Telegram ID")
        token = st.text_input("Токен", type="password")
        
        if st.form_submit_button("Войти", type="primary"):
            # Для тестирования используем простую логику
            if user_id and token:
                # Создаем тестового пользователя
                if user_id == "123456789" and token == "admin_token":
                    st.session_state.user_id = int(user_id)
                    st.session_state.role = "ADMIN"
                    st.session_state.token = token
                    st.session_state.authenticated = True
                    st.success("✅ Вход выполнен как Администратор")
                    st.rerun()
                elif user_id == "987654321" and token == "editor_token":
                    st.session_state.user_id = int(user_id)
                    st.session_state.role = "EDITOR"
                    st.session_state.token = token
                    st.session_state.authenticated = True
                    st.success("✅ Вход выполнен как Редактор")
                    st.rerun()
                else:
                    st.error("❌ Неверные учетные данные")

def admin_dashboard():
    """Панель администратора"""
    st.title("👑 Панель администратора")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Роль", st.session_state.role)
    with col2:
        st.metric("User ID", st.session_state.user_id)
    with col3:
        if st.button("🚪 Выйти"):
            for key in ['user_id', 'role', 'token', 'authenticated']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    st.divider()
    
    # Табы для разных функций
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Главная",
        "👥 Пользователи", 
        "📝 Заявки",
        "🤖 Агенты",
        "⚙️ Настройки"
    ])
    
    with tab1:
        st.header("Добро пожаловать в GrantService Admin")
        st.write("Это тестовая панель администратора с системой авторизации.")
        
        # Показываем доступные права
        st.subheader("📋 Ваши права доступа:")
        
        if st.session_state.role == "ADMIN":
            st.success("""
            ✅ Полный доступ ко всем функциям:
            - Управление пользователями
            - Управление ролями
            - Просмотр и редактирование заявок
            - Управление агентами
            - Системные настройки
            - Просмотр логов
            """)
        elif st.session_state.role == "EDITOR":
            st.info("""
            ✅ Доступ к функциям редактора:
            - Просмотр заявок
            - Редактирование вопросов
            - Управление агентами
            - Просмотр аналитики
            
            ❌ Недоступно:
            - Управление пользователями
            - Системные настройки
            """)
    
    with tab2:
        if st.session_state.role == "ADMIN":
            st.header("👥 Управление пользователями")
            
            # Форма добавления пользователя
            with st.expander("➕ Добавить пользователя"):
                with st.form("add_user"):
                    new_user_id = st.text_input("Telegram ID")
                    new_role = st.selectbox("Роль", ["USER", "VIEWER", "EDITOR", "ADMIN"])
                    if st.form_submit_button("Добавить"):
                        st.success(f"✅ Пользователь {new_user_id} добавлен с ролью {new_role}")
            
            # Список пользователей
            st.subheader("Текущие пользователи")
            users_data = {
                "ID": [123456789, 987654321, 555555555],
                "Роль": ["ADMIN", "EDITOR", "USER"],
                "Статус": ["✅ Активен", "✅ Активен", "⏸️ Неактивен"],
                "Последний вход": ["Сегодня", "Вчера", "Неделю назад"]
            }
            st.dataframe(users_data, use_container_width=True)
            
        else:
            st.error("❌ У вас нет доступа к управлению пользователями")
    
    with tab3:
        st.header("📝 Заявки на гранты")
        
        # Фильтры
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Статус", ["Все", "Новые", "В работе", "Завершены"])
        with col2:
            agent_filter = st.selectbox("Агент", ["Все", "Interviewer", "Analyst", "Writer"])
        with col3:
            date_filter = st.date_input("Дата")
        
        # Таблица заявок
        applications_data = {
            "ID": ["#001", "#002", "#003"],
            "Название": ["Проект А", "Проект Б", "Проект В"],
            "Статус": ["🟢 В работе", "🔵 Новая", "✅ Завершена"],
            "Агент": ["Analyst", "Interviewer", "Writer"],
            "Прогресс": ["60%", "20%", "100%"]
        }
        st.dataframe(applications_data, use_container_width=True)
        
        if st.session_state.role in ["ADMIN", "EDITOR"]:
            if st.button("✏️ Редактировать выбранную заявку"):
                st.info("Функция редактирования заявки")
    
    with tab4:
        st.header("🤖 Управление агентами")
        
        if st.session_state.role in ["ADMIN", "EDITOR"]:
            # Статус агентов
            st.subheader("Статус агентов")
            
            agents = ["Interviewer", "Analyst", "Researcher", "Writer", "Auditor"]
            cols = st.columns(len(agents))
            
            for i, agent in enumerate(agents):
                with cols[i]:
                    st.metric(
                        agent,
                        "🟢 Активен",
                        "5 задач"
                    )
            
            # Настройки агентов
            with st.expander("⚙️ Настройки агентов"):
                selected_agent = st.selectbox("Выберите агента", agents)
                
                st.text_area(
                    f"Промпт для {selected_agent}",
                    value="Текущий промпт агента...",
                    height=200
                )
                
                if st.button("💾 Сохранить промпт"):
                    st.success("✅ Промпт обновлен")
        else:
            st.info("ℹ️ У вас есть доступ только для просмотра")
    
    with tab5:
        st.header("⚙️ Системные настройки")
        
        if st.session_state.role == "ADMIN":
            st.subheader("🔧 Параметры системы")
            
            # Настройки LLM
            with st.expander("🧠 Настройки LLM"):
                llm_provider = st.selectbox(
                    "Провайдер",
                    ["GigaChat", "Perplexity", "Ollama"]
                )
                
                st.text_input("API Key", type="password", value="*" * 20)
                st.slider("Temperature", 0.0, 1.0, 0.7)
                st.slider("Max Tokens", 100, 4000, 2000)
                
                if st.button("💾 Сохранить настройки LLM"):
                    st.success("✅ Настройки LLM обновлены")
            
            # Логи системы
            with st.expander("📜 Системные логи"):
                st.code("""
                [2024-01-17 10:30:15] INFO: System started
                [2024-01-17 10:30:20] INFO: Database connected
                [2024-01-17 10:30:25] INFO: Admin logged in (ID: 123456789)
                [2024-01-17 10:31:00] INFO: Agent Interviewer started task
                [2024-01-17 10:32:15] WARNING: High memory usage detected
                [2024-01-17 10:35:00] INFO: Application #001 processed
                """)
                
                if st.button("🔄 Обновить логи"):
                    st.rerun()
            
            # Резервное копирование
            with st.expander("💾 Резервное копирование"):
                st.button("📦 Создать резервную копию БД", type="primary")
                st.button("📥 Восстановить из резервной копии")
                
                st.info("Последняя резервная копия: 2024-01-16 23:00")
        else:
            st.error("❌ У вас нет доступа к системным настройкам")

def main():
    """Главная функция"""
    
    # Проверяем аутентификацию
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Отображаем соответствующую страницу
    if not st.session_state.authenticated:
        login_page()
    else:
        admin_dashboard()
    
    # Футер с информацией
    st.divider()
    st.caption("""
    🔐 GrantService Admin v1.0 | Тестовая версия с системой авторизации
    """)

if __name__ == "__main__":
    main()