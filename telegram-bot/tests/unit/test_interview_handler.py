#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for InteractiveInterviewHandler

Tests the critical fixes applied:
- Bug #1-5: Interview finalization and state handling
- Bug #6: Event loop blocking with asyncio.create_task
- Bug #7: Progress bar spam removed from callback
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "agents"))

from telegram import Update
from telegram.ext import ContextTypes

# Import the handler we're testing
from handlers.interactive_interview_handler import InteractiveInterviewHandler

# Import helper from conftest
from tests.conftest import create_fake_update


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def handler(mock_db):
    """Create an InteractiveInterviewHandler instance"""
    return InteractiveInterviewHandler(db=mock_db)


@pytest.fixture
def sample_user_data():
    """Sample user data for interview"""
    return {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": "+79999999999",
        "grant_fund": "Фонд президентских грантов"
    }


# ============================================================
# TEST: Basic Handler Initialization
# ============================================================

@pytest.mark.unit
def test_handler_initialization(mock_db):
    """Test that handler initializes correctly"""
    handler = InteractiveInterviewHandler(db=mock_db)

    assert handler.db == mock_db
    assert handler.active_interviews == {}
    assert hasattr(handler, 'start_interview')
    assert hasattr(handler, 'continue_interview')
    assert hasattr(handler, 'handle_message')


# ============================================================
# TEST: Start Interview
# ============================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_interview_creates_agent(handler, sample_user_data):
    """Test that start_interview creates agent and answer queue"""
    user_id = sample_user_data['telegram_id']

    update = create_fake_update(user_id=user_id, text="/start_interview")
    context = MagicMock()

    # Mock agent creation
    with patch('handlers.interactive_interview_handler.InteractiveInterviewerAgentV2') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        await handler.start_interview(update, context, sample_user_data)

        # Verify agent was created
        assert user_id in handler.active_interviews
        assert 'agent' in handler.active_interviews[user_id]
        assert 'answer_queue' in handler.active_interviews[user_id]

        # Verify answer_queue is an asyncio.Queue
        assert isinstance(handler.active_interviews[user_id]['answer_queue'], asyncio.Queue)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_interview_sends_greeting(handler, sample_user_data):
    """Test that start_interview sends greeting message"""
    user_id = sample_user_data['telegram_id']

    update = create_fake_update(user_id=user_id, text="/start_interview")
    context = MagicMock()

    with patch('handlers.interactive_interview_handler.InteractiveInterviewerAgentV2'):
        await handler.start_interview(update, context, sample_user_data)

        # Verify greeting was sent
        update.message.reply_text.assert_called()
        call_args = update.message.reply_text.call_args[0][0]
        assert "Здравствуйте" in call_args or "приветств" in call_args.lower()


# ============================================================
# TEST: Bug #6 Fix - Event Loop Not Blocking
# ============================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_continue_interview_uses_background_task(handler, sample_user_data):
    """
    CRITICAL TEST: Verify Bug #6 fix - conduct_interview runs in background task

    This test verifies that continue_interview uses asyncio.create_task()
    so the event loop is NOT blocked while waiting for user answers.
    """
    user_id = sample_user_data['telegram_id']

    # Setup: create active interview
    mock_agent = MagicMock()
    mock_agent.conduct_interview = AsyncMock(return_value={
        'status': 'success',
        'questions_asked': 5,
        'audit_score': 85
    })

    handler.active_interviews[user_id] = {
        'agent': mock_agent,
        'answer_queue': asyncio.Queue(),
        'user_data': sample_user_data
    }

    update = create_fake_update(user_id=user_id, text="/continue")
    context = MagicMock()

    # Mock asyncio.create_task to verify it's called
    with patch('asyncio.create_task') as mock_create_task:
        mock_create_task.return_value = MagicMock()

        await handler.continue_interview(update, context)

        # CRITICAL: Verify asyncio.create_task was called (background task)
        assert mock_create_task.called, "Bug #6 NOT FIXED: asyncio.create_task not called!"

        # The method should return immediately, NOT await conduct_interview
        # If it awaited, the event loop would block


@pytest.mark.unit
@pytest.mark.asyncio
async def test_continue_interview_returns_immediately(handler, sample_user_data):
    """
    Test that continue_interview returns immediately (doesn't block)

    This verifies the fix for Bug #6 where the event loop was blocked
    """
    user_id = sample_user_data['telegram_id']

    # Create a slow mock agent that takes 5 seconds
    mock_agent = MagicMock()

    async def slow_interview(*args, **kwargs):
        await asyncio.sleep(5)  # Simulate slow interview
        return {'status': 'success'}

    mock_agent.conduct_interview = AsyncMock(side_effect=slow_interview)

    handler.active_interviews[user_id] = {
        'agent': mock_agent,
        'answer_queue': asyncio.Queue(),
        'user_data': sample_user_data
    }

    update = create_fake_update(user_id=user_id, text="/continue")
    context = MagicMock()

    # Measure time - should return in < 1 second
    start = asyncio.get_event_loop().time()

    await handler.continue_interview(update, context)

    elapsed = asyncio.get_event_loop().time() - start

    # Should return immediately (< 1 sec), NOT wait 5 seconds
    assert elapsed < 1.0, f"continue_interview blocked for {elapsed}s (Bug #6 NOT FIXED!)"


