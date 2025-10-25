#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest configuration and fixtures for GrantService bot tests

Provides mock objects and helpers for testing without real Telegram API calls
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock
from typing import Dict, Any

# Mock Telegram objects
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes


# ============================================================
# FIXTURES: Mock Telegram Objects
# ============================================================

@pytest.fixture
def mock_user():
    """Create a mock Telegram User"""
    user = User(
        id=123456789,
        first_name='Test',
        is_bot=False,
        username='testuser',
        last_name='User'
    )
    return user


@pytest.fixture
def mock_chat():
    """Create a mock Telegram Chat"""
    chat = Chat(
        id=123456789,
        type='private'
    )
    return chat


def create_fake_update(
    user_id: int = 123456789,
    text: str = "/start",
    username: str = "testuser",
    chat_type: str = 'private'
) -> Update:
    """
    Create a fake Telegram Update object for testing

    Args:
        user_id: Telegram user ID
        text: Message text
        username: Username
        chat_type: Type of chat (private, group, etc.)

    Returns:
        Mock Update object
    """
    message = Message(
        message_id=1,
        date=datetime.now(),
        chat=Chat(id=user_id, type=chat_type),
        from_user=User(
            id=user_id,
            first_name='Test',
            username=username,
            is_bot=False,
            last_name='User'
        ),
        text=text
    )

    # Mock reply_text method
    message.reply_text = AsyncMock(return_value=message)

    update = Update(
        update_id=1,
        message=message
    )

    return update


@pytest.fixture
def fake_update():
    """Fixture that creates a fake Update"""
    return create_fake_update()


@pytest.fixture
def mock_context():
    """Create a mock Context object"""
    context = MagicMock()
    context.bot = AsyncMock()
    context.bot.send_message = AsyncMock()
    context.user_data = {}
    context.chat_data = {}
    return context


# ============================================================
# FIXTURES: Mock Database
# ============================================================

@pytest.fixture
def mock_db():
    """Create a mock GrantServiceDatabase"""
    db = MagicMock()

    # Mock database methods
    db.get_user = AsyncMock(return_value={
        'id': 123456789,
        'username': 'testuser',
        'authorized': True
    })

    db.save_interview = AsyncMock(return_value={'interview_id': 1})
    db.get_interview = AsyncMock(return_value=None)
    db.update_interview = AsyncMock(return_value=True)

    return db


# ============================================================
# FIXTURES: Mock LLM
# ============================================================

@pytest.fixture
def mock_llm():
    """Create a mock UnifiedLLMClient"""
    llm = AsyncMock()

    # Mock generate_async to return realistic questions
    async def generate_question(*args, **kwargs):
        return "Расскажите о вашем проекте подробнее?"

    llm.generate_async = AsyncMock(side_effect=generate_question)

    return llm


# ============================================================
# FIXTURES: Mock Interview Components
# ============================================================

@pytest.fixture
def mock_reference_point():
    """Create a mock ReferencePoint"""
    from unittest.mock import MagicMock

    rp = MagicMock()
    rp.id = 'project_description'
    rp.priority = 'P0_CRITICAL'
    rp.is_complete = MagicMock(return_value=False)
    rp.add_answer = MagicMock()
    rp.get_completeness_score = MagicMock(return_value=0.5)

    return rp


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
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
# FIXTURES: Answer Queue for Testing
# ============================================================

@pytest.fixture
async def answer_queue():
    """Create an asyncio Queue for testing answer flow"""
    queue = asyncio.Queue()
    return queue


# ============================================================
# HELPERS: Test Utilities
# ============================================================

class AsyncQueueHelper:
    """Helper for testing async queue operations"""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.responses = []

    async def simulate_user_answer(self, answer: str):
        """Simulate user putting answer in queue"""
        await self.queue.put(answer)

    async def get_answer(self):
        """Get answer from queue"""
        answer = await self.queue.get()
        self.responses.append(answer)
        return answer


@pytest.fixture
def queue_helper():
    """Fixture for AsyncQueueHelper"""
    return AsyncQueueHelper()


# ============================================================
# PYTEST CONFIGURATION
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """Pytest configuration"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires Telethon)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


# ============================================================
# MOCK INTERVIEW STATE
# ============================================================

@pytest.fixture
def mock_interview_state():
    """Create a mock interview state"""
    return {
        'user_id': 123456789,
        'agent': MagicMock(),
        'answer_queue': asyncio.Queue(),
        'started_at': datetime.now(),
        'state': 'active'
    }
