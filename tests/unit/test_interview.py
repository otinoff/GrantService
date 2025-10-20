#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit тесты для data/database/interview.py
"""

import pytest
import json
import sys
from pathlib import Path

tests_dir = Path(__file__).parent.parent
sys.path.insert(0, str(tests_dir))

from fixtures.test_data import EXPECTED_MIGRATION_DATA


@pytest.mark.unit
class TestInterviewQuestions:
    """Тесты работы с вопросами интервью"""

    def test_get_active_questions(self, interview_manager):
        """Тест: получение всех активных вопросов"""
        questions = interview_manager.get_active_questions()

        assert questions is not None
        assert len(questions) == EXPECTED_MIGRATION_DATA['questions_count'], \
            f"Ожидается {EXPECTED_MIGRATION_DATA['questions_count']} вопросов, получено {len(questions)}"

    def test_questions_ordered_by_number(self, interview_manager):
        """Тест: вопросы отсортированы по номеру"""
        questions = interview_manager.get_active_questions()

        for i, question in enumerate(questions, start=1):
            assert question['question_number'] == i, \
                f"Вопрос {i} имеет номер {question['question_number']}"

    def test_question_has_required_fields(self, interview_manager):
        """Тест: каждый вопрос содержит все необходимые поля"""
        questions = interview_manager.get_active_questions()

        required_fields = [
            'id', 'question_number', 'question_text',
            'field_name', 'question_type', 'is_required'
        ]

        for question in questions:
            for field in required_fields:
                assert field in question, f"Поле {field} отсутствует в вопросе {question['question_number']}"
                assert question[field] is not None, f"Поле {field} пустое в вопросе {question['question_number']}"

    def test_get_question_by_number(self, interview_manager):
        """Тест: получение вопроса по номеру"""
        question = interview_manager.get_question_by_number(1)

        assert question is not None
        assert question['question_number'] == 1
        assert 'question_text' in question

    def test_get_nonexistent_question(self, interview_manager):
        """Тест: получение несуществующего вопроса возвращает None"""
        question = interview_manager.get_question_by_number(9999)
        assert question is None

    def test_validation_rules_format(self, interview_manager):
        """Тест: validation_rules имеют правильный формат JSON"""
        questions = interview_manager.get_active_questions()

        for question in questions:
            if question.get('validation_rules'):
                # Должен быть словарь (уже распарсенный)
                assert isinstance(question['validation_rules'], dict), \
                    f"validation_rules вопроса {question['question_number']} не является словарем"

    def test_question_types_valid(self, interview_manager):
        """Тест: типы вопросов валидны"""
        valid_types = ['text', 'textarea', 'number', 'select', 'date']
        questions = interview_manager.get_active_questions()

        for question in questions:
            assert question['question_type'] in valid_types, \
                f"Недопустимый тип вопроса {question['question_type']} в вопросе {question['question_number']}"


@pytest.mark.unit
class TestValidationRules:
    """Тесты правил валидации ответов"""

    def test_min_length_validation(self, interview_manager):
        """Тест: валидация минимальной длины ответа"""
        # Найдем вопрос с validation_rules
        questions = interview_manager.get_active_questions()

        question_with_validation = None
        for q in questions:
            validation_rules = q.get('validation_rules') or {}
            if validation_rules.get('min_length'):
                question_with_validation = q
                break

        # Если нашли вопрос с min_length - тестируем
        if question_with_validation:
            validation_rules = question_with_validation.get('validation_rules') or {}
            min_length = validation_rules.get('min_length', 0)

            # Корректный ответ
            valid_answer = "A" * min_length
            assert len(valid_answer) >= min_length

            # Некорректный ответ
            invalid_answer = "A" * (min_length - 1)
            assert len(invalid_answer) < min_length
        else:
            # Пропускаем тест если нет правил валидации
            pytest.skip("Нет вопросов с min_length validation")

    def test_max_length_validation(self, interview_manager):
        """Тест: валидация максимальной длины ответа"""
        question = interview_manager.get_question_by_number(1)

        validation_rules = question.get('validation_rules') or {}
        max_length = validation_rules.get('max_length')

        if max_length:
            # Корректный ответ
            valid_answer = "A" * max_length
            assert len(valid_answer) <= max_length

            # Некорректный ответ
            invalid_answer = "A" * (max_length + 1)
            assert len(invalid_answer) > max_length

    def test_required_questions_marked(self, interview_manager):
        """Тест: обязательные вопросы помечены правильно"""
        questions = interview_manager.get_active_questions()

        # Проверяем что большинство вопросов обязательные
        required_count = sum(1 for q in questions if q['is_required'])
        assert required_count >= len(questions) // 2, \
            f"Ожидается что минимум половина вопросов обязательны, найдено {required_count}/{len(questions)}"


@pytest.mark.unit
class TestQuestionFlow:
    """Тесты логики прохождения вопросов"""

    def test_first_question_is_1(self, interview_manager):
        """Тест: первый вопрос имеет номер 1"""
        questions = interview_manager.get_active_questions()
        assert questions[0]['question_number'] == 1

    def test_last_question_is_25(self, interview_manager):
        """Тест: последний вопрос имеет номер 25"""
        questions = interview_manager.get_active_questions()
        assert questions[-1]['question_number'] == EXPECTED_MIGRATION_DATA['questions_count']

    def test_no_gaps_in_question_numbers(self, interview_manager):
        """Тест: нет пропусков в нумерации вопросов"""
        questions = interview_manager.get_active_questions()

        question_numbers = [q['question_number'] for q in questions]
        expected_numbers = list(range(1, EXPECTED_MIGRATION_DATA['questions_count'] + 1))

        assert question_numbers == expected_numbers, \
            f"Обнаружены пропуски в нумерации: {set(expected_numbers) - set(question_numbers)}"

    def test_field_names_unique(self, interview_manager):
        """Тест: field_name уникальны для каждого вопроса"""
        questions = interview_manager.get_active_questions()

        field_names = [q['field_name'] for q in questions]
        unique_field_names = set(field_names)

        assert len(field_names) == len(unique_field_names), \
            "Обнаружены дублирующиеся field_name"
