#!/usr/bin/env python3
"""
Упрощенный тестовый скрипт Streamlit без внешних зависимостей
Демонстрация системы авторизации с ролями Admin и Editor
"""

import streamlit as st
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

# Настройка страницы
st.set_page_config(
    page_title="GrantService Admin - Тест авторизации",
    page_icon="🔐",
    layout="wide"
)

# Простая имитация базы данных в памяти
class SimpleAuthManager:
    """Упрощенный менеджер авторизации для тестирования"""
    
    def __init__(self):
        # Предустановленные пользователи для тестирования
        self.users = {
            123456789: {
                "role": "ADMIN",
                "name": "Администратор",
                "token": self.generate_token(123456789),
                "permissions": ["all"]
            },
            987654321: {
                "role": "EDITOR", 
                "name": "Редактор",
                "token": self.generate_token(987654321),
                "permissions": ["view", "edit", "manage_agents"]
            },
            555555555: {
                "role": "VIEWER",
                "name": "Наблюдатель",
                "token": self.generate_token(555555555),
                "permissions": ["view"]
            }
        }
    
    def generate_token(self, user_id):
        """Генерация простого токена"""
        return hashlib.md5(f"{user_id}_token".encode()).hexdigest()[:10]
    
    def authenticate(self, user_id, token):
        """Проверка аутентификации"""
        try:
            uid = int(user_id)
            if uid in self.users and self.users[uid]["token"] == token:
                return self.users[uid]
        except:
            pass
        return None
    
    def has_permission(self, role, permission):
        """Проверка прав доступа"""
        permissions_map = {
            "ADMIN": ["all"],
            "EDITOR": ["view", "edit", "manage_agents"],
            "VIEWER": ["view"],
            "USER": ["view_limited"]
        }
        
        if role == "ADMIN":
            return True
        
        return permission in permissions_map.get(role, [])

# Создаем глобальный экземпляр
auth_manager = SimpleAuthManager()

def show_login_page():
    """Страница входа в систему"""
    st.title("🔐 GrantService - Вход в систему")
    
    st.markdown("""
    ### Тестовые учетные записи:
    
    | Роль | User ID | Токен |
    |------|---------|-------|
    | 👑 **Администратор** | `123456789` | `e807f1fcf8` |
    | ✏️ **Редактор** | `987654321` | `b8c37e33de` |
    | 👁️ **Наблюдатель** | `555555555` | `5d7b9adcbe` |
    """)
    
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            user_id = st.text_input("Telegram User ID", placeholder="Например: 123456789")
        
        with col2:
            token = st.text_input("Токен доступа", type="password", placeholder="Например: e807f1fcf8")
        
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            submit = st.form_submit_button("🔓 Войти", type="primary", use_container_width=True)
        
        if submit:
            user = auth_manager.authenticate(user_id, token)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.user_id = int(user_id)
                st.success(f"✅ Успешный вход как {user['name']} ({user['role']})")
                st.rerun()
            else:
                st.error("❌ Неверные учетные данные")

def show_admin_panel():
    """Главная панель администрирования"""
    user = st.session_state.user
    
    # Заголовок с информацией о пользователе
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        st.title("📊 GrantService Admin Panel")
    
    with col2:
        st.metric("Роль", user['role'])
    
    with col3:
        st.metric("ID", st.session_state.user_id)
    
    with col4:
        if st.button("🚪 Выйти", use_container_width=True):
            for key in ['authenticated', 'user', 'user_id']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    st.divider()
    
    # Вкладки функционала
    if user['role'] == "ADMIN":
        tabs = st.tabs(["📈 Дашборд", "👥 Пользователи", "📝 Заявки", "🤖 Агенты", "⚙️ Настройки", "📊 Аналитика"])
    elif user['role'] == "EDITOR":
        tabs = st.tabs(["📈 Дашборд", "📝 Заявки", "🤖 Агенты", "📊 Аналитика"])
    else:
        tabs = st.tabs(["📈 Дашборд", "📊 Аналитика"])
    
    # Вкладка Дашборд (доступна всем)
    with tabs[0]:
        show_dashboard(user['role'])
    
    # Остальные вкладки в зависимости от роли
    if user['role'] == "ADMIN":
        with tabs[1]:
            show_users_management()
        with tabs[2]:
            show_applications(can_edit=True)
        with tabs[3]:
            show_agents_management(can_edit=True)
        with tabs[4]:
            show_settings()
        with tabs[5]:
            show_analytics()
    
    elif user['role'] == "EDITOR":
        with tabs[1]:
            show_applications(can_edit=True)
        with tabs[2]:
            show_agents_management(can_edit=True)
        with tabs[3]:
            show_analytics()
    
    else:  # VIEWER
        with tabs[1]:
            show_analytics()

