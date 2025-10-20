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

    def __init__(self, db, admin_chat_id: Optional[int] = None):
        """
        Инициализация handler

        Args:
            db: Database instance
            admin_chat_id: ID админского чата для уведомлений
        """
        self.db = db
        self.admin_chat_id = admin_chat_id

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
        user_data: Dict[str, Any]
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

        # Инициализировать агента
        try:
            from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2

            agent = InteractiveInterviewerAgentV2(
                db=self.db,
                llm_provider="claude_code",
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

            # Приветствие
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

            logger.info(f"[OK] Interview initialized for user {user_id}")

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
        async def ask_question_callback(question: str) -> str:
            """
            Callback для задавания вопросов через Telegram

            Args:
                question: Вопрос от агента

            Returns:
                Ответ пользователя
            """
            # Отправить вопрос
            await update.message.reply_text(question)

            # Ждем реального ответа из очереди
            logger.info(f"[WAITING] Waiting for answer from user {user_id}")
            answer = await answer_queue.get()
            logger.info(f"[RECEIVED] Got answer from user {user_id}: {answer[:50]}...")

            return answer

        try:
            # Запустить интервью
            result = await agent.conduct_interview(
                user_data=interview['user_data'],
                callback_ask_question=ask_question_callback
            )

            # Интервью завершено
            logger.info(f"[COMPLETE] Interview completed for user {user_id}")
            logger.info(f"[SCORE] Audit score: {result['audit_score']}/100")

            # Отправить результаты
            await self._send_results(update, result)

            # Удалить из активных
            del self.active_interviews[user_id]

        except Exception as e:
            logger.error(f"[ERROR] Interview error for user {user_id}: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(
                f"Произошла ошибка во время интервью: {e}"
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

        if not self.is_interview_active(user_id):
            # Не активное интервью - игнорируем
            return

        interview = self.active_interviews[user_id]
        answer_queue = interview.get('answer_queue')

        if not answer_queue:
            # Нет очереди - старая версия handler
            return

        # Получить ответ
        answer = update.message.text

        logger.info(f"[ANSWER] User {user_id}: {answer[:50]}...")

        # Положить ответ в очередь - callback его заберёт
        await answer_queue.put(answer)

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
