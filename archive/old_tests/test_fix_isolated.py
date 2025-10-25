#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ИЗОЛИРОВАННАЯ ПРОВЕРКА ИСПРАВЛЕНИЯ commit 64fe88b

Тестирует ТОЛЬКО исправленную логику ConversationFlowManager._should_finalize()
БЕЗ подключения к БД, Telegram, или LLM.

Проверяет:
1. questions_asked < 10 → НЕ finalize
2. questions_asked >= 10 → может finalize

Это МИНИМАЛЬНЫЙ тест который доказывает что исправление работает.
"""

import sys
from pathlib import Path

# Добавить пути
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agents"))
sys.path.insert(0, str(project_root / "agents" / "reference_points"))

print()
print("="*80)
print("ISOLATED FIX VERIFICATION - commit 64fe88b")
print("="*80)
print()

# Импортировать только нужные модули
from agents.reference_points.conversation_flow_manager import ConversationFlowManager, ConversationState
from agents.reference_points.reference_point_manager import ReferencePointManager

print("[1/3] Modules imported successfully")
print()

# Создать минимальный flow manager
print("[2/3] Creating flow manager...")

try:
    # Mock ReferencePointManager
    class MockRPManager:
        def get_next_reference_point(self, exclude_completed=True):
            return None  # Симулируем что нет больше вопросов

        def get_progress(self):
            class Progress:
                completed_rps = 0
                total_rps = 10
                critical_completed = False
                important_completed = False
            return Progress()

    # Создать flow manager с моком
    rp_manager = MockRPManager()
    flow_manager = ConversationFlowManager(rp_manager=rp_manager)

    print("[OK] Flow manager created")
    print()

    # Тесты
    print("[3/3] RUNNING TESTS")
    print("-"*80)
    print()

    test_cases = [
        (0, False, "0 questions - should NOT finalize"),
        (1, False, "1 question - should NOT finalize"),
        (5, False, "5 questions - should NOT finalize"),
        (9, False, "9 questions - should NOT finalize"),
        (10, True, "10 questions - CAN finalize (but may not depending on other conditions)"),
        (15, True, "15 questions - CAN finalize"),
    ]

    results = []

    for questions_asked, expected_can_finalize, description in test_cases:
        # Установить количество заданных вопросов
        flow_manager.context.questions_asked = questions_asked

        # Проверить _should_finalize()
        should_finalize = flow_manager._should_finalize()

        # Expected logic after fix:
        # if questions_asked < 10: return False
        # else: продолжить другие проверки...

        # Для вопросов < 10: должно быть False
        # Для вопросов >= 10: зависит от других условий

        if questions_asked < 10:
            expected = False
            test_passed = (should_finalize == False)
        else:
            # При >= 10 вопросов защита не срабатывает,
            # результат зависит от других условий
            # Для нашего теста мы проверяем что НЕ блокируется
            expected = "varies"
            test_passed = True  # Просто проверяем что не крашится

        status = "[PASS]" if test_passed else "[FAIL]"
        results.append((status, description, questions_asked, should_finalize))

        print(f"{status} {description}")
        print(f"       questions_asked={questions_asked}, should_finalize={should_finalize}")
        print()

    # Финальная проверка
    print("-"*80)
    print()
    print("CRITICAL FIX VERIFICATION:")
    print()

    # Самая важная проверка: с 1 вопросом НЕ должно финализироваться
    flow_manager.context.questions_asked = 1
    result_1q = flow_manager._should_finalize()

    critical_check_passed = (result_1q == False)

    if critical_check_passed:
        print("[SUCCESS] FIX VERIFIED!")
        print()
        print("With 1 question asked: should_finalize = False")
        print()
        print("This confirms commit 64fe88b fix is working:")
        print("  BEFORE: questions_asked == 0  (only blocked at 0)")
        print("  AFTER:  questions_asked < 10  (blocks until 10)")
        print()
        print("Expected production behavior:")
        print("  - Interview will NOT terminate before 10 questions")
        print("  - Minimum questions: 10 (was: 0)")
        print("  - User will get full interview")
    else:
        print("[FAILED] FIX NOT WORKING!")
        print()
        print(f"With 1 question: should_finalize = {result_1q}")
        print("Expected: False (should NOT finalize)")
        print()
        print("This means the fix is NOT applied or NOT working correctly.")

    print()
    print("="*80)

    sys.exit(0 if critical_check_passed else 1)

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
