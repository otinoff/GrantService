#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модели базы данных GrantService для PostgreSQL 18
"""

import os
import psycopg2
import psycopg2.extras
from psycopg2.extras import Json
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_kuzbass_time():
    """Получить текущее время в часовом поясе Кемерово (GMT+7)"""
    try:
        import pytz
        kuzbass_tz = pytz.timezone('Asia/Novosibirsk')
        return datetime.now(kuzbass_tz).isoformat()
    except ImportError:
        # Fallback без pytz - добавляем 7 часов к UTC
        utc_time = datetime.now(timezone.utc)
        kuzbass_time = utc_time + timedelta(hours=7)
        return kuzbass_time.isoformat()

class GrantServiceDatabase:
    """Класс для работы с PostgreSQL базой данных GrantService"""

    def __init__(self, connection_params: Optional[Dict[str, Any]] = None):
        """
        Инициализация подключения к PostgreSQL

        Args:
            connection_params: Параметры подключения. Если None, берутся из переменных окружения
        """
        if connection_params is None:
            # Читаем из переменных окружения
            self.connection_params = {
                'host': os.getenv('PGHOST', 'localhost'),
                'port': int(os.getenv('PGPORT', '5434')),  # Custom port 5434 (not default 5432)
                'database': os.getenv('PGDATABASE', 'grantservice'),
                'user': os.getenv('PGUSER', 'postgres'),
                'password': os.getenv('PGPASSWORD', 'root')
            }
        else:
            self.connection_params = connection_params

        logger.info(f"PostgreSQL connection configured: {self.connection_params['host']}:{self.connection_params['port']}/{self.connection_params['database']}")

        # Проверяем подключение
        self._test_connection()

    def _test_connection(self):
        """Проверка подключения к БД"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version[:50]}...")
                cursor.close()
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def connect(self):
        """Создание соединения с PostgreSQL"""
        return psycopg2.connect(**self.connection_params)

    def init_database(self):
        """
        Инициализация базы данных

        ВАЖНО: Таблицы уже созданы через миграцию!
        Эта функция только проверяет наличие таблиц.
        """
        logger.info("Checking database schema...")

        with self.connect() as conn:
            cursor = conn.cursor()

            # Проверяем наличие основных таблиц
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)

            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(tables)} tables in database")

            required_tables = [
                'users', 'sessions', 'interview_questions',
                'grant_applications', 'agent_prompts'
            ]

            missing_tables = [t for t in required_tables if t not in tables]

            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}")
                logger.warning("Please run schema migration first!")
            else:
                logger.info("All required tables present")

            cursor.close()

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========

    def _dict_row(self, cursor, row):
        """Преобразовать row в словарь"""
        if row is None:
            return None
        return dict(zip([desc[0] for desc in cursor.description], row))

    def _dict_rows(self, cursor, rows):
        """Преобразовать список rows в список словарей"""
        if not rows:
            return []
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    # ========== СВОЙСТВА ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ ==========

    @property
    def db_path(self):
        """Обратная совместимость - возвращает строку подключения"""
        return f"postgresql://{self.connection_params['user']}@{self.connection_params['host']}:{self.connection_params['port']}/{self.connection_params['database']}"

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С USERS ==========

    def create_user(self, telegram_id: int, username: str = None,
                   first_name: str = None, last_name: str = None) -> int:
        """Создать нового пользователя"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (telegram_id) DO UPDATE
                SET last_active = CURRENT_TIMESTAMP
                RETURNING id
            """, (telegram_id, username, first_name, last_name))

            user_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

            return user_id

    def register_user(self, telegram_id: int, username: str = None,
                     first_name: str = None, last_name: str = None) -> bool:
        """
        Зарегистрировать пользователя (обратная совместимость для create_user)
        """
        try:
            self.create_user(telegram_id, username, first_name, last_name)
            logger.info(f"User {telegram_id} registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register user {telegram_id}: {e}")
            return False

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Получить пользователя по telegram_id"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM users WHERE telegram_id = %s
            """, (telegram_id,))

            row = cursor.fetchone()
            cursor.close()

            return self._dict_row(cursor, row) if row else None

    def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM users
                ORDER BY created_at DESC
            """)

            rows = cursor.fetchall()
            cursor.close()

            return self._dict_rows(cursor, rows)

    def get_users_statistics(self) -> Dict[str, Any]:
        """Получить статистику пользователей"""
        with self.connect() as conn:
            cursor = conn.cursor()

            # Общее количество пользователей
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            # Активные за последние 7 дней
            cursor.execute("""
                SELECT COUNT(*) FROM users
                WHERE last_active > NOW() - INTERVAL '7 days'
            """)
            active_users = cursor.fetchone()[0]

            # Новые пользователи за последние 30 дней
            cursor.execute("""
                SELECT COUNT(*) FROM users
                WHERE created_at > NOW() - INTERVAL '30 days'
            """)
            new_users = cursor.fetchone()[0]

            cursor.close()

            return {
                'total_users': total_users,
                'active_users_7d': active_users,
                'new_users_30d': new_users
            }

    def get_user_llm_preference(self, telegram_id: int) -> str:
        """
        Получить предпочитаемый LLM провайдер пользователя

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            str: 'claude_code' или 'gigachat', по умолчанию 'claude_code'
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT preferred_llm_provider FROM users
                    WHERE telegram_id = %s
                """, (telegram_id,))

                row = cursor.fetchone()
                cursor.close()

                return row[0] if row and row[0] else 'claude_code'
        except Exception as e:
            # Column might not exist yet or other DB error - return default
            logger.warning(f"Failed to get LLM preference for user {telegram_id}: {e}")
            return 'claude_code'

    def set_user_llm_preference(self, telegram_id: int, provider: str) -> bool:
        """
        Установить предпочитаемый LLM провайдер для пользователя

        Args:
            telegram_id: Telegram ID пользователя
            provider: 'claude_code' или 'gigachat'

        Returns:
            bool: True если успешно, False если ошибка
        """
        if provider not in ['claude_code', 'gigachat']:
            logger.error(f"Invalid LLM provider: {provider}. Must be 'claude_code' or 'gigachat'")
            return False

        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE users
                    SET preferred_llm_provider = %s
                    WHERE telegram_id = %s
                """, (provider, telegram_id))

                conn.commit()
                cursor.close()

                logger.info(f"User {telegram_id} LLM preference set to: {provider}")
                return True
        except Exception as e:
            logger.error(f"Failed to set LLM preference for user {telegram_id}: {e}")
            return False

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С SESSIONS ==========

    def create_session(self, telegram_id: int) -> int:
        """Создать новую сессию"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO sessions (telegram_id, status, current_step)
                VALUES (%s, 'active', 'started')
                RETURNING id
            """, (telegram_id,))

            session_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

            logger.info(f"Created session {session_id} for telegram_id {telegram_id}")
            return session_id

    def get_session_by_id(self, session_id: int) -> Optional[Dict]:
        """Получить сессию по ID"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sessions WHERE id = %s
            """, (session_id,))

            row = cursor.fetchone()
            cursor.close()

            return self._dict_row(cursor, row) if row else None

    def get_user_sessions(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """Получить сессии пользователя"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sessions
                WHERE telegram_id = %s
                ORDER BY started_at DESC
                LIMIT %s
            """, (telegram_id, limit))

            rows = cursor.fetchall()
            cursor.close()

            return self._dict_rows(cursor, rows)

    def get_active_sessions(self) -> List[Dict]:
        """Получить все активные сессии"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sessions
                WHERE status = 'active'
                ORDER BY last_activity DESC
            """)

            rows = cursor.fetchall()
            cursor.close()

            return self._dict_rows(cursor, rows)

    def get_completed_sessions(self) -> List[Dict]:
        """Получить все завершенные сессии"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sessions
                WHERE status = 'completed'
                ORDER BY completed_at DESC
            """)

            rows = cursor.fetchall()
            cursor.close()

            return self._dict_rows(cursor, rows)

    def get_session_progress(self, session_id: int) -> Dict[str, Any]:
        """Получить прогресс сессии"""
        session = self.get_session_by_id(session_id)
        if not session:
            return {}

        # Подсчитываем количество отвеченных вопросов
        answers_data = session.get('answers_data', {})
        if isinstance(answers_data, str):
            import json
            answers_data = json.loads(answers_data) if answers_data else {}

        total_questions = len(self.get_active_questions())
        answered_questions = len(answers_data)

        return {
            'session_id': session_id,
            'current_step': session.get('current_step'),
            'status': session.get('status'),
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'progress_percent': int((answered_questions / total_questions * 100)) if total_questions > 0 else 0,
            'answers': answers_data
        }

    def get_user_answers(self, session_id: int) -> List[Dict[str, Any]]:
        """Получить ответы пользователя"""
        session = self.get_session_by_id(session_id)
        if not session:
            return []

        answers_data = session.get('answers_data', {})
        if isinstance(answers_data, str):
            import json
            answers_data = json.loads(answers_data) if answers_data else {}

        # Преобразуем в список
        answers_list = []
        for question_id, answer_text in answers_data.items():
            question = self.get_question_by_number(int(question_id))
            answers_list.append({
                'question_id': int(question_id),
                'question_text': question.get('question_text') if question else '',
                'answer_text': answer_text,
                'session_id': session_id
            })

        return answers_list

    def save_user_answer(self, session_id: int, question_id: int, answer_text: str) -> bool:
        """Сохранить ответ пользователя"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                # Получаем текущие ответы
                cursor.execute("""
                    SELECT answers_data FROM sessions WHERE id = %s
                """, (session_id,))

                row = cursor.fetchone()
                if not row:
                    logger.error(f"Session {session_id} not found")
                    return False

                answers_data = row[0] or {}
                if isinstance(answers_data, str):
                    answers_data = json.loads(answers_data) if answers_data else {}

                # Добавляем новый ответ
                answers_data[str(question_id)] = answer_text

                # Обновляем сессию
                cursor.execute("""
                    UPDATE sessions
                    SET answers_data = %s,
                        last_activity = CURRENT_TIMESTAMP,
                        total_messages = total_messages + 1
                    WHERE id = %s
                """, (json.dumps(answers_data), session_id))

                conn.commit()
                cursor.close()

                logger.info(f"Answer saved for session {session_id}, question {question_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to save answer: {e}")
            return False

    def validate_answer(self, question_id: int, answer: str) -> Dict[str, Any]:
        """Валидация ответа"""
        question = self.get_question_by_number(question_id)
        if not question:
            return {
                'is_valid': False,
                'message': f'Вопрос {question_id} не найден'
            }

        # Базовая валидация - проверяем, что ответ не пустой
        if not answer or not answer.strip():
            return {
                'is_valid': False,
                'message': 'Ответ не может быть пустым'
            }

        # Проверяем минимальную длину (если указана в вопросе)
        min_length = question.get('min_length', 1)
        if len(answer.strip()) < min_length:
            return {
                'is_valid': False,
                'message': f'Ответ слишком короткий. Минимум {min_length} символов.'
            }

        # Проверяем максимальную длину (если указана)
        max_length = question.get('max_length', 10000)
        if len(answer) > max_length:
            return {
                'is_valid': False,
                'message': f'Ответ слишком длинный. Максимум {max_length} символов.'
            }

        return {
            'is_valid': True,
            'message': 'Ответ принят'
        }

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С INTERVIEW QUESTIONS ==========

    def get_question_by_number(self, question_number: int) -> Optional[Dict]:
        """Получить вопрос по номеру"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM interview_questions
                WHERE question_number = %s AND is_active = TRUE
            """, (question_number,))

            row = cursor.fetchone()
            cursor.close()

            return self._dict_row(cursor, row) if row else None

    def get_active_questions(self) -> List[Dict]:
        """Получить все активные вопросы"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM interview_questions
                WHERE is_active = TRUE
                ORDER BY question_number
            """)

            rows = cursor.fetchall()
            cursor.close()

            return self._dict_rows(cursor, rows)

    def insert_default_questions(self):
        """Вставить вопросы по умолчанию (если их нет)"""
        with self.connect() as conn:
            cursor = conn.cursor()

            # Проверяем, есть ли вопросы
            cursor.execute("SELECT COUNT(*) FROM interview_questions")
            count = cursor.fetchone()[0]

            if count == 0:
                logger.info("No questions found, inserting defaults...")
                # Вставка вопросов по умолчанию здесь
                # TODO: Добавить стандартные вопросы
            else:
                logger.info(f"Found {count} questions in database")

            cursor.close()

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С GRANT APPLICATIONS ==========

    def save_grant_application(self, application_data: Dict[str, Any]) -> str:
        """Сохранить грантовую заявку"""
        with self.connect() as conn:
            cursor = conn.cursor()

            # Генерация номера заявки
            if 'application_number' in application_data:
                application_number = application_data['application_number']
            else:
                import uuid
                application_number = f"GA-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

            cursor.execute("""
                INSERT INTO grant_applications (
                    application_number, session_id, status, content_json,
                    title, summary, admin_user, grant_fund,
                    requested_amount, project_duration
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING application_number
            """, (
                application_number,
                application_data.get('session_id'),
                application_data.get('status', 'draft'),
                json.dumps(application_data.get('content', application_data.get('application', {}))),
                application_data.get('title', 'Проект'),
                application_data.get('summary', '')[:500] if application_data.get('summary') else '',
                application_data.get('admin_user', 'ai_agent'),
                application_data.get('grant_fund', ''),
                application_data.get('requested_amount', 0.0),
                application_data.get('project_duration', 12)
            ))

            result = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

            logger.info(f"Grant application {result} saved successfully")
            return result

    def get_all_applications(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Получить список всех заявок"""
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM grant_applications
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))

            rows = cursor.fetchall()
            cursor.close()

            return self._dict_rows(cursor, rows)

    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С АНКЕТАМИ ==========

    def generate_anketa_id(self, user_data: Dict[str, Any]) -> str:
        """Генерация ID анкеты в формате #AN-YYYYMMDD-username-001"""
        date_str = datetime.now().strftime("%Y%m%d")
        user_identifier = self._get_user_identifier(user_data)

        # Получаем следующий номер анкеты для пользователя за сегодня
        next_number = self._get_next_anketa_number(user_identifier, date_str)

        return f"#AN-{date_str}-{user_identifier}-{next_number:03d}"

    def _get_user_identifier(self, user_data: Dict[str, Any]) -> str:
        """
        Получить читаемый идентификатор пользователя

        Приоритет:
        1. first_name + last_name (транслитерация) - самый профессиональный вариант
        2. first_name только (транслитерация)
        3. username (если есть)
        4. telegram_id (fallback, всегда есть)
        """
        import re

        # 1. Имя + Фамилия (транслитерация кириллицы) - ПРИОРИТЕТ
        first_name = user_data.get('first_name', '').strip()
        last_name = user_data.get('last_name', '').strip()

        if first_name and last_name:
            # Екатерина Максимова → ekaterina_maksimova
            first_trans = self._transliterate(first_name)
            last_trans = self._transliterate(last_name)
            if first_trans and last_trans:
                return f"{first_trans}_{last_trans}"[:20]

        # 2. Только имя (транслитерация)
        if first_name:
            # Валерия → valeriya
            first_trans = self._transliterate(first_name)
            if first_trans:
                return first_trans[:20]

        # 3. Username (fallback если нет имени)
        username = user_data.get('username', '').strip()
        if username:
            # Очистка от @ если есть
            username = username.lstrip('@').lower()
            # Очистка от спецсимволов
            username = re.sub(r'[^a-z0-9_]', '', username)
            if username:
                return username[:20]

        # 4. Fallback - telegram_id (всегда есть)
        return str(user_data['telegram_id'])

    def _transliterate(self, text: str) -> str:
        """Транслитерация кириллицы в латиницу (ГОСТ 7.79-2000)"""
        import re

        # Таблица транслитерации
        translit = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
            'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
            'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
            'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
            'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
            'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
            'э': 'e', 'ю': 'yu', 'я': 'ya',
            # Uppercase
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
            'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z', 'И': 'I',
            'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
            'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
            'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch',
            'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
            'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
        }

        result = []
        for char in text:
            if char in translit:
                result.append(translit[char])
            else:
                result.append(char)

        # Lowercase and clean
        result_str = ''.join(result).lower()

        # Remove non-alphanumeric except underscore
        result_str = re.sub(r'[^a-z0-9_]', '', result_str)

        return result_str

    def _get_next_anketa_number(self, user_identifier: str, date_str: str) -> int:
        """Получить следующий номер анкеты для пользователя за день"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT COUNT(*) FROM sessions
                    WHERE anketa_id LIKE %s
                """, (f"#AN-{date_str}-{user_identifier}-%",))

                count = cursor.fetchone()[0]
                cursor.close()

                return count + 1
        except Exception as e:
            logger.error(f"Error getting next anketa number: {e}")
            return 1

    def save_anketa(self, anketa_data: Dict[str, Any]) -> str:
        """Сохранить анкету и вернуть anketa_id"""
        try:
            anketa_id = self.generate_anketa_id(anketa_data['user_data'])
            session_id = anketa_data['session_id']
            telegram_id = anketa_data['user_data'].get('telegram_id')

            with self.connect() as conn:
                cursor = conn.cursor()

                # Обновляем сессию
                cursor.execute("""
                    UPDATE sessions
                    SET anketa_id = %s,
                        interview_data = %s,
                        status = %s,
                        completed_at = %s
                    WHERE id = %s
                """, (
                    anketa_id,
                    json.dumps(anketa_data['interview_data']),
                    'completed',
                    datetime.now(),
                    session_id
                ))

                # Получаем user_id
                cursor.execute("""
                    SELECT id FROM users WHERE telegram_id = %s
                """, (telegram_id,))
                user_row = cursor.fetchone()

                if user_row:
                    user_id = user_row[0]

                    # Создаем запись в grant_applications
                    project_name = anketa_data['interview_data'].get('project_name', 'Новый проект')

                    cursor.execute("""
                        INSERT INTO grant_applications
                        (user_id, session_id, application_number, title, content_json, status, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """, (
                        user_id,
                        session_id,
                        anketa_id,
                        project_name,
                        json.dumps(anketa_data['interview_data']),
                        'draft'
                    ))

                    logger.info(f"Создана заявка в grant_applications для anketa_id: {anketa_id}")
                else:
                    logger.warning(f"Пользователь с telegram_id {telegram_id} не найден при создании grant_application")

                conn.commit()
                cursor.close()

                logger.info(f"Анкета сохранена: {anketa_id}")
                return anketa_id

        except Exception as e:
            logger.error(f"Ошибка сохранения анкеты: {e}")
            return None

    def get_session_by_anketa_id(self, anketa_id: str) -> Optional[Dict[str, Any]]:
        """Получить сессию по ID анкеты"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT s.*, u.username, u.first_name, u.last_name
                    FROM sessions s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    WHERE s.anketa_id = %s
                """, (anketa_id,))

                row = cursor.fetchone()
                cursor.close()

                return self._dict_row(cursor, row) if row else None

        except Exception as e:
            logger.error(f"Ошибка получения сессии по anketa_id: {e}")
            return None

    def generate_audit_id(self, anketa_id: str) -> str:
        """
        Generate audit ID in unified format: anketa_id + AU suffix + counter

        Examples:
            #AN-20251008-ekaterina_maksimova-001-AU-001
            #AN-20251008-ekaterina_maksimova-001-AU-002
        """
        from datetime import datetime

        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                # Count existing audits for this anketa
                # Используем JOIN чтобы связать auditor_results с sessions по session_id
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM auditor_results ar
                    JOIN sessions s ON ar.session_id = s.id
                    WHERE s.anketa_id = %s
                """, (anketa_id,))

                count = cursor.fetchone()[0] or 0
                cursor.close()

                # Generate ID: anketa_id-AU-NNN
                audit_id = f"{anketa_id}-AU-{count + 1:03d}"
                return audit_id

        except Exception as e:
            logger.error(f"Ошибка генерации audit_id: {e}")
            # Fallback to simple format
            return f"{anketa_id}-AU-{datetime.now().strftime('%H%M%S')}"

    def generate_research_id(self, anketa_id: str) -> str:
        """
        Generate research ID in unified format: anketa_id + RS suffix + counter

        Examples:
            #AN-20251008-ekaterina_maksimova-001-RS-001
            #AN-20251008-ekaterina_maksimova-001-RS-002
        """
        from datetime import datetime

        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                # Count existing research for this anketa
                cursor.execute("""
                    SELECT COUNT(*) FROM researcher_research
                    WHERE anketa_id = %s
                """, (anketa_id,))

                count = cursor.fetchone()[0] or 0
                cursor.close()

                # Generate ID: anketa_id-RS-NNN
                research_id = f"{anketa_id}-RS-{count + 1:03d}"
                return research_id

        except Exception as e:
            logger.error(f"Ошибка генерации research_id: {e}")
            # Fallback to simple format
            return f"{anketa_id}-RS-{datetime.now().strftime('%H%M%S')}"

    def generate_grant_id(self, anketa_id: str) -> str:
        """
        Generate grant ID in unified format: anketa_id + GR suffix + counter

        Examples:
            #AN-20251008-ekaterina_maksimova-001-GR-001
            #AN-20251008-ekaterina_maksimova-001-GR-002
        """
        from datetime import datetime

        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                # Count existing grants for this anketa
                cursor.execute("""
                    SELECT COUNT(*) FROM grants
                    WHERE anketa_id = %s
                """, (anketa_id,))

                count = cursor.fetchone()[0] or 0
                cursor.close()

                # Generate ID: anketa_id-GR-NNN
                grant_id = f"{anketa_id}-GR-{count + 1:03d}"
                return grant_id

        except Exception as e:
            logger.error(f"Ошибка генерации grant_id: {e}")
            # Fallback to simple format
            return f"{anketa_id}-GR-{datetime.now().strftime('%H%M%S')}"

    def generate_review_id(self, anketa_id: str) -> str:
        """
        Generate review ID in unified format: anketa_id + RV suffix + counter

        Examples:
            #AN-20251008-ekaterina_maksimova-001-RV-001
            #AN-20251008-ekaterina_maksimova-001-RV-002

        Note: Review - это независимое экспертное мнение о готовом гранте.
              Review НЕ изменяет грант, а создает отдельную оценочную запись.
        """
        from datetime import datetime

        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                # Count existing reviews for this anketa
                cursor.execute("""
                    SELECT COUNT(*) FROM grant_reviews
                    WHERE anketa_id = %s
                """, (anketa_id,))

                count = cursor.fetchone()[0] or 0
                cursor.close()

                # Generate ID: anketa_id-RV-NNN
                review_id = f"{anketa_id}-RV-{count + 1:03d}"
                return review_id

        except Exception as e:
            logger.error(f"Ошибка генерации review_id: {e}")
            # Fallback to simple format
            return f"{anketa_id}-RV-{datetime.now().strftime('%H%M%S')}"

    def save_research_results(self, research_data: Dict[str, Any]) -> str:
        """Сохранить результаты исследования и вернуть research_id"""
        try:
            anketa_id = research_data['anketa_id']
            research_id = self.generate_research_id(anketa_id)

            with self.connect() as conn:
                cursor = conn.cursor()

                # Get user info from session
                cursor.execute("""
                    SELECT u.id, u.username, u.first_name, u.last_name, s.id as session_id
                    FROM sessions s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    WHERE s.anketa_id = %s
                    LIMIT 1
                """, (anketa_id,))

                session_row = cursor.fetchone()
                if not session_row:
                    logger.error(f"Session not found for anketa_id: {anketa_id}")
                    return None

                user_id, username, first_name, last_name, session_id = session_row

                cursor.execute("""
                    INSERT INTO researcher_research
                    (research_id, anketa_id, user_id, username, first_name, last_name,
                     session_id, llm_provider, model, status,
                     research_results, created_at, completed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                    RETURNING research_id
                """, (
                    research_id,
                    anketa_id,
                    user_id,
                    username,
                    first_name,
                    last_name,
                    session_id,
                    research_data.get('llm_provider', 'claude_code'),
                    research_data.get('model', 'sonnet-4.5'),
                    research_data.get('status', 'completed'),
                    Json(research_data.get('research_results', {})),
                    research_data.get('completed_at')
                ))

                result = cursor.fetchone()[0]
                conn.commit()
                cursor.close()

                logger.info(f"Исследование сохранено: {result}")
                return result

        except Exception as e:
            logger.error(f"Ошибка сохранения исследования: {e}")
            return None

    def save_review_results(self, review_data: Dict[str, Any]) -> str:
        """
        Сохранить результаты Review и вернуть review_id

        Review - это независимое экспертное мнение о готовом гранте.
        Review НЕ изменяет грант, а создает отдельную оценочную запись.

        Args:
            review_data: Словарь с результатами review_grant_async() из ReviewerAgent
                - anketa_id: ID анкеты
                - grant_id: ID гранта, который оценивается
                - readiness_score: Общая оценка готовности (0-10)
                - approval_probability: Вероятность одобрения (0-100%)
                - criteria_scores: Детальные оценки по 4 критериям
                - strengths: Список сильных сторон
                - weaknesses: Список слабых сторон
                - recommendations: Список рекомендаций
                - can_submit: Флаг готовности к подаче
                - quality_tier: Уровень качества
                - review_content: Полный текст review отчета (optional)
                - review_md_path: Путь к MD файлу (optional)
                - review_pdf_path: Путь к PDF файлу (optional)
                - llm_provider: LLM провайдер (optional)
                - model: Модель LLM (optional)
                - processing_time: Время обработки (optional)
                - tokens_used: Количество токенов (optional)

        Returns:
            review_id: Уникальный ID review в формате #AN-YYYYMMDD-username-NNN-RV-NNN
        """
        try:
            anketa_id = review_data['anketa_id']
            grant_id = review_data['grant_id']
            review_id = self.generate_review_id(anketa_id)

            with self.connect() as conn:
                cursor = conn.cursor()

                # Extract criteria scores
                criteria = review_data.get('criteria_scores', {})
                evidence = criteria.get('evidence_base', {})
                structure = criteria.get('structure', {})
                matching = criteria.get('matching', {})
                economics = criteria.get('economics', {})

                cursor.execute("""
                    INSERT INTO grant_reviews
                    (review_id, grant_id, anketa_id,
                     readiness_score, approval_probability, can_submit, quality_tier,
                     evidence_score, structure_score, matching_score, economics_score,
                     criteria_scores, strengths, weaknesses, recommendations,
                     review_content, review_md_path, review_pdf_path,
                     llm_provider, model, processing_time, tokens_used,
                     created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING review_id
                """, (
                    review_id,
                    grant_id,
                    anketa_id,
                    review_data.get('readiness_score'),
                    review_data.get('approval_probability'),
                    review_data.get('can_submit', False),
                    review_data.get('quality_tier', 'Unknown'),
                    evidence.get('score'),
                    structure.get('score'),
                    matching.get('score'),
                    economics.get('score'),
                    Json(review_data.get('criteria_scores', {})),
                    review_data.get('strengths', []),
                    review_data.get('weaknesses', []),
                    review_data.get('recommendations', []),
                    review_data.get('review_content'),
                    review_data.get('review_md_path'),
                    review_data.get('review_pdf_path'),
                    review_data.get('llm_provider', 'claude_code'),
                    review_data.get('model', 'sonnet-4.5'),
                    review_data.get('processing_time'),
                    review_data.get('tokens_used')
                ))

                result = cursor.fetchone()[0]
                conn.commit()
                cursor.close()

                logger.info(f"Review сохранен: {result} для grant_id={grant_id}")
                return result

        except Exception as e:
            logger.error(f"Ошибка сохранения review: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_grant_by_id(self, grant_id: int) -> Optional[Dict]:
        """Получить грант по ID"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM grants WHERE id = %s
                """, (grant_id,))

                row = cursor.fetchone()
                cursor.close()

                return self._dict_row(cursor, row) if row else None

        except Exception as e:
            logger.error(f"Ошибка получения гранта по ID: {e}")
            return None


# Для обратной совместимости - создаем глобальный экземпляр
# НО только если переменные окружения настроены
if os.getenv('PGHOST') or os.getenv('DATABASE_URL'):
    try:
        db = GrantServiceDatabase()
        logger.info("Global PostgreSQL database instance created")
    except Exception as e:
        logger.error(f"Failed to create global database instance: {e}")
        db = None
else:
    logger.warning("PostgreSQL environment variables not set, db instance not created")
    db = None
