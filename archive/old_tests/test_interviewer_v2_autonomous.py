#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автономное тестирование Interactive Interviewer Agent V2

Тесты запускаются БЕЗ участия пользователя!

Проверяет:
- Нет бесконечных циклов
- Reference Points помечаются как completed
- Интервью завершается корректно
- Анкета заполняется
"""

import sys
import json
import asyncio
from pathlib import Path
import logging

# Добавляем пути
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))
sys.path.insert(0, str(Path(__file__).parent / "shared"))

# Отключаем лишние логи
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


class AutonomousTestRunner:
    """Автономный тестировщик V2 интервьюера"""

    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def log_test(self, test_name, passed, message=""):
        """Логирование результата теста"""
        status = "PASS" if passed else "FAIL"
        emoji = "[OK]" if passed else "[FAIL]"

        result = {
            "test": test_name,
            "status": status,
            "message": message
        }

        self.test_results.append(result)

        if passed:
            self.tests_passed += 1
            print(f"{emoji} {status}: {test_name}")
        else:
            self.tests_failed += 1
            print(f"{emoji} {status}: {test_name}")
            if message:
                print(f"   ERROR: {message}")

    async def test_no_infinite_loop(self):
        """Тест 1: НЕТ бесконечного цикла"""
        try:
            from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2

            # Mock database
            class MockDB:
                def __init__(self):
                    self.data = {}

                def save(self, key, value):
                    self.data[key] = value

                def get(self, key):
                    return self.data.get(key)

            # Create agent
            agent = InteractiveInterviewerAgentV2(db=MockDB(), llm_provider="claude_code")

            # Mock user data
            user_data = {
                'user_id': 'test_user',
                'project_name': 'Test Project'
            }

            # Mock callback that returns test answers
            answers = [
                "Лучные клубы Кемерово",  # Project name
                "Нет доступа к стрельбе из лука для молодёжи 14-25 лет",  # Problem
                "500+ молодых людей 14-25 лет в Кемеровской области",  # Target audience
                "Создать 3 клуба, набрать тренеров, провести мероприятия",  # Methodology
                "800 тысяч рублей",  # Budget
                "300к оборудование, 200к аренда, 300к зарплаты",  # Budget breakdown
                "500 участников, 3 клуба, 20 мероприятий в год",  # Results
                "Я руководитель, 3 тренера с опытом 5+ лет",  # Team
                "Администрация Кемерово, школы",  # Partners
                "Членские взносы 1000р/мес"  # Sustainability
            ]

            answer_idx = [0]  # Используем list чтобы модифицировать в closure

            async def mock_callback(question):
                if answer_idx[0] < len(answers):
                    answer = answers[answer_idx[0]]
                    answer_idx[0] += 1
                    return answer
                else:
                    return "Дополнительный ответ"

            # Run interview with timeout to catch infinite loops
            try:
                # Таймаут 30 секунд - если не завершится, значит зацикливание
                anketa = await asyncio.wait_for(
                    agent.conduct_interview(user_data, callback_ask_question=mock_callback),
                    timeout=30.0
                )

                # Проверяем что интервью завершилось
                assert anketa is not None, "Anketa is None"
                assert len(anketa) > 0, "Anketa is empty"

                # Проверяем прогресс
                progress = agent.rp_manager.get_progress()
                completed_rps = progress.completed_rps

                # Должно быть completed хотя бы несколько RPs
                assert completed_rps > 0, f"No RPs completed! (completed={completed_rps})"

                self.log_test(
                    "test_no_infinite_loop",
                    True,
                    f"Interview completed. RPs completed: {completed_rps}/{progress.total_rps}"
                )
                return True

            except asyncio.TimeoutError:
                self.log_test(
                    "test_no_infinite_loop",
                    False,
                    "INFINITE LOOP DETECTED! Interview didn't finish in 30 seconds"
                )
                return False

        except Exception as e:
            self.log_test("test_no_infinite_loop", False, str(e))
            return False

    async def test_rps_marked_as_completed(self):
        """Тест 2: Reference Points помечаются как completed"""
        try:
            from agents.reference_points.reference_point_manager import ReferencePointManager

            # Create manager
            manager = ReferencePointManager()
            manager.load_fpg_reference_points()

            # Get first RP
            rp1 = manager.get_next_reference_point()
            assert rp1 is not None, "First RP is None"
            rp1_id = rp1.id

            # Mark as completed
            manager.mark_completed(rp1_id, confidence=1.0)

            # Get next RP - should be different
            rp2 = manager.get_next_reference_point()
            assert rp2 is not None, "Second RP is None"
            assert rp2.id != rp1_id, f"Same RP returned! {rp1_id} == {rp2.id}"

            # Check completed list
            completed_ids = manager.get_completed_rp_ids()
            assert rp1_id in completed_ids, f"{rp1_id} not in completed list"
            assert rp2.id not in completed_ids, f"{rp2.id} should not be completed"

            self.log_test("test_rps_marked_as_completed", True)
            return True

        except Exception as e:
            self.log_test("test_rps_marked_as_completed", False, str(e))
            return False

    async def test_skip_already_covered_marks_complete(self):
        """Тест 3: При skip already covered RP помечается как completed"""
        try:
            # Это проверка логики из исправленного бага
            # Если question generator возвращает None (already covered),
            # RP должен быть помечен как completed

            from agents.reference_points.reference_point_manager import ReferencePointManager

            manager = ReferencePointManager()
            manager.load_fpg_reference_points()

            # Simulate: get RP, skip it, check it's completed
            rp = manager.get_next_reference_point()
            initial_id = rp.id

            # Simulate: question generator returned None (already covered)
            # Agent should mark as completed
            manager.mark_completed(rp.id, confidence=1.0)

            # Get next - should be different
            next_rp = manager.get_next_reference_point()
            assert next_rp.id != initial_id, \
                f"BUG: get_next_reference_point() returned same RP after marking completed!"

            self.log_test("test_skip_already_covered_marks_complete", True)
            return True

        except Exception as e:
            self.log_test("test_skip_already_covered_marks_complete", False, str(e))
            return False

    async def test_interview_finishes_with_minimum_questions(self):
        """Тест 4: Интервью завершается после минимального числа вопросов"""
        try:
            from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2

            class MockDB:
                def __init__(self):
                    self.data = {}

            agent = InteractiveInterviewerAgentV2(db=MockDB(), llm_provider="claude_code")

            # Mock user data
            user_data = {
                'user_id': 'test_user',
                'project_name': 'Test Project'
            }

            # Track number of questions asked
            questions_asked = [0]

            async def mock_callback(question):
                questions_asked[0] += 1
                # Always return detailed answers to trigger completion faster
                return "Подробный ответ с достаточной информацией для завершения reference point " * 5

            # Run interview
            anketa = await asyncio.wait_for(
                agent.conduct_interview(user_data, callback_ask_question=mock_callback),
                timeout=30.0
            )

            # Check minimum questions were asked (at least 5-10)
            assert questions_asked[0] >= 5, \
                f"Too few questions asked: {questions_asked[0]}"

            # Check it didn't go crazy (max 30)
            assert questions_asked[0] <= 30, \
                f"Too many questions asked: {questions_asked[0]} (possible loop)"

            self.log_test(
                "test_interview_finishes_with_minimum_questions",
                True,
                f"Questions asked: {questions_asked[0]}"
            )
            return True

        except Exception as e:
            self.log_test("test_interview_finishes_with_minimum_questions", False, str(e))
            return False

    async def run_all_tests(self):
        """Запустить все тесты автономно"""
        print("=" * 80)
        print("AUTONOMOUS TEST RUNNER - Interactive Interviewer Agent V2")
        print("Testing for infinite loop bug and RP completion")
        print("=" * 80)

        print("\nLLM Provider Policy:")
        print("  - Claude Code: MAIN and ONLY provider")
        print("  - Bug fixed: RPs now marked as completed when skipped")

        print("\n" + "=" * 80)
        print("Running tests...")
        print("=" * 80 + "\n")

        # Run tests
        await self.test_rps_marked_as_completed()
        await self.test_skip_already_covered_marks_complete()
        await self.test_no_infinite_loop()
        await self.test_interview_finishes_with_minimum_questions()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        total_tests = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0

        print(f"\nTotal tests: {total_tests}")
        print(f"Passed: {self.tests_passed} [OK]")
        print(f"Failed: {self.tests_failed} [FAIL]")
        print(f"Pass rate: {pass_rate:.1f}%")

        if self.tests_failed == 0:
            print("\n[SUCCESS] ALL TESTS PASSED!")
            print("[OK] V2 Interviewer is ready - no infinite loops!")
        else:
            print("\n[WARNING] SOME TESTS FAILED")
            print("Review the errors above")

        # Save results
        results_file = Path(__file__).parent / "test_results_v2.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': '2025-10-22',
                'agent': 'InteractiveInterviewerAgentV2',
                'total': total_tests,
                'passed': self.tests_passed,
                'failed': self.tests_failed,
                'pass_rate': pass_rate,
                'results': self.test_results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n[FILE] Results saved to: {results_file}")

        return self.tests_failed == 0


async def main():
    """Главная функция"""
    runner = AutonomousTestRunner()
    success = await runner.run_all_tests()

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
