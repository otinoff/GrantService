#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit тесты для data/database/sessions.py
"""

import pytest
import sys
from pathlib import Path

tests_dir = Path(__file__).parent.parent
sys.path.insert(0, str(tests_dir))

from fixtures.test_data import EXPECTED_MIGRATION_DATA


@pytest.mark.unit
class TestSessionManager:
    """Тесты SessionManager"""

    def test_create_session(self, session_manager, test_user_data, cleanup_test_user):
        """Тест: создание новой сессии"""
        # Создаем пользователя
        session_manager.db.create_user(telegram_id=test_user_data['telegram_id'])

        # Создаем сессию
        session_id = session_manager.create_session(test_user_data['telegram_id'])

        assert session_id is not None
        assert session_id > 0

    def test_session_default_status(self, session_manager, test_user_data, cleanup_test_user):
        """Тест: новая сессия имеет статус 'active'"""
        session_manager.db.create_user(telegram_id=test_user_data['telegram_id'])
        session_id = session_manager.create_session(test_user_data['telegram_id'])

        # Проверяем статус
        with session_manager.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM sessions WHERE id = %s", (session_id,))
            status = cursor.fetchone()[0]
            cursor.close()

        assert status == 'active'

    def test_session_has_total_questions(self, session_manager, test_user_data, cleanup_test_user):
        """Тест: сессия содержит total_questions"""
        session_manager.db.create_user(telegram_id=test_user_data['telegram_id'])
        session_id = session_manager.create_session(test_user_data['telegram_id'])

        # Проверяем total_questions
        with session_manager.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'sessions' AND column_name = 'total_questions'
            """)
            has_column = cursor.fetchone() is not None

            if has_column:
                cursor.execute("SELECT total_questions FROM sessions WHERE id = %s", (session_id,))
                total_questions = cursor.fetchone()[0]
                cursor.close()

                assert total_questions == EXPECTED_MIGRATION_DATA['questions_count']


@pytest.mark.unit
class TestUserSessions:
    """Тесты получения сессий пользователя"""

    def test_get_user_sessions(self, session_manager, test_user_data, cleanup_test_user):
        """Тест: получение всех сессий пользователя"""
        # Создаем пользователя и сессию
        session_manager.db.create_user(telegram_id=test_user_data['telegram_id'])
        session_id = session_manager.create_session(test_user_data['telegram_id'])

        # Получаем сессии
        sessions = session_manager.get_user_sessions(test_user_data['telegram_id'])

        assert len(sessions) > 0
        assert sessions[0]['id'] == session_id

    def test_user_sessions_include_user_data(self, session_manager, test_user_data, cleanup_test_user):
        """Тест: сессии включают данные пользователя (JOIN)"""
        session_manager.db.create_user(
            telegram_id=test_user_data['telegram_id'],
            username=test_user_data['username'],
            first_name=test_user_data['first_name']
        )
        session_manager.create_session(test_user_data['telegram_id'])

        sessions = session_manager.get_user_sessions(test_user_data['telegram_id'])

        assert len(sessions) > 0
        session = sessions[0]
        # Проверяем наличие данных пользователя
        assert 'username' in session or 'first_name' in session

    def test_sessions_ordered_by_date(self, session_manager, test_user_data, cleanup_test_user):
        """Тест: сессии отсортированы по дате (новые первыми)"""
        session_manager.db.create_user(telegram_id=test_user_data['telegram_id'])

        # Создаем несколько сессий
        session_id_1 = session_manager.create_session(test_user_data['telegram_id'])
        session_id_2 = session_manager.create_session(test_user_data['telegram_id'])

        sessions = session_manager.get_user_sessions(test_user_data['telegram_id'])

        # Первая в списке должна быть самая новая
        assert len(sessions) >= 2
        assert sessions[0]['id'] == session_id_2  # Новая сессия
        assert sessions[1]['id'] == session_id_1  # Старая сессия


