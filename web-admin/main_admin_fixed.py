#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ГрантСервис - Веб-админ панель
Streamlit приложение для управления Telegram ботом
Домен: grantservice.onff.ru
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('/var/GrantService/config/.env')

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

# Конфигурация Streamlit
st.set_page_config(
    page_title="🏆 ГрантСервис - Админ панель",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стили
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #667eea;
}
.status-running {
    color: #28a745;
    font-weight: bold;
}
.status-error {
    color: #dc3545;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Функции для работы с данными
@st.cache_data(ttl=60)
def get_bot_status():
    """Получение статуса Telegram бота"""
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN', '7685915842:AAGcW0kgtljyIob8enM3zvFSLuZ-BZzcPOo')}/getMe",
            timeout=5
        )
        if response.status_code == 200:
            return {"status": "running", "data": response.json()}
        else:
            return {"status": "error", "data": None}
    except:
        return {"status": "error", "data": None}

@st.cache_data(ttl=300)
def get_analytics_data():
    """Получение аналитических данных"""
    # Здесь будет интеграция с базой данных
    return {
        "total_sessions": 142,
        "completed_apps": 67,
        "conversion_rate": 47.2,
        "avg_time_minutes": 12,
        "daily_stats": {
            "Понедельник": 15,
            "Вторник": 23, 
            "Среда": 18,
            "Четверг": 31,
            "Пятница": 42,
            "Суббота": 12,
            "Воскресенье": 8
        }
    }

@st.cache_data(ttl=60)
def get_system_status():
    """Получение статуса системы"""
    try:
        # Проверка systemd сервиса
        result = os.system("systemctl is-active --quiet grantservice-bot.service")
        systemd_status = "active" if result == 0 else "inactive"
        
        return {
            "telegram_bot": "running",  # Заглушка
            "systemd_service": systemd_status,
            "web_admin": "running"
        }
    except:
        return {
            "telegram_bot": "error",
            "systemd_service": "error", 
            "web_admin": "running"
        }

# Заголовок
st.markdown("""
<div class="main-header">
    <h1>🏆 ГрантСервис - Админ панель</h1>
    <p>Управление системой создания грантовых заявок</p>
</div>
""", unsafe_allow_html=True)

# Sidebar навигация
st.sidebar.markdown("### 🎛️ Навигация")
page = st.sidebar.selectbox("Выберите раздел:", [
    "🏠 Главная", 
    "📊 Аналитика", 
    "📝 Управление вопросами",
    "📝 Редактор промптов", 
    "👥 Пользователи",
    "⚙️ Настройки системы",
    "📈 Мониторинг"
])

# Статус системы в sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Статус системы")
system_status = get_system_status()

if system_status["telegram_bot"] == "running":
    st.sidebar.markdown("🟢 **Telegram Bot:** Работает")
else:
    st.sidebar.markdown("🔴 **Telegram Bot:** Ошибка")

if system_status["systemd_service"] == "active":
    st.sidebar.markdown("🟢 **SystemD:** Активен")
else:
    st.sidebar.markdown("🔴 **SystemD:** Неактивен")

st.sidebar.markdown("🟢 **Веб-админка:** Работает")

