#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование получения статистики аккаунта из базы данных
"""

import sys
import os
sys.path.append('/var/GrantService')

from services.perplexity_service import PerplexityService

def test_account_statistics():
    """Тестирование получения статистики аккаунта"""
    print("🧪 Тестирование получения статистики аккаунта")
    print("=" * 60)
    
    # Инициализируем сервис
    perplexity_service = PerplexityService()
    
    # Получаем статистику аккаунта
    print("📡 Получаем статистику аккаунта из базы данных...")
    account_stats = perplexity_service.get_account_statistics()
    
    print("\n✅ Статистика получена успешно!")
    print("=" * 60)
    
    # Выводим информацию об аккаунте
    account_info = account_stats['account_info']
    print(f"🎯 Текущий тариф: {account_info['current_tier']}")
    print(f"💰 Потрачено: ${account_info['total_spent']:.2f}")
    
    tier_progress = account_info['tier_progress']
    print(f"📈 Прогресс: {tier_progress['progress_percent']:.1f}%")
    if tier_progress['next_tier']:
        print(f"🎯 До {tier_progress['next_tier']}: ${tier_progress['remaining_to_next']:.2f}")
    
    # Выводим статистику использования
    usage_stats = account_stats['usage_stats']
    print(f"\n📊 Статистика использования:")
    print(f"  - Всего запросов: {usage_stats['total_queries']}")
    print(f"  - Успешных: {usage_stats['successful_queries']}")
    print(f"  - Ошибок: {usage_stats['failed_queries']}")
    print(f"  - Успешность: {usage_stats['success_rate']:.1f}%")
    print(f"  - Общие расходы: ${usage_stats['total_cost']:.2f}")
    print(f"  - Входные токены: {usage_stats['total_input_tokens']:,}")
    print(f"  - Выходные токены: {usage_stats['total_output_tokens']:,}")
    print(f"  - Поисковые запросы: {usage_stats['total_search_queries']}")
    
    # Выводим лимиты для текущего тарифа
    rate_limits = account_stats['rate_limits']
    print(f"\n🚦 Лимиты запросов (за минуту):")
    print(f"  - sonar: {rate_limits['sonar']}")
    print(f"  - sonar-pro: {rate_limits['sonar-pro']}")
    print(f"  - sonar-reasoning: {rate_limits['sonar-reasoning']}")
    print(f"  - sonar-reasoning-pro: {rate_limits['sonar-reasoning-pro']}")
    print(f"  - sonar-deep-research: {rate_limits['sonar-deep-research']}")
    
    # Выводим статистику по дням
    daily_usage = account_stats['daily_usage']
    if daily_usage:
        print(f"\n📅 Статистика по дням (последние 5 дней):")
        for date, stats in daily_usage[:5]:
            print(f"  - {date}: {stats['queries']} запросов, ${stats['cost']:.2f}, {stats['tokens']} токенов")
    
    print(f"\n🕒 Последнее обновление: {account_stats['last_updated']}")
    
    if 'note' in account_stats:
        print(f"⚠️ Примечание: {account_stats['note']}")
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")
    
    return account_stats

def test_model_settings_with_account():
    """Тестирование настроек модели вместе со статистикой аккаунта"""
    print("\n🔧 Тестирование настроек модели + статистика аккаунта")
    print("=" * 60)
    
    perplexity_service = PerplexityService()
    
    # Получаем настройки модели
    print("📡 Получаем настройки модели...")
    model_settings = perplexity_service.get_model_settings("sonar")
    
    # Получаем статистику аккаунта
    print("📊 Получаем статистику аккаунта...")
    account_stats = perplexity_service.get_account_statistics()
    
    print("\n✅ Данные получены!")
    print("=" * 60)
    
    # Сравниваем настройки с лимитами
    current_tier = account_stats['account_info']['current_tier']
    rate_limits = account_stats['rate_limits']
    
    print(f"🤖 Модель: {model_settings['model_name']}")
    print(f"🎯 Текущий тариф: {current_tier}")
    print(f"🚦 Лимит для sonar: {rate_limits['sonar']} запросов/мин")
    print(f"💰 Стоимость: {model_settings['pricing']['input_tokens']}")
    
    # Проверяем совместимость
    if rate_limits['sonar'] >= 50:
        print("✅ Лимиты достаточны для нормальной работы")
    else:
        print("⚠️ Лимиты могут быть ограничивающими")
    
    print("\n" + "=" * 60)
    print("✅ Сравнение завершено!")

if __name__ == "__main__":
    # Тестируем статистику аккаунта
    stats = test_account_statistics()
    
    # Тестируем настройки модели вместе со статистикой
    test_model_settings_with_account() 