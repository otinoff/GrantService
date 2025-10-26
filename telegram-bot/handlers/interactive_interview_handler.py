#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Interview Handler - Reference Points Framework для Telegram Bot

Обрабатывает интерактивное интервью V2 с адаптивными вопросами
и естественным потоком диалога.

Author: Grant Service Architect Agent
Created: 2025-10-20
Version: 2.0
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class InteractiveInterviewHandler:
    """
    Handler для интерактивного интервью с Reference Points Framework

    Управляет:
    - Запуском/остановкой интервью
    - Задаванием вопросов через Telegram
    - Сохранением ответов
    - Отображением прогресса
    """

    def __init__(self, db, admin_chat_id: Optional[int] = None, pipeline_handler=None):
        """
        Инициализация handler

        Args:
            db: Database instance
            admin_chat_id: ID админского чата для уведомлений
            pipeline_handler: InteractivePipelineHandler для интеграции с Iteration 52
        """
        self.db = db
        self.admin_chat_id = admin_chat_id
        self.pipeline_handler = pipeline_handler

        # Хранилище активных интервью
        # {user_id: {agent, update, context, conversation_state, answer_queue}}
        self.active_interviews = {}

        # Import asyncio для Queue
        import asyncio
        self.asyncio = asyncio

    def is_interview_active(self, user_id: int) -> bool:
        """Проверить активно ли интервью для пользователя"""
        return user_id in self.active_interviews

    async def start_interview(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict[str, Any],
        skip_greeting: bool = False
    ):
        """
        Начать интерактивное интервью

        Args:
            update: Telegram Update
            context: Telegram Context
            user_data: Данные пользователя
        """
        user_id = update.effective_user.id

        # Проверить если уже есть активное интервью
        if self.is_interview_active(user_id):
            await update.message.reply_text(
                "У вас уже есть активное интервью. "
                "Для начала нового завершите текущее командой /stop_interview"
            )
            return

        logger.info(f"[START] Interactive Interview V2 for user {user_id}")

        # Получить предпочитаемый LLM провайдер пользователя
        llm_provider = self.db.get_user_llm_preference(user_id)
        logger.info(f"User {user_id} preferred LLM: {llm_provider}")

        # Инициализировать агента
        try:
            from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2

            agent = InteractiveInterviewerAgentV2(
                db=self.db,
                llm_provider=llm_provider,  # Используем настройку пользователя
                qdrant_host="5.35.88.251",
                qdrant_port=6333
            )

            # Создать очередь для ответов
            import asyncio
            answer_queue = asyncio.Queue()

            # Сохранить в активные
            self.active_interviews[user_id] = {
                'agent': agent,
                'update': update,
                'context': context,
                'user_data': user_data,
                'started_at': datetime.now(),
                'answer_queue': answer_queue  # Очередь для ответов
            }

            # Приветствие (если не пропускаем)
            if not skip_greeting:
                greeting = f"""
Здравствуйте! 👋

Я помогу вам оформить заявку на грант Фонда президентских грантов.

Мы проведём интересный разговор о вашем проекте. Я буду задавать вопросы,
а вы рассказывайте всё, что считаете важным.

Не беспокойтесь о структуре - я сам соберу всю информацию правильно.

Готовы начать? Нажмите /continue для продолжения.
                """

                # Send greeting (works with both message and callback)
                chat = update.effective_chat
                await context.bot.send_message(chat_id=chat.id, text=greeting)

            logger.info(f"[OK] Interview initialized for user {user_id} (skip_greeting={skip_greeting})")

        except ImportError as e:
            logger.error(f"[ERROR] Failed to import InteractiveInterviewerAgentV2: {e}")
            chat = update.effective_chat
            await context.bot.send_message(
                chat_id=chat.id,
                text="Извините, система интервью временно недоступна. "
                     "Попробуйте позже или обратитесь в поддержку."
            )
        except Exception as e:
            logger.error(f"[ERROR] Failed to start interview: {e}")
            import traceback
            traceback.print_exc()
            chat = update.effective_chat
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"Произошла ошибка при запуске интервью: {e}"
            )

    async def continue_interview(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Продолжить интервью (задать следующий вопрос)

        Args:
            update: Telegram Update
            context: Telegram Context
        """
        user_id = update.effective_user.id

        if not self.is_interview_active(user_id):
            await update.message.reply_text(
                "У вас нет активного интервью. "
                "Начните новое командой /start_interview"
            )
            return

        interview = self.active_interviews[user_id]
        agent = interview['agent']
        answer_queue = interview['answer_queue']

        # Создать callback для задавания вопросов
        async def ask_question_callback(question: str = None) -> str:
            """
            Callback для задавания вопросов через Telegram

            Args:
                question: Вопрос от агента (None = пропустить отправку, только ждать ответа)

            Returns:
                Ответ пользователя
            """
            # Отправить вопрос (если он есть)
            # ✅ ITERATION 26: Если question=None, пропускаем отправку (для hardcoded вопросов)
            if question is not None:
                # Отправить вопрос (используем context.bot вместо update.message для совместимости с callback)
                chat_id = update.effective_chat.id if update.effective_chat else user_id
                await context.bot.send_message(chat_id=chat_id, text=question)
                logger.info(f"[SENT] Question sent to user {user_id}")
            else:
                logger.info(f"[SKIP] Skipping question send (hardcoded RP) for user {user_id}")

            # Ждем реального ответа из очереди
            logger.info(f"[WAITING] Waiting for answer from user {user_id}")
            answer = await answer_queue.get()
            logger.info(f"[RECEIVED] Got answer from user {user_id}: {answer[:50]}...")

            return answer

        try:
            # ВАЖНО: Запустить интервью в отдельной задаче (task)
            # чтобы не блокировать event loop
            async def run_interview():
                """Запустить интервью в фоне"""
                try:
                    result = await agent.conduct_interview(
                        user_data=interview['user_data'],
                        callback_ask_question=ask_question_callback
                    )

                    # Интервью завершено
                    logger.info(f"[COMPLETE] Interview completed for user {user_id}")
                    logger.info(f"[SCORE] Audit score: {result['audit_score']}/100")

                    # Сохранить анкету в БД
                    try:
                        # Получить user_data из интервью
                        interview_data = self.active_interviews.get(user_id, {})
                        user_data_from_interview = interview_data.get('user_data', {})

                        # ITERATION 52 FIX (Phase 14): Сохранить через БД правильно
                        import json
                        from datetime import datetime
                        anketa_data = result.get('anketa', {})

                        # Использовать правильные функции БД
                        from data.database import get_or_create_session, update_session_data

                        # Получить или создать сессию
                        session_data = get_or_create_session(user_id)
                        if not session_data:
                            logger.error(f"[DB] Failed to create session for user {user_id}")
                            raise Exception("Failed to create database session")

                        session_id = session_data.get('id')
                        logger.info(f"[DB] Using session ID: {session_id}")

                        # Сгенерировать anketa_id
                        anketa_id = f"anketa_{session_id}_{int(datetime.now().timestamp())}"

                        # Сохранить данные анкеты в БД
                        update_data = {
                            'interview_data': json.dumps(anketa_data, ensure_ascii=False),
                            'anketa_id': anketa_id,
                            'audit_result': json.dumps(result.get('audit_details', {}), ensure_ascii=False),
                            'completion_status': 'completed',
                            'status': 'completed',
                            'completed_at': datetime.now()
                        }

                        success = update_session_data(session_id, update_data)
                        if not success:
                            logger.error(f"[DB] Failed to update session {session_id}")
                            raise Exception("Failed to save anketa to database")

                        logger.info(f"[DB] Anketa saved successfully with ID: {anketa_id}")

                        # ITERATION 52 FIX (Phase 15): НЕ вызываем _send_results() здесь!
                        # update может быть None в background task.
                        # Pipeline handler сам отправит файл anketa.txt с данными.
                        # await self._send_results(update, result)  # ← Removed

                        # ITERATION 52: Вызвать Interactive Pipeline
                        if self.pipeline_handler and anketa_id:
                            logger.info(f"[PIPELINE] Starting interactive pipeline for anketa {anketa_id}")

                            # Подготовить session_data для pipeline
                            session_for_pipeline = {
                                'audit_score': result.get('audit_score', 0),
                                'audit_recommendations': result.get('audit_details', {}).get('recommendations', [])
                            }

                            # Вызвать on_anketa_complete
                            await self.pipeline_handler.on_anketa_complete(
                                update,
                                context,
                                anketa_id,
                                session_for_pipeline
                            )
                        else:
                            logger.warning("[PIPELINE] Pipeline handler not available or anketa_id missing")

                    except Exception as e:
                        logger.error(f"[ERROR] Failed to save anketa or start pipeline: {e}")
                        import traceback
                        traceback.print_exc()

                        # ITERATION 52 FIX (Phase 15): НЕ пытаемся отправить результаты
                        # update может быть None в background task
                        # Просто логируем ошибку
                        # await self._send_results(update, result)  # ← Removed

                    # Удалить из активных
                    if user_id in self.active_interviews:
                        del self.active_interviews[user_id]

                except Exception as e:
                    logger.error(f"[ERROR] Interview error for user {user_id}: {e}")
                    import traceback
                    traceback.print_exc()

                    # Отправить сообщение об ошибке
                    chat = update.effective_chat
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=f"Произошла ошибка во время интервью: {e}"
                    )

            # Запустить в background task
            import asyncio
            asyncio.create_task(run_interview())

            logger.info(f"[BACKGROUND] Interview task created for user {user_id}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to start interview task for user {user_id}: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(
                f"Произошла ошибка при запуске интервью: {e}"
            )

    async def handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Обработать ответ пользователя на вопрос

        Args:
            update: Telegram Update
            context: Telegram Context
        """
        user_id = update.effective_user.id
        logger.info(f"[DEBUG] handle_message called for user {user_id}")

        if not self.is_interview_active(user_id):
            # Не активное интервью - игнорируем
            logger.info(f"[DEBUG] No active interview for user {user_id}")
            return

        logger.info(f"[DEBUG] Interview is active for user {user_id}")
        interview = self.active_interviews[user_id]
        answer_queue = interview.get('answer_queue')

        if not answer_queue:
            # Нет очереди - старая версия handler
            logger.warning(f"[DEBUG] No answer_queue for user {user_id}")
            return

        # Получить ответ
        answer = update.message.text

        logger.info(f"[ANSWER] User {user_id}: {answer[:50]}...")

        # Положить ответ в очередь - callback его заберёт
        await answer_queue.put(answer)
        logger.info(f"[DEBUG] Answer put in queue for user {user_id}")

    async def stop_interview(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Остановить интервью

        Args:
            update: Telegram Update
            context: Telegram Context
        """
        user_id = update.effective_user.id

        if not self.is_interview_active(user_id):
            await update.message.reply_text(
                "У вас нет активного интервью."
            )
            return

        # Удалить из активных
        del self.active_interviews[user_id]

        await update.message.reply_text(
            "Интервью остановлено. "
            "Вы можете начать новое командой /start_interview"
        )

        logger.info(f"[STOP] Interview stopped for user {user_id}")

    async def show_progress(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Показать прогресс интервью

        Args:
            update: Telegram Update
            context: Telegram Context
        """
        user_id = update.effective_user.id

        if not self.is_interview_active(user_id):
            await update.message.reply_text(
                "У вас нет активного интервью."
            )
            return

        interview = self.active_interviews[user_id]
        agent = interview['agent']

        # Получить прогресс от flow manager
        progress_message = agent.flow_manager.get_progress_message()

        await update.message.reply_text(
            f"[PROGRESS]\n\n{progress_message}"
        )

    async def _send_results(
        self,
        update: Update,
        result: Dict[str, Any]
    ):
        """
        Отправить результаты интервью пользователю

        Args:
            update: Telegram Update
            result: Результаты от agent
        """
        score = result['audit_score']

        # Эмодзи в зависимости от оценки
        if score >= 80:
            emoji = "[EXCELLENT]"
            status = "Отлично!"
        elif score >= 60:
            emoji = "[GOOD]"
            status = "Хорошо"
        elif score >= 40:
            emoji = "[NEEDS_WORK]"
            status = "Требует доработки"
        else:
            emoji = "[POOR]"
            status = "Недостаточно информации"

        message = f"""
{emoji} Интервью завершено!

Оценка: {score}/100
Статус: {status}

Задано вопросов: {result['questions_asked']}
Уточняющих вопросов: {result['follow_ups_asked']}
Время: {result['processing_time']:.1f} секунд

Ваша анкета сохранена и будет обработана.
        """

        await update.message.reply_text(message)

        # Отправить уведомление админу
        if self.admin_chat_id:
            try:
                admin_message = f"""
[NEW INTERVIEW COMPLETED]

User ID: {update.effective_user.id}
Username: @{update.effective_user.username}
Score: {score}/100
Questions: {result['questions_asked']}
Follow-ups: {result['follow_ups_asked']}
                """
                # TODO: Отправить админу через bot.send_message
                logger.info(f"[ADMIN] {admin_message}")
            except Exception as e:
                logger.error(f"[ERROR] Failed to notify admin: {e}")


# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Interactive Interview Handler V2")
    print("Ready for integration with Telegram Bot")
