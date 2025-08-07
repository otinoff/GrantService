#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с пользователями
"""

import sqlite3
from typing import List, Dict, Any
from .models import GrantServiceDatabase, get_kuzbass_time

class UserManager:
    def __init__(self, db: GrantServiceDatabase):
        self.db = db
    
    def register_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Зарегистрировать нового пользователя"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем, существует ли пользователь
                cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    # Обновляем время последней активности
                    cursor.execute("""
                        UPDATE users 
                        SET last_active = ?, username = ?, first_name = ?, last_name = ?
                        WHERE telegram_id = ?
                    """, (get_kuzbass_time(), username, first_name, last_name, telegram_id))
                    print(f"✅ Пользователь {telegram_id} обновлен")
                else:
                    # Создаем нового пользователя
                    current_time = get_kuzbass_time()
                    cursor.execute("""
                        INSERT INTO users (telegram_id, username, first_name, last_name, registration_date, last_active)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (telegram_id, username, first_name, last_name, current_time, current_time))
                    print(f"✅ Новый пользователь {telegram_id} зарегистрирован")
                
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Ошибка регистрации пользователя: {e}")
            return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получить всех пользователей с их статистикой"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        u.*,
                        COUNT(s.id) as total_sessions,
                        COUNT(CASE WHEN s.completion_status = 'completed' THEN 1 END) as completed_sessions,
                        AVG(s.progress_percentage) as avg_progress,
                        MAX(s.last_activity) as last_session_activity
                    FROM users u
                    LEFT JOIN sessions s ON u.telegram_id = s.telegram_id
                    GROUP BY u.telegram_id
                    ORDER BY u.registration_date DESC
                """)
                
                columns = [description[0] for description in cursor.description]
                users = []
                for row in cursor.fetchall():
                    user = dict(zip(columns, row))
                    users.append(user)
                
                return users
        except Exception as e:
            print(f"❌ Ошибка получения пользователей: {e}")
            return []

# Глобальные функции для совместимости
def get_total_users():
    """Получение общего количества пользователей (совместимость с новыми страницами)"""
    try:
        from . import db
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]
    except:
        return 0 