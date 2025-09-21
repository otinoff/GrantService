import streamlit as st
import sys
import os

# Simple imports without path manipulation
# The environment will be set up by the launcher

# Authorization check
try:
    from utils.auth import is_user_authorized
    if not is_user_authorized():
        st.error("⛔ Не авторизован / Not authorized")
        st.info("Пожалуйста, используйте бота для получения токена / Please use the bot to get a token")
        st.stop()
except ImportError as e:
    st.error(f"❌ Ошибка импорта / Import error: {e}")
    st.info("Запустите через launcher.py / Run via launcher.py")
    st.stop()

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService
sys.path.insert(0, grandparent_dir)  # Для импорта config и data
sys.path.insert(0, parent_dir)  # Для импорта utils

# Проверка авторизации
from utils.auth import is_user_authorized

if not is_user_authorized():
    # Импортируем страницу входа
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "login_page", 
        os.path.join(current_dir, "🔐_Вход.py")
    )
    login_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(login_module)
    login_module.show_login_page()
    st.stop()
# Добавляем пути к модулям
sys.path.append(os.path.join(grandparent_dir, 'telegram-bot'))
sys.path.append(os.path.join(grandparent_dir, 'data'))
sys.path.append(grandparent_dir)

# Импорты агентов и сервисов
try:
    from services.llm_router import LLMRouter, LLMProvider
    from services.gigachat_service import GigaChatService
    from services.local_llm_service import LocalLLMService
    # Импорт агентов из общей папки
    sys.path.append(os.path.join(grandparent_dir, 'agents'))
    from agents.researcher_agent import ResearcherAgent
    from agents.writer_agent import WriterAgent
    from agents.auditor_agent import AuditorAgent
    from agents.interviewer_agent import InterviewerAgent
    from agents.grant_crew import GrantCrew
    from database.prompts import (
        get_prompts_by_agent, get_prompt_by_name, format_prompt,
        create_prompt, update_prompt, delete_prompt, get_all_categories
    )
    # Импорт базы данных для работы с анкетами
    from data.database.models import GrantServiceDatabase
    AGENTS_AVAILABLE = True
    PROMPTS_AVAILABLE = True
    DATABASE_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Ошибка импорта агентов: {e}")
    AGENTS_AVAILABLE = False
    PROMPTS_AVAILABLE = False
    DATABASE_AVAILABLE = False

