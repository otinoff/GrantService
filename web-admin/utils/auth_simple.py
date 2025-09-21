#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая заглушка для авторизации - отключает все проверки
Позволяет всем пользователям доступ к админке
"""

from typing import Optional, Dict, Any
from functools import wraps

def validate_login_token(token: str) -> Optional[Dict[str, Any]]:
    """Всегда возвращает данные пользователя (без проверки)"""
    return {
        'id': 1,
        'telegram_id': 123456789,
        'user_id': 123456789,
        'username': 'admin',
        'first_name': 'Admin',
        'last_name': 'User',
        'is_active': True
    }

def check_user_access(user_id: int) -> bool:
    """Всегда разрешает доступ"""
    return True

def is_admin(user_id: int) -> bool:
    """Все пользователи - администраторы"""
    return True

def is_user_authorized() -> bool:
    """Всегда авторизован"""
    return True

def get_current_user() -> Optional[Dict[str, Any]]:
    """Возвращает фиктивного пользователя"""
    return {
        'id': 1,
        'telegram_id': 123456789,
        'user_id': 123456789,
        'username': 'admin', 
        'first_name': 'Admin',
        'last_name': 'User',
        'is_active': True
    }

def logout() -> None:
    """Ничего не делает"""
    pass

def require_auth(func):
    """Декоратор без проверки авторизации"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def require_admin(func):
    """Декоратор без проверки прав администратора"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper