 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование логирования Researcher Agent
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

sys.path.append('/var/GrantService/agents')
from researcher_agent import ResearcherAgent
from data.database import GrantServiceDatabase as Database

def test_researcher_logging():
    """Тестирование логирования Researcher Agent"""
    print("🧪 Тестирование логирования Researcher Agent")
    print("=" * 50)
    
    try:
        # Инициализируем базу данных и агента
        db = Database()
        researcher = ResearcherAgent(db)
        print("✅ Researcher Agent инициализирован")
        
        # Тестовые данные пользователя
        test_data = {
            'user_answers': {
                'project_type': 'малый бизнес',
                'region': 'Кемеровская область',
                'budget': 'до 500 000 рублей',
                'experience': '3-5 лет',
                'team_size': '5-10 человек'
            },
            'project_description': 'Развитие малого бизнеса в регионе через внедрение современных технологий',
            'user_id': 1,
            'session_id': 1
        }
        
        print("\n📝 Выполняем исследование с логированием...")
        result = researcher.process(test_data)
        
        if result.get('status') == 'success':
            print("✅ Исследование выполнено успешно")
            print(f"📊 Выполнено запросов: {result.get('queries_count', 0)}")
            print(f"💰 Общая стоимость: ${result.get('total_cost', 0):.4f}")
            print(f"👤 Пользователь ID: {result.get('user_id', 0)}")
            print(f"🆔 Сессия ID: {result.get('session_id', 0)}")
            
            # Показываем результаты
            results = result.get('results', [])
            for i, res in enumerate(results, 1):
                print(f"\n📋 Результат {i}: {res['prompt_name']}")
                print(f"🔍 Запрос: {res['query'][:100]}...")
                print(f"📄 Ответ: {res['result'][:200]}...")
                print(f"💰 Стоимость: ${res['cost']:.4f}")
                print(f"📚 Источников: {len(res['sources'])}")
            
            # Проверяем логи в базе
            print("\n📊 Проверяем логи в базе данных...")
            logs = db.get_researcher_logs(user_id=1, limit=10)
            
            if logs:
                print(f"✅ Найдено {len(logs)} записей в логах")
                for log in logs:
                    print(f"📝 Лог ID {log['id']}: {log['status']} - ${log['cost']:.4f}")
            else:
                print("❌ Логи не найдены")
            
            # Проверяем статистику
            print("\n📈 Проверяем статистику...")
            stats = db.get_researcher_statistics(30)
            print(f"📊 Всего запросов: {stats.get('total_queries', 0)}")
            print(f"✅ Успешных: {stats.get('successful_queries', 0)}")
            print(f"💰 Общая стоимость: ${stats.get('total_cost', 0):.4f}")
            print(f"📈 Процент успеха: {stats.get('success_rate', 0):.1f}%")
            
        else:
            print(f"❌ Ошибка исследования: {result.get('message')}")
        
        print("\n" + "=" * 50)
        print("🎉 Тестирование логирования завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_researcher_logging()