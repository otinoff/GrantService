 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновление стоимости в существующих логах Perplexity API
"""

import sys
import os
sys.path.append('/var/GrantService')

from data.database import GrantServiceDatabase
from services.perplexity_service import PerplexityService

def update_existing_costs():
    """Обновление стоимости в существующих логах"""
    print("🔄 ОБНОВЛЕНИЕ СТОИМОСТИ В ЛОГАХ")
    print("=" * 50)
    
    db = GrantServiceDatabase()
    perplexity_service = PerplexityService()
    
    # Получаем все логи
    logs = db.get_researcher_logs(limit=1000)
    print(f"📋 Найдено логов: {len(logs)}")
    
    updated_count = 0
    total_cost = 0.0
    
    for log in logs:
        log_id = log['id']
        current_cost = log['cost']
        usage_stats = log['usage_stats']
        
        # Рассчитываем правильную стоимость
        correct_cost = perplexity_service._calculate_cost(usage_stats)
        
        if abs(current_cost - correct_cost) > 0.000001:  # Если стоимость отличается
            print(f"  🔄 Лог {log_id}: ${current_cost:.6f} → ${correct_cost:.6f}")
            
            # Обновляем стоимость в БД
            try:
                with db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE researcher_logs SET cost = ? WHERE id = ?",
                        (correct_cost, log_id)
                    )
                    conn.commit()
                
                updated_count += 1
                total_cost += correct_cost
                
            except Exception as e:
                print(f"    ❌ Ошибка обновления: {e}")
        else:
            total_cost += current_cost
    
    print(f"\n✅ Обновлено логов: {updated_count}")
    print(f"💰 Общая стоимость: ${total_cost:.6f}")
    
    # Проверяем статистику после обновления
    print("\n📊 Проверяем статистику после обновления...")
    stats = perplexity_service.get_account_statistics()
    print(f"  - Запросов: {stats['usage_stats']['total_queries']}")
    print(f"  - Расходы: ${stats['usage_stats']['total_cost']:.6f}")
    
    return updated_count

if __name__ == "__main__":
    print("🚀 Запуск обновления стоимости в логах")
    
    response = input("\nПродолжить обновление? (y/N): ")
    if response.lower() in ['y', 'yes', 'да']:
        update_existing_costs()
    else:
        print("❌ Обновление отменено")