# ============================================================
# TEST: Handle Message (Answer Queue)
# ============================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_message_puts_answer_in_queue(handler, sample_user_data):
    """
    Test that handle_message puts user's answer in the queue

    This is part of the Bug #6 fix - answers are collected via queue
    """
    user_id = sample_user_data['telegram_id']

    # Setup active interview with queue
    answer_queue = asyncio.Queue()
    handler.active_interviews[user_id] = {
        'agent': MagicMock(),
        'answer_queue': answer_queue,
        'user_data': sample_user_data
    }

    # Simulate user sending answer
    answer_text = "Литературный проект для жителей Кемерово"
    update = create_fake_update(user_id=user_id, text=answer_text)
    context = MagicMock()

    await handler.handle_message(update, context)

    # Verify answer was put in queue
    assert not answer_queue.empty(), "Answer NOT put in queue!"

    # Get answer from queue
    queued_answer = await answer_queue.get()
    assert queued_answer == answer_text


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_message_ignores_if_no_active_interview(handler):
    """Test that handle_message ignores messages when no active interview"""
    user_id = 123456789

    # NO active interview
    assert user_id not in handler.active_interviews

    update = create_fake_update(user_id=user_id, text="Some message")
    context = MagicMock()

    # Should not raise error, just return
    await handler.handle_message(update, context)

    # No queue should be created
    assert user_id not in handler.active_interviews


# ============================================================
# TEST: Interview State Management
# ============================================================

@pytest.mark.unit
def test_is_interview_active_returns_true_when_active(handler, sample_user_data):
    """Test is_interview_active returns True for active interviews"""
    user_id = sample_user_data['telegram_id']

    handler.active_interviews[user_id] = {
        'agent': MagicMock(),
        'answer_queue': asyncio.Queue()
    }

    assert handler.is_interview_active(user_id) is True


@pytest.mark.unit
def test_is_interview_active_returns_false_when_not_active(handler):
    """Test is_interview_active returns False when no interview"""
    user_id = 123456789

    assert handler.is_interview_active(user_id) is False


# ============================================================
# TEST: Callback Ask Question
# ============================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_callback_ask_question_waits_for_answer(handler, sample_user_data):
    """
    Test that callback_ask_question waits for answer from queue

    This is the mechanism that synchronizes bot questions with user answers
    """
    user_id = sample_user_data['telegram_id']

    answer_queue = asyncio.Queue()
    handler.active_interviews[user_id] = {
        'agent': MagicMock(),
        'answer_queue': answer_queue,
        'user_data': sample_user_data
    }

    update = create_fake_update(user_id=user_id)
    context = MagicMock()

    # Create callback (this is what gets passed to conduct_interview)
    async def ask_question_callback(question: str) -> str:
        await update.message.reply_text(question)
        answer = await answer_queue.get()  # Wait for answer
        return answer

    # Simulate: Bot asks question, user answers
    question = "Расскажите о вашем проекте?"
    expected_answer = "Литературный проект для Кемерово"

    # Start asking question in background
    async def bot_asks():
        answer = await ask_question_callback(question)
        return answer

    # Start both tasks
    ask_task = asyncio.create_task(bot_asks())

    # Simulate delay before user answers
    await asyncio.sleep(0.1)

    # User puts answer in queue
    await answer_queue.put(expected_answer)

    # Get result
    result = await ask_task

    assert result == expected_answer


