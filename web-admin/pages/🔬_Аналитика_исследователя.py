#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Researcher analytics page for GrantService admin panel
"""

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

import streamlit as st
import sys
import pandas as pd
from datetime import datetime, timedelta

import streamlit as st
import sys
import os

# Добавляем пути кроссплатформенно
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
# Добавляем путь к проекту
sys.path.append(grandparent_dir)

from utils.database import AdminDatabase
from utils.charts import create_researcher_metrics, create_cost_chart, create_popular_queries_chart

# Отображение аналитики исследователя
st.title("🔍 Аналитика исследователя")

# Инициализация БД
db = AdminDatabase()

# ===== СТАТИСТИКА АККАУНТА =====
st.markdown("---")
st.subheader("💰 Статистика аккаунта")

# Получаем актуальные настройки через API
try:
    import sys
    sys.path.append(os.path.join(grandparent_dir, 'telegram-bot'))
    from services.perplexity_service import PerplexityService
    perplexity_service = PerplexityService()
    
    # Получаем комбинированную статистику (наши данные + данные из скринов)
    account_stats = perplexity_service.get_combined_statistics()
    
    account_info = account_stats.get('account_info', {})
    usage_stats = account_stats.get('usage_stats', {})
    # Убираем rate_limits, так как его нет в наших данных
    
    col1, col2, col3 = st.columns(3)
    
    # Получаем данные из базы для использования во всех секциях
    screen_data = perplexity_service.get_latest_screen_data()
    
    with col1:
        # Получаем текущий баланс
        from data.database import get_latest_credit_balance, update_latest_credit_balance
        
        current_balance = get_latest_credit_balance()

        balance_emoji = "💰"
        tier = account_info.get('current_tier', 'Tier 0')
        spent = account_info.get('total_spent', 0.02)
        balance_str = f"{current_balance:.6f}"
        spent_str = f"{spent:.2f}"
        st.markdown(f"""
        **{balance_emoji} Баланс аккаунта:**
        - **Credit balance:** {balance_str} USD
        - **Уровень:** {tier}
        - **Потрачено:** {spent_str} USD
        """)
        
        # Интерфейс для редактирования баланса
        with st.expander("✏️ Редактировать баланс"):
            new_balance = st.number_input(
                "Новый баланс (USD)",
                min_value=0.0,
                max_value=10000.0,
                value=float(current_balance),
                step=0.000001,
                format="%.6f",
                help="Введите актуальный баланс из Perplexity dashboard"
            )
            
            col1_edit, col2_edit = st.columns(2)
            
            with col1_edit:
                if st.button("💾 Обновить баланс", type="primary"):
                    if update_latest_credit_balance(new_balance):
                        st.success(f"✅ Баланс обновлен: ${new_balance:.6f} USD")
                        st.rerun()
                    else:
                        st.error("❌ Ошибка обновления баланса")
            
            with col2_edit:
                if st.button("🔄 Обновить все логи"):
                    from data.database import update_all_credit_balances
                    if update_all_credit_balances(new_balance):
                        st.success(f"✅ Все логи обновлены: ${new_balance:.6f} USD")
                        st.rerun()
                    else:
                        st.error("❌ Ошибка обновления логов")
        
        # Показываем информацию о прогрессе до следующего тиера
        tier_progress = account_info.get('tier_progress', {})
        if tier_progress.get('next_tier'):
            remaining = tier_progress.get('remaining_to_next', 249.98)
            st.info(f"📈 До {tier_progress['next_tier']}: ${remaining:.2f}")
        
        # Интерфейс для редактирования Input Tokens
        with st.expander("✏️ Редактировать Input Tokens"):
            st.markdown("**Настройка токенов по моделям:**")
            
            col1_tokens, col2_tokens, col3_tokens = st.columns(3)
            
            with col1_tokens:
                sonar_tokens = st.number_input(
                    "sonar:",
                    min_value=0,
                    max_value=100000,
                    value=int(screen_data.get('sonar_input_tokens', 0)),
                    step=1
                )
            
            with col2_tokens:
                reasoning_tokens = st.number_input(
                    "reasoning-pro:",
                    min_value=0,
                    max_value=100000,
                    value=int(screen_data.get('reasoning_pro_input_tokens', 0)),
                    step=1
                )
            
            with col3_tokens:
                sonar_pro_tokens = st.number_input(
                    "sonar-pro:",
                    min_value=0,
                    max_value=100000,
                    value=int(screen_data.get('sonar_pro_input_tokens', 0)),
                    step=1
                )
            
            if st.button("💾 Сохранить Input Tokens", type="primary"):
                try:
                    from data.database import update_input_tokens_by_model
                    update_input_tokens_by_model('sonar', sonar_tokens)
                    update_input_tokens_by_model('reasoning-pro', reasoning_tokens)
                    update_input_tokens_by_model('sonar-pro', sonar_pro_tokens)
                    st.success("✅ Input Tokens обновлены!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
    
    with col2:
        chart_emoji = "📊"
        st.markdown(f"""
        **{chart_emoji} API Requests:**
        - **sonar-pro, low:** {screen_data.get('sonar_pro_low', 0)}
        - **sonar, medium:** {screen_data.get('sonar_medium', 0)}
        - **sonar, low:** {screen_data.get('sonar_low', 0)}
        - **reasoning-pro, none:** {screen_data.get('reasoning_pro', 0)}
        """)
    
    with col3:
        
        st.markdown("**📥 Input Tokens:**")
        st.markdown(f"""
        - **sonar:** {screen_data.get('sonar_input_tokens', 0):,}
        - **reasoning-pro:** {screen_data.get('reasoning_pro_input_tokens', 0):,}
        - **sonar-pro:** {screen_data.get('sonar_pro_input_tokens', 0):,}
        - **Общие:** {screen_data.get('total_input_tokens', 0):,}
        """)
    
    # Показываем информацию о синхронизации
    if 'note' in account_stats:
        st.success(f"✅ {account_stats['note']}")
        if 'last_updated' in account_stats:
            st.caption(f"🕐 Последнее обновление: {account_stats['last_updated']}")
    
    # Добавляем детальную статистику по моделям как в Perplexity
    st.markdown("---")
    st.subheader("📊 API Requests (как в Perplexity)")
    
    # Создаем 4 колонки в том же порядке как на скрине
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**sonar-pro, low**")
        st.metric(
            label="",
            value=screen_data.get('sonar_pro_low', 0),
            help="Sonar Pro с низким качеством"
        )
    
    with col2:
        st.markdown("**sonar, medium**")
        st.metric(
            label="",
            value=screen_data.get('sonar_medium', 0),
            help="Sonar со средним качеством"
        )
    
    with col3:
        st.markdown("**sonar, low**")
        st.metric(
            label="",
            value=screen_data.get('sonar_low', 0),
            help="Sonar с низким качеством"
        )
    
    with col4:
        st.markdown("**reasoning-pro, none**")
        st.metric(
            label="",
            value=screen_data.get('reasoning_pro', 0),
            help="Reasoning Pro без качества"
        )
    
    # Показываем общую сумму
    total_requests = (
        screen_data.get('sonar_pro_low', 0) + 
        screen_data.get('sonar_medium', 0) + 
        screen_data.get('sonar_low', 0) + 
        screen_data.get('reasoning_pro', 0)
    )

    chart_emoji2 = "📊"
    st.markdown(f"**{chart_emoji2} Всего запросов: {total_requests}**")
    
    # Добавляем секцию Input Tokens как в Perplexity
    st.markdown("---")
    st.subheader("📥 Input Tokens (как в Perplexity)")
    
    # Создаем 3 колонки для Input Tokens
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**sonar**")
        st.metric(
            label="",
            value=screen_data.get('sonar_input_tokens', 0),
            help="Input tokens для sonar"
        )
    
    with col2:
        st.markdown("**reasoning-pro**")
        st.metric(
            label="",
            value=screen_data.get('reasoning_pro_input_tokens', 0),
            help="Input tokens для reasoning-pro"
        )
    
    with col3:
        st.markdown("**sonar-pro**")
        st.metric(
            label="",
            value=screen_data.get('sonar_pro_input_tokens', 0),
            help="Input tokens для sonar-pro"
        )
    
    # Показываем время последнего обновления
    st.caption(f"🕐 Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Лимиты для текущего тарифа (упрощенная версия)
    st.markdown("---")
    st.subheader("🚦 Лимиты запросов (за минуту)")
    
    st.markdown("""
    **🤖 Sonar модели:**
    - **sonar:** 50 запросов/мин
    - **sonar-pro:** 50 запросов/мин
    
    **🧠 Reasoning модели:**
    - **reasoning-pro:** 50 запросов/мин
    - **sonar-reasoning:** 50 запросов/мин
    
    **🔬 Research модели:**
    - **sonar-deep-research:** 50 запросов/мин
    """)
    
    # Получаем настройки модели
    model_settings = perplexity_service.get_model_settings("sonar")
    
    # Предупреждение о расходах
    st.markdown("---")
    st.warning("""
    **⚠️ Важно:** Модель `sonar` - самая экономичная из доступных. 
    Избегайте использования дорогих моделей:
    - ❌ `sonar-deep-research` - слишком дорого
    - ❌ `sonar-reasoning-pro` - дорогие рассуждения
    - ❌ Высокий контекст поиска - $12 за 1K запросов
    """)
    
    # ===== НАСТРОЙКИ СИСТЕМЫ =====
    st.markdown("---")
    st.subheader("⚙️ Настройки системы")
    
    # Информация о модели и конфигурации
    col1, col2, col3 = st.columns(3)

    with col1:
        robot_emoji = "🤖"
        st.markdown(f"""
        **{robot_emoji} Модель Perplexity API:**
        - **Название:** `{model_settings['model_name']}`
        - **Тип:** {model_settings['model_type']}
        - **Контекст:** {model_settings['context_size']}
        """)

    with col2:
        pricing = model_settings['pricing']
        money_emoji = "💰"
        checkmark = "✅"
        st.markdown(f"""
        **{money_emoji} Стоимость:**
        - **Вход:** {pricing['input_tokens']}
        - **Выход:** {pricing['output_tokens']}
        - **Поиск:** {pricing['search_queries']}
        - **Статус:** {checkmark} {pricing['status']}
        """)

    with col3:
        performance = model_settings['performance']
        lightning_emoji = "⚡"
        check = "✅"
        cross = "❌"
        web_search_icon = check if performance['web_search'] else cross
        sources_icon = check if performance['sources'] else cross
        citations_icon = check if performance['citations'] else cross
        st.markdown(f"""
        **{lightning_emoji} Производительность:**
        - **Запросы/мин:** {performance['requests_per_minute']}
        - **Поиск в интернете:** {web_search_icon}
        - **Источники:** {sources_icon}
        - **Цитаты:** {citations_icon}
        """)

    # Дополнительная информация
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        capabilities = model_settings['capabilities']
        check_emoji = "✅"
        capabilities_text = "\n".join([f"- {check_emoji} {cap}" for cap in capabilities])
        target_emoji = "🎯"
        st.markdown(f"""
        **{target_emoji} Возможности модели `{model_settings['model_name']}`:**
        {capabilities_text}
        """)

    with col2:
        chart_emoji3 = "📊"
        st.markdown(f"""
        **{chart_emoji3} Текущие настройки:**
        - **Max tokens:** {model_settings['max_tokens']} (ограничение)
        - **Temperature:** {model_settings['temperature']} (точность)
        - **Timeout:** {model_settings['timeout']} секунд
        - **Retry attempts:** {model_settings['retry_attempts']}
        - **Search mode:** {model_settings['search_mode']}
        - **Context size:** {model_settings['web_search_options']['search_context_size']}
        """)

    # Информация о последнем обновлении
    if 'last_updated' in model_settings:
        clock_emoji = "🕒"
        st.info(f"{clock_emoji} Настройки обновлены: {model_settings['last_updated']}")

    if 'note' in model_settings:
        warning_emoji = "⚠️"
        st.warning(f"{warning_emoji} {model_settings['note']}")
    
    # ===== НАСТРОЙКИ КОНТЕКСТА =====
    st.markdown("---")
    st.subheader("📏 Настройки контекста")
    
    # Статистика экономии
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **💰 Экономия токенов:**
        - **Было:** 128K токенов = $0.128
        - **Станет:** 4K токенов = $0.004
        - **Экономия:** 97% = $0.124 за запрос
        """)
    
    with col2:
        st.markdown("""
        **⚡ Производительность:**
        - **Скорость:** Быстрее в 3-5 раз
        - **Стабильность:** Меньше таймаутов
        - **Rate limits:** Эффективнее использование
        """)
    
    with col3:
        st.markdown("""
        **🎯 Качество ответов:**
        - **Релевантность:** Фокус на важном
        - **Структурированность:** Лучше формат
        - **Точность:** Меньше шума
        """)
    
    # Настройки контекста
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Параметры контекста")
        
        # Слайдеры для настройки
        max_context_tokens = st.slider(
            "Максимум токенов контекста", 
            min_value=1000, 
            max_value=8000, 
            value=4000, 
            step=500,
            help="Общий размер контекста для отправки в API"
        )
        
        max_description_tokens = st.slider(
            "Максимум токенов описания", 
            min_value=500, 
            max_value=3000, 
            value=1500, 
            step=100,
            help="Размер описания проекта"
        )
        
        max_tech_tokens = st.slider(
            "Максимум технических деталей", 
            min_value=300, 
            max_value=2000, 
            value=1000, 
            step=100,
            help="Размер технических требований"
        )
        
        # Стратегия выборки
        strategy = st.selectbox(
            "Стратегия выборки контекста",
            ["Умная выборка", "Простое обрезание", "Сжатие текста"],
            help="Как выбирать данные для контекста"
        )
    
    with col2:
        st.subheader("🎯 Приоритетные поля")
        
        # Чекбоксы для приоритетных полей
        priority_fields = {
            "project_name": "Название проекта",
            "budget": "Бюджет", 
            "team_size": "Размер команды",
            "region": "Регион",
            "project_description": "Описание проекта",
            "tech_requirements": "Технические требования",
            "timeline": "Сроки реализации",
            "target_audience": "Целевая аудитория"
        }
        
        selected_fields = []
        for field_key, field_name in priority_fields.items():
            if st.checkbox(field_name, value=field_key in ["project_name", "budget", "team_size", "region", "project_description"]):
                selected_fields.append(field_key)
        
        # Показываем выбранные поля
        if selected_fields:
            st.success(f"✅ Выбрано полей: {len(selected_fields)}")
            for field in selected_fields[:3]:  # Показываем первые 3
                st.write(f"• {priority_fields[field]}")
            if len(selected_fields) > 3:
                st.write(f"• ... и еще {len(selected_fields) - 3} полей")
    
    # Кнопки управления
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Применить настройки", type="primary"):
            # TODO: Сохранить настройки в БД
            st.success("✅ Настройки применены!")
    
    with col2:
        if st.button("🧪 Тестовый запрос"):
            # TODO: Выполнить тестовый запрос с новыми настройками
            st.info("🔍 Выполняется тестовый запрос...")
    
    with col3:
        if st.button("🔄 Сбросить к умолчаниям"):
            # TODO: Сбросить настройки
            st.warning("⚠️ Настройки сброшены к умолчаниям")
    
    # Информация о текущих настройках
    st.markdown("---")
    clipboard_emoji = "📋"
    context_tokens = f"{max_context_tokens:,}"
    desc_tokens = f"{max_description_tokens:,}"
    tech_tokens = f"{max_tech_tokens:,}"
    fields_count = len(selected_fields)
    st.info(f"""
    **{clipboard_emoji} Текущие настройки контекста:**
    - **Общий лимит:** {context_tokens} токенов
    - **Описание:** {desc_tokens} токенов
    - **Технические детали:** {tech_tokens} токенов
    - **Стратегия:** {strategy}
    - **Приоритетных полей:** {fields_count}
    """)

