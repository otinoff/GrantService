#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт запуска Writer Agent V2 для session 9
ТОЛЬКО через Claude Code (178.236.17.55:8000)
"""
import sys
import os
import json
import asyncio

# Добавляем пути (используем os.path для кроссплатформенности)
base_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'shared'))
sys.path.insert(0, os.path.join(base_dir, 'agents'))

# Устанавливаем переменные окружения для Claude Code
os.environ['CLAUDE_CODE_API_KEY'] = 'max_subscription_2025oct'
os.environ['CLAUDE_CODE_BASE_URL'] = 'http://178.236.17.55:8000'

# Импорт SQLite wrapper (для локального тестирования)
from sqlite_db_wrapper import SQLiteDBWrapper
import sqlite3

db_wrapper = SQLiteDBWrapper()

# Загружаем данные из session 9
def load_session_data():
    print("\n" + "="*70)
    print("ЗАГРУЗКА ДАННЫХ SESSION 9")
    print("="*70)
    
    # Получаем данные сессии через SQLite
    conn = sqlite3.connect('C:\\SnowWhiteAI\\GrantService\\data\\grantservice.db')
    cursor = conn.cursor()

    # Interview data
    cursor.execute("SELECT interview_data FROM sessions WHERE id = 9")
    interview_row = cursor.fetchone()
    interview_data = json.loads(interview_row[0]) if interview_row and interview_row[0] else {}

    print(f"\nИнтервью данные: {len(interview_data)} полей")

    # Research results
    cursor.execute("""
        SELECT research_id, research_results
        FROM researcher_research
        WHERE session_id = 9 AND status = 'completed'
        ORDER BY completed_at DESC LIMIT 1
    """)
    research_row = cursor.fetchone()
    research_id = research_row[0] if research_row else None
    research_results = json.loads(research_row[1]) if research_row and research_row[1] else None

    print(f"Research ID: {research_id}")
    print(f"Research данные: {len(str(research_results))} символов" if research_results else "Research отсутствует")

    cursor.close()
    conn.close()
    
    # Формируем user_answers из interview_data
    user_answers = {
        'project_name': interview_data.get('question_38', 'Стрельба из лука'),
        'description': interview_data.get('question_34', ''),
        'problem': interview_data.get('question_36', ''),
        'solution': interview_data.get('question_39', ''),
        'target_group': interview_data.get('question_37', ''),
        'geography': interview_data.get('question_35', ''),
        'budget': interview_data.get('question_51', '750000'),
        'timeline': '12',
        'team': 'Лига стрельбы из лука Кемерово, Федерация стрельбы из лука Кузбасса'
    }
    
    return {
        'user_answers': user_answers,
        'anketa_id': '#AN-20250905-Natalia_bruzzzz-001',
        'session_id': 9,
        'selected_grant': {
            'name': 'Президентский грант',
            'fund': 'ФПГ'
        },
        'admin_user': 'claude_code_test',
        'requested_amount': float(user_answers.get('budget', 750000)),
        'project_duration': 12
    }

async def run_writer():
    print("\n" + "="*70)
    print("ЗАПУСК WRITER AGENT V2")
    print("LLM PROVIDER: Claude Code ТОЛЬКО")
    print("URL: http://178.236.17.55:8000")
    print("="*70)

    # Загружаем данные
    input_data = load_session_data()
    
    # Импортируем Writer V2
    from agents.writer_agent_v2 import WriterAgentV2

    # Создаем Writer с llm_provider="claude_code" и SQLite wrapper
    writer = WriterAgentV2(db_wrapper, llm_provider="claude_code")
    
    print("\n[OK] Writer Agent V2 создан")
    print(f"[OK] LLM Provider: claude_code")
    print(f"[OK] Anketa ID: {input_data['anketa_id']}")
    print(f"[OK] Session ID: {input_data['session_id']}")
    
    # Запускаем написание
    print("\n" + "="*70)
    print("STAGE 1+2: PLANNING + WRITING через Claude Code")
    print("="*70)
    
    try:
        result = await writer.write_application_async(input_data)
        
        print("\n" + "="*70)
        print("РЕЗУЛЬТАТ")
        print("="*70)
        
        if result['status'] == 'success':
            print(f"\n[OK] УСПЕШНО!")
            print(f"[OK] Application Number: {result.get('application_number', 'N/A')}")
            print(f"[OK] Quality Score: {result.get('quality_score', 0)}/10")
            print(f"[OK] Citations Used: {len(result.get('citations', []))}")
            print(f"[OK] Tables Included: {len(result.get('tables', []))}")
            print(f"[OK] Total Chars: {len(result.get('application', {}).get('full_text', ''))}")
            print(f"[OK] Provider Used: {result.get('provider_used', 'N/A')}")
            
            # Сохраняем результат в файл
            output_dir = os.path.join(base_dir, 'grant_export_session_9', '03_grant_draft')
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, 'grant_result.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n[OK] Результат сохранен: {output_file}")
            
            return result
        else:
            print(f"\n[FAIL] ОШИБКА: {result.get('message', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"\n[FAIL] КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(run_writer())
    
    if result and result['status'] == 'success':
        print("\n" + "="*70)
        print("WRITER AGENT ЗАВЕРШЕН УСПЕШНО")
        print("="*70)
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("WRITER AGENT ЗАВЕРШЕН С ОШИБКОЙ")
        print("="*70)
        sys.exit(1)
