 
import streamlit as st
import sys
import os

# Определяем пути кроссплатформенно
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService

# Добавляем пути
sys.path.insert(0, grandparent_dir)  # Для импорта config
sys.path.insert(0, parent_dir)  # Для импорта utils

# Импортируем кроссплатформенные пути
from config import paths

# Проверка авторизации - используем относительный импорт
from utils.auth import is_user_authorized

if not is_user_authorized():
    # Импортируем страницу входа
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "login_page",
        paths.LOGIN_PAGE
    )
    login_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(login_module)
    login_module.show_login_page()
    st.stop()