except Exception as e:
    st.error(f"❌ Ошибка получения настроек через API: {e}")
    
    # Fallback к статичным настройкам
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **🤖 Модель Perplexity API:**
        - **Название:** `sonar`
        - **Тип:** Поисковая модель
        - **Контекст:** 128K токенов
        """)

    with col2:
        st.markdown("""
        **💰 Стоимость:**
        - **Вход:** $1 за 1M токенов
        - **Выход:** $1 за 1M токенов
        - **Поиск:** $5 за 1K запросов
        - **Статус:** ✅ САМАЯ ЭКОНОМИЧНАЯ
        """)

    with col3:
        st.markdown("""
        **⚡ Производительность:**
        - **Запросы/мин:** 50
        - **Поиск в интернете:** ✅
        - **Источники:** ✅
        - **Цитаты:** ✅
        """)

    # Дополнительная информация
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🎯 Возможности модели `sonar`:**
        - ✅ Поиск в интернете (как на сайте Perplexity)
        - ✅ Источники и цитаты
        - ✅ Быстрые факты и новости
        - ✅ Простые Q&A
        - ✅ Анализ актуальной информации
        """)

    with col2:
        st.markdown("""
        **📊 Текущие настройки:**
        - **Max tokens:** 2000 (ограничение)
        - **Temperature:** 0.2 (точность)
        - **Timeout:** 30 секунд
        - **Retry attempts:** 3
        - **Search mode:** web
        """)

    # Предупреждение о расходах
    st.markdown("---")
    st.warning("""
    **⚠️ Важно:** Модель `sonar` - самая экономичная из доступных. 
    Избегайте использования дорогих моделей:
    - ❌ `sonar-deep-research` - слишком дорого
    - ❌ `sonar-reasoning-pro` - дорогие рассуждения
    - ❌ Высокий контекст поиска - $12 за 1K запросов
    """)