@pytest.mark.unit
class TestSessionProgress:
    """Тесты прогресса заполнения сессии"""

    def test_get_session_progress(self, session_manager, test_user_data, cleanup_test_user):
        """Тест: получение прогресса сессии"""
        session_manager.db.create_user(telegram_id=test_user_data['telegram_id'])
        session_id = session_manager.create_session(test_user_data['telegram_id'])

        progress = session_manager.get_session_progress(session_id)

        assert progress is not None
        assert 'answers_count' in progress
        assert 'total_questions' in progress

    def test_progress_calculation(self, session_manager, test_user_data, cleanup_test_user):
        """Тест: расчет процента прогресса"""
        session_manager.db.create_user(telegram_id=test_user_data['telegram_id'])
        session_id = session_manager.create_session(test_user_data['telegram_id'])

        # Добавляем несколько ответов
        with session_manager.db.connect() as conn:
            cursor = conn.cursor()

            # Получаем первые 3 вопроса
            cursor.execute("SELECT id FROM interview_questions WHERE is_active = TRUE ORDER BY question_number LIMIT 3")
            question_ids = [row[0] for row in cursor.fetchall()]

            # Добавляем ответы
            for question_id in question_ids:
                cursor.execute("""
                    INSERT INTO user_answers (session_id, question_id, answer_text)
                    VALUES (%s, %s, %s)
                """, (session_id, question_id, "Test answer"))
            conn.commit()
            cursor.close()

        # Получаем прогресс
        progress = session_manager.get_session_progress(session_id)

        # Должно быть 3 ответа
        assert progress['answers_count'] == 3

        # Процент должен быть 3/25 * 100 = 12%
        if 'calculated_progress' in progress:
            expected_progress = (3 * 100) // EXPECTED_MIGRATION_DATA['questions_count']
            assert progress['calculated_progress'] == expected_progress


@pytest.mark.unit
class TestUserAnswers:
    """Тесты получения ответов пользователя"""

    def test_get_user_answers(self, session_manager, test_user_data, cleanup_test_user):
        """Тест: получение всех ответов пользователя"""
        session_manager.db.create_user(telegram_id=test_user_data['telegram_id'])
        session_id = session_manager.create_session(test_user_data['telegram_id'])

        # Добавляем ответ
        with session_manager.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM interview_questions WHERE question_number = 1 LIMIT 1")
            question_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO user_answers (session_id, question_id, answer_text)
                VALUES (%s, %s, %s)
            """, (session_id, question_id, "Test answer"))
            conn.commit()
            cursor.close()

        # Получаем ответы
        answers = session_manager.get_user_answers(session_id)

        assert len(answers) > 0
        assert answers[0]['answer_text'] == "Test answer"

    def test_answers_include_question_data(self, session_manager, test_user_data, cleanup_test_user):
        """Тест: ответы включают данные вопроса (JOIN)"""
        session_manager.db.create_user(telegram_id=test_user_data['telegram_id'])
        session_id = session_manager.create_session(test_user_data['telegram_id'])

        # Добавляем ответ
        with session_manager.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM interview_questions WHERE question_number = 1 LIMIT 1")
            question_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO user_answers (session_id, question_id, answer_text)
                VALUES (%s, %s, %s)
            """, (session_id, question_id, "Test answer"))
            conn.commit()
            cursor.close()

        answers = session_manager.get_user_answers(session_id)

        assert len(answers) > 0
        answer = answers[0]
        # Проверяем наличие данных вопроса
        assert 'question_number' in answer
        assert 'question_text' in answer
        assert answer['question_number'] == 1


@pytest.mark.unit
class TestSessionMigration:
    """Тесты миграции сессий"""

    def test_migrated_sessions_count(self, db):
        """Тест: количество мигрированных сессий"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions")
            count = cursor.fetchone()[0]
            cursor.close()

        assert count >= EXPECTED_MIGRATION_DATA['min_sessions_count'], \
            f"Ожидается минимум {EXPECTED_MIGRATION_DATA['min_sessions_count']} сессий после миграции"

    def test_sessions_have_users(self, db):
        """Тест: все сессии привязаны к существующим пользователям"""
        with db.connect() as conn:
            cursor = conn.cursor()

            # Находим сессии без пользователей
            cursor.execute("""
                SELECT s.id
                FROM sessions s
                LEFT JOIN users u ON s.telegram_id = u.telegram_id
                WHERE u.telegram_id IS NULL
            """)
            orphan_sessions = cursor.fetchall()
            cursor.close()

        assert len(orphan_sessions) == 0, \
            f"Найдено {len(orphan_sessions)} сессий без пользователей"
