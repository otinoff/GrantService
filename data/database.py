#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
База данных GrantService - основной файл для совместимости
Экспортирует функции из папки database/
"""

# Импортируем все функции через модульную структуру
from .database.models import GrantServiceDatabase
from .database import (
    get_researcher_logs, add_researcher_log, get_latest_credit_balance,
    update_latest_credit_balance, update_all_credit_balances, update_input_tokens_by_model,
    get_interview_questions, insert_interview_question, update_interview_question, delete_interview_question,
    get_agent_prompts, insert_agent_prompt, update_agent_prompt, delete_agent_prompt,
    get_total_users, get_all_sessions, get_sessions_by_date_range, get_completed_applications,
    db, auth_manager, session_manager
)

# Импортируем новые функции авторизации
from .database.auth import (
    AuthManager, UserRole,
    create_login_token, verify_login_token,
    get_or_create_login_token, cleanup_expired_tokens,
    get_user_role, set_user_role
)

# Добавляем функции-обертки для работы с грантовыми заявками
def save_grant_application(application_data):
    """Сохранить грантовую заявку в базу данных"""
    return db.save_grant_application(application_data)

def get_all_applications(limit=100, offset=0):
    """Получить список всех заявок"""
    return db.get_all_applications(limit, offset)

def get_application_by_number(application_number):
    """Получить заявку по номеру"""
    return db.get_application_by_number(application_number)

def update_application_status(application_number, status):
    """Обновить статус заявки"""
    return db.update_application_status(application_number, status)

def get_applications_statistics():
    """Получить статистику по заявкам"""
    return db.get_applications_statistics()

# Для обратной совместимости - экспортируем основные классы и функции
__all__ = [
    'GrantServiceDatabase',
    'db',
    'auth_manager',
    'session_manager',
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
    # Новые функции для работы с грантовыми заявками
    'save_grant_application',
    'get_all_applications',
    'get_application_by_number',
    'update_application_status',
    'get_applications_statistics',
    # Функции авторизации
    'AuthManager',
    'UserRole',
    'create_login_token',
    'verify_login_token',
    'get_or_create_login_token',
    'cleanup_expired_tokens',
    'get_user_role',
    'set_user_role'
]