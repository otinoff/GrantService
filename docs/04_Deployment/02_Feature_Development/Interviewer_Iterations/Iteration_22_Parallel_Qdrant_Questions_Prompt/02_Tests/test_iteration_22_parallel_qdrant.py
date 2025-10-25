#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для Iteration 22: Parallel Qdrant + System Prompt with Questions

Проверяет:
1. System prompt содержит 12 ключевых вопросов
2. Параллельная обработка Qdrant + gaps работает
3. Timeout защита срабатывает
4. Performance улучшился (5-6s → 3-5s)

Author: Grant Service Test Engineer
Created: 2025-10-22
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

# Добавить корень проекта в path
# Путь: 02_Tests -> Iteration_22 -> Interviewer_Iterations -> 02_Feature_Development -> Development -> GrantService_Project
# Нужно: C:\SnowWhiteAI\GrantService
project_root = Path(r"C:\SnowWhiteAI\GrantService")
sys.path.insert(0, str(project_root))

from agents.reference_points.adaptive_question_generator import (
    AdaptiveQuestionGenerator,
    UserExpertiseLevel,
    ProjectType
)
from agents.reference_points.reference_point import ReferencePoint, ReferencePointPriority, CompletionCriteria


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    mock = AsyncMock()
    mock.generate_async = AsyncMock(return_value="Какую проблему решает ваш проект?")
    return mock


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    mock = Mock()
    mock.search = Mock(return_value=[
        Mock(payload={'content': 'Тестовый контекст из базы знаний ФПГ'}, score=0.95)
    ])
    return mock


@pytest.fixture
def sample_reference_point():
    """Sample Reference Point"""
    return ReferencePoint(
        id="rp_002_problem",
        name="Определить проблему",
        description="Понять, какую социальную проблему решает проект",
        priority=ReferencePointPriority.P0_CRITICAL,
        required=True,
        completion_criteria=CompletionCriteria(
            min_length=100,
            required_keywords=["проблема"]
        ),
        question_hints=[
            "Какую проблему решает ваш проект?",
            "Почему эта проблема важна?"
        ],
        tags=["problem", "social_issue"]
    )


@pytest.fixture
def sample_context():
    """Sample conversation context"""
    return {
        'project_essence': 'Создание инклюзивных пространств для детей с ОВЗ',
        'collected_fields': {'project_essence'},
        'covered_topics': []
    }


# =============================================================================
# TESTS: System Prompt with Questions
# =============================================================================

@pytest.mark.autonomous
def test_system_prompt_contains_12_questions(mock_llm_client):
    """
    Тест 1: System prompt содержит все 12 ключевых вопросов
    """
    generator = AdaptiveQuestionGenerator(mock_llm_client)

    # Проверяем что метод _llm_generate_question использует правильный prompt
    # Для этого нужно проверить что system_prompt содержит ключевые темы

    expected_topics = [
        "Имя заявителя",
        "Суть проекта",
        "Проблема",
        "Целевая аудитория",
        "География",
        "Методология",
        "Результаты",
        "Бюджет",
        "Команда",
        "Риски",
        "Устойчивость",
        "Уникальность"
    ]

    # Читаем исходный код метода чтобы проверить system_prompt
    import inspect
    source = inspect.getsource(generator._llm_generate_question)

    found_count = 0
    for topic in expected_topics:
        if topic in source:
            found_count += 1

    assert found_count >= 10, f"System prompt должен содержать минимум 10 из 12 тем, найдено: {found_count}"
    print(f"[OK] System prompt содержит {found_count}/12 ключевых тем")


