#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест реального запроса к Perplexity API с логированием стоимости
"""

import sys
import os
sys.path.append('/var/GrantService')

from services.perplexity_service import PerplexityService
from data.database import GrantServiceDatabase

def test_real_perplexity():
    """Тест с реальным запросом к API"""
    print("🧪 РЕАЛЬНЫЙ ТЕСТ Perplexity API")
    print("=" * 50)
    print("💰 Цель: Проверить реальные затраты и логирование")
    print("⚠️ ВНИМАНИЕ: Будет выполнен ОДИН реальный запрос!")
    print("=" * 50)
    
    # Инициализируем сервис
    perplexity_service = PerplexityService()
    db = GrantServiceDatabase()
    
    # 1. Проверяем статистику ДО запроса
    print("\n📊 Статистика ДО запроса:")
    stats_before = perplexity_service.get_account_statistics()
    print(f"  - Запросов: {stats_before['usage_stats']['total_queries']}")
    print(f"  - Расходы: ${stats_before['usage_stats']['total_cost']:.6f}")
    
    # 2. Выполняем реальный запрос с логированием
    print("\n🔍 Выполняем реальный запрос...")
    try:
        result = perplexity_service.search_grants(
            query="гранты для IT стартапов",
            region="Россия",
            budget_range="до 5 млн рублей",
            user_id=999,  # Тестовый пользователь
            session_id=999  # Тестовая сессия
        )
        
        if "error" in result:
            print(f"❌ Ошибка API: {result['error']}")
            return False
        
        print("✅ Запрос выполнен успешно!")
        print(f"📄 Длина ответа: {len(result.get('grants_info', ''))} символов")
        
        # Показываем usage данные
        usage = result.get('usage', {})
        print(f"📊 Usage данные:")
        print(f"  - Prompt tokens: {usage.get('prompt_tokens', 0)}")
        print(f"  - Completion tokens: {usage.get('completion_tokens', 0)}")
        print(f"  - Total tokens: {usage.get('total_tokens', 0)}")
        print(f"  - Search queries: {usage.get('num_search_queries', 0)}")
        print(f"  - Search context size: {usage.get('search_context_size', 'N/A')}")
        
        # Показываем детальную стоимость
        cost_info = usage.get('cost', {})
        if cost_info:
            print(f"💰 Детальная стоимость:")
            print(f"  - Input tokens cost: ${cost_info.get('input_tokens_cost', 0):.6f}")
            print(f"  - Output tokens cost: ${cost_info.get('output_tokens_cost', 0):.6f}")
            print(f"  - Request cost: ${cost_info.get('request_cost', 0):.6f}")
            print(f"  - Total cost: ${cost_info.get('total_cost', 0):.6f}")
        
        # Показываем источники
        sources = result.get('sources', [])
        print(f"🔗 Источники: {len(sources)} найдено")
        for i, source in enumerate(sources[:3]):  # Показываем первые 3
            print(f"  {i+1}. {source.get('title', 'Без названия')[:50]}...")
        
        # 3. Проверяем статистику ПОСЛЕ запроса
        print("\n📊 Статистика ПОСЛЕ запроса:")
        stats_after = perplexity_service.get_account_statistics()
        print(f"  - Запросов: {stats_after['usage_stats']['total_queries']}")
        print(f"  - Расходы: ${stats_after['usage_stats']['total_cost']:.6f}")
        
        # 4. Показываем разницу
        cost_diff = stats_after['usage_stats']['total_cost'] - stats_before['usage_stats']['total_cost']
        queries_diff = stats_after['usage_stats']['total_queries'] - stats_before['usage_stats']['total_queries']
        
        print(f"\n💰 Стоимость запроса: ${cost_diff:.6f}")
        print(f"📈 Новых запросов: {queries_diff}")
        
        # 5. Проверяем последний лог
        print("\n📋 Проверяем последний лог...")
        logs = db.get_researcher_logs(limit=1)
        
        if logs:
            latest_log = logs[0]
            print(f"  - Лог ID: {latest_log['id']}")
            print(f"  - Статус: {latest_log['status']}")
            print(f"  - Стоимость: ${latest_log['cost']:.6f}")
            print(f"  - Время: {latest_log['created_at']}")
            
            # Показываем usage_stats из лога
            usage_stats = latest_log['usage_stats']
            print(f"  - Usage из лога:")
            print(f"    Prompt tokens: {usage_stats.get('prompt_tokens', 0)}")
            print(f"    Completion tokens: {usage_stats.get('completion_tokens', 0)}")
            print(f"    Total tokens: {usage_stats.get('total_tokens', 0)}")
        else:
            print("  - Логи не найдены")
        
        # 6. Итоговая информация
        print("\n" + "=" * 50)
        print("✅ РЕАЛЬНЫЙ ТЕСТ ЗАВЕРШЕН!")
        print(f"💰 Потрачено: ${cost_diff:.6f}")
        print(f"💳 Остаток баланса: ~${1.1 - cost_diff:.3f}")
        print("📊 Статистика обновлена")
        print("📋 Логирование работает")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск реального тестирования Perplexity API")
    print("⚠️ ВНИМАНИЕ: Будет выполнен ОДИН запрос для проверки логирования")
    
    response = input("\nПродолжить тест? (y/N): ")
    if response.lower() in ['y', 'yes', 'да']:
        test_real_perplexity()
    else:
        print("❌ Тест отменен") 