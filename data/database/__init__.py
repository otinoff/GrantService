#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной интерфейс базы данных GrantService
"""

from .models import GrantServiceDatabase

# Глобальный экземпляр БД
db = GrantServiceDatabase()

# Импортируем функции после создания экземпляра БД
from .researcher import (
    get_researcher_logs, add_researcher_log, get_latest_credit_balance,
    update_latest_credit_balance, update_all_credit_balances, update_input_tokens_by_model
)
from .users import get_total_users
from .sessions import get_all_sessions, get_sessions_by_date_range, get_completed_applications, SessionManager
from .interview import get_interview_questions, insert_interview_question, update_interview_question, delete_interview_question
from .agents import get_agent_prompts, insert_agent_prompt, update_agent_prompt, delete_agent_prompt
from .user_progress import (
    get_user_progress, get_user_answers, get_current_question_info,
    get_all_users_progress, get_questions_with_answers, export_user_form
)
from .auth import AuthManager

# Создаем экземпляр SessionManager для доступа к новым функциям
session_manager = SessionManager(db)

# Создаем экземпляр AuthManager для управления авторизацией
auth_manager = AuthManager(db)

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