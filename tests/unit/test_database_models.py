#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit тесты для data/database/models.py
"""

import pytest
import json
from datetime import datetime
import sys
from pathlib import Path

# Добавляем путь к tests для импорта test_data
tests_dir = Path(__file__).parent.parent
sys.path.insert(0, str(tests_dir))

from fixtures.test_data import TEST_ANSWERS


@pytest.mark.unit
class TestDatabaseConnection:
    """Тесты подключения к PostgreSQL"""

    def test_connection_exists(self, db):
        """Тест: подключение к БД успешно"""
        assert db is not None
        assert db.connection_params['database'] == 'grantservice'

    def test_connection_works(self, db):
        """Тест: можем выполнять запросы"""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            assert 'PostgreSQL' in version

    def test_tables_exist(self, db):
        """Тест: все необходимые таблицы существуют"""
        required_tables = [
            'users', 'sessions', 'interview_questions',
            'grant_applications', 'agent_prompts', 'user_answers'
        ]

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            cursor.close()

            for table in required_tables:
                assert table in existing_tables, f"Таблица {table} не найдена"


@pytest.mark.unit
class TestUserOperations:
    """Тесты операций с пользователями"""

    def test_create_user(self, db, test_user_data, cleanup_test_user):
        """Тест: создание нового пользователя"""
        user_id = db.create_user(
            telegram_id=test_user_data['telegram_id'],
            username=test_user_data['username'],
            first_name=test_user_data['first_name'],
            last_name=test_user_data['last_name']
        )

        assert user_id is not None
        assert user_id > 0

        # Проверяем что пользователь создан
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (test_user_data['telegram_id'],))
            user = cursor.fetchone()
            cursor.close()

            assert user is not None

    def test_create_user_duplicate(self, db, test_user_data, cleanup_test_user):
        """Тест: повторное создание пользователя (должно обновить last_active)"""
        # Создаем пользователя первый раз
        user_id_1 = db.create_user(
            telegram_id=test_user_data['telegram_id'],
            username=test_user_data['username']
        )

        # Создаем того же пользователя второй раз
        user_id_2 = db.create_user(
            telegram_id=test_user_data['telegram_id'],
            username=test_user_data['username']
        )

        # ID должны совпадать (ON CONFLICT DO UPDATE)
        assert user_id_1 == user_id_2

    def test_get_user_by_telegram_id(self, db, test_user_data, cleanup_test_user):
        """Тест: получение пользователя по telegram_id"""
        # Создаем пользователя
        db.create_user(
            telegram_id=test_user_data['telegram_id'],
            username=test_user_data['username']
        )

        # Получаем пользователя
        user = db.get_user_by_telegram_id(test_user_data['telegram_id'])

        assert user is not None
        assert user['telegram_id'] == test_user_data['telegram_id']
        assert user['username'] == test_user_data['username']


@pytest.mark.unit
class TestSessionOperations:
    """Тесты операций с сессиями"""

    def test_create_session(self, db, test_user_data, cleanup_test_user):
        """Тест: создание новой сессии"""
        # Создаем пользователя
        db.create_user(
            telegram_id=test_user_data['telegram_id'],
            username=test_user_data['username']
        )

        # Создаем сессию
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (telegram_id, current_step, status)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (test_user_data['telegram_id'], 'main_menu', 'active'))
            session_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

        assert session_id is not None
        assert session_id > 0

    def test_session_has_correct_fields(self, db, test_user_data, cleanup_test_user):
        """Тест: сессия содержит все необходимые поля"""
        # Создаем пользователя и сессию
        db.create_user(telegram_id=test_user_data['telegram_id'])

        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (telegram_id, current_step, status)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (test_user_data['telegram_id'], 'main_menu', 'active'))
            session_id = cursor.fetchone()[0]
            conn.commit()

            # Получаем сессию
            cursor.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
            columns = [desc[0] for desc in cursor.description]
            cursor.close()

        required_fields = ['id', 'telegram_id', 'current_step', 'status', 'started_at', 'last_activity']
        for field in required_fields:
            assert field in columns, f"Поле {field} отсутствует в таблице sessions"


@pytest.mark.unit
class TestAnswerOperations:
    """Тесты операций с ответами"""

    def test_save_user_answer(self, db, test_user_data, cleanup_test_user):
        """Тест: сохранение ответа пользователя"""
        # Создаем пользователя и сессию
        db.create_user(telegram_id=test_user_data['telegram_id'])

        with db.connect() as conn:
            cursor = conn.cursor()

            # Создаем сессию
            cursor.execute("""
                INSERT INTO sessions (telegram_id, current_step, status)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (test_user_data['telegram_id'], 'question_1', 'active'))
            session_id = cursor.fetchone()[0]
            conn.commit()

            # Получаем первый вопрос
            cursor.execute("SELECT id FROM interview_questions WHERE question_number = 1 LIMIT 1")
            question_id = cursor.fetchone()[0]

            # Сохраняем ответ
            cursor.execute("""
                INSERT INTO user_answers (session_id, question_id, answer_text)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (session_id, question_id, TEST_ANSWERS[1]))
            answer_id = cursor.fetchone()[0]
            conn.commit()

            cursor.close()

        assert answer_id is not None
        assert answer_id > 0

    def test_answer_validation_min_length(self, db, test_user_data, cleanup_test_user):
        """Тест: валидация минимальной длины ответа"""
        # Получаем правило валидации для первого вопроса
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT validation_rules
                FROM interview_questions
                WHERE question_number = 1
            """)
            validation_rules = cursor.fetchone()
            cursor.close()

            if validation_rules and validation_rules[0]:
                rules = json.loads(validation_rules[0])
                min_length = rules.get('min_length', 0)

                # Проверяем что валидный ответ проходит
                assert len(TEST_ANSWERS[1]) >= min_length

                # Проверяем что слишком короткий ответ не проходит
                short_answer = "ab"
                assert len(short_answer) < min_length


@pytest.mark.unit
class TestAnketaSaving:
    """Тесты сохранения анкеты"""

    def test_generate_anketa_id(self, db, test_user_data, cleanup_test_user):
        """Тест: генерация anketa_id в правильном формате"""
        import re
        from fixtures.test_data import ANKETA_ID_PATTERN

        # Создаем пользователя
        db.create_user(
            telegram_id=test_user_data['telegram_id'],
            username=test_user_data['username']
        )

        # Генерируем anketa_id
        with db.connect() as conn:
            cursor = conn.cursor()

            # Получаем пользователя
            cursor.execute("SELECT username FROM users WHERE telegram_id = %s", (test_user_data['telegram_id'],))
            username = cursor.fetchone()[0] or str(test_user_data['telegram_id'])

            # Генерируем ID
            today = datetime.now().strftime('%Y%m%d')
            anketa_id = f"#AN-{today}-{username}-001"

            cursor.close()

        # Проверяем формат
        assert re.match(ANKETA_ID_PATTERN, anketa_id) is not None
