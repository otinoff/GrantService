#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Константы GrantService с многоагентной архитектурой
"""

# Состояния пользователя
USER_STATES = {
    'MAIN_MENU': 'main_menu',
    'INTERVIEWING': 'interviewing',
    'REVIEW': 'review',
    'PAYMENT': 'payment',
    'STATUS': 'status'
}

# Callback данные для кнопок
CALLBACK_DATA = {
    'START_INTERVIEW': 'start_interview',
    'PAYMENT': 'payment',
    'STATUS': 'status',
    'ABOUT': 'about',
    'NEXT_QUESTION': 'next_question',
    'PREV_QUESTION': 'prev_question',
    'BACK_TO_MENU': 'back_to_menu',
    'SUBMIT_APPLICATION': 'submit_application',
    'REVIEW_APPLICATION': 'review_application'
}

# Типы агентов
AGENT_TYPES = {
    'INTERVIEWER': 'interviewer',
    'RESEARCHER': 'researcher',
    'WRITER': 'writer',
    'AUDITOR': 'auditor'
}

# Статусы задач агентов
TASK_STATUSES = {
    'PENDING': 'pending',
    'IN_PROGRESS': 'in_progress',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'CANCELLED': 'cancelled'
}

# Типы вопросов
QUESTION_TYPES = {
    'TEXT': 'text',
    'TEXTAREA': 'textarea',
    'SELECT': 'select',
    'MULTISELECT': 'multiselect',
    'NUMBER': 'number',
    'DATE': 'date'
}

# Статусы сессий
SESSION_STATUSES = {
    'ACTIVE': 'active',
    'COMPLETED': 'completed',
    'CANCELLED': 'cancelled',
    'PAUSED': 'paused'
}

# Типы уведомлений
NOTIFICATION_TYPES = {
    'INFO': 'info',
    'SUCCESS': 'success',
    'WARNING': 'warning',
    'ERROR': 'error'
}

# Форматы файлов
FILE_FORMATS = {
    'PDF': 'pdf',
    'DOCX': 'docx',
    'TXT': 'txt',
    'JSON': 'json'
}

# Ограничения
LIMITS = {
    'MAX_QUESTIONS': 30,
    'MAX_ANSWER_LENGTH': 2000,
    'MAX_PROJECT_NAME_LENGTH': 100,
    'MAX_DESCRIPTION_LENGTH': 500,
    'MAX_TEAM_SIZE': 10
}

# Валидация
VALIDATION_RULES = {
    'PROJECT_NAME': {
        'min_length': 3,
        'max_length': 100,
        'pattern': r'^[а-яёa-z0-9\s\-_\.]+$'
    },
    'EMAIL': {
        'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    },
    'PHONE': {
        'pattern': r'^\+?[1-9]\d{1,14}$'
    }
}

# Сообщения об ошибках
ERROR_MESSAGES = {
    'VALIDATION_ERROR': 'Ошибка валидации данных',
    'API_ERROR': 'Ошибка внешнего API',
    'DATABASE_ERROR': 'Ошибка базы данных',
    'TIMEOUT_ERROR': 'Превышено время ожидания',
    'RATE_LIMIT_ERROR': 'Превышен лимит запросов',
    'AUTHENTICATION_ERROR': 'Ошибка аутентификации',
    'PERMISSION_ERROR': 'Недостаточно прав',
    'NOT_FOUND_ERROR': 'Данные не найдены',
    'INTERNAL_ERROR': 'Внутренняя ошибка системы'
}

# Успешные сообщения
SUCCESS_MESSAGES = {
    'INTERVIEW_STARTED': 'Интервью начато',
    'QUESTION_ANSWERED': 'Ответ сохранен',
    'INTERVIEW_COMPLETED': 'Интервью завершено',
    'APPLICATION_SUBMITTED': 'Заявка отправлена на проверку',
    'APPLICATION_GENERATED': 'Заявка сгенерирована',
    'RESEARCH_COMPLETED': 'Исследование завершено',
    'ANALYSIS_COMPLETED': 'Анализ завершен'
}

# Эмодзи для интерфейса
EMOJIS = {
    'START': '🚀',
    'MENU': '📋',
    'QUESTION': '❓',
    'ANSWER': '💬',
    'SUCCESS': '✅',
    'ERROR': '❌',
    'WARNING': '⚠️',
    'INFO': 'ℹ️',
    'PAYMENT': '💳',
    'STATUS': '📊',
    'ABOUT': 'ℹ️',
    'BACK': '⬅️',
    'NEXT': '➡️',
    'SUBMIT': '📤',
    'REVIEW': '🔍',
    'DOWNLOAD': '📥',
    'SETTINGS': '⚙️',
    'HELP': '❓',
    'CLOSE': '❌',
    'SAVE': '💾',
    'EDIT': '✏️',
    'DELETE': '🗑️',
    'SEARCH': '🔍',
    'FILTER': '🔧',
    'SORT': '📊',
    'EXPORT': '📤',
    'IMPORT': '📥',
    'REFRESH': '🔄',
    'LOADING': '⏳',
    'DONE': '✅',
    'PROGRESS': '📈',
    'TIME': '⏰',
    'CALENDAR': '📅',
    'USER': '👤',
    'TEAM': '👥',
    'PROJECT': '📁',
    'GRANT': '💰',
    'DOCUMENT': '📄',
    'REPORT': '📊',
    'ANALYTICS': '📈',
    'MONITORING': '📊',
    'AGENT': '🤖',
    'AI': '🧠',
    'RESEARCH': '🔬',
    'WRITE': '✍️',
    'AUDIT': '🔍'
}

# Цвета для интерфейса (если используется)
COLORS = {
    'PRIMARY': '#007bff',
    'SUCCESS': '#28a745',
    'WARNING': '#ffc107',
    'DANGER': '#dc3545',
    'INFO': '#17a2b8',
    'LIGHT': '#f8f9fa',
    'DARK': '#343a40'
}

# Настройки по умолчанию
DEFAULTS = {
    'LANGUAGE': 'ru',
    'TIMEZONE': 'Asia/Novosibirsk',
    'CURRENCY': 'RUB',
    'DATE_FORMAT': '%d.%m.%Y',
    'TIME_FORMAT': '%H:%M',
    'DATETIME_FORMAT': '%d.%m.%Y %H:%M'
}

# Авторизация

# Администраторы - имеют доступ к админ-панели и команде /admin
ADMIN_USERS = {
    826960528,   # Администратор 1
    591630092,   # Администратор 2
    5032079932,  # Администратор 3
}

# Разрешенные пользователи для бота
# ВАЖНО: Пустой set означает, что бот доступен ВСЕМ пользователям
ALLOWED_USERS = set()  # Пустой set = бот доступен для всех пользователей Telegram