#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с пользователями (PostgreSQL)
"""

from typing import List, Dict, Any
from .models import GrantServiceDatabase, get_kuzbass_time

class UserManager:
    def __init__(self, db: GrantServiceDatabase):
        self.db = db

    def register_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Зарегистрировать нового пользователя"""
        return self.db.register_user(telegram_id, username, first_name, last_name)

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получить всех пользователей с их статистикой"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        u.*,
                        COUNT(s.id) as sessions_count,
                        COUNT(CASE WHEN s.status = 'completed' THEN 1 END) as completed_sessions,
                        AVG(CASE
                            WHEN s.current_step ~ '^[0-9]+$'
                            THEN CAST(s.current_step AS INTEGER)
                            ELSE 0
                        END) as avg_progress,
                        MAX(s.last_activity) as last_session_activity
                    FROM users u
                    LEFT JOIN sessions s ON u.telegram_id = s.telegram_id
                    GROUP BY u.id, u.telegram_id, u.username, u.first_name, u.last_name,
                             u.role, u.permissions, u.login_token, u.token_expires_at,
                             u.registration_date, u.last_active, u.total_sessions,
                             u.completed_applications, u.is_active
                    ORDER BY u.registration_date DESC
                """)

                columns = [description[0] for description in cursor.description]
                users = []
                for row in cursor.fetchall():
                    user = dict(zip(columns, row))
                    users.append(user)

                cursor.close()
                return users
        except Exception as e:
            print(f"❌ Ошибка получения пользователей: {e}")
            return []

# Глобальные функции для совместимости
def get_total_users():
    """Получение общего количества пользователей (PostgreSQL)"""
    try:
        from . import db
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
    except Exception as e:
        print(f"❌ Ошибка подсчета пользователей: {e}")
        return 0 