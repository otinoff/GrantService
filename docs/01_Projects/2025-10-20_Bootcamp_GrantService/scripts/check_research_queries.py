#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка запросов из Researcher V2
"""
import sys
import os
sys.path.insert(0, r'C:\SnowWhiteAI\GrantService')
sys.path.insert(0, r'C:\SnowWhiteAI\GrantService\web-admin')

# Настройка локальной БД
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'
os.environ['PGDATABASE'] = 'grantservice'
os.environ['PGUSER'] = 'postgres'
os.environ['PGPASSWORD'] = 'root'

import json
import psycopg2

def main():
    # Подключаемся к БД
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='grantservice',
        user='postgres',
        password='root'
    )

    cursor = conn.cursor()

    cursor.execute('''
        SELECT research_results
        FROM researcher_research
        WHERE anketa_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    ''', ('#AN-20251012-Natalia_bruzzzz-001',))

    row = cursor.fetchone()
    if not row:
        print("❌ Research results не найдены")
        conn.close()
        return

    # row[0] уже dict если PostgreSQL вернул JSONB
    research = row[0] if isinstance(row[0], dict) else json.loads(row[0])

    print("="*80)
    print("RESEARCH QUERIES ANALYSIS")
    print("="*80)

    # Проверить query во всех блоках
    for block_name in ['block1_statistics', 'block2_geography', 'block3_goals']:
        if block_name in research:
            block = research[block_name]
            print(f'\n=== {block_name} ===')

            if 'query' in block:
                query = block['query']
                print(f'\n📝 Query:')
                print(query[:800])
                if len(query) > 800:
                    print(f'\n... (всего {len(query)} символов)')
            else:
                print('❌ NO QUERY FIELD!')

            if 'raw_results' in block:
                print(f'\n📊 Raw results length: {len(str(block["raw_results"]))} chars')
        else:
            print(f'\n=== {block_name} ===')
            print(f'❌ Block not found!')

    print("\n" + "="*80)

    conn.close()

if __name__ == "__main__":
    main()
