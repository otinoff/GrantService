"""
Integration test fixtures for GrantService.

Provides:
- test_db: Real database connection (using test database)
- test_anketa: Realistic test anketa data
- mock_gigachat: Mocked GigaChat responses
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load test environment
os.environ['ENV_FILE'] = '.env.test'


@pytest.fixture(scope="session")
def test_env():
    """Ensure test environment is loaded"""
    # Force load .env.test
    from dotenv import load_dotenv
    load_dotenv('.env.test', override=True)

    # Verify test mode
    assert os.getenv('ENVIRONMENT') == 'test', "Must run in test environment!"

    return {
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'GIGACHAT_API_KEY': os.getenv('GIGACHAT_API_KEY'),
    }


@pytest.fixture(scope="module")
def test_db(test_env):
    """
    Provide real database connection for tests.
    Uses grantservice_test database.
    """
    # Import database module
    try:
        from data.database.models import GrantServiceDatabase

        # Create test DB connection
        db = GrantServiceDatabase()

        yield db

        # Cleanup: Don't actually need to truncate for tests
        # Each test should use unique IDs

    except Exception as e:
        pytest.skip(f"Database not available: {e}")


@pytest.fixture
def test_anketa():
    """Realistic test anketa data"""
    timestamp = int(datetime.now().timestamp())

    return {
        'id': f'test_anketa_{timestamp}',
        'user_id': 99999,  # Test user ID
        'telegram_id': 99999,
        'project_name': 'Тестовый инновационный проект',
        'organization': 'Тестовая Организация ТОО',
        'budget': 1000000,
        'duration_months': 12,
        'goal': 'Разработать инновационное решение для тестирования грантовых заявок',
        'target_audience': 'Исследователи, разработчики, научные организации',
        'expected_results': 'Создание рабочего прототипа автоматизированной системы',
        'team_experience': 'Команда с опытом реализации проектов более 5 лет',
        'methodology': 'Agile методология с итеративной разработкой',
        'innovations': 'Использование AI для автоматической генерации заявок',
        'social_impact': 'Упрощение процесса подачи грантовых заявок',
        'created_at': datetime.now().isoformat()
    }


@pytest.fixture
def mock_gigachat():
    """
    Mock GigaChat API responses.
    Returns AsyncMock that can be configured per test.

    NOTE: For basic smoke tests, we don't need to mock LLM calls.
    This fixture is here for future tests that actually call LLM methods.
    """
    # For now, just return a simple mock without patching anything
    # Since our smoke tests only instantiate agents without calling LLM methods
    mock_instance = AsyncMock()
    mock_instance.generate.return_value = {
        'status': 'success',
        'content': 'Тестовый ответ от GigaChat'
    }
    return mock_instance


@pytest.fixture
def sample_audit_result():
    """Sample audit result for testing"""
    return {
        'status': 'success',
        'audit_details': {
            'score': 8.5,
            'strengths': [
                'Четкая постановка цели',
                'Обоснованный бюджет',
                'Опытная команда'
            ],
            'weaknesses': [
                'Недостаточно конкретных метрик результата'
            ],
            'recommendations': [
                'Добавить конкретные KPI',
                'Детализировать методологию'
            ]
        }
    }


@pytest.fixture
def sample_grant_content():
    """Sample grant content for testing"""
    return """
# Грантовая заявка: Тестовый инновационный проект

## 1. Актуальность и обоснование

Проект направлен на решение важной проблемы в области автоматизации процесса подготовки грантовых заявок...

## 2. Цель и задачи проекта

**Основная цель:** Разработать инновационное решение для автоматизации подготовки грантовых заявок.

**Задачи:**
1. Провести анализ существующих решений
2. Разработать прототип системы
3. Протестировать на реальных данных
4. Внедрить в опытную эксплуатацию

## 3. Методология реализации

Проект будет реализован с использованием Agile методологии...

## 4. Бюджет проекта

**Общий бюджет:** 1 000 000 рублей

**Основные статьи расходов:**
- Оборудование и программное обеспечение: 500 000 руб
- Оплата труда специалистов: 400 000 руб
- Прочие расходы: 100 000 руб

## 5. Ожидаемые результаты

Ожидается создание работающего прототипа системы, который будет способен автоматически генерировать грантовые заявки на основе входных данных...

## 6. Команда проекта

Команда проекта состоит из опытных специалистов с опытом работы более 5 лет...

## 7. Инновационность

Проект использует современные технологии искусственного интеллекта...

## 8. Социальный эффект

Проект окажет положительное влияние на научное сообщество, упростив процесс подачи грантовых заявок...
""" * 3  # Multiply to get realistic length
