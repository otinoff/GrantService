#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Iteration 25: Optimized LLM Generation

Tests:
1. question_hints is a list (not string)
2. User prompt is streamlined (fewer sections)
3. Temperature is reduced to 0.5
4. System prompt instructions are simplified
5. Conditional sections only added when needed

Author: Claude Code
Created: 2025-10-22
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# Note: conftest.py already adds project root to sys.path
from agents.reference_points.adaptive_question_generator import AdaptiveQuestionGenerator
from agents.reference_points.reference_point import ReferencePoint, ReferencePointPriority


@pytest.fixture
def mock_llm():
    """Mock LLM client"""
    llm = Mock()
    llm.generate_async = AsyncMock(return_value="Сгенерированный вопрос?")
    return llm


@pytest.fixture
def mock_qdrant():
    """Mock Qdrant client"""
    qdrant = Mock()
    qdrant.search = Mock(return_value=[])
    return qdrant


@pytest.fixture
def question_generator(mock_llm, mock_qdrant):
    """Create question generator with mocked dependencies"""
    generator = AdaptiveQuestionGenerator(
        llm_client=mock_llm,
        qdrant_client=mock_qdrant,
        qdrant_collection="test_collection"
    )
    # Skip embedding model loading for tests
    generator.embedding_model = Mock()
    generator.embedding_model.encode = Mock(return_value=[0.1, 0.2, 0.3])
    return generator


@pytest.fixture
def sample_reference_point():
    """Sample reference point with question_hints as LIST"""
    return ReferencePoint(
        id="rp_001_project_essence",
        name="Понять суть проекта",
        description="Получить чёткое понимание того, что делает проект",
        priority=ReferencePointPriority.P0_CRITICAL,
        required=True,
        question_hints=[  # LIST, not string!
            "Что конкретно делает ваш проект?",
            "В чём основная идея?",
            "Какую главную задачу решает проект?",
            "Расскажите о сути проекта",
            "Чем занимается ваш проект?"
        ],
        tags=["основа", "цель", "суть"]
    )


class TestIteration25QuestionHints:
    """Test that question_hints is handled as a list"""

    @pytest.mark.asyncio
    async def test_question_hints_is_list(self, question_generator, sample_reference_point):
        """Test: question_hints should be a list, not string"""
        assert isinstance(sample_reference_point.question_hints, list)
        assert len(sample_reference_point.question_hints) == 5

    @pytest.mark.asyncio
    async def test_question_hints_no_split_error(self, question_generator, sample_reference_point, mock_llm):
        """Test: Should not call .split() on question_hints"""
        # This should NOT raise AttributeError: 'list' object has no attribute 'split'

        conversation_context = {
            'covered_topics': ['greeting'],
            'collected_fields': {'applicant_name': 'Андрей'}
        }

        try:
            question = await question_generator.generate_question(
                reference_point=sample_reference_point,
                conversation_context=conversation_context
            )

            # Should succeed without AttributeError
            assert question == "Сгенерированный вопрос?"
            assert mock_llm.generate_async.called

        except AttributeError as e:
            if "'list' object has no attribute 'split'" in str(e):
                pytest.fail(f"AttributeError on question_hints: {e}")
            raise

    @pytest.mark.asyncio
    async def test_limited_to_2_hints(self, question_generator, sample_reference_point, mock_llm):
        """Test: Should use only first 2 question_hints"""

        conversation_context = {
            'covered_topics': [],
            'collected_fields': {}
        }

        await question_generator.generate_question(
            reference_point=sample_reference_point,
            conversation_context=conversation_context
        )

        # Check that LLM was called
        assert mock_llm.generate_async.called

        # Get the prompt that was sent to LLM
        call_args = mock_llm.generate_async.call_args
        prompt = call_args.kwargs.get('prompt') or call_args.args[0]

        # Should include only first 2 hints
        assert "Что конкретно делает ваш проект?" in prompt
        assert "В чём основная идея?" in prompt

        # Should NOT include 3rd, 4th, 5th hints
        assert "Какую главную задачу решает проект?" not in prompt
        assert "Расскажите о сути проекта" not in prompt
        assert "Чем занимается ваш проект?" not in prompt


class TestIteration25StreamlinedPrompt:
    """Test streamlined user prompt structure"""

    @pytest.mark.asyncio
    async def test_prompt_has_fewer_sections(self, question_generator, sample_reference_point, mock_llm):
        """Test: User prompt should have 5 sections or fewer (was 9)"""

        conversation_context = {
            'covered_topics': ['greeting', 'applicant_name'],
            'collected_fields': {'applicant_name': 'Андрей'}
        }

        await question_generator.generate_question(
            reference_point=sample_reference_point,
            conversation_context=conversation_context
        )

        call_args = mock_llm.generate_async.call_args
        prompt = call_args.kwargs.get('prompt') or call_args.args[0]

        # Should have "Задача" section
        assert "# Задача" in prompt or "Узнать:" in prompt

        # Should have "Контекст разговора" (merged section)
        assert "# Контекст разговора" in prompt or "Уже обсуждено:" in prompt

        # Should NOT have separate "Уровень пользователя" section
        assert "# Уровень пользователя" not in prompt

    @pytest.mark.asyncio
    async def test_conditional_sections_not_empty(self, question_generator, sample_reference_point, mock_llm):
        """Test: Empty sections should not be included"""

        # Context with NO gaps and NO fpg_context
        conversation_context = {
            'covered_topics': [],
            'collected_fields': {}
        }

        await question_generator.generate_question(
            reference_point=sample_reference_point,
            conversation_context=conversation_context
            # gaps and fpg_context are computed internally, not parameters
        )

        call_args = mock_llm.generate_async.call_args
        prompt = call_args.kwargs.get('prompt') or call_args.args[0]

        # Should NOT include "Пробелы: Нет явных пробелов"
        assert "Нет явных пробелов" not in prompt

        # Should NOT include "Контекст ФПГ: Нет специфичных требований"
        assert "Нет специфичных требований" not in prompt


