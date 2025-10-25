#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автономный тест InteractiveInterviewer через Telegram Bot

Полностью автоматический:
1. Запускает тестового бота локально (фоновый процесс)
2. Подключается как пользователь
3. Проходит интервью автоматически
4. Проверяет результаты
5. Останавливает бота
6. Показывает отчёт

НЕ ТРЕБУЕТ УЧАСТИЯ ПОЛЬЗОВАТЕЛЯ!

Usage:
    python test_bot_autonomous.py
"""

import asyncio
import sys
import subprocess
import time
import os
from pathlib import Path
from telegram import Bot
from telegram.ext import Application

# Add project paths
_project_root = Path(__file__).parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "data" / "database"))

from data.database.models import GrantServiceDatabase


# Симулированные ответы (те же что в automated тесте)
SIMULATED_ANSWERS = [
    "Лучные клубы в Кемерово для детей и подростков",
    "Хотим развивать стрельбу из лука как вид спорта, проводить соревнования",
    "В Кемерово мало доступных спортивных секций для детей, особенно по стрельбе из лука",
    "Дети и подростки 10-17 лет, их родители",
    "Кемерово, Кемеровская область",
    "Закупить оборудование, обучить тренеров, провести 3 соревнования",
    "Групповые тренировки 3 раза в неделю, соревнования раз в квартал",
    "100 детей пройдут обучение, 3 соревнования с участием 200+ человек",
    "500,000 рублей",
    "Оборудование 300к, зарплата тренера 150к, аренда зала 50к",
    "Опытный тренер с 10-летним стажем, волонтеры-помощники",
    "Школа №5, спортивный комплекс 'Олимп'",
    "Недостаток оборудования - закупим запас, низкая посещаемость - активная реклама",
    "Родители будут оплачивать символическую абонплату, спонсорская поддержка",
    "12 месяцев",
    "Да, уже есть зал в школе №5, договорились с директором",
    "Будут как новички, так и дети с опытом в других видах спорта",
    "Планируем начать в сентябре 2025",
    "Тренер сертифицирован федерацией стрельбы из лука",
    "Родители очень заинтересованы, провели опрос - 80+ заявок"
]


class AutonomousBotTester:
    """Автономный тестер бота"""

    def __init__(self, bot_token: str, test_chat_id: int):
        """
        Args:
            bot_token: Telegram Bot токен
            test_chat_id: ID чата для тестирования (твой Telegram ID)
        """
        self.bot_token = bot_token
        self.test_chat_id = test_chat_id
        self.bot_process = None
        self.bot = None
        self.db = None

    async def start_bot_background(self):
        """Запустить бота в фоновом процессе"""
        print("\n[1/6] Запуск тестового бота в фоне...")

        # Запускаем telegram-bot/main.py как subprocess
        bot_script = _project_root / "telegram-bot" / "main.py"

        self.bot_process = subprocess.Popen(
            [sys.executable, str(bot_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(_project_root / "telegram-bot"),
            text=True
        )

        # Ждём запуска
        print("   Ожидание запуска бота (5 сек)...")
        await asyncio.sleep(5)

        if self.bot_process.poll() is not None:
            # Процесс завершился - ошибка
            stdout, stderr = self.bot_process.communicate()
            print(f"   ❌ Бот не запустился!")
            print(f"   STDOUT: {stdout}")
            print(f"   STDERR: {stderr}")
            return False

        print("   ✅ Бот запущен в фоне (PID: {})".format(self.bot_process.pid))
        return True

    async def init_bot_client(self):
        """Инициализировать клиент для отправки сообщений"""
        print("\n[2/6] Инициализация клиента...")

        self.bot = Bot(token=self.bot_token)

        # Проверка подключения
        try:
            me = await self.bot.get_me()
            print(f"   ✅ Подключён к боту: @{me.username}")
            return True
        except Exception as e:
            print(f"   ❌ Ошибка подключения: {e}")
            return False

    async def send_message(self, text: str):
        """Отправить сообщение боту"""
        await self.bot.send_message(chat_id=self.test_chat_id, text=text)
        await asyncio.sleep(0.5)  # Задержка для обработки

    async def run_interview(self):
        """Пройти интервью автоматически"""
        print("\n[3/6] Прохождение интервью...")

        # Старт интервью
        print("   Отправка /start_interview...")
        await self.send_message("/start_interview")
        await asyncio.sleep(2)

        # Начать интервью
        print("   Отправка /continue...")
        await self.send_message("/continue")
        await asyncio.sleep(2)

        # Отправить ответы
        for i, answer in enumerate(SIMULATED_ANSWERS, 1):
            print(f"   Ответ {i}/20: {answer[:50]}...")
            await self.send_message(answer)
            await asyncio.sleep(1.5)  # Задержка между ответами

        print("   ✅ Все ответы отправлены")

        # Дать время на обработку финального аудита
        print("   Ожидание финального аудита (10 сек)...")
        await asyncio.sleep(10)

    async def check_results(self):
        """Проверить результаты в БД"""
        print("\n[4/6] Проверка результатов...")

        self.db = GrantServiceDatabase()

        # Получить последнюю анкету для тестового пользователя
        with self.db.connect() as conn:
            cursor = conn.cursor()

            # Найти последнюю анкету
            cursor.execute("""
                SELECT
                    id,
                    audit_score,
                    audit_status,
                    created_at,
                    data
                FROM applications
                WHERE telegram_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (self.test_chat_id,))

            result = cursor.fetchone()

            if not result:
                print("   ❌ Анкета не найдена в БД!")
                return None

            app_id, score, status, created_at, data = result

            print(f"   ✅ Анкета найдена!")
            print(f"      ID: {app_id}")
            print(f"      Оценка: {score}/100")
            print(f"      Статус: {status}")
            print(f"      Создана: {created_at}")

            # Подсчитать вопросы
            import json
            anketa_data = json.loads(data) if isinstance(data, str) else data

            # Поискать информацию о вопросах в разных местах
            questions_asked = 0

            # Попробуем найти в dialogue_history
            if 'dialogue_history' in anketa_data:
                questions_asked = len(anketa_data['dialogue_history'])

            print(f"      Вопросов задано: {questions_asked}")

            return {
                'id': app_id,
                'score': score,
                'status': status,
                'questions_asked': questions_asked,
                'created_at': created_at
            }

    async def validate_results(self, results: dict):
        """Валидация результатов"""
        print("\n[5/6] Валидация результатов...")

        checks = []

        # Check 1: Анкета создана
        has_anketa = results is not None
        checks.append(('Анкета создана', has_anketa))

        if not has_anketa:
            print("   ❌ Анкета не создана - остальные проверки невозможны")
            return False

        # Check 2: Оценка > 0
        has_score = results['score'] > 0
        checks.append(('Оценка > 0', has_score))

        # Check 3: Минимум вопросов (наше исправление!)
        min_questions = results['questions_asked'] >= 10
        checks.append(('Задано ≥10 вопросов', min_questions))

        # Check 4: Статус валидный
        valid_status = results['status'] in ['PENDING', 'EXCELLENT', 'GOOD', 'NEEDS_WORK', 'POOR']
        checks.append(('Статус валидный', valid_status))

        # Вывод
        for check_name, passed in checks:
            status = '✅' if passed else '❌'
            print(f"   {status} {check_name}")

        all_passed = all(check[1] for check in checks)

        return all_passed

    async def stop_bot(self):
        """Остановить бота"""
        print("\n[6/6] Остановка бота...")

        if self.bot_process:
            self.bot_process.terminate()

            # Ждём завершения
            try:
                self.bot_process.wait(timeout=5)
                print("   ✅ Бот остановлен")
            except subprocess.TimeoutExpired:
                print("   ⚠️  Бот не остановился, принудительное завершение...")
                self.bot_process.kill()
                print("   ✅ Бот убит")

    async def run_full_test(self):
        """Запустить полный тестовый цикл"""
        print("="*80)
        print("АВТОНОМНЫЙ ТЕСТ TELEGRAM BOT + INTERACTIVEinterviewer")
        print("="*80)

        success = False

        try:
            # 1. Запустить бота
            if not await self.start_bot_background():
                return False

            # 2. Инициализировать клиент
            if not await self.init_bot_client():
                return False

            # 3. Пройти интервью
            await self.run_interview()

            # 4. Проверить результаты
            results = await self.check_results()

            # 5. Валидация
            if results:
                success = await self.validate_results(results)

        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # 6. Всегда останавливаем бота
            await self.stop_bot()

        # Финальный отчёт
        print("\n" + "="*80)
        print("ФИНАЛЬНЫЙ ОТЧЁТ")
        print("="*80)

        if success:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
            print("\n✅ InteractiveInterviewer работает корректно:")
            print("   - Задаёт ≥10 вопросов")
            print("   - Создаёт анкету с оценкой > 0")
            print("   - Сохраняет в БД")
            print("\n🚀 ГОТОВ К ДЕПЛОЮ НА ПРОДАКШЕН!")
        else:
            print("❌ ТЕСТЫ ПРОВАЛЕНЫ!")
            print("\n⚠️  Проблемы обнаружены, исправь перед деплоем на продакшен")

        print("="*80)

        return success


async def main():
    """Main entry point"""

    # Загрузить токен из .env
    from dotenv import load_dotenv
    load_dotenv(_project_root / "config" / ".env")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    test_chat_id = int(os.getenv("TEST_CHAT_ID", "0"))  # Добавь свой ID в .env

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в config/.env")
        return False

    if test_chat_id == 0:
        print("❌ TEST_CHAT_ID не найден в config/.env")
        print("   Добавь свой Telegram ID в config/.env:")
        print("   TEST_CHAT_ID=твой_telegram_id")
        return False

    tester = AutonomousBotTester(bot_token, test_chat_id)
    return await tester.run_full_test()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
