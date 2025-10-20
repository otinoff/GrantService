#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Interactive Interview - Step-by-step версия для Telegram Bot

Адаптированная версия Reference Points Framework для работы
в Telegram Bot с событийной моделью (event-driven).

Author: Grant Service Architect Agent
Created: 2025-10-20
Version: 2.0
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

# Setup paths
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))

from agents.reference_points import (
    ReferencePointManager,
    ReferencePointState,
    AdaptiveQuestionGenerator,
    ConversationFlowManager,
    ConversationState,
    UserExpertiseLevel,
    ProjectType
)

logger = logging.getLogger(__name__)


class TelegramInteractiveInterview:
    """
    Step-by-step интервью для Telegram Bot

    Работает по принципу:
    1. get_next_question() - получить следующий вопрос
    2. process_answer(answer) - обработать ответ
    3. is_complete() - проверить завершенность
    4. get_results() - получить результаты

    Example:
        >>> interview = TelegramInteractiveInterview(db, user_data)
        >>> question = await interview.get_next_question()
        >>> # Отправить вопрос пользователю через Telegram
        >>> # Получить ответ от пользователя
        >>> await interview.process_answer(answer)
        >>> if interview.is_complete():
        ...     results = interview.get_results()
    """

    def __init__(
        self,
        db,
        user_data: Dict[str, Any],
        llm_provider: str = "claude_code",
        qdrant_host: str = "5.35.88.251",
        qdrant_port: int = 6333
    ):
        """
        Инициализация интервью

        Args:
            db: Database instance
            user_data: Данные пользователя
            llm_provider: LLM провайдер
            qdrant_host: Qdrant хост
            qdrant_port: Qdrant порт
        """
        self.db = db
        self.user_data = user_data
        self.llm_provider = llm_provider

        # Reference Points Framework
        self.rp_manager = ReferencePointManager()
        self.rp_manager.load_fpg_reference_points()

        self.flow_manager = ConversationFlowManager(self.rp_manager)

        # Qdrant
        self.qdrant = None
        try:
            from qdrant_client import QdrantClient
            self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=10)
            logger.info(f"[OK] Qdrant connected: {qdrant_host}:{qdrant_port}")
        except Exception as e:
            logger.warning(f"[WARN] Qdrant unavailable: {e}")

        # Question Generator
        self.question_generator = None
        self._init_question_generator()

        # Состояние
        self.current_question = None
        self.current_rp = None
        self.last_answer = None
        self.started_at = datetime.now()

        # Принудительно перевести в EXPLORING state
        self.flow_manager.context.current_state = ConversationState.EXPLORING

        logger.info(f"[INIT] Telegram Interview for user {user_data.get('telegram_id')}")

    def _init_question_generator(self):
        """Инициализировать генератор вопросов"""
        try:
            from llm.unified_llm_client import UnifiedLLMClient
            from llm.config import AGENT_CONFIGS

            config = AGENT_CONFIGS.get("interviewer", {})

            llm = UnifiedLLMClient(
                provider=self.llm_provider,
                model=config.get("model"),
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 2000)
            )

            self.question_generator = AdaptiveQuestionGenerator(
                llm_client=llm,
                qdrant_client=self.qdrant,
                qdrant_collection="knowledge_sections"
            )

            logger.info("[OK] Question generator initialized")

        except Exception as e:
            logger.error(f"[ERROR] Failed to init question generator: {e}")
            self.question_generator = None

    async def get_next_question(self) -> Optional[str]:
        """
        Получить следующий вопрос для пользователя

        Returns:
            Вопрос или None если интервью завершено
        """
        # Цикл для обработки skip вопросов
        max_iterations = 20  # Защита от бесконечного цикла
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Определить следующее действие
            # Не передаем last_answer для первого вопроса
            if self.flow_manager.context.questions_asked == 0:
                action = self.flow_manager.decide_next_action()
            else:
                action = self.flow_manager.decide_next_action(last_answer=self.last_answer)

            logger.info(f"[ACTION] Type: {action['type']}, Transition: {action['transition'].value}")

            # Проверить финализацию
            if action['type'] == 'finalize':
                logger.info("[FINALIZE] Interview complete")
                return None

            # Получить reference point
            rp = action['reference_point']
            self.current_rp = rp

            logger.info(f"[RP] {rp.id}: {rp.name} [P{rp.priority.value}]")

            # Сгенерировать вопрос
            question = await self._generate_question(rp)

            if not question:
                # Skip - уже отвечено, пробуем следующий
                logger.info(f"[SKIP] {rp.id} already covered, trying next")
                # Помечаем текущий RP как завершенный чтобы не попадать в него снова
                rp.update_state(ReferencePointState.COMPLETED)
                continue

            # Нашли вопрос!
            self.current_question = question

            # Добавить transition message если есть
            if action.get('message'):
                question = f"{action['message']}\n\n{question}"

            return question

        # Если вышли из цикла - что-то пошло не так
        logger.error("[ERROR] Too many iterations in get_next_question")
        return None

    async def _generate_question(self, rp) -> Optional[str]:
        """
        Сгенерировать вопрос для Reference Point

        Args:
            rp: ReferencePoint

        Returns:
            Вопрос или None если skip
        """
        if not self.question_generator:
            # Fallback - использовать hints
            logger.warning("[FALLBACK] Using question hints")
            return rp.question_hints[0] if rp.question_hints else f"Расскажите о: {rp.name}"

        # Контекст разговора
        context = {
            'collected_fields': {rp_id: rp.collected_data.get('text', '')
                               for rp_id, rp in self.rp_manager.reference_points.items()
                               if rp.collected_data},
            'covered_topics': self.flow_manager.context.covered_topics,
            **self.flow_manager.context.collected_data
        }

        # Сгенерировать вопрос
        try:
            question = await self.question_generator.generate_question(
                reference_point=rp,
                conversation_context=context,
                user_level=UserExpertiseLevel.INTERMEDIATE,
                project_type=ProjectType.UNKNOWN
            )

            return question

        except Exception as e:
            logger.error(f"[ERROR] Question generation failed: {e}")
            # Fallback
            return rp.question_hints[0] if rp.question_hints else f"Расскажите о: {rp.name}"

    async def process_answer(self, answer: str):
        """
        Обработать ответ пользователя

        Args:
            answer: Ответ пользователя
        """
        if not self.current_rp:
            logger.warning("[WARN] No current RP to process answer")
            return

        logger.info(f"[ANSWER] Processing answer for {self.current_rp.id}: {answer[:50]}...")

        # Сохранить ответ в RP
        self.current_rp.add_data('text', answer)

        # Сохранить в context
        self.flow_manager.context.add_turn(
            question=self.current_question,
            answer=answer,
            rp_id=self.current_rp.id
        )

        # Сохранить last_answer
        self.last_answer = answer

        logger.info(f"[OK] Answer processed for {self.current_rp.id}")

    def is_complete(self) -> bool:
        """
        Проверить завершенность интервью

        Returns:
            True если интервью завершено
        """
        return self.flow_manager.context.current_state.value == 'finalizing'

    def get_progress(self) -> str:
        """
        Получить информацию о прогрессе

        Returns:
            Текст с прогрессом
        """
        return self.flow_manager.get_progress_message()

    async def get_results(self) -> Dict[str, Any]:
        """
        Получить результаты интервью

        Returns:
            Результаты с анкетой и оценкой
        """
        # Построить анкету из Reference Points
        anketa = self._build_anketa()

        # Финальный аудит
        audit_result = await self._final_audit(anketa)

        # Сохранить в БД
        await self._save_to_db(anketa, audit_result)

        processing_time = (datetime.now() - self.started_at).total_seconds()

        return {
            'anketa': anketa,
            'audit_score': audit_result.get('final_score', 0),
            'audit_details': audit_result,
            'questions_asked': self.flow_manager.context.questions_asked,
            'follow_ups_asked': self.flow_manager.context.follow_ups_asked,
            'processing_time': processing_time,
            'conversation_state': self.flow_manager.context.current_state.value
        }

    def _build_anketa(self) -> Dict[str, Any]:
        """
        Построить анкету из Reference Points

        Returns:
            Анкета в формате для аудита
        """
        anketa = {}

        # Маппинг RP -> поля анкеты
        rp_to_field_mapping = {
            'rp_001_project_essence': 'project_goal',
            'rp_002_problem': 'problem_description',
            'rp_003_target_audience': 'target_audience',
            'rp_004_methodology': 'methodology',
            'rp_005_budget': 'budget_total',
            'rp_006_budget_breakdown': 'budget_breakdown',
            'rp_007_results': 'expected_results',
            'rp_008_team': 'team_description',
            'rp_009_partners': 'partners',
            'rp_010_risks': 'risks',
            'rp_011_sustainability': 'sustainability',
            'rp_012_geography': 'region',
            'rp_013_timeline': 'project_duration_months'
        }

        for rp_id, field_name in rp_to_field_mapping.items():
            rp = self.rp_manager.get_reference_point(rp_id)
            if rp and rp.collected_data:
                anketa[field_name] = rp.collected_data.get('text', '')

        return anketa

    async def _final_audit(self, anketa: Dict[str, Any]) -> Dict[str, Any]:
        """
        Финальный аудит анкеты

        Args:
            anketa: Собранная анкета

        Returns:
            Результаты аудита
        """
        try:
            from agents.auditor_agent import AuditorAgent

            auditor = AuditorAgent(self.db, self.llm_provider)
            audit_result = await auditor.evaluate_anketa(anketa, grant_fund='fpg')

            # Пересчитать score с учетом Reference Points
            rp_progress = self.rp_manager.get_progress()

            # Модификация score на основе полноты RP
            completion_bonus = rp_progress.overall_completion * 10  # До +10 баллов

            final_score = min(100, audit_result.get('final_score', 0) + completion_bonus)

            return {
                **audit_result,
                'final_score': final_score,
                'rp_completion': rp_progress.overall_completion,
                'critical_completed': rp_progress.critical_completed,
                'important_completed': rp_progress.important_completed
            }

        except Exception as e:
            logger.error(f"[ERROR] Audit failed: {e}")
            return {
                'final_score': 50,
                'error': str(e)
            }

    async def _save_to_db(
        self,
        anketa: Dict[str, Any],
        audit_result: Dict[str, Any]
    ):
        """
        Сохранить результаты в БД

        Args:
            anketa: Анкета
            audit_result: Результаты аудита
        """
        try:
            # TODO: Реализовать сохранение в БД
            logger.info(f"[SAVE] Saving to DB: user={self.user_data.get('telegram_id')}, "
                       f"score={audit_result['final_score']}")

        except Exception as e:
            logger.error(f"[ERROR] DB save failed: {e}")


