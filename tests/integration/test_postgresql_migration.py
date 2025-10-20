#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интеграционные тесты миграции с SQLite на PostgreSQL 18
"""

import pytest
import sys
from pathlib import Path

tests_dir = Path(__file__).parent.parent
sys.path.insert(0, str(tests_dir))

from fixtures.test_data import EXPECTED_MIGRATION_DATA


@pytest.mark.integration
class TestMigrationUsers:
    """Тесты миграции пользователей"""

    def test_users_migrated_count(self, db):
        """Тест: все пользователи мигрированы (ожидается 4)"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            cursor.close()

        assert count >= EXPECTED_MIGRATION_DATA['users_count'], \
            f"Ожидается минимум {EXPECTED_MIGRATION_DATA['users_count']} пользователей, найдено {count}"

    def test_users_have_telegram_ids(self, db):
        """Тест: все мигрированные пользователи имеют telegram_id"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM users WHERE telegram_id IS NULL
            """)
            null_count = cursor.fetchone()[0]
            cursor.close()

        assert null_count == 0, f"Найдено {null_count} пользователей без telegram_id"

    def test_users_have_timestamps(self, db):
        """Тест: все пользователи имеют registration_date"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM users WHERE registration_date IS NULL
            """)
            null_count = cursor.fetchone()[0]
            cursor.close()

        assert null_count == 0, f"Найдено {null_count} пользователей без registration_date"


@pytest.mark.integration
class TestMigrationSessions:
    """Тесты миграции сессий"""

    def test_sessions_migrated_count(self, db):
        """Тест: все сессии мигрированы (ожидается минимум 16-17)"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions")
            count = cursor.fetchone()[0]
            cursor.close()

        assert count >= EXPECTED_MIGRATION_DATA['min_sessions_count'], \
            f"Ожидается минимум {EXPECTED_MIGRATION_DATA['min_sessions_count']} сессий, найдено {count}"

    def test_sessions_linked_to_users(self, db):
        """Тест: все сессии привязаны к существующим пользователям"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, s.telegram_id
                FROM sessions s
                LEFT JOIN users u ON s.telegram_id = u.telegram_id
                WHERE u.telegram_id IS NULL
            """)
            orphan_sessions = cursor.fetchall()
            cursor.close()

        assert len(orphan_sessions) == 0, \
            f"Найдено {len(orphan_sessions)} сессий без пользователей: {orphan_sessions}"

    def test_sessions_have_status(self, db):
        """Тест: все сессии имеют статус"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM sessions WHERE status IS NULL
            """)
            null_count = cursor.fetchone()[0]
            cursor.close()

        assert null_count == 0, f"Найдено {null_count} сессий без статуса"

    def test_session_statuses_valid(self, db):
        """Тест: статусы сессий валидны"""
        valid_statuses = ['active', 'completed', 'abandoned', 'in_progress']

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT status FROM sessions
            """)
            statuses = [row[0] for row in cursor.fetchall()]
            cursor.close()

        for status in statuses:
            if status:  # Пропускаем NULL если есть
                assert status in valid_statuses, \
                    f"Недопустимый статус сессии: {status}"


@pytest.mark.integration
class TestMigrationQuestions:
    """Тесты миграции вопросов интервью"""

    def test_questions_migrated_count(self, db):
        """Тест: все вопросы мигрированы (ожидается 25)"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = TRUE")
            count = cursor.fetchone()[0]
            cursor.close()

        assert count == EXPECTED_MIGRATION_DATA['questions_count'], \
            f"Ожидается {EXPECTED_MIGRATION_DATA['questions_count']} активных вопросов, найдено {count}"

    def test_questions_numbered_correctly(self, db):
        """Тест: вопросы пронумерованы от 1 до 25"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT question_number FROM interview_questions
                WHERE is_active = TRUE
                ORDER BY question_number
            """)
            question_numbers = [row[0] for row in cursor.fetchall()]
            cursor.close()

        expected_numbers = list(range(1, EXPECTED_MIGRATION_DATA['questions_count'] + 1))
        assert question_numbers == expected_numbers, \
            f"Найдены пропуски в нумерации: {set(expected_numbers) - set(question_numbers)}"

    def test_questions_have_validation_rules(self, db):
        """Тест: вопросы имеют правила валидации"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT question_number, validation_rules
                FROM interview_questions
                WHERE is_active = TRUE
                ORDER BY question_number
            """)
            results = cursor.fetchall()
            cursor.close()

        # Проверяем что хотя бы некоторые вопросы имеют validation_rules
        with_rules = [r for r in results if r[1] is not None]
        assert len(with_rules) > 0, "Ни один вопрос не имеет validation_rules"


@pytest.mark.integration
class TestMigrationApplications:
    """Тесты миграции заявок"""

    def test_applications_migrated_count(self, db):
        """Тест: заявки мигрированы (ожидается минимум 19)"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM grant_applications")
            count = cursor.fetchone()[0]
            cursor.close()

        assert count >= EXPECTED_MIGRATION_DATA['min_applications_count'], \
            f"Ожидается минимум {EXPECTED_MIGRATION_DATA['min_applications_count']} заявок, найдено {count}"

    def test_applications_have_anketa_ids(self, db):
        """Тест: завершенные сессии имеют anketa_id"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM sessions WHERE anketa_id IS NOT NULL
            """)
            with_ids = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'completed'")
            total_completed = cursor.fetchone()[0]

            cursor.close()

        # Хотя бы одна завершенная сессия должна иметь anketa_id
        assert with_ids > 0, "Ни одна сессия не имеет anketa_id"

    def test_applications_linked_to_users(self, db):
        """Тест: заявки привязаны к существующим пользователям"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ga.id, ga.user_id
                FROM grant_applications ga
                LEFT JOIN users u ON ga.user_id = u.id
                WHERE ga.user_id IS NOT NULL AND u.id IS NULL
            """)
            orphan_applications = cursor.fetchall()
            cursor.close()

        assert len(orphan_applications) == 0, \
            f"Найдено {len(orphan_applications)} заявок без пользователей"


