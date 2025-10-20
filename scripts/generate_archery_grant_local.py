#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Локальный скрипт для генерации гранта "Лучные клубы Кемерово"

ВНИМАНИЕ: НЕ коммитить в git!
Только для локальной разработки и тестирования.

Usage:
    python scripts/generate_archery_grant_local.py

Author: Grant Service Architect Agent
Created: 2025-10-12
"""

import sys
import os
import asyncio
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tests" / "integration"))

# Import test
from test_archery_club_fpg_e2e import test_archery_club_full_pipeline


async def main():
    """
    Запуск полного pipeline для проекта "Лучные клубы Кемерово"
    """
    print("=" * 80)
    print("Генерация гранта: Лучные клубы Кемерово")
    print("=" * 80)
    print()
    print("Pipeline:")
    print("  1. Interactive Interview + Audit")
    print("  2. Research + WebSearch (27 + 1 queries)")
    print("  3. Grant Writing")
    print("  4. Final Review")
    print()
    print("Артефакты будут сохранены в: grants_output/archery_kemerovo/")
    print("=" * 80)
    print()

    try:
        # Запуск теста
        await test_archery_club_full_pipeline()

        print()
        print("=" * 80)
        print("✅ УСПЕШНО! Все артефакты созданы.")
        print("=" * 80)
        print()
        print("Проверьте директорию: grants_output/archery_kemerovo/")
        print()
        print("Файлы:")
        print("  - anketa_archery_kemerovo_audit.md + .pdf")
        print("  - research_archery_kemerovo.md + .pdf")
        print("  - grant_AN-YYYYMMDD-archery_kemerovo-NNN.md + .pdf")
        print("  - review_AN-YYYYMMDD-archery_kemerovo-NNN.md + .pdf")
        print()

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ОШИБКА: {e}")
        print("=" * 80)
        print()
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
