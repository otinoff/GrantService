#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Кроссплатформенная конфигурация путей для GrantService
Автоматически определяет операционную систему и устанавливает правильные пути
"""

import os
import sys
import platform

# ========================
# Определение ОС
# ========================
IS_WINDOWS = os.name == 'nt' or platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# Для отладки
CURRENT_OS = platform.system()
print(f"🖥️ Обнаружена ОС: {CURRENT_OS}")

# ========================
# Базовые пути проекта
# ========================
if IS_WINDOWS:
    # Windows пути
    BASE_PATH = r'C:\SnowWhiteAI\GrantService'
    WEB_ADMIN_PATH = r'C:\SnowWhiteAI\GrantService\web-admin'
    DATA_PATH = r'C:\SnowWhiteAI\GrantService\data'
    TELEGRAM_BOT_PATH = r'C:\SnowWhiteAI\GrantService\telegram-bot'
    CONFIG_PATH = r'C:\SnowWhiteAI\GrantService\config'
    SCRIPTS_PATH = r'C:\SnowWhiteAI\GrantService\scripts'
    AGENTS_PATH = r'C:\SnowWhiteAI\GrantService\agents'
else:  
    # Linux/Ubuntu/Mac пути
    BASE_PATH = '/var/GrantService'
    WEB_ADMIN_PATH = '/var/GrantService/web-admin'
    DATA_PATH = '/var/GrantService/data'
    TELEGRAM_BOT_PATH = '/var/GrantService/telegram-bot'
    CONFIG_PATH = '/var/GrantService/config'
    SCRIPTS_PATH = '/var/GrantService/scripts'
    AGENTS_PATH = '/var/GrantService/agents'

# ========================
# Подпути web-admin
# ========================
WEB_ADMIN_PAGES = os.path.join(WEB_ADMIN_PATH, 'pages')
WEB_ADMIN_UTILS = os.path.join(WEB_ADMIN_PATH, 'utils')
WEB_ADMIN_BACKEND = os.path.join(WEB_ADMIN_PATH, 'backend')
WEB_ADMIN_FRONTEND = os.path.join(WEB_ADMIN_PATH, 'frontend')

# ========================
# Подпути telegram-bot
# ========================
TELEGRAM_BOT_CONFIG = os.path.join(TELEGRAM_BOT_PATH, 'config')
TELEGRAM_BOT_HANDLERS = os.path.join(TELEGRAM_BOT_PATH, 'handlers')

# ========================
# Файлы страниц
# ========================
LOGIN_PAGE = os.path.join(WEB_ADMIN_PAGES, '🔐_Вход.py')
MAIN_PAGE = os.path.join(WEB_ADMIN_PAGES, '🏠_Главная.py')
USERS_PAGE = os.path.join(WEB_ADMIN_PAGES, '👥_Пользователи.py')
QUESTIONS_PAGE = os.path.join(WEB_ADMIN_PAGES, '❓_Вопросы_интервью.py')
ANALYTICS_PAGE = os.path.join(WEB_ADMIN_PAGES, '📊_Общая_аналитика.py')

# ========================
# Конфигурационные файлы
# ========================
CONSTANTS_FILE = os.path.join(TELEGRAM_BOT_CONFIG, 'constants.py')
AUTH_CONFIG_FILE = os.path.join(TELEGRAM_BOT_CONFIG, 'auth_config.py')

# ========================
# Добавление путей в sys.path
# ========================
def setup_paths():
    """Добавляет необходимые пути в sys.path"""
    paths_to_add = [
        BASE_PATH,
        WEB_ADMIN_PATH,
        DATA_PATH,
        TELEGRAM_BOT_PATH,
    ]
    
    for path in paths_to_add:
        if path not in sys.path and os.path.exists(path):
            sys.path.insert(0, path)
            print(f"✅ Добавлен путь: {path}")
        elif not os.path.exists(path):
            print(f"⚠️ Путь не существует: {path}")

# Автоматически настраиваем пути при импорте модуля
setup_paths()

# ========================
# Утилиты для работы с путями
# ========================
def get_absolute_path(relative_path):
    """
    Преобразует относительный путь в абсолютный
    относительно базовой директории проекта
    """
    return os.path.join(BASE_PATH, relative_path)

def ensure_directory_exists(path):
    """Создает директорию если она не существует"""
    os.makedirs(path, exist_ok=True)
    return path

def get_db_path():
    """Возвращает путь к файлу базы данных"""
    return os.path.join(DATA_PATH, 'grant_service.db')

def get_logs_path():
    """Возвращает путь к директории логов"""
    logs_path = os.path.join(BASE_PATH, 'logs')
    ensure_directory_exists(logs_path)
    return logs_path

# ========================
# Экспорт всех путей
# ========================
__all__ = [
    # Флаги ОС
    'IS_WINDOWS',
    'IS_LINUX', 
    'IS_MAC',
    'CURRENT_OS',
    
    # Основные пути
    'BASE_PATH',
    'WEB_ADMIN_PATH',
    'DATA_PATH',
    'TELEGRAM_BOT_PATH',
    'CONFIG_PATH',
    'SCRIPTS_PATH',
    'AGENTS_PATH',
    
    # Подпути
    'WEB_ADMIN_PAGES',
    'WEB_ADMIN_UTILS',
    'WEB_ADMIN_BACKEND',
    'WEB_ADMIN_FRONTEND',
    'TELEGRAM_BOT_CONFIG',
    'TELEGRAM_BOT_HANDLERS',
    
    # Файлы страниц
    'LOGIN_PAGE',
    'MAIN_PAGE',
    'USERS_PAGE',
    'QUESTIONS_PAGE',
    'ANALYTICS_PAGE',
    
    # Конфигурационные файлы
    'CONSTANTS_FILE',
    'AUTH_CONFIG_FILE',
    
    # Функции
    'setup_paths',
    'get_absolute_path',
    'ensure_directory_exists',
    'get_db_path',
    'get_logs_path',
]

# Отладочная информация при импорте
if __name__ != "__main__":
    print(f"📁 Базовый путь проекта: {BASE_PATH}")
    print(f"📁 Путь к web-admin: {WEB_ADMIN_PATH}")
    print(f"📁 Путь к данным: {DATA_PATH}")