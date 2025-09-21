#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль авторизации для Streamlit админки GrantService
Кроссплатформенная версия
"""

import streamlit as st
import sys
import os
from typing import Optional, Dict, Any
from functools import wraps
import importlib.util

# Добавляем путь к корню проекта для импорта
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

# Импортируем кроссплатформенные пути из core
try:
    from core import get_path_manager
    paths = get_path_manager()
except ImportError:
    # Fallback to direct path calculation if core module not available
    from pathlib import Path
    class FallbackPaths:
        def __init__(self):
            self.base_path = Path(parent_dir)
            self.CONSTANTS_FILE = self.base_path / "telegram-bot" / "config" / "constants.py"
            self.LOGIN_PAGE = self.base_path / "web-admin" / "pages" / "login.py"
    paths = FallbackPaths()

from data.database import GrantServiceDatabase

# Динамический импорт модуля telegram-bot с дефисом в имени
try:
    spec = importlib.util.spec_from_file_location(
        "telegram_bot_config_constants",
        str(paths.CONSTANTS_FILE) if hasattr(paths, 'CONSTANTS_FILE') else str(paths.constants_file)
    )
    if spec and spec.loader:
        telegram_bot_config_constants = importlib.util.module_from_spec(spec)
        sys.modules["telegram_bot_config_constants"] = telegram_bot_config_constants
        spec.loader.exec_module(telegram_bot_config_constants)
        
        # Получаем переменные из импортированного модуля
        ADMIN_USERS = telegram_bot_config_constants.ADMIN_USERS
        ALLOWED_USERS = telegram_bot_config_constants.ALLOWED_USERS
    else:
        # Fallback values if import fails
        ADMIN_USERS = []
        ALLOWED_USERS = []
        print("⚠️ Warning: Could not load user lists from constants.py")
except Exception as e:
    print(f"⚠️ Warning: Error loading constants: {e}")
    ADMIN_USERS = []
    ALLOWED_USERS = []
def validate_login_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Проверяет токен авторизации и возвращает данные пользователя
    
    Args:
        token (str): Токен авторизации
        
    Returns:
        Optional[Dict[str, Any]]: Данные пользователя или None
    """
    print(f"🔍 validate_login_token вызван с токеном: {token[:20] if token else 'None'}")
    
    if not token:
        print("❌ Пустой токен")
        return None
    
    try:
        # Используем глобальный экземпляр БД
        from data.database import db
        user_data = db.validate_login_token(token)
        print(f"👤 Получены данные пользователя: {user_data}")
        return user_data
    except Exception as e:
        print(f"❌ Ошибка проверки токена: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_user_access(user_id: int) -> bool:
    """
    Проверяет, имеет ли пользователь доступ к админке
    
    Args:
        user_id (int): ID пользователя в Telegram
        
    Returns:
        bool: True если пользователь имеет доступ
    """
    print(f"🔍 Проверка доступа для пользователя {user_id}")
    print(f"📋 ALLOWED_USERS: {ALLOWED_USERS}")
    
    # Если список разрешенных пользователей пуст, разрешаем всем
    if not ALLOWED_USERS:
        print("✅ Доступ разрешен для всех (список ALLOWED_USERS пуст)")
        return True
    
    has_access = user_id in ALLOWED_USERS
    print(f"{'✅' if has_access else '❌'} Доступ {'предоставлен' if has_access else 'запрещен'} для пользователя {user_id}")
    return has_access

def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором
    
    Args:
        user_id (int): ID пользователя в Telegram
        
    Returns:
        bool: True если пользователь администратор
    """
    return user_id in ADMIN_USERS

def is_user_authorized() -> bool:
    """
    Проверяет, авторизован ли текущий пользователь
    
    Returns:
        bool: True если пользователь авторизован
    """
    return 'auth_token' in st.session_state and 'user' in st.session_state

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Возвращает данные текущего пользователя
    
    Returns:
        Optional[Dict[str, Any]]: Данные пользователя или None
    """
    return st.session_state.get('user')

def logout() -> None:
    """Выполняет выход пользователя"""
    if 'auth_token' in st.session_state:
        del st.session_state.auth_token
    if 'user' in st.session_state:
        del st.session_state.user
    st.rerun()

def require_auth(func):
    """
    Декоратор для функций/страниц, требующих авторизации
    
    Args:
        func: Функция для декорирования
        
    Returns:
        wrapper: Обернутая функция
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_user_authorized():
            # Импортируем страницу входа с кроссплатформенным путем
            import importlib.util
            login_page_path = str(paths.LOGIN_PAGE) if hasattr(paths, 'LOGIN_PAGE') else str(paths.login_page)
            spec = importlib.util.spec_from_file_location(
                "login_page",
                login_page_path
            )
            login_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(login_module)
            login_module.show_login_page()
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def require_admin(func):
    """
    Декоратор для функций/страниц, требующих прав администратора
    
    Args:
        func: Функция для декорирования
        
    Returns:
        wrapper: Обернутая функция
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_user_authorized():
            # Импортируем страницу входа с кроссплатформенным путем
            import importlib.util
            login_page_path = str(paths.LOGIN_PAGE) if hasattr(paths, 'LOGIN_PAGE') else str(paths.login_page)
            spec = importlib.util.spec_from_file_location(
                "login_page",
                login_page_path
            )
            login_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(login_module)
            login_module.show_login_page()
            st.stop()
        
        user = get_current_user()
        if not user or not is_admin(user['telegram_id']):
            st.error("❌ Недостаточно прав. Требуются права администратора.")
            st.stop()
            
        return func(*args, **kwargs)
    return wrapper