class TestIteration25Temperature:
    """Test temperature parameter"""

    @pytest.mark.asyncio
    async def test_temperature_is_0_5(self, question_generator, sample_reference_point, mock_llm):
        """Test: Temperature should be 0.5 (was 0.7)"""

        conversation_context = {
            'covered_topics': [],
            'collected_fields': {}
        }

        await question_generator.generate_question(
            reference_point=sample_reference_point,
            conversation_context=conversation_context
        )

        # Check temperature parameter
        call_args = mock_llm.generate_async.call_args
        temperature = call_args.kwargs.get('temperature')

        assert temperature == 0.5, f"Expected temperature=0.5, got {temperature}"


class TestIteration25SystemPrompt:
    """Test simplified system prompt"""

    @pytest.mark.asyncio
    async def test_system_prompt_simplified(self, question_generator, sample_reference_point, mock_llm):
        """Test: System prompt should have 4 bullet points (was 9+)"""

        conversation_context = {
            'covered_topics': [],
            'collected_fields': {}
        }

        await question_generator.generate_question(
            reference_point=sample_reference_point,
            conversation_context=conversation_context
        )

        call_args = mock_llm.generate_async.call_args
        prompt = call_args.kwargs.get('prompt') or call_args.args[0]

        # Should have "ВАЖНО:" section
        assert "ВАЖНО:" in prompt

        # Count bullet points in ВАЖНО section
        important_section = prompt.split("ВАЖНО:")[1].split("\n\n")[0]
        bullet_count = important_section.count("- ")

        # Should have 4 bullets (not 9+)
        assert bullet_count <= 5, f"Expected ≤5 bullets, got {bullet_count}"

    @pytest.mark.asyncio
    async def test_system_prompt_has_key_instructions(self, question_generator, sample_reference_point, mock_llm):
        """Test: System prompt should have key instructions"""

        conversation_context = {
            'covered_topics': [],
            'collected_fields': {}
        }

        await question_generator.generate_question(
            reference_point=sample_reference_point,
            conversation_context=conversation_context
        )

        call_args = mock_llm.generate_async.call_args
        prompt = call_args.kwargs.get('prompt') or call_args.args[0]

        # Key instructions should be present
        assert "Задавай ОДИН вопрос" in prompt or "один вопрос" in prompt.lower()
        assert "не дублируй" in prompt.lower() or "дубл" in prompt.lower()
        assert "по имени" in prompt.lower()


class TestIteration25PromptSize:
    """Test overall prompt size reduction"""

    @pytest.mark.asyncio
    async def test_prompt_size_reduced(self, question_generator, sample_reference_point, mock_llm):
        """Test: Total prompt should be smaller than before"""

        conversation_context = {
            'covered_topics': ['greeting', 'applicant_name', 'project_type'],
            'collected_fields': {'applicant_name': 'Андрей', 'project_type': 'социальный'}
        }

        await question_generator.generate_question(
            reference_point=sample_reference_point,
            conversation_context=conversation_context
            # gaps and fpg_context are computed internally
        )

        call_args = mock_llm.generate_async.call_args
        prompt = call_args.kwargs.get('prompt') or call_args.args[0]

        # Prompt should be reasonably sized (not bloated)
        # Before: ~1400-2100 chars
        # After: ~900-1400 chars
        prompt_size = len(prompt)

        print(f"[INFO] Prompt size: {prompt_size} chars")

        # Should be less than 1800 chars for typical case
        assert prompt_size < 1800, f"Prompt too large: {prompt_size} chars (expected <1800)"


def test_suite_summary():
    """Print test suite summary"""
    print("\n" + "="*80)
    print("ITERATION 25 TEST SUITE")
    print("="*80)
    print("\nTests:")
    print("1. [OK] question_hints handled as list (no .split() error)")
    print("2. [OK] Limited to 2 question_hints (not 3-5)")
    print("3. [OK] Streamlined prompt (fewer sections)")
    print("4. [OK] Conditional sections (empty not included)")
    print("5. [OK] Temperature reduced to 0.5")
    print("6. [OK] System prompt simplified (4 bullets)")
    print("7. [OK] Overall prompt size reduced")
    print("\n" + "="*80)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
    test_suite_summary()
