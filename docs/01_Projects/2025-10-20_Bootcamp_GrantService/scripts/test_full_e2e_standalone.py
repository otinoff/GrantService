#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iteration 30 - FULL E2E TEST (БЕЗ Telegram Bot!)

ЦЕЛЬ: Протестировать полный грантовый поток БЕЗ зависимости от Telegram Bot

Input: JSON file (natalia_anketa_20251012.json)
Output: 3 текстовых файла:
  1. research_results.json (Researcher + Perplexity)
  2. grant_application.md (Writer + GigaChat)
  3. audit_report.json (Auditor + GigaChat)

Workflow:
  JSON input → GrantPipeline → 3 files

Duration: ~9 minutes
  - Stage 1 (Researcher): 6-7 min
  - Stage 2 (Writer): 1-2 min
  - Stage 3 (Auditor): 30 sec

Автор: Claude Code (Iteration 30)
Дата: 2025-10-24
"""

import sys
import os
from pathlib import Path
import logging
import asyncio
import time
from datetime import datetime
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add paths
project_dir = Path(__file__).parent.parent
lib_dir = project_dir / "lib"
sys.path.insert(0, str(lib_dir))

# Import GrantPipeline
from grant_pipeline import GrantPipeline

# Create logs directory
logs_dir = project_dir / "logs"
logs_dir.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(logs_dir / f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Загрузить конфигурацию из JSON"""
    logger.info(f"Loading config from: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    logger.info("✅ Config loaded successfully")
    return config


def load_json_anketa(anketa_path: Path) -> dict:
    """Загрузить анкету из JSON"""
    logger.info(f"Loading anketa from: {anketa_path}")

    with open(anketa_path, 'r', encoding='utf-8') as f:
        anketa_data = json.load(f)

    logger.info("✅ Anketa loaded successfully")
    return anketa_data


def extract_project_data(anketa_data: dict) -> dict:
    """
    Извлечь project_data из anketa JSON

    Args:
        anketa_data: Данные из natalia_anketa_20251012.json

    Returns:
        project_data: {
            "project_name": "...",
            "problem": "...",
            "target_audience": "...",
            "geography": "...",
            "goals": [...]
        }
    """
    interview_data = anketa_data.get('interview_data', {})

    project_data = {
        "project_name": anketa_data.get('project_info', {}).get('name', ''),
        "problem": interview_data.get('problem_and_significance', ''),
        "target_audience": interview_data.get('target_group', ''),
        "geography": interview_data.get('geography', ''),
        "goals": [
            interview_data.get('main_goal', '')
        ]
    }

    logger.info("📋 Project data extracted:")
    logger.info(f"   Name: {project_data['project_name'][:50]}...")
    logger.info(f"   Geography: {project_data['geography']}")
    logger.info(f"   Target: {project_data['target_audience'][:50]}...")

    return project_data


async def main():
    """
    Main E2E test function
    """
    test_start = time.time()

    print("=" * 80)
    print("🚀 ITERATION 30 - FULL E2E TEST (STANDALONE)")
    print("=" * 80)
    print("БЕЗ Telegram Bot! БЕЗ database dependency!")
    print("")
    print("Input: JSON file")
    print("Output: 3 text files (research + grant + audit)")
    print("")
    print("=" * 80)
    print("")

    try:
        # ============================================================
        # STEP 1: Load config
        # ============================================================
        print("📁 STEP 1: Loading configuration...")
        config_path = project_dir / "test_config.json"
        config = load_config(config_path)

        # ============================================================
        # STEP 2: Load JSON anketa
        # ============================================================
        print("")
        print("📄 STEP 2: Loading JSON anketa...")
        anketa_path = project_dir / "test_data" / "natalia_anketa_20251012.json"

        if not anketa_path.exists():
            raise FileNotFoundError(f"Anketa not found: {anketa_path}")

        anketa_data = load_json_anketa(anketa_path)

        # ============================================================
        # STEP 3: Extract project_data
        # ============================================================
        print("")
        print("🔍 STEP 3: Extracting project data...")
        project_data = extract_project_data(anketa_data)

        # ============================================================
        # STEP 4: Initialize GrantPipeline
        # ============================================================
        print("")
        print("⚙️ STEP 4: Initializing GrantPipeline...")
        pipeline = GrantPipeline(config)

        # ============================================================
        # STEP 5: RUN PIPELINE (БЕЗ ОСТАНОВКИ!)
        # ============================================================
        print("")
        print("=" * 80)
        print("🚀 STEP 5: RUNNING FULL PIPELINE (Researcher → Writer → Auditor)")
        print("=" * 80)
        print("⚠️ This will take ~9 minutes, DO NOT STOP!")
        print("")

        export_dir = project_dir / "test_results" / f"iteration_30_e2e_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        results = await pipeline.run(
            project_data=project_data,
            export_dir=export_dir
        )

        # ============================================================
        # STEP 6: Summary
        # ============================================================
        test_duration = time.time() - test_start

        print("")
        print("=" * 80)
        print("✅ E2E TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("")
        print(f"Total duration: {test_duration:.1f}s ({test_duration/60:.1f} min)")
        print("")
        print("📊 RESULTS:")
        print(f"   Auditor score: {results['auditor'].get('overall_score', 0) * 100:.1f}%")
        print(f"   Can submit: {results['auditor'].get('can_submit', False)}")
        print(f"   Grant length: {len(results['writer'])} characters")
        print("")
        print("📁 EXPORTED FILES:")
        for i, file_path in enumerate(results['exported_files'], 1):
            print(f"   {i}. {file_path.name}")
            print(f"      Path: {file_path}")
        print("")
        print("=" * 80)
        print("")

        # ============================================================
        # STEP 7: Validation
        # ============================================================
        print("🔍 VALIDATION:")
        print("")

        # Check file sizes
        for file_path in results['exported_files']:
            size_kb = file_path.stat().st_size / 1024
            print(f"   ✅ {file_path.name}: {size_kb:.1f} KB")

        # Check Auditor score
        score = results['auditor'].get('overall_score', 0)
        can_submit = results['auditor'].get('can_submit', False)

        print("")
        if can_submit and score >= 0.8:
            print("   ✅ VALIDATION PASSED: Score ≥ 80%, can_submit = true")
        else:
            print(f"   ⚠️ VALIDATION WARNING: Score {score*100:.1f}%, can_submit = {can_submit}")

        print("")
        print("=" * 80)
        print("🎉 ITERATION 30 - FULL E2E TEST SUCCESSFUL!")
        print("=" * 80)

    except Exception as e:
        print("")
        print("=" * 80)
        print(f"❌ E2E TEST FAILED: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    """
    Run E2E test
    """
    print("")
    print("🚀 Starting Iteration 30 E2E Test...")
    print("")

    # Run test
    asyncio.run(main())
