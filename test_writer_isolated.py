#!/usr/bin/env python3
"""Isolated test for WriterAgentV2 - check if it generates proper grant text"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.writer_agent_v2 import WriterAgentV2
from data.database.models import GrantServiceDatabase

async def test_writer():
    print("="*60)
    print("ISOLATED TEST: WriterAgentV2")
    print("="*60)
    
    # Initialize
    db = GrantServiceDatabase()
    writer = WriterAgentV2(db=db, llm_provider="gigachat")
    
    # Test data
    input_data = {
        "anketa_id": "#AN-TEST-001",
        "user_answers": {
            "problem": "Тестовая проблема: недостаток образовательных программ",
            "solution": "Тестовое решение: создание центра обучения",
            "goals": "Цели: повышение грамотности населения",
            "activities": "Мероприятия: проведение семинаров и тренингов",
            "results": "Результаты: обучено 100 человек",
            "budget_breakdown": "Бюджет: 500 000 рублей"
        },
        "selected_grant": {
            "name": "Президентский грант",
            "organization": "Фонд президентских грантов"
        }
    }
    
    print(f"\n✅ Input data prepared")
    print(f"   Problem: {input_data['user_answers']['problem'][:50]}...")
    
    # Test grant generation
    print(f"\n🔧 Calling writer.write_application_async()...")
    
    try:
        result = await writer.write_application_async(input_data)
        
        print(f"\n✅ Writer returned result!")
        print(f"   Type: {type(result)}")
        print(f"   Keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        # Check grant text
        if 'grant_text' in result:
            grant_text = result['grant_text']
            print(f"\n📊 Grant Text Stats:")
            print(f"   Length: {len(grant_text)} characters")
            print(f"   Lines: {grant_text.count(chr(10))}")
            print(f"   First 200 chars:\n   {grant_text[:200]}")
            
            if len(grant_text) < 1000:
                print(f"\n❌ FAIL: Grant too short ({len(grant_text)} < 1000)")
                return False
            else:
                print(f"\n✅ SUCCESS: Grant looks good!")
                return True
        else:
            print(f"\n❌ FAIL: No 'grant_text' in result")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_writer())
    sys.exit(0 if success else 1)
