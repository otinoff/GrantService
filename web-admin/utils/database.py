#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database utilities for GrantService admin panel
Кроссплатформенная версия с централизованным подключением
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import streamlit as st

# CRITICAL: Setup paths first before imports
# Add web-admin to path to import setup_paths
web_admin_dir = Path(__file__).parent.parent
if str(web_admin_dir) not in sys.path:
    sys.path.insert(0, str(web_admin_dir))

import setup_paths  # Centralized path configuration

# Импортируем кроссплатформенные пути из core
try:
    from core import get_path_manager
    paths = get_path_manager()
except ImportError:
    # Fallback - paths не критичны для работы БД
    paths = None

from data.database import GrantServiceDatabase as Database, get_total_users, get_sessions_by_date_range, get_completed_applications, get_all_sessions, insert_agent_prompt, update_agent_prompt, delete_agent_prompt, get_researcher_logs as get_researcher_logs_db

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


# =============================================================================
# ЦЕНТРАЛИЗОВАННОЕ ПОДКЛЮЧЕНИЕ К БД
# =============================================================================

@st.cache_resource
def get_db_connection():
    """
    Establish centralized database connection with caching

    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        # Determine database path
        db_path = Path(__file__).parent.parent.parent / "data" / "grantservice.db"

        if not db_path.exists():
            logger.warning(f"Database file not found at {db_path}")
            # Try to create database directory
            db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create connection
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable column access by name

        logger.info(f"Database connection established: {db_path}")
        return conn

    except Exception as e:
        logger.error(f"Failed to connect to database: {e}", exc_info=True)
        raise


@st.cache_resource
def get_admin_database():
    """
    Get cached AdminDatabase instance

    Returns:
        AdminDatabase: Singleton database instance
    """
    return AdminDatabase()


# =============================================================================
# ADMIN DATABASE CLASS
# =============================================================================

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
                # PostgreSQL возвращает datetime объект
                started_at = session['started_at']
                if isinstance(started_at, str):
                    date = started_at[:10]  # YYYY-MM-DD
                else:
                    date = started_at.strftime('%Y-%m-%d')

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
            # Используем импортированную функцию вместо метода объекта
            return get_researcher_logs_db(limit=limit)
        except Exception as e:
            logger.error(f"Error getting researcher logs: {e}", exc_info=True)
            return []


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def execute_query(query: str, params: tuple = None, fetch_one: bool = False):
    """
    Execute SQL query with centralized connection

    Args:
        query: SQL query string
        params: Query parameters tuple
        fetch_one: If True, return single row, else all rows

    Returns:
        Query results or None if error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if query.strip().upper().startswith('SELECT'):
            result = cursor.fetchone() if fetch_one else cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount

        return result

    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        return None


def get_table_info(table_name: str):
    """
    Get table schema information

    Args:
        table_name: Name of the table

    Returns:
        List of column definitions
    """
    query = f"PRAGMA table_info({table_name})"
    return execute_query(query)


def get_table_count(table_name: str):
    """
    Get count of records in table

    Args:
        table_name: Name of the table

    Returns:
        Number of records
    """
    query = f"SELECT COUNT(*) FROM {table_name}"
    result = execute_query(query, fetch_one=True)
    return result[0] if result else 0