def show_dashboard(role):
    """Главный дашборд"""
    st.header("📈 Главная панель")
    
    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего заявок", "127", "+12 за неделю")
    
    with col2:
        st.metric("Активные", "23", "+3 сегодня")
    
    with col3:
        st.metric("Завершенные", "104", "+9 за неделю")
    
    with col4:
        st.metric("Успешность", "82%", "+5%")
    
    st.divider()
    
    # Права доступа
    st.subheader("🔐 Ваши права доступа")
    
    if role == "ADMIN":
        st.success("""
        **Полный доступ ко всем функциям:**
        - ✅ Управление пользователями и ролями
        - ✅ Полное редактирование заявок
        - ✅ Управление всеми агентами
        - ✅ Системные настройки
        - ✅ Доступ к логам и отладке
        """)
    elif role == "EDITOR":
        st.info("""
        **Права редактора:**
        - ✅ Просмотр и редактирование заявок
        - ✅ Управление агентами
        - ✅ Просмотр аналитики
        - ❌ Управление пользователями
        - ❌ Системные настройки
        """)
    else:
        st.warning("""
        **Ограниченный доступ:**
        - ✅ Просмотр дашборда
        - ✅ Просмотр аналитики
        - ❌ Редактирование данных
        - ❌ Управление системой
        """)

