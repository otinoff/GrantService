#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Configuration and Fixtures for Interactive Interviewer Agent V2

Provides test fixtures for unit, integration, and E2E tests.
"""

import sys
from pathlib import Path
import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock

# Add project root to path
_project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "agents"))
sys.path.insert(0, str(_project_root / "data"))

from data.database.models import GrantServiceDatabase


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def test_db():
    """Real database connection for integration tests."""
    db = GrantServiceDatabase()
    yield db
    # Cleanup if needed


@pytest.fixture
def test_anketa():
    """Sample anketa data for testing."""
    return {
        'project_name': 'AI Grant Assistant Test',
        'project_description': 'Тестовая система для автоматизации подачи грантовых заявок',
        'target_audience': 'Молодые учёные и исследователи',
        'grant_type': 'Фонд Президентских Грантов',
        'budget_total': '1500000',
        'budget_breakdown': {
            'personnel': '800000',
            'equipment': '400000',
            'other': '300000'
        },
        'timeline': '12 месяцев',
        'expected_results': 'Рабочий прототип AI-ассистента',
        'team_size': '5',
        'has_experience': 'да',
        'previous_grants': 'Грант РФФИ 2023',
        'social_impact': 'Упрощение доступа к грантам для молодых учёных'
    }


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        'telegram_id': 123456789,
        'username': 'test_user',
        'first_name': 'Test',
        'last_name': 'User'
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing without real API calls."""
    mock = AsyncMock()

    # Default response for question generation
    mock.generate_text.return_value = "Расскажите подробнее о целевой аудитории проекта?"

    # Default response for validation
    mock.validate_response.return_value = True

    return mock


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing without vector DB."""
    mock = Mock()

    # Default search response
    mock.search.return_value = [
        Mock(payload={'text': 'Sample knowledge base entry'}, score=0.95)
    ]

    return mock


@pytest.fixture
def mock_callback_ask_question():
    """Mock callback for asking questions in tests."""
    questions_asked = []
    answers = [
        "AI Grant Assistant - система для автоматизации грантов",
        "Молодые учёные и исследователи до 35 лет",
        "Фонд Президентских Грантов",
        "1 500 000 рублей",
        "12 месяцев",
        "Рабочий прототип с веб-интерфейсом",
        "5 человек: 2 разработчика, 1 дизайнер, 1 менеджер, 1 тестировщик",
        "Да, получали грант РФФИ в 2023 году",
        "Упрощение доступа к грантовому финансированию",
        "Уже есть MVP, нужны средства на развитие"
    ]
    answer_index = [0]  # Mutable counter

    async def callback(question: str) -> str:
        questions_asked.append(question)
        idx = answer_index[0]
        answer_index[0] += 1
        return answers[idx] if idx < len(answers) else "Тестовый ответ"

    callback.questions_asked = questions_asked
    callback.answers = answers

    return callback


# =============================================================================
# AGENT FIXTURES
# =============================================================================

@pytest.fixture
def mock_agent_with_llm(test_db, mock_llm_client):
    """Interviewer agent with mocked LLM for controlled testing."""
    from agents.interactive_interviewer_v2.agent import InteractiveInterviewerAgentV2

    agent = InteractiveInterviewerAgentV2(
        db=test_db,
        llm_provider="gigachat",
        qdrant_host=None,  # Disable Qdrant for speed
        qdrant_port=None
    )

    # Replace LLM with mock
    agent.llm = mock_llm_client

    return agent


@pytest.fixture
def real_agent(test_db):
    """Real interviewer agent for E2E tests (uses real LLM)."""
    from agents.interactive_interviewer_v2.agent import InteractiveInterviewerAgentV2

    agent = InteractiveInterviewerAgentV2(
        db=test_db,
        llm_provider="gigachat",
        qdrant_host="localhost",
        qdrant_port=6333
    )

    return agent


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_reference_points():
    """Sample reference points for testing."""
    return [
        {
            'key': 'project_name',
            'required': True,
            'priority': 1,
            'category': 'basic',
            'description': 'Название проекта'
        },
        {
            'key': 'project_description',
            'required': True,
            'priority': 1,
            'category': 'basic',
            'description': 'Описание проекта'
        },
        {
            'key': 'target_audience',
            'required': True,
            'priority': 2,
            'category': 'basic',
            'description': 'Целевая аудитория'
        }
    ]


@pytest.fixture
def sample_audit_result():
    """Sample audit result for testing."""
    return {
        'final_score': 85,
        'status': 'success',
        'criteria_scores': {
            'relevance': 90,
            'feasibility': 85,
            'innovation': 80,
            'impact': 85
        },
        'recommendations': [
            'Усилить описание социального эффекта',
            'Добавить количественные показатели результатов'
        ]
    }


@pytest.fixture
def sample_grant_content():
    """Sample grant text for testing."""
    return """
# Грантовая заявка: AI Grant Assistant

## Название проекта
AI Grant Assistant - Интеллектуальная система автоматизации грантовых заявок

## Описание проекта
Система использует технологии искусственного интеллекта для автоматизации
процесса подготовки грантовых заявок...

## Целевая аудитория
Молодые учёные и исследователи в возрасте до 35 лет...

## Бюджет
Общий бюджет: 1 500 000 рублей
- Зарплаты: 800 000 рублей
- Оборудование: 400 000 рублей
- Прочие расходы: 300 000 рублей
"""
