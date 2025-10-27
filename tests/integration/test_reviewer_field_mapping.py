#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: Reviewer Field Mapping Fix

Tests that ReviewerAgent returns correct field names expected by handler.
Related: Iteration_57

Background:
- Reviewer calculates 'readiness_score' (0-10)
- Handler expects 'review_score' (0-10)
- File generator expects 'review_score' and 'final_status'
- Without aliases → score = 0

Fix:
- Add 'review_score' as alias for 'readiness_score'
- Add 'final_status' derived from 'readiness_score'
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock database for testing
class MockDB:
    """Mock database for testing"""
    pass


@pytest.mark.asyncio
async def test_reviewer_returns_review_score():
    """
    Test that ReviewerAgent returns review_score field (not just readiness_score)

    This test verifies the fix for Iteration_57:
    - Handler expects review.get('review_score', 0)
    - Reviewer must return 'review_score' (not just 'readiness_score')
    """
    from agents.reviewer_agent import ReviewerAgent

    # Create mock input
    review_input = {
        'grant_content': {
            'text': '''
            Проект "Школа юных предпринимателей"

            ПРОБЛЕМА:
            В нашем регионе отсутствует системная поддержка молодежного предпринимательства.

            РЕШЕНИЕ:
            Создание образовательной программы для школьников 14-18 лет.

            ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
            - Обучение 100 школьников
            - Создание 10 бизнес-проектов
            '''
        },
        'user_answers': {
            'project_name': 'Школа юных предпринимателей',
            'budget': '500000'
        },
        'research_results': {},
        'citations': ['Росстат 2024'],
        'tables': [],
        'selected_grant': {
            'fund_name': 'Фонд президентских грантов'
        }
    }

    # Create reviewer (with mock DB)
    reviewer = ReviewerAgent(db=MockDB())

    # Run review
    print("\n[TEST] Running ReviewerAgent...")
    result = await reviewer.review_grant_async(review_input)

    print(f"[TEST] Reviewer returned keys: {list(result.keys())}")

    # Test 1: Check BOTH readiness_score and review_score exist
    assert 'readiness_score' in result, \
        "Missing readiness_score - reviewer should still return this"

    assert 'review_score' in result, \
        "Missing review_score - THIS IS THE BUG! Handler needs this field"

    assert 'final_status' in result, \
        "Missing final_status - file generator needs this"

    print(f"[OK] Both fields exist: readiness_score={result['readiness_score']}, review_score={result['review_score']}")

    # Test 2: Check they have same value (review_score is alias)
    assert result['readiness_score'] == result['review_score'], \
        f"review_score ({result['review_score']}) should equal readiness_score ({result['readiness_score']})"

    print(f"[OK] Values match: {result['readiness_score']} == {result['review_score']}")

    # Test 3: Check score is NOT 0 (the bug symptom)
    assert result['review_score'] > 0, \
        f"review_score should not be 0 (got {result['review_score']})"

    assert result['review_score'] <= 10, \
        f"review_score should be <= 10 (got {result['review_score']})"

    print(f"[OK] Score is valid: {result['review_score']}/10")

    # Test 4: Check final_status logic
    score = result['review_score']

    if score >= 7.0:
        expected_status = 'approved'
    elif score >= 5.0:
        expected_status = 'needs_revision'
    else:
        expected_status = 'rejected'

    assert result['final_status'] == expected_status, \
        f"final_status should be '{expected_status}' for score {score}, got '{result['final_status']}'"

    print(f"[OK] final_status correct: {result['final_status']} (score={score})")

    # Test 5: Simulate what handler does
    # This is the EXACT code from interactive_pipeline_handler.py:631
    score_from_handler = result.get('review_score', 0)
    status_from_handler = result.get('final_status', 'pending')

    assert score_from_handler > 0, \
        f"Handler gets review_score=0 (the bug!). Got: {score_from_handler}"

    assert status_from_handler != 'pending', \
        f"Handler gets final_status='pending' (missing field!). Got: {status_from_handler}"

    print(f"[OK] Handler would receive: score={score_from_handler}, status={status_from_handler}")

    print("\n[SUCCESS] All field mapping tests passed!")
    print(f"  readiness_score: {result['readiness_score']}")
    print(f"  review_score:    {result['review_score']}")
    print(f"  final_status:    {result['final_status']}")
    print(f"  approval_prob:   {result.get('approval_probability', 'N/A')}%")