def show_users_management():
    """Управление пользователями (только для админов)"""
    st.header("👥 Управление пользователями")
    
    # Добавление нового пользователя
    with st.expander("➕ Добавить нового пользователя"):
        with st.form("add_user"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_id = st.text_input("Telegram User ID")
                new_name = st.text_input("Имя пользователя")
            
            with col2:
                new_role = st.selectbox("Роль", ["USER", "VIEWER", "EDITOR", "ADMIN"])
                new_token = st.text_input("Токен (автоматически)", value="Будет сгенерирован", disabled=True)
            
            if st.form_submit_button("Добавить пользователя", type="primary"):
                st.success(f"✅ Пользователь {new_name} добавлен с ролью {new_role}")
    
    # Список существующих пользователей
    st.subheader("Существующие пользователи")
    
    users_data = {
        "ID": [123456789, 987654321, 555555555, 111111111],
        "Имя": ["Администратор", "Редактор", "Наблюдатель", "Пользователь"],
        "Роль": ["ADMIN", "EDITOR", "VIEWER", "USER"],
        "Статус": ["🟢 Активен", "🟢 Активен", "🟡 Неактивен", "🔴 Заблокирован"],
        "Последний вход": ["Сейчас", "2 часа назад", "Вчера", "Неделю назад"],
        "Действия": ["", "Изменить", "Изменить", "Разблокировать"]
    }
    
    st.dataframe(users_data, use_container_width=True, hide_index=True)

def show_applications(can_edit=False):
    """Просмотр и управление заявками"""
    st.header("📝 Заявки на гранты")
    
    # Фильтры
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.selectbox("Статус", ["Все", "Новые", "В работе", "На проверке", "Завершены"])
    
    with col2:
        st.selectbox("Агент", ["Все", "Interviewer", "Analyst", "Researcher", "Writer", "Auditor"])
    
    with col3:
        st.date_input("Дата от", datetime.now() - timedelta(days=30))
    
    with col4:
        st.date_input("Дата до", datetime.now())
    
    # Таблица заявок
    applications = {
        "ID": ["#2024-001", "#2024-002", "#2024-003", "#2024-004", "#2024-005"],
        "Название проекта": [
            "ИИ для медицины",
            "Образовательная платформа", 
            "Экологический мониторинг",
            "Социальная сеть для НКО",
            "Автоматизация производства"
        ],
        "Статус": ["🟢 В работе", "🔵 Новая", "🟡 На проверке", "✅ Завершена", "🟢 В работе"],
        "Текущий агент": ["Analyst", "Interviewer", "Auditor", "Completed", "Writer"],
        "Прогресс": ["45%", "15%", "85%", "100%", "60%"],
        "Дедлайн": ["15.02.2024", "20.02.2024", "10.02.2024", "01.02.2024", "25.02.2024"]
    }
    
    st.dataframe(applications, use_container_width=True, hide_index=True)
    
    if can_edit:
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("✏️ Редактировать", use_container_width=True):
                st.info("Выберите заявку для редактирования")
        with col2:
            if st.button("🔄 Перезапустить", use_container_width=True):
                st.info("Выберите заявку для перезапуска")

def show_agents_management(can_edit=False):
    """Управление AI агентами"""
    st.header("🤖 Управление агентами")
    
    # Статус агентов
    st.subheader("Текущий статус")
    
    agents = {
        "Interviewer": {"status": "🟢 Активен", "tasks": 3, "cpu": "12%", "memory": "256 MB"},
        "Analyst": {"status": "🟢 Активен", "tasks": 5, "cpu": "45%", "memory": "512 MB"},
        "Researcher": {"status": "🟡 Ожидание", "tasks": 0, "cpu": "2%", "memory": "128 MB"},
        "Writer": {"status": "🟢 Активен", "tasks": 2, "cpu": "23%", "memory": "384 MB"},
        "Auditor": {"status": "🔴 Остановлен", "tasks": 0, "cpu": "0%", "memory": "64 MB"}
    }
    
    cols = st.columns(5)
    for i, (agent_name, info) in enumerate(agents.items()):
        with cols[i]:
            st.metric(
                agent_name,
                info["status"],
                f"{info['tasks']} задач"
            )
            st.caption(f"CPU: {info['cpu']}")
            st.caption(f"RAM: {info['memory']}")
    
    if can_edit:
        st.divider()
        
        # Настройки агента
        st.subheader("⚙️ Настройки агента")
        
        selected_agent = st.selectbox("Выберите агента для настройки", list(agents.keys()))
        
        with st.expander(f"Настройки {selected_agent}"):
            st.text_area(
                "System Prompt",
                value=f"Вы - {selected_agent} в системе GrantService...",
                height=150
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.slider("Temperature", 0.0, 1.0, 0.7)
                st.slider("Max Tokens", 100, 4000, 2000)
            
            with col2:
                st.selectbox("Модель", ["GigaChat", "GPT-4", "Claude"])
                st.number_input("Timeout (сек)", 30, 300, 60)
            
            if st.button("💾 Сохранить настройки", type="primary"):
                st.success(f"✅ Настройки {selected_agent} сохранены")

def show_settings():
    """Системные настройки (только для админов)"""
    st.header("⚙️ Системные настройки")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🧠 LLM", "🗄️ База данных", "🔐 Безопасность", "📜 Логи"])
    
    with tab1:
        st.subheader("Настройки языковых моделей")
        
        col1, col2 = st.columns(2)
        
        with col1:
            provider = st.selectbox("Основной провайдер", ["GigaChat", "OpenAI", "Anthropic", "Local Ollama"])
            api_key = st.text_input("API ключ", type="password", value="*" * 30)
            
        with col2:
            st.slider("Default Temperature", 0.0, 1.0, 0.7)
            st.slider("Default Max Tokens", 100, 8000, 2000)
            st.selectbox("Fallback провайдер", ["Нет", "Ollama", "GigaChat"])
        
        if st.button("Сохранить настройки LLM", type="primary"):
            st.success("✅ Настройки LLM обновлены")
    
    with tab2:
        st.subheader("Настройки базы данных")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Путь к БД", value="/var/GrantService/data/database.db")
            st.number_input("Автосохранение (мин)", 1, 60, 5)
        
        with col2:
            st.text_input("Путь к бэкапам", value="/var/GrantService/backups/")
            st.number_input("Хранить бэкапов", 1, 30, 7)
        
        if st.button("Создать резервную копию сейчас", type="secondary"):
            st.success("✅ Резервная копия создана")
    
    with tab3:
        st.subheader("Настройки безопасности")
        
        st.checkbox("Двухфакторная аутентификация", value=False)
        st.slider("Срок действия токена (часы)", 1, 168, 24)
        st.number_input("Максимум попыток входа", 1, 10, 3)
        st.checkbox("Логировать все действия", value=True)
        
        if st.button("Применить настройки безопасности", type="primary"):
            st.success("✅ Настройки безопасности обновлены")
    
    with tab4:
        st.subheader("Системные логи")
        
        log_level = st.selectbox("Уровень логирования", ["DEBUG", "INFO", "WARNING", "ERROR"])
        
        st.code("""
[2024-01-17 10:30:15] INFO: System started successfully
[2024-01-17 10:30:20] INFO: Database connection established
[2024-01-17 10:30:25] INFO: Admin user authenticated (ID: 123456789)
[2024-01-17 10:31:00] INFO: Agent Interviewer started processing task #2024-001
[2024-01-17 10:32:15] WARNING: High memory usage detected for Agent Analyst (512MB)
[2024-01-17 10:35:00] INFO: Application #2024-003 moved to Auditor
[2024-01-17 10:36:42] ERROR: Failed to connect to GigaChat API (timeout)
[2024-01-17 10:36:43] INFO: Fallback to Ollama activated
[2024-01-17 10:40:00] INFO: Backup created successfully
[2024-01-17 10:45:12] DEBUG: Cache cleared for expired tokens
        """, language="log")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Обновить логи"):
                st.rerun()
        with col2:
            if st.button("📥 Скачать логи"):
                st.info("Подготовка архива с логами...")

def show_analytics():
    """Аналитика (доступна всем)"""
    st.header("📊 Аналитика")
    
    # Статистика по заявкам
    st.subheader("Статистика заявок")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Среднее время обработки", "3.5 дня", "-0.5 дня")
    
    with col2:
        st.metric("Успешность", "82%", "+5%")
    
    with col3:
        st.metric("Отклонено", "18%", "-5%")
    
    # График (имитация)
    st.subheader("Динамика за месяц")
    chart_data = {
        "Дата": ["01.01", "05.01", "10.01", "15.01", "20.01", "25.01", "30.01"],
        "Новые": [5, 8, 12, 6, 9, 11, 7],
        "Завершенные": [3, 6, 10, 8, 7, 9, 5],
        "Отклоненные": [1, 2, 1, 0, 2, 1, 2]
    }
    st.line_chart(data=chart_data, x="Дата", y=["Новые", "Завершенные", "Отклоненные"])
    
    # Статистика по агентам
    st.subheader("Производительность агентов")
    
    agents_stats = {
        "Агент": ["Interviewer", "Analyst", "Researcher", "Writer", "Auditor"],
        "Обработано задач": [145, 132, 98, 127, 89],
        "Среднее время (мин)": [15, 25, 45, 35, 20],
        "Успешность (%)": [95, 88, 92, 85, 97]
    }
    
    st.dataframe(agents_stats, use_container_width=True, hide_index=True)

def main():
    """Главная функция приложения"""
    
    # Инициализация состояния сессии
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Маршрутизация
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_admin_panel()
    
    # Футер
    st.divider()
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            st.caption("🔐 GrantService v1.0")
            st.caption("Тестовая версия")

if __name__ == "__main__":
    main()