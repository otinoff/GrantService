 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование получения настроек модели через API
"""

import sys
import os
sys.path.append('/var/GrantService')

from services.perplexity_service import PerplexityService

def test_model_settings():
    """Тестирование получения настроек модели"""
    print("🧪 Тестирование получения настроек модели через API")
    print("=" * 60)
    
    # Инициализируем сервис
    perplexity_service = PerplexityService()
    
    # Получаем настройки модели
    print("📡 Получаем настройки модели 'sonar'...")
    model_settings = perplexity_service.get_model_settings("sonar")
    
    print("\n✅ Настройки получены успешно!")
    print("=" * 60)
    
    # Выводим детальную информацию
    print(f"🤖 Модель: {model_settings['model_name']}")
    print(f"📋 Тип: {model_settings['model_type']}")
    print(f"🧠 Контекст: {model_settings['context_size']}")
    print(f"🔢 Max tokens: {model_settings['max_tokens']}")
    print(f"🌡️ Temperature: {model_settings['temperature']}")
    print(f"⏱️ Timeout: {model_settings['timeout']} секунд")
    print(f"🔄 Retry attempts: {model_settings['retry_attempts']}")
    print(f"🔍 Search mode: {model_settings['search_mode']}")
    print(f"📊 Context size: {model_settings['web_search_options']['search_context_size']}")
    
    print("\n💰 Стоимость:")
    pricing = model_settings['pricing']
    print(f"  - Вход: {pricing['input_tokens']}")
    print(f"  - Выход: {pricing['output_tokens']}")
    print(f"  - Поиск: {pricing['search_queries']}")
    print(f"  - Статус: {pricing['status']}")
    
    print("\n⚡ Производительность:")
    performance = model_settings['performance']
    print(f"  - Запросы/мин: {performance['requests_per_minute']}")
    print(f"  - Поиск в интернете: {'✅' if performance['web_search'] else '❌'}")
    print(f"  - Источники: {'✅' if performance['sources'] else '❌'}")
    print(f"  - Цитаты: {'✅' if performance['citations'] else '❌'}")
    
    print("\n🎯 Возможности:")
    for capability in model_settings['capabilities']:
        print(f"  - ✅ {capability}")
    
    print(f"\n🕒 Последнее обновление: {model_settings['last_updated']}")
    
    if 'note' in model_settings:
        print(f"⚠️ Примечание: {model_settings['note']}")
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")
    
    return model_settings

def test_search_with_dynamic_settings():
    """Тестирование поиска с динамическими настройками"""
    print("\n🔍 Тестирование поиска с динамическими настройками")
    print("=" * 60)
    
    perplexity_service = PerplexityService()
    
    # Тестовый запрос
    test_query = "гранты для образования в России"
    
    print(f"📝 Тестовый запрос: {test_query}")
    print("🚀 Выполняем поиск...")
    
    try:
        result = perplexity_service.search_grants(test_query)
        
        if "error" in result:
            print(f"❌ Ошибка: {result['error']}")
        else:
            print("✅ Поиск выполнен успешно!")
            print(f"📄 Длина ответа: {len(result.get('grants_info', ''))} символов")
            print(f"🔗 Источники: {len(result.get('sources', []))}")
            print(f"❓ Связанные вопросы: {len(result.get('related_questions', []))}")
            
            # Показываем часть ответа
            grants_info = result.get('grants_info', '')
            if grants_info:
                print(f"\n📋 Часть ответа:")
                print(grants_info[:300] + "..." if len(grants_info) > 300 else grants_info)
        
    except Exception as e:
        print(f"❌ Ошибка при поиске: {e}")

if __name__ == "__main__":
    # Тестируем получение настроек
    settings = test_model_settings()
    
    # Тестируем поиск с динамическими настройками
    test_search_with_dynamic_settings()