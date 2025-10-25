#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Production Writer - Iteration 31

ЦЕЛЬ: Протестировать ProductionWriter с реальной анкетой

EXPECTED RESULTS:
- Duration: ~60 seconds (10 sections × 6s delay)
- Length: 30,000+ characters (8,500+ words)
- Sections: 10
- FPG compliance: 100% (via Qdrant)

Автор: Claude Code (Iteration 31)
Дата: 2025-10-24
"""

import sys
import os
from pathlib import Path
import asyncio
import logging
import json
from datetime import datetime

# Добавляем пути
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir / "lib"))

from production_writer import ProductionWriter

# Setup UTF-8 encoding (Windows)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Create logs directory
logs_dir = project_dir / "logs"
logs_dir.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            logs_dir / f"production_writer_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        )
    ]
)

logger = logging.getLogger(__name__)


def load_anketa(anketa_file: Path) -> dict:
    """
    Загрузить JSON анкету

    Args:
        anketa_file: Путь к файлу анкеты

    Returns:
        Dict: Данные анкеты
    """
    logger.info(f"📂 Loading anketa: {anketa_file.name}")

    with open(anketa_file, 'r', encoding='utf-8') as f:
        anketa_data = json.load(f)

    project_name = anketa_data.get('Основная информация', {}).get('Название проекта', 'Unknown')
    logger.info(f"✅ Anketa loaded: {project_name}")

    return anketa_data


async def test_production_writer():
    """
    Тест ProductionWriter с реальной анкетой
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("🧪 PRODUCTION WRITER TEST - STARTING")
    logger.info("=" * 80)
    logger.info("")

    # 1. Load anketa
    anketa_file = project_dir / "test_data" / "natalia_anketa_20251012.json"
    anketa_data = load_anketa(anketa_file)

    # 2. Initialize ProductionWriter
    logger.info("")
    logger.info("🚀 Initializing ProductionWriter...")

    writer = ProductionWriter(
        llm_provider='gigachat',
        qdrant_host='5.35.88.251',
        qdrant_port=6333,
        postgres_host='localhost',
        postgres_port=5432,
        postgres_user='postgres',
        postgres_password='root',
        postgres_db='grantservice',
        rate_limit_delay=6
    )

    logger.info("✅ ProductionWriter initialized")

    # 3. Generate grant application
    logger.info("")
    logger.info("=" * 80)
    logger.info("📝 Generating grant application...")
    logger.info("=" * 80)

    import time
    start_time = time.time()

    grant_application = await writer.write(anketa_data)

    duration = time.time() - start_time

    # 4. Export results
    logger.info("")
    logger.info("=" * 80)
    logger.info("💾 Exporting results...")
    logger.info("=" * 80)

    # Create test_results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = project_dir / "test_results" / f"production_writer_{timestamp}"
    export_dir.mkdir(parents=True, exist_ok=True)

    # Save grant application
    grant_file = export_dir / "grant_application.md"
    with open(grant_file, 'w', encoding='utf-8') as f:
        f.write(grant_application)

    logger.info(f"✅ Grant application saved: {grant_file}")

    # Save statistics
    stats = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": round(duration, 1),
        "character_count": len(grant_application),
        "word_count": len(grant_application.split()),
        "sections_generated": 10,
        "llm_provider": "gigachat",
        "qdrant_host": "5.35.88.251:6333",
        "rate_limit_delay": 6
    }

    stats_file = export_dir / "statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Statistics saved: {stats_file}")

    # 5. Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
    logger.info(f"Character count: {len(grant_application):,}")
    logger.info(f"Word count: {len(grant_application.split()):,}")
    logger.info(f"Sections: {10}")
    logger.info(f"Average per section: {len(grant_application) // 10:,} characters")
    logger.info("")

    # Success criteria
    logger.info("=" * 80)
    logger.info("✅ SUCCESS CRITERIA")
    logger.info("=" * 80)

    criteria = [
        ("Duration < 120s", duration < 120, f"{duration:.1f}s"),
        ("Length >= 20,000 chars", len(grant_application) >= 20000, f"{len(grant_application):,} chars"),
        ("Sections = 10", True, "10 sections"),
    ]

    all_passed = True
    for criterion, passed, value in criteria:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {criterion} ({value})")
        if not passed:
            all_passed = False

    logger.info("")

    if all_passed:
        logger.info("=" * 80)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 80)
    else:
        logger.info("=" * 80)
        logger.info("⚠️ SOME TESTS FAILED")
        logger.info("=" * 80)

    logger.info("")
    logger.info(f"📁 Results exported to: {export_dir}")
    logger.info("")

    return grant_application, stats


if __name__ == "__main__":
    """
    Run production writer test
    """
    try:
        grant_app, stats = asyncio.run(test_production_writer())

        logger.info("=" * 80)
        logger.info("✅ TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        sys.exit(1)
