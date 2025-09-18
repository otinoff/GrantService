#!/usr/bin/env python3
"""
Тестирование Writer Agent с детальным логированием
"""
import asyncio
import logging
import sys

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Добавляем пути
sys.path.append('/var/GrantService')
sys.path.append('/var/GrantService/agents')

from agents.writer_agent import WriterAgent
from data.database import GrantServiceDatabase

async def test_writer():
    """Тестирование Writer Agent"""
    print("="*60)
    print("🧪 ТЕСТИРОВАНИЕ WRITER AGENT С GIGACHAT")
    print("="*60)
    
    try:
        # Инициализация
        print("\n1️⃣ Инициализация базы данных...")
        db = GrantServiceDatabase()
        print("✅ База данных подключена")
        
        print("\n2️⃣ Создание Writer Agent...")
        agent = WriterAgent(db=db, llm_provider="gigachat")
        print("✅ Writer Agent создан")
        
        # Тестовые данные
        test_data = {
            'user_answers': {
                'project_name': 'ИИ-Ассистент для грантов',
                'description': 'Платформа автоматизации грантовых заявок',
                'problem': 'Сложность подготовки грантовых заявок',
                'solution': 'Автоматизация с помощью ИИ',
                'budget': '500,000 рублей',
                'timeline': '6 месяцев',
                'team': 'Команда из 3 разработчиков',
                'impact': 'Повышение успешности заявок на 40%'
            },
            'research_data': {
                'relevant_grants': ['Фонд развития ИТ', 'Инновационный фонд'],
                'success_factors': ['Инновационность', 'Социальная значимость']
            },
            'selected_grant': {
                'name': 'Фонд развития ИТ',
                'amount': '500,000 рублей',
                'deadline': '2025-12-31'
            }
        }
        
        print("\n3️⃣ Запуск генерации заявки...")
        print("📝 Входные данные:")
        print(f"   - Название проекта: {test_data['user_answers']['project_name']}")
        print(f"   - Бюджет: {test_data['user_answers']['budget']}")
        print(f"   - Срок: {test_data['user_answers']['timeline']}")
        
        # Запускаем генерацию
        result = await agent.write_application_async(test_data)
        
        print("\n4️⃣ Результаты:")
        print(f"   - Статус: {result.get('status')}")
        print(f"   - Провайдер: {result.get('provider_used', 'Unknown')}")
        print(f"   - Оценка качества: {result.get('quality_score', 0)}/10")
        
        if result.get('status') == 'success':
            print("\n📄 СГЕНЕРИРОВАННАЯ ЗАЯВКА:")
            print("-"*50)
            application = result.get('application', {})
            for section, content in application.items():
                print(f"\n### {section.upper()}")
                print(content[:200] + "..." if len(str(content)) > 200 else content)
        else:
            print(f"\n❌ Ошибка: {result.get('message')}")
        
        # Показываем debug log от UnifiedLLMClient
        if hasattr(agent, 'llm_client') and hasattr(agent.llm_client, 'get_debug_log'):
            debug_log = agent.llm_client.get_debug_log()
            if debug_log:
                print("\n5️⃣ DEBUG LOG от UnifiedLLMClient:")
                print("-"*50)
                for log_entry in debug_log:
                    print(log_entry)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск теста Writer Agent...")
    asyncio.run(test_writer())
