import streamlit as st
import sys
import os
import json
from datetime import datetime, timedelta
import pandas as pd

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
# Добавляем пути к модулям
sys.path.append('/var/GrantService/data')
sys.path.append('/var/GrantService')

# Импорты базы данных
try:
    from database import GrantServiceDatabase
    DATABASE_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Ошибка импорта базы данных: {e}")
    DATABASE_AVAILABLE = False

# Настройка страницы
st.set_page_config(
    page_title="📄 Грантовые заявки",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

def show_applications_list():
    """Показывает список всех заявок"""
    if not DATABASE_AVAILABLE:
        st.error("❌ База данных недоступна")
        return
    
    db = GrantServiceDatabase()
    
    st.header("📄 Список грантовых заявок")
    st.markdown("---")
    
    # Получаем статистику
    stats = db.get_applications_statistics()
    
    # Показываем статистику
    if stats:
        st.subheader("📊 Статистика")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего заявок", stats.get('total_applications', 0))
        
        with col2:
            st.metric("Средняя оценка", f"{stats.get('average_quality_score', 0):.1f}/10")
        
        with col3:
            draft_count = stats.get('status_distribution', {}).get('draft', 0)
            st.metric("Черновики", draft_count)
        
        with col4:
            submitted_count = stats.get('status_distribution', {}).get('submitted', 0)
            st.metric("Отправлены", submitted_count)
        
        # Распределение по статусам
        if stats.get('status_distribution'):
            st.subheader("📈 Распределение по статусам")
            
            status_data = stats['status_distribution']
            status_names = {
                'draft': 'Черновик',
                'submitted': 'Отправлена',
                'approved': 'Одобрена',
                'rejected': 'Отклонена'
            }
            
            status_df = pd.DataFrame([
                {'Статус': status_names.get(status, status), 'Количество': count}
                for status, count in status_data.items()
            ])
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.bar_chart(status_df.set_index('Статус'))
            with col2:
                st.dataframe(status_df, use_container_width=True)
    
    # Фильтры
    st.subheader("🔍 Фильтры")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Статус",
            ["Все", "draft", "submitted", "approved", "rejected"],
            format_func=lambda x: {
                "Все": "Все статусы",
                "draft": "Черновик", 
                "submitted": "Отправлена",
                "approved": "Одобрена",
                "rejected": "Отклонена"
            }.get(x, x)
        )
    
    with col2:
        date_filter = st.selectbox(
            "Период",
            ["Все время", "Сегодня", "Неделя", "Месяц"]
        )
    
    with col3:
        provider_filter = st.selectbox(
            "LLM провайдер",
            ["Все", "gigachat", "local", "fallback"]
        )
    
    # Получаем список заявок
    applications = db.get_all_applications(limit=50)
    
    if not applications:
        st.info("📝 Пока нет созданных заявок")
        return
    
    # Дедупликация по номеру заявки
    seen_numbers = set()
    unique_applications = []
    for app in applications:
        app_number = app.get('application_number', '')
        if app_number and app_number not in seen_numbers:
            seen_numbers.add(app_number)
            unique_applications.append(app)
    
    applications = unique_applications
    
    # Применяем фильтры
    filtered_apps = applications
    
    if status_filter != "Все":
        filtered_apps = [app for app in filtered_apps if app.get('status') == status_filter]
    
    if provider_filter != "Все":
        filtered_apps = [app for app in filtered_apps if app.get('llm_provider') == provider_filter]
    
    # Фильтр по дате
    if date_filter != "Все время":
        now = datetime.now()
        if date_filter == "Сегодня":
            cutoff_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == "Неделя":
            cutoff_date = now - timedelta(days=7)
        elif date_filter == "Месяц":
            cutoff_date = now - timedelta(days=30)
        
        date_filtered_apps = []
        for app in filtered_apps:  # Используем уже отфильтрованные заявки
            try:
                created_at = datetime.fromisoformat(app.get('created_at', ''))
                if created_at >= cutoff_date:
                    date_filtered_apps.append(app)
            except:
                continue
        filtered_apps = date_filtered_apps
    
    # Показываем заявки
    st.subheader(f"📄 Заявки ({len(filtered_apps)})")
    
    if not filtered_apps:
        st.info("🔍 По выбранным фильтрам заявки не найдены")
        return
    
    # Создаем таблицу
    for app in filtered_apps:
        # Создаем красивый заголовок
        title = app.get('title', 'Без названия')
        if len(title) > 80:
            display_title = title[:80] + "..."
        else:
            display_title = title
            
        app_number = app.get('application_number', 'Без номера')
        
        with st.expander(f"📄 {display_title} (#{app_number})", expanded=False):
            
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
            
            # Дополнительная информация
            if app.get('summary'):
                st.write("**Описание:**")
                st.write(app['summary'])
            
            # Кнопки действий
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                if st.button(f"👁️ Просмотр", key=f"view_{app['id']}"):
                    st.session_state.selected_application = app['application_number']
                    st.switch_page("pages/📄_Просмотр_заявки.py")
            
            with col2:
                if st.button(f"✏️ Изменить статус", key=f"status_{app['id']}"):
                    change_status_modal(app)
            
            with col3:
                if st.button(f"📥 Экспорт", key=f"export_{app['id']}"):
                    export_application(app['application_number'])
            
            with col4:
                if st.button(f"📋 Копировать", key=f"copy_{app['id']}"):
                    st.session_state.copy_source = app['application_number']
                    st.success("✅ Номер заявки скопирован!")
            
            with col5:
                if app.get('status') == 'draft':
                    if st.button(f"🗑️ Удалить", key=f"delete_{app['id']}", type="secondary"):
                        # Здесь можно добавить логику удаления
                        st.warning("⚠️ Функция удаления будет добавлена позже")

