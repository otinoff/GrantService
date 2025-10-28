#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test ResearcherAgent WebSearch - Iteration 60

Проверяет что research_anketa() использует реальный WebSearch
и возвращает источники (не 0).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agents.researcher_agent import ResearcherAgent
from data.database.models import get_db_instance
import json

def test_researcher_websearch():
    """
    Test: ResearcherAgent должен возвращать реальные WebSearch results
    """

    print("=" * 80)
    print("TEST: ResearcherAgent WebSearch (Iteration 60)")
    print("=" * 80)
    print()

    # Get database
    db = get_db_instance()

    # Создаем тестовую анкету в БД
    print("[1/4] Creating test anketa in database...")

    test_anketa = {
        'telegram_id': 999999,
        'anketa_id': 'test_iter60_websearch',
        'interview_data': json.dumps({
            'Основная информация': {
                'Название проекта': 'Адаптивные программы для детей с инвалидностью',
                'Организация': 'Центр инклюзивного образования',
                'Регион': 'Москва'
            },
            'Суть проекта': {
                'Проблема': 'Нехватка адаптивных образовательных программ для детей с инвалидностью в возрасте 7-14 лет',
                'Целевая группа': 'Дети с инвалидностью 7-14 лет'
            }
        }, ensure_ascii=False),
        'stage': 'completed'
    }

    # Сохраняем через прямой SQL (упрощенная версия)
    import psycopg2

    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5434'),
            database=os.getenv('PGDATABASE', 'grantservice'),
            user=os.getenv('PGUSER', 'postgres'),
            password=os.getenv('PGPASSWORD', 'root')
        )

        with conn.cursor() as cur:
            # Проверяем существует ли
            cur.execute(
                "SELECT id FROM sessions WHERE anketa_id = %s",
                ('test_iter60_websearch',)
            )
            existing = cur.fetchone()

            if existing:
                print(f"   Anketa already exists: test_iter60_websearch")
            else:
                # Создаем новую
                cur.execute(
                    """
                    INSERT INTO sessions (telegram_id, anketa_id, interview_data, stage)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        test_anketa['telegram_id'],
                        test_anketa['anketa_id'],
                        test_anketa['interview_data'],
                        test_anketa['stage']
                    )
                )
                conn.commit()
                print(f"   Created test anketa: test_iter60_websearch")

        conn.close()

    except Exception as e:
        print(f"   WARNING: Could not create test anketa: {e}")
        print(f"   Using existing data...")

    print()

    # Create ResearcherAgent
    print("[2/4] Creating ResearcherAgent...")
    researcher = ResearcherAgent(db=db, llm_provider='claude_code')
    print("   ResearcherAgent created ✓")
    print()

    # Run research_anketa() with WebSearch
    print("[3/4] Running research_anketa() with WebSearch...")
    print("   This will make 3 Claude Code WebSearch requests...")
    print("   Expected: ~30-60 seconds")
    print()

    anketa_id = 'test_iter60_websearch'

    try:
        research_result = researcher.research_anketa(anketa_id)

        print("[4/4] Analyzing results...")
        print()

        # Check status
        status = research_result.get('status')
        print(f"   Status: {status}")

        if status != 'success':
            print(f"   ERROR: Research failed!")
            print(f"   Message: {research_result.get('message')}")
            return False

        # Extract metadata
        results = research_result.get('results', {})
        metadata = results.get('metadata', {})

        sources_count = metadata.get('sources_count', 0)
        total_queries = metadata.get('total_queries', 0)

        print(f"   Sources found: {sources_count}")
        print(f"   Queries executed: {total_queries}")
        print()

        # Check Block 1 results
        block1 = results.get('block1', {})
        queries = block1.get('queries', [])

        print(f"   Block 1 queries: {len(queries)}")
        for i, q in enumerate(queries, 1):
            query_text = q.get('query', 'N/A')
            answer_preview = q.get('answer', '')[:100]
            print(f"   Query {i}: {query_text}")
            print(f"            Answer: {answer_preview}...")

        print()

        # Verification
        print("=" * 80)
        if sources_count == 0:
            print("❌ FAIL: WebSearch returned 0 sources")
            print("   This means WebSearch did NOT work correctly")
            print()
            print("   Debug info:")
            print(f"   - research_result keys: {list(research_result.keys())}")
            print(f"   - results keys: {list(results.keys())}")
            print(f"   - metadata: {metadata}")
            return False
        elif sources_count > 0:
            print(f"✅ PASS: WebSearch returned {sources_count} sources")
            print(f"   Executed {total_queries} queries")
            print()
            print("   Iteration 60 fix VERIFIED!")
            print("   research_anketa() correctly uses Claude Code WebSearch")
            return True

    except Exception as e:
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        print()

        import traceback
        traceback.print_exc()

        return False

if __name__ == "__main__":
    success = test_researcher_websearch()

    print()
    print("=" * 80)
    if success:
        print("TEST RESULT: ✅ PASSED")
        print()
        print("Next steps:")
        print("1. Commit changes")
        print("2. Deploy to production")
        print("3. Test with real Telegram bot")
    else:
        print("TEST RESULT: ❌ FAILED")
        print()
        print("Fix required before deployment!")
    print("=" * 80)

    sys.exit(0 if success else 1)
