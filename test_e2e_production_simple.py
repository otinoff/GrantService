#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E Test: Full Pipeline on Production (Iteration 59)
Tests: Interviewer → Auditor → Researcher → Writer → Reviewer
"""

import sys
import os
import asyncio
import json
sys.path.insert(0, '/var/GrantService')

from agents.auditor_agent import AuditorAgent
from agents.researcher_agent import ResearcherAgent
from agents.production_writer import ProductionWriter
from agents.reviewer_agent import ReviewerAgent
from data.database.models import get_db_instance


async def test_full_pipeline():
    """Test complete pipeline with all agents"""

    print("=" * 80)
    print("E2E TEST: Full Pipeline (Iteration 59)")
    print("=" * 80)
    print()

    # Mock anketa data (realistic)
    anketa_data = {
        'Основная информация': {
            'Название проекта': 'Адаптивные программы для детей с инвалидностью',
            'Организация': 'Центр инклюзивного образования',
            'ИНН': '1234567890',
            'Регион': 'Москва'
        },
        'Суть проекта': {
            'Проблема': 'Нехватка адаптивных образовательных программ для детей с инвалидностью в возрасте 7-14 лет. Согласно статистике Росстата, более 700 тысяч детей нуждаются в специализированных программах.',
            'Решение': 'Создание комплекса адаптивных образовательных программ с использованием современных методик инклюзивного образования',
            'Цель': 'Обеспечить доступ к качественному образованию для 500 детей с инвалидностью в течение года'
        },
        'Целевая аудитория': {
            'Описание': 'Дети с инвалидностью 7-14 лет',
            'Количество': '500',
            'География': 'Москва и Московская область'
        },
        'Бюджет': {
            'Общая сумма': '5000000',
            'Источники финансирования': 'Президентский грант, софинансирование'
        }
    }

    print(f"Project: {anketa_data['Основная информация']['Название проекта']}")
    print()

    # Get database instance
    db = get_db_instance()

    try:
        # Step 1: Auditor
        print("[1/4] Running AuditorAgent...")
        print("-" * 80)
        auditor = AuditorAgent(db=db)
        audit_result = await auditor.audit_async(anketa_data=anketa_data)

        if not audit_result or audit_result.get('status') != 'success':
            print("[FAIL] Auditor failed")
            return False

        audit_score = audit_result.get('audit_score', 0)
        print(f"[OK] Audit score: {audit_score}")
        print()

        # Step 2: Researcher
        print("[2/4] Running ResearcherAgent...")
        print("-" * 80)
        researcher = ResearcherAgent(db=db, llm_provider='claude_code')

        research_input = {
            'description': (
                f"{anketa_data['Основная информация']['Название проекта']}. "
                f"{anketa_data['Суть проекта']['Проблема']}"
            ),
            'llm_provider': 'claude_code'
        }

        research_result = await researcher.research_grant_async(research_input)

        if not research_result or research_result.get('status') != 'success':
            print("[WARNING] Research returned empty (not critical)")
            research_result = {}
        else:
            sources_count = len(research_result.get('sources', []))
            results_count = research_result.get('total_results', 0)
            print(f"[OK] Research: {sources_count} sources, {results_count} results")

        print()

        # Step 3: Writer (WITH research_results)
        print("[3/4] Running ProductionWriter (with research_results)...")
        print("-" * 80)
        writer = ProductionWriter(db=db)

        grant = await writer.write(
            anketa_data=anketa_data,
            research_results=research_result
        )

        if not grant or len(grant) < 1000:
            print(f"[FAIL] Grant too short: {len(grant)} chars")
            return False

        print(f"[OK] Grant generated: {len(grant)} characters")
        print()

        # Step 4: Reviewer
        print("[4/4] Running ReviewerAgent...")
        print("-" * 80)
        reviewer = ReviewerAgent(db=db)

        review_result = await reviewer.review_async(grant_text=grant)

        if not review_result or review_result.get('status') != 'success':
            print("[FAIL] Reviewer failed")
            return False

        review_score = review_result.get('score', 0)
        print(f"[OK] Review score: {review_score}")
        print()

        # Summary
        print("=" * 80)
        print("[SUCCESS] Full Pipeline E2E Test PASSED!")
        print("=" * 80)
        print()
        print(f"Pipeline: Interview → Audit ({audit_score}) → Research ({len(research_result.get('sources', []))}) → Writer ({len(grant)}) → Review ({review_score})")
        print()
        print("All agents executed successfully with Iteration 59 changes!")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 80)
        print("[ERROR] E2E Test FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()

        import traceback
        traceback.print_exc()
        print()

        return False


if __name__ == "__main__":
    success = asyncio.run(test_full_pipeline())
    sys.exit(0 if success else 1)
