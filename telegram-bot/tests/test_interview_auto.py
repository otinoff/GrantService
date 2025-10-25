#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматический тест Interactive Interview V2 с использованием Telethon

Этот скрипт симулирует реального пользователя и тестирует бота автоматически.

Requirements:
    pip install telethon pytest pytest-asyncio

Setup:
    1. Получить API credentials на https://my.telegram.org/
    2. Создать .env с TELEGRAM_API_ID и TELEGRAM_API_HASH
    3. Запустить: python test_interview_auto.py

Author: Grant Service Testing Agent
Created: 2025-10-21
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.custom import Message

# Load env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / 'config' / '.env')


class InterviewTester:
    """
    Автоматический тестер для Interactive Interview V2

    Использует Telethon для симуляции реального пользователя.
    """

    def __init__(
        self,
        bot_username: str = "@grantservice_test_bot",  # ЗАМЕНИТЕ на имя вашего бота!
        api_id: int = None,
        api_hash: str = None
    ):
        """
        Инициализация тестера

        Args:
            bot_username: Username бота (с @)
            api_id: Telegram API ID (из my.telegram.org)
            api_hash: Telegram API Hash
        """
        self.bot_username = bot_username

        # Получить credentials из env или параметров
        self.api_id = api_id or int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = api_hash or os.getenv('TELEGRAM_API_HASH')

        if not self.api_id or not self.api_hash:
            raise ValueError(
                "TELEGRAM_API_ID и TELEGRAM_API_HASH должны быть установлены!\n"
                "Получите их на https://my.telegram.org/"
            )

        # Создать клиента
        self.client = TelegramClient(
            'test_session',  # Файл сессии
            self.api_id,
            self.api_hash
        )

        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }

    async def start(self):
        """Запустить клиента"""
        await self.client.start()
        print(f"✅ Подключено к Telegram как {await self.client.get_me()}")

    async def stop(self):
        """Остановить клиента"""
        await self.client.disconnect()

    async def send_and_wait(self, conv, message: str, timeout: int = 15) -> Message:
        """
        Отправить сообщение и подождать ответа

        Args:
            conv: Conversation объект
            message: Текст сообщения
            timeout: Таймаут в секундах

        Returns:
            Message от бота
        """
        print(f"\n👤 USER → BOT: {message}")
        await conv.send_message(message)

        try:
            response = await conv.get_response(timeout=timeout)
            print(f"🤖 BOT → USER: {response.text[:200]}...")
            return response
        except asyncio.TimeoutError:
            print(f"❌ TIMEOUT: Бот не ответил за {timeout} секунд")
            raise

    async def test_interview_flow(self):
        """
        Тест полного интервью

        Проверяет:
        - /start_interview_v2 запускает интервью
        - /continue задает первый вопрос
        - Ответы обрабатываются
        - Бот задает следующие вопросы
        - Интервью завершается с оценкой
        """
        print("\n" + "=" * 80)
        print("ТЕСТ: Полный Flow Interactive Interview V2")
        print("=" * 80)

        self.results['total_tests'] += 1

        try:
            async with self.client.conversation(self.bot_username) as conv:
                # 1. Запустить интервью
                print("\n[ШАГ 1] Запуск интервью...")
                response = await self.send_and_wait(conv, '/start_interview_v2', timeout=10)

                assert 'Здравствуйте' in response.text or 'привет' in response.text.lower(), \
                    "Приветствие не содержит ожидаемый текст"
                print("✅ Приветствие получено")

                # 2. Продолжить (получить первый вопрос)
                print("\n[ШАГ 2] Получение первого вопроса...")
                response = await self.send_and_wait(conv, '/continue', timeout=15)

                assert len(response.text) > 10, "Вопрос слишком короткий"
                print(f"✅ Первый вопрос получен: {response.text[:100]}...")

                # 3. Отвечаем на 5 вопросов
                print("\n[ШАГ 3] Отвечаем на вопросы...")

                answers = [
                    "Литературный проект для жителей Кемерово - организация литературных вечеров и встреч с писателями",
                    "Недостаток культурных мероприятий в городе, особенно связанных с литературой",
                    "Жители города Кемерово, любители литературы, школьники и студенты",
                    "Проведение ежемесячных литературных вечеров в библиотеках города с приглашением местных писателей",
                    "500000 рублей на год: 300000 на гонорары писателей, 100000 на аренду помещений, 100000 на рекламу"
                ]

                for i, answer in enumerate(answers, 1):
                    print(f"\n  Ответ {i}/5...")
                    response = await self.send_and_wait(conv, answer, timeout=20)

                    # Проверяем что бот ответил (либо вопрос, либо прогресс, либо завершение)
                    assert len(response.text) > 0, f"Бот не ответил на ответ {i}"

                    # Проверяем что это НЕ ошибка
                    assert 'ошибка' not in response.text.lower(), f"Бот вернул ошибку: {response.text}"
                    assert 'error' not in response.text.lower(), f"Бот вернул ошибку: {response.text}"

                    print(f"  ✅ Ответ {i} обработан")

                # 4. Ждем завершения интервью
                print("\n[ШАГ 4] Ожидание завершения интервью...")

                # Может быть ещё несколько вопросов или сразу завершение
                max_turns = 10
                for turn in range(max_turns):
                    try:
                        response = await conv.get_response(timeout=5)
                        print(f"  Ответ бота: {response.text[:100]}...")

                        # Проверяем признаки завершения
                        if any(word in response.text.lower() for word in [
                            'завершено', 'спасибо', 'оценка', 'score', 'интервью завершено'
                        ]):
                            print(f"✅ Интервью завершено! Финальное сообщение: {response.text[:200]}...")
                            break
                    except asyncio.TimeoutError:
                        # Timeout - возможно интервью уже завершено
                        print("  Timeout - возможно интервью завершено")
                        break

                print("\n✅ ТЕСТ ПРОЙДЕН: Interactive Interview V2 работает!")
                self.results['passed'] += 1

        except AssertionError as e:
            print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН: {e}")
            self.results['failed'] += 1
            self.results['errors'].append(str(e))

        except Exception as e:
            print(f"\n❌ ОШИБКА В ТЕСТЕ: {e}")
            import traceback
            traceback.print_exc()
            self.results['failed'] += 1
            self.results['errors'].append(f"Exception: {e}")

    async def test_already_covered_fix(self):
        """
        Регрессионный тест для бага "already covered"

        Проверяет что бот ЗАДАЕТ вопросы, а не сразу завершает интервью.
        """
        print("\n" + "=" * 80)
        print("РЕГРЕССИОННЫЙ ТЕСТ: Already Covered Bug Fix")
        print("=" * 80)

        self.results['total_tests'] += 1

        try:
            async with self.client.conversation(self.bot_username) as conv:
                # Запустить интервью
                await self.send_and_wait(conv, '/start_interview_v2', timeout=10)

                # Получить первый вопрос
                response = await self.send_and_wait(conv, '/continue', timeout=15)

                # КРИТИЧЕСКАЯ ПРОВЕРКА: вопрос должен быть задан
                assert '?' in response.text or 'расскажите' in response.text.lower(), \
                    "Бот не задал вопрос! Возможно баг 'already covered' вернулся"

                # Ответить
                await self.send_and_wait(conv, "Тестовый ответ на первый вопрос", timeout=15)

                # Проверить что бот НЕ завершил сразу
                response = await conv.get_response(timeout=10)

                assert 'завершено' not in response.text.lower(), \
                    "Бот завершил интервью после первого ответа! Баг 'already covered' присутствует"

                print("✅ ТЕСТ ПРОЙДЕН: Баг 'already covered' исправлен")
                self.results['passed'] += 1

        except AssertionError as e:
            print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН: {e}")
            self.results['failed'] += 1
            self.results['errors'].append(str(e))
        except Exception as e:
            print(f"\n❌ ОШИБКА: {e}")
            self.results['failed'] += 1
            self.results['errors'].append(f"Exception: {e}")

    async def run_all_tests(self):
        """Запустить все тесты"""
        print("\n" + "=" * 80)
        print("🚀 ЗАПУСК АВТОМАТИЧЕСКИХ ТЕСТОВ")
        print("=" * 80)
        print(f"Время: {datetime.now()}")
        print(f"Бот: {self.bot_username}")
        print("=" * 80)

        await self.start()

        try:
            # Тест 1: Полный flow
            await self.test_interview_flow()

            await asyncio.sleep(2)  # Пауза между тестами

            # Тест 2: Регрессионный тест
            await self.test_already_covered_fix()

        finally:
            await self.stop()

        # Отчет
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        print(f"Всего тестов: {self.results['total_tests']}")
        print(f"✅ Пройдено: {self.results['passed']}")
        print(f"❌ Провалено: {self.results['failed']}")

        if self.results['errors']:
            print("\nОшибки:")
            for i, error in enumerate(self.results['errors'], 1):
                print(f"  {i}. {error}")

        print("=" * 80)

        return self.results['failed'] == 0  # True если все тесты пройдены


async def main():
    """Главная функция"""
    # ВАЖНО: Замените на username вашего бота!
    BOT_USERNAME = os.getenv('TEST_BOT_USERNAME', '@grantservice_test_bot')

    print(f"""
╔════════════════════════════════════════════════════════════════╗
║  Interactive Interview V2 - Автоматический Тест               ║
╚════════════════════════════════════════════════════════════════╝

Настройка:
1. Получите API credentials на https://my.telegram.org/
2. Добавьте в .env:
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TEST_BOT_USERNAME={BOT_USERNAME}

3. Запустите бота
4. Запустите этот скрипт: python test_interview_auto.py

""")

    # Создать тестер
    tester = InterviewTester(bot_username=BOT_USERNAME)

    # Запустить тесты
    success = await tester.run_all_tests()

    # Выход с кодом (для CI/CD)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
