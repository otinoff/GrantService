#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Настройки GrantService Telegram Bot
"""

import os
import logging
from typing import Dict, Any

# Настройки бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'http://localhost:5678/webhook/grant-service')
GIGACHAT_API_KEY = os.getenv('GIGACHAT_API_KEY')

# Настройки логирования
LOG_LEVEL = logging.INFO
LOG_FILE = '/var/GrantService/logs/telegram_bot.log'

# Настройки БД
DATABASE_PATH = '/var/GrantService/data/grantservice.db'

# Состояния пользователя
USER_STATES = {
    'MAIN_MENU': 'main_menu',
    'INTERVIEWING': 'interviewing',
    'REVIEW': 'review'
}

# Callback данные
CALLBACK_DATA = {
    'START_INTERVIEW': 'start_interview',
    'PAYMENT': 'payment',
    'STATUS': 'status',
    'ABOUT': 'about',
    'NEXT_QUESTION': 'next_question',
    'PREV_QUESTION': 'prev_question',
    'SUBMIT_APPLICATION': 'submit_application',
    'BACK_TO_MENU': 'back_to_menu'
}

# Настройки интервью
INTERVIEW_CONFIG = {
    'MAX_QUESTIONS': 100,  # Максимальное количество вопросов для проверки
    'DEFAULT_QUESTIONS': 24,  # Количество вопросов по умолчанию
    'SESSION_TIMEOUT': 3600,  # Таймаут сессии в секундах (1 час)
}

# Настройки n8n
N8N_CONFIG = {
    'TIMEOUT': 30,  # Таймаут запроса в секундах
    'RETRY_ATTEMPTS': 3,  # Количество попыток при ошибке
}

# Настройки ГигаЧат
GIGACHAT_CONFIG = {
    'MODEL': 'GigaChat-Pro',
    'TEMPERATURE': 0.7,
    'MAX_TOKENS': 2000,
    'TIMEOUT': 60,
} 