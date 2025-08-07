#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Импорт данных из скринов Perplexity в нашу БД
"""

import sys
import os
sys.path.append('/var/GrantService')

from data.database import GrantServiceDatabase
from datetime import datetime

def import_screen_data():
    """Импорт данных из скринов Perplexity"""
    print("📥 ИМПОРТ ДАННЫХ ИЗ СКРИНОВ PERPLEXITY")
    print("=" * 50)
    
    db = GrantServiceDatabase()
    
    # Данные из скринов Perplexity (3 августа 2025)
    screen_data = {
        "api_requests": {
            "reasoning-pro, none": 20,
            "sonar-pro, low": 1,
            "sonar, low": 56,
            "sonar, medium": 8
        },
        "input_tokens": {
            "sonar": 1788,
            "reasoning-pro": 2546,
            "sonar-pro": 5
        },
        "output_tokens": {
            "sonar": 9833,
            "reasoning-pro": 169065,
            "sonar-pro": 50
        },
        "reasoning_tokens": {
            "reasoning-pro": 5853115
        }
    }
    
    print("📊 Данные для импорта:")
    print(f"  API Requests: {sum(screen_data['api_requests'].values())}")
    print(f"  Input Tokens: {sum(screen_data['input_tokens'].values()):,}")
    print(f"  Output Tokens: {sum(screen_data['output_tokens'].values()):,}")
    print(f"  Reasoning Tokens: {sum(screen_data['reasoning_tokens'].values()):,}")
    
    # Создаем логи для каждой модели
    models_to_import = [
        ("reasoning-pro", "none", 20, 2546, 169065, 5853115),
        ("sonar-pro", "low", 1, 5, 50, 0),
        ("sonar", "low", 56, 0, 0, 0),  # Данные из sonar, low
        ("sonar", "medium", 8, 1788, 9833, 0)  # Данные из sonar, medium
    ]
    
    imported_count = 0
    
    for model, context, requests, input_tokens, output_tokens, reasoning_tokens in models_to_import:
        for i in range(requests):
            try:
                # Создаем лог для каждого запроса
                log_id = db.log_researcher_query(
                    user_id=999,  # Системный пользователь
                    session_id=999,  # Системная сессия
                    query_text=f"Импортированный запрос {model} ({context}) - {i+1}/{requests}",
                    perplexity_response=f"Данные импортированы из скринов Perplexity: {model}",
                    sources=[],
                    usage_stats={
                        "prompt_tokens": input_tokens // requests if requests > 0 else 0,
                        "completion_tokens": output_tokens // requests if requests > 0 else 0,
                        "total_tokens": (input_tokens + output_tokens) // requests if requests > 0 else 0,
                        "search_context_size": context,
                        "num_search_queries": 0,
                        "reasoning_tokens": reasoning_tokens // requests if requests > 0 else 0
                    },
                    cost=0.0,  # Стоимость будет рассчитана автоматически
                    status="imported",
                    error_message=None
                )
                imported_count += 1
                
            except Exception as e:
                print(f"❌ Ошибка импорта {model}: {e}")
    
    print(f"\n✅ Импортировано записей: {imported_count}")
    
    # Проверяем результат
    print("\n📊 Проверяем результат импорта...")
    stats = db.get_researcher_statistics(days=30)
    print(f"  Всего запросов: {stats['total_queries']}")
    print(f"  Общие расходы: ${stats['total_cost']:.6f}")
    
    return imported_count

if __name__ == "__main__":
    print("🚀 Запуск импорта данных из скринов Perplexity")
    
    response = input("\nПродолжить импорт? (y/N): ")
    if response.lower() in ['y', 'yes', 'да']:
        import_screen_data()
    else:
        print("❌ Импорт отменен") 