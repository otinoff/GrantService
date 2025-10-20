#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Фикстуры для работы с PostgreSQL базой данных
"""

import pytest
import os
from data.database.models import GrantServiceDatabase
from data.database.users import UserManager
from data.database.interview import InterviewManager
from data.database.sessions import SessionManager


@pytest.fixture(scope='function')
def db():
    """
    Фикстура PostgreSQL database instance
    Scope: function - создается для каждого теста
    """
    database = GrantServiceDatabase()
    yield database
    # Cleanup после каждого теста не требуется - работаем с реальной БД


@pytest.fixture(scope='function')
def user_manager(db):
    """Менеджер пользователей"""
    return UserManager(db)


@pytest.fixture(scope='function')
def interview_manager(db):
    """Менеджер интервью"""
    return InterviewManager(db)


@pytest.fixture(scope='function')
def session_manager(db):
    """Менеджер сессий"""
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
            cursor.execute("DELETE FROM user_answers WHERE session_id IN (SELECT id FROM sessions WHERE telegram_id = %s)", (test_user_data['telegram_id'],))
            cursor.execute("DELETE FROM sessions WHERE telegram_id = %s", (test_user_data['telegram_id'],))
            cursor.execute("DELETE FROM users WHERE telegram_id = %s", (test_user_data['telegram_id'],))
            conn.commit()
            cursor.close()
            print(f"\n[CLEANUP] Удален тестовый пользователь {test_user_data['telegram_id']}")
    except Exception as e:
        print(f"\n[WARNING] Ошибка при очистке тестовых данных: {e}")
