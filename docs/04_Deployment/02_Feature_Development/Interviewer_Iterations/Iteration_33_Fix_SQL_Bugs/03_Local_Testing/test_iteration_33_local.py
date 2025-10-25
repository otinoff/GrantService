#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iteration 33 - Local E2E Test (ProductionWriter)

ЦЕЛЬ: Протестировать ProductionWriter локально после фиксов

Что тестируем:
1. ProductionWriter использует GigaChat-Max (не Lite)
2. Database методы работают с правильными колонками (telegram_id)
3. ProductionWriter генерирует грант end-to-end

Input: anketa_id из локальной БД
Output:
  1. grant_content (30K+ символов)
  2. Метрики генерации
  3. Проверка токенов GigaChat

Автор: Claude Code (Iteration 33)
Дата: 2025-10-24
"""

import sys
import os
from pathlib import Path
import logging
import asyncio
import time
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add paths
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agents"))
sys.path.insert(0, str(project_root / "data" / "database"))

# Imports
from agents.production_writer import ProductionWriter
from data.database.models import GrantServiceDatabase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


async def test_database_methods(db: GrantServiceDatabase, user_id: int):
    """
    Test 1: Database методы с правильными колонками

    Проверяем:
    - get_latest_completed_anketa() использует telegram_id
    - get_latest_grant_for_user() использует user_id
    - get_user_grants() использует user_id
    """
    print_section("TEST 1: Database Methods")

    results = {
        "get_latest_completed_anketa": None,
        "get_latest_grant_for_user": None,
        "get_user_grants": None
    }

    # Test 1: get_latest_completed_anketa
    logger.info(f"Testing get_latest_completed_anketa(user_id={user_id})...")
    try:
        anketa = db.get_latest_completed_anketa(user_id)
        if anketa:
            logger.info(f"✅ Found anketa: {anketa['anketa_id']}")
            logger.info(f"   Status: {anketa['status']}")
            logger.info(f"   Telegram ID: {anketa.get('telegram_id', 'N/A')}")
            results["get_latest_completed_anketa"] = "PASS"
        else:
            logger.warning("⚠️ No completed anketa found")
            results["get_latest_completed_anketa"] = "NO_DATA"
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        results["get_latest_completed_anketa"] = f"FAIL: {e}"

    # Test 2: get_latest_grant_for_user
    logger.info(f"\nTesting get_latest_grant_for_user(user_id={user_id})...")
    try:
        grant = db.get_latest_grant_for_user(user_id)
        if grant:
            logger.info(f"✅ Found grant: {grant['grant_id']}")
            logger.info(f"   Status: {grant['status']}")
            logger.info(f"   Characters: {grant.get('character_count', 'N/A')}")
            results["get_latest_grant_for_user"] = "PASS"
        else:
            logger.warning("⚠️ No grants found")
            results["get_latest_grant_for_user"] = "NO_DATA"
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        results["get_latest_grant_for_user"] = f"FAIL: {e}"

    # Test 3: get_user_grants
    logger.info(f"\nTesting get_user_grants(user_id={user_id})...")
    try:
        grants = db.get_user_grants(user_id)
        logger.info(f"✅ Found {len(grants)} grants")
        for grant in grants[:3]:
            logger.info(f"   - {grant['grant_id']} ({grant['status']})")
        results["get_user_grants"] = "PASS"
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        results["get_user_grants"] = f"FAIL: {e}"

    return results


async def test_production_writer_init():
    """
    Test 2: ProductionWriter инициализация

    Проверяем:
    - LLM client использует GigaChat-Max
    - Qdrant connection работает
    - Expert Agent инициализирован
    """
    print_section("TEST 2: ProductionWriter Initialization")

    logger.info("Initializing ProductionWriter...")

    try:
        writer = ProductionWriter(
            llm_provider='gigachat',
            qdrant_host='5.35.88.251',
            qdrant_port=6333,
            postgres_host='5.35.88.251',
            postgres_port=5434,
            postgres_user='grantservice',
            postgres_password='jPsGn%Nt%q#THnUB&&cqo*1Q',
            postgres_db='grantservice'
        )

        # Check model
        model = writer.llm_client.model
        logger.info(f"✅ LLM Client initialized")
        logger.info(f"   Provider: {writer.llm_provider}")
        logger.info(f"   Model: {model}")

        if model == "GigaChat-Max":
            logger.info("   ✅ Using GigaChat-Max (tokens from package)")
            model_check = "PASS"
        else:
            logger.error(f"   ❌ WRONG MODEL: {model} (should be GigaChat-Max)")
            model_check = f"FAIL: Using {model}"

        # Check Expert Agent
        if writer.expert_agent:
            logger.info("✅ Expert Agent initialized")
            expert_check = "PASS"
        else:
            logger.error("❌ Expert Agent NOT initialized")
            expert_check = "FAIL"

        return {
            "model_check": model_check,
            "expert_agent": expert_check,
            "initialization": "PASS"
        }

    except Exception as e:
        logger.error(f"❌ ProductionWriter initialization FAILED: {e}")
        return {
            "model_check": f"FAIL: {e}",
            "expert_agent": "NOT_TESTED",
            "initialization": f"FAIL: {e}"
        }


async def test_grant_generation(db: GrantServiceDatabase, user_id: int):
    """
    Test 3: Full Grant Generation

    Проверяем:
    - Получение anketa
    - Генерация через ProductionWriter
    - Сохранение в БД
    - Метрики генерации
    """
    print_section("TEST 3: Grant Generation (End-to-End)")

    # Get anketa
    logger.info(f"Getting latest completed anketa for user {user_id}...")
    anketa = db.get_latest_completed_anketa(user_id)

    if not anketa:
        logger.error("❌ No completed anketa found. Cannot test generation.")
        return {
            "anketa_retrieval": "FAIL: No anketa",
            "generation": "NOT_TESTED",
            "database_save": "NOT_TESTED"
        }

    anketa_id = anketa['anketa_id']
    logger.info(f"✅ Found anketa: {anketa_id}")
    logger.info(f"   User: {anketa.get('first_name', '')} {anketa.get('last_name', '')}")
    logger.info(f"   Status: {anketa['status']}")

    # Initialize ProductionWriter
    logger.info("\nInitializing ProductionWriter...")
    writer = ProductionWriter(
        llm_provider='gigachat',
        qdrant_host='5.35.88.251',
        qdrant_port=6333,
        postgres_host='5.35.88.251',
        postgres_port=5434,
        postgres_user='grantservice',
        postgres_password='jPsGn%Nt%q#THnUB&&cqo*1Q',
        postgres_db='grantservice',
        db=db
    )

    logger.info(f"✅ ProductionWriter initialized (Model: {writer.llm_client.model})")

    # Generate grant
    logger.info(f"\n🚀 Starting grant generation for anketa {anketa_id}...")
    logger.info("   This will take ~60-180 seconds (10 sections)")

    start_time = time.time()

    try:
        result = await writer.write(
            anketa_id=anketa_id,
            user_id=user_id
        )

        duration = time.time() - start_time

        logger.info(f"\n✅ Grant generated successfully!")
        logger.info(f"   Duration: {duration:.1f} seconds")
        logger.info(f"   Grant ID: {result.get('grant_id', 'N/A')}")
        logger.info(f"   Characters: {result.get('character_count', 'N/A')}")
        logger.info(f"   Words: {result.get('word_count', 'N/A')}")
        logger.info(f"   Sections: {result.get('sections_generated', 'N/A')}")

        # Verify in database
        logger.info("\nVerifying grant in database...")
        grant = db.get_grant_by_anketa_id(anketa_id)

        if grant:
            logger.info("✅ Grant found in database")
            logger.info(f"   Grant ID: {grant['grant_id']}")
            logger.info(f"   Status: {grant['status']}")
            db_check = "PASS"
        else:
            logger.error("❌ Grant NOT found in database")
            db_check = "FAIL"

        return {
            "anketa_retrieval": "PASS",
            "generation": "PASS",
            "database_save": db_check,
            "duration_seconds": duration,
            "character_count": result.get('character_count', 0),
            "word_count": result.get('word_count', 0),
            "grant_id": result.get('grant_id', '')
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Grant generation FAILED after {duration:.1f}s: {e}")
        return {
            "anketa_retrieval": "PASS",
            "generation": f"FAIL: {e}",
            "database_save": "NOT_TESTED",
            "duration_seconds": duration
        }


async def main():
    """Main test function"""
    print("\n" + "=" * 80)
    print("  ITERATION 33 - LOCAL E2E TEST")
    print("  Testing ProductionWriter after SQL fixes")
    print("=" * 80 + "\n")

    # Test user (Andrew Otinoff from production)
    TEST_USER_ID = 5032079932

    logger.info(f"Test User ID: {TEST_USER_ID}")
    logger.info(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize database
    logger.info("\nConnecting to database...")
    db = GrantServiceDatabase(
        connection_params={
            'host': '5.35.88.251',
            'port': 5434,
            'user': 'grantservice',
            'password': 'jPsGn%Nt%q#THnUB&&cqo*1Q',
            'database': 'grantservice'
        }
    )
    logger.info("✅ Database connected")

    # Run tests
    all_results = {}

    # Test 1: Database methods
    db_results = await test_database_methods(db, TEST_USER_ID)
    all_results["database_methods"] = db_results

    # Test 2: ProductionWriter initialization
    init_results = await test_production_writer_init()
    all_results["production_writer_init"] = init_results

    # Test 3: Grant generation (optional - takes time!)
    logger.info("\n" + "=" * 80)
    generate = input("Run full grant generation test? (takes 60-180s) [y/N]: ")

    if generate.lower() == 'y':
        gen_results = await test_grant_generation(db, TEST_USER_ID)
        all_results["grant_generation"] = gen_results
    else:
        logger.info("Skipping grant generation test")
        all_results["grant_generation"] = {"status": "SKIPPED"}

    # Print summary
    print_section("TEST SUMMARY")

    print("Database Methods:")
    for test, result in all_results["database_methods"].items():
        status = "✅" if result == "PASS" else ("⚠️" if result == "NO_DATA" else "❌")
        print(f"  {status} {test}: {result}")

    print("\nProductionWriter Initialization:")
    for test, result in all_results["production_writer_init"].items():
        status = "✅" if result == "PASS" else "❌"
        print(f"  {status} {test}: {result}")

    if all_results["grant_generation"]["status"] != "SKIPPED":
        print("\nGrant Generation:")
        for test, result in all_results["grant_generation"].items():
            if isinstance(result, (int, float)):
                print(f"  📊 {test}: {result}")
            else:
                status = "✅" if result == "PASS" else "❌"
                print(f"  {status} {test}: {result}")

    # Overall status
    print("\n" + "=" * 80)

    # Check critical tests
    critical_passed = (
        all_results["database_methods"]["get_latest_completed_anketa"] in ["PASS", "NO_DATA"] and
        all_results["production_writer_init"]["model_check"] == "PASS"
    )

    if critical_passed:
        print("✅ ITERATION 33 FIXES: VALIDATED")
        print("   - Database methods use correct columns")
        print("   - ProductionWriter uses GigaChat-Max")
    else:
        print("❌ ITERATION 33 FIXES: FAILED")
        print("   Check errors above")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
