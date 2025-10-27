"""
Edge case tests for file_generators module.

These tests catch production bugs that weren't caught by basic smoke tests.
Based on real bugs found in production (Iteration 52 → Iteration 53).

Run with: pytest tests/integration/test_file_generators_edge_cases.py -v
"""

import pytest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# ============================================================
# TEST 1: NULL answers_data (Production Bug Found!)
# ============================================================

@pytest.mark.integration
def test_generate_anketa_txt_with_null_answers_data():
    """
    PRODUCTION BUG: answers_data was NULL in database, but code called .items()

    This test reproduces the bug:
    - Database returned session with answers_data=NULL
    - generate_anketa_txt() tried to call answers_data.items()
    - Result: AttributeError: 'NoneType' object has no attribute 'items'

    Fix: Fallback to interview_data when answers_data is NULL/empty
    """
    from shared.telegram.file_generators import generate_anketa_txt

    # Simulate real production data structure
    anketa_data = {
        'anketa_id': 'anketa_606_1761527391',
        'project_name': 'Тестовый проект',
        'completed_at': datetime.now(),
        'answers_data': None,  # ← NULL in database!
        'interview_data': {  # ← Real data is here
            'problem_description': 'Нужно решить проблему',
            'target_audience': 'Молодежь 10-21',
            'project_goal': 'Развитие спорта',
            'budget_total': '750000'
        }
    }

    # Should NOT crash
    result = generate_anketa_txt(anketa_data)

    # Verify it worked
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0

    # Should contain data from interview_data
    assert 'Нужно решить проблему' in result
    assert 'Молодежь 10-21' in result

    print("✅ NULL answers_data handled correctly with fallback to interview_data")


# ============================================================
# TEST 2: Empty answers_data dict
# ============================================================

@pytest.mark.integration
def test_generate_anketa_txt_with_empty_answers_data():
    """
    Test handling of empty answers_data dict.
    Should fallback to interview_data.
    """
    from shared.telegram.file_generators import generate_anketa_txt

    anketa_data = {
        'anketa_id': 'test_empty',
        'project_name': 'Проект с пустыми ответами',
        'completed_at': datetime.now(),
        'answers_data': {},  # ← Empty dict
        'interview_data': {
            'problem': 'Test problem',
            'solution': 'Test solution'
        }
    }

    result = generate_anketa_txt(anketa_data)

    assert result is not None
    assert 'Test problem' in result
    assert 'Test solution' in result

    print("✅ Empty answers_data handled correctly")


# ============================================================
# TEST 3: Invalid JSON string in answers_data
# ============================================================

@pytest.mark.integration
def test_generate_anketa_txt_with_invalid_json_string():
    """
    Test handling of invalid JSON string in answers_data.
    Should gracefully handle parse errors.
    """
    from shared.telegram.file_generators import generate_anketa_txt

    anketa_data = {
        'anketa_id': 'test_invalid_json',
        'project_name': 'Проект с некорректным JSON',
        'completed_at': datetime.now(),
        'answers_data': '{invalid json syntax}',  # ← Invalid JSON
        'interview_data': {
            'problem': 'Backup data'
        }
    }

    # Should NOT crash on JSON parse error
    result = generate_anketa_txt(anketa_data)

    assert result is not None
    assert isinstance(result, str)

    print("✅ Invalid JSON string handled gracefully")


# ============================================================
# TEST 4: Missing interview_data AND answers_data
# ============================================================

@pytest.mark.integration
def test_generate_anketa_txt_with_no_data():
    """
    Test handling when both answers_data and interview_data are missing.
    Should generate file with minimal information.
    """
    from shared.telegram.file_generators import generate_anketa_txt

    anketa_data = {
        'anketa_id': 'test_no_data',
        'project_name': 'Минимальная анкета',
        'completed_at': datetime.now()
        # No answers_data or interview_data
    }

    # Should NOT crash
    result = generate_anketa_txt(anketa_data)

    assert result is not None
    assert 'test_no_data' in result
    assert 'Минимальная анкета' in result
    assert 'Всего вопросов: 0' in result

    print("✅ Missing data handled with minimal output")


# ============================================================
# TEST 5: Valid JSON string in answers_data
# ============================================================

@pytest.mark.integration
def test_generate_anketa_txt_with_valid_json_string():
    """
    Test that valid JSON string is properly parsed.
    """
    from shared.telegram.file_generators import generate_anketa_txt
    import json

    answers = {
        'problem': 'JSON проблема',
        'solution': 'JSON решение',
        'budget': '500000'
    }

    anketa_data = {
        'anketa_id': 'test_json_string',
        'project_name': 'Проект с JSON строкой',
        'completed_at': datetime.now(),
        'answers_data': json.dumps(answers)  # ← Valid JSON string
    }

    result = generate_anketa_txt(anketa_data)

    assert 'JSON проблема' in result
    assert 'JSON решение' in result
    assert '500000' in result

    print("✅ Valid JSON string parsed correctly")


# ============================================================
# TEST 6: All new field labels (from Iteration 53 fix)
# ============================================================

