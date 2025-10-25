#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Fallback Strategy - проверка решения infinite loop

Цель: Проверить что система не зацикливается когда все RP покрыты,
      но questions_asked < MIN_QUESTIONS (10)

Ожидаемое поведение:
1. Система задаёт вопросы по всем RP (2 RP в тесте)
2. После покрытия всех RP, но questions_asked < 10
3. Система использует fallback_questions
4. Задаёт дополнительные вопросы до достижения MIN_QUESTIONS
5. Завершает интервью gracefully

Created: 2025-10-21
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import logging
from agents.reference_points.conversation_flow_manager import ConversationFlowManager
from agents.reference_points.reference_point_manager import ReferencePointManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_fallback_strategy():
    """
    Тест fallback стратегии
    """
    print("\n" + "="*60)
    print("ТЕСТ: Fallback Strategy для Infinite Loop Problem")
    print("="*60)

    # 1. Создать минимальный набор RP (2 штуки)
    print("\n[1] Создаём минимальный набор из 2 RP...")

    from agents.reference_points.reference_point import ReferencePoint

    rp_manager = ReferencePointManager()

    # Добавить 2 простых RP
    from agents.reference_points.reference_point import ReferencePointPriority

    rp1 = ReferencePoint(
        id="rp_001_test_problem",
        name="Проблема",
        description="Понять какую проблему решает проект",
        priority=ReferencePointPriority.P0_CRITICAL,
        required=True,
        question_hints=["Какую проблему решает ваш проект?"],
        tags=["problem"]
    )

    rp2 = ReferencePoint(
        id="rp_002_test_solution",
        name="Решение",
        description="Понять как проект решает проблему",
        priority=ReferencePointPriority.P0_CRITICAL,
        required=True,
        question_hints=["Как вы планируете решить эту проблему?"],
        tags=["solution"]
    )

    # reference_points должен быть dict, не list
    rp_manager.reference_points = {
        rp1.id: rp1,
        rp2.id: rp2
    }
    print(f"[OK] Добавлено {len(rp_manager.reference_points)} RP")

    # 2. Создать flow manager
    print("\n[2] Создаём ConversationFlowManager...")
    flow = ConversationFlowManager(rp_manager)
    print(f"[OK] FlowManager создан, fallback_bank: {flow.fallback_bank}")

    # 3. Симуляция диалога
    print("\n[3] Симуляция диалога...")
    print("-"*60)

    turn = 1
    max_turns = 20  # Защита от бесконечного цикла

    while turn <= max_turns:
        print(f"\n--- Turn {turn} ---")

        # Получить следующее действие
        action = flow.decide_next_action()

        print(f"State: {flow.context.current_state.value}")
        print(f"Action: {action['type']}")
        print(f"Transition: {action['transition'].value}")
        print(f"Questions asked: {flow.context.questions_asked}")
        print(f"Using fallback: {flow.context.using_fallback}")

        # Проверка завершения
        if action['type'] == 'finalize':
            print(f"\n[FINALIZE] {action['message']}")
            print(f"Total questions asked: {flow.context.questions_asked}")

            # Проверить что задано >= 10 вопросов
            if flow.context.questions_asked >= 10:
                print("\n[OK] SUCCESS - Asked >= 10 questions before finalize")
                return True
            else:
                print(f"\n[FAIL] FAILED - Only {flow.context.questions_asked} questions asked!")
                return False

        # Получить RP
        rp = action['reference_point']
        print(f"RP: {rp.id} - {rp.name}")

        # Проверить fallback
        if rp.id.startswith('rp_fallback_'):
            question = rp.question_hints[0] if rp.question_hints else "N/A"
            print(f"[FALLBACK] Using fallback question: {question[:60]}...")

        # Симуляция ответа
        question_text = rp.question_hints[0] if rp.question_hints else f"Вопрос о {rp.name}"
        mock_answer = f"Ответ на вопрос о {rp.name}. " * 3

        # Добавить в историю (это увеличивает questions_asked)
        flow.context.add_turn(
            question=question_text,
            answer=mock_answer,
            rp_id=rp.id
        )

        # Обработать ответ
        flow.decide_next_action(last_answer=mock_answer)

        turn += 1

    # Если достигли max_turns - ошибка
    print(f"\n[FAIL] TIMEOUT - Reached {max_turns} turns without finalize")
    print("This indicates infinite loop is NOT fixed!")
    return False


def test_fallback_question_uniqueness():
    """
    Тест уникальности fallback вопросов
    """
    print("\n" + "="*60)
    print("ТЕСТ: Уникальность Fallback Questions")
    print("="*60)

    from agents.reference_points.fallback_questions import get_fallback_bank

    fallback_bank = get_fallback_bank()

    # Статистика
    stats = fallback_bank.get_question_count()
    print(f"\n[Stats]")
    print(f"DB questions: {stats['db_questions']} (required: {stats['db_required']}, optional: {stats['db_optional']})")
    print(f"Hardcoded categories: {stats['hardcoded_categories']}")
    print(f"Hardcoded total: {stats['hardcoded_total']}")

    total_available = stats['db_questions'] + stats['hardcoded_total']
    print(f"\nTotal available questions: {total_available}")

    if total_available < 10:
        print(f"[WARN] Only {total_available} questions available - may not be enough!")

    # Тест получения уникальных вопросов
    print("\n[Test] Getting 15 unique questions...")
    used_questions = []

    for i in range(15):
        question = fallback_bank.get_fallback_question(
            category="problem",
            used_questions=used_questions
        )

        if question in used_questions:
            print(f"[FAIL] Question {i+1} is duplicate: {question[:50]}...")
            return False

        used_questions.append(question)
        print(f"Q{i+1}: {question[:60]}...")

    print(f"\n[OK] All 15 questions are unique!")
    return True


def main():
    """Запуск всех тестов"""
    print("\n" + "="*60)
    print("FALLBACK STRATEGY INTEGRATION TEST")
    print("="*60)

    # Тест 1: Уникальность вопросов
    print("\n" + "="*60)
    result1 = test_fallback_question_uniqueness()
    print("="*60)

    # Тест 2: Fallback стратегия
    print("\n" + "="*60)
    result2 = test_fallback_strategy()
    print("="*60)

    # Итого
    print("\n" + "="*60)
    print("TEST RESULTS:")
    print("="*60)
    print(f"Uniqueness Test: {'[OK] PASSED' if result1 else '[FAIL] FAILED'}")
    print(f"Fallback Strategy Test: {'[OK] PASSED' if result2 else '[FAIL] FAILED'}")

    if result1 and result2:
        print("\n[OK] ALL TESTS PASSED!")
        print("Infinite loop problem should be FIXED")
        return 0
    else:
        print("\n[FAIL] SOME TESTS FAILED")
        print("Infinite loop problem is NOT fixed yet")
        return 1


if __name__ == "__main__":
    sys.exit(main())
