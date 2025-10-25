#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test AnketaValidator with GigaChat"""

import sys
import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add paths
sys.path.insert(0, 'C:/SnowWhiteAI/GrantService')
sys.path.insert(0, 'C:/SnowWhiteAI/GrantService/shared')

from agents.anketa_validator import AnketaValidator

# Test data - same as create_test_anketa()
test_anketa = {
    'project_name': 'Молодежный образовательный центр "Цифровое будущее"',
    'organization': 'АНО "Развитие молодежных инициатив"',
    'region': 'Кемеровская область - Кузбасс',
    'problem': """В Кемеровской области наблюдается острый дефицит доступных образовательных
    программ по цифровым технологиям для молодежи из малых городов. Согласно данным
    регионального министерства образования, только 15% молодых людей в возрасте 14-25 лет
    имеют доступ к качественному обучению в сфере IT. Это приводит к оттоку талантливой
    молодежи в крупные города и снижению инновационного потенциала региона.""",
    'solution': """Создание молодежного образовательного центра с бесплатными курсами по
    программированию, веб-дизайну, и цифровому маркетингу. Центр будет оснащен современным
    оборудованием и работать на базе местного ДК.""",
    'goals': [
        'Обучить 200 молодых людей цифровым навыкам за год',
        'Создать 3 постоянные образовательные программы',
        'Организовать стажировки для 50 выпускников в местных IT-компаниях'
    ],
    'activities': [
        'Запуск курсов по программированию (Python, JavaScript)',
        'Мастер-классы по веб-дизайну',
        'Хакатоны и командные проекты',
        'Встречи с IT-специалистами',
        'Организация стажировок'
    ],
    'results': [
        '200 обученных молодых людей',
        '50 трудоустроенных выпускников',
        'Снижение оттока молодежи на 15%'
    ],
    'budget': '850000',
    'budget_breakdown': {
        'equipment': '300000',
        'teachers': '400000',
        'materials': '100000',
        'other': '50000'
    }
}

async def test_gigachat_direct():
    """Test 1: GigaChat API works"""
    print("\n" + "="*60)
    print("TEST 1: GigaChat API Direct")
    print("="*60)

    try:
        from shared.llm.unified_llm_client import UnifiedLLMClient

        client = UnifiedLLMClient(provider='gigachat')
        async with client:
            result = await client.generate_text(
                prompt='Привет! Ответь одним словом: OK',
                max_tokens=50
            )

        print(f"[OK] GigaChat response: {result[:100]}")
        return True
    except Exception as e:
        print(f"[FAIL] GigaChat API failed: {e}")
        return False

async def test_validator_basic():
    """Test 2: AnketaValidator required fields check"""
    print("\n" + "="*60)
    print("TEST 2: AnketaValidator Basic Checks (No LLM)")
    print("="*60)

    try:
        validator = AnketaValidator(llm_provider='gigachat')

        # Test required fields
        missing = validator._check_required_fields(test_anketa)
        print(f"Missing fields: {missing if missing else 'None (OK)'}")

        # Test min lengths
        violations = validator._check_minimum_lengths(test_anketa)
        if violations:
            print(f"Length violations:")
            for v in violations:
                print(f"  - {v['field']}: {v['current']}/{v['required']} chars")
        else:
            print("No length violations (OK)")

        return len(missing) == 0 and len(violations) == 0
    except Exception as e:
        print(f"[FAIL] Basic checks failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_validator_full():
    """Test 3: Full AnketaValidator with LLM"""
    print("\n" + "="*60)
    print("TEST 3: Full AnketaValidator (With LLM)")
    print("="*60)

    try:
        validator = AnketaValidator(llm_provider='gigachat')

        print("Running full validation...")
        result = await validator.validate(test_anketa)

        print(f"\n[RESULT]")
        print(f"  Score: {result['score']:.1f}/10")
        print(f"  Valid: {result['valid']}")
        print(f"  Can Proceed: {result['can_proceed']}")
        print(f"  Status: {result.get('details', {}).get('llm_assessment', {}).get('can_proceed', 'N/A')}")

        if result['issues']:
            print(f"\n  Issues ({len(result['issues'])}):")
            for i, issue in enumerate(result['issues'][:5], 1):
                print(f"    {i}. {issue}")

        if result['recommendations']:
            print(f"\n  Recommendations ({len(result['recommendations'])}):")
            for i, rec in enumerate(result['recommendations'][:5], 1):
                print(f"    {i}. {rec}")

        # Success if score >= 5.0
        success = result['score'] >= 5.0

        if success:
            print(f"\n[OK] Validation passed with score {result['score']:.1f}/10")
        else:
            print(f"\n[FAIL] Validation score too low: {result['score']:.1f}/10")

        return success
    except Exception as e:
        print(f"[FAIL] Full validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("="*60)
    print("ANKETA VALIDATOR TEST SUITE")
    print("="*60)

    results = {}

    # Test 1: GigaChat
    results['gigachat'] = await test_gigachat_direct()

    # Test 2: Basic checks
    results['basic'] = await test_validator_basic()

    # Test 3: Full validation (only if GigaChat works)
    if results['gigachat']:
        results['full'] = await test_validator_full()
    else:
        print("\n[SKIP] Skipping full validation test (GigaChat not available)")
        results['full'] = False

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"1. GigaChat API:        {'[OK]' if results['gigachat'] else '[FAIL]'}")
    print(f"2. Basic Checks:        {'[OK]' if results['basic'] else '[FAIL]'}")
    print(f"3. Full Validation:     {'[OK]' if results['full'] else '[FAIL]'}")

    all_pass = all(results.values())
    print(f"\nOVERALL: {'[PASS]' if all_pass else '[FAIL]'}")

    if all_pass:
        print("\n✅ AnketaValidator ready for production!")
    else:
        print("\n❌ Issues found - check logs above")

if __name__ == "__main__":
    asyncio.run(main())
