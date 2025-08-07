#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Очистка и обновление данных Perplexity API
"""

import sys
import os
import json
from datetime import datetime

# Добавляем путь к модулям
sys.path.append('/var/GrantService')

from data.database import GrantServiceDatabase

def clean_and_update_data():
    """Очистка базы и добавление актуальных данных"""
    print("🧹 Очистка и обновление данных Perplexity API")
    print("=" * 50)
    
    # Инициализируем базу данных
    db = GrantServiceDatabase()
    
    # Очищаем старые записи миграции
    print("🗑️ Очистка старых записей миграции...")
    try:
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM researcher_logs 
                WHERE query_text LIKE 'Миграция:%'
            ''')
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"✅ Удалено {deleted_count} старых записей миграции")
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
    
    # Актуальные данные из скрина (3 августа 2025)
    current_data = {
        'credit_balance': 0.747174,
        'api_requests': {
            'sonar_medium': 9,
            'sonar_low': 66,
            'reasoning_pro': 20,
            'sonar_pro_low': 1
        },
        'input_tokens': {
            'sonar': 1788,
            'reasoning_pro': 2546,
            'sonar_pro': 5,
            'total': 4339
        },
        'output_tokens': {
            'sonar': 9833,
            'reasoning_pro': 169065,
            'sonar_pro': 50,
            'total': 178948
        },
        'reasoning_tokens': {
            'reasoning_pro': 5853115
        },
        'total_cost': 0.133939
    }
    
    # Создаем записи в базе данных для каждого типа модели
    models_data = [
        {
            'user_id': 1,
            'session_id': 1,
            'query_text': 'Актуальные данные: sonar medium запросы',
            'perplexity_response': 'Актуальные данные из Perplexity dashboard',
            'sources': [],
            'usage_stats': {
                'model': 'sonar',
                'quality': 'medium',
                'input_tokens': current_data['input_tokens']['sonar'],
                'output_tokens': current_data['output_tokens']['sonar'],
                'search_queries': 0,
                'reasoning_tokens': 0,
                'requests_count': current_data['api_requests']['sonar_medium']
            },
            'cost': current_data['total_cost'] * (current_data['api_requests']['sonar_medium'] / 96),  # Пропорционально
            'status': 'success',
            'error_message': None,
            'credit_balance': current_data['credit_balance']
        },
        {
            'user_id': 1,
            'session_id': 1,
            'query_text': 'Актуальные данные: sonar low запросы',
            'perplexity_response': 'Актуальные данные из Perplexity dashboard',
            'sources': [],
            'usage_stats': {
                'model': 'sonar',
                'quality': 'low',
                'input_tokens': current_data['input_tokens']['sonar'],
                'output_tokens': current_data['output_tokens']['sonar'],
                'search_queries': 0,
                'reasoning_tokens': 0,
                'requests_count': current_data['api_requests']['sonar_low']
            },
            'cost': current_data['total_cost'] * (current_data['api_requests']['sonar_low'] / 96),
            'status': 'success',
            'error_message': None,
            'credit_balance': current_data['credit_balance']
        },
        {
            'user_id': 1,
            'session_id': 1,
            'query_text': 'Актуальные данные: reasoning-pro запросы',
            'perplexity_response': 'Актуальные данные из Perplexity dashboard',
            'sources': [],
            'usage_stats': {
                'model': 'reasoning-pro',
                'quality': 'none',
                'input_tokens': current_data['input_tokens']['reasoning_pro'],
                'output_tokens': current_data['output_tokens']['reasoning_pro'],
                'search_queries': 0,
                'reasoning_tokens': current_data['reasoning_tokens']['reasoning_pro'],
                'requests_count': current_data['api_requests']['reasoning_pro']
            },
            'cost': current_data['total_cost'] * (current_data['api_requests']['reasoning_pro'] / 96),
            'status': 'success',
            'error_message': None,
            'credit_balance': current_data['credit_balance']
        },
        {
            'user_id': 1,
            'session_id': 1,
            'query_text': 'Актуальные данные: sonar-pro low запросы',
            'perplexity_response': 'Актуальные данные из Perplexity dashboard',
            'sources': [],
            'usage_stats': {
                'model': 'sonar-pro',
                'quality': 'low',
                'input_tokens': current_data['input_tokens']['sonar_pro'],
                'output_tokens': current_data['output_tokens']['sonar_pro'],
                'search_queries': 0,
                'reasoning_tokens': 0,
                'requests_count': current_data['api_requests']['sonar_pro_low']
            },
            'cost': current_data['total_cost'] * (current_data['api_requests']['sonar_pro_low'] / 96),
            'status': 'success',
            'error_message': None,
            'credit_balance': current_data['credit_balance']
        }
    ]
    
    # Добавляем записи в базу данных
    print("📝 Добавление актуальных записей в базу данных...")
    
    for i, data in enumerate(models_data, 1):
        try:
            log_id = db.log_researcher_query(
                user_id=data['user_id'],
                session_id=data['session_id'],
                query_text=data['query_text'],
                perplexity_response=data['perplexity_response'],
                sources=data['sources'],
                usage_stats=data['usage_stats'],
                cost=data['cost'],
                status=data['status'],
                error_message=data['error_message'],
                credit_balance=data['credit_balance']
            )
            print(f"✅ Запись {i} добавлена с ID: {log_id}")
        except Exception as e:
            print(f"❌ Ошибка добавления записи {i}: {e}")
    
    # Проверяем результат
    print("\n📊 Проверка результата обновления:")
    logs = db.get_researcher_logs(limit=10)
    
    if logs:
        print(f"Найдено {len(logs)} записей:")
        for log in logs:
            usage_stats = log.get('usage_stats', {})
            model = usage_stats.get('model', 'unknown')
            quality = usage_stats.get('quality', 'unknown')
            requests = usage_stats.get('requests_count', 0)
            balance = log.get('credit_balance', 0.0)
            
            try:
                balance_float = float(balance) if balance else 0.0
                print(f"  • {model} ({quality}): {requests} запросов, баланс: ${balance_float:.6f}")
            except (ValueError, TypeError):
                print(f"  • {model} ({quality}): {requests} запросов, баланс: N/A")
    else:
        print("Записи не найдены")
    
    print("\n✅ Очистка и обновление завершены!")

if __name__ == "__main__":
    clean_and_update_data() 