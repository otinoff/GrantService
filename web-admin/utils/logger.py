#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система логирования для GrantService
"""

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name):
    """Настройка логгера с ротацией (fallback на консоль при ошибках записи)"""
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.ERROR)
    
    # Очищаем существующие обработчики
    if logger.handlers:
        logger.handlers.clear()
    
    # Формат сообщений
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    try:
        # Пытаемся создать папку для логов
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Файловый обработчик с ротацией
        log_file = os.path.join(log_dir, f'{name}.log')
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError):
        # Если не можем писать в файл - используем только консоль
        pass
    
    # Всегда добавляем консольный обработчик как fallback
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger