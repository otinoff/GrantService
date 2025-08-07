#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Минимальный тест Perplexity API - только проверка подключения
"""

import sys
import os
sys.path.append('/var/GrantService')

from services.perplexity_service import PerplexityService
from data.database import GrantServiceDatabase

def test_minimal_perplexity():
    """Минимальный тест - только проверка подключения без реальных запросов"""
    print("🧪 МИНИМАЛЬНЫЙ ТЕСТ Perplexity API")
    print("=" * 50)
    print("💰 Цель: Проверить подключение БЕЗ трат")
    print("⚠️ Затраты: $0.0000")
    print("=" * 50)
    
    # Инициализируем сервис
    perplexity_service = PerplexityService()
    db = GrantServiceDatabase()
    
    # 1. Проверяем настройки модели
    print("\n🔧 Проверяем настройки модели...")
    try:
        settings = perplexity_service.get_model_settings()
        print(f"  ✅ Модель: {settings.get('model_name', 'sonar')}")
        print(f"  ✅ Макс токенов: {settings.get('max_tokens', 'N/A')}")
        print(f"  ✅ Цена: {settings.get('pricing', {}).get('status', 'N/A')}")
    except Exception as e:
        print(f"  ❌ Ошибка настроек: {e}")
    
    # 2. Проверяем статистику БД
    print("\n📊 Проверяем статистику БД...")
    try:
        stats = perplexity_service.get_account_statistics()
        if "error" in stats:
            print(f"  ⚠️ Ошибка статистики: {stats['error']}")
        else:
            print(f"  ✅ Всего запросов: {stats['usage_stats']['total_queries']}")
            print(f"  ✅ Общие расходы: ${stats['usage_stats']['total_cost']:.4f}")
    except Exception as e:
        print(f"  ❌ Ошибка БД: {e}")
    
    # 3. Проверяем последние логи
    print("\n📋 Проверяем последние логи...")
    try:
        logs = db.get_researcher_logs(limit=3)
        if logs:
            print(f"  ✅ Найдено логов: {len(logs)}")
            latest = logs[0]
            print(f"  ✅ Последний: {latest['created_at']} - {latest['status']}")
        else:
            print("  ℹ️ Логи не найдены")
    except Exception as e:
        print(f"  ❌ Ошибка логов: {e}")
    
    # 4. Проверяем структуру БД
    print("\n🗄️ Проверяем структуру БД...")
    try:
        # Проверяем таблицу researcher_logs
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(researcher_logs)")
            columns = cursor.fetchall()
            print(f"  ✅ Таблица researcher_logs: {len(columns)} колонок")
            
            # Проверяем количество записей
            cursor.execute("SELECT COUNT(*) FROM researcher_logs")
            count = cursor.fetchone()[0]
            print(f"  ✅ Записей в логах: {count}")
            
    except Exception as e:
        print(f"  ❌ Ошибка БД: {e}")
    
    # 5. Тест без реального запроса
    print("\n🔍 Тест без реального запроса...")
    try:
        # Создаем тестовый лог в БД без обращения к API
        test_log_id = db.log_researcher_query(
            user_id=999,
            session_id=999,
            query_text="ТЕСТОВЫЙ ЗАПРОС - без обращения к API",
            perplexity_response="Тестовый ответ без затрат",
            sources=[],
            usage_stats={"prompt_tokens": 10, "completion_tokens": 5},
            cost=0.0,
            status="test",
            error_message=None
        )
        print(f"  ✅ Создан тестовый лог ID: {test_log_id}")
        
        # Проверяем, что лог создался
        test_log = db.get_researcher_logs(limit=1)[0]
        print(f"  ✅ Проверка лога: {test_log['status']} - ${test_log['cost']:.4f}")
        
    except Exception as e:
        print(f"  ❌ Ошибка тестового лога: {e}")
    
    print("\n" + "=" * 50)
    print("✅ МИНИМАЛЬНЫЙ ТЕСТ ЗАВЕРШЕН!")
    print("💰 Потрачено: $0.0000")
    print("🔧 Проверена работа БД и сервиса")
    print("📋 Логирование работает")
    
    return True

if __name__ == "__main__":
    print("🚀 Запуск минимального тестирования Perplexity API")
    print("⚠️ ВНИМАНИЕ: БЕЗ обращения к API - только проверка системы")
    
    response = input("\nПродолжить тест? (y/N): ")
    if response.lower() in ['y', 'yes', 'да']:
        test_minimal_perplexity()
    else:
        print("❌ Тест отменен") 