#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Шаблон для добавления проверки авторизации в страницы админки
"""

import streamlit as st
import sys
import os

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

# Импортируем модуль авторизации
from web_admin.utils.auth import is_user_authorized, get_current_user

def check_authorization():
    """
    Проверяет авторизацию пользователя и отображает страницу входа если не авторизован
    Возвращает True если пользователь авторизован, False если нет
    """
    if not is_user_authorized():
        # Импортируем страницу входа
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "login_page", 
            "/var/GrantService/web-admin/pages/🔐_Вход.py"
        )
        login_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(login_module)
        login_module.show_login_page()
        return False
    return True

def get_authorized_user():
    """
    Возвращает данные авторизованного пользователя
    """
    return get_current_user()

def require_authorization():
    """
    Декоратор для функций/страниц, требующих авторизации
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_authorization():
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator