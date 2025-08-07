#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Страница тестирования промптов исследователя (упрощенная версия)
"""

import streamlit as st
import sys
import os
import json
from datetime import datetime

# Добавляем путь к модулям
sys.path.append('/var/GrantService')

from data.database import get_agent_prompts, get_researcher_logs
# Импортируем PerplexityService напрямую
import sys
sys.path.append('/var/GrantService/telegram-bot')
from services.perplexity_service import PerplexityService

# Инициализация
perplexity_service = PerplexityService()

st.set_page_config(
    page_title="🧪 Тестирование промптов",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Тестирование промптов исследователя")
st.markdown("Тестируйте промпты и отправляйте запросы в Perplexity API")

# Получаем промпты из базы данных
@st.cache_data(ttl=300)
def get_researcher_prompts():
    """Получить промпты исследователя"""
    try:
        prompts = get_agent_prompts('researcher')
        return prompts
    except Exception as e:
        st.error(f"Ошибка получения промптов: {e}")
        return []

prompts = get_researcher_prompts()

# Секция 1: Произвольный запрос
st.markdown("---")
st.subheader("📝 Произвольный запрос")

col1, col2 = st.columns([3, 1])

with col1:
    user_query = st.text_area(
        "Введите любой запрос для Perplexity",
        placeholder="Например: Найди гранты для НКО в области образования на 2025 год",
        height=120
    )

with col2:
    st.markdown("**Настройки:**")
    model = st.selectbox(
        "Модель:",
        ["sonar", "sonar-pro", "reasoning-pro"],
        index=0,
        help="sonar - самая экономичная, reasoning-pro - для сложных рассуждений"
    )
    
    st.markdown("**Информация о модели:**")
    if model == "sonar":
        st.info("💰 Экономичная модель\n⚡ Быстрые ответы\n🔍 Поиск в интернете\n💵 $1/1M токенов")
    elif model == "sonar-pro":
        st.info("🧠 Улучшенная модель\n📊 Более детальные ответы\n💰 Средняя стоимость\n💵 $3/1M токенов")
    elif model == "reasoning-pro":
        st.info("🤖 Модель рассуждений\n🧩 Сложная логика\n💸 Высокая стоимость\n💵 $15/1M токенов")

# Кнопка отправки
if st.button("🚀 Отправить в Perplexity", type="primary", disabled=not user_query.strip()):
    if user_query.strip():
        with st.spinner("Отправляем запрос в Perplexity..."):
            try:
                # Отправляем запрос
                result = perplexity_service.search_grants(
                    user_query, 
                    user_id=1, 
                    session_id=1
                )
                
                if result and ('answer' in result or 'grants_info' in result):
                    st.success("✅ Запрос выполнен успешно!")
                    
                    # Показываем результат
                    st.markdown("---")
                    st.subheader("📊 Результат")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("**Ответ:**")
                        answer_text = result.get('answer') or result.get('grants_info', 'Ответ не найден')
                        st.markdown(answer_text)
                        
                        if 'sources' in result and result['sources']:
                            st.markdown("**Источники:**")
                            for i, source in enumerate(result['sources'][:5]):  # Показываем первые 5
                                st.markdown(f"{i+1}. [{source.get('title', 'Без названия')}]({source.get('url', '#')})")
                    
                    with col2:
                        st.markdown("**Статистика запроса:**")
                        if 'usage' in result:
                            usage = result['usage']
                            st.metric("Входные токены", usage.get('input_tokens', 0))
                            st.metric("Выходные токены", usage.get('output_tokens', 0))
                            st.metric("Стоимость", f"${usage.get('cost', 0):.6f}")
                        
                        st.markdown("**Параметры:**")
                        st.markdown(f"- Модель: {model}")
                        st.markdown(f"- Время: {datetime.now().strftime('%H:%M:%S')}")
                
                else:
                    st.error("❌ Ошибка получения ответа от Perplexity")
                    
            except Exception as e:
                st.error(f"❌ Ошибка отправки запроса: {e}")

# Секция 2: История запросов
st.markdown("---")
st.subheader("📈 История запросов")

# Получаем последние логи
try:
    logs = get_researcher_logs(limit=10)
    
    if logs:
        for i, log in enumerate(logs):
            # Основная информация о запросе
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                query_preview = log['query_text'][:50] + "..." if len(log['query_text']) > 50 else log['query_text']
                st.markdown(f"**{query_preview}**")
                st.caption(f"Время: {log['created_at']}")
                
                # Показываем модель если есть
                try:
                    usage_stats_raw = log.get('usage_stats', '{}')
                    if isinstance(usage_stats_raw, dict):
                        usage_stats = usage_stats_raw
                    else:
                        usage_stats = json.loads(usage_stats_raw)
                    model = usage_stats.get('model', 'unknown')
                    st.caption(f"Модель: {model}")
                except:
                    st.caption("Модель: unknown")
            
            with col2:
                st.markdown(f"**Стоимость:** ${log.get('cost', 0):.6f}")
            
            with col3:
                if log.get('status') == 'success':
                    st.success("✅")
                else:
                    st.error("❌")
            
            with col4:
                # Кнопка для просмотра деталей
                if st.button("🔍 Детали", key=f"details_{i}"):
                    st.session_state[f"show_details_{i}"] = not st.session_state.get(f"show_details_{i}", False)
            
            # Показываем детали если кнопка нажата
            if st.session_state.get(f"show_details_{i}", False):
                with st.expander("📋 Детальная информация о запросе", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📤 Отправленный запрос:**")
                        st.code(log['query_text'], language="text")
                        
                        st.markdown("**📊 Статистика использования:**")
                        try:
                            usage_stats_raw = log.get('usage_stats', '{}')
                            if isinstance(usage_stats_raw, dict):
                                usage_stats = usage_stats_raw
                            else:
                                usage_stats = json.loads(usage_stats_raw)
                            st.json(usage_stats)
                        except Exception as e:
                            st.error(f"Ошибка парсинга статистики: {e}")
                    
                    with col2:
                        st.markdown("**📥 Полный ответ API:**")
                        try:
                            response_data = None
                            if log.get('perplexity_response'):
                                response_data = json.loads(log.get('perplexity_response', '{}'))
                            elif log.get('result'):
                                response_data = json.loads(log.get('result', '{}'))
                            else:
                                response_data = {}
                            
                            st.json(response_data)
                        except Exception as e:
                            st.error(f"Ошибка парсинга ответа: {e}")
                        
                        if log.get('error_message'):
                            st.markdown("**❌ Ошибка:**")
                            st.error(log['error_message'])
                    
                    # Показываем источники если есть
                    try:
                        sources_raw = log.get('sources', '[]')
                        if isinstance(sources_raw, list):
                            sources = sources_raw
                        else:
                            sources = json.loads(sources_raw)
                        
                        if sources:
                            st.markdown("**🔗 Источники:**")
                            for j, source in enumerate(sources[:3]):  # Показываем первые 3
                                title = source.get('title', 'Без названия')
                                url = source.get('url', '#')
                                st.markdown(f"{j+1}. [{title}]({url})")
                    except Exception as e:
                        st.error(f"Ошибка парсинга источников: {e}")
    else:
        st.info("📝 История запросов пуста")
        
except Exception as e:
    st.error(f"Ошибка получения истории: {e}")

# Информация о стоимости
st.markdown("---")
st.subheader("💰 Информация о стоимости")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**sonar (экономичная):**")
    st.markdown("- Вход: $1/1M токенов")
    st.markdown("- Выход: $1/1M токенов")
    st.markdown("- Поиск: $5/1K запросов")

with col2:
    st.markdown("**sonar-pro (улучшенная):**")
    st.markdown("- Вход: $1/1M токенов")
    st.markdown("- Выход: $1/1M токенов")
    st.markdown("- Поиск: $5/1K запросов")

with col3:
    st.markdown("**reasoning-pro (рассуждения):**")
    st.markdown("- Вход: $1/1M токенов")
    st.markdown("- Выход: $1/1M токенов")
    st.markdown("- Рассуждения: $12/1K")

st.info("💡 Совет: Используйте модель 'sonar' для экономии средств. Модель 'reasoning-pro' предназначена для сложных логических задач.") 