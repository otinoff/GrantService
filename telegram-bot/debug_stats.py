 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладка статистики Perplexity API
"""

import sys
import os
sys.path.append('/var/GrantService')

from services.perplexity_service import PerplexityService
from data.database import GrantServiceDatabase

def debug_stats():
    """Отладка статистики"""
    print("🔍 ОТЛАДКА СТАТИСТИКИ")
    print("=" * 40)
    
    # Инициализируем сервис
    perplexity_service = PerplexityService()
    db = GrantServiceDatabase()
    
    # 1. Проверяем логи напрямую
    print("\n📋 Проверяем логи напрямую...")
    try:
        logs = db.get_researcher_logs(limit=2)
        print(f"  Тип logs: {type(logs)}")
        print(f"  Количество: {len(logs)}")
        
        if logs:
            first_log = logs[0]
            print(f"  Тип первого лога: {type(first_log)}")
            print(f"  Ключи: {list(first_log.keys())}")
            
            # Проверяем usage_stats
            usage_stats = first_log.get('usage_stats')
            print(f"  Тип usage_stats: {type(usage_stats)}")
            print(f"  Значение usage_stats: {usage_stats}")
            
    except Exception as e:
        print(f"  ❌ Ошибка логов: {e}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")
    
    # 2. Тестируем статистику
    print("\n📊 Тестируем статистику...")
    try:
        stats = perplexity_service.get_account_statistics()
        print(f"  Тип stats: {type(stats)}")
        print(f"  Ключи: {list(stats.keys()) if isinstance(stats, dict) else 'НЕ СЛОВАРЬ'}")
        
        if isinstance(stats, dict):
            usage_stats = stats.get('usage_stats')
            print(f"  Тип usage_stats: {type(usage_stats)}")
            print(f"  Значение: {usage_stats}")
        
    except Exception as e:
        print(f"  ❌ Ошибка статистики: {e}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_stats()