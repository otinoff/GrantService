#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование Perplexity сервиса
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from services.perplexity_service import PerplexityService
sys.path.append('/var/GrantService/agents')
from researcher_agent import ResearcherAgent
from data.database import GrantServiceDatabase as Database

def test_perplexity_service():
    """Тестирование Perplexity сервиса"""
    print("🧪 Тестирование Perplexity сервиса")
    print("=" * 50)
    
    try:
        # Инициализируем сервис
        perplexity = PerplexityService()
        print("✅ Perplexity сервис инициализирован")
        
        # Тест 1: Поиск грантов
        print("\n🔍 Тест 1: Поиск грантов...")
        result = perplexity.search_grants(
            query="гранты для малого бизнеса",
            region="Кемеровская область",
            budget_range="до 500 000 рублей"
        )
        
        if result.get('status') == 'success':
            print("✅ Поиск грантов выполнен успешно")
            print(f"📝 Найдено источников: {len(result.get('sources', []))}")
            print(f"❓ Связанных вопросов: {len(result.get('related_questions', []))}")
            
            # Показываем часть результата
            grants_info = result.get('grants_info', '')
            if grants_info:
                print(f"📄 Результат (первые 300 символов): {grants_info[:300]}...")
        else:
            print(f"❌ Ошибка поиска: {result.get('error')}")
        
        # Тест 2: Связанные гранты
        print("\n🔗 Тест 2: Поиск связанных грантов...")
        related_result = perplexity.get_related_grants("малый бизнес")
        
        if related_result.get('status') == 'success':
            print("✅ Связанные гранты найдены")
            print(f"📝 Источников: {len(related_result.get('sources', []))}")
        else:
            print(f"❌ Ошибка поиска связанных грантов: {related_result.get('error')}")
        
        # Тест 3: Анализ гранта
        print("\n📊 Тест 3: Анализ гранта...")
        grant_info = "Грант на развитие малого бизнеса, размер до 500 000 рублей"
        analysis_result = perplexity.get_grant_analysis(grant_info)
        
        if analysis_result.get('status') == 'success':
            print("✅ Анализ гранта выполнен")
            analysis = analysis_result.get('analysis', '')
            if analysis:
                print(f"📄 Анализ (первые 200 символов): {analysis[:200]}...")
        else:
            print(f"❌ Ошибка анализа: {analysis_result.get('error')}")
        
        print("\n" + "=" * 50)
        print("🎉 Тестирование Perplexity сервиса завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

def test_researcher_agent():
    """Тестирование Researcher Agent с Perplexity"""
    print("\n🤖 Тестирование Researcher Agent")
    print("=" * 50)
    
    try:
        # Инициализируем базу данных и агента
        db = Database()
        researcher = ResearcherAgent(db)
        print("✅ Researcher Agent инициализирован")
        
        # Тестируем подключение к Perplexity
        print("\n🔗 Тест подключения к Perplexity...")
        connection_test = researcher.test_perplexity_connection()
        
        if connection_test.get('status') == 'success':
            print("✅ Подключение к Perplexity работает")
            usage = connection_test.get('usage', {})
            if usage:
                print(f"📊 Использование токенов: {usage}")
        else:
            print(f"❌ Ошибка подключения: {connection_test.get('message')}")
        
        # Тестируем обработку данных
        print("\n📝 Тест обработки данных...")
        test_data = {
            'user_answers': {
                'project_type': 'малый бизнес',
                'region': 'Кемеровская область',
                'budget': 'до 500 000 рублей',
                'experience': '3-5 лет'
            },
            'project_description': 'Развитие малого бизнеса в регионе'
        }
        
        result = researcher.process(test_data)
        
        if result.get('status') == 'success':
            print("✅ Обработка данных выполнена успешно")
            print(f"🔍 Поисковый запрос: {result.get('search_query', '')}")
            print(f"📄 Найдено грантов: {len(result.get('found_grants', ''))} символов")
            print(f"🔗 Связанных грантов: {len(result.get('related_grants', ''))} символов")
            print(f"📚 Источников: {len(result.get('sources', []))}")
        else:
            print(f"❌ Ошибка обработки: {result.get('message')}")
        
        print("\n" + "=" * 50)
        print("🎉 Тестирование Researcher Agent завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_perplexity_service()
    test_researcher_agent() 