@pytest.mark.integration
def test_generate_anketa_txt_with_all_new_fields():
    """
    Test that all new field labels added in Iteration 53 work correctly.
    """
    from shared.telegram.file_generators import generate_anketa_txt

    anketa_data = {
        'anketa_id': 'test_all_fields',
        'project_name': 'Полная анкета',
        'completed_at': datetime.now(),
        'answers_data': {
            'problem_description': 'Детальное описание проблемы',
            'team_description': 'Описание команды проекта',
            'budget_total': '1000000',
            'budget_breakdown': 'Детализация бюджета',
            'project_goal': 'Цель проекта',
            'methodology': 'Методология реализации',
            'risks': 'Риски проекта',
            'sustainability': 'Устойчивость проекта'
        }
    }

    result = generate_anketa_txt(anketa_data)

    # Check all new labels appear
    assert 'Описание проблемы:' in result
    assert 'Описание команды:' in result
    assert 'Общий бюджет:' in result
    assert 'Структура бюджета:' in result
    assert 'Цель проекта:' in result
    assert 'Методология:' in result
    assert 'Риски:' in result
    assert 'Устойчивость:' in result

    # Check all values appear
    assert 'Детальное описание проблемы' in result
    assert '1000000' in result

    print("✅ All new field labels working correctly")


# ============================================================
# TEST 7: Non-dict type in answers_data
# ============================================================

@pytest.mark.integration
def test_generate_anketa_txt_with_list_instead_of_dict():
    """
    Test handling when answers_data is a list instead of dict.
    Should handle gracefully without crashing.
    """
    from shared.telegram.file_generators import generate_anketa_txt

    anketa_data = {
        'anketa_id': 'test_wrong_type',
        'project_name': 'Проект с неправильным типом',
        'completed_at': datetime.now(),
        'answers_data': ['item1', 'item2'],  # ← List instead of dict!
        'interview_data': {
            'problem': 'Fallback problem'
        }
    }

    # Should NOT crash
    result = generate_anketa_txt(anketa_data)

    assert result is not None
    # Should fallback to interview_data
    assert 'Fallback problem' in result

    print("✅ Non-dict type handled gracefully")


# ============================================================
# TEST 8: Special characters in data
# ============================================================

@pytest.mark.integration
def test_generate_anketa_txt_with_special_characters():
    """
    Test that special characters (Cyrillic, quotes, newlines) are handled.
    """
    from shared.telegram.file_generators import generate_anketa_txt

    anketa_data = {
        'anketa_id': 'test_special_chars',
        'project_name': 'Проект "Кавычки" и\nПереносы',
        'completed_at': datetime.now(),
        'answers_data': {
            'problem': 'Проблема с "кавычками" и спецсимволами: №, %, &',
            'solution': 'Решение\nс переносами\nстрок'
        }
    }

    result = generate_anketa_txt(anketa_data)

    assert '"Кавычки"' in result
    assert 'спецсимволами: №, %, &' in result

    print("✅ Special characters handled correctly")


# ============================================================
# TEST 9: Very long text values
# ============================================================

@pytest.mark.integration
def test_generate_anketa_txt_with_long_text():
    """
    Test handling of very long text values (stress test).
    """
    from shared.telegram.file_generators import generate_anketa_txt

    long_text = "А" * 10000  # 10K characters

    anketa_data = {
        'anketa_id': 'test_long_text',
        'project_name': 'Проект с длинным текстом',
        'completed_at': datetime.now(),
        'answers_data': {
            'problem': long_text,
            'solution': 'Short solution'
        }
    }

    # Should handle long text without issues
    result = generate_anketa_txt(anketa_data)

    assert len(result) > 10000
    assert long_text in result

    print("✅ Long text handled correctly")


# ============================================================
# TEST 10: Production data structure (Real example)
# ============================================================

@pytest.mark.integration
def test_generate_anketa_txt_with_real_production_data():
    """
    Test with REAL production data structure from anketa_606_1761527391.
    This is the exact data that caused the production bug.
    """
    from shared.telegram.file_generators import generate_anketa_txt

    # Real production data
    anketa_data = {
        'anketa_id': 'anketa_606_1761527391',
        'project_name': 'Лучный клуб',
        'completed_at': '2025-10-27 08:09:51',
        'answers_data': None,  # ← This was the bug!
        'interview_data': {
            'risks': 'не дадут денег',
            'partners': 'Лига стрельбы из лука Кемерово, Федерация стрельбы из лука Кузбасса',
            'methodology': 'Организовать мастер-классы, провести информационную компанию',
            'budget_total': '750000',
            'project_goal': 'Хотим приобщить детей и молодёжь к стрельбе из лука',
            'sustainability': 'Лучный клуб готов и дальше работать над развитием навыков',
            'target_audience': 'Дети и молодёжь 10-21 лет',
            'budget_breakdown': '750000',
            'expected_results': 'Спортивно-патриотическое воспитание детей и молодежи',
            'team_description': 'Клуб Луки стрелы',
            'problem_description': 'Уроки физры не могут в полной мере привлечь детей к спорту'
        }
    }

    # This used to crash with: 'NoneType' object has no attribute 'items'
    result = generate_anketa_txt(anketa_data)

    # Verify all real data is present
    assert 'anketa_606_1761527391' in result
    assert 'Лучный клуб' in result
    assert 'не дадут денег' in result
    assert 'Лига стрельбы из лука Кемерово' in result
    assert '750000' in result
    assert 'Дети и молодёжь 10-21 лет' in result

    # Verify correct field labels
    assert 'Риски:' in result
    assert 'Партнеры:' in result
    assert 'Цель проекта:' in result
    assert 'Описание проблемы:' in result

    print("✅ Real production data handled correctly!")
    print(f"   Generated file length: {len(result)} chars")


# ============================================================
# Helper to run all tests
# ============================================================

if __name__ == "__main__":
    """
    Run tests directly:
    python tests/integration/test_file_generators_edge_cases.py
    """
    pytest.main([__file__, "-v", "-s"])
