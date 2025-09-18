import streamlit as st
import sys
import os
import json
from datetime import datetime

# Добавляем путь к модулям базы данных
sys.path.append('/var/GrantService/data')

try:
    from database.prompts import (
        init_prompts_tables, insert_default_prompts, get_prompts_by_agent,
        get_prompts_by_category, create_prompt, update_prompt, delete_prompt,
        get_all_categories, format_prompt, get_prompt_by_name
    )
    PROMPTS_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Ошибка импорта модуля промптов: {e}")
    PROMPTS_AVAILABLE = False

st.set_page_config(
    page_title="⚙️ Управление промптами",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_database():
    """Инициализация базы данных промптов"""
    if st.button("🗄️ Инициализировать базу промптов"):
        with st.spinner("Создание таблиц..."):
            init_prompts_tables()
        with st.spinner("Добавление дефолтных промптов..."):
            insert_default_prompts()
        st.success("✅ База данных промптов инициализирована!")

def show_prompt_editor(prompt_data=None):
    """Редактор промпта"""
    st.subheader("✏️ Редактор промпта")
    
    # Получаем категории для выбора
    categories = get_all_categories()
    category_options = {cat['name']: cat['description'] for cat in categories}
    
    with st.form("prompt_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            category_name = st.selectbox(
                "Категория",
                options=list(category_options.keys()),
                index=0 if not prompt_data else list(category_options.keys()).index(prompt_data.get('category_name', '')),
                help="Выберите категорию промпта"
            )
            
            name = st.text_input(
                "Название промпта",
                value=prompt_data.get('name', '') if prompt_data else '',
                help="Краткое название промпта"
            )
            
            priority = st.number_input(
                "Приоритет",
                min_value=0,
                max_value=100,
                value=prompt_data.get('priority', 0) if prompt_data else 0,
                help="Приоритет промпта (выше = важнее)"
            )
        
        with col2:
            description = st.text_area(
                "Описание",
                value=prompt_data.get('description', '') if prompt_data else '',
                height=100,
                help="Описание назначения промпта"
            )
            
            # Переменные промпта
            variables_text = st.text_area(
                "Переменные (по одной на строку)",
                value='\n'.join(prompt_data.get('variables', [])) if prompt_data else '',
                height=100,
                help="Список переменных, используемых в промпте"
            )
        
        # Шаблон промпта
        prompt_template = st.text_area(
            "Шаблон промпта",
            value=prompt_data.get('prompt_template', '') if prompt_data else '',
            height=300,
            help="Шаблон промпта с переменными в фигурных скобках {variable_name}"
        )
        
        # Предварительный просмотр
        if prompt_template and variables_text:
            st.subheader("👁️ Предварительный просмотр")
            
            # Парсим переменные
            variables_list = [v.strip() for v in variables_text.split('\n') if v.strip()]
            
            # Создаем тестовые данные
            test_data = {}
            for var in variables_list:
                test_data[var] = f"[{var}]"
            
            try:
                preview = format_prompt(prompt_template, test_data)
                st.code(preview, language="text")
            except Exception as e:
                st.error(f"Ошибка предварительного просмотра: {e}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submitted = st.form_submit_button("💾 Сохранить")
        
        with col2:
            if prompt_data:
                delete_clicked = st.form_submit_button("🗑️ Удалить", type="secondary")
            else:
                delete_clicked = False
        
        with col3:
            test_clicked = st.form_submit_button("🧪 Тест")
        
        if submitted:
            if not name or not prompt_template:
                st.error("❌ Заполните название и шаблон промпта!")
                return
            
            variables_list = [v.strip() for v in variables_text.split('\n') if v.strip()]
            
            if prompt_data:
                # Обновление
                success = update_prompt(
                    prompt_id=prompt_data['id'],
                    name=name,
                    description=description,
                    prompt_template=prompt_template,
                    variables=variables_list,
                    priority=priority
                )
                if success:
                    st.success("✅ Промпт обновлен!")
                    st.rerun()
                else:
                    st.error("❌ Ошибка обновления промпта!")
            else:
                # Создание
                success = create_prompt(
                    category_name=category_name,
                    name=name,
                    description=description,
                    prompt_template=prompt_template,
                    variables=variables_list,
                    priority=priority
                )
                if success:
                    st.success("✅ Промпт создан!")
                    st.rerun()
                else:
                    st.error("❌ Ошибка создания промпта!")
        
        if delete_clicked and prompt_data:
            if st.checkbox("Подтвердить удаление"):
                success = delete_prompt(prompt_data['id'])
                if success:
                    st.success("✅ Промпт удален!")
                    st.rerun()
                else:
                    st.error("❌ Ошибка удаления промпта!")

def show_prompts_by_agent():
    """Показать промпты по агентам"""
    st.subheader("🤖 Промпты по агентам")
    
    agent_types = ["researcher", "writer", "auditor", "interviewer"]
    selected_agent = st.selectbox("Выберите агента", agent_types)
    
    prompts = get_prompts_by_agent(selected_agent)
    
    if not prompts:
        st.info(f"📝 Нет промптов для агента {selected_agent}")
        return
    
    # Группируем по категориям
    categories = {}
    for prompt in prompts:
        cat = prompt['category_name']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(prompt)
    
    for category_name, category_prompts in categories.items():
        with st.expander(f"📁 {category_name} ({len(category_prompts)} промптов)"):
            for prompt in category_prompts:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{prompt['name']}**")
                    if prompt['description']:
                        st.caption(prompt['description'])
                
                with col2:
                    st.write(f"Приоритет: {prompt['priority']}")
                
                with col3:
                    if st.button("✏️", key=f"edit_{prompt['id']}"):
                        st.session_state.editing_prompt = prompt
                        st.rerun()

def show_prompts_by_category():
    """Показать промпты по категориям"""
    st.subheader("📁 Промпты по категориям")
    
    categories = get_all_categories()
    
    if not categories:
        st.info("📝 Нет категорий промптов")
        return
    
    selected_category = st.selectbox(
        "Выберите категорию",
        options=[cat['name'] for cat in categories],
        format_func=lambda x: f"{x} ({next((cat['agent_type'] for cat in categories if cat['name'] == x), '')})"
    )
    
    prompts = get_prompts_by_category(selected_category)
    
    if not prompts:
        st.info(f"📝 Нет промптов в категории {selected_category}")
        return
    
    for prompt in prompts:
        with st.expander(f"📄 {prompt['name']} (приоритет: {prompt['priority']})"):
            st.write(f"**Описание:** {prompt['description'] or 'Нет описания'}")
            st.write(f"**Переменные:** {', '.join(prompt['variables']) if prompt['variables'] else 'Нет переменных'}")
            
            st.write("**Шаблон:**")
            st.code(prompt['prompt_template'], language="text")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Редактировать", key=f"edit_cat_{prompt['id']}"):
                    st.session_state.editing_prompt = prompt
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Удалить", key=f"delete_cat_{prompt['id']}"):
                    if st.checkbox("Подтвердить удаление", key=f"confirm_{prompt['id']}"):
                        success = delete_prompt(prompt['id'])
                        if success:
                            st.success("✅ Промпт удален!")
                            st.rerun()
                        else:
                            st.error("❌ Ошибка удаления!")

def show_prompt_tester():
    """Тестер промптов"""
    st.subheader("🧪 Тестер промптов")
    
    # Выбор промпта
    all_prompts = []
    for agent_type in ["researcher", "writer", "auditor", "interviewer"]:
        prompts = get_prompts_by_agent(agent_type)
        all_prompts.extend(prompts)
    
    if not all_prompts:
        st.info("📝 Нет доступных промптов для тестирования")
        return
    
    selected_prompt_name = st.selectbox(
        "Выберите промпт для тестирования",
        options=[p['name'] for p in all_prompts],
        format_func=lambda x: f"{x} ({next((p['agent_type'] for p in all_prompts if p['name'] == x), '')})"
    )
    
    prompt_data = get_prompt_by_name(selected_prompt_name)
    
    if not prompt_data:
        st.error("❌ Промпт не найден!")
        return
    
    st.write(f"**Описание:** {prompt_data['description']}")
    st.write(f"**Переменные:** {', '.join(prompt_data['variables'])}")
    
    # Ввод тестовых данных
    st.write("**Тестовые данные:**")
    test_data = {}
    
    for variable in prompt_data['variables']:
        test_data[variable] = st.text_area(
            f"Значение для {variable}",
            value=f"Тестовое значение для {variable}",
            height=100
        )
    
    # Форматированный промпт
    if st.button("🔧 Форматировать промпт"):
        try:
            formatted_prompt = format_prompt(prompt_data['prompt_template'], test_data)
            st.write("**Результат форматирования:**")
            st.code(formatted_prompt, language="text")
            
            # Копирование в буфер
            st.text_area("Скопируйте результат", formatted_prompt, height=200)
            
        except Exception as e:
            st.error(f"❌ Ошибка форматирования: {e}")

def main():
    st.title("⚙️ Управление промптами агентов")
    st.markdown("---")
    
    if not PROMPTS_AVAILABLE:
        st.error("❌ Модуль промптов недоступен!")
        return
    
    # Инициализация сессии
    if 'editing_prompt' not in st.session_state:
        st.session_state.editing_prompt = None
    
    # Боковая панель
    st.sidebar.title("🎯 Действия")
    
    action = st.sidebar.selectbox(
        "Выберите действие",
        [
            "🗄️ Инициализация БД",
            "✏️ Редактор промптов",
            "🤖 По агентам",
            "📁 По категориям",
            "🧪 Тестер промптов"
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ Информация")
    st.sidebar.info("""
    **Система промптов GrantService**
    
    Управляйте промптами для всех ИИ-агентов:
    - Researcher (исследователь)
    - Writer (писатель)
    - Auditor (аудитор)
    - Interviewer (интервьюер)
    
    Промпты хранятся в базе данных и могут быть изменены без перезапуска.
    """)
    
    # Основной контент
    if action == "🗄️ Инициализация БД":
        init_database()
        
    elif action == "✏️ Редактор промптов":
        if st.session_state.editing_prompt:
            show_prompt_editor(st.session_state.editing_prompt)
            if st.button("❌ Отменить редактирование"):
                st.session_state.editing_prompt = None
                st.rerun()
        else:
            show_prompt_editor()
            
    elif action == "🤖 По агентам":
        show_prompts_by_agent()
        
    elif action == "📁 По категориям":
        show_prompts_by_category()
        
    elif action == "🧪 Тестер промптов":
        show_prompt_tester()

if __name__ == "__main__":
    main()