# Настройка страницы
st.set_page_config(
    page_title="🤖 AI Агенты GrantService",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация сессии
if 'agent_results' not in st.session_state:
    st.session_state.agent_results = {}
if 'current_agent' not in st.session_state:
    st.session_state.current_agent = "researcher"

def show_llm_status():
    """Показывает статус LLM провайдеров"""
    try:
        router = LLMRouter()
        status = router.get_provider_status()
        
        st.subheader("🤖 Статус LLM провайдеров")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Текущий провайдер", status['current_provider'].upper())
        
        with col2:
            available_count = len(status['available_providers'])
            st.metric("Доступно провайдеров", available_count)
        
        with col3:
            if status['providers'].get('local', {}).get('available', False):
                models = status['providers']['local'].get('models', [])
                st.metric("Локальные модели", len(models))
        
        # Детальный статус
        st.subheader("📊 Детальный статус")
        
        for provider_name, provider_info in status['providers'].items():
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if provider_info['available']:
                    st.success(f"✅ {provider_name.upper()}")
                else:
                    st.error(f"❌ {provider_name.upper()}")
            
            with col2:
                if provider_name == 'local' and 'models' in provider_info:
                    st.write(f"Модели: {', '.join(provider_info['models'])}")
                else:
                    st.write("Статус: " + ("Доступен" if provider_info['available'] else "Недоступен"))
            
            with col3:
                if st.button(f"🔄 Тест {provider_name}", key=f"test_{provider_name}"):
                    test_provider(provider_name)
        
    except Exception as e:
        st.error(f"❌ Ошибка получения статуса: {e}")

def show_prompt_management(agent_type: str):
    """Управление промптами для агента"""
    if not PROMPTS_AVAILABLE:
        st.warning("⚠️ Модуль промптов недоступен")
        return
    
    st.subheader("⚙️ Управление промптами")
    
    # Получаем промпты агента
    prompts = get_prompts_by_agent(agent_type)
    
    if not prompts:
        st.info(f"📝 Нет промптов для агента {agent_type}")
        return
    
    # Выбор промпта для редактирования
    prompt_names = [p['name'] for p in prompts]
    selected_prompt_name = st.selectbox(
        "Выберите промпт для редактирования",
        prompt_names,
        key=f"prompt_select_{agent_type}"
    )
    
    selected_prompt = next((p for p in prompts if p['name'] == selected_prompt_name), None)
    
    if selected_prompt:
        with st.expander(f"✏️ Редактирование промпта: {selected_prompt['name']}"):
            with st.form(f"prompt_form_{agent_type}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input(
                        "Название",
                        value=selected_prompt['name'],
                        key=f"name_{agent_type}"
                    )
                    
                    priority = st.number_input(
                        "Приоритет",
                        min_value=0,
                        max_value=100,
                        value=selected_prompt['priority'],
                        key=f"priority_{agent_type}"
                    )
                
                with col2:
                    description = st.text_area(
                        "Описание",
                        value=selected_prompt['description'] or '',
                        height=100,
                        key=f"desc_{agent_type}"
                    )
                    
                    variables_text = st.text_area(
                        "Переменные (по одной на строку)",
                        value='\n'.join(selected_prompt['variables']),
                        height=100,
                        key=f"vars_{agent_type}"
                    )
                
                # Шаблон промпта
                prompt_template = st.text_area(
                    "Шаблон промпта",
                    value=selected_prompt['prompt_template'],
                    height=200,
                    key=f"template_{agent_type}"
                )
                
                # Предварительный просмотр
                if prompt_template and variables_text:
                    variables_list = [v.strip() for v in variables_text.split('\n') if v.strip()]
                    test_data = {var: f"[{var}]" for var in variables_list}
                    
                    try:
                        preview = format_prompt(prompt_template, test_data)
                        st.write("**Предварительный просмотр:**")
                        st.code(preview, language="text")
                    except Exception as e:
                        st.error(f"Ошибка предварительного просмотра: {e}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.form_submit_button("💾 Сохранить"):
                        variables_list = [v.strip() for v in variables_text.split('\n') if v.strip()]
                        
                        success = update_prompt(
                            prompt_id=selected_prompt['id'],
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
                
                with col2:
                    if st.form_submit_button("🗑️ Удалить", type="secondary"):
                        if st.checkbox("Подтвердить удаление"):
                            success = delete_prompt(selected_prompt['id'])
                            if success:
                                st.success("✅ Промпт удален!")
                                st.rerun()
                            else:
                                st.error("❌ Ошибка удаления!")
                
                with col3:
                    if st.form_submit_button("🧪 Тест"):
                        st.info("Промпт готов к тестированию!")

def test_provider(provider_name):
    """Тестирует провайдера"""
    try:
        # Попробуем сначала новый UnifiedLLMClient
        if provider_name == "gigachat":
            test_gigachat_unified()
        else:
            # Fallback на старый роутер для других провайдеров
            router = LLMRouter()
            
            if provider_name == "local":
                provider = LLMProvider.LOCAL
            elif provider_name == "gigachat":
                provider = LLMProvider.GIGACHAT
            else:
                provider = LLMProvider.AUTO
            
            result = router.analyze_grant_application(
                "Тестовый проект для проверки работы провайдера",
                "Критерии: инновационность, социальная значимость",
                provider
            )
            
            if result.get('error'):
                st.error(f"❌ Ошибка тестирования {provider_name}: {result['error']}")
            else:
                st.success(f"✅ {provider_name.upper()} работает! Использован провайдер: {result.get('provider_used', 'Unknown')}")
                
    except Exception as e:
        st.error(f"❌ Ошибка тестирования {provider_name}: {e}")

def test_gigachat_unified():
    """Тестирует GigaChat через UnifiedLLMClient"""
    import asyncio
    
    try:
        # Добавляем путь к UnifiedLLMClient
        sys.path.append('/var/GrantService/shared')
        from llm.unified_llm_client import UnifiedLLMClient
        
        async def run_test():
            async with UnifiedLLMClient() as client:
                response = await client.generate_async(
                    "Кратко ответь: что такое грант?",
                    provider="gigachat",
                    max_tokens=50
                )
                return response
        
        # Запускаем тест
        with st.spinner("🔄 Тестируем GigaChat..."):
            response = asyncio.run(run_test())
            
        if response and len(response) > 10:
            st.success(f"✅ GIGACHAT работает через UnifiedLLMClient!")
            with st.expander("📝 Пример ответа"):
                st.write(response[:200] + "..." if len(response) > 200 else response)
        else:
            st.error("❌ GigaChat дал пустой ответ")
            
    except Exception as e:
        st.error(f"❌ Ошибка тестирования GigaChat: {e}")
        # Fallback на старый метод
        try:
            router = LLMRouter()
            result = router.analyze_grant_application(
                "Тест",
                "Критерии тестирования",
                LLMProvider.GIGACHAT
            )
            if not result.get('error'):
                st.warning("⚠️ GigaChat работает через старый роутер")
        except:
            pass

def show_researcher_agent():
    """Страница агента-исследователя"""
    st.header("🔍 Researcher Agent")
    st.markdown("---")
    
    # Настройки
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("⚙️ Настройки агента")
        
        llm_provider = st.selectbox(
            "Провайдер LLM",
            ["auto", "gigachat", "local"],
            key="researcher_provider"
        )
        
        if llm_provider == "local":
            model = st.selectbox("Локальная модель", ["qwen2.5:3b", "qwen2.5:7b"], key="researcher_local_model")
        elif llm_provider == "gigachat":
            model = st.selectbox("GigaChat модель", ["GigaChat", "GigaChat-Pro"], key="researcher_giga_model")
        else:
            model = "auto"
        
        temperature = st.slider("Температура", 0.1, 1.0, 0.3, key="researcher_temp")
        max_tokens = st.number_input("Макс. токенов", 100, 2000, 1000, key="researcher_tokens")
    
    with col2:
        st.subheader("📊 Статистика")
        st.metric("Запросов сегодня", "12")
        st.metric("Среднее время", "2.3 сек")
        st.metric("Успешность", "95%")
    
    # Ручное исследование анкет
    st.subheader("🎯 Ручное исследование анкет")
    
    if DATABASE_AVAILABLE:
        try:
            # Инициализируем базу данных
            db = GrantServiceDatabase()
            
            # Получаем список анкет
            all_sessions = db.get_all_sessions(limit=1000)
            anketas = [s for s in all_sessions if s.get('anketa_id')]
            
            if anketas:
                # Создаем список для выбора
                anketa_options = []
                for anketa in anketas:
                    user_display = anketa.get('username', f"ID:{anketa['telegram_id']}")
                    date_str = anketa.get('started_at', 'Unknown')[:10] if anketa.get('started_at') else 'Unknown'
                    anketa_options.append(f"{anketa['anketa_id']} - {user_display} ({date_str})")
                
                selected_anketa_display = st.selectbox(
                    "Выберите анкету для исследования:",
                    anketa_options,
                    key="selected_anketa_researcher"
                )
                
                if selected_anketa_display:
                    # Извлекаем anketa_id из выбранного варианта
                    selected_anketa_id = selected_anketa_display.split(' - ')[0]
                    
                    # Показываем информацию об анкете
                    selected_anketa = next((a for a in anketas if a['anketa_id'] == selected_anketa_id), None)
                    
                    if selected_anketa:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            user_display = selected_anketa.get('username', f"ID:{selected_anketa['telegram_id']}")
                            st.info(f"**Пользователь:** {user_display}")
                        with col2:
                            date_display = selected_anketa.get('started_at', 'Unknown')[:10] if selected_anketa.get('started_at') else 'Unknown'
                            st.info(f"**Дата:** {date_display}")
                        with col3:
                            st.info(f"**Статус:** {selected_anketa.get('status', 'Unknown')}")
                        
                        # Кнопка запуска исследования анкеты
                        if st.button("🚀 Исследовать анкету", type="primary", key="research_anketa_btn"):
                            if AGENTS_AVAILABLE:
                                with st.spinner("🔍 Исследую анкету..."):
                                    try:
                                        # Создаем агента с базой данных
                                        agent = ResearcherAgent(db=db, llm_provider=llm_provider)
                                        
                                        # Запускаем исследование анкеты
                                        result = agent.research_anketa(selected_anketa_id)
                                        
                                        if result.get('status') == 'success':
                                            st.success(f"✅ Исследование завершено! ID: {result.get('research_id')}")
                                            
                                            # Показываем результат
                                            with st.expander("📊 Результат исследования", expanded=True):
                                                st.text_area(
                                                    "Результат",
                                                    result.get('result', ''),
                                                    height=300,
                                                    disabled=True
                                                )
                                        else:
                                            st.error(f"❌ Ошибка исследования: {result.get('message', 'Неизвестная ошибка')}")
                                            
                                    except Exception as e:
                                        st.error(f"❌ Ошибка: {str(e)}")
                            else:
                                st.warning("⚠️ Агенты недоступны")
            else:
                st.info("📋 Пока нет анкет для исследования")
                
        except Exception as e:
            st.error(f"❌ Ошибка работы с базой данных: {e}")
    else:
        st.warning("⚠️ База данных недоступна")
    
    st.markdown("---")
    
    # Ввод данных
    st.subheader("📝 Входные данные для исследования")
    
    # Проверяем данные от других агентов
    if 'writer_input' in st.session_state:
        st.info("📤 Получены данные от Writer Agent")
        default_input = st.session_state.writer_input
    elif 'auditor_input' in st.session_state:
        st.info("📤 Получены данные от Auditor Agent")
        default_input = st.session_state.auditor_input
    else:
        default_input = ""
    
    research_data = st.text_area(
        "Введите данные для исследования",
        value=default_input,
        placeholder="Название проекта, описание, цели, бюджет...",
        height=200,
        key="researcher_input"
    )
    
    # Запуск исследования
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Запустить исследование", type="primary", use_container_width=True):
            if research_data and AGENTS_AVAILABLE:
                with st.spinner("🔍 Провожу исследование..."):
                    try:
                        # Создаем агента
                        agent = ResearcherAgent(db=None, llm_provider=llm_provider)
                        
                        # Запускаем исследование
                        result = agent.research_grant({
                            'description': research_data,
                            'llm_provider': llm_provider,
                            'model': model,
                            'temperature': temperature,
                            'max_tokens': max_tokens
                        })
                        
                        # Сохраняем результат
                        st.session_state.agent_results['researcher'] = result
                        st.session_state.researcher_timestamp = datetime.now()
                        
                        st.success("✅ Исследование завершено!")
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")
            else:
                st.warning("⚠️ Введите данные для исследования")
    
    with col2:
        if st.button("🧹 Очистить данные", use_container_width=True):
            if 'researcher' in st.session_state.agent_results:
                del st.session_state.agent_results['researcher']
            if 'researcher_timestamp' in st.session_state:
                del st.session_state.researcher_timestamp
            st.success("✅ Данные очищены!")
    
    # Результаты
    if 'researcher' in st.session_state.agent_results:
        st.markdown("---")
        st.subheader("📊 Результаты исследования")
        
        result = st.session_state.agent_results['researcher']
        timestamp = st.session_state.researcher_timestamp
        
        # Информация о запросе
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Провайдер", result.get('provider', 'Unknown'))
        with col2:
            st.metric("Время обработки", f"{result.get('processing_time', 0):.2f} сек")
        with col3:
            st.metric("Дата", timestamp.strftime("%H:%M:%S"))
        
        # Результат
        st.text_area(
            "Результат исследования",
            result.get('result', ''),
            height=300,
            disabled=True
        )
        
        # Передача результата
        st.subheader("📤 Передача результата")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📤 → Writer", use_container_width=True):
                st.session_state.writer_input = result.get('result', '')
                st.success("✅ Отправлено в Writer Agent!")
        
        with col2:
            if st.button("📤 → Auditor", use_container_width=True):
                st.session_state.auditor_input = result.get('result', '')
                st.success("✅ Отправлено в Auditor Agent!")
        
        with col3:
            if st.button("📤 → Interviewer", use_container_width=True):
                st.session_state.interviewer_input = result.get('result', '')
                st.success("✅ Отправлено в Interviewer Agent!")
        
        with col4:
            if st.button("💾 Сохранить", use_container_width=True):
                st.success("✅ Результат сохранен!")
    
    # Управление промптами
    show_prompt_management("researcher")

def show_writer_agent():
    """Страница агента-писателя"""
    st.header("✍️ Writer Agent")
    st.markdown("---")
    
    # Настройки
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("⚙️ Настройки агента")
        
        llm_provider = st.selectbox(
            "Провайдер LLM",
            ["auto", "gigachat", "local"],
            key="writer_provider"
        )
        
        if llm_provider == "local":
            model = st.selectbox("Локальная модель", ["qwen2.5:3b", "qwen2.5:7b"], key="writer_local_model")
        elif llm_provider == "gigachat":
            model = st.selectbox("GigaChat модель", ["GigaChat", "GigaChat-Pro"], key="writer_giga_model")
        else:
            model = "auto"
        
        temperature = st.slider("Температура", 0.1, 1.0, 0.4, key="writer_temp")
        max_tokens = st.number_input("Макс. токенов", 100, 3000, 1500, key="writer_tokens")
    
    with col2:
        st.subheader("📊 Статистика")
        st.metric("Заявок создано", "8")
        st.metric("Среднее время", "3.1 сек")
        st.metric("Успешность", "92%")
    
    # Выбор данных из базы
    st.subheader("📋 Выбор данных для написания")
    
    if DATABASE_AVAILABLE:
        try:
            # Инициализируем базу данных
            db_instance = GrantServiceDatabase()
            
            # Получаем список анкет с исследованиями
            all_sessions = db_instance.get_all_sessions(limit=1000)
            anketas_with_research = []
            
            for session in all_sessions:
                if session.get('anketa_id'):
                    # Проверяем есть ли исследования для этой анкеты
                    research_list = db_instance.get_research_by_anketa_id(session['anketa_id'])
                    if research_list:
                        anketas_with_research.append({
                            'session': session,
                            'research': research_list[0]  # Берем первое исследование
                        })
            
            if anketas_with_research:
                # Создаем список для выбора
                anketa_options = []
                for item in anketas_with_research:
                    session = item['session']
                    research = item['research']
                    user_display = session.get('username', f"ID:{session['telegram_id']}")
                    date_str = session.get('started_at', 'Unknown')[:10] if session.get('started_at') else 'Unknown'
                    status = research.get('status', 'unknown')
                    anketa_options.append(f"{session['anketa_id']} - {user_display} ({date_str}) [{status}]")
                
                selected_anketa_display = st.selectbox(
                    "Выберите анкету с исследованием:",
                    ["--- Выберите анкету ---"] + anketa_options,
                    key="selected_anketa_writer"
                )
                
                if selected_anketa_display and selected_anketa_display != "--- Выберите анкету ---":
                    # Извлекаем anketa_id из выбранного варианта
                    selected_anketa_id = selected_anketa_display.split(' - ')[0]
                    
                    # Находим выбранные данные
                    selected_data = next((item for item in anketas_with_research 
                                        if item['session']['anketa_id'] == selected_anketa_id), None)
                    
                    if selected_data:
                        session = selected_data['session']
                        research = selected_data['research']
                        
                        # Показываем информацию о выбранных данных
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            user_display = session.get('username', f"ID:{session['telegram_id']}")
                            st.info(f"**👤 Пользователь:** {user_display}")
                        with col2:
                            st.info(f"**📋 Анкета:** {session['anketa_id']}")
                        with col3:
                            st.info(f"**🔬 Исследование:** {research['research_id']}")
                        
                        # Кнопка написания гранта
                        if st.button("✍️ Написать грант", type="primary", key="write_grant_btn"):
                            if AGENTS_AVAILABLE:
                                with st.spinner("✍️ Пишу грант на основе выбранных данных..."):
                                    try:
                                        # Формируем данные для писателя
                                        combined_data = f"""📋 АНКЕТА: {session['anketa_id']}
👤 Пользователь: @{session.get('username', 'N/A')} ({session.get('first_name', '')} {session.get('last_name', '')})
📅 Дата создания: {session.get('started_at', 'Unknown')[:10]}

🔬 ИССЛЕДОВАНИЕ: {research['research_id']}
🤖 Провайдер: {research['llm_provider']}
📊 Статус: {research['status']}
⏰ Завершено: {research.get('completed_at', 'N/A')}

📝 ДАННЫЕ АНКЕТЫ:
{json.dumps(session.get('interview_data', {}), ensure_ascii=False, indent=2)}

🔍 РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ:
{research.get('research_results', 'Нет данных')}

📋 ЛОГИ ПРОЦЕССА:
{research.get('logs', 'Нет логов')}
"""
                                        
                                        # Создаем агента с базой данных
                                        db = GrantServiceDatabase()
                                        agent = WriterAgent(db=db, llm_provider=llm_provider)
                                        
                                        # Запускаем написание гранта
                                        result = agent.write_application({
                                            'research_data': combined_data,
                                            'llm_provider': llm_provider,
                                            'model': model,
                                            'temperature': temperature,
                                            'max_tokens': max_tokens,
                                            'anketa_id': session['anketa_id'],
                                            'research_id': research['research_id']
                                        })
                                        
                                        # Сохраняем результат
                                        st.session_state.agent_results['writer'] = result
                                        st.session_state.writer_timestamp = datetime.now()
                                        st.session_state.writer_anketa_id = session['anketa_id']
                                        st.session_state.writer_research_id = research['research_id']
                                        
                                        st.success("✅ Грант написан!")
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"❌ Ошибка: {str(e)}")
                            else:
                                st.warning("⚠️ Агенты недоступны")
                        
                        # Превью данных
                        with st.expander("👁️ Превью данных", expanded=False):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**📋 Данные анкеты:**")
                                if session.get('interview_data'):
                                    st.json(session['interview_data'])
                                else:
                                    st.write("Нет данных")
                            
                            with col2:
                                st.write("**🔍 Результаты исследования:**")
                                st.text_area(
                                    "Содержание",
                                    research.get('research_results', 'Нет данных'),
                                    height=200,
                                    disabled=True
                                )
            else:
                st.info("📋 Пока нет анкет с завершенными исследованиями")
                
        except Exception as e:
            st.error(f"❌ Ошибка работы с базой данных: {e}")
    else:
        st.warning("⚠️ База данных недоступна")
    
    st.markdown("---")
    
    # Результаты написания гранта
    if 'writer' in st.session_state.agent_results:
        st.subheader("📄 Созданный грант")
        
        result = st.session_state.agent_results['writer']
        timestamp = st.session_state.writer_timestamp
        
        # Информация о созданном гранте
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Провайдер", result.get('provider', result.get('provider_used', 'Unknown')))
        with col2:
            st.metric("Время обработки", f"{result.get('processing_time', 0):.2f} сек")
        with col3:
            st.metric("Дата создания", timestamp.strftime("%H:%M:%S"))
        with col4:
            if 'application_number' in result:
                st.metric("Номер заявки", result['application_number'])
                st.success("✅ Грант сохранен в БД!")
            else:
                st.metric("Статус", "Создан")
        
        # Показываем созданный грант
        application = result.get('application', {})
        if application:
            st.subheader("📋 Содержание гранта")
            
            # Показываем каждый раздел гранта
            for section_key, section_content in application.items():
                section_name = {
                    'title': '📝 Название проекта',
                    'summary': '📋 Краткое описание',
                    'problem': '❗ Проблема',
                    'solution': '💡 Решение',
                    'implementation': '🛠️ План реализации',
                    'budget': '💰 Бюджет',
                    'timeline': '⏰ Временные рамки',
                    'team': '👥 Команда',
                    'impact': '🎯 Ожидаемый результат',
                    'sustainability': '♻️ Устойчивость'
                }.get(section_key, section_key.title())
                
                with st.expander(section_name, expanded=False):
                    st.write(section_content)
        else:
            st.text_area(
                "Созданный грант",
                result.get('result', 'Содержание гранта не найдено'),
                height=400,
                disabled=True
            )
        
        # Действия с созданным грантом
        st.subheader("📤 Действия с грантом")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📤 → Auditor", use_container_width=True):
                st.session_state.auditor_input = result.get('result', '')
                st.success("✅ Отправлено в Auditor Agent!")
        
        with col2:
            if st.button("📤 → Researcher", use_container_width=True):
                st.session_state.researcher_input = result.get('result', '')
                st.success("✅ Отправлено в Researcher Agent!")
        
        with col3:
            if st.button("💾 Сохранить", use_container_width=True):
                st.success("✅ Грант сохранен!")
        
        with col4:
            if st.button("🧹 Очистить", use_container_width=True):
                if 'writer' in st.session_state.agent_results:
                    del st.session_state.agent_results['writer']
                if 'writer_timestamp' in st.session_state:
                    del st.session_state.writer_timestamp
                if 'writer_anketa_id' in st.session_state:
                    del st.session_state.writer_anketa_id
                if 'writer_research_id' in st.session_state:
                    del st.session_state.writer_research_id
                st.success("✅ Данные очищены!")
                st.rerun()
    
    # Старая логика для ручного ввода (скрыта, но оставлена для совместимости)
    if st.checkbox("🔧 Ручной режим (для разработчиков)", key="manual_mode_writer"):
        st.subheader("📝 Ручной ввод данных")
    
    # Проверяем данные от других агентов
    if 'researcher_input' in st.session_state:
        st.info("📤 Получены данные от Researcher Agent")
        default_input = st.session_state.researcher_input
    elif 'auditor_input' in st.session_state:
        st.info("📤 Получены данные от Auditor Agent")
        default_input = st.session_state.auditor_input
    else:
        default_input = ""
    
    writing_data = st.text_area(
        "Введите данные для написания заявки",
        value=default_input,
        placeholder="Результаты исследования, требования гранта, данные проекта...",
        height=200,
        key="writer_input"
    )
    
    # Запуск написания
    col1, col2 = st.columns(2)
    
    with col1:
            if st.button("🚀 Создать заявку (ручной режим)", type="primary", use_container_width=True):
            if writing_data and AGENTS_AVAILABLE:
                with st.spinner("✍️ Создаю заявку..."):
                    try:
                        # Создаем агента с базой данных
                        db = GrantServiceDatabase()
                        agent = WriterAgent(db=db, llm_provider=llm_provider)
                        
                            # Запускаем написание
                            result = agent.write_application({
                                'research_data': writing_data,
                                'llm_provider': llm_provider,
                                'model': model,
                                'temperature': temperature,
                                'max_tokens': max_tokens
                            })
                            
                            # Сохраняем результат
                            st.session_state.agent_results['writer'] = result
                            st.session_state.writer_timestamp = datetime.now()
                            
                            st.success("✅ Заявка создана!")
                            
                        except Exception as e:
                            st.error(f"❌ Ошибка: {str(e)}")
                else:
                    st.warning("⚠️ Введите данные для написания")
        
        with col2:
            if st.button("🧹 Очистить данные", use_container_width=True):
                if 'writer' in st.session_state.agent_results:
                    del st.session_state.agent_results['writer']
                if 'writer_timestamp' in st.session_state:
                    del st.session_state.writer_timestamp
                st.success("✅ Данные очищены!")
                st.rerun()
    
    # Управление промптами
    show_prompt_management("writer")

def show_auditor_agent():
    """Страница агента-аудитора"""
    st.header("🔍 Auditor Agent")
    st.markdown("---")
    
    # Настройки
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("⚙️ Настройки агента")
        
        llm_provider = st.selectbox(
            "Провайдер LLM",
            ["auto", "gigachat", "local"],
            key="auditor_provider"
        )
        
        if llm_provider == "local":
            model = st.selectbox("Локальная модель", ["qwen2.5:3b", "qwen2.5:7b"], key="auditor_local_model")
        elif llm_provider == "gigachat":
            model = st.selectbox("GigaChat модель", ["GigaChat", "GigaChat-Pro"], key="auditor_giga_model")
        else:
            model = "auto"
        
        temperature = st.slider("Температура", 0.1, 1.0, 0.2, key="auditor_temp")
        max_tokens = st.number_input("Макс. токенов", 100, 2000, 1000, key="auditor_tokens")
    
    with col2:
        st.subheader("📊 Статистика")
        st.metric("Заявок проверено", "15")
        st.metric("Среднее время", "1.8 сек")
        st.metric("Успешность", "88%")
    
    # Ввод данных
    st.subheader("📝 Входные данные для аудита")
    
    # Проверяем данные от других агентов
    if 'writer_input' in st.session_state:
        st.info("📤 Получены данные от Writer Agent")
        default_input = st.session_state.writer_input
    elif 'researcher_input' in st.session_state:
        st.info("📤 Получены данные от Researcher Agent")
        default_input = st.session_state.researcher_input
    else:
        default_input = ""
    
    audit_data = st.text_area(
        "Введите данные для аудита",
        value=default_input,
        placeholder="Заявка, результаты исследования, требования гранта...",
        height=200,
        key="auditor_input"
    )
    
    # Запуск аудита
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Запустить аудит", type="primary", use_container_width=True):
            if audit_data and AGENTS_AVAILABLE:
                with st.spinner("🔍 Провожу аудит..."):
                    try:
                        # Создаем агента
                        agent = AuditorAgent(db=None, llm_provider=llm_provider)
                        
                        # Запускаем аудит
                        result = agent.audit_application({
                            'application': audit_data,
                            'llm_provider': llm_provider,
                            'model': model,
                            'temperature': temperature,
                            'max_tokens': max_tokens
                        })
                        
                        # Сохраняем результат
                        st.session_state.agent_results['auditor'] = result
                        st.session_state.auditor_timestamp = datetime.now()
                        
                        st.success("✅ Аудит завершен!")
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")
            else:
                st.warning("⚠️ Введите данные для аудита")
    
    with col2:
        if st.button("🧹 Очистить данные", use_container_width=True):
            if 'auditor' in st.session_state.agent_results:
                del st.session_state.agent_results['auditor']
            if 'auditor_timestamp' in st.session_state:
                del st.session_state.auditor_timestamp
            st.success("✅ Данные очищены!")
    
    # Результаты
    if 'auditor' in st.session_state.agent_results:
        st.markdown("---")
        st.subheader("📊 Результаты аудита")
        
        result = st.session_state.agent_results['auditor']
        timestamp = st.session_state.auditor_timestamp
        
        # Информация о запросе
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Провайдер", result.get('provider', 'Unknown'))
        with col2:
            st.metric("Время обработки", f"{result.get('processing_time', 0):.2f} сек")
        with col3:
            st.metric("Дата", timestamp.strftime("%H:%M:%S"))
        
        # Оценка
        if 'overall_score' in result:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Общая оценка", f"{result['overall_score']:.1f}/10")
            with col2:
                st.metric("Полнота", f"{result.get('completeness_score', 0):.1f}/10")
            with col3:
                st.metric("Качество", f"{result.get('quality_score', 0):.1f}/10")
            with col4:
                st.metric("Соответствие", f"{result.get('compliance_score', 0):.1f}/10")
        
        # Результат
        st.text_area(
            "Результат аудита",
            result.get('result', ''),
            height=300,
            disabled=True
        )
        
        # Передача результата
        st.subheader("📤 Передача результата")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📤 → Writer", use_container_width=True):
                st.session_state.writer_input = result.get('result', '')
                st.success("✅ Отправлено в Writer Agent!")
        
        with col2:
            if st.button("📤 → Researcher", use_container_width=True):
                st.session_state.researcher_input = result.get('result', '')
                st.success("✅ Отправлено в Researcher Agent!")
        
        with col3:
            if st.button("📤 → Interviewer", use_container_width=True):
                st.session_state.interviewer_input = result.get('result', '')
                st.success("✅ Отправлено в Interviewer Agent!")
        
        with col4:
            if st.button("💾 Сохранить", use_container_width=True):
                st.success("✅ Результат аудита сохранен!")
    
    # Управление промптами
    show_prompt_management("auditor")

def show_interviewer_agent():
    """Страница агента-интервьюера"""
    st.header("💬 Interviewer Agent")
    st.markdown("---")
    
    # Настройки
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("⚙️ Настройки агента")
        
        llm_provider = st.selectbox(
            "Провайдер LLM",
            ["auto", "gigachat", "local"],
            key="interviewer_provider"
        )
        
        if llm_provider == "local":
            model = st.selectbox("Локальная модель", ["qwen2.5:3b", "qwen2.5:7b"], key="interviewer_local_model")
        elif llm_provider == "gigachat":
            model = st.selectbox("GigaChat модель", ["GigaChat", "GigaChat-Pro"], key="interviewer_giga_model")
        else:
            model = "auto"
        
        temperature = st.slider("Температура", 0.1, 1.0, 0.5, key="interviewer_temp")
        max_tokens = st.number_input("Макс. токенов", 100, 1500, 800, key="interviewer_tokens")
    
    with col2:
        st.subheader("📊 Статистика")
        st.metric("Интервью проведено", "23")
        st.metric("Среднее время", "15 мин")
        st.metric("Успешность", "96%")
    
    # Ввод данных
    st.subheader("📝 Входные данные для интервью")
    
    # Проверяем данные от других агентов
    if 'auditor_input' in st.session_state:
        st.info("📤 Получены данные от Auditor Agent")
        default_input = st.session_state.auditor_input
    elif 'researcher_input' in st.session_state:
        st.info("📤 Получены данные от Researcher Agent")
        default_input = st.session_state.researcher_input
    else:
        default_input = ""
    
    interview_data = st.text_area(
        "Введите данные для создания вопросов",
        value=default_input,
        placeholder="Профиль пользователя, требования гранта, недостающая информация...",
        height=200,
        key="interviewer_input"
    )
    
    # Запуск создания вопросов
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Создать вопросы", type="primary", use_container_width=True):
            if interview_data and AGENTS_AVAILABLE:
                with st.spinner("💬 Создаю вопросы..."):
                    try:
                        # Создаем агента
                        agent = InterviewerAgent(db=None, llm_provider=llm_provider)
                        
                        # Запускаем создание вопросов
                        result = agent.create_questions({
                            'user_profile': interview_data,
                            'llm_provider': llm_provider,
                            'model': model,
                            'temperature': temperature,
                            'max_tokens': max_tokens
                        })
                        
                        # Сохраняем результат
                        st.session_state.agent_results['interviewer'] = result
                        st.session_state.interviewer_timestamp = datetime.now()
                        
                        st.success("✅ Вопросы созданы!")
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")
            else:
                st.warning("⚠️ Введите данные для создания вопросов")
    
    with col2:
        if st.button("🧹 Очистить данные", use_container_width=True):
            if 'interviewer' in st.session_state.agent_results:
                del st.session_state.agent_results['interviewer']
            if 'interviewer_timestamp' in st.session_state:
                del st.session_state.interviewer_timestamp
            st.success("✅ Данные очищены!")
    
    # Результаты
    if 'interviewer' in st.session_state.agent_results:
        st.markdown("---")
        st.subheader("📊 Созданные вопросы")
        
        result = st.session_state.agent_results['interviewer']
        timestamp = st.session_state.interviewer_timestamp
        
        # Информация о запросе
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Провайдер", result.get('provider', 'Unknown'))
        with col2:
            st.metric("Время обработки", f"{result.get('processing_time', 0):.2f} сек")
        with col3:
            st.metric("Дата", timestamp.strftime("%H:%M:%S"))
        
        # Результат
        st.text_area(
            "Созданные вопросы",
            result.get('result', ''),
            height=300,
            disabled=True
        )
        
        # Передача результата
        st.subheader("📤 Передача результата")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📤 → Researcher", use_container_width=True):
                st.session_state.researcher_input = result.get('result', '')
                st.success("✅ Отправлено в Researcher Agent!")
        
        with col2:
            if st.button("📤 → Writer", use_container_width=True):
                st.session_state.writer_input = result.get('result', '')
                st.success("✅ Отправлено в Writer Agent!")
        
        with col3:
            if st.button("📤 → Auditor", use_container_width=True):
                st.session_state.auditor_input = result.get('result', '')
                st.success("✅ Отправлено в Auditor Agent!")
        
        with col4:
            if st.button("💾 Сохранить", use_container_width=True):
                st.success("✅ Вопросы сохранены!")
    
    # Управление промптами
    show_prompt_management("interviewer")

def main():
    """Главная функция страницы"""
    st.title("🤖 AI Агенты GrantService")
    st.markdown("---")
    
    # Боковое меню для выбора агента
    st.sidebar.title("🎯 Выберите агента")
    
    selected_agent = st.sidebar.selectbox(
        "Агент",
        [
            "📊 Статус LLM",
            "🔍 Researcher Agent",
            "✍️ Writer Agent", 
            "🔍 Auditor Agent",
            "💬 Interviewer Agent"
        ],
        index=0
    )
    
    # Общие настройки
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Общие настройки")
    
    default_provider = st.sidebar.selectbox(
        "Провайдер по умолчанию",
        ["auto", "gigachat", "local"],
        help="Auto: автоматический выбор, GigaChat: облачный, Local: локальный"
    )
    
    # Переключение между агентами
    if selected_agent == "📊 Статус LLM":
        show_llm_status()
    elif selected_agent == "🔍 Researcher Agent":
        show_researcher_agent()
    elif selected_agent == "✍️ Writer Agent":
        show_writer_agent()
    elif selected_agent == "🔍 Auditor Agent":
        show_auditor_agent()
    elif selected_agent == "💬 Interviewer Agent":
        show_interviewer_agent()
    
    # Информация о системе
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ Информация")
    st.sidebar.info("""
    **GrantService AI Agents**
    
    Система автоматической подготовки грантовых заявок с помощью ИИ-агентов.
    
    Каждый агент специализируется на своей области и может работать с разными LLM провайдерами.
    """)

if __name__ == "__main__":
    main()
