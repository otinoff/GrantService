#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной интерфейс базы данных GrantService
"""

import os
from .models import GrantServiceDatabase

# Глобальный экземпляр БД для PostgreSQL
# ИЗМЕНЕНО: Lazy initialization для тестирования
# Параметры подключения берутся из переменных окружения
_db_instance = None

def get_db():
    """Получить или создать экземпляр БД (lazy initialization)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = GrantServiceDatabase()
    return _db_instance

def set_db(db_instance):
    """Установить экземпляр БД (для тестов)"""
    global _db_instance, _session_manager, _auth_manager
    _db_instance = db_instance
    # Сбросить managers чтобы пересоздались с новым DB
    _session_manager = None
    _auth_manager = None

def reset_db():
    """Сбросить экземпляр БД (для тестов)"""
    global _db_instance, _session_manager, _auth_manager
    _db_instance = None
    _session_manager = None
    _auth_manager = None

# Для обратной совместимости - создаём db при первом обращении
class _DBProxy:
    """Прокси для ленивой инициализации БД"""
    def __getattr__(self, name):
        return getattr(get_db(), name)

    def __call__(self, *args, **kwargs):
        return get_db()(*args, **kwargs)

db = _DBProxy()

# Импортируем классы авторизации
from .auth import AuthManager, UserRole, UserPermission

# Импортируем функции после создания экземпляра БД
from .researcher import (
    get_researcher_logs, add_researcher_log, get_latest_credit_balance,
    update_latest_credit_balance, update_all_credit_balances, update_input_tokens_by_model
)
from .users import get_total_users
from .sessions import get_all_sessions, get_sessions_by_date_range, get_completed_applications, SessionManager
from .interview import get_interview_questions, insert_interview_question, update_interview_question, delete_interview_question
from .agent_prompt_manager import get_agent_prompts, insert_agent_prompt, update_agent_prompt, delete_agent_prompt
from .user_progress import (
    get_user_progress, get_user_answers, get_current_question_info,
    get_all_users_progress, get_questions_with_answers, export_user_form
)
# Создаем экземпляры SessionManager и AuthManager лениво
_session_manager = None
_auth_manager = None

def get_session_manager():
    """Получить экземпляр SessionManager (lazy)"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(get_db())
    return _session_manager

def get_auth_manager():
    """Получить экземпляр AuthManager (lazy)"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager(get_db())
    return _auth_manager

# Для обратной совместимости
class _ManagerProxy:
    def __init__(self, getter):
        self._getter = getter
    def __getattr__(self, name):
        return getattr(self._getter(), name)

session_manager = _ManagerProxy(get_session_manager)
auth_manager = _ManagerProxy(get_auth_manager)

# Экспортируем основные функции для совместимости
__all__ = [
    'db',
    'session_manager',
    'auth_manager',
    'get_researcher_logs',
    'add_researcher_log',
    'get_latest_credit_balance',
    'update_latest_credit_balance',
    'update_all_credit_balances',
    'update_input_tokens_by_model',
    'get_interview_questions',
    'insert_interview_question',
    'update_interview_question',
    'delete_interview_question',
    'get_agent_prompts',
    'get_total_users',
    'get_all_sessions',
    'get_sessions_by_date_range',
    'get_completed_applications',
    'insert_agent_prompt',
    'update_agent_prompt',
    'delete_agent_prompt',
    'get_user_progress',
    'get_user_answers',
    'get_current_question_info',
    'get_all_users_progress',
    'get_questions_with_answers',
    'export_user_form',
    'get_or_create_session',
    'update_session_data'
]

# Добавляем функции как глобальные для совместимости
def get_or_create_session(telegram_id: int):
    """Получить или создать сессию пользователя"""
    return session_manager.get_or_create_session(telegram_id)

def update_session_data(session_id: int, data: dict):
    """Обновить данные сессии"""
    return session_manager.update_session_data(session_id, data)

# Функции для работы с грантовыми заявками
def save_grant_application(application_data):
    """Сохранить грантовую заявку в базу данных"""
    return db.save_grant_application(application_data)

def get_all_applications(limit=100, offset=0):
    """Получить список всех заявок"""
    return db.get_all_applications(limit, offset)

def get_application_by_number(application_number):
    """Получить заявку по номеру"""
    return db.get_application_by_number(application_number)