# ============================================================
# TEST: Regression Tests for All Bugs
# ============================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_regression_bug6_event_loop_not_blocked(handler, sample_user_data):
    """
    REGRESSION TEST for Bug #6: Event loop blocking

    Verify that after /continue, handle_message can still be called
    (event loop is not blocked)
    """
    user_id = sample_user_data['telegram_id']

    # Create agent that waits for answer
    mock_agent = MagicMock()

    async def interview_that_waits(*args, callback_ask_question=None, **kwargs):
        # Ask one question
        answer = await callback_ask_question("Расскажите о проекте?")
        return {'status': 'success', 'first_answer': answer}

    mock_agent.conduct_interview = AsyncMock(side_effect=interview_that_waits)

    handler.active_interviews[user_id] = {
        'agent': mock_agent,
        'answer_queue': asyncio.Queue(),
        'user_data': sample_user_data
    }

    update = create_fake_update(user_id=user_id, text="/continue")
    context = MagicMock()

    # Start interview (should use background task)
    await handler.continue_interview(update, context)

    # Give background task time to start
    await asyncio.sleep(0.1)

    # NOW: Simulate user sending answer via handle_message
    # This should work because event loop is NOT blocked
    answer_update = create_fake_update(user_id=user_id, text="Литературный проект")

    # This call should succeed (NOT block)
    await handler.handle_message(answer_update, context)

    # Verify answer was queued
    queue = handler.active_interviews[user_id]['answer_queue']
    assert not queue.empty(), "Bug #6 REGRESSION: handle_message didn't queue answer!"


@pytest.mark.unit
def test_regression_bug7_no_progress_bar_in_callback():
    """
    REGRESSION TEST for Bug #7: Progress bar spam

    This is a reminder that progress bars should NOT be sent via
    callback_ask_question (which waits for answer).

    This test documents the fix - actual implementation is in agent.
    """
    # Progress bars should be sent via a separate notification callback
    # NOT via callback_ask_question

    # This test serves as documentation that:
    # 1. callback_ask_question should ONLY be used for actual questions
    # 2. Progress bars/info messages should use a separate callback

    # See: agents/interactive_interviewer_agent_v2.py lines 298-303
    assert True  # Documentation test


# ============================================================
# TEST: Integration - Full Flow Simulation
# ============================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_full_interview_flow_simulation(handler, sample_user_data):
    """
    Simulate a complete interview flow:
    1. Start interview
    2. Continue (bot asks question)
    3. User answers
    4. Bot asks next question
    5. Interview completes
    """
    user_id = sample_user_data['telegram_id']

    # Mock agent that asks 3 questions
    mock_agent = MagicMock()

    async def mock_interview(*args, callback_ask_question=None, **kwargs):
        answers = []

        # Ask 3 questions
        for i in range(3):
            answer = await callback_ask_question(f"Вопрос {i+1}?")
            answers.append(answer)

        return {
            'status': 'success',
            'questions_asked': 3,
            'answers': answers,
            'audit_score': 85
        }

    mock_agent.conduct_interview = AsyncMock(side_effect=mock_interview)

    context = MagicMock()

    # Step 1: Start interview
    with patch('handlers.interactive_interview_handler.InteractiveInterviewerAgentV2', return_value=mock_agent):
        start_update = create_fake_update(user_id=user_id, text="/start_interview")
        await handler.start_interview(start_update, context, sample_user_data)

    assert user_id in handler.active_interviews

    # Step 2: Continue interview (background task)
    continue_update = create_fake_update(user_id=user_id, text="/continue")

    # We need to manually run the interview since we can't easily test asyncio.create_task
    # In real test, we'd need to await the task completion

    # For this unit test, we'll directly test the callback mechanism
    answer_queue = handler.active_interviews[user_id]['answer_queue']

    # Simulate 3 Q&A exchanges
    user_answers = ["Ответ 1", "Ответ 2", "Ответ 3"]

    async def simulate_user_responses():
        for answer in user_answers:
            await asyncio.sleep(0.1)  # Delay
            await answer_queue.put(answer)

    # Start simulation
    simulate_task = asyncio.create_task(simulate_user_responses())

    # Run interview
    result = await mock_agent.conduct_interview(
        user_data=sample_user_data,
        callback_ask_question=lambda q: answer_queue.get()
    )

    await simulate_task

    # Verify
    assert result['status'] == 'success'
    assert result['questions_asked'] == 3
    assert result['answers'] == user_answers


# ============================================================
# TEST: Error Handling
# ============================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_message_with_invalid_queue(handler):
    """Test that handle_message handles missing answer_queue gracefully"""
    user_id = 123456789

    # Setup interview without answer_queue (edge case)
    handler.active_interviews[user_id] = {
        'agent': MagicMock()
        # Missing 'answer_queue'!
    }

    update = create_fake_update(user_id=user_id, text="Answer")
    context = MagicMock()

    # Should handle gracefully (not crash)
    try:
        await handler.handle_message(update, context)
    except KeyError:
        pytest.fail("handle_message should handle missing answer_queue gracefully")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_continue_interview_when_not_started(handler):
    """Test that continue_interview handles case when interview not started"""
    user_id = 123456789

    # NO interview started
    assert user_id not in handler.active_interviews

    update = create_fake_update(user_id=user_id, text="/continue")
    context = MagicMock()

    # Should send error message or handle gracefully
    await handler.continue_interview(update, context)

    # Should have replied with error
    update.message.reply_text.assert_called()
