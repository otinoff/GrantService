#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматизированный тест InteractiveInterviewerAgentV2

НЕ ТРЕБУЕТ TELEGRAM UI!

Симулирует реальный диалог с пользователем для тестирования логики интервью.

Usage:
    python test_interactive_interviewer_automated.py
"""

import asyncio
import sys
from pathlib import Path

# Add project paths
_project_root = Path(__file__).parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "agents"))

from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2
from data.database.models import GrantServiceDatabase


# Симулированные ответы пользователя
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


class InterviewSimulator:
    """Симулятор интервью для тестирования"""

    def __init__(self, answers: dict):
        self.answers = answers
        self.question_count = 0

    async def ask_question(self, question: str) -> str:
        """
        Callback для вопросов - возвращает симулированный ответ

        Args:
            question: Вопрос от интервьюера

        Returns:
            Симулированный ответ пользователя
        """
        self.question_count += 1

        print(f"\n{'='*70}")
        print(f"[Q{self.question_count}] {question}")
        print(f"{'='*70}")

        # Получить ответ из словаря
        answer = self.answers.get(self.question_count, f"[Нет ответа на вопрос {self.question_count}]")

        print(f"[A{self.question_count}] {answer}\n")

        # Небольшая задержка для реалистичности
        await asyncio.sleep(0.1)

        return answer


async def test_interview_automated():
    """
    Автоматизированный тест интервью

    Симулирует полный диалог без Telegram UI
    """
    print("="*80)
    print("АВТОМАТИЗИРОВАННЫЙ ТЕСТ InteractiveInterviewerAgentV2")
    print("="*80)
    print()

    # 1. Подключение к БД
    print("[1/4] Подключение к БД...")
    db = GrantServiceDatabase()
    print("✅ БД подключена")

    # 2. Инициализация агента
    print("\n[2/4] Инициализация InteractiveInterviewerAgentV2...")
    agent = InteractiveInterviewerAgentV2(
        db=db,
        llm_provider="claude_code",
        qdrant_host="5.35.88.251",
        qdrant_port=6333
    )
    print("✅ Агент инициализирован")

    # 3. Подготовка данных пользователя
    print("\n[3/4] Подготовка данных пользователя...")
    user_data = {
        'telegram_id': 999999999,  # Test user
        'username': 'test_archery_user',
        'first_name': 'Тестовый',
        'last_name': 'Пользователь',
        'email': 'test@example.com',
        'phone': '+7999000111',
        'grant_fund': 'Фонд президентских грантов'
    }
    print("✅ Пользователь подготовлен")

    # 4. Запуск интервью с симулированными ответами
    print("\n[4/4] Запуск интервью...")
    print("-"*80)

    simulator = InterviewSimulator(SIMULATED_ANSWERS)

    try:
        result = await agent.conduct_interview(
            user_data=user_data,
            callback_ask_question=simulator.ask_question
        )

        print("\n" + "="*80)
        print("РЕЗУЛЬТАТЫ ИНТЕРВЬЮ")
        print("="*80)
        print(f"✅ Статус: Успешно завершено")
        print(f"📊 Оценка: {result['audit_score']}/100")
        print(f"❓ Задано вопросов: {result['questions_asked']}")
        print(f"🔍 Уточняющих вопросов: {result['follow_ups_asked']}")
        print(f"⏱️  Время: {result['processing_time']:.1f} секунд")
        print(f"🎯 Финальное состояние: {result['conversation_state']}")
        print()

        # Детали аудита
        if 'audit_details' in result:
            audit = result['audit_details']
            print("📋 Детали аудита:")
            print(f"   - Итоговая оценка: {audit.get('final_score', 'N/A')}/100")
            print(f"   - Статус готовности: {audit.get('readiness_status', 'N/A')}")

        # Проверки
        print("\n" + "="*80)
        print("ПРОВЕРКИ")
        print("="*80)

        checks = []

        # Check 1: Минимум 10 вопросов
        min_questions = result['questions_asked'] >= 10
        checks.append(('Задано ≥10 вопросов', min_questions))

        # Check 2: Оценка > 0
        has_score = result['audit_score'] > 0
        checks.append(('Оценка > 0', has_score))

        # Check 3: Анкета не пустая
        has_anketa = bool(result.get('anketa'))
        checks.append(('Анкета заполнена', has_anketa))

        # Check 4: Время выполнения разумное
        reasonable_time = 10 < result['processing_time'] < 120
        checks.append(('Время выполнения OK', reasonable_time))

        for check_name, passed in checks:
            status = '✅' if passed else '❌'
            print(f"{status} {check_name}")

        all_passed = all(check[1] for check in checks)

        print()
        if all_passed:
            print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
            return True
        else:
            print("⚠️  НЕКОТОРЫЕ ПРОВЕРКИ ПРОВАЛЕНЫ")
            return False

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_interview_automated())

    sys.exit(0 if success else 1)
