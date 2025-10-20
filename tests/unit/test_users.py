#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit тесты для data/database/users.py
"""

import pytest
import sys
from pathlib import Path

tests_dir = Path(__file__).parent.parent
sys.path.insert(0, str(tests_dir))

from fixtures.test_data import EXPECTED_MIGRATION_DATA


@pytest.mark.unit
class TestUserManager:
    """Тесты UserManager"""

    def test_register_user(self, user_manager, test_user_data, cleanup_test_user):
        """Тест: регистрация нового пользователя"""
        result = user_manager.register_user(
            telegram_id=test_user_data['telegram_id'],
            username=test_user_data['username'],
            first_name=test_user_data['first_name'],
            last_name=test_user_data['last_name']
        )

        assert result == True

    def test_register_user_without_username(self, user_manager, cleanup_test_user):
        """Тест: регистрация пользователя без username"""
        result = user_manager.register_user(
            telegram_id=999999998,
            username=None,
            first_name='NoUsername',
            last_name='User'
        )

        # Должно успешно зарегистрировать
        assert result == True

        # Cleanup
        with user_manager.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE telegram_id = %s", (999999998,))
            cursor.execute("DELETE FROM users WHERE telegram_id = %s", (999999998,))
            conn.commit()
            cursor.close()

    def test_get_all_users(self, user_manager):
        """Тест: получение всех пользователей"""
        users = user_manager.get_all_users()

        assert users is not None
        assert len(users) >= EXPECTED_MIGRATION_DATA['users_count'], \
            f"Ожидается минимум {EXPECTED_MIGRATION_DATA['users_count']} пользователей после миграции"

    def test_user_has_statistics(self, user_manager):
        """Тест: пользователи содержат статистику"""
        users = user_manager.get_all_users()

        if len(users) > 0:
            user = users[0]
            # Проверяем наличие статистических полей
            assert 'sessions_count' in user or 'total_sessions' in user
            assert 'completed_sessions' in user
            sessions_field = 'sessions_count' if 'sessions_count' in user else 'total_sessions'
            assert user[sessions_field] is not None


@pytest.mark.unit
class TestUserCounts:
    """Тесты подсчета пользователей"""

    def test_get_total_users_after_migration(self, db):
        """Тест: количество пользователей после миграции соответствует ожидаемому"""
        from data.database.users import get_total_users

        total = get_total_users()

        assert total >= EXPECTED_MIGRATION_DATA['users_count'], \
            f"Ожидается минимум {EXPECTED_MIGRATION_DATA['users_count']} пользователей, получено {total}"

    def test_total_users_matches_db(self, db):
        """Тест: get_total_users() возвращает точное количество из БД"""
        from data.database.users import get_total_users

        # Получаем через функцию
        function_count = get_total_users()

        # Получаем напрямую из БД
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            db_count = cursor.fetchone()[0]
            cursor.close()

        assert function_count == db_count


@pytest.mark.unit
class TestUserData:
    """Тесты данных пользователей"""

    def test_user_has_telegram_id(self, user_manager):
        """Тест: каждый пользователь имеет telegram_id"""
        users = user_manager.get_all_users()

        for user in users:
            assert 'telegram_id' in user
            assert user['telegram_id'] is not None
            assert isinstance(user['telegram_id'], int)

    def test_user_has_timestamps(self, user_manager):
        """Тест: каждый пользователь имеет временные метки"""
        users = user_manager.get_all_users()

        for user in users:
            assert 'registration_date' in user
            assert user['registration_date'] is not None

    def test_user_role_valid(self, user_manager):
        """Тест: роль пользователя валидна"""
        valid_roles = ['user', 'coordinator', 'admin']
        users = user_manager.get_all_users()

        for user in users:
            if user.get('role'):
                assert user['role'] in valid_roles, \
                    f"Недопустимая роль {user['role']} для пользователя {user['telegram_id']}"


@pytest.mark.unit
class TestUserEdgeCases:
    """Тесты граничных случаев"""

    def test_register_user_with_long_name(self, user_manager, cleanup_test_user):
        """Тест: регистрация пользователя с очень длинным именем"""
        long_name = "A" * 100

        result = user_manager.register_user(
            telegram_id=999999997,
            username='test_long_name',
            first_name=long_name,
            last_name=long_name
        )

        # Должно успешно зарегистрировать (БД должна обрезать или принять)
        assert result == True

        # Cleanup
        with user_manager.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE telegram_id = %s", (999999997,))
            cursor.execute("DELETE FROM users WHERE telegram_id = %s", (999999997,))
            conn.commit()
            cursor.close()

    def test_user_with_only_telegram_id(self, user_manager, cleanup_test_user):
        """Тест: создание пользователя только с telegram_id"""
        result = user_manager.register_user(
            telegram_id=999999996,
            username=None,
            first_name=None,
            last_name=None
        )

        assert result == True

        # Cleanup
        with user_manager.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE telegram_id = %s", (999999996,))
            cursor.execute("DELETE FROM users WHERE telegram_id = %s", (999999996,))
            conn.commit()
            cursor.close()
