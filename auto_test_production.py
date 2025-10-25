#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛНОСТЬЮ АВТОМАТИЧЕСКИЙ ТЕСТ InteractiveInterviewer на ПРОДАКШЕНЕ

САМ:
1. Отправляет /start_interview
2. Отправляет /continue
3. Отправляет 15 ответов
4. Получает результаты из БД
5. Проверяет: вопросов >=10, оценка >0

НЕ ТРЕБУЕТ УЧАСТИЯ ЧЕЛОВЕКА!
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Установить DB env vars для продакшена
os.environ["DB_HOST"] = "5.35.88.251"
os.environ["DB_PORT"] = "5434"
os.environ["DB_NAME"] = "grantservice"
os.environ["DB_USER"] = "grantservice"
os.environ["DB_PASSWORD"] = "jPsGn%Nt%q#THnUB&&cqo*1Q"

# Telegram
from telegram import Bot
from telegram.error import TelegramError

# PRODUCTION Bot Token (from production server)
BOT_TOKEN = "7685915842:AAGcW0kgtljyIob8enM3zvFSLuZ-BZzcPOo"
TEST_USER_ID = 419597164  # Твой Telegram ID

# Ответы
ANSWERS = [
    "Лучные клубы в Кемерово для детей",
    "Развивать стрельбу из лука как спорт",
    "Мало доступных спортивных секций",
    "Дети и подростки 10-17 лет",
    "Кемерово, Кемеровская область",
    "Закупить оборудование и обучить тренеров",
    "Групповые тренировки 3 раза в неделю",
    "100 детей пройдут обучение",
    "500000 рублей",
    "Оборудование 300к, тренер 150к, аренда 50к",
    "Опытный тренер с 10-летним стажем",
    "Школа №5, спортивный комплекс Олимп",
    "Активная реклама и работа с родителями",
    "Абонплата от родителей и спонсоры",
    "12 месяцев реализации проекта",
]


async def main():
    print("="*80)
    print("АВТОМАТИЧЕСКИЙ ТЕСТ ПРОДАКШЕНА")
    print("="*80)
    print()

    if not BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN не найден в .env")
        return False

    bot = Bot(token=BOT_TOKEN)

    try:
        # 1. Проверка бота
        print("[1/6] Проверка подключения к боту...")
        me = await bot.get_me()
        print(f"[OK] Бот: @{me.username}")
        print()

        # 2. Старт интервью
        print("[2/6] Запуск интервью...")
        await bot.send_message(TEST_USER_ID, "/start_interview")
        print("[OK] /start_interview отправлено")
        await asyncio.sleep(2)

        await bot.send_message(TEST_USER_ID, "/continue")
        print("[OK] /continue отправлено")
        print()
        await asyncio.sleep(3)

        # 3. Отправка ответов
        print("[3/6] Отправка ответов...")
        start_time = time.time()

        for i, answer in enumerate(ANSWERS, 1):
            print(f"[{i:2d}/15] {answer[:50]}...")
            await bot.send_message(TEST_USER_ID, answer)
            await asyncio.sleep(1.5)  # Пауза между ответами

        print()
        print(f"[OK] Все 15 ответов отправлены за {time.time()-start_time:.1f}с")
        print()

        # 4. Ждём обработки
        print("[4/6] Ожидание финального аудита...")
        print("     (10-15 секунд)")
        await asyncio.sleep(12)
        print()

        # 5. Проверка результатов в БД
        print("[5/6] Проверка результатов в БД...")

        import psycopg2

        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"]
        )

        cursor = conn.cursor()

        # Получить последнюю анкету
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
        """, (TEST_USER_ID,))

        result = cursor.fetchone()

        if not result:
            print("[ERROR] Анкета не найдена в БД!")
            conn.close()
            return False

        app_id, score, status, created_at, data = result

        print(f"[OK] Анкета найдена!")
        print(f"     ID: {app_id}")
        print(f"     Создана: {created_at}")
        print(f"     Оценка: {score}/100")
        print(f"     Статус: {status}")
        print()

        # Подсчитать вопросы из dialogue_history
        import json
        anketa_data = json.loads(data) if isinstance(data, str) else data

        questions_asked = 0
        if 'dialogue_history' in anketa_data:
            questions_asked = len(anketa_data['dialogue_history'])

        print(f"     Вопросов задано: {questions_asked}")
        print()

        conn.close()

        # 6. Проверки
        print("[6/6] ФИНАЛЬНЫЕ ПРОВЕРКИ")
        print("="*80)
        print()

        checks = []

        # Check 1: >=10 вопросов
        check_questions = questions_asked >= 10
        checks.append(("Задано >=10 вопросов", check_questions, f"{questions_asked} вопросов"))

        # Check 2: Оценка >0
        check_score = score > 0
        checks.append(("Оценка >0", check_score, f"{score}/100"))

        # Check 3: Статус валидный
        check_status = status in ['EXCELLENT', 'GOOD', 'NEEDS_WORK', 'POOR']
        checks.append(("Статус валидный", check_status, status))

        # Вывод
        for name, passed, details in checks:
            status_icon = "[PASS]" if passed else "[FAIL]"
            print(f"{status_icon} {name}: {details}")

        print()
        print("="*80)

        all_passed = all(c[1] for c in checks)

        if all_passed:
            print("[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
            print()
            print("InteractiveInterviewer работает корректно:")
            print(f"  - Задал {questions_asked} вопросов (требовалось >=10)")
            print(f"  - Оценка: {score}/100")
            print(f"  - Статус: {status}")
            print()
            print("[READY] ГОТОВ К ИСПОЛЬЗОВАНИЮ НА ПРОДАКШЕНЕ!")
        else:
            print("[FAILED] НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
            print()
            print("Проблемы:")
            for name, passed, details in checks:
                if not passed:
                    print(f"  - {name}: {details}")
            print()
            print("[FIX NEEDED] Требуется исправление")

        print("="*80)

        return all_passed

    except TelegramError as e:
        print(f"[ERROR] Telegram ошибка: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(main())
    print()
    sys.exit(0 if success else 1)
