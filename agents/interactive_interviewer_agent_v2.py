#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Interviewer Agent V2 - Reference Points Framework

НОВАЯ АРХИТЕКТУРА:
- Reference Points вместо жёстких вопросов
- Адаптивная генерация вопросов на основе контекста
- Естественный поток диалога (state machine)
- Интеграция с Qdrant (база знаний ФПГ)
- Бюджет уточняющих вопросов (макс 5)

Flow:
1. INIT: Приветствие
2. EXPLORING: Исследование проекта (базовые RP)
3. DEEPENING: Углубление (неполные критичные RP)
4. VALIDATING: Валидация (проверка понимания)
5. FINALIZING: Завершение + сохранение

Author: Grant Service Architect Agent
Created: 2025-10-20
Version: 2.0 (Reference Points Framework)
"""

import sys
import os
from pathlib import Path

# Cross-platform path setup
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "shared"))
sys.path.insert(0, str(_project_root / "agents"))

from typing import Dict, Any, List, Optional
import logging
import asyncio
import time
from datetime import datetime

from base_agent import BaseAgent
from auditor_agent import AuditorAgent

# Reference Points Framework
from reference_points import (
    ReferencePointManager,
    AdaptiveQuestionGenerator,
    ConversationFlowManager,
    ConversationState,
    TransitionType,
    UserExpertiseLevel,
    ProjectType
)

# LLM
try:
    from llm.unified_llm_client import UnifiedLLMClient
    from llm.config import AGENT_CONFIGS
    UNIFIED_CLIENT_AVAILABLE = True
except ImportError:
    UNIFIED_CLIENT_AVAILABLE = False
    print("[WARN] UnifiedLLMClient недоступен")

# Qdrant
try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("[WARN] Qdrant client недоступен")

logger = logging.getLogger(__name__)


class InteractiveInterviewerAgentV2(BaseAgent):
    """
    Интерактивный интервьюер с Reference Points Framework

    Основные отличия от V1:
    - Адаптивные вопросы вместо жёстких
    - State machine для естественного диалога
    - Интеграция с Qdrant для контекста
    - Приоритизация информации (P0-P3)
    - Бюджет уточняющих вопросов (макс 5)

    Example:
        >>> agent = InteractiveInterviewerAgentV2(db, llm_provider="claude_code")
        >>> result = await agent.conduct_interview(user_data)
        >>> print(result['audit_score'])
    """

    def __init__(
        self,
        db,
        llm_provider: str = "claude_code",
        qdrant_host: str = "5.35.88.251",
        qdrant_port: int = 6333
    ):
        """
        Инициализация агента

        Args:
            db: Database connection
            llm_provider: LLM провайдер (claude_code, gigachat, openai)
            qdrant_host: Хост Qdrant сервера
            qdrant_port: Порт Qdrant
        """
        super().__init__("interactive_interviewer_v2", db, llm_provider)

        # Auditor для оценки
        self.auditor = AuditorAgent(db, llm_provider)

        # Reference Points Manager
        self.rp_manager = ReferencePointManager()
        self.rp_manager.load_fpg_reference_points()  # Загрузить ФПГ reference points

        # Adaptive Question Generator
        self.question_generator = None  # Инициализируем после LLM

        # Conversation Flow Manager
        self.flow_manager = ConversationFlowManager(self.rp_manager)

        # Qdrant для контекста
        self.qdrant = None
        self.qdrant_collection = "knowledge_sections"

        if QDRANT_AVAILABLE:
            try:
                self.qdrant = QdrantClient(
                    host=qdrant_host,
                    port=qdrant_port,
                    timeout=10
                )
                logger.info(f"✅ Qdrant connected ({qdrant_host}:{qdrant_port})")
            except Exception as e:
                logger.warning(f"⚠️ Qdrant unavailable: {e}")
                self.qdrant = None
        else:
            logger.warning("⚠️ Qdrant client not installed")

        # Инициализация LLM
        self._init_llm()

        # Инициализация Question Generator
        if self.llm:
            self.question_generator = AdaptiveQuestionGenerator(
                llm_client=self.llm,
                qdrant_client=self.qdrant,
                qdrant_collection=self.qdrant_collection
            )

        logger.info(f"✅ InteractiveInterviewerAgentV2 initialized with {llm_provider}")

    def _init_llm(self):
        """Инициализация LLM клиента"""
        if not UNIFIED_CLIENT_AVAILABLE:
            logger.error("UnifiedLLMClient not available")
            self.llm = None
            return

        try:
            # Получить конфигурацию для interviewer
            config = AGENT_CONFIGS.get("interviewer", {})

            self.llm = UnifiedLLMClient(
                provider=self.llm_provider,
                model=config.get("model"),
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 2000)
            )

            logger.info(f"✅ LLM initialized: {self.llm_provider}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Основной метод обработки (требуется BaseAgent)

        Для V2 используйте async метод conduct_interview()
        """
        raise NotImplementedError(
            "InteractiveInterviewerAgentV2 is async-only. "
            "Use: await agent.conduct_interview(user_data, callback)"
        )

    async def conduct_interview(
        self,
        user_data: Dict[str, Any],
        callback_ask_question: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Провести интервью с использованием Reference Points Framework

        Args:
            user_data: Данные пользователя (telegram_id, username, grant_fund)
            callback_ask_question: Callback для задавания вопросов
                async def ask(question: str) -> str

        Returns:
            {
                'anketa': {...},  # Собранная анкета
                'audit_score': float,  # Итоговая оценка 0-100
                'audit_details': {...},  # Детали аудита
                'questions_asked': int,  # Сколько вопросов задано
                'follow_ups_asked': int,  # Сколько уточняющих
                'processing_time': float,  # Время в секундах
                'conversation_state': str  # Финальное состояние
            }
        """
        start_time = time.time()

        logger.info("=" * 80)
        logger.info("НАЧАЛО ИНТЕРАКТИВНОГО ИНТЕРВЬЮ V2 (REFERENCE POINTS)")
        logger.info("=" * 80)

        # Приветствие
        await self._send_greeting(user_data, callback_ask_question)

        # Основной цикл разговора
        anketa = await self._conversation_loop(user_data, callback_ask_question)

        # Финальный аудит
        logger.info("\n[ФИНАЛЬНЫЙ АУДИТ] Комплексная оценка заявки")
        audit_result = await self._final_audit(anketa)

        # Сохранить в БД
        await self._save_to_db(user_data, anketa, audit_result)

        processing_time = time.time() - start_time

        logger.info("=" * 80)
        logger.info(f"ИНТЕРВЬЮ ЗАВЕРШЕНО | Score: {audit_result['final_score']}/100 | "
                   f"Time: {processing_time:.1f}s")
        logger.info("=" * 80)

        return {
            'anketa': anketa,
            'audit_score': audit_result['final_score'],
            'audit_details': audit_result,
            'questions_asked': self.flow_manager.context.questions_asked,
            'follow_ups_asked': self.flow_manager.context.follow_ups_asked,
            'processing_time': processing_time,
            'conversation_state': self.flow_manager.context.current_state.value
        }

    async def _send_greeting(
        self,
        user_data: Dict[str, Any],
        callback: Optional[callable]
    ):
        """Отправить приветствие"""
        greeting = f"""
Здравствуйте! 👋

Я помогу вам оформить заявку на грант Фонда президентских грантов.

Мы проведём интересный разговор о вашем проекте. Я буду задавать вопросы,
а вы рассказывайте всё, что считаете важным.

Не беспокойтесь о структуре - я сам соберу всю информацию правильно.

Готовы начать? 🚀
"""
        if callback:
            await callback(greeting)
        else:
            logger.info(f"GREETING: {greeting}")

    async def _conversation_loop(
        self,
        user_data: Dict[str, Any],
        callback_ask_question: Optional[callable]
    ) -> Dict[str, Any]:
        """
        Основной цикл разговора

        Args:
            user_data: Данные пользователя
            callback_ask_question: Callback для вопросов

        Returns:
            Собранная анкета
        """
        last_answer = None
        turn = 1
        max_turns = 30  # Защита от бесконечного цикла

        while turn <= max_turns:
            logger.info(f"\n--- Turn {turn} ---")

            # Определить следующее действие
            action = self.flow_manager.decide_next_action(last_answer=last_answer)

            logger.info(f"Action: {action['type']} | Transition: {action['transition'].value}")

            # Проверить финализацию
            if action['type'] == 'finalize':
                if callback_ask_question:
                    await callback_ask_question(action['message'])
                logger.info(action['message'])
                break

            # Получить reference point
            rp = action['reference_point']
            logger.info(f"Current RP: {rp.id} ({rp.name}) [P{rp.priority.value}]")

            # Показать прогресс (каждые 5 вопросов)
            if turn % 5 == 1 and turn > 1:
                progress_msg = self.flow_manager.get_progress_message()
                if callback_ask_question:
                    await callback_ask_question(progress_msg)
                logger.info(progress_msg)

            # Сгенерировать вопрос
            question = await self._generate_question_for_rp(
                rp,
                action['transition']
            )

            if not question:
                # Skip - уже отвечено
                logger.info(f"Skipping {rp.id} - already covered")
                turn += 1
                continue

            # Показать сообщение перехода
            if action.get('message'):
                full_question = f"{action['message']}\n\n{question}"
            else:
                full_question = question

            # Задать вопрос
            if callback_ask_question:
                answer = await callback_ask_question(full_question)
            else:
                # Mock для тестирования
                logger.info(f"QUESTION: {full_question}")
                answer = f"[Mock answer for {rp.name}]"
                logger.info(f"ANSWER: {answer}")

            # Сохранить ответ
            self.flow_manager.context.add_turn(
                question=question,
                answer=answer,
                rp_id=rp.id
            )

            # Отметить follow-up если это уточнение
            if action['transition'] in [TransitionType.DEEP_DIVE, TransitionType.LOOP_BACK]:
                self.flow_manager.add_follow_up()

            last_answer = answer
            turn += 1

        # Собрать анкету из reference points
        anketa = self._build_anketa_from_rps()

        return anketa

    async def _generate_question_for_rp(
        self,
        rp,
        transition: TransitionType
    ) -> Optional[str]:
        """
        Сгенерировать вопрос для Reference Point

        Args:
            rp: ReferencePoint
            transition: Тип перехода

        Returns:
            Вопрос или None если skip
        """
        if not self.question_generator:
            # Fallback - использовать hints из RP
            logger.warning("Question generator not available, using fallback")
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
        question = await self.question_generator.generate_question(
            reference_point=rp,
            conversation_context=context,
            user_level=UserExpertiseLevel.INTERMEDIATE,  # TODO: динамически определять
            project_type=ProjectType.UNKNOWN  # TODO: классифицировать
        )

        return question

    def _build_anketa_from_rps(self) -> Dict[str, Any]:
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
            audit_result = await self.auditor.evaluate_anketa(anketa, grant_fund='fpg')

            # Пересчитать score с учётом Reference Points
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
            logger.error(f"Audit failed: {e}")
            return {
                'final_score': 50,
                'error': str(e)
            }

    async def _save_to_db(
        self,
        user_data: Dict[str, Any],
        anketa: Dict[str, Any],
        audit_result: Dict[str, Any]
    ):
        """
        Сохранить результаты в БД

        Args:
            user_data: Данные пользователя
            anketa: Анкета
            audit_result: Результаты аудита
        """
        try:
            # TODO: Реализовать сохранение в БД
            logger.info(f"Saving to DB: user={user_data.get('telegram_id')}, "
                       f"score={audit_result['final_score']}")

        except Exception as e:
            logger.error(f"DB save failed: {e}")


# Пример использования
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def main():
        # Mock DB
        db = None

        # Создать агента
        agent = InteractiveInterviewerAgentV2(
            db=db,
            llm_provider="claude_code",
            qdrant_host="5.35.88.251",
            qdrant_port=6333
        )

        # Mock user data
        user_data = {
            'telegram_id': 123456,
            'username': 'test_user',
            'grant_fund': 'fpg'
        }

        # Mock callback для вопросов
        async def ask_question(question: str) -> str:
            print(f"\n🤖 BOT: {question}")
            await asyncio.sleep(0.5)
            return f"Mock answer to: {question[:50]}..."

        # Провести интервью
        result = await agent.conduct_interview(
            user_data=user_data,
            callback_ask_question=ask_question
        )

        print("\n=== РЕЗУЛЬТАТЫ ===")
        print(f"Audit Score: {result['audit_score']:.1f}/100")
        print(f"Questions Asked: {result['questions_asked']}")
        print(f"Follow-ups: {result['follow_ups_asked']}")
        print(f"Processing Time: {result['processing_time']:.1f}s")
        print(f"Final State: {result['conversation_state']}")

    asyncio.run(main())
