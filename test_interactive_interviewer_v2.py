#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script - Interactive Interviewer Agent V2 (Reference Points Framework)

Демонстрирует работу нового адаптивного интервьюера с Reference Points.

Author: Grant Service Architect Agent
Created: 2025-10-20
"""

import sys
import os
from pathlib import Path

# Path setup
_project_root = Path(__file__).parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "agents"))

import asyncio
import logging
from typing import Dict, Any

# Импорт компонентов Reference Points
from agents.reference_points import (
    ReferencePointManager,
    AdaptiveQuestionGenerator,
    ConversationFlowManager,
    UserExpertiseLevel,
    ProjectType
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """Mock LLM клиент для тестирования"""

    async def chat(self, messages, temperature=0.7):
        """Симуляция LLM ответа"""
        await asyncio.sleep(0.3)  # Имитация задержки

        # Извлечь user prompt
        user_msg = messages[-1]['content']

        # Простая логика генерации вопросов
        if 'проект' in user_msg.lower() and 'суть' in user_msg.lower():
            return "Расскажите, пожалуйста, что конкретно делает ваш проект?"

        elif 'проблем' in user_msg.lower():
            return "Какую социальную проблему решает ваш проект?"

        elif 'целевая аудитория' in user_msg.lower():
            return "Кто будет пользоваться результатами вашего проекта?"

        elif 'методолог' in user_msg.lower():
            return "Как вы планируете реализовать проект? Опишите конкретные шаги."

        elif 'бюджет' in user_msg.lower():
            if 'детализ' in user_msg.lower():
                return "Распределите бюджет по основным статьям расходов."
            else:
                return "Какой общий бюджет проекта вы планируете?"

        elif 'результат' in user_msg.lower():
            return "Какие конкретные измеримые результаты вы ожидаете получить?"

        elif 'команд' in user_msg.lower():
            return "Кто будет реализовывать проект? Расскажите о вашей команде."

        elif 'партнёр' in user_msg.lower():
            return "Есть ли у вас партнёры по проекту?"

        elif 'риск' in user_msg.lower():
            return "Какие риски вы видите и как планируете их снижать?"

        elif 'устойчивость' in user_msg.lower():
            return "Как проект будет существовать после окончания гранта?"

        else:
            return "Расскажите подробнее об этом аспекте проекта."


class MockUser:
    """Mock пользователь для тестирования"""

    def __init__(self):
        self.answers = [
            # Ответ 1: Суть проекта
            "Наш проект создаёт инклюзивные пространства для детей с ОВЗ (ограниченными возможностями здоровья). "
            "Мы хотим дать таким детям возможность развиваться вместе со сверстниками в комфортной среде.",

            # Ответ 2: Проблема
            "Основная проблема - отсутствие доступных инклюзивных пространств в нашем регионе. "
            "Дети с ОВЗ изолированы, не могут полноценно общаться и развиваться.",

            # Ответ 3: Целевая аудитория
            "Целевая аудитория - дети с ОВЗ в возрасте 7-14 лет и их семьи. "
            "Планируем охватить около 150 детей в год.",

            # Ответ 4: Методология
            "Мы создадим специализированный центр с адаптированным оборудованием, "
            "проведём обучение специалистов и запустим регулярные занятия по социализации.",

            # Ответ 5: Бюджет
            "Общий бюджет проекта - 1,500,000 рублей.",

            # Ответ 6: Детализация бюджета
            "Основные статьи: оборудование (600,000₽), зарплаты специалистов (500,000₽), "
            "аренда помещения (300,000₽), расходные материалы (100,000₽).",

            # Ответ 7: Результаты
            "Ожидаем: 150 детей пройдут программу, улучшение социальных навыков у 80% участников, "
            "создание постоянно действующего инклюзивного центра.",

            # Ответ 8: Команда
            "Команда: 2 психолога, 1 социальный педагог, 2 волонтёра. Опыт работы с детьми с ОВЗ - более 5 лет.",

            # Ответ 9: Партнёры
            "Партнёры: местная школа-интернат, родительская ассоциация, департамент образования.",

            # Ответ 10: Риски
            "Риски: низкая посещаемость (будем активно информировать), нехватка специалистов (создадим резерв), "
            "недофинансирование (ищем дополнительные источники)."
        ]
        self.answer_index = 0

    async def answer_question(self, question: str) -> str:
        """Ответить на вопрос"""
        await asyncio.sleep(0.2)  # Имитация времени на ответ

        if self.answer_index < len(self.answers):
            answer = self.answers[self.answer_index]
            self.answer_index += 1
        else:
            answer = "Да, всё верно. Больше добавить нечего."

        return answer


async def test_reference_points_framework():
    """
    Тест Reference Points Framework

    Демонстрирует:
    1. Инициализацию компонентов
    2. Адаптивную генерацию вопросов
    3. State machine диалога
    4. Прогресс и завершение
    """
    print("\n" + "=" * 80)
    print("ТЕСТ: REFERENCE POINTS FRAMEWORK")
    print("=" * 80 + "\n")

    # 1. Инициализация компонентов
    print("[1] Инициализация компонентов...\n")

    rp_manager = ReferencePointManager()
    rp_manager.load_fpg_reference_points()

    print(f"[OK] Loaded {len(rp_manager.reference_points)} Reference Points for FPG")

    # Список RP
    print("\n[LIST] Reference Points:")
    for rp_id, rp in rp_manager.reference_points.items():
        print(f"  - {rp.id}: {rp.name} [P{rp.priority.value}]")

    # Mock LLM и Question Generator
    llm = MockLLMClient()
    question_generator = AdaptiveQuestionGenerator(
        llm_client=llm,
        qdrant_client=None  # Without Qdrant in test
    )

    print("[OK] Adaptive Question Generator initialized")

    # Flow Manager
    flow_manager = ConversationFlowManager(rp_manager)

    print("[OK] Conversation Flow Manager initialized")

    # Mock пользователь
    user = MockUser()

    # 2. Симуляция интервью
    print("\n" + "=" * 80)
    print("[2] НАЧАЛО ИНТЕРВЬЮ")
    print("=" * 80 + "\n")

    turn = 1
    max_turns = 15

    while turn <= max_turns:
        print(f"\n{'-' * 80}")
        print(f"TURN {turn}")
        print(f"{'-' * 80}\n")

        # Определить следующее действие
        action = flow_manager.decide_next_action()

        print(f"[STATE] {flow_manager.context.current_state.value.upper()}")
        print(f"[TRANSITION] {action['transition'].value}")

        # Проверить финализацию
        if action['type'] == 'finalize':
            print(f"\n[SUCCESS] {action['message']}\n")
            break

        # Получить Reference Point
        rp = action['reference_point']
        print(f"[RP] Current: {rp.name} [P{rp.priority.value}]")

        # Показать прогресс (каждые 3 хода)
        if turn % 3 == 0:
            print(flow_manager.get_progress_message())

        # Сгенерировать вопрос
        context = {
            'collected_fields': {rp_id: rp.collected_data.get('text', '')
                               for rp_id, rp in rp_manager.reference_points.items()
                               if rp.collected_data},
            'covered_topics': flow_manager.context.covered_topics
        }

        question = await question_generator.generate_question(
            reference_point=rp,
            conversation_context=context,
            user_level=UserExpertiseLevel.INTERMEDIATE,
            project_type=ProjectType.SOCIAL
        )

        if not question:
            print("[SKIP] Already covered\n")
            turn += 1
            continue

        # Задать вопрос
        print(f"\n[BOT] {question}")

        # Получить ответ
        answer = await user.answer_question(question)
        print(f"[USER] {answer}\n")

        # Сохранить ход
        flow_manager.context.add_turn(
            question=question,
            answer=answer,
            rp_id=rp.id
        )

        # Обработать ответ
        action = flow_manager.decide_next_action(last_answer=answer)

        turn += 1

    # 3. Финальные результаты
    print("\n" + "=" * 80)
    print("[3] ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 80 + "\n")

    progress = rp_manager.get_progress()

    print("[PROGRESS] Overview:")
    print(f"  - Total RPs: {progress.total_rps}")
    print(f"  - Completed: {progress.completed_rps}")
    print(f"  - In Progress: {progress.in_progress_rps}")
    print(f"  - Not Started: {progress.not_started_rps}")
    print(f"  - Overall Completion: {progress.overall_completion:.1%}")
    print(f"  - Critical Completed: {'YES' if progress.critical_completed else 'NO'}")
    print(f"  - Important Completed: {'YES' if progress.important_completed else 'NO'}")

    print("\n[METRICS] Conversation:")
    print(f"  - Questions Asked: {flow_manager.context.questions_asked}")
    print(f"  - Follow-ups Asked: {flow_manager.context.follow_ups_asked}")
    print(f"  - Engagement Score: {flow_manager.context.user_engagement_score:.2f}")
    print(f"  - Conversation Quality: {flow_manager.context.conversation_quality:.2f}")

    print("\n[DATA] Collected:")
    for rp_id, rp in rp_manager.reference_points.items():
        if rp.is_complete():
            text = rp.collected_data.get('text', '')
            print(f"  [OK] {rp.name}: {text[:60]}...")

    # 4. Демонстрация state machine
    print("\n" + "=" * 80)
    print("[4] ИСТОРИЯ СОСТОЯНИЙ")
    print("=" * 80 + "\n")

    states_seen = set()
    for entry in flow_manager.context.dialogue_history:
        state = entry['state']
        if state not in states_seen:
            print(f"  {state.upper()}")
            states_seen.add(state)

    print("\n" + "=" * 80)
    print("[SUCCESS] TEST COMPLETED")
    print("=" * 80 + "\n")


async def test_adaptive_question_generation():
    """
    Тест адаптивной генерации вопросов

    Показывает как меняются вопросы в зависимости от контекста
    """
    print("\n" + "=" * 80)
    print("ТЕСТ: АДАПТИВНАЯ ГЕНЕРАЦИЯ ВОПРОСОВ")
    print("=" * 80 + "\n")

    # Инициализация
    llm = MockLLMClient()
    gen = AdaptiveQuestionGenerator(llm, qdrant_client=None)

    rp_manager = ReferencePointManager()
    rp_manager.load_fpg_reference_points()

    # Получить первый RP
    rp = rp_manager.get_next_reference_point()

    # Сценарий 1: Пустой контекст (начало интервью)
    print("[Сценарий 1] Пустой контекст - начало интервью\n")

    context1 = {
        'collected_fields': {},
        'covered_topics': []
    }

    q1 = await gen.generate_question(rp, context1)
    print(f"[BOT] Question: {q1}\n")

    # Сценарий 2: Уже есть информация о проекте
    print("[Scenario 2] Context with project info\n")

    context2 = {
        'collected_fields': {
            'project_essence': 'Inclusive center for children'
        },
        'covered_topics': ['project', 'children']
    }

    q2 = await gen.generate_question(rp, context2)
    print(f"[BOT] Question: {q2}\n")

    # Сценарий 3: Новичок vs Эксперт
    print("[Scenario 3] Novice vs Expert\n")

    rp_budget = rp_manager.get_reference_point('rp_005_budget')

    # Новичок
    print("  Level: NOVICE")
    q_novice = await gen.generate_question(
        rp_budget,
        context2,
        user_level=UserExpertiseLevel.NOVICE
    )
    print(f"  [BOT] Question: {q_novice}\n")

    # Эксперт
    print("  Level: EXPERT")
    q_expert = await gen.generate_question(
        rp_budget,
        context2,
        user_level=UserExpertiseLevel.EXPERT
    )
    print(f"  [BOT] Question: {q_expert}\n")

    print("=" * 80)
    print("[SUCCESS] TEST COMPLETED")
    print("=" * 80 + "\n")


async def main():
    """Главная функция - запустить все тесты"""
    print("\n" + "+" + "=" * 78 + "+")
    print("|" + " " * 15 + "REFERENCE POINTS FRAMEWORK - TESTS" + " " * 29 + "|")
    print("+" + "=" * 78 + "+\n")

    # Тест 1: Полный flow
    await test_reference_points_framework()

    # Разделитель
    print("\n" * 2)

    # Тест 2: Адаптивные вопросы
    await test_adaptive_question_generation()

    print("\n" + "+" + "=" * 78 + "+")
    print("|" + " " * 25 + "ALL TESTS COMPLETED" + " " * 34 + "|")
    print("+" + "=" * 78 + "+\n")


if __name__ == "__main__":
    asyncio.run(main())
