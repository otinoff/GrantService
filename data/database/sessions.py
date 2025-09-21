#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с сессиями пользователей
"""

import sqlite3
from typing import List, Dict, Any
from .models import GrantServiceDatabase, get_kuzbass_time

class SessionManager:
    def __init__(self, db: GrantServiceDatabase):
        self.db = db
    
    def create_session(self, telegram_id: int) -> int:
        """Создать новую сессию для пользователя"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Получаем актуальное количество активных вопросов
                cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = 1")
                active_questions_count = cursor.fetchone()[0] or 0
                
                current_time = get_kuzbass_time()
                
                # Проверяем, есть ли колонка total_questions
                cursor.execute("PRAGMA table_info(sessions)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'total_questions' in columns:
                    cursor.execute("""
                        INSERT INTO sessions (telegram_id, current_step, status, started_at, last_activity, total_questions)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        telegram_id,
                        'main_menu',
                        'active',
                        current_time,
                        current_time,
                        active_questions_count
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO sessions (telegram_id, current_step, status, started_at, last_activity)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        telegram_id,
                        'main_menu',
                        'active',
                        current_time,
                        current_time
                    ))
                
                session_id = cursor.lastrowid
                conn.commit()
                print(f"[OK] Создана сессия {session_id} для пользователя {telegram_id}")
                return session_id
        except Exception as e:
            print(f"[ERROR] Ошибка создания сессии: {e}")
            return 0
    
    def get_user_sessions(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Получить все сессии пользователя"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.*, u.first_name, u.last_name, u.username
                    FROM sessions s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    WHERE s.telegram_id = ?
                    ORDER BY s.started_at DESC
                """, (telegram_id,))
                
                columns = [description[0] for description in cursor.description]
                sessions = []
                for row in cursor.fetchall():
                    session = dict(zip(columns, row))
                    sessions.append(session)
                
                return sessions
        except Exception as e:
            print(f"[ERROR] Ошибка получения сессий пользователя: {e}")
            return []
    
    def get_session_progress(self, session_id: int) -> Dict[str, Any]:
        """Получить прогресс заполнения сессии"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        s.*,
                        u.first_name, u.last_name, u.username,
                        COUNT(ua.id) as answers_count,
                        s.total_questions,
                        CASE 
                            WHEN s.total_questions > 0 
                            THEN (COUNT(ua.id) * 100) / s.total_questions 
                            ELSE 0 
                        END as calculated_progress
                    FROM sessions s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    LEFT JOIN user_answers ua ON s.id = ua.session_id
                    WHERE s.id = ?
                    GROUP BY s.id
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return {}
        except Exception as e:
            print(f"[ERROR] Ошибка получения прогресса сессии: {e}")
            return {}
    
    def get_user_answers(self, session_id: int) -> List[Dict[str, Any]]:
        """Получить все ответы пользователя в сессии"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        ua.*,
                        iq.question_number,
                        iq.question_text,
                        iq.field_name
                    FROM user_answers ua
                    JOIN interview_questions iq ON ua.question_id = iq.id
                    WHERE ua.session_id = ?
                    ORDER BY iq.question_number
                """, (session_id,))
                
                columns = [description[0] for description in cursor.description]
                answers = []
                for row in cursor.fetchall():
                    answer = dict(zip(columns, row))
                    answers.append(answer)
                
                return answers
        except Exception as e:
            print(f"[ERROR] Ошибка получения ответов пользователя: {e}")
            return []
    
    def save_user_answer(self, session_id: int, question_id: int, answer_text: str) -> bool:
        """Сохранить ответ пользователя"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Сохраняем ответ
                cursor.execute("""
                    INSERT INTO user_answers (session_id, question_id, answer_text)
                    VALUES (?, ?, ?)
                """, (session_id, question_id, answer_text))
                
                # Обновляем прогресс сессии
                cursor.execute("""
                    UPDATE sessions 
                    SET 
                        questions_answered = (
                            SELECT COUNT(*) FROM user_answers WHERE session_id = ?
                        ),
                        progress_percentage = CASE 
                            WHEN total_questions > 0 
                            THEN (questions_answered * 100) / total_questions 
                            ELSE 0 
                        END,
                        last_activity = ?
                    WHERE id = ?
                """, (session_id, get_kuzbass_time(), session_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"[ERROR] Ошибка сохранения ответа: {e}")
            return False
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Получить активные сессии"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        s.*,
                        u.first_name, u.last_name, u.username,
                        COUNT(ua.id) as answers_count
                    FROM sessions s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    LEFT JOIN user_answers ua ON s.id = ua.session_id
                    WHERE s.completion_status = 'in_progress'
                    GROUP BY s.id
                    ORDER BY s.last_activity DESC
                """)
                
                columns = [description[0] for description in cursor.description]
                sessions = []
                for row in cursor.fetchall():
                    session = dict(zip(columns, row))
                    sessions.append(session)
                
                return sessions
        except Exception as e:
            print(f"[ERROR] Ошибка получения активных сессий: {e}")
            return []
    
    def get_completed_sessions(self) -> List[Dict[str, Any]]:
        """Получить завершенные сессии"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        s.*,
                        u.first_name, u.last_name, u.username,
                        COUNT(ua.id) as answers_count
                    FROM sessions s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    LEFT JOIN user_answers ua ON s.id = ua.session_id
                    WHERE s.completion_status = 'completed'
                    GROUP BY s.id
                    ORDER BY s.completed_at DESC
                """)
                
                columns = [description[0] for description in cursor.description]
                sessions = []
                for row in cursor.fetchall():
                    session = dict(zip(columns, row))
                    sessions.append(session)
                
                return sessions
        except Exception as e:
            print(f"[ERROR] Ошибка получения завершенных сессий: {e}")
            return []

    def get_or_create_session(self, telegram_id: int) -> Dict[str, Any]:
        """Получить активную сессию пользователя или создать новую"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Ищем активную сессию
                cursor.execute("""
                    SELECT * FROM sessions 
                    WHERE telegram_id = ? AND status = 'active'
                    ORDER BY started_at DESC
                    LIMIT 1
                """, (telegram_id,))
                
                session = cursor.fetchone()
                
                if session:
                    # Возвращаем существующую сессию
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, session))
                else:
                    # Создаем новую сессию
                    session_id = self.create_session(telegram_id)
                    if session_id:
                        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
                        session = cursor.fetchone()
                        columns = [description[0] for description in cursor.description]
                        return dict(zip(columns, session))
                    else:
                        return None
                        
        except Exception as e:
            print(f"[ERROR] Ошибка получения/создания сессии: {e}")
            return None

    def update_session_data(self, session_id: int, data: Dict[str, Any]) -> bool:
        """Обновить данные сессии"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Формируем SET часть запроса
                set_fields = []
                values = []
                
                for field, value in data.items():
                    set_fields.append(f"{field} = ?")
                    values.append(value)
                
                values.append(session_id)
                
                query = f"""
                    UPDATE sessions 
                    SET {', '.join(set_fields)}
                    WHERE id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                
                return True
                
        except Exception as e:
            print(f"[ERROR] Ошибка обновления сессии: {e}")
            return False

# Глобальные функции для совместимости
def get_all_sessions(limit: int = 50):
    """Получение всех сессий (совместимость с новыми страницами)"""
    try:
        from . import db
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions 
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,))
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            sessions = []
            for row in rows:
                session = dict(zip(columns, row))
                sessions.append(session)
            
            return sessions
    except:
        return []

def get_sessions_by_date_range(start_date: str, end_date: str):
    """Получение сессий по диапазону дат (совместимость с новыми страницами)"""
    try:
        from . import db
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions 
                WHERE DATE(started_at) BETWEEN ? AND ?
                ORDER BY started_at DESC
            """, (start_date, end_date))
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            sessions = []
            for row in rows:
                session = dict(zip(columns, row))
                sessions.append(session)
            
            return sessions
    except:
        return []

def get_completed_applications():
    """Получение завершенных заявок (совместимость с новыми страницами)"""
    try:
        from . import db
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions 
                WHERE status = 'completed'
                ORDER BY completed_at DESC
            """)
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            applications = []
            for row in rows:
                application = dict(zip(columns, row))
                applications.append(application)
            
            return applications
    except:
        return [] 