def change_status_modal(app):
    """Модальное окно для изменения статуса заявки"""
    with st.container():
        st.subheader(f"Изменение статуса заявки #{app['application_number']}")
        
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
            }.get(x, x),
            key=f"new_status_{app['id']}"
        )
        
        if st.button("💾 Сохранить изменения", key=f"save_status_{app['id']}"):
            if DATABASE_AVAILABLE:
                db = GrantServiceDatabase()
                success = db.update_application_status(app['application_number'], new_status)
                
                if success:
                    st.success(f"✅ Статус изменен на: {new_status}")
                    st.rerun()
                else:
                    st.error("❌ Ошибка изменения статуса")

def export_application(application_number):
    """Экспорт заявки в различных форматах"""
    if not DATABASE_AVAILABLE:
        st.error("❌ База данных недоступна")
        return
    
    db = GrantServiceDatabase()
    app = db.get_application_by_number(application_number)
    
    if not app:
        st.error("❌ Заявка не найдена")
        return
    
    # JSON экспорт
    export_data = {
        'application_number': app['application_number'],
        'title': app['title'],
        'status': app['status'],
        'created_at': app['created_at'],
        'content': app.get('content', {}),
        'quality_score': app['quality_score']
    }
    
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="📥 Скачать JSON",
        data=json_str.encode('utf-8'),
        file_name=f"grant_application_{application_number}.json",
        mime="application/json",
        key=f"download_json_{application_number}"
    )

def main():
    """Главная функция страницы"""
    st.title("📄 Управление грантовыми заявками")
    
    # Боковое меню
    st.sidebar.title("🎯 Навигация")
    
    page_mode = st.sidebar.selectbox(
        "Выберите режим",
        ["📄 Список заявок", "📊 Аналитика", "⚙️ Настройки"]
    )
    
    if page_mode == "📄 Список заявок":
        show_applications_list()
    elif page_mode == "📊 Аналитика":
        show_analytics()
    elif page_mode == "⚙️ Настройки":
        show_settings()

def show_analytics():
    """Показывает аналитику по заявкам"""
    st.header("📊 Аналитика грантовых заявок")
    st.markdown("---")
    
    if not DATABASE_AVAILABLE:
        st.error("❌ База данных недоступна")
        return
    
    db = GrantServiceDatabase()
    applications = db.get_all_applications(limit=1000)  # Больше данных для аналитики
    
    if not applications:
        st.info("📝 Нет данных для аналитики")
        return
    
    # Создаем DataFrame для анализа
    df = pd.DataFrame(applications)
    
    # График по дням
    st.subheader("📈 Создание заявок по дням")
    
    if 'created_at' in df.columns:
        try:
            df['date'] = pd.to_datetime(df['created_at']).dt.date
            daily_counts = df.groupby('date').size().reset_index(name='count')
            
            if not daily_counts.empty:
                st.line_chart(daily_counts.set_index('date'))
            else:
                st.info("Недостаточно данных для графика")
        except Exception as e:
            st.error(f"Ошибка обработки дат: {e}")
    
    # Распределение по провайдерам
    st.subheader("🤖 Использование LLM провайдеров")
    
    if 'llm_provider' in df.columns:
        provider_counts = df['llm_provider'].value_counts()
        if not provider_counts.empty:
            st.bar_chart(provider_counts)
    
    # Качество заявок
    st.subheader("⭐ Распределение оценок качества")
    
    if 'quality_score' in df.columns:
        quality_scores = df['quality_score'].dropna()
        if not quality_scores.empty:
            hist_data = pd.DataFrame({'Оценка': quality_scores})
            st.histogram_chart(hist_data, x='Оценка')

def show_settings():
    """Показывает настройки системы заявок"""
    st.header("⚙️ Настройки системы заявок")
    st.markdown("---")
    
    st.subheader("🔧 Общие настройки")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_save = st.checkbox("Автоматическое сохранение заявок", value=True)
        show_debug = st.checkbox("Показывать отладочную информацию", value=False)
        
    with col2:
        default_status = st.selectbox(
            "Статус по умолчанию",
            ["draft", "submitted"],
            format_func=lambda x: {"draft": "Черновик", "submitted": "Отправлена"}.get(x, x)
        )
    
    st.subheader("📤 Настройки экспорта")
    
    export_formats = st.multiselect(
        "Доступные форматы экспорта",
        ["JSON", "PDF", "DOCX", "TXT"],
        default=["JSON"]
    )
    
    if st.button("💾 Сохранить настройки"):
        st.success("✅ Настройки сохранены!")
    
    # Информация о системе
    st.markdown("---")
    st.subheader("ℹ️ Информация о системе")
    
    if DATABASE_AVAILABLE:
        db = GrantServiceDatabase()
        stats = db.get_applications_statistics()
        
        st.info(f"""
        **Состояние системы:**
        - ✅ База данных подключена
        - 📄 Всего заявок: {stats.get('total_applications', 0)}
        - ⭐ Средняя оценка: {stats.get('average_quality_score', 0):.1f}/10
        - 🕒 Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
    else:
        st.error("❌ База данных недоступна")

if __name__ == "__main__":
    main()

