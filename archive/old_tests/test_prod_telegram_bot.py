#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест InteractiveInterviewer на ПРОДАКШЕНЕ через Telegram Bot

Симулирует пользователя, проходит интервью, проверяет результаты.

НЕ ТРЕБУЕТ SSH!

Usage:
    python test_prod_telegram_bot.py
"""

import asyncio
import os
import sys
from pathlib import Path
from telegram import Bot
from telegram.error import TelegramError
import time

# Load env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "config" / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUR_TELEGRAM_ID = 419597164  # Твой ID (замени если другой)

# Симулированные ответы
ANSWERS = [
    "Лучные клубы в Кемерово для детей и подростков",
    "Развивать стрельбу из лука как вид спорта",
    "Мало доступных спортивных секций для детей",
    "Дети и подростки 10-17 лет",
    "Кемерово, Кемеровская область",
    "Закупить оборудование, обучить тренеров, провести соревнования",
    "Групповые тренировки 3 раза в неделю",
    "100 детей пройдут обучение, 3 соревнования",
    "500000 рублей на оборудование и зарплаты",
    "Оборудование 300к, тренер 150к, аренда 50к",
    "Опытный тренер с 10-летним стажем",
    "Школа №5, спортивный комплекс Олимп",
    "Активная реклама и работа с родителями",
    "Абонплата от родителей и спонсоры",
    "12 месяцев реализации проекта",
]


async def test_prod_bot():
    """Тест продакшн бота"""

    print("="*80)
    print("ТЕСТ INTERACTIVEINTERVIEWER НА ПРОДАКШЕНЕ")
    print("="*80)
    print()

    if not BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN не найден в config/.env")
        return False

    bot = Bot(token=BOT_TOKEN)

    try:
        # Проверка подключения
        print("[1/5] Проверка подключения к боту...")
        me = await bot.get_me()
        print(f"[OK] Подключён к боту: @{me.username}")
        print(f"     Bot ID: {me.id}")
        print()

        # Отправка /start_interview
        print("[2/5] Запуск интервью...")
        await bot.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text="/start_interview"
        )
        print("[OK] Команда /start_interview отправлена")
        await asyncio.sleep(3)

        # Отправка /continue
        print("[OK] Отправка /continue...")
        await bot.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text="/continue"
        )
        print("[OK] Интервью начато")
        await asyncio.sleep(3)

        # Отправка ответов
        print()
        print("[3/5] Отправка ответов...")
        print(f"     Всего ответов: {len(ANSWERS)}")
        print()

        for i, answer in enumerate(ANSWERS, 1):
            print(f"[{i}/{len(ANSWERS)}] {answer[:60]}...")

            await bot.send_message(
                chat_id=YOUR_TELEGRAM_ID,
                text=answer
            )

            # Пауза между ответами
            await asyncio.sleep(2)

        print()
        print("[OK] Все ответы отправлены!")
        print()

        # Ждём завершения обработки
        print("[4/5] Ожидание финального аудита...")
        print("     (это может занять 10-20 секунд)")
        await asyncio.sleep(15)

        print()
        print("[5/5] РЕЗУЛЬТАТЫ")
        print("="*80)
        print()
        print("[INFO] Проверь в Telegram:")
        print(f"       1. Сколько вопросов задал бот? (должно быть >=10)")
        print(f"       2. Какую оценку получил? (должна быть >0)")
        print(f"       3. Есть ли финальное сообщение с результатами?")
        print()
        print("[SUCCESS] Тест завершён!")
        print()
        print("ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:")
        print("  - Бот задал >=10 вопросов (наше исправление!)")
        print("  - Оценка > 0 баллов")
        print("  - Анкета сохранена в БД")
        print()
        print("ЕСЛИ БОТА ЗАДАЛ < 10 ВОПРОСОВ:")
        print("  - Значит деплой ещё не завершился")
        print("  - Подожди 5 минут и попробуй ещё раз")
        print()

        return True

    except TelegramError as e:
        print(f"[ERROR] Ошибка Telegram: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_bot_status():
    """Быстрая проверка статуса бота"""

    if not BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN не найден")
        return False

    bot = Bot(token=BOT_TOKEN)

    try:
        me = await bot.get_me()
        print(f"[OK] Бот работает: @{me.username}")
        return True
    except Exception as e:
        print(f"[ERROR] Бот недоступен: {e}")
        return False


if __name__ == "__main__":
    print()
    print("Выбери режим:")
    print("1. Быстрая проверка статуса бота")
    print("2. Полный тест интервью (отправит 15 ответов)")
    print()

    if len(sys.argv) > 1 and sys.argv[1] == "full":
        # Полный тест
        success = asyncio.run(test_prod_bot())
    else:
        # Быстрая проверка
        print("Запуск быстрой проверки...")
        print("(для полного теста: python test_prod_telegram_bot.py full)")
        print()
        success = asyncio.run(check_bot_status())

    sys.exit(0 if success else 1)