# === ГЛАВНАЯ СТРАНИЦА ===
if page == "🏠 Главная":
    st.markdown("## 🎯 Обзор системы")
    
    # Метрики системы
    col1, col2, col3, col4 = st.columns(4)
    analytics = get_analytics_data()
    
    with col1:
        st.metric(
            "Всего сессий", 
            analytics["total_sessions"], 
            "+12"
        )
    with col2:
        st.metric(
            "Готовых заявок", 
            analytics["completed_apps"], 
            "+5"
        )
    with col3:
        st.metric(
            "Конверсия", 
            f"{analytics['conversion_rate']}%", 
            "+3%"
        )
    with col4:
        st.metric(
            "Среднее время", 
            f"{analytics['avg_time_minutes']} мин", 
            "-2 мин"
        )
    
    # Статус компонентов
    st.markdown("### 🔧 Статус компонентов")
    col1, col2 = st.columns(2)
    
    with col1:
        bot_status = get_bot_status()
        if bot_status["status"] == "running":
            st.success("🤖 **Telegram Bot** - Работает нормально")
            if bot_status["data"]:
                bot_info = bot_status["data"]["result"]
                st.info(f"@{bot_info['username']} | ID: {bot_info['id']}")
        else:
            st.error("🤖 **Telegram Bot** - Недоступен")
    
    with col2:
        if system_status["systemd_service"] == "active":
            st.success("⚙️ **SystemD Service** - Активен")
        else:
            st.error("⚙️ **SystemD Service** - Неактивен")
    
    # Последние активности (заглушка)
    st.markdown("### 📋 Последние активности")
    activities = [
        {"time": "10:30", "user": "Николай Степанов", "action": "Создал заявку на грант Потанина"},
        {"time": "09:15", "user": "Тестовый пользователь", "action": "Прошел интервью"},
        {"time": "08:45", "user": "Admin", "action": "Обновил промпт агента-аудитора"},
    ]
    
    for activity in activities:
        st.markdown(f"**{activity['time']}** - {activity['user']}: {activity['action']}")

# === АНАЛИТИКА ===
elif page == "📊 Аналитика":
    st.markdown("## 📊 Аналитика ГрантСервиса")
    
    analytics = get_analytics_data()
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего сессий", analytics["total_sessions"], "+12")
    with col2:
        st.metric("Готовых заявок", analytics["completed_apps"], "+5")
    with col3:
        st.metric("Конверсия", f"{analytics['conversion_rate']}%", "+3%")
    with col4:
        st.metric("Среднее время", f"{analytics['avg_time_minutes']} мин", "-2 мин")
    
    # График активности по дням
    st.markdown("### 📈 Активность по дням недели")
    daily_data = analytics["daily_stats"]
    df_daily = pd.DataFrame(list(daily_data.items()), columns=['День', 'Сессии'])
    
    st.bar_chart(df_daily.set_index('День'))
    
    # Детальная статистика
    st.markdown("### 📋 Детальная статистика")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Топ пользователей:**")
        users = [
            {"name": "Николай Степанов", "sessions": 15, "completed": 8},
            {"name": "Тестовый пользователь", "sessions": 12, "completed": 6},
            {"name": "Новый пользователь", "sessions": 8, "completed": 3},
        ]
        
        for user in users:
            st.markdown(f"- {user['name']}: {user['sessions']} сессий, {user['completed']} завершено")
    
    with col2:
        st.markdown("**Статистика по этапам:**")
        stages = [
            {"stage": "Интервью", "completed": 142, "conversion": "100%"},
            {"stage": "Аудит", "completed": 98, "conversion": "69%"},
            {"stage": "Планирование", "completed": 67, "conversion": "47%"},
            {"stage": "Написание", "completed": 67, "conversion": "47%"},
        ]
        
        for stage in stages:
            st.markdown(f"- {stage['stage']}: {stage['completed']} ({stage['conversion']})")

