#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест отображения баланса Perplexity API
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append('/var/GrantService')

from services.perplexity_service import PerplexityService
from data.database import get_researcher_logs, add_researcher_log

def test_balance_display():
    """Тест отображения баланса"""
    print("🔍 Тестирование отображения баланса Perplexity API")
    print("=" * 50)
    
    # Инициализируем сервис
    perplexity_service = PerplexityService()
    
    # Получаем комбинированную статистику
    print("📊 Получение комбинированной статистики...")
    combined_stats = perplexity_service.get_combined_statistics()
    
    account_info = combined_stats.get('account_info', {})
    usage_stats = combined_stats.get('usage_stats', {})
    
    print(f"💰 Баланс аккаунта: ${account_info.get('credit_balance', 0.0):.6f} USD")
    print(f"🎯 Текущий уровень: {account_info.get('current_tier', 'Tier 0')}")
    print(f"💸 Потрачено: ${account_info.get('total_spent', 0.0):.2f}")
    
    # Показываем прогресс до следующего тиера
    tier_progress = account_info.get('tier_progress', {})
    if tier_progress.get('next_tier'):
        remaining = tier_progress.get('remaining_to_next', 0.0)
        print(f"📈 До {tier_progress['next_tier']}: ${remaining:.2f}")
    
    print("\n📊 API Requests по моделям:")
    print(f"  • sonar: {usage_stats.get('sonar_low', 0) + usage_stats.get('sonar_medium', 0)}")
    print(f"  • sonar-pro: {usage_stats.get('sonar_pro_low', 0)}")
    print(f"  • reasoning-pro: {usage_stats.get('reasoning_pro', 0)}")
    print(f"  • Всего запросов: {usage_stats.get('total_queries', 0)}")
    
    # Получаем статистику по моделям
    print("\n🔍 Детальная статистика по моделям:")
    model_stats = perplexity_service.get_model_specific_statistics()
    
    for model, data in model_stats.items():
        if model != 'total_requests' and model != 'last_updated':
            print(f"  • {model}:")
            print(f"    - Low: {data.get('low', 0)}")
            print(f"    - Medium: {data.get('medium', 0)}")
            print(f"    - High: {data.get('high', 0)}")
            print(f"    - Total: {data.get('total', 0)}")
    
    print(f"\n🕐 Последнее обновление: {model_stats.get('last_updated', 'N/A')}")
    
    # Проверяем логи в базе данных
    print("\n📋 Проверка логов в базе данных:")
    logs = get_researcher_logs(limit=5)
    
    if logs:
        print(f"Найдено {len(logs)} последних логов:")
        for log in logs:
            try:
                balance = float(log.get('credit_balance', 0.0)) if log.get('credit_balance') else 0.0
                cost = float(log.get('cost', 0.0)) if log.get('cost') else 0.0
                print(f"  • ID: {log.get('id')}, Баланс: ${balance:.6f}, Стоимость: ${cost:.6f}")
            except (ValueError, TypeError):
                print(f"  • ID: {log.get('id')}, Баланс: N/A, Стоимость: N/A")
    else:
        print("Логи не найдены")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    test_balance_display() 