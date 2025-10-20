#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для запуска Researcher Agent для заявки Натальи про стрельбу из лука

Проверка:
1. Запуск researcher для anketa_id
2. Сохранение в БД с правильной номенклатурой (research_id)
3. Экспорт MD отчета в reports/
4. Генерация PDF отчета
"""

import sys
import os
import asyncio
import logging

# Настройка путей
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'agents'))
sys.path.insert(0, os.path.join(current_dir, 'shared'))
sys.path.insert(0, os.path.join(current_dir, 'data'))
sys.path.insert(0, os.path.join(current_dir, 'web-admin'))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорты
from data.database.models import GrantServiceDatabase
from agents.researcher_agent_v2 import ResearcherAgentV2


async def test_researcher_archery():
    """
    Тестовый запуск Researcher Agent для заявки про стрельбу из лука
    """

    # Настройка UTF-8 для Windows консоли
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

    print("=" * 80)
    print("TEST: Researcher Agent for anketa #AN-20251012-Natalia_bruzzzz-001")
    print("=" * 80)
    print()

    # Параметры
    anketa_id = '#AN-20251012-Natalia_bruzzzz-001'

    # 1. Инициализация БД
    print("[DB] Connecting to database...")
    db = GrantServiceDatabase()
    print(f"[OK] Connected: {db.db_path}")
    print()

    # 2. Проверка существования анкеты
    print(f"[CHECK] Verifying anketa {anketa_id}...")
    session = db.get_session_by_anketa_id(anketa_id)

    if not session:
        print(f"[ERROR] Anketa {anketa_id} not found in DB!")
        return

    print(f"[OK] Anketa found:")
    print(f"   - Session ID: {session.get('id')}")
    print(f"   - Telegram ID: {session.get('telegram_id')}")
    print(f"   - Project: Archery training for children and youth")
    print(f"   - Location: Kemerovo")
    print()

    # 3. Проверка существующих исследований
    print("[CHECK] Checking existing research...")
    try:
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT research_id, status, created_at, completed_at
                FROM researcher_research
                WHERE anketa_id = %s
                ORDER BY created_at DESC
            """, (anketa_id,))

            existing = cursor.fetchall()
            cursor.close()

            if existing:
                print(f"[WARN] Found {len(existing)} existing research records:")
                for row in existing:
                    research_id = row[0]
                    status = row[1]
                    created = row[2]
                    completed = row[3]
                    print(f"   - {research_id}: {status} (created: {created})")
            else:
                print("[OK] No existing research - new one will be created")
    except Exception as e:
        logger.error(f"Error checking research: {e}")

    print()

    # 4. Инициализация Researcher Agent
    print("[INIT] Initializing Researcher Agent V2...")
    researcher = ResearcherAgentV2(
        db=db,
        llm_provider='claude_code',
        websearch_provider='claude_code'  # Using Claude Code per policy
    )
    print("[OK] Researcher Agent initialized")
    print()

    # 5. Запуск исследования
    print("[RUN] STARTING RESEARCH...")
    print("   This will take ~10-15 minutes (27 WebSearch queries)")
    print("   Please wait...")
    print()

    try:
        start_time = asyncio.get_event_loop().time()

        result = await researcher.research_with_expert_prompts(anketa_id)

        elapsed = asyncio.get_event_loop().time() - start_time

        print()
        print("=" * 80)
        print("[SUCCESS] RESEARCH COMPLETED!")
        print("=" * 80)
        print()

        if result.get('status') == 'completed':
            research_id = result.get('research_id')
            research_results = result.get('research_results', {})
            metadata = research_results.get('metadata', {})

            print(f"[ID] Research ID: {research_id}")
            print(f"[TIME] Execution time: {elapsed:.2f}s")
            print()

            print("[STATS] Statistics:")
            print(f"   - Total queries: {metadata.get('total_queries', 0)}")
            print(f"   - Total sources: {metadata.get('sources_count', 0)}")
            print(f"   - WebSearch provider: {metadata.get('websearch_provider', 'unknown')}")
            print()

            blocks = metadata.get('blocks', {})
            print("[BLOCKS] Blocks:")
            for block_name, block_data in blocks.items():
                print(f"   - {block_name}: {block_data.get('queries')} queries, "
                      f"{block_data.get('sources')} sources, "
                      f"{block_data.get('processing_time')}s")
            print()

            # 6. Проверка файлов
            print("[FILES] Checking generated files...")
            reports_dir = os.path.join(current_dir, 'reports')

            md_filename = f"{research_id.replace('#', '')}.md"
            md_filepath = os.path.join(reports_dir, md_filename)

            pdf_filename = f"{research_id.replace('#', '')}.pdf"
            pdf_filepath = os.path.join(reports_dir, pdf_filename)

            if os.path.exists(md_filepath):
                md_size = os.path.getsize(md_filepath)
                print(f"[OK] MD report created: {md_filepath} ({md_size:,} bytes)")
            else:
                print(f"[WARN] MD report not found: {md_filepath}")

            if os.path.exists(pdf_filepath):
                pdf_size = os.path.getsize(pdf_filepath)
                print(f"[OK] PDF report created: {pdf_filepath} ({pdf_size:,} bytes)")
            else:
                print(f"[WARN] PDF report not found: {pdf_filepath}")

            print()

            # 7. Проверка сохранения в БД
            print("[DB] Checking database storage...")
            try:
                with db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT
                            research_id,
                            status,
                            llm_provider,
                            model,
                            created_at,
                            completed_at,
                            jsonb_typeof(research_results) as results_type,
                            jsonb_object_keys(research_results) as result_keys
                        FROM researcher_research
                        WHERE research_id = %s
                    """, (research_id,))

                    db_row = cursor.fetchone()
                    cursor.close()

                    if db_row:
                        print(f"[OK] Record found in DB:")
                        print(f"   - Research ID: {db_row[0]}")
                        print(f"   - Status: {db_row[1]}")
                        print(f"   - LLM Provider: {db_row[2]}")
                        print(f"   - Model: {db_row[3]}")
                        print(f"   - Created: {db_row[4]}")
                        print(f"   - Completed: {db_row[5]}")
                        print(f"   - Results type: {db_row[6]}")
                        print(f"   - Result keys: {db_row[7]}")
                    else:
                        print(f"[ERROR] Record {research_id} not found in DB!")

            except Exception as e:
                logger.error(f"Error checking DB: {e}")

            print()
            print("=" * 80)
            print("[SUCCESS] TEST COMPLETED!")
            print("=" * 80)

        elif result.get('status') == 'error':
            print(f"[ERROR] ERROR: {result.get('error')}")
            print()

            if result.get('research_id'):
                print(f"[ID] Research ID (partial): {result.get('research_id')}")
                print("[WARN] Check DB for details")

    except Exception as e:
        logger.error(f"[ERROR] Exception during research: {e}", exc_info=True)
        print()
        print(f"[CRITICAL] CRITICAL ERROR: {e}")


if __name__ == "__main__":
    # Запуск async функции
    asyncio.run(test_researcher_archery())
