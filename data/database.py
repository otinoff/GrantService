#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
База данных GrantService - основной файл для совместимости
Теперь использует модульную структуру из папки database/
"""

# Импортируем все из новой модульной структуры
from .database import *

# Для обратной совместимости - экспортируем основные классы и функции
__all__ = [
    'GrantServiceDatabase',
    'db',
    'get_researcher_logs',
    'add_researcher_log', 
    'get_latest_credit_balance',
    'update_latest_credit_balance',
    'update_all_credit_balances',
    'update_input_tokens_by_model',
    'get_interview_questions',
    'get_agent_prompts',
    'get_total_users',
    'get_all_sessions',
    'get_sessions_by_date_range',
    'get_completed_applications',
    'insert_agent_prompt',
    'update_agent_prompt',
    'delete_agent_prompt'
] 