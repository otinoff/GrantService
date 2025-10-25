#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест Researcher Agent с Perplexity WebSearch
"""

import sys
import os
import asyncio
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'agents'))
sys.path.insert(0, os.path.join(current_dir, 'shared'))
sys.path.insert(0, os.path.join(current_dir, 'data'))
sys.path.insert(0, os.path.join(current_dir, 'web-admin'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from data.database.models import GrantServiceDatabase
from agents.researcher_agent_v2 import ResearcherAgentV2


async def test_researcher_perplexity():
    """Test with Perplexity WebSearch"""

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

    print("=" * 80)
    print("TEST: Researcher Agent with PERPLEXITY WebSearch")
    print("=" * 80)
    print()

    anketa_id = '#AN-20251012-Natalia_bruzzzz-001'

    print("[DB] Connecting...")
    db = GrantServiceDatabase()
    print(f"[OK] Connected: {db.db_path}")
    print()

    print("[INIT] Initializing Researcher Agent with Perplexity...")
    researcher = ResearcherAgentV2(
        db=db,
        llm_provider='claude_code',
        websearch_provider='perplexity',  # PERPLEXITY!
        websearch_fallback=None  # NO fallback
    )
    print("[OK] Researcher initialized with Perplexity")
    print()

    # Удаляем старое исследование если есть
    try:
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM researcher_research
                WHERE anketa_id = %s AND research_id = %s
            """, (anketa_id, '#AN-20251012-Natalia_bruzzzz-001-RS-001'))
            conn.commit()
            cursor.close()
            print("[CLEAN] Deleted previous research")
    except:
        pass

    print()
    print("[RUN] STARTING RESEARCH WITH PERPLEXITY...")
    print("   This will take ~5-10 minutes")
    print()

    try:
        start_time = asyncio.get_event_loop().time()
        result = await researcher.research_with_expert_prompts(anketa_id)
        elapsed = asyncio.get_event_loop().time() - start_time

        print()
        print("=" * 80)
        if result.get('status') == 'completed':
            print("[SUCCESS] RESEARCH COMPLETED!")
        else:
            print("[FAILED] RESEARCH FAILED!")
        print("=" * 80)
        print()

        if result.get('status') == 'completed':
            research_id = result.get('research_id')
            metadata = result.get('research_results', {}).get('metadata', {})

            print(f"[ID] Research ID: {research_id}")
            print(f"[TIME] Execution time: {elapsed:.2f}s")
            print(f"[SOURCES] Total sources: {metadata.get('sources_count', 0)}")
            print(f"[PROVIDER] WebSearch provider: {metadata.get('websearch_provider')}")
            print()

            blocks = metadata.get('blocks', {})
            print("[BLOCKS]")
            for block_name, block_data in blocks.items():
                print(f"   - {block_name}: {block_data.get('sources')} sources")

            # Проверка файлов
            print()
            print("[FILES]")
            reports_dir = os.path.join(current_dir, 'reports')
            md_path = os.path.join(reports_dir, f"{research_id.replace('#', '')}.md")

            if os.path.exists(md_path):
                md_size = os.path.getsize(md_path)
                print(f"   - MD report: {md_size:,} bytes")

                # Проверка контента
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_answers = content.count('Нет данных')
                    total_queries = 27
                    answered = total_queries - has_answers
                    print(f"   - Answered queries: {answered}/{total_queries}")

            print()
            print("=" * 80)
            print("[SUCCESS] TEST COMPLETED!")
            print("=" * 80)

        else:
            print(f"[ERROR] {result.get('error')}")

    except Exception as e:
        logger.error(f"Exception: {e}", exc_info=True)
        print(f"[CRITICAL] {e}")


if __name__ == "__main__":
    asyncio.run(test_researcher_perplexity())
