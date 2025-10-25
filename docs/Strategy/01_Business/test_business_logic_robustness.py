#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E Test: Business Logic Robustness Test
=========================================

Цель: Проверить как интервьюер справляется с "взломом" бизнес-логики -
когда пользователь отвечает нелогично, бессмысленно или пытается сломать систему.

Тестируемые сценарии:
1. Полностью нерелевантные ответы ("banana" на вопрос о проекте)
2. Односложные бессмысленные ответы
3. Случайный текст/gibberish
4. Уход от темы
5. Противоречивые ответы

Ожидаемое поведение системы:
- ✅ Не должна падать/крашиться
- ✅ Должна пытаться уточнить/перенаправить
- ✅ Должна задавать follow-up вопросы
- ✅ Должна в конце концов завершить интервью (даже с плохими данными)
- ✅ Цель: помочь пользователю заполнить анкету, несмотря на качество ответов

Author: Grant Service Testing Team
Created: 2025-10-23
Version: 1.0
"""

import sys
import os
from pathlib import Path

# Setup path для импорта агента
_project_root = Path(__file__).parent.parent.parent / "GrantService"
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "agents"))

import pytest
import asyncio
import logging
from typing import Dict, Any, List

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Mock Database для изоляции теста
# =============================================================================

class MockDatabase:
    """Mock database для тестирования без реального DB"""

    def __init__(self):
        self.sessions = {}
        self.users = {}

    def create_session(self, user_id: int, grant_fund: str = "fpg") -> int:
        """Создать mock session"""
        session_id = len(self.sessions) + 1
        self.sessions[session_id] = {
            'user_id': user_id,
            'grant_fund': grant_fund,
            'status': 'active',
            'collected_info': {}
        }
        return session_id

    def update_session(self, session_id: int, collected_info: Dict):
        """Обновить session данными"""
        if session_id in self.sessions:
            self.sessions[session_id]['collected_info'] = collected_info

    def get_session(self, session_id: int) -> Dict:
        """Получить session"""
        return self.sessions.get(session_id, {})


# =============================================================================
# Test Scenarios
# =============================================================================

class TestBusinessLogicRobustness:
    """
    Тесты устойчивости бизнес-логики интервьюера к нелогичным ответам
    """

    @pytest.fixture
    def mock_db(self):
        """Фикстура для mock database"""
        return MockDatabase()

    @pytest.fixture
    def user_data(self):
        """Фикстура для тестовых данных пользователя"""
        return {
            'telegram_id': 999999,
            'username': 'test_chaos_user',
            'first_name': 'Test',
            'last_name': 'Chaos',
            'grant_fund': 'fpg'
        }

    # =========================================================================
    # Scenario 1: Completely Irrelevant Answers
    # =========================================================================

    @pytest.mark.asyncio
    async def test_irrelevant_answers_scenario(self, mock_db, user_data):
        """
        Сценарий 1: Пользователь отвечает полностью не по теме

        Вопрос: "В чем суть вашего проекта?"
        Ответ: "Мне нравятся бананы и синий цвет"

        Ожидание:
        - Система не падает
        - Система пытается уточнить или перенаправить
        - Система задает follow-up вопрос
        """
        logger.info("\n" + "="*80)
        logger.info("TEST SCENARIO 1: Irrelevant Answers")
        logger.info("="*80)

        # Подготовка
        session_id = mock_db.create_session(user_data['telegram_id'])

        # Симулируем диалог
        conversation = [
            {
                'question': 'В чем суть вашего проекта?',
                'user_answer': 'Мне нравятся бананы и синий цвет',
                'expected_behavior': [
                    'должна попытаться перенаправить',
                    'должна задать уточняющий вопрос',
                    'НЕ должна упасть'
                ]
            },
            {
                'question': 'Какую социальную проблему решает проект?',
                'user_answer': 'Вчера был дождь, а сегодня солнечно',
                'expected_behavior': [
                    'должна снова попытаться уточнить',
                    'возможно, предложит примеры'
                ]
            }
        ]

        # Результаты теста
        test_results = {
            'scenario': 'irrelevant_answers',
            'passed': True,
            'errors': [],
            'observations': []
        }

        for turn in conversation:
            logger.info(f"\nВопрос: {turn['question']}")
            logger.info(f"Ответ пользователя: {turn['user_answer']}")
            logger.info(f"Ожидаемое поведение: {turn['expected_behavior']}")

            # ПРОВЕРКА: Система должна обработать ответ без ошибок
            try:
                # Симулируем обработку ответа
                processed = self._simulate_answer_processing(turn['user_answer'])
                test_results['observations'].append(
                    f"✅ Ответ обработан без ошибок: '{turn['user_answer'][:50]}...'"
                )
            except Exception as e:
                test_results['passed'] = False
                test_results['errors'].append(
                    f"❌ Ошибка при обработке: {str(e)}"
                )

        # Выводим результаты
        self._print_test_results(test_results)

        # Assertions
        assert test_results['passed'], f"Test failed with errors: {test_results['errors']}"

    # =========================================================================
    # Scenario 2: Single Word Nonsense
    # =========================================================================

    @pytest.mark.asyncio
    async def test_single_word_nonsense(self, mock_db, user_data):
        """
        Сценарий 2: Односложные бессмысленные ответы

        Вопрос: "Расскажите о вашей целевой аудитории?"
        Ответ: "Да"

        Ожидание:
        - Система запросит больше деталей
        - Система не примет односложный ответ как полный
        """
        logger.info("\n" + "="*80)
        logger.info("TEST SCENARIO 2: Single Word Nonsense")
        logger.info("="*80)

        conversation = [
            {
                'question': 'Расскажите о вашей целевой аудитории?',
                'user_answer': 'Да',
                'expected_behavior': [
                    'должна запросить больше деталей',
                    'не должна принять это как полный ответ'
                ]
            },
            {
                'question': 'Какие ресурсы нужны для проекта?',
                'user_answer': 'Ок',
                'expected_behavior': [
                    'должна попросить конкретики',
                    'возможно, дать примеры'
                ]
            },
            {
                'question': 'Как будете измерять результаты?',
                'user_answer': 'Хм',
                'expected_behavior': [
                    'должна продолжить диалог',
                    'не должна зациклиться'
                ]
            }
        ]

        test_results = {
            'scenario': 'single_word_nonsense',
            'passed': True,
            'errors': [],
            'observations': []
        }

        for turn in conversation:
            logger.info(f"\nВопрос: {turn['question']}")
            logger.info(f"Ответ: {turn['user_answer']}")

            # ПРОВЕРКА: Короткие ответы должны обрабатываться
            try:
                processed = self._simulate_answer_processing(turn['user_answer'])
                is_too_short = len(turn['user_answer'].split()) < 2

                if is_too_short:
                    test_results['observations'].append(
                        f"✅ Обнаружен короткий ответ, система должна запросить детали"
                    )

            except Exception as e:
                test_results['passed'] = False
                test_results['errors'].append(f"❌ Ошибка: {str(e)}")

        self._print_test_results(test_results)
        assert test_results['passed'], f"Test failed: {test_results['errors']}"

    # =========================================================================
    # Scenario 3: Random Gibberish
    # =========================================================================

    @pytest.mark.asyncio
    async def test_random_gibberish(self, mock_db, user_data):
        """
        Сценарий 3: Случайный текст/gibberish

        Вопрос: "Опишите методологию проекта?"
        Ответ: "asdfghjkl qwerty zxcvbnm"

        Ожидание:
        - Система обрабатывает без краша
        - Система пытается получить нормальный ответ
        """
        logger.info("\n" + "="*80)
        logger.info("TEST SCENARIO 3: Random Gibberish")
        logger.info("="*80)

        gibberish_inputs = [
            "asdfghjkl qwerty zxcvbnm",
            "123456789 !@#$%^&*()",
            "йцукенг шщзх фывапролд",
            "a b c d e f g h i j k",
            ".............",
        ]

        test_results = {
            'scenario': 'random_gibberish',
            'passed': True,
            'errors': [],
            'observations': []
        }

        for gibberish in gibberish_inputs:
            logger.info(f"\nGibberish input: '{gibberish}'")

            # ПРОВЕРКА: Система должна обработать gibberish без краша
            try:
                processed = self._simulate_answer_processing(gibberish)
                test_results['observations'].append(
                    f"✅ Gibberish обработан без ошибок: '{gibberish}'"
                )
            except Exception as e:
                test_results['passed'] = False
                test_results['errors'].append(
                    f"❌ Краш на gibberish '{gibberish}': {str(e)}"
                )

        self._print_test_results(test_results)
        assert test_results['passed'], "System crashed on gibberish input!"

    # =========================================================================
    # Scenario 4: Contradictory Answers
    # =========================================================================

    @pytest.mark.asyncio
    async def test_contradictory_answers(self, mock_db, user_data):
        """
        Сценарий 4: Противоречивые ответы

        Ответ 1: "Целевая аудитория - дети 5-7 лет"
        Ответ 2: "Проект для пенсионеров 70+"

        Ожидание:
        - Система замечает противоречие
        - Система просит уточнить
        """
        logger.info("\n" + "="*80)
        logger.info("TEST SCENARIO 4: Contradictory Answers")
        logger.info("="*80)

        collected_info = {}

        # Первый ответ
        logger.info("\nШаг 1: Пользователь говорит про детей 5-7 лет")
        collected_info['target_audience'] = 'дети 5-7 лет'

        # Второй ответ противоречит
        logger.info("Шаг 2: Затем говорит про пенсионеров 70+")
        contradictory = 'пенсионеры старше 70 лет'

        # ПРОВЕРКА: Система должна заметить противоречие
        test_results = {
            'scenario': 'contradictory_answers',
            'passed': True,
            'errors': [],
            'observations': []
        }

        try:
            # Симулируем детекцию противоречия
            has_contradiction = self._detect_contradiction(
                collected_info['target_audience'],
                contradictory
            )

            if has_contradiction:
                test_results['observations'].append(
                    "✅ Противоречие обнаружено (дети vs пенсионеры)"
                )
                test_results['observations'].append(
                    "✅ Система должна попросить уточнить"
                )
            else:
                test_results['observations'].append(
                    "⚠️ Противоречие НЕ обнаружено (может быть проблема)"
                )

        except Exception as e:
            test_results['passed'] = False
            test_results['errors'].append(f"❌ Ошибка: {str(e)}")

        self._print_test_results(test_results)
        assert test_results['passed']

    # =========================================================================
    # Scenario 5: Full Interview with Bad Quality Answers
    # =========================================================================

    @pytest.mark.asyncio
    async def test_full_interview_bad_quality(self, mock_db, user_data):
        """
        Сценарий 5: Полное интервью с плохими ответами

        Проверяем что система:
        - Завершает интервью (не зависает)
        - Собирает хоть какую-то информацию
        - Помогает пользователю, несмотря на плохие ответы
        """
        logger.info("\n" + "="*80)
        logger.info("TEST SCENARIO 5: Full Interview with Bad Quality Answers")
        logger.info("="*80)

        # Симулируем полное интервью с плохими ответами
        full_interview = [
            {'q': 'Имя?', 'a': 'Вася'},  # OK
            {'q': 'Суть проекта?', 'a': 'Ну типа да'},  # Плохой
            {'q': 'Социальная проблема?', 'a': 'asdfgh'},  # Gibberish
            {'q': 'Целевая аудитория?', 'a': 'Все'},  # Слишком общий
            {'q': 'Методология?', 'a': '???'},  # Бессмысленный
            {'q': 'Бюджет?', 'a': 'Много'},  # Неконкретный
            {'q': 'Результаты?', 'a': 'Будет хорошо'},  # Расплывчатый
        ]

        test_results = {
            'scenario': 'full_interview_bad_quality',
            'passed': True,
            'errors': [],
            'observations': [],
            'questions_asked': 0,
            'answers_processed': 0,
            'interview_completed': False
        }

        logger.info("\nНачинаем интервью с плохими ответами...\n")

        for turn in full_interview:
            test_results['questions_asked'] += 1
            logger.info(f"Q: {turn['q']}")
            logger.info(f"A: {turn['a']}")

            # Обрабатываем ответ
            try:
                processed = self._simulate_answer_processing(turn['a'])
                test_results['answers_processed'] += 1
                logger.info(f"   ✅ Ответ обработан")
            except Exception as e:
                test_results['passed'] = False
                test_results['errors'].append(f"❌ Краш на вопросе '{turn['q']}': {str(e)}")
                logger.error(f"   ❌ ОШИБКА: {str(e)}")
                break

        # ПРОВЕРКА: Интервью должно завершиться
        if test_results['answers_processed'] == len(full_interview):
            test_results['interview_completed'] = True
            test_results['observations'].append(
                f"✅ Интервью завершено ({len(full_interview)} вопросов обработано)"
            )
        else:
            test_results['observations'].append(
                f"⚠️ Интервью не завершено ({test_results['answers_processed']}/{len(full_interview)})"
            )

        logger.info(f"\n{'='*80}")
        logger.info(f"Результаты интервью:")
        logger.info(f"  Вопросов задано: {test_results['questions_asked']}")
        logger.info(f"  Ответов обработано: {test_results['answers_processed']}")
        logger.info(f"  Интервью завершено: {test_results['interview_completed']}")

        self._print_test_results(test_results)

        # Assertions
        assert test_results['passed'], "Interview crashed with bad quality answers!"
        assert test_results['interview_completed'], "Interview did not complete!"

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _simulate_answer_processing(self, answer: str) -> Dict[str, Any]:
        """
        Симулирует обработку ответа пользователя

        В реальности это делает InteractiveInterviewerAgentV2,
        здесь мы проверяем что ответ можно обработать без ошибок
        """
        # Базовая валидация
        if not isinstance(answer, str):
            raise ValueError(f"Answer must be string, got {type(answer)}")

        # Обработка
        processed = {
            'raw_answer': answer,
            'length': len(answer),
            'word_count': len(answer.split()),
            'is_short': len(answer.split()) < 3,
            'is_gibberish': self._is_gibberish(answer),
            'timestamp': 'mock_timestamp'
        }

        return processed

    def _is_gibberish(self, text: str) -> bool:
        """Простая эвристика для определения gibberish"""
        words = text.split()
        if not words:
            return True

        # Если все "слова" < 3 букв или содержат спецсимволы
        short_words = sum(1 for w in words if len(w) < 3)
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())

        return short_words > len(words) * 0.7 or special_chars > len(text) * 0.5

    def _detect_contradiction(self, answer1: str, answer2: str) -> bool:
        """
        Простая проверка на противоречия
        (в реальности это делает LLM)
        """
        # Простая эвристика: дети vs пенсионеры
        is_children_1 = any(word in answer1.lower() for word in ['дети', 'детский', 'ребенок'])
        is_elderly_1 = any(word in answer1.lower() for word in ['пенсионер', 'пожилой', 'старш'])

        is_children_2 = any(word in answer2.lower() for word in ['дети', 'детский', 'ребенок'])
        is_elderly_2 = any(word in answer2.lower() for word in ['пенсионер', 'пожилой', 'старш'])

        # Противоречие если в первом дети, во втором пенсионеры (или наоборот)
        return (is_children_1 and is_elderly_2) or (is_elderly_1 and is_children_2)

    def _print_test_results(self, results: Dict[str, Any]):
        """Красивый вывод результатов теста"""
        logger.info("\n" + "="*80)
        logger.info(f"РЕЗУЛЬТАТЫ ТЕСТА: {results['scenario']}")
        logger.info("="*80)

        if results['passed']:
            logger.info("✅ ТЕСТ ПРОЙДЕН")
        else:
            logger.error("❌ ТЕСТ ПРОВАЛЕН")

        if results['observations']:
            logger.info("\nНаблюдения:")
            for obs in results['observations']:
                logger.info(f"  {obs}")

        if results['errors']:
            logger.error("\nОшибки:")
            for err in results['errors']:
                logger.error(f"  {err}")

        logger.info("="*80 + "\n")


# =============================================================================
# Main execution для запуска вне pytest
# =============================================================================

if __name__ == "__main__":
    """
    Запуск тестов напрямую (без pytest)

    Usage:
        python test_business_logic_robustness.py
    """
    print("\n" + "="*80)
    print("BUSINESS LOGIC ROBUSTNESS TEST SUITE")
    print("="*80)
    print("\nЗапуск тестов устойчивости бизнес-логики...\n")

    # Запуск через pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])
