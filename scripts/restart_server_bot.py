#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для перезапуска бота на сервере и проверки базы данных
"""

import os
import sys
import sqlite3
import subprocess
import time
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_database_status():
    """Проверка состояния базы данных"""
    db_path = "data/grant_service.db"
    
    if not os.path.exists(db_path):
        logger.error(f"База данных не найдена: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем количество активных вопросов
        cursor.execute("SELECT COUNT(*) FROM questions WHERE is_active = 1")
        active_questions = cursor.fetchone()[0]
        
        # Проверяем наличие подсказок
        cursor.execute("SELECT COUNT(*) FROM questions WHERE hint_text IS NOT NULL AND hint_text != ''")
        questions_with_hints = cursor.fetchone()[0]
        
        # Проверяем последнее обновление
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
        table_exists = cursor.fetchone() is not None
        
        conn.close()
        
        logger.info(f"📊 Состояние базы данных:")
        logger.info(f"  - Активных вопросов: {active_questions}")
        logger.info(f"  - Вопросов с подсказками: {questions_with_hints}")
        logger.info(f"  - Таблица questions существует: {table_exists}")
        
        # Проверяем время изменения файла
        mod_time = os.path.getmtime(db_path)
        mod_datetime = datetime.fromtimestamp(mod_time)
        logger.info(f"  - Последнее изменение БД: {mod_datetime}")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка проверки БД: {e}")
        return False

def find_bot_process():
    """Поиск процесса бота"""
    try:
        # Поиск процесса Python с main.py
        result = subprocess.run(['pgrep', '-f', 'main.py'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            logger.info(f"🔍 Найдены процессы бота: {pids}")
            return pids
        else:
            logger.info("🔍 Процессы бота не найдены")
            return []
    except Exception as e:
        logger.error(f"Ошибка поиска процессов: {e}")
        return []

def kill_bot_processes(pids):
    """Остановка процессов бота"""
    for pid in pids:
        try:
            subprocess.run(['kill', '-TERM', pid], check=True)
            logger.info(f"✅ Процесс {pid} остановлен")
            time.sleep(2)
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Не удалось остановить процесс {pid}: {e}")
            try:
                subprocess.run(['kill', '-KILL', pid], check=True)
                logger.info(f"💀 Процесс {pid} принудительно завершен")
            except Exception as e2:
                logger.error(f"❌ Не удалось завершить процесс {pid}: {e2}")

def start_bot():
    """Запуск бота"""
    try:
        # Переходим в папку telegram-bot
        os.chdir('telegram-bot')
        
        # Запускаем бота в фоне
        subprocess.Popen(['python3', 'main.py'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL,
                        start_new_session=True)
        
        logger.info("🚀 Бот запущен")
        
        # Возвращаемся в корневую папку
        os.chdir('..')
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("🔄 Начинаем перезапуск бота на сервере")
    
    # 1. Проверяем состояние БД
    logger.info("1️⃣ Проверка базы данных...")
    if not check_database_status():
        logger.error("❌ Проблемы с базой данных")
        return False
    
    # 2. Ищем процессы бота
    logger.info("2️⃣ Поиск процессов бота...")
    pids = find_bot_process()
    
    # 3. Останавливаем бота если он запущен
    if pids:
        logger.info("3️⃣ Остановка текущих процессов бота...")
        kill_bot_processes(pids)
        time.sleep(3)
    else:
        logger.info("3️⃣ Активных процессов бота не найдено")
    
    # 4. Запускаем бота заново
    logger.info("4️⃣ Запуск бота...")
    if start_bot():
        logger.info("✅ Бот успешно перезапущен!")
        
        # Ждем немного и проверяем что бот запустился
        time.sleep(5)
        new_pids = find_bot_process()
        if new_pids:
            logger.info(f"✅ Бот работает с PID: {new_pids}")
        else:
            logger.warning("⚠️ Бот может не запуститься - проверьте логи")
        
        return True
    else:
        logger.error("❌ Не удалось запустить бота")
        return False

if __name__ == "__main__":
    main()