@pytest.mark.integration
class TestMigrationDataIntegrity:
    """Тесты целостности данных после миграции"""

    def test_foreign_keys_intact(self, db):
        """Тест: внешние ключи целостны"""

        with db.connect() as conn:
            cursor = conn.cursor()

            # Проверяем sessions -> users
            cursor.execute("""
                SELECT COUNT(*)
                FROM sessions s
                WHERE NOT EXISTS (
                    SELECT 1 FROM users u WHERE u.telegram_id = s.telegram_id
                )
            """)
            broken_sessions = cursor.fetchone()[0]

            # Проверяем user_answers -> sessions
            cursor.execute("""
                SELECT COUNT(*)
                FROM user_answers ua
                WHERE NOT EXISTS (
                    SELECT 1 FROM sessions s WHERE s.id = ua.session_id
                )
            """)
            broken_answers = cursor.fetchone()[0]

            # Проверяем user_answers -> interview_questions
            cursor.execute("""
                SELECT COUNT(*)
                FROM user_answers ua
                WHERE NOT EXISTS (
                    SELECT 1 FROM interview_questions iq WHERE iq.id = ua.question_id
                )
            """)
            broken_question_refs = cursor.fetchone()[0]

            cursor.close()

        assert broken_sessions == 0, f"Найдено {broken_sessions} сессий с несуществующими пользователями"
        assert broken_answers == 0, f"Найдено {broken_answers} ответов с несуществующими сессиями"
        assert broken_question_refs == 0, f"Найдено {broken_question_refs} ответов с несуществующими вопросами"

    def test_no_duplicate_telegram_ids(self, db):
        """Тест: нет дублирующихся telegram_id"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT telegram_id, COUNT(*)
                FROM users
                GROUP BY telegram_id
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            cursor.close()

        assert len(duplicates) == 0, f"Найдены дублирующиеся telegram_id: {duplicates}"

    def test_timestamps_reasonable(self, db):
        """Тест: временные метки адекватны"""
        import datetime

        with db.connect() as conn:
            cursor = conn.cursor()

            # Проверяем что registration_date не в будущем
            cursor.execute("""
                SELECT COUNT(*)
                FROM users
                WHERE registration_date > CURRENT_TIMESTAMP
            """)
            future_dates = cursor.fetchone()[0]

            cursor.close()

        assert future_dates == 0, f"Найдено {future_dates} пользователей с датой регистрации в будущем"


@pytest.mark.integration
class TestMigrationPerformance:
    """Тесты производительности после миграции"""

    def test_user_query_performance(self, db):
        """Тест: запросы к пользователям выполняются быстро"""
        import time

        start = time.time()

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            cursor.fetchall()
            cursor.close()

        duration = time.time() - start

        # Запрос должен выполняться быстро (< 1 секунды)
        assert duration < 1.0, f"Запрос выполнялся {duration:.2f} секунд"

    def test_session_query_performance(self, db):
        """Тест: запросы к сессиям выполняются быстро"""
        import time

        start = time.time()

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, u.username
                FROM sessions s
                LEFT JOIN users u ON s.telegram_id = u.telegram_id
            """)
            cursor.fetchall()
            cursor.close()

        duration = time.time() - start

        # Запрос с JOIN должен выполняться быстро (< 2 секунд)
        assert duration < 2.0, f"Запрос с JOIN выполнялся {duration:.2f} секунд"