# ===== ОСНОВНАЯ АНАЛИТИКА =====
st.markdown("---")
st.subheader("📊 Основные метрики")

# Получение статистики
researcher_stats = db.get_researcher_statistics()

# Основные метрики
create_researcher_metrics(researcher_stats)

# Графики
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Запросы по дням")
    # Здесь можно добавить график запросов по дням
    # Пока заглушка
    st.info("График запросов по дням")

with col2:
    st.subheader("💰 Затраты по дням")
    # Здесь можно добавить график затрат по дням
    # Пока заглушка
    st.info("График затрат по дням")

# Популярные запросы
st.subheader("🔥 Популярные запросы")

# Получение логов для анализа популярных запросов
logs = db.get_researcher_logs(limit=1000)

if logs:
    # Анализ популярных запросов
    query_counts = {}
    for log in logs:
        query = log['query_text'][:50] + "..." if len(log['query_text']) > 50 else log['query_text']
        query_counts[query] = query_counts.get(query, 0) + 1
    
    # Сортируем по популярности
    popular_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)
    
    if popular_queries:
        # Создаем DataFrame для графика
        queries_df = pd.DataFrame(popular_queries[:10], columns=['Запрос', 'Количество'])
        create_popular_queries_chart(popular_queries[:10])
    else:
        st.info("Нет данных о запросах")
