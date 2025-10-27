"""
Integration Test: Audit Recommendations Format Handling

Tests that generate_audit_txt() handles different recommendation formats:
- dict: {'problems': [...], 'suggestions': [...]}
- list: ['problem1', 'problem2']
- string: JSON encoded dict

Related: Iteration_55_Auditor_TypeError_Fix (Part 2)
Issue: AttributeError when recommendations is list instead of dict
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.telegram_utils.file_generators import generate_audit_txt


def test_recommendations_as_dict():
    """Test recommendations as dict (expected format)."""

    audit_result = {
        'overall_score': 6.0,
        'completeness_score': 7.0,
        'quality_score': 5.0,
        'compliance_score': 6.0,
        'can_submit': False,
        'readiness_status': 'Требует доработки',
        'recommendations': {
            'problems': ['Недостаточно деталей о бюджете', 'Нет плана рисков'],
            'suggestions': ['Добавить детализацию', 'Указать метрики']
        }
    }

    txt = generate_audit_txt(audit_result)

    assert txt is not None
    assert 'РЕКОМЕНДАЦИИ:' in txt
    assert 'ПРОБЛЕМЫ:' in txt
    assert 'Недостаточно деталей о бюджете' in txt
    assert 'ПРЕДЛОЖЕНИЯ ПО УЛУЧШЕНИЮ:' in txt
    assert 'Добавить детализацию' in txt

    print("[OK] Dict format: PASSED")


def test_recommendations_as_list():
    """
    Test recommendations as list (REAL Agent format).

    Background:
    - AuditorAgent returns recommendations as list of strings
    - Code tried: list.get('problems') → AttributeError
    - Fixed: Convert list to dict format
    """

    audit_result = {
        'overall_score': 6.0,
        'completeness_score': 7.0,
        'quality_score': 5.0,
        'compliance_score': 6.0,
        'can_submit': False,
        'readiness_status': 'Требует доработки',
        'recommendations': [  # ← List format (as Agent returns)
            'Недостаточно деталей о бюджете',
            'Нет плана рисков',
            'Укажите конкретные метрики'
        ]
    }

    # Should NOT raise AttributeError
    txt = generate_audit_txt(audit_result)

    assert txt is not None
    assert 'РЕКОМЕНДАЦИИ:' in txt
    assert 'ПРОБЛЕМЫ:' in txt
    assert 'Недостаточно деталей о бюджете' in txt
    assert 'Нет плана рисков' in txt
    assert 'Укажите конкретные метрики' in txt

    print("[OK] List format (REAL Agent): PASSED")


def test_recommendations_as_json_string():
    """Test recommendations as JSON string."""

    recommendations_dict = {
        'problems': ['Проблема 1', 'Проблема 2'],
        'suggestions': ['Предложение 1']
    }

    audit_result = {
        'overall_score': 6.0,
        'completeness_score': 7.0,
        'quality_score': 5.0,
        'compliance_score': 6.0,
        'can_submit': False,
        'readiness_status': 'Требует доработки',
        'recommendations': json.dumps(recommendations_dict)  # ← String format
    }

    txt = generate_audit_txt(audit_result)

    assert txt is not None
    assert 'РЕКОМЕНДАЦИИ:' in txt
    assert 'Проблема 1' in txt
    assert 'Предложение 1' in txt

    print("[OK] JSON string format: PASSED")


def test_recommendations_empty_list():
    """Test empty recommendations list."""

    audit_result = {
        'overall_score': 9.0,
        'completeness_score': 9.0,
        'quality_score': 9.0,
        'compliance_score': 9.0,
        'can_submit': True,
        'readiness_status': 'Одобрено',
        'recommendations': []  # Empty list
    }

    txt = generate_audit_txt(audit_result)

    # Should work, but no recommendations section
    assert txt is not None
    # If empty, recommendations section should not appear
    # or appear but be empty

    print("[OK] Empty list: PASSED")


def test_recommendations_none():
    """Test missing recommendations field."""

    audit_result = {
        'overall_score': 8.0,
        'completeness_score': 8.0,
        'quality_score': 8.0,
        'compliance_score': 8.0,
        'can_submit': True,
        'readiness_status': 'Одобрено'
        # No recommendations field
    }

    txt = generate_audit_txt(audit_result)

    assert txt is not None
    # Should work without recommendations

    print("[OK] Missing recommendations: PASSED")


def test_recommendations_invalid_string():
    """Test invalid JSON string."""

    audit_result = {
        'overall_score': 6.0,
        'completeness_score': 7.0,
        'quality_score': 5.0,
        'compliance_score': 6.0,
        'can_submit': False,
        'readiness_status': 'Требует доработки',
        'recommendations': 'not valid json {'  # ← Invalid JSON
    }

    # Should handle gracefully (not crash)
    txt = generate_audit_txt(audit_result)

    assert txt is not None

    print("[OK] Invalid JSON string: PASSED (handled gracefully)")


def test_real_agent_output_structure():
    """
    Test with structure matching REAL production Agent output.

    This is the actual format from production logs.
    """

    # Based on actual AuditorAgent output from production
    audit_result = {
        'overall_score': 5.95,  # Float from handler
        'completeness_score': 7.8,
        'quality_score': 4.2,
        'compliance_score': 6.1,
        'feasibility_score': 8.3,
        'innovation_score': 3.7,
        'can_submit': False,
        'readiness_status': 'Требует доработки',
        'recommendations': [  # Agent returns LIST
            'Добавьте более детальное описание целевой аудитории',
            'Укажите конкретные измеримые показатели результатов',
            'Дополните раздел о рисках и способах их минимизации'
        ],
        'auditor_llm_provider': 'claude'
    }

    # Should work perfectly
    txt = generate_audit_txt(audit_result)

    assert txt is not None
    assert len(txt) > 0

    # Check all components
    assert 'РЕЗУЛЬТАТЫ АУДИТА' in txt or 'Audit Results' in txt
    assert 'ДЕТАЛЬНЫЕ ОЦЕНКИ:' in txt
    assert 'Полнота информации' in txt  # completeness label
    assert 'РЕКОМЕНДАЦИИ:' in txt
    assert 'ПРОБЛЕМЫ:' in txt
    assert 'Добавьте более детальное описание' in txt

    # Check scores with progress bars
    assert '█' in txt  # Has bars
    assert '░' in txt  # Has empty bars
    assert '/10' in txt  # Has score format

    print("[OK] REAL Agent output structure: PASSED")
    print(f"     Generated {len(txt)} chars")


if __name__ == '__main__':
    """Run all tests."""
    print("="*70)
    print("INTEGRATION TEST: Audit Recommendations Format Handling")
    print("="*70)
    print()

    try:
        test_recommendations_as_dict()
        test_recommendations_as_list()
        test_recommendations_as_json_string()
        test_recommendations_empty_list()
        test_recommendations_none()
        test_recommendations_invalid_string()
        test_real_agent_output_structure()

        print()
        print("="*70)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("="*70)
    except Exception as e:
        print()
        print("="*70)
        print(f"[FAILED] TEST FAILED: {e}")
        print("="*70)
        raise
