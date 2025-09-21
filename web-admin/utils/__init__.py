#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Инициализация модуля utils для web-admin
"""

import sys
import os

# Добавляем пути для корректной работы импортов
current_dir = os.path.dirname(os.path.abspath(__file__))  # utils
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService

# Добавляем пути в sys.path
if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Экспортируем функции из auth
try:
    from .auth import (
        is_user_authorized,
        get_current_user,
        logout,
        require_auth,
        require_admin,
        validate_login_token,
        check_user_access,
        is_admin
    )
except ImportError as e:
    print(f"Warning: Could not import auth functions: {e}")
    # Создаем заглушки для функций
    def is_user_authorized():
        return False
    def get_current_user():
        return None
    def logout():
        pass
    def require_auth(func):
        return func
    def require_admin(func):
        return func
    def validate_login_token(token):
        return None
    def check_user_access(user_id):
        return False
    def is_admin(user_id):
        return False

# Экспортируем функции из database
try:
    from .database import AdminDatabase
except ImportError as e:
    print(f"Warning: Could not import AdminDatabase: {e}")
    AdminDatabase = None

# Экспортируем функции из logger
try:
    from .logger import setup_logger
except ImportError as e:
    print(f"Warning: Could not import logger: {e}")
    def setup_logger(name):
        import logging
        return logging.getLogger(name)

# Экспортируем функции из charts
try:
    from .charts import create_metrics_cards, create_daily_chart
except ImportError as e:
    print(f"Warning: Could not import charts: {e}")
    def create_metrics_cards(stats):
        pass
    def create_daily_chart(daily_stats, title):
        pass

# Список экспортируемых имен
__all__ = [
    'is_user_authorized',
    'get_current_user',
    'logout',
    'require_auth',
    'require_admin',
    'validate_login_token',
    'check_user_access',
    'is_admin',
    'AdminDatabase',
    'setup_logger',
    'create_metrics_cards',
    'create_daily_chart'
]