#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test: File Generator Float Fix (Iteration_58 Part 2)
Tests that generate_review_txt handles float scores
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from shared.telegram_utils.file_generators import generate_review_txt

def test_float_score():
    """Test that file generator handles float scores"""

    print("="*70)
    print("QUICK TEST: File Generator Float Fix (Iteration_58 Part 2)")
    print("="*70)
    print()

    # Test Case: Float score (what reviewer returns)
    review_data = {
        'review_score': 0.3,  # ← FLOAT!
        'final_status': 'rejected',
        'grant_id': 'TEST123',
        'updated_at': '2025-10-27 20:35:00'
    }

    try:
        print("[1/2] Testing with float score (0.3)...")
        txt = generate_review_txt(review_data)

        assert txt is not None, "generate_review_txt returned None"
        assert len(txt) > 0, "Generated text is empty"
        assert '0.3/10' in txt, "Score not in text"
        assert '█' in txt or '░' in txt, "Missing progress bar"

        print(f"[OK] File generated: {len(txt)} characters")
        print(f"[OK] Contains score: 0.3/10")
        print(f"[OK] Has progress bar")
        print()

        # Test Case 2: Integer score
        print("[2/2] Testing with integer score (5)...")
        review_data2 = {
            'review_score': 5,  # ← INT!
            'final_status': 'needs_revision'
        }

        txt2 = generate_review_txt(review_data2)
        assert '5/10' in txt2 or '5.0/10' in txt2
        print("[OK] Integer score also works")
        print()

        print("="*70)
        print("[SUCCESS] File generator fix working!")
        print("="*70)
        print()
        print("Fix: int(review_score) before multiplying string")
        print()

        return True

    except Exception as e:
        print()
        print("="*70)
        print("[FAILED] File generator still broken")
        print("="*70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_float_score()
    sys.exit(0 if success else 1)