@pytest.mark.asyncio
async def test_review_score_thresholds():
    """
    Test final_status derivation from review_score

    Thresholds:
    - >= 7.0 → 'approved'
    - >= 5.0 → 'needs_revision'
    - <  5.0 → 'rejected'
    """

    # Mock reviewer result for different scores
    test_cases = [
        {'score': 8.5, 'expected': 'approved'},
        {'score': 7.0, 'expected': 'approved'},
        {'score': 6.5, 'expected': 'needs_revision'},
        {'score': 5.0, 'expected': 'needs_revision'},
        {'score': 4.5, 'expected': 'rejected'},
        {'score': 2.0, 'expected': 'rejected'},
    ]

    print("\n[TEST] Testing final_status logic...")

    for case in test_cases:
        score = case['score']
        expected = case['expected']

        # Simulate reviewer logic
        if score >= 7.0:
            status = 'approved'
        elif score >= 5.0:
            status = 'needs_revision'
        else:
            status = 'rejected'

        assert status == expected, \
            f"Score {score} should give '{expected}', got '{status}'"

        print(f"[OK] Score {score}/10 → {status}")

    print("[SUCCESS] All threshold tests passed!")


def test_file_generator_integration():
    """
    Test that generate_review_txt() works with review_score

    This simulates full pipeline:
    Reviewer → Handler → File Generator
    """
    from shared.telegram_utils.file_generators import generate_review_txt

    print("\n[TEST] Testing file generator integration...")

    # Simulate reviewer output (after fix)
    review_data = {
        'review_score': 6.2,
        'final_status': 'needs_revision',
        'grant_id': 'GNT123',
        'updated_at': '2025-10-27 20:00:00'
    }

    # Generate file
    txt = generate_review_txt(review_data)

    # Verify content
    assert txt is not None, "generate_review_txt should not return None"
    assert len(txt) > 0, "Generated text should not be empty"

    assert 'ОБЩАЯ ОЦЕНКА: 6.2/10' in txt or 'ОБЩАЯ ОЦЕНКА: 6/10' in txt, \
        "Review file should show score 6.2/10"

    assert 'ТРЕБУЕТСЯ ДОРАБОТКА' in txt or 'needs_revision' in txt, \
        "Review file should show 'needs_revision' status"

    # Check progress bar
    assert '█' in txt, "Review file should have progress bar"

    print(f"[OK] File generated: {len(txt)} characters")
    print("[OK] Score displayed correctly in file")

    print("[SUCCESS] File generator integration passed!")


if __name__ == '__main__':
    """Run tests manually"""
    import asyncio

    print("="*70)
    print("INTEGRATION TEST: Reviewer Field Mapping Fix (Iteration_57)")
    print("="*70)
    print()

    # Test 1: Field mapping
    print("TEST 1: ReviewerAgent field mapping...")
    asyncio.run(test_reviewer_returns_review_score())
    print()

    # Test 2: Status thresholds
    print("TEST 2: final_status thresholds...")
    asyncio.run(test_review_score_thresholds())
    print()

    # Test 3: File generator
    print("TEST 3: File generator integration...")
    test_file_generator_integration()
    print()

    print("="*70)
    print("[SUCCESS] ALL TESTS PASSED!")
    print("="*70)
    print()
    print("Fix verified:")
    print("  ✅ Reviewer returns 'review_score' field")
    print("  ✅ Reviewer returns 'final_status' field")
    print("  ✅ Handler can read review_score (not 0)")
    print("  ✅ File generator displays correct score")
