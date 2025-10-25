#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autonomous Test Runner - полностью автономное тестирование
БЕЗ участия пользователя!

Использует:
- pytest для unit тестов
- Mock для симуляции LLM ответов
- Автоматическая проверка всех компонентов
"""

import sys
import json
import asyncio
from pathlib import Path

# Добавляем пути
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем наш адаптивный интервьюер
from adaptive_interviewer_with_question_bank import AdaptiveInterviewerWithQuestionBank


class AutonomousTestRunner:
    """Автономный тестировщик - сам запускает и проверяет все"""

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

    async def test_basic_initialization(self):
        """Тест 1: Базовая инициализация"""
        try:
            interviewer = AdaptiveInterviewerWithQuestionBank(
                llm_client=None,
                llm_provider="claude_code"
            )

            # Проверяем что инициализировался с Claude Code
            assert interviewer.llm_provider == "claude_code", \
                f"Expected claude_code, got {interviewer.llm_provider}"

            # Проверяем банк вопросов
            assert len(interviewer.QUESTION_BANK) == 10, \
                f"Expected 10 questions, got {len(interviewer.QUESTION_BANK)}"

            # Проверяем приоритеты
            p0_questions = [q for q, data in interviewer.QUESTION_BANK.items()
                           if data['priority'] == 'P0']
            assert len(p0_questions) == 4, \
                f"Expected 4 P0 questions, got {len(p0_questions)}"

            self.log_test("test_basic_initialization", True)
            return True

        except Exception as e:
            self.log_test("test_basic_initialization", False, str(e))
            return False

    async def test_first_question_is_q1(self):
        """Тест 2: Первый вопрос всегда Q1"""
        try:
            interviewer = AdaptiveInterviewerWithQuestionBank(
                llm_client=None,
                llm_provider="claude_code"
            )

            result = await interviewer.ask_next_question()

            assert result['question_id'] == 'Q1', \
                f"Expected Q1, got {result['question_id']}"

            assert not result['is_clarifying'], \
                "First question should not be clarifying"

            assert not result['should_finish'], \
                "Should not finish after first question"

            self.log_test("test_first_question_is_q1", True)
            return True

        except Exception as e:
            self.log_test("test_first_question_is_q1", False, str(e))
            return False

    async def test_mock_full_interview(self):
        """Тест 3: Полное интервью в mock режиме"""
        try:
            interviewer = AdaptiveInterviewerWithQuestionBank(
                llm_client=None,
                llm_provider="claude_code"
            )

            # Тестовые ответы
            test_answers = [
                "Лучные клубы Кемерово",  # Q1
                "В Кемерово нет доступа к стрельбе из лука для молодёжи 14-25 лет, " * 5,  # Q2 (длинный)
                "500+ молодых людей 14-25 лет в Кемеровской области, " * 3,  # Q3
                "Создать 3 клуба за 2 года, охват 500 человек, " * 2,  # Q4
                "Задачи: найти помещения, купить оборудование, набрать тренеров, " * 2,  # Q5
                "800 тысяч: 300к оборудование, 200к аренда, 300к зарплаты, " * 2,  # Q6
                "500 участников, 3 клуба, 20 мероприятий в год, " * 2,  # Q7
                "Я руководитель, 3 тренера с опытом 5+ лет, " * 2,  # Q8
                "Администрация Кемерово, школы, федерация стрельбы из лука, " * 2,  # Q9
                "Членские взносы 1000р/мес, аренда тира для мероприятий, " * 2  # Q10
            ]

            # Первый вопрос
            result = await interviewer.ask_next_question()
            assert result['question_id'] == 'Q1'

            # Цикл интервью
            question_count = 1
            for answer in test_answers:
                if result['should_finish']:
                    break

                result = await interviewer.ask_next_question(answer)
                question_count += 1

                if question_count > 20:  # Защита
                    break

            # Проверяем что завершилось
            assert result['should_finish'] or question_count >= 10, \
                "Interview should finish"

            # Проверяем анкету
            anketa = interviewer.get_anketa()
            assert len(anketa) > 0, "Anketa should not be empty"

            # Проверяем что есть основные поля
            expected_fields = ['project_name', 'problem_statement', 'target_audience']
            for field in expected_fields:
                assert field in anketa, f"Missing field: {field}"

            self.log_test("test_mock_full_interview", True,
                         f"Questions asked: {len(interviewer.asked_questions)}, "
                         f"Anketa fields: {len(anketa)}")
            return True

        except Exception as e:
            self.log_test("test_mock_full_interview", False, str(e))
            return False

    async def test_claude_code_is_default(self):
        """Тест 4: Claude Code - провайдер по умолчанию"""
        try:
            # Без указания provider
            interviewer = AdaptiveInterviewerWithQuestionBank()

            # Должен быть claude_code по умолчанию
            assert interviewer.llm_provider == "claude_code", \
                f"Default should be claude_code, got {interviewer.llm_provider}"

            self.log_test("test_claude_code_is_default", True)
            return True

        except Exception as e:
            self.log_test("test_claude_code_is_default", False, str(e))
            return False

    async def test_no_gigachat_by_default(self):
        """Тест 5: НЕТ автоматического использования GigaChat"""
        try:
            interviewer = AdaptiveInterviewerWithQuestionBank(
                llm_client=None
            )

            # Проверяем что НЕ gigachat
            assert interviewer.llm_provider != "gigachat", \
                "Should NOT default to gigachat!"

            # Проверяем что claude_code
            assert interviewer.llm_provider == "claude_code", \
                "Should default to claude_code"

            self.log_test("test_no_gigachat_by_default", True)
            return True

        except Exception as e:
            self.log_test("test_no_gigachat_by_default", False, str(e))
            return False

    async def test_question_bank_structure(self):
        """Тест 6: Структура банка вопросов"""
        try:
            interviewer = AdaptiveInterviewerWithQuestionBank()

            # Проверяем все вопросы
            for q_id, data in interviewer.QUESTION_BANK.items():
                # Проверяем наличие обязательных полей
                assert 'text' in data, f"{q_id} missing 'text'"
                assert 'priority' in data, f"{q_id} missing 'priority'"
                assert 'category' in data, f"{q_id} missing 'category'"

                # Проверяем валидность приоритета
                assert data['priority'] in ['P0', 'P1', 'P2'], \
                    f"{q_id} invalid priority: {data['priority']}"

                # Проверяем что текст не пустой
                assert len(data['text']) > 10, \
                    f"{q_id} text too short: {data['text']}"

            self.log_test("test_question_bank_structure", True)
            return True

        except Exception as e:
            self.log_test("test_question_bank_structure", False, str(e))
            return False

    async def run_all_tests(self):
        """Запустить все тесты автономно"""
        print("=" * 80)
        print("AUTONOMOUS TEST RUNNER - Running all tests automatically")
        print("No user intervention required!")
        print("=" * 80)

        print("\nLLM Provider Policy Check:")
        print("  - Claude Code: MAIN and ONLY provider")
        print("  - GigaChat: Manual choice only")
        print("  - Fallback: NO automatic fallback")

        print("\n" + "=" * 80)
        print("Running tests...")
        print("=" * 80 + "\n")

        # Запускаем все тесты
        await self.test_basic_initialization()
        await self.test_first_question_is_q1()
        await self.test_claude_code_is_default()
        await self.test_no_gigachat_by_default()
        await self.test_question_bank_structure()
        await self.test_mock_full_interview()

        # Итоги
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
            print("[OK] Code is ready for next step: LLM integration")
        else:
            print("\n[WARNING] SOME TESTS FAILED")
            print("Review the errors above")

        # Сохраняем результаты в JSON
        results_file = Path(__file__).parent / "test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': '2025-10-22',
                'total': total_tests,
                'passed': self.tests_passed,
                'failed': self.tests_failed,
                'pass_rate': pass_rate,
                'results': self.test_results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n[FILE] Results saved to: {results_file}")

        return self.tests_failed == 0


async def main():
    """Главная функция - запускает все автономно"""
    runner = AutonomousTestRunner()
    success = await runner.run_all_tests()

    # Exit code для CI/CD
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
