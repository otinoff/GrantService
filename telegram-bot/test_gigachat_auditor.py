#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест интеграции GigaChat с AuditorAgent
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from services.gigachat_service import GigaChatService
sys.path.append('/var/GrantService/agents')
from auditor_agent import AuditorAgent
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gigachat_service():
    """Тест прямого обращения к GigaChat"""
    print("🧪 Тестируем GigaChat Service")
    print("=" * 50)
    
    service = GigaChatService()
    
    # Простой тест заявки
    test_application = """
    НАЗВАНИЕ: Разработка мобильного приложения для изучения языков
    
    РЕЗЮМЕ: Создание инновационного мобильного приложения для изучения иностранных языков 
    с использованием ИИ и геймификации.
    
    ПРОБЛЕМА: Существующие приложения для изучения языков не персонализированы и скучны.
    
    РЕШЕНИЕ: Разработать ИИ-ассистента, который адаптирует обучение под каждого пользователя.
    
    БЮДЖЕТ: 500,000 рублей на разработку и тестирование.
    """
    
    result = service.analyze_grant_application(test_application)
    
    if result.get('status') == 'success':
        print("✅ GigaChat ответил успешно!")
        print(f"📝 Анализ: {result.get('analysis')[:200]}...")
    else:
        print(f"❌ Ошибка: {result.get('message')}")
    
    return result

def test_auditor_agent():
    """Тест AuditorAgent с GigaChat"""
    print("\n🤖 Тестируем AuditorAgent с GigaChat")
    print("=" * 50)
    
    # Мок базы данных
    class MockDB:
        def get_agent_prompts(self, agent_type):
            return {"system_prompt": "Ты эксперт по грантам"}
    
    auditor = AuditorAgent(MockDB())
    
    # Тестовые данные
    test_data = {
        'application': {
            'title': 'Разработка ИИ-ассистента для образования',
            'summary': 'Создание умного помощника для студентов',
            'problem': 'Студенты нуждаются в персонализированной помощи',
            'solution': 'ИИ-ассистент с адаптивным обучением',
            'budget': '750,000 рублей',
            'timeline': '12 месяцев'
        },
        'user_answers': {
            'experience': 'high',
            'budget': '500000-1000000',
            'region': 'Кемеровская область'
        },
        'selected_grant': {
            'requirements': 'Инновационные проекты в сфере образования',
            'amount': '1,000,000 рублей',
            'deadline': '2025-12-31'
        }
    }
    
    try:
        result = auditor.process(test_data)
        
        if result.get('status') == 'success':
            print("✅ AuditorAgent отработал успешно!")
            
            # Проверяем наличие GigaChat анализа
            gigachat_analysis = result.get('analysis', {}).get('gigachat_analysis', {})
            
            if gigachat_analysis.get('status') == 'success':
                print("🤖 GigaChat анализ прошел успешно!")
                print(f"📊 Оценка: {gigachat_analysis.get('score', 'N/A')}")
                print(f"📝 Рекомендации: {len(gigachat_analysis.get('recommendations', []))} штук")
            else:
                print(f"⚠️ GigaChat анализ не удался: {gigachat_analysis.get('message', 'N/A')}")
            
            print(f"🎯 Общая оценка: {result.get('overall_score', 'N/A')}")
            print(f"🏆 Статус готовности: {result.get('readiness_status', 'N/A')}")
            
        else:
            print(f"❌ Ошибка AuditorAgent: {result.get('message')}")
            
        return result
        
    except Exception as e:
        print(f"💥 Исключение в тесте: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Запуск тестов GigaChat интеграции")
    print("🕐 Это может занять несколько секунд...")
    
    # Тест 1: Прямое обращение к GigaChat
    gigachat_result = test_gigachat_service()
    
    # Тест 2: Полный AuditorAgent с GigaChat
    auditor_result = test_auditor_agent()
    
    print("\n" + "="*50)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"🤖 GigaChat Service: {'✅ Работает' if gigachat_result and gigachat_result.get('status') == 'success' else '❌ Не работает'}")
    print(f"🕵️ AuditorAgent: {'✅ Работает' if auditor_result and auditor_result.get('status') == 'success' else '❌ Не работает'}")
    
    if gigachat_result and gigachat_result.get('status') == 'success':
        print("\n🎉 GigaChat успешно интегрирован с AuditorAgent!")
        print("📋 Теперь можно использовать ИИ-анализ заявок на гранты")
    else:
        print("\n🔧 Требуется доработка интеграции")
