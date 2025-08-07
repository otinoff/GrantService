#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование агента-исследователя с промптами из БД
"""

import sys
import os
sys.path.append('/var/GrantService')

from data.database import GrantServiceDatabase
from services.perplexity_service import PerplexityService

def test_researcher_with_db():
    """Тестируем агента-исследователя с промптами из БД"""
    
    # Инициализируем БД и сервис
    db = GrantServiceDatabase()
    perplexity_service = PerplexityService()
    
    print("🔍 Тестирование агента-исследователя с промптами из БД")
    print("=" * 60)
    
    # Получаем промпты исследователя из БД
    researcher_prompts = db.get_agent_prompts('researcher')
    
    if not researcher_prompts:
        print("❌ Промпты исследователя не найдены в БД")
        return
    
    print(f"✅ Найдено {len(researcher_prompts)} промптов исследователя")
    print()
    
    # Тестовые данные пользователя (имитация интервью)
    test_user_data = {
        'project_name': 'Цифровое образование для сельских школ',
        'project_description': 'Создание онлайн-платформы для обучения школьников в сельской местности с использованием современных технологий',
        'target_audience': 'Школьники 5-11 классов в сельских районах',
        'region': 'Кемеровская область',
        'budget': '5000000',
        'duration': '24 месяца'
    }
    
    print("📋 Тестовые данные проекта:")
    for key, value in test_user_data.items():
        print(f"  {key}: {value}")
    print()
    
    # Фильтруем только task промпты
    task_prompts = [p for p in researcher_prompts if p['prompt_type'] == 'task']
    
    print(f"🎯 Найдено {len(task_prompts)} task промптов для выполнения:")
    for i, prompt in enumerate(task_prompts, 1):
        print(f"  {i}. {prompt['prompt_name']}")
    print()
    
    # Выполняем каждый task промпт
    for i, prompt in enumerate(task_prompts, 1):
        print(f"🚀 Выполняем промпт {i}: {prompt['prompt_name']}")
        print("-" * 40)
        
        # Строим запрос на основе промпта и данных пользователя
        query = f"""
{prompt['prompt_content']}

Контекст проекта:
- Название: {test_user_data['project_name']}
- Описание: {test_user_data['project_description']}
- Целевая аудитория: {test_user_data['target_audience']}
- Регион: {test_user_data['region']}
- Бюджет: {test_user_data['budget']} руб.
- Срок: {test_user_data['duration']}

Проведи исследование по данному проекту.
"""
        
        print(f"📝 Запрос к Perplexity:")
        print(query[:200] + "..." if len(query) > 200 else query)
        print()
        
        try:
            # Выполняем запрос к Perplexity
            response = perplexity_service.search_grants(query)
            
            print(f"✅ Ответ получен ({len(response)} символов)")
            print("📄 Ответ:")
            print(response[:500] + "..." if len(response) > 500 else response)
            print()
            
            # Логируем в БД
            log_data = {
                'user_id': 999,  # тестовый пользователь
                'session_id': 999,  # тестовая сессия
                'query_text': query,
                'perplexity_response': response,
                'sources': 'Perplexity API',
                'usage_stats': 'test_query',
                'cost': 0.01,  # примерная стоимость
                'status': 'success',
                'error_message': None
            }
            
            db.log_researcher_query(**log_data)
            print(f"💾 Запрос залогирован в БД")
            
        except Exception as e:
            print(f"❌ Ошибка при выполнении запроса: {e}")
            
            # Логируем ошибку
            log_data = {
                'user_id': 999,
                'session_id': 999,
                'query_text': query,
                'perplexity_response': None,
                'sources': None,
                'usage_stats': 'error',
                'cost': 0,
                'status': 'error',
                'error_message': str(e)
            }
            
            db.log_researcher_query(**log_data)
        
        print("=" * 60)
        print()
    
    print("🎉 Тестирование завершено!")
    print("📊 Проверьте логи в админ-панели в разделе 'Аналитика исследователя'")

if __name__ == "__main__":
    test_researcher_with_db() 