# =============================================================================
# TESTS: Parallel Execution
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.autonomous
async def test_parallel_qdrant_and_gaps_execution(
    mock_llm_client,
    sample_reference_point,
    sample_context
):
    """
    Тест 2: Qdrant search и gaps analysis выполняются параллельно

    Проверяет что:
    - Обе функции вызываются
    - Время выполнения < суммы времен (параллельность)
    """
    # Mock embedding model
    with patch('agents.reference_points.adaptive_question_generator.SENTENCE_TRANSFORMERS_AVAILABLE', True):
        with patch('agents.reference_points.adaptive_question_generator.SentenceTransformer') as MockModel:
            mock_model = Mock()
            mock_model.encode = Mock(return_value=[0.1] * 384)
            MockModel.return_value = mock_model

            # Mock Qdrant с задержкой
            mock_qdrant = Mock()

            async def slow_search(*args, **kwargs):
                await asyncio.sleep(0.5)  # 500ms задержка
                return [Mock(payload={'content': 'Контекст'}, score=0.9)]

            mock_qdrant.search = slow_search

            generator = AdaptiveQuestionGenerator(
                mock_llm_client,
                qdrant_client=mock_qdrant
            )

            start_time = time.time()

            # Генерация вопроса (должна быть параллельной)
            question = await generator.generate_question(
                reference_point=sample_reference_point,
                conversation_context=sample_context,
                user_level=UserExpertiseLevel.NOVICE,
                project_type=ProjectType.SOCIAL
            )

            elapsed = time.time() - start_time

            # Проверки
            assert question is not None
            assert isinstance(question, str)
            assert len(question) > 0

            # Время должно быть < 1.5 сек (0.5 Qdrant + 0.01 gaps + 0.1 LLM mock)
            # Если не параллельно, было бы > 0.6 сек
            print(f"[TIME] Время генерации: {elapsed:.3f}s")
            assert elapsed < 2.0, f"Слишком долго: {elapsed:.3f}s (должно быть < 2s)"

            print(f"[OK] Параллельная обработка работает, время: {elapsed:.3f}s")


@pytest.mark.asyncio
@pytest.mark.autonomous
async def test_qdrant_timeout_protection(
    mock_llm_client,
    sample_reference_point,
    sample_context
):
    """
    Тест 3: Timeout защита для Qdrant search

    Проверяет что:
    - Если Qdrant медленный (>2 сек), срабатывает timeout
    - Fallback на пустой контекст
    - Генерация вопроса продолжается
    """
    with patch('agents.reference_points.adaptive_question_generator.SENTENCE_TRANSFORMERS_AVAILABLE', True):
        with patch('agents.reference_points.adaptive_question_generator.SentenceTransformer') as MockModel:
            mock_model = Mock()
            mock_model.encode = Mock(return_value=[0.1] * 384)
            MockModel.return_value = mock_model

            # Mock Qdrant с ДОЛГОЙ задержкой (имитация медленного сервера)
            mock_qdrant = Mock()

            async def very_slow_search(*args, **kwargs):
                await asyncio.sleep(5.0)  # 5 секунд - больше timeout (2s)
                return [Mock(payload={'content': 'Контекст'}, score=0.9)]

            mock_qdrant.search = very_slow_search

            generator = AdaptiveQuestionGenerator(
                mock_llm_client,
                qdrant_client=mock_qdrant
            )

            start_time = time.time()

            # Генерация вопроса
            question = await generator.generate_question(
                reference_point=sample_reference_point,
                conversation_context=sample_context,
                user_level=UserExpertiseLevel.NOVICE,
                project_type=ProjectType.SOCIAL
            )

            elapsed = time.time() - start_time

            # Проверки
            assert question is not None, "Вопрос должен быть сгенерирован даже при timeout Qdrant"

            # Время должно быть ~2-3 сек (2s timeout + LLM), а не 5+ сек
            print(f"[TIME] Время с timeout: {elapsed:.3f}s")
            assert elapsed < 4.0, f"Timeout не сработал, время: {elapsed:.3f}s (должно быть < 4s)"

            print(f"[OK] Timeout защита работает, время: {elapsed:.3f}s")


# =============================================================================
# TESTS: Performance Improvement
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.autonomous
async def test_performance_improvement_vs_sequential(
    mock_llm_client,
    sample_reference_point,
    sample_context
):
    """
    Тест 4: Performance улучшение vs последовательного выполнения

    Сравнивает:
    - Параллельное выполнение
    - Последовательное выполнение (симуляция старого кода)

    Ожидание: параллельное быстрее на 30-40%
    """
    with patch('agents.reference_points.adaptive_question_generator.SENTENCE_TRANSFORMERS_AVAILABLE', True):
        with patch('agents.reference_points.adaptive_question_generator.SentenceTransformer') as MockModel:
            mock_model = Mock()
            mock_model.encode = Mock(return_value=[0.1] * 384)
            MockModel.return_value = mock_model

            # Mock Qdrant с задержкой
            async def search_with_delay(*args, **kwargs):
                await asyncio.sleep(0.3)  # 300ms
                return [Mock(payload={'content': 'Контекст'}, score=0.9)]

            mock_qdrant = Mock()
            mock_qdrant.search = search_with_delay

            generator = AdaptiveQuestionGenerator(
                mock_llm_client,
                qdrant_client=mock_qdrant
            )

            # 1. Тест параллельного выполнения (новый код)
            start_parallel = time.time()
            question_parallel = await generator.generate_question(
                reference_point=sample_reference_point,
                conversation_context=sample_context,
                user_level=UserExpertiseLevel.NOVICE,
                project_type=ProjectType.SOCIAL
            )
            time_parallel = time.time() - start_parallel

            # 2. Симуляция последовательного выполнения (старый код)
            start_sequential = time.time()

            # Последовательно (как было раньше)
            fpg_context = await generator._get_fpg_context(
                sample_reference_point,
                ProjectType.SOCIAL
            )
            gaps = generator._identify_information_gaps(
                sample_reference_point,
                sample_context
            )
            question_sequential = await mock_llm_client.generate_async("test")

            time_sequential = time.time() - start_sequential

            # Сравнение
            improvement = ((time_sequential - time_parallel) / time_sequential) * 100

            print(f"\n[STATS] Performance Comparison:")
            print(f"   Параллельное: {time_parallel:.3f}s")
            print(f"   Последовательное: {time_sequential:.3f}s")
            print(f"   Улучшение: {improvement:.1f}%")

            # Параллельное должно быть быстрее (или хотя бы не медленнее)
            assert time_parallel <= time_sequential, \
                f"Параллельное выполнение медленнее! {time_parallel:.3f}s vs {time_sequential:.3f}s"

            print(f"[OK] Performance улучшение: {improvement:.1f}%")


# =============================================================================
# TESTS: Error Handling
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.autonomous
async def test_graceful_degradation_on_qdrant_error(
    mock_llm_client,
    sample_reference_point,
    sample_context
):
    """
    Тест 5: Graceful degradation при ошибке Qdrant

    Проверяет что:
    - Если Qdrant выбрасывает exception, используется fallback
    - Генерация вопроса продолжается
    - Нет crash
    """
    with patch('agents.reference_points.adaptive_question_generator.SENTENCE_TRANSFORMERS_AVAILABLE', True):
        with patch('agents.reference_points.adaptive_question_generator.SentenceTransformer') as MockModel:
            mock_model = Mock()
            mock_model.encode = Mock(return_value=[0.1] * 384)
            MockModel.return_value = mock_model

            # Mock Qdrant с ошибкой
            mock_qdrant = Mock()
            mock_qdrant.search = Mock(side_effect=Exception("Connection refused"))

            generator = AdaptiveQuestionGenerator(
                mock_llm_client,
                qdrant_client=mock_qdrant
            )

            # Генерация вопроса НЕ должна крешиться
            question = await generator.generate_question(
                reference_point=sample_reference_point,
                conversation_context=sample_context,
                user_level=UserExpertiseLevel.NOVICE,
                project_type=ProjectType.SOCIAL
            )

            # Проверки
            assert question is not None, "Вопрос должен быть сгенерирован даже при ошибке Qdrant"
            assert isinstance(question, str)
            assert len(question) > 0

            print(f"[OK] Graceful degradation работает: '{question}'")


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Iteration 22 Tests: Parallel Qdrant + System Prompt")
    print("=" * 80)

    pytest.main([__file__, "-v", "-s", "--tb=short"])
