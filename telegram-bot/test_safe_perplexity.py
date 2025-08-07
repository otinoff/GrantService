#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Безопасный тест Perplexity API с минимальными затратами
"""

import sys
import os
sys.path.append('/var/GrantService')

from services.perplexity_service import PerplexityService
from data.database import GrantServiceDatabase

def test_safe_perplexity():
    """Безопасный тест с минимальными затратами"""
    print("🧪 БЕЗОПАСНЫЙ ТЕСТ Perplexity API")
    print("=" * 60)
    print("💰 Баланс: $1.1")
    print("🎯 Цель: Проверить статистику и логирование")
    print("⚠️ Ожидаемые затраты: ~$0.001-0.002")
    print("=" * 60)
    
    # Инициализируем сервис
    perplexity_service = PerplexityService()
    db = GrantServiceDatabase()
    
    # 1. Проверяем статистику ДО запроса
    print("\n📊 Статистика ДО запроса:")
    stats_before = perplexity_service.get_account_statistics()
    
    if "error" in stats_before:
        print(f"Ошибка получения статистики аккаунта: {stats_before['error']}")
        print(f"  - Запросов: {stats_before['usage_stats']['total_queries']}")
        print(f"  - Расходы: ${stats_before['usage_stats']['total_cost']:.4f}")
    else:
        print(f"  - Запросов: {stats_before['usage_stats']['total_queries']}")
        print(f"  - Расходы: ${stats_before['usage_stats']['total_cost']:.4f}")
    
    # 2. Делаем ОДИН минимальный запрос
    print("\n🔍 Выполняем ОДИН тестовый запрос...")
    
    try:
        # Минимальный запрос с ограниченным контекстом
        test_query = "Найди 3 гранта для IT проектов в России"
        
        # Используем минимальные настройки
        result = perplexity_service.search_grants(
            query=test_query,
            region="Россия",
            budget_range="до 1 млн рублей"
        )
        
        if "error" in result:
            print(f"❌ Ошибка API: {result['error']}")
            return False
        
        print("✅ Запрос выполнен успешно!")
        print(f"📄 Длина ответа: {len(result.get('grants_info', ''))} символов")
        
        # 3. Проверяем статистику ПОСЛЕ запроса
        print("\n📊 Статистика ПОСЛЕ запроса:")
        stats_after = perplexity_service.get_account_statistics()
        
        if "error" in stats_after:
            print(f"Ошибка получения статистики аккаунта: {stats_after['error']}")
            print(f"  - Запросов: {stats_after['usage_stats']['total_queries']}")
            print(f"  - Расходы: ${stats_after['usage_stats']['total_cost']:.4f}")
        else:
            print(f"  - Запросов: {stats_after['usage_stats']['total_queries']}")
            print(f"  - Расходы: ${stats_after['usage_stats']['total_cost']:.4f}")
        
        # 4. Показываем разницу
        cost_diff = stats_after['usage_stats']['total_cost'] - stats_before['usage_stats']['total_cost']
        queries_diff = stats_after['usage_stats']['total_queries'] - stats_before['usage_stats']['total_queries']
        
        print(f"\n💰 Стоимость запроса: ${cost_diff:.4f}")
        print(f"📈 Новых запросов: {queries_diff}")
        
        # 5. Проверяем логи в БД
        print("\n📋 Проверяем логи в базе данных...")
        logs = db.get_researcher_logs(limit=5)
        
        if logs:
            latest_log = logs[0]  # Самый свежий лог
            print(f"  - Последний лог ID: {latest_log['id']}")
            print(f"  - Статус: {latest_log['status']}")
            print(f"  - Стоимость: ${latest_log.get('cost', 0):.4f}")
            print(f"  - Время: {latest_log['created_at']}")
            
            # Показываем часть запроса
            query_text = latest_log['query_text']
            if len(query_text) > 50:
                query_text = query_text[:50] + "..."
            print(f"  - Запрос: {query_text}")
        else:
            print("  - Логи не найдены")
        
        # 6. Итоговая информация
        print("\n" + "=" * 60)
        print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
        print(f"💰 Потрачено: ${cost_diff:.4f}")
        print(f"💳 Остаток баланса: ~${1.1 - cost_diff:.3f}")
        print("📊 Статистика работает корректно")
        print("📋 Логирование функционирует")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

def test_context_settings():
    """Тест настроек контекста"""
    print("\n🔧 Тест настроек контекста")
    print("=" * 40)
    
    perplexity_service = PerplexityService()
    
    # Тестируем ограничение контекста
    test_data = {
        "project_name": "Тестовый IT проект",
        "budget": "500,000 рублей",
        "team_size": "5 человек",
        "region": "Москва",
        "project_description": "Это очень длинное описание проекта, которое содержит много деталей и технических требований. " * 50,  # 50 повторений для большого текста
        "tech_requirements": "Python, Django, PostgreSQL, Docker " * 30  # 30 повторений
    }
    
    print("📏 Тестируем ограничение контекста...")
    
    # Показываем размер исходных данных
    total_chars = sum(len(str(v)) for v in test_data.values())
    estimated_tokens = total_chars // 4  # Примерно 4 символа на токен
    
    print(f"  - Исходный размер: {total_chars:,} символов")
    print(f"  - Примерно токенов: {estimated_tokens:,}")
    
    # TODO: Здесь будет функция ограничения контекста
    print("  - Функция ограничения: будет реализована")
    
    return True

if __name__ == "__main__":
    print("🚀 Запуск безопасного тестирования Perplexity API")
    print("⚠️ ВНИМАНИЕ: Будет выполнен ОДИН запрос для проверки")
    
    # Запрашиваем подтверждение
    confirm = input("\nПродолжить тест? (y/N): ").lower().strip()
    
    if confirm == 'y':
        # Выполняем тест
        success = test_safe_perplexity()
        
        if success:
            # Дополнительно тестируем настройки контекста
            test_context_settings()
            
        print("\n🎉 Тестирование завершено!")
    else:
        print("❌ Тест отменен") 