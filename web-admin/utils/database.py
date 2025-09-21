#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database utilities for GrantService admin panel
Кроссплатформенная версия
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Добавляем путь к корню проекта для импорта
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

# Импортируем кроссплатформенные пути из core
try:
    from core import get_path_manager
    paths = get_path_manager()
except ImportError:
    # Fallback - paths не критичны для работы БД
    paths = None

from data.database import GrantServiceDatabase as Database, get_total_users, get_sessions_by_date_range, get_completed_applications, get_all_sessions, insert_agent_prompt, update_agent_prompt, delete_agent_prompt

# Импортируем logger
try:
    from utils.logger import setup_logger
except ImportError:
    # Fallback to relative import or create simple logger
    try:
        from .logger import setup_logger
    except ImportError:
        # Create a simple logger if imports fail
        import logging
        def setup_logger(name):
            return logging.getLogger(name)

# Инициализация логгера
logger = setup_logger('database')

class AdminDatabase:
    """Класс для работы с базой данных в админ панели"""
    
    def __init__(self):
        self.db = Database()
    
    def get_basic_stats(self):
        """Получение базовой статистики"""
        try:
            # Общее количество пользователей
            total_users = get_total_users()
            
            # Сессии за последние 7 дней
            recent_sessions = get_sessions_by_date_range(
                start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            # Завершенные заявки
            completed_apps = get_completed_applications()
            
            return {
                "total_users": total_users,
                "recent_sessions": len(recent_sessions),
                "completed_apps": len(completed_apps),
                "conversion_rate": round((len(completed_apps) / max(total_users, 1)) * 100, 1)
            }
        except Exception as e:
            logger.error(f"Error getting basic stats: {e}", exc_info=True)
            return {
                "total_users": 0,
                "recent_sessions": 0,
                "completed_apps": 0,
                "conversion_rate": 0
            }
    
    def get_daily_stats(self, days=7):
        """Получение статистики по дням"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            sessions = get_sessions_by_date_range(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Группируем по дням
            daily_data = {}
            for session in sessions:
                date = session['started_at'][:10]  # YYYY-MM-DD
                if date not in daily_data:
                    daily_data[date] = 0
                daily_data[date] += 1
            
            return daily_data
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}", exc_info=True)
            return {}
    
    def get_user_sessions(self, user_id=None, limit=50):
        """Получение сессий пользователей"""
        try:
            if user_id:
                return self.db.get_user_sessions(user_id, limit)
            else:
                return get_all_sessions(limit)
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}", exc_info=True)
            return []
    
    def get_researcher_statistics(self):
        """Получение статистики исследователя"""
        try:
            return self.db.get_researcher_statistics()
        except Exception as e:
            logger.error(f"Error getting researcher stats: {e}", exc_info=True)
            return {
                "total_queries": 0,
                "successful_queries": 0,
                "success_rate": 0,
                "total_cost": 0.0
            }
    
    def get_researcher_logs(self, user_id=None, status=None, limit=100):
        """Получение логов исследователя"""
        try:
            return self.db.get_researcher_logs(user_id, status, limit)
        except Exception as e:
            logger.error(f"Error getting researcher logs: {e}", exc_info=True)
            return [] 