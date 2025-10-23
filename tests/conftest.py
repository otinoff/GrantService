#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурация pytest для GrantService
FIXED: Lazy imports для database modules чтобы не ломать smoke tests
"""

import os
import sys
import pytest
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Устанавливаем переменные окружения для PostgreSQL
os.environ['PGHOST'] = os.getenv('PGHOST', 'localhost')
os.environ['PGPORT'] = os.getenv('PGPORT', '5432')
os.environ['PGDATABASE'] = os.getenv('PGDATABASE', 'grantservice')
os.environ['PGUSER'] = os.getenv('PGUSER', 'postgres')
os.environ['PGPASSWORD'] = os.getenv('PGPASSWORD', 'root')

# Настройка логирования для тестов
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)

@pytest.fixture(scope='session')
def project_root_path():
    """Корневая директория проекта"""
    return project_root

@pytest.fixture(scope='session')
def db_config():
    """Конфигурация PostgreSQL из переменных окружения"""
    return {
        'host': os.environ['PGHOST'],
        'port': int(os.environ['PGPORT']),
        'database': os.environ['PGDATABASE'],
        'user': os.environ['PGUSER'],
        'password': os.environ['PGPASSWORD']
    }

def pytest_configure(config):
    """Настройка pytest перед запуском тестов"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test"
    )


# ========== DATABASE FIXTURES ==========
# IMPORTANT: Lazy imports inside fixtures to not break smoke tests!

@pytest.fixture(scope='function')
def db():
    """
    Фикстура PostgreSQL database instance
    Scope: function - создается для каждого теста

    LAZY IMPORT: импорт происходит только когда фикстура используется
    """
    from data.database.models import GrantServiceDatabase
    database = GrantServiceDatabase()
    yield database
    # Cleanup после каждого теста не требуется - работаем с реальной БД


@pytest.fixture(scope='function')
def user_manager(db):
    """Менеджер пользователей"""
    from data.database.users import UserManager
    return UserManager(db)


@pytest.fixture(scope='function')
def interview_manager(db):
    """Менеджер интервью"""
    from data.database.interview import InterviewManager
    return InterviewManager(db)


@pytest.fixture(scope='function')
def session_manager(db):
    """Менеджер сессий"""
    from data.database.sessions import SessionManager
    return SessionManager(db)


@pytest.fixture(scope='function')
def test_user_data():
    """Тестовые данные пользователя"""
    return {
        'telegram_id': 999999999,  # Тестовый ID, не конфликтующий с реальными
        'username': 'test_user_pytest',
        'first_name': 'Test',
        'last_name': 'User'
    }


@pytest.fixture(scope='function')
def cleanup_test_user(db, test_user_data):
    """
    Фикстура для очистки тестового пользователя после теста
    """
    yield
    # Cleanup после теста
    try:
        with db.connect() as conn:
            cursor = conn.cursor()
            # Удаляем тестового пользователя и все связанные данные
            # grant_applications привязаны через session_id, а не telegram_id
            cursor.execute("DELETE FROM grant_applications WHERE session_id IN (SELECT id FROM sessions WHERE telegram_id = %s)", (test_user_data['telegram_id'],))
            cursor.execute("DELETE FROM user_answers WHERE session_id IN (SELECT id FROM sessions WHERE telegram_id = %s)", (test_user_data['telegram_id'],))
            cursor.execute("DELETE FROM sessions WHERE telegram_id = %s", (test_user_data['telegram_id'],))
            cursor.execute("DELETE FROM users WHERE telegram_id = %s", (test_user_data['telegram_id'],))
            conn.commit()
            cursor.close()
            print(f"\n[CLEANUP] Удален тестовый пользователь {test_user_data['telegram_id']}")
    except Exception as e:
        print(f"\n[WARNING] Ошибка при очистке тестовых данных: {e}")