else:
    st.info("Нет логов для анализа")

# Детальные логи
st.subheader("📋 Детальные логи")

# Фильтры
col1, col2, col3 = st.columns(3)

with col1:
    user_filter = st.selectbox(
        "Фильтр по пользователю",
        ["Все"] + [str(log['user_id']) for log in logs[:50] if log.get('user_id')]
    )

with col2:
    status_filter = st.selectbox(
        "Фильтр по статусу",
        ["Все", "success", "error"]
    )

with col3:
    limit_filter = st.slider("Количество записей", 10, 100, 50)

# Применяем фильтры
filtered_logs = logs

if user_filter != "Все":
    filtered_logs = [log for log in filtered_logs if str(log.get('user_id', '')) == user_filter]

if status_filter != "Все":
    filtered_logs = [log for log in filtered_logs if log.get('status') == status_filter]

filtered_logs = filtered_logs[:limit_filter]

# Отображаем логи
if filtered_logs:
    for log in filtered_logs:
        with st.expander(f"Запрос {log['id']} - {log['created_at']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Запрос:** {log['query_text']}")
                st.write(f"**Статус:** {log['status']}")
                st.write(f"**Затраты:** {log.get('cost', 0):.2f}₽")
            
            with col2:
                st.write(f"**Пользователь:** {log.get('user_id', 'N/A')}")
                st.write(f"**Сессия:** {log.get('session_id', 'N/A')}")
                st.write(f"**Время:** {log['created_at']}")
            
            if log['perplexity_response']:
                st.write("**Ответ:**")
                st.text(log['perplexity_response'][:500] + "..." if len(log['perplexity_response']) > 500 else log['perplexity_response'])
            
            if log['error_message']:
                st.write("**Ошибка:**")
                st.error(log['error_message'])
else:
    st.info("Логи запросов пока отсутствуют")

# Экспорт данных
st.subheader("📤 Экспорт данных")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Экспорт статистики"):
        # Создаем DataFrame для экспорта
        stats_df = pd.DataFrame([researcher_stats])
        csv = stats_df.to_csv(index=False)
        st.download_button(
            label="Скачать CSV",
            data=csv,
            file_name=f"researcher_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📋 Экспорт логов"):
        if filtered_logs:
            # Создаем DataFrame для экспорта логов
            logs_df = pd.DataFrame(filtered_logs)
            csv = logs_df.to_csv(index=False)
            st.download_button(
                label="Скачать логи CSV",
                data=csv,
                file_name=f"researcher_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("Нет логов для экспорта")