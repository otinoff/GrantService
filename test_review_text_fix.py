#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test: Review Text Display Fix (Iteration_58 Part 3)
Tests that file generator displays strengths/weaknesses/recommendations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from shared.telegram_utils.file_generators import generate_review_txt

def test_review_text_display():
    """Test that file generator displays reviewer output correctly"""

    print("="*70)
    print("QUICK TEST: Review Text Display (Iteration_58 Part 3)")
    print("="*70)
    print()

    # Test Case: Reviewer output (what it actually returns)
    review_data = {
        'review_score': 0.3,
        'final_status': 'rejected',
        'grant_id': 'TEST123',
        'updated_at': '2025-10-27 20:45:00',

        # Fields that reviewer returns (lines 288-290 in reviewer_agent.py)
        'strengths': [],  # Empty for 0.3/10 score
        'weaknesses': [
            'Недостаточно цитат (0, нужно 10+)',
            'Недостаточно таблиц (0, нужно 2+)',
            'Отсутствует официальная статистика (Росстат, министерства)'
        ],
        'recommendations': [
            '❌ Заявка требует существенной доработки перед подачей.',
            'Добавьте минимум 10 цитат из надежных источников',
            'Создайте 2+ сравнительные таблицы с данными'
        ]
    }

    try:
        print("[1/2] Testing with low score (0.3/10) - should have weaknesses...")
        txt = generate_review_txt(review_data)

        assert txt is not None, "generate_review_txt returned None"
        assert len(txt) > 0, "Generated text is empty"

        # Check for score
        assert '0.3/10' in txt, "Missing score"

        # Check for weaknesses section
        assert 'СЛАБЫЕ СТОРОНЫ:' in txt, "Missing СЛАБЫЕ СТОРОНЫ section!"
        assert 'Недостаточно цитат' in txt, "Missing weakness text"
        assert 'Недостаточно таблиц' in txt, "Missing weakness text"

        # Check for recommendations section
        assert 'РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:' in txt, "Missing РЕКОМЕНДАЦИИ section!"
        assert 'существенной доработки' in txt, "Missing recommendation text"

        print(f"[OK] File generated: {len(txt)} characters")
        print(f"[OK] Has СЛАБЫЕ СТОРОНЫ section")
        print(f"[OK] Has РЕКОМЕНДАЦИИ section")
        print()

        # Show sample output
        print("Sample output:")
        print("-" * 70)
        for line in txt.split('\n')[15:30]:  # Show middle section
            print(line)
        print("-" * 70)
        print()

        # Test Case 2: High score with strengths
        print("[2/2] Testing with high score (8.5/10) - should have strengths...")
        review_data2 = {
            'review_score': 8.5,
            'final_status': 'approved',
            'strengths': [
                'Сильная доказательная база с официальной статистикой',
                'Хорошая структура с логичной последовательностью',
                'Ясные SMART-цели и индикаторы'
            ],
            'weaknesses': ['Можно улучшить детализацию бюджета'],
            'recommendations': ['✅ Заявка готова к подаче! Высокая вероятность одобрения.']
        }

        txt2 = generate_review_txt(review_data2)
        assert 'СИЛЬНЫЕ СТОРОНЫ:' in txt2, "Missing СИЛЬНЫЕ СТОРОНЫ for high score"
        assert 'Сильная доказательная база' in txt2, "Missing strength text"
        print("[OK] High score shows strengths")
        print()

        print("="*70)
        print("[SUCCESS] Review text display fix working!")
        print("="*70)
        print()
        print("Fix: file_generators now reads strengths/weaknesses/recommendations")
        print("     directly from review_data (not from JSON string)")
        print()

        return True

    except Exception as e:
        print()
        print("="*70)
        print("[FAILED] Review text display still broken")
        print("="*70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_review_text_display()
    sys.exit(0 if success else 1)
