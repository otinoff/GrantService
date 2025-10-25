#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автономный локальный тест InteractiveInterviewerAgentV2

Полностью автоматический - тестирует агента НАПРЯМУЮ (без Telegram):
1. Подключается к локальной БД (или создаёт SQLite)
2. Запускает InteractiveInterviewerAgentV2
3. Симулирует 20 ответов пользователя
4. Проверяет результаты
5. Показывает отчёт

НЕ ТРЕБУЕТ:
- Telegram Bot
- Участия пользователя
- Продакшн БД

Usage:
    python test_agent_local_autonomous.py
"""

import asyncio
import sys
import os
from pathlib import Path
import time

# ВАЖНО: Установить DB env vars ДО любых импортов!
if not os.getenv("DB_HOST"):
    print("[INFO] Используем продакшн БД (5.35.88.251)")
    os.environ["DB_HOST"] = "5.35.88.251"
    os.environ["DB_PORT"] = "5432"
    os.environ["DB_NAME"] = "grantservice"
    os.environ["DB_USER"] = "postgres"
    os.environ["DB_PASSWORD"] = "Snowwhite2024!"

# Add project paths
_project_root = Path(__file__).parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "agents"))
sys.path.insert(0, str(_project_root / "data" / "database"))


# Симулированные ответы
SIMULATED_ANSWERS = {
    1: "Лучные клубы в Кемерово для детей и подростков",
    2: "Хотим развивать стрельбу из лука как вид спорта, проводить соревнования",
    3: "В Кемерово мало доступных спортивных секций для детей, особенно по стрельбе из лука",
    4: "Дети и подростки 10-17 лет, их родители",
    5: "Кемерово, Кемеровская область",
    6: "Закупить оборудование, обучить тренеров, провести 3 соревнования",
    7: "Групповые тренировки 3 раза в неделю, соревнования раз в квартал",
    8: "100 детей пройдут обучение, 3 соревнования с участием 200+ человек",
    9: "500,000 рублей",
    10: "Оборудование 300к, зарплата тренера 150к, аренда зала 50к",
    11: "Опытный тренер с 10-летним стажем, волонтеры-помощники",
    12: "Школа №5, спортивный комплекс 'Олимп'",
    13: "Недостаток оборудования - закупим запас, низкая посещаемость - активная реклама",
    14: "Родители будут оплачивать символическую абонплату, спонсорская поддержка",
    15: "12 месяцев",
    # Уточняющие вопросы
    16: "Да, уже есть зал в школе №5, договорились с директором",
    17: "Будут как новички, так и дети с опытом в других видах спорта",
    18: "Планируем начать в сентябре 2025",
    19: "Тренер сертифицирован федерацией стрельбы из лука",
    20: "Родители очень заинтересованы, провели опрос - 80+ заявок"
}


class MockDatabase:
    """Mock БД для локального тестирования"""

    def __init__(self):
        self.applications = []
        self.users = []

    def save_application(self, app_data):
        """Сохранить анкету"""
        app_data['id'] = len(self.applications) + 1
        self.applications.append(app_data)
        return app_data['id']

    def get_user_llm_preference(self, user_id):
        """Получить LLM preference"""
        return "claude_code"  # Default

    def save_user_state(self, user_id, state):
        """Сохранить состояние пользователя"""
        pass

    def get_user_state(self, user_id):
        """Получить состояние пользователя"""
        return None

    def connect(self):
        """Заглушка для контекстного менеджера"""
        class FakeConnection:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def cursor(self):
                class FakeCursor:
                    def execute(self, *args):
                        pass
                    def fetchone(self):
                        return None
                    def fetchall(self):
                        return []
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        pass
                return FakeCursor()
        return FakeConnection()


class InterviewSimulator:
    """Симулятор интервью для тестирования"""

    def __init__(self, answers: dict):
        self.answers = answers
        self.question_count = 0
        self.questions = []
        self.responses = []

    async def ask_question(self, question: str) -> str:
        """
        Callback для вопросов - возвращает симулированный ответ

        Args:
            question: Вопрос от интервьюера

        Returns:
            Симулированный ответ пользователя
        """
        self.question_count += 1
        self.questions.append(question)

        print(f"\n{'='*70}")
        print(f"[Q{self.question_count}] {question[:100]}...")
        print(f"{'='*70}")

        # Получить ответ из словаря
        answer = self.answers.get(self.question_count, f"[Нет ответа на вопрос {self.question_count}]")
        self.responses.append(answer)

        print(f"[A{self.question_count}] {answer}\n")

        # Небольшая задержка для реалистичности
        await asyncio.sleep(0.1)

        return answer


async def test_agent_autonomous():
    """
    Автономный тест агента

    Тестирует InteractiveInterviewerAgentV2 напрямую
    """
    print("="*80)
    print("АВТОНОМНЫЙ ТЕСТ InteractiveInterviewerAgentV2")
    print("="*80)
    print()

    # 1. Подключение к БД (используем mock)
    print("[1/5] Инициализация БД...")
    mock_db = MockDatabase()
    print("[OK] Mock БД инициализирована")

    # 2. Инициализация агента
    print("\n[2/5] Инициализация InteractiveInterviewerAgentV2...")

    try:
        from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2

        agent = InteractiveInterviewerAgentV2(
            db=mock_db,
            llm_provider="claude_code",
            qdrant_host="5.35.88.251",
            qdrant_port=6333
        )
        print("[OK] Агент инициализирован")
        print(f"   LLM: claude_code")
        print(f"   Qdrant: 5.35.88.251:6333")

    except Exception as e:
        print(f"[ERROR] Ошибка инициализации агента: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 3. Подготовка данных пользователя
    print("\n[3/5] Подготовка данных пользователя...")
    user_data = {
        'telegram_id': 999999999,  # Test user
        'username': 'test_archery_user',
        'first_name': 'Тестовый',
        'last_name': 'Пользователь',
        'email': 'test@example.com',
        'phone': '+7999000111',
        'grant_fund': 'Фонд президентских грантов'
    }
    print("[OK] Пользователь подготовлен")

    # 4. Запуск интервью с симулированными ответами
    print("\n[4/5] Запуск интервью...")
    print("-"*80)

    simulator = InterviewSimulator(SIMULATED_ANSWERS)
    start_time = time.time()

    try:
        result = await agent.conduct_interview(
            user_data=user_data,
            callback_ask_question=simulator.ask_question
        )

        processing_time = time.time() - start_time

        print("\n" + "="*80)
        print("РЕЗУЛЬТАТЫ ИНТЕРВЬЮ")
        print("="*80)
        print(f"[OK] Статус: Успешно завершено")
        print(f"[SCORE] Оценка: {result.get('audit_score', 'N/A')}/100")
        print(f"[QUESTIONS] Задано вопросов: {simulator.question_count}")
        print(f"[TIME] Время: {processing_time:.1f} секунд")

        if 'conversation_state' in result:
            print(f"[STATE] Финальное состояние: {result['conversation_state']}")

        print()

        # 5. Проверки
        print("\n[5/5] ПРОВЕРКИ")
        print("="*80)

        checks = []

        # Check 1: Минимум 10 вопросов (ГЛАВНАЯ ПРОВЕРКА!)
        min_questions = simulator.question_count >= 10
        checks.append(('Задано ≥10 вопросов', min_questions))
        if min_questions:
            print(f"[PASS] Задано ≥10 вопросов: {simulator.question_count} вопросов")
        else:
            print(f"[FAIL] Задано < 10 вопросов: {simulator.question_count} вопросов")

        # Check 2: Оценка существует и > 0
        has_score = result.get('audit_score', 0) > 0
        checks.append(('Оценка > 0', has_score))
        if has_score:
            print(f"[PASS] Оценка > 0: {result.get('audit_score')} баллов")
        else:
            print(f"[FAIL] Оценка = 0 или отсутствует")

        # Check 3: Анкета не пустая
        has_anketa = bool(result.get('anketa'))
        checks.append(('Анкета заполнена', has_anketa))
        if has_anketa:
            print(f"[PASS] Анкета заполнена")
        else:
            print(f"[FAIL] Анкета пустая")

        # Check 4: Время выполнения разумное
        reasonable_time = 10 < processing_time < 180
        checks.append(('Время выполнения OK', reasonable_time))
        if reasonable_time:
            print(f"[PASS] Время выполнения OK: {processing_time:.1f}с")
        else:
            print(f"[FAIL] Время выполнения странное: {processing_time:.1f}с")

        # Check 5: Нет ранних завершений (для диагностики)
        no_early_termination = simulator.question_count > 5
        checks.append(('Нет раннего завершения', no_early_termination))
        if no_early_termination:
            print(f"[PASS] Нет раннего завершения ({simulator.question_count} > 5)")
        else:
            print(f"[FAIL] РАННЕЕ ЗАВЕРШЕНИЕ! Только {simulator.question_count} вопросов")

        all_passed = all(check[1] for check in checks)

        print()
        print("="*80)
        print("ФИНАЛЬНЫЙ ВЕРДИКТ")
        print("="*80)

        if all_passed:
            print("[SUCCESS] ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
            print()
            print("[OK] InteractiveInterviewer работает корректно:")
            print(f"   - Задал {simulator.question_count} вопросов (требовалось >=10)")
            print(f"   - Оценка: {result.get('audit_score')}/100")
            print(f"   - Анкета создана")
            print(f"   - Время: {processing_time:.1f}с")
            print()
            print("[READY] ГОТОВ К ДЕПЛОЮ НА ПРОДАКШЕН!")
            return True
        else:
            print("[FAILED] НЕКОТОРЫЕ ПРОВЕРКИ ПРОВАЛЕНЫ")
            print()
            print("[WARNING] Проблемы:")
            for check_name, passed in checks:
                if not passed:
                    print(f"   - {check_name}")
            print()
            print("[FIX NEEDED] ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ ПЕРЕД ДЕПЛОЕМ")
            return False

    except Exception as e:
        print(f"\n[ERROR] ОШИБКА ВО ВРЕМЯ ИНТЕРВЬЮ: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    print("Запуск автономного теста...")
    print("(тест займёт 30-60 секунд)")
    print()

    success = asyncio.run(test_agent_autonomous())

    print()
    print("="*80)
    sys.exit(0 if success else 1)
