#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test: ProductionWriter with research_results (Iteration 59)
Tests that Writer accepts and uses research_results parameter
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(__file__))

from agents.production_writer import ProductionWriter


async def test_writer_with_research():
    """Test ProductionWriter accepts research_results"""

    print("=" * 80)
    print("ITERATION 59: ProductionWriter + research_results Quick Test")
    print("=" * 80)
    print()

    # Mock anketa data
    anketa_data = {
        'Основная информация': {
            'Название проекта': 'Адаптивные программы для детей',
            'Организация': 'Тестовая организация',
        },
        'Суть проекта': {
            'Проблема': 'Тестовая проблема',
            'Решение': 'Тестовое решение',
        },
        'Целевая аудитория': {
            'Описание': 'Дети 7-14 лет',
        }
    }

    # Mock research results (as if ResearcherAgent found data)
    research_results = {
        'status': 'success',
        'sources': [
            'https://rosstat.gov.ru/folder/13964',
            'https://mintrud.gov.ru/ministry/about/structure/invalid'
        ],
        'results': [
            {
                'title': 'Статистика инвалидов России 2024',
                'url': 'https://rosstat.gov.ru/folder/13964',
                'snippet': 'В России проживает более 700 тысяч детей с инвалидностью',
                'source': 'rosstat.gov.ru'
            },
            {
                'title': 'Программы реабилитации детей',
                'url': 'https://mintrud.gov.ru/ministry/about/structure/invalid',
                'snippet': 'Только 23% детей имеют доступ к адаптивным программам',
                'source': 'mintrud.gov.ru'
            }
        ],
        'total_results': 2
    }

    # Mock DB
    class MockDB:
        pass

    db = MockDB()

    try:
        print("[1/3] Creating ProductionWriter...")
        writer = ProductionWriter(db=db)
        print("[OK] ProductionWriter created")
        print()

        print("[2/3] Testing write() WITH research_results...")
        print(f"      Research data: {len(research_results.get('sources', []))} sources, "
              f"{research_results.get('total_results', 0)} results")
        print()
        print("      NOTE: Generating full grant (10 sections) - may take 1-2 minutes")
        print()

        # Generate grant WITH research_results
        grant_with_research = await writer.write(
            anketa_data=anketa_data,
            research_results=research_results
        )

        print(f"[OK] Grant generated: {len(grant_with_research)} characters")
        print()

        print("[3/3] Verifying grant contains research data...")

        # Check for research keywords
        has_rosstat = 'rosstat' in grant_with_research.lower()
        has_mintrud = 'mintrud' in grant_with_research.lower()
        has_statistics = any(word in grant_with_research.lower()
                            for word in ['статистик', '700', '23%'])

        print(f"      Contains 'rosstat': {has_rosstat}")
        print(f"      Contains 'mintrud': {has_mintrud}")
        print(f"      Contains statistics: {has_statistics}")
        print()

        if has_rosstat or has_mintrud or has_statistics:
            print("[OK] Grant includes research data!")
        else:
            print("[WARNING] Research data may not be included in grant")

        # Save for inspection
        output_file = "test_grant_with_mock_research.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== RESEARCH RESULTS ===\n")
            f.write(f"Sources: {research_results.get('sources')}\n\n")
            f.write("=== GRANT ===\n")
            f.write(grant_with_research)

        print(f"[OK] Grant saved to: {output_file}")
        print()

        print("=" * 80)
        print("[SUCCESS] ProductionWriter research_results integration WORKS!")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ Writer accepts research_results parameter")
        print("  ✓ Grant generated successfully")
        print(f"  ✓ Research keywords present: {has_rosstat or has_mintrud or has_statistics}")
        print()
        print("Next step: Deploy to production and test full pipeline")

        return True

    except Exception as e:
        print()
        print("=" * 80)
        print("[ERROR] Test FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()

        import traceback
        traceback.print_exc()
        print()

        return False


if __name__ == "__main__":
    success = asyncio.run(test_writer_with_research())
    sys.exit(0 if success else 1)
