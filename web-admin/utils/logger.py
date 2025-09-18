#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенная система логирования для GrantService Web Admin
Версия 2.0 - с ротацией, полным покрытием уровней и централизованной обработкой ошибок
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
import traceback
import json
from functools import wraps

class ColoredFormatter(logging.Formatter):
    """Цветное форматирование для консоли"""
    
    # Цветовые коды
    COLORS = {
        'DEBUG': '\033[94m',     # Синий
        'INFO': '\033[92m',      # Зеленый
        'WARNING': '\033[93m',   # Желтый
        'ERROR': '\033[91m',     # Красный
        'CRITICAL': '\033[95m',  # Пурпурный
        'ENDC': '\033[0m'        # Конец цвета
    }
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['ENDC']}"
        return super().format(record)

class GrantServiceLogger:
    """Централизованная система логирования GrantService"""
    
    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        self.ensure_log_directory()
    
    def ensure_log_directory(self):
        """Создание директории логов с graceful fallback"""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            os.chmod(self.log_dir, 0o755)
        except (OSError, PermissionError) as e:
            print(f"⚠️ Не удалось создать папку логов: {e}")
            # Отключаем файловое логирование вместо fallback в /tmp
            self.log_dir = None
    
    def setup_logger(self, name, level=logging.INFO, 
                    max_bytes=10*1024*1024, backup_count=5, 
                    use_time_rotation=True):
        """
        Настройка логгера с улучшенными возможностями
        
        Args:
            name: Имя логгера (будет использовано в имени файла)
            level: Уровень логирования (по умолчанию INFO)
            max_bytes: Максимальный размер файла (10MB)
            backup_count: Количество бэкапов
            use_time_rotation: Использовать ли ротацию по времени
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Очищаем существующие обработчики
        if logger.handlers:
            logger.handlers.clear()
        
        # Форматтеры
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # === ФАЙЛОВЫЕ ОБРАБОТЧИКИ ===
        if self.log_dir:  # Только если папка логов доступна
            try:
                # 1. Основной лог файл с ротацией по размеру
                main_log_file = os.path.join(self.log_dir, f'{name}.log')
                file_handler = RotatingFileHandler(
                    main_log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)  # Сохраняем ВСЁ в файлах
                file_handler.setFormatter(detailed_formatter)
                logger.addHandler(file_handler)
                
                # 2. Файл только для ошибок
                error_log_file = os.path.join(self.log_dir, f'{name}_errors.log')
                error_handler = RotatingFileHandler(
                    error_log_file,
                    maxBytes=5*1024*1024,  # 5MB для ошибок
                    backupCount=3,
                    encoding='utf-8'
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(detailed_formatter)
                logger.addHandler(error_handler)
                
                # 3. Дневная ротация для долгосрочного хранения
                if use_time_rotation:
                    daily_log_file = os.path.join(self.log_dir, f'{name}_daily.log')
                    daily_handler = TimedRotatingFileHandler(
                        daily_log_file,
                        when='midnight',
                        interval=1,
                        backupCount=30,  # Храним 30 дней
                        encoding='utf-8'
                    )
                    daily_handler.setLevel(logging.INFO)
                    daily_handler.setFormatter(detailed_formatter)
                    logger.addHandler(daily_handler)
                
                logger.info(f"📝 Логирование инициализировано: {main_log_file}")
                
            except (OSError, PermissionError) as e:
                print(f"❌ Ошибка создания файлов логов: {e}")
        else:
            print("⚠️ Файловое логирование отключено - используется только консоль")
        
        # === КОНСОЛЬНЫЙ ОБРАБОТЧИК ===
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Предотвращаем дублирование логов
        logger.propagate = False
        
        return logger
    
    def get_log_stats(self):
        """Получение статистики по логам"""
        stats = {
            'log_directory': self.log_dir,
            'files': [],
            'total_size': 0,
            'last_modified': None
        }
        
        try:
            if os.path.exists(self.log_dir):
                for file in os.listdir(self.log_dir):
                    if file.endswith('.log'):
                        file_path = os.path.join(self.log_dir, file)
                        file_stat = os.stat(file_path)
                        stats['files'].append({
                            'name': file,
                            'size': file_stat.st_size,
                            'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
                        stats['total_size'] += file_stat.st_size
                        
                        if not stats['last_modified'] or file_stat.st_mtime > stats['last_modified']:
                            stats['last_modified'] = datetime.fromtimestamp(file_stat.st_mtime)
        
        except Exception as e:
            stats['error'] = str(e)
        
        return stats

# Глобальный экземпляр
_grant_logger = GrantServiceLogger()

def setup_logger(name, level=logging.INFO, **kwargs):
    """Фабрика логгеров - основная функция для создания логгеров"""
    return _grant_logger.setup_logger(name, level, **kwargs)

def get_log_stats():
    """Получить статистику логов"""
    return _grant_logger.get_log_stats()

def log_exception(logger, message="Произошла ошибка"):
    """Декоратор для автоматического логирования исключений"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{message} в {func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator

def log_performance(logger):
    """Декоратор для логирования производительности"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"⚡ {func.__name__} выполнен за {execution_time:.3f}с")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"💥 {func.__name__} упал через {execution_time:.3f}с: {str(e)}")
                raise
        return wrapper
    return decorator

# Создаем основные логгеры для системы
main_logger = setup_logger('web_admin', level=logging.INFO)
database_logger = setup_logger('database', level=logging.DEBUG)
api_logger = setup_logger('api', level=logging.INFO)
error_logger = setup_logger('errors', level=logging.ERROR)

# Логирование старта системы
main_logger.info("🚀 GrantService Web Admin - система логирования v2.0 запущена")
main_logger.info(f"📁 Логи сохраняются в: {_grant_logger.log_dir}")