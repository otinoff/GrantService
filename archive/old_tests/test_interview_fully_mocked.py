#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛНОСТЬЮ ЗАМОКИРОВАННЫЙ ТЕСТ InteractiveInterviewer

НЕ ТРЕБУЕТ:
- Telegram подключения
- Реальной базы данных
- Интернета

ИСПОЛЬЗУЕТ:
- unittest.mock для мокирования БД
- Прямой вызов агента
- Симулированные ответы пользователя

Цель: Проверить что InteractiveInterviewer задаёт >=10 вопросов
      и ставит оценку >0 после исправления commit 64fe88b

Based on: pytest + SQLAlchemy mocking best practices (web search 2025-10-21)
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json

# Path setup
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "agents"))

# Mock database BEFORE any imports that might use it
class MockDatabase:
    """Mock database that pretends to work but does nothing"""

    def __init__(self, *args, **kwargs):
        print("[MOCK DB] Created mock database connection")
        self.connected = True

    def save_application(self, telegram_id: int, data: dict, audit_score: float, audit_status: str):
        """Mock save - just log it"""
        print(f"[MOCK DB] save_application called:")
        print(f"           telegram_id={telegram_id}")
        print(f"           audit_score={audit_score}")
        print(f"           audit_status={audit_status}")
        print(f"           data keys={list(data.keys())}")
        return {"id": 12345, "success": True}

    def get_user_by_telegram_id(self, telegram_id: int):
        """Mock user lookup"""
        return {
            "id": 1,
            "telegram_id": telegram_id,
            "username": "test_user",
            "settings": {}
        }

    def close(self):
        print("[MOCK DB] Closed connection")


# Patch database import
sys.modules['data.database'] = MagicMock()
sys.modules['data.database.db'] = MagicMock()


# Now safe to import agent
from agents.interactive_interviewer_agent import InteractiveInterviewerAgentV2


# Test answers
TEST_ANSWERS = {
    1: "Лучные клубы для детей в Кемерово",
    2: "Развивать стрельбу из лука как спорт среди молодёжи",
    3: "Мало доступных спортивных секций для детей",
    4: "Дети и подростки 10-17 лет",
    5: "Кемерово, Кемеровская область",
    6: "Закупить оборудование и обучить тренеров",
    7: "Групповые тренировки 3 раза в неделю",
    8: "100 детей пройдут обучение в первый год",
    9: "500000 рублей на весь проект",
    10: "Оборудование 300к, тренер 150к, аренда 50к",
    11: "Опытный тренер с 10-летним стажем",
    12: "Школа №5, спортивный комплекс Олимп",
    13: "Активная реклама в школах и работа с родителями",
    14: "Абонплата от родителей и местные спонсоры",
    15: "12 месяцев на полную реализацию",
    16: "Дополнительная информация о партнёрах",
    17: "Планируем участие в соревнованиях",
    18: "Есть опыт работы с детьми",
    19: "Поддержка от администрации города",
    20: "Долгосрочная устойчивость проекта",
}


class MockUICallback:
    """Mock UI callback that simulates user responses"""

    def __init__(self, answers: dict):
        self.answers = answers
        self.question_count = 0
        self.questions_asked = []

    async def __call__(self, question: str) -> str:
        """Called by agent to ask question"""
        self.question_count += 1
        self.questions_asked.append(question)

        answer = self.answers.get(self.question_count, f"Ответ {self.question_count}")

        print(f"\n[Q{self.question_count:2d}] {question[:80]}...")
        print(f"[A{self.question_count:2d}] {answer}")

        return answer


async def test_fully_mocked():
    """Полностью замокированный тест"""

    print("="*80)
    print("FULLY MOCKED TEST - InteractiveInterviewer")
    print("="*80)
    print()

    # Create mock UI callback
    ui_callback = MockUICallback(TEST_ANSWERS)

    # Mock database connection
    mock_db = MockDatabase()

    print("[1/4] Initializing agent with mocked dependencies...")
    print()

    # Patch database in the agent module
    with patch('agents.interactive_interviewer_agent.db', mock_db):

        # Create agent (will use mocked DB)
        agent = InteractiveInterviewerAgentV2(
            agent_id="test-agent",
            telegram_id=419597164,
            project_context="Тестовый проект лучных клубов"
        )

        print("[OK] Agent created")
        print()

        # Run interview
        print("[2/4] Running interview...")
        print()

        start_time = asyncio.get_event_loop().time()

        try:
            result = await agent.run_interview(ui_callback=ui_callback)

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            print()
            print(f"[OK] Interview completed in {duration:.1f}s")
            print()

        except Exception as e:
            print(f"[ERROR] Interview failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Analyze results
        print("[3/4] Analyzing results...")
        print("-"*80)

        questions_asked = ui_callback.question_count

        print(f"Questions asked: {questions_asked}")
        print(f"Result keys: {list(result.keys())}")

        if 'audit_score' in result:
            print(f"Audit score: {result['audit_score']}/100")

        if 'audit_status' in result:
            print(f"Audit status: {result['audit_status']}")

        if 'recommendations' in result:
            print(f"Recommendations: {len(result.get('recommendations', []))} items")

        print("-"*80)
        print()

        # Checks
        print("[4/4] VERIFICATION CHECKS")
        print("="*80)
        print()

        checks = []

        # Check 1: Minimum questions
        check_questions = questions_asked >= 10
        checks.append(("Asked >=10 questions", check_questions, f"{questions_asked} questions"))

        # Check 2: Audit score exists and >0
        has_score = 'audit_score' in result
        score_value = result.get('audit_score', 0)
        check_score = has_score and score_value > 0
        checks.append(("Audit score >0", check_score, f"{score_value}/100"))

        # Check 3: Has status
        has_status = 'audit_status' in result
        checks.append(("Has audit status", has_status, result.get('audit_status', 'N/A')))

        # Print checks
        for name, passed, details in checks:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{status} {name}: {details}")

        print()
        print("="*80)

        all_passed = all(c[1] for c in checks)

        if all_passed:
            print("[SUCCESS] ALL CHECKS PASSED!")
            print()
            print("InteractiveInterviewer works correctly after fix:")
            print(f"  - Asked {questions_asked} questions (required >=10)")
            print(f"  - Score: {score_value}/100")
            print(f"  - Status: {result.get('audit_status', 'N/A')}")
            print()
            print("[VERIFIED] Fix (commit 64fe88b) working as expected!")
        else:
            print("[FAILED] SOME CHECKS FAILED")
            print()
            print("Problems:")
            for name, passed, details in checks:
                if not passed:
                    print(f"  - {name}: {details}")

        print("="*80)

        return all_passed


if __name__ == "__main__":
    print()
    print("STARTING FULLY MOCKED TEST")
    print("This test requires NO database, NO Telegram, NO internet")
    print()

    success = asyncio.run(test_fully_mocked())

    print()
    sys.exit(0 if success else 1)
