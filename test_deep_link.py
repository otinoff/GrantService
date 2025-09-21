#!/usr/bin/env python3
"""
Тестовый скрипт для проверки deep linking в Telegram боте
"""

import asyncio
import logging
from telegram import Bot
from telegram.ext import Application
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, 'C:\\SnowWhiteAI\\GrantService')

# Настраиваем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_env():
    """Загрузить переменные окружения"""
    env_path = 'config/.env'
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        value = value.strip('"\'')
                        os.environ[key] = value
        return True
    return False

async def test_deep_link():
    """Тестировать deep link"""
    # Загружаем конфигурацию
    if not load_env():
        logger.error("Не удалось загрузить .env файл")
        return
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен")
        return
    
    # Создаем бота
    bot = Bot(token=token)
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"Бот: @{bot_info.username}")
    
    # Формируем deep link
    deep_link = f"https://t.me/{bot_info.username}?start=get_access"
    
    print("\n" + "="*50)
    print("ТЕСТИРОВАНИЕ DEEP LINKING")
    print("="*50)
    print(f"\nБот: @{bot_info.username}")
    print(f"\nDeep link для получения токена доступа:")
    print(f"{deep_link}")
    print("\nЧто проверить:")
    print("1. Перейдите по ссылке выше")
    print("2. Нажмите START в боте")
    print("3. Бот должен автоматически сгенерировать токен")
    print("4. Проверьте логи бота на наличие сообщения:")
    print("   'Deep link /start get_access от пользователя ...'")
    print("\n" + "="*50)
    
    # Закрываем соединение
    await bot.close()

if __name__ == "__main__":
    asyncio.run(test_deep_link())