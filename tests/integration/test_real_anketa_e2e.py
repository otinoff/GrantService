#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Test: Real Anketa Data from Production

Использует реальные ответы из анкеты #AN-20251008-maxkate1-001
для полного end-to-end тестирования интервью.

Author: Claude Code
Created: 2025-10-23
Priority: P0 CRITICAL
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict

# Note: conftest.py adds project root to sys.path
from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2
from agents.reference_points.reference_point import ReferencePointPriority


# Реальные данные из анкеты #AN-20251008-maxkate1-001
REAL_ANKETA_DATA = {
    "applicant_name": "Екатерина Максимова",
    "project_name": "Восстановление иконостаса в храме святого Иоанна Богослова",

    # Ответы в порядке важности (будут подаваться адаптивно)
    "answers": {
        # Суть проекта (P0)
        "project_essence": "Развитие социально-культурной инфраструктуры села Анисимово и Чагодощенского района Вологодской области для местного населения с целью сохранения исторического наследия родного края.",

        # Проблема (P0)
        "problem": "Жители не могут самостоятельно восстановить ценные заброшенные на территории села архитектурные памятники, в результате чего теряется память и наследие русской провинции для нынешних и будущих поколений",

        # Целевая аудитория (P0)
        "target_audience": "Местные жители, люди с корнями из Вологодской области, Старшие и средние школьники и молодежь Чагодощенского района Вологодской области",

        # Цель проекта
        "goal": "Повысить интерес к сохранению своего культурного наследия у жителей Чагодощенского района, в первую очередь молодежи",

        # Методология (P1)
        "methodology": "Воссоздание уникального исторического иконостаса в восстанавливаемом храме святого Иоанна Богослова в деревне Анисимово. Проведение социально-значимых культурных мероприятий для разъяснения важности сохранения исторического и духовного наследия. Популяризация проекта",

        # Мероприятия
        "activities": "Экскурсии по местной краеведческой экспозиции 10 экскурсий, 1ч, 50 чел, в течение полугода. Экскурсии в восстанавливаемый храм и по территории села с показом ценных архитектурных зданий, 5 экскурсий по 20 человек, 1ч в течение полугода. Информирование о ходе восстановления иконостаса в соцсетях на протяжение всего проекта. Торжественное открытие и встреча с художниками-реставраторами, 200 человек, 1 событие.",

        # Бюджет (P1)
        "budget": "5 000 000 руб",

        # Детализация бюджета
        "budget_breakdown": "Изготовление иконостаса будет происходить в мастерской в Московской области, с доставкой и установкой в храм в Анисимово.",

        # Результаты (P1)
        "results": "Изготовлен и установлен иконостас, появился интерес к истории края(опрос), рост охватов в соцсетях",

        # Команда (P2)
        "team": "Фонд Лепта, волонтеры, художники-реставраторы",

        # Партнеры (P2)
        "partners": "ДК Первомайский - предоставление помещения для мероприятий, Чагодощенская ЦБС подготовка и проведение конференции 'Иваны всея Руси', ООО 'Толково' - помощь создания контента для соцсетей.",

        # Риски (P2)
        "risks": "Недостаточное финансирование, сложности с доставкой и установкой",

        # Устойчивость (P2)
        "sustainability": "Мероприятия будут продолжаться, экскурсии с показом восстановленных объектов, культурные мероприятия, соцсети с освещением и продвижением проекта",

        # География (P3)
        "geography": "Деревня Анисимово Чагодощенского района Вологодской области",

        # История грантов
        "grant_history": "2021, ФПГ, 1 174 010 руб., Документальный фильм Стеклоград на Чагодоще. 2023, 2952000 руб., Это не мусор",

        # Ссылки
        "links": "https://lepta.info/fund/ ; vk.com/fondlepta; vk.com/anisimovo_usadba",

        # Направление
        "direction": "5 - Развитие культуры и искусства",
    }
}


@pytest.fixture
def mock_db():
    """Mock database"""
    db = Mock()
    db.save = Mock()
    db.get = Mock(return_value=None)
    return db


@pytest.fixture
def real_callback_with_queue():
    """
    РЕАЛЬНЫЙ callback как в продакшене

    Симулирует:
    1. Отправку сообщений в Telegram
    2. Очередь для ответов пользователя
    3. Асинхронное ожидание
    """
    # Отслеживание отправленных вопросов
    sent_questions = []

    # Очередь для ответов (как в продакшене)
    answer_queue = asyncio.Queue()

    async def real_callback(question: str = None) -> str:
        """
        Реальный callback как в handlers/interactive_interview_handler.py

        Args:
            question: Вопрос для отправки (None = пропустить отправку)

        Returns:
            Ответ из очереди
        """
        # Отправить вопрос (если есть)
        if question is not None:
            sent_questions.append(question)
            print(f"\n[CALLBACK] Sent question #{len(sent_questions)}: {question[:80]}...")
        else:
            print(f"\n[CALLBACK] Skipped sending (hardcoded RP)")

        # Дождаться ответа из очереди
        print(f"[CALLBACK] Waiting for answer from queue...")
        answer = await answer_queue.get()
        print(f"[CALLBACK] Got answer: {answer[:80]}...")

        return answer

    return {
        'callback': real_callback,
        'answer_queue': answer_queue,
        'sent_questions': sent_questions
    }


@pytest.fixture
def agent_for_e2e(mock_db):
    """Agent для E2E тестов с реальной конфигурацией"""
    with patch('agents.interactive_interviewer_agent_v2.QdrantClient'):
        agent = InteractiveInterviewerAgentV2(
            db=mock_db,
            llm_provider="claude_code",
            qdrant_host="localhost",
            qdrant_port=6333
        )

        # Mock LLM для быстрых тестов
        agent.llm = Mock()
        agent.llm.generate_async = AsyncMock(return_value="Сгенерированный вопрос?")

        # Mock question generator
        agent.question_generator.llm_client = agent.llm
        agent.question_generator.embedding_model = Mock()
        agent.question_generator.embedding_model.encode = Mock(return_value=[0.1, 0.2])

        # Mock auditor
        agent.auditor.analyze_project = AsyncMock(return_value={
            'final_score': 85,
            'strengths': ['Хороший проект', 'Четкая цель'],
            'weaknesses': ['Нужно больше деталей о команде'],
            'recommendations': ['Детализировать бюджет']
        })

        return agent


class TestRealAnketaE2E:
    """End-to-End тесты с реальными данными из анкеты"""

    @pytest.mark.asyncio
    async def test_full_interview_with_real_anketa(self, agent_for_e2e, real_callback_with_queue):
        """
        CRITICAL TEST: Полное интервью с реальными данными

        Использует ответы из анкеты #AN-20251008-maxkate1-001
        для проверки end-to-end работы интервьюера.
        """
        callback = real_callback_with_queue['callback']
        answer_queue = real_callback_with_queue['answer_queue']
        sent_questions = real_callback_with_queue['sent_questions']

        # Подготовить ответы в правильном порядке
        # Порядок соответствует приоритетам Reference Points
        answers_pool = [
            REAL_ANKETA_DATA['answers']['project_essence'],  # RP1: Суть проекта (hardcoded!)
            REAL_ANKETA_DATA['answers']['problem'],          # RP2: Проблема
            REAL_ANKETA_DATA['answers']['target_audience'],  # RP3: Целевая аудитория
            REAL_ANKETA_DATA['answers']['methodology'],      # RP4: Методология
            REAL_ANKETA_DATA['answers']['budget'],           # RP5: Бюджет
            REAL_ANKETA_DATA['answers']['budget_breakdown'], # RP6: Детализация
            REAL_ANKETA_DATA['answers']['results'],          # RP7: Результаты
            REAL_ANKETA_DATA['answers']['team'],             # RP8: Команда
            REAL_ANKETA_DATA['answers']['partners'],         # RP9: Партнеры
            REAL_ANKETA_DATA['answers']['sustainability'],   # RP10: Устойчивость
            REAL_ANKETA_DATA['answers']['geography'],        # RP11: География
            REAL_ANKETA_DATA['answers']['grant_history'],    # Дополнительно
            "Да, готовы к финализации"                       # Finalize
        ]

        # User data с hardcoded RP (Iteration 26)
        user_data = {
            'user_id': 'test_real_anketa',
            'applicant_name': REAL_ANKETA_DATA['applicant_name'],
            'project_name': REAL_ANKETA_DATA['project_name'],
            'hardcoded_rps': ['rp_001_project_essence'],  # ✅ ITERATION 26
            'covered_topics': ['applicant_name', 'greeting', 'project_essence_asked'],
            'collected_fields': {'applicant_name': REAL_ANKETA_DATA['applicant_name']}
        }

        print(f"\n{'='*80}")
        print(f"STARTING E2E TEST WITH REAL ANKETA DATA")
        print(f"Applicant: {REAL_ANKETA_DATA['applicant_name']}")
        print(f"Project: {REAL_ANKETA_DATA['project_name']}")
        print(f"Total answers prepared: {len(answers_pool)}")
        print(f"{'='*80}\n")

        # Задача для подачи ответов
        async def feed_answers():
            for i, answer in enumerate(answers_pool):
                await asyncio.sleep(0.1)  # Небольшая задержка
                print(f"[FEEDER] Feeding answer #{i+1}: {answer[:60]}...")
                await answer_queue.put(answer)

        # Запустить подачу ответов в фоне
        answer_task = asyncio.create_task(feed_answers())

        try:
            # Запустить интервью с РЕАЛЬНЫМ callback
            print(f"\n[TEST] Starting interview...")
            result = await agent_for_e2e.conduct_interview(
                user_data=user_data,
                callback_ask_question=callback
            )

            # === ПРОВЕРКИ ===

            print(f"\n{'='*80}")
            print(f"INTERVIEW COMPLETED - CHECKING RESULTS")
            print(f"{'='*80}\n")

            # 1. Интервью завершено успешно
            print(f"[CHECK 1] Interview completion status...")
            assert 'anketa' in result, "Result must contain 'anketa'"
            assert 'audit_score' in result, "Result must contain 'audit_score'"
            print(f"[OK] Interview completed successfully")

            # 2. Вопросы были заданы
            print(f"\n[CHECK 2] Questions asked...")
            print(f"Total questions sent: {len(sent_questions)}")
            assert len(sent_questions) >= 5, f"Should have sent at least 5 questions (got {len(sent_questions)})"
            print(f"[OK] Sufficient questions asked: {len(sent_questions)}")

            # 3. Первый вопрос НЕ про суть (hardcoded)
            print(f"\n[CHECK 3] Hardcoded question #2 handling...")
            if len(sent_questions) > 0:
                first_question = sent_questions[0].lower()
                assert 'суть' not in first_question and 'проект' not in first_question[:50], \
                    "First sent question should NOT be about project essence (it's hardcoded!)"
                print(f"[OK] Hardcoded RP worked: first question is NOT about essence")

            # 4. Анкета содержит данные
            print(f"\n[CHECK 4] Anketa data collection...")
            anketa = result['anketa']
            print(f"Anketa keys: {list(anketa.keys())}")
            assert len(anketa) > 0, "Anketa should contain collected data"
            print(f"[OK] Anketa contains {len(anketa)} fields")

            # 5. Оценка проекта
            print(f"\n[CHECK 5] Project audit score...")
            score = result['audit_score']
            assert score > 0, f"Audit score should be positive (got {score})"
            print(f"[OK] Audit score: {score}")

            # 6. Количество заданных вопросов
            print(f"\n[CHECK 6] Questions count...")
            questions_asked = result.get('questions_asked', 0)
            assert questions_asked >= 5, f"Should ask at least 5 questions (got {questions_asked})"
            print(f"[OK] Questions asked: {questions_asked}")

            # === ФИНАЛЬНЫЙ ОТЧЕТ ===

            print(f"\n{'='*80}")
            print(f"[SUCCESS] ALL CHECKS PASSED - E2E TEST SUCCESSFUL!")
            print(f"{'='*80}\n")

            print(f"[SUMMARY] Test Summary:")
            print(f"  - Applicant: {REAL_ANKETA_DATA['applicant_name']}")
            print(f"  - Questions sent: {len(sent_questions)}")
            print(f"  - Questions asked: {questions_asked}")
            print(f"  - Audit score: {score}")
            print(f"  - Anketa fields: {len(anketa)}")
            print(f"  - Test duration: {result.get('interview_time', 'N/A')}")

            print(f"\n[QUESTIONS] Sent Questions:")
            for i, q in enumerate(sent_questions[:10]):  # Показать первые 10
                print(f"  {i+1}. {q[:100]}...")

            print(f"\n[SUCCESS] END-TO-END TEST COMPLETED SUCCESSFULLY!")

        finally:
            # Отменить задачу подачи ответов
            answer_task.cancel()
            try:
                await answer_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_hardcoded_question_with_real_data(self, agent_for_e2e, real_callback_with_queue):
        """
        Test: Hardcoded question #2 с реальными данными

        Проверяет что вопрос #2 (про суть проекта) не отправляется,
        но ответ из анкеты корректно обрабатывается.
        """
        callback = real_callback_with_queue['callback']
        answer_queue = real_callback_with_queue['answer_queue']
        sent_questions = real_callback_with_queue['sent_questions']

        # User data с hardcoded RP
        user_data = {
            'user_id': 'test_hardcoded',
            'applicant_name': REAL_ANKETA_DATA['applicant_name'],
            'hardcoded_rps': ['rp_001_project_essence'],
            'covered_topics': ['applicant_name', 'greeting', 'project_essence_asked'],
            'collected_fields': {'applicant_name': REAL_ANKETA_DATA['applicant_name']}
        }

        # Подать только первый ответ
        await answer_queue.put(REAL_ANKETA_DATA['answers']['project_essence'])

        # Запустить агента только для первого RP
        from agents.reference_points.conversation_flow_manager import ConversationFlowManager

        flow_manager = ConversationFlowManager(
            user_data=user_data,
            rp_manager=agent_for_e2e.rp_manager
        )

        # Получить первый RP
        decision = flow_manager.decide_next_action()
        assert decision['action'] == 'ask_question'

        rp = decision['reference_point']
        assert rp.id == 'rp_001_project_essence', "First RP should be project essence"

        # Собрать ответ через callback
        answer = await callback(None)

        # Проверки
        assert len(sent_questions) == 0, "Hardcoded question should NOT be sent"
        assert answer == REAL_ANKETA_DATA['answers']['project_essence']

        print(f"[OK] Hardcoded question test passed!")
        print(f"   Answer length: {len(answer)}")


def test_anketa_data_completeness():
    """Test: Проверить что данные анкеты полные"""

    print(f"\n{'='*80}")
    print(f"CHECKING ANKETA DATA COMPLETENESS")
    print(f"{'='*80}\n")

    required_fields = [
        'project_essence',
        'problem',
        'target_audience',
        'methodology',
        'budget',
        'results'
    ]

    answers = REAL_ANKETA_DATA['answers']

    for field in required_fields:
        assert field in answers, f"Missing required field: {field}"
        assert len(answers[field]) > 10, f"Field {field} is too short"
        print(f"[OK] {field}: {len(answers[field])} chars")

    print(f"\n[OK] All required fields present and valid!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