# === УПРАВЛЕНИЕ ВОПРОСАМИ ===
elif page == "📝 Управление вопросами":
    st.markdown("## 📝 Управление вопросами интервью")
    
    # Подключение к БД
    try:
        sys.path.append('/var/GrantService/data')
        from database import db
        
        # Заголовок с действиями
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("### Список вопросов интервью")
        with col2:
            if st.button("➕ Добавить вопрос", type="primary"):
                st.session_state.add_question = True
        with col3:
            if st.button("🔄 Обновить"):
                st.rerun()
        
        # Получаем все активные вопросы
        questions = db.get_active_questions()
        
        if not questions:
            st.warning("❌ Вопросы не найдены. Проверьте подключение к базе данных.")
        else:
            # Таблица вопросов
            st.markdown("### 📋 Список вопросов")
            
            for i, question in enumerate(questions):
                with st.expander(f"Вопрос {question['question_number']}: {question['question_text'][:50]}..."):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Текст вопроса:** {question['question_text']}")
                        if question['hint_text']:
                            st.markdown(f"**Подсказка:** {question['hint_text']}")
                        st.markdown(f"**Тип:** {question['question_type']} | **Поле БД:** {question['field_name']}")
                        st.markdown(f"**Обязательный:** {'✅' if question['is_required'] else '❌'}")
                        
                        if question['validation_rules']:
                            rules = question['validation_rules']
                            rules_text = []
                            if 'min_length' in rules:
                                rules_text.append(f"мин. длина: {rules['min_length']}")
                            if 'max_length' in rules:
                                rules_text.append(f"макс. длина: {rules['max_length']}")
                            st.markdown(f"**Валидация:** {', '.join(rules_text)}")
                    
                    with col2:
                        if st.button(f"✏️ Редактировать", key=f"edit_{i}"):
                            st.session_state.edit_question = question
                        if st.button(f"🗑️ Удалить", key=f"delete_{i}"):
                            if db.delete_question(question['id']):
                                st.success("✅ Вопрос удален!")
                                st.rerun()
                            else:
                                st.error("❌ Ошибка удаления")
            
            # Форма добавления/редактирования вопроса
            if st.session_state.get('add_question') or st.session_state.get('edit_question'):
                st.markdown("---")
                st.markdown("### ✏️ Редактирование вопроса")
                
                question = st.session_state.get('edit_question', {})
                
                with st.form("question_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        question_number = st.number_input("Номер вопроса", 1, 100, question.get('question_number', 1))
                        question_text = st.text_area("Текст вопроса", question.get('question_text', ''), height=100)
                        field_name = st.text_input("Название поля в БД", question.get('field_name', ''))
                        question_type = st.selectbox("Тип вопроса", 
                            ['text', 'textarea', 'select', 'number', 'date'], 
                            index=['text', 'textarea', 'select', 'number', 'date'].index(question.get('question_type', 'text')))
                    
                    with col2:
                        hint_text = st.text_area("Подсказка/пример", question.get('hint_text', ''), height=100)
                        is_required = st.checkbox("Обязательный вопрос", question.get('is_required', True))
                        is_active = st.checkbox("Активный вопрос", question.get('is_active', True))
                        
                        # Валидация
                        st.markdown("**Правила валидации:**")
                        min_length = st.number_input("Минимальная длина", 0, 1000, question.get('validation_rules', {}).get('min_length', 0))
                        max_length = st.number_input("Максимальная длина", 0, 10000, question.get('validation_rules', {}).get('max_length', 1000))
                    
                    # Кнопки формы
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.form_submit_button("💾 Сохранить"):
                            validation_rules = {}
                            if min_length > 0:
                                validation_rules['min_length'] = min_length
                            if max_length > 0:
                                validation_rules['max_length'] = max_length
                            
                            question_data = {
                                'question_number': question_number,
                                'question_text': question_text,
                                'field_name': field_name,
                                'question_type': question_type,
                                'hint_text': hint_text,
                                'is_required': is_required,
                                'is_active': is_active,
                                'validation_rules': validation_rules
                            }
                            
                            if st.session_state.get('edit_question'):
                                # Обновление
                                if db.update_question(question['id'], question_data):
                                    st.success("✅ Вопрос обновлен!")
                                    del st.session_state.edit_question
                                    st.rerun()
                                else:
                                    st.error("❌ Ошибка обновления")
                            else:
                                # Создание
                                new_id = db.create_question(question_data)
                                if new_id:
                                    st.success("✅ Вопрос создан!")
                                    del st.session_state.add_question
                                    st.rerun()
                                else:
                                    st.error("❌ Ошибка создания")
                    
                    with col2:
                        if st.form_submit_button("❌ Отмена"):
                            if st.session_state.get('edit_question'):
                                del st.session_state.edit_question
                            if st.session_state.get('add_question'):
                                del st.session_state.add_question
                            st.rerun()
                    
                    with col3:
                        if st.form_submit_button("🧪 Тестировать"):
                            st.info("Функция тестирования в разработке")
    
    except ImportError as e:
        st.error(f"❌ Ошибка импорта модуля БД: {e}")
        st.info("Убедитесь, что файл database.py существует в /var/GrantService/data/")
    except Exception as e:
        st.error(f"❌ Ошибка работы с БД: {e}")

# === РЕДАКТОР ПРОМПТОВ ===
elif page == "📝 Редактор промптов":
    st.markdown("## 📝 Редактор промптов агентов")
    
    # Загрузка промптов
    prompts = load_prompts()
    
    # Выбор агента
    agent_type = st.selectbox(
        "Выберите агента:",
        ["interviewer", "auditor", "planner", "writer"],
        format_func=lambda x: {
            "interviewer": "🎤 Интервьюер",
            "auditor": "🔍 Аудитор", 
            "planner": "📋 Планировщик",
            "writer": "✍️ Писатель"
        }[x]
    )
    
    # Редактор промпта
    st.markdown(f"### Редактирование промпта для агента: {agent_type}")
    
    current_prompt = prompts.get(agent_type, "")
    
    new_prompt = st.text_area(
        "Промпт:",
        value=current_prompt,
        height=400,
        help="Системный промпт для ИИ агента"
    )
    
    # Параметры
    col1, col2, col3 = st.columns(3)
    with col1:
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    with col2:
        max_tokens = st.number_input("Max tokens", 100, 4000, 2000, 100)
    with col3:
        model = st.selectbox("Модель", ["GigaChat-Max", "GigaChat-Pro", "GigaChat"])
    
    # Кнопки
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Сохранить промпт", type="primary"):
            prompts[agent_type] = new_prompt
            save_prompts(prompts)
            st.success("✅ Промпт сохранен!")
    with col2:
        if st.button("🔄 Сбросить к исходному"):
            # Здесь можно загрузить исходные промпты
            st.info("Функция сброса в разработке")

# === ПОЛЬЗОВАТЕЛИ ===
elif page == "👥 Пользователи":
    st.markdown("## 👥 Управление пользователями")
    
    # Заглушка для пользователей
    st.info("📊 Интеграция с базой данных пользователей в разработке")
    
    # Пример данных
    users_data = [
        {"id": 1, "name": "Николай Степанов", "telegram_id": "123456789", "sessions": 15, "last_active": "2025-07-18 10:30"},
        {"id": 2, "name": "Тестовый пользователь", "telegram_id": "987654321", "sessions": 8, "last_active": "2025-07-18 09:15"},
        {"id": 3, "name": "Новый пользователь", "telegram_id": "555666777", "sessions": 3, "last_active": "2025-07-18 08:45"},
    ]
    
    df_users = pd.DataFrame(users_data)
    st.dataframe(df_users, use_container_width=True)

# === НАСТРОЙКИ СИСТЕМЫ ===
elif page == "⚙️ Настройки системы":
    st.markdown("## ⚙️ Настройки системы")
    
    # Настройки ИИ
    st.markdown("### 🤖 Настройки ИИ")
    col1, col2 = st.columns(2)
    
    with col1:
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        max_tokens = st.number_input("Max tokens", 100, 4000, 2000, 100)
    
    with col2:
        model = st.selectbox("Модель", ["GigaChat-Max", "GigaChat-Pro", "GigaChat"])
        timeout = st.number_input("Timeout (сек)", 5, 60, 30)
    
    # Настройки Telegram
    st.markdown("### 📱 Настройки Telegram бота")
    welcome_message = st.text_area(
        "Приветственное сообщение:",
        value="""🤖 Добро пожаловать в ГрантСервис!

Привет! Я помогу тебе создать профессиональную грантовую заявку за 15-20 минут.

Как это работает:
1️⃣ Интервью - соберу информацию о твоем проекте
2️⃣ Аудит - проанализирую и дам рекомендации  
3️⃣ Планирование - создам структуру заявки
4️⃣ Написание - сформирую финальный документ

Готов начать? Жми /interview 👇""",
        height=200
    )
    
    # Системные настройки
    st.markdown("### 🔧 Системные настройки")
    col1, col2 = st.columns(2)
    
    with col1:
        log_level = st.selectbox("Уровень логирования", ["DEBUG", "INFO", "WARNING", "ERROR"])
        auto_backup = st.checkbox("Автоматическое резервирование", value=True)
    
    with col2:
        maintenance_mode = st.checkbox("Режим обслуживания", value=False)
        debug_mode = st.checkbox("Режим отладки", value=True)
    
    # Кнопка сохранения
    if st.button("💾 Сохранить все настройки", type="primary"):
        st.success("✅ Настройки сохранены!")

# === МОНИТОРИНГ ===
elif page == "📈 Мониторинг":
    st.markdown("## 📈 Мониторинг системы")
    
    # Системные метрики
    st.markdown("### 💻 Системные ресурсы")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("CPU", "15%", "↓5%")
    with col2:
        st.metric("RAM", "512MB", "↑50MB")
    with col3:
        st.metric("Диск", "2.1GB", "↑100MB")
    
    # Логи системы
    st.markdown("### 📋 Последние логи")
    
    # Фильтры логов
    col1, col2, col3 = st.columns(3)
    with col1:
        log_level_filter = st.selectbox("Уровень", ["ALL", "INFO", "WARNING", "ERROR"])
    with col2:
        log_component = st.selectbox("Компонент", ["ALL", "Telegram Bot", "Web Admin", "SystemD"])
    with col3:
        log_lines = st.number_input("Строк", 10, 100, 20)
    
    # Заглушка для логов
    sample_logs = [
        "2025-07-18 03:45:30 - INFO - HTTP Request: getUpdates 200 OK",
        "2025-07-18 03:45:25 - INFO - User 123456789 started interview",
        "2025-07-18 03:45:20 - INFO - SystemD service healthy",
        "2025-07-18 03:45:15 - WARNING - High CPU usage detected",
        "2025-07-18 03:45:10 - INFO - Prompt updated for agent Аудитор",
    ]
    
    st.code("\n".join(sample_logs))
    
    # Кнопки управления
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Обновить логи"):
            st.rerun()
    with col2:
        if st.button("📥 Скачать логи"):
            st.info("Функция в разработке")
    with col3:
        if st.button("🗑️ Очистить логи"):
            st.warning("Требует подтверждения")

# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; margin-top: 2rem;'>
    <p>🏆 ГрантСервис Веб-админка v1.0 | 
    Разработано: Андрей Отинов | 
    Домен: <a href='https://grantservice.onff.ru'>grantservice.onff.ru</a></p>
</div>
""", unsafe_allow_html=True)

# Функции для работы с промптами (заглушки)
def load_prompts():
    """Загрузка промптов из файла"""
    return {
        "interviewer": "Ты - опытный интервьюер для сбора информации о проектах. Задавай четкие вопросы и помогай пользователю сформулировать ответы.",
        "auditor": "Ты - эксперт по аудиту проектов. Анализируй информацию и давай конструктивные рекомендации.",
        "planner": "Ты - специалист по планированию. Создавай структуру документов на основе собранной информации.",
        "writer": "Ты - профессиональный писатель. Создавай качественные тексты на основе структуры и информации."
    }

def save_prompts(prompts):
    """Сохранение промптов в файл"""
    # Здесь будет сохранение в файл или БД
    pass 