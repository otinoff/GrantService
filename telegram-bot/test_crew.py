#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование полной команды CrewAI
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from data.database import GrantServiceDatabase as Database
from crew.grant_crew import GrantCrew

def test_crew():
    """Тестирование команды агентов"""
    print("🤖 Тестирование команды CrewAI")
    print("=" * 50)
    
    try:
        # Инициализируем базу данных
        db = Database()
        print("✅ База данных подключена")
        
        # Создаем команду
        print("\n🚀 Создание команды агентов...")
        crew = GrantCrew(db)
        
        if crew.crew:
            print("✅ Команда CrewAI создана успешно")
            
            # Проверяем статус агентов
            print("\n📊 Статус агентов:")
            status = crew.get_agent_status()
            for agent, info in status.items():
                if agent != 'crew_available':
                    print(f"  {agent}: {'✅' if info['available'] else '❌'} (промптов: {info['prompts_count']})")
            print(f"  CrewAI: {'✅' if status['crew_available'] else '❌'}")
            
            # Тестируем простой процесс
            print("\n🧪 Тестирование простого процесса...")
            test_data = {
                'project_type': 'малый бизнес',
                'region': 'Кемеровская область',
                'budget': '500 000',
                'experience': '3-5 лет'
            }
            
            result = crew.process_application(test_data, "Тестовый проект")
            
            if result.get('status') == 'success':
                print("✅ Процесс выполнен успешно")
                print(f"📝 Результат: {len(str(result.get('result', {})))} символов")
            else:
                print(f"❌ Ошибка процесса: {result.get('message')}")
        else:
            print("❌ Ошибка создания команды")
        
        print("\n" + "=" * 50)
        print("🎉 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crew() 