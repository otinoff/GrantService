#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест синхронизации с Perplexity API
"""

import sys
import os
sys.path.append('/var/GrantService')

from services.perplexity_service import PerplexityService

def test_sync_perplexity():
    """Тест синхронизации с Perplexity API"""
    print("🔄 ТЕСТ СИНХРОНИЗАЦИИ С PERPLEXITY API")
    print("=" * 50)
    
    # Инициализируем сервис
    perplexity_service = PerplexityService()
    
    # 1. Получаем данные от Perplexity API
    print("\n📡 Получаем данные от Perplexity API...")
    api_data = perplexity_service.get_perplexity_api_usage()
    
    if "error" in api_data:
        print(f"❌ Ошибка API: {api_data['error']}")
        return False
    
    print("✅ Данные получены от API")
    print(f"📊 Структура данных: {list(api_data.keys())}")
    
    # 2. Получаем наши данные из БД
    print("\n🗄️ Получаем данные из нашей БД...")
    db_stats = perplexity_service.get_account_statistics()
    
    if "error" in db_stats:
        print(f"❌ Ошибка БД: {db_stats['error']}")
        return False
    
    print("✅ Данные получены из БД")
    
    # 3. Синхронизация
    print("\n🔄 Выполняем синхронизацию...")
    sync_result = perplexity_service.sync_with_perplexity_api()
    
    if "error" in sync_result:
        print(f"❌ Ошибка синхронизации: {sync_result['error']}")
        return False
    
    print("✅ Синхронизация завершена")
    
    # 4. Показываем сравнение
    print("\n📊 СРАВНЕНИЕ ДАННЫХ:")
    print("-" * 50)
    
    # Данные из скринов Perplexity
    if 'manual_data' in api_data:
        manual = api_data['manual_data']
        print("🔍 ДАННЫЕ ИЗ СКРИНОВ PERPLEXITY:")
        print(f"  API Requests: {manual['api_requests']['total']}")
        print(f"  Input Tokens: {manual['input_tokens']['total']:,}")
        print(f"  Output Tokens: {manual['output_tokens']['total']:,}")
        print(f"  Reasoning Tokens: {manual['reasoning_tokens']['reasoning-pro']:,}")
        
        print("\n📊 ДЕТАЛИЗАЦИЯ ПО МОДЕЛЯМ:")
        print("  API Requests:")
        for model, count in manual['api_requests'].items():
            if model != 'total':
                print(f"    {model}: {count}")
        
        print("  Input Tokens:")
        for model, count in manual['input_tokens'].items():
            if model != 'total':
                print(f"    {model}: {count:,}")
        
        print("  Output Tokens:")
        for model, count in manual['output_tokens'].items():
            if model != 'total':
                print(f"    {model}: {count:,}")
    
    # БД данные
    db_usage = db_stats['usage_stats']
    print(f"\n🗄️ НАША БД:")
    print(f"  Requests: {db_usage['total_queries']}")
    print(f"  Input Tokens: {db_usage['total_input_tokens']:,}")
    print(f"  Output Tokens: {db_usage['total_output_tokens']:,}")
    
    # Сравнение
    if 'manual_data' in api_data:
        manual = api_data['manual_data']
        print(f"\n📈 СРАВНЕНИЕ:")
        print(f"  Requests: {db_usage['total_queries']} / {manual['api_requests']['total']} ({db_usage['total_queries']/manual['api_requests']['total']*100:.1f}%)")
        print(f"  Input Tokens: {db_usage['total_input_tokens']:,} / {manual['input_tokens']['total']:,} ({db_usage['total_input_tokens']/manual['input_tokens']['total']*100:.1f}%)")
        print(f"  Output Tokens: {db_usage['total_output_tokens']:,} / {manual['output_tokens']['total']:,} ({db_usage['total_output_tokens']/manual['output_tokens']['total']*100:.1f}%)")
    
    return True

if __name__ == "__main__":
    print("🚀 Запуск теста синхронизации с Perplexity API")
    
    response = input("\nПродолжить тест? (y/N): ")
    if response.lower() in ['y', 'yes', 'да']:
        test_sync_perplexity()
    else:
        print("❌ Тест отменен") 