# Пример использования
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def main():
        # Mock DB
        db = None

        # Mock user data
        user_data = {
            'telegram_id': 123456,
            'username': 'test_user',
            'grant_fund': 'fpg'
        }

        # Создать интервью
        interview = TelegramInteractiveInterview(db, user_data)

        # Симуляция диалога
        answers = [
            "Наш проект создает инклюзивные пространства для детей с ОВЗ",
            "Проблема - отсутствие доступных пространств в регионе",
            "Целевая аудитория - дети 7-14 лет с ОВЗ",
            # ...
        ]

        for i, mock_answer in enumerate(answers[:5]):
            # Получить вопрос
            question = await interview.get_next_question()

            if not question:
                print("[COMPLETE] Interview finished early")
                break

            print(f"\n[Q{i+1}] {question}")
            print(f"[A{i+1}] {mock_answer}")

            # Обработать ответ
            await interview.process_answer(mock_answer)

            # Показать прогресс
            if (i + 1) % 3 == 0:
                print(f"\n{interview.get_progress()}")

        # Получить результаты
        if interview.is_complete():
            results = await interview.get_results()
            print(f"\n[RESULTS] Score: {results['audit_score']}/100")
            print(f"Questions: {results['questions_asked']}")
            print(f"Follow-ups: {results['follow_ups_asked']}")

    asyncio.run(main())
