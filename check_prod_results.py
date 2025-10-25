#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка результатов InteractiveInterviewer на продакшене

Подключается к продакшн БД и показывает:
- Последние 10 анкет
- Сколько вопросов было задано
- Какие оценки получены
- Есть ли раннее завершение

НЕ ТРЕБУЕТ TELEGRAM!
"""

import os
import sys

# Установить env vars
os.environ["DB_HOST"] = "5.35.88.251"
os.environ["DB_PORT"] = "5434"
os.environ["DB_NAME"] = "grantservice"
os.environ["DB_USER"] = "grantservice"
os.environ["DB_PASSWORD"] = "jPsGn%Nt%q#THnUB&&cqo*1Q"

import psycopg2
import json
from datetime import datetime, timedelta


def check_production_results():
    """Проверить результаты на продакшене"""

    print("="*90)
    print("ПРОВЕРКА РЕЗУЛЬТАТОВ INTERACTIVEINTERVIEWER НА ПРОДАКШЕНЕ")
    print("="*90)
    print()

    try:
        # Подключение
        print("[1/3] Подключение к продакшн БД...")
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"]
        )
        print(f"[OK] Подключено к {os.environ['DB_HOST']}")
        print()

        cursor = conn.cursor()

        # Получить последние анкеты
        print("[2/3] Получение последних анкет...")
        cursor.execute("""
            SELECT
                id,
                telegram_id,
                audit_score,
                audit_status,
                created_at,
                data
            FROM applications
            ORDER BY created_at DESC
            LIMIT 20
        """)

        results = cursor.fetchall()

        if not results:
            print("[INFO] Нет анкет в БД")
            return False

        print(f"[OK] Найдено {len(results)} анкет")
        print()

        # Анализ результатов
        print("[3/3] АНАЛИЗ РЕЗУЛЬТАТОВ")
        print("="*90)
        print()

        # Фильтр: только последние 24 часа
        cutoff_time = datetime.now() - timedelta(hours=24)

        recent_count = 0
        early_termination_count = 0
        good_interviews = 0

        print(f"{'ID':<8} {'Дата':<20} {'User':<12} {'Оценка':<10} {'Статус':<12} {'Вопросов'}")
        print("-"*90)

        for row in results:
            app_id, telegram_id, score, status, created_at, data = row

            # Подсчитать вопросы
            questions_asked = 0
            try:
                anketa_data = json.loads(data) if isinstance(data, str) else data
                if 'dialogue_history' in anketa_data:
                    questions_asked = len(anketa_data['dialogue_history'])
            except:
                pass

            # Только свежие
            if created_at < cutoff_time:
                continue

            recent_count += 1

            # Проверка на раннее завершение
            early_term = questions_asked < 10

            if early_term:
                early_termination_count += 1
                marker = "[EARLY!]"
            else:
                good_interviews += 1
                marker = "[OK]   "

            print(f"{app_id:<8} {str(created_at):<20} {telegram_id:<12} {score:<10} {status:<12} {questions_asked:>3} {marker}")

        print("-"*90)
        print()

        # Статистика
        print("СТАТИСТИКА (последние 24 часа):")
        print(f"  Всего анкет: {recent_count}")
        print(f"  С ранним завершением (<10 вопросов): {early_termination_count}")
        print(f"  Полноценных интервью (>=10 вопросов): {good_interviews}")
        print()

        if recent_count > 0:
            success_rate = (good_interviews / recent_count) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
            print()

        # Проверка исправления
        print("ПРОВЕРКА ИСПРАВЛЕНИЯ (commit 64fe88b):")
        print()

        if early_termination_count > 0:
            print("[WARNING] Обнаружены случаи раннего завершения!")
            print(f"          {early_termination_count} анкет с <10 вопросов")
            print()
            print("ВОЗМОЖНЫЕ ПРИЧИНЫ:")
            print("  1. Деплой ещё не завершился (подожди 5-10 минут)")
            print("  2. Это старые анкеты (до исправления)")
            print("  3. Проблема не полностью исправлена")
        else:
            print("[SUCCESS] Нет случаев раннего завершения!")
            print("          Все анкеты с >=10 вопросов")
            print()
            print("ИСПРАВЛЕНИЕ РАБОТАЕТ КОРРЕКТНО!")

        print()
        print("="*90)

        conn.close()

        return early_termination_count == 0

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = check_production_results()
    print()

    if success:
        print("[RESULT] InteractiveInterviewer работает корректно на продакшене!")
    else:
        print("[RESULT] Требуется дополнительная проверка")

    print()
    sys.exit(0 if success else 1)
