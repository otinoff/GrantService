#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grant Handler - ProductionWriter Integration для Telegram Bot

Обрабатывает генерацию грантовых заявок через ProductionWriter.

Author: Grant Service Architect Agent
Created: 2025-10-24
Version: 1.0
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class GrantHandler:
    """
    Handler для генерации грантовых заявок через ProductionWriter

    Управляет:
    - Генерацией грантов по anketa_id
    - Отображением статуса генерации
    - Отправкой готовых грантов пользователю
    - Уведомлениями администраторов
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

        # Хранилище активных генераций
        # {user_id: {grant_id, start_time, status}}
        self.active_generations = {}

    def is_generation_active(self, user_id: int) -> bool:
        """Проверить активна ли генерация для пользователя"""
        return user_id in self.active_generations

    async def generate_grant(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        anketa_id: str = None
    ):
        """
        Генерировать грантовую заявку

        Args:
            update: Telegram Update
            context: Telegram Context
            anketa_id: ID анкеты (опционально, если не указан - берется последняя)
        """
        user_id = update.effective_user.id

        # Проверить если уже есть активная генерация
        if self.is_generation_active(user_id):
            await update.message.reply_text(
                "⏳ У вас уже запущена генерация гранта. "
                "Пожалуйста, дождитесь завершения текущей генерации."
            )
            return

        logger.info(f"[GRANT] Starting grant generation for user {user_id}, anketa_id={anketa_id}")

        # Получить anketa_id если не указан
        if anketa_id is None:
            # Получить последнюю завершенную анкету пользователя
            anketa = self.db.get_latest_completed_anketa(user_id)
            if anketa is None:
                await update.message.reply_text(
                    "❌ У вас нет завершенных анкет.\n"
                    "Пожалуйста, сначала пройдите интервью командой /start"
                )
                return
            anketa_id = anketa['anketa_id']
        else:
            # Проверить что анкета существует и принадлежит пользователю
            anketa = self.db.get_session_by_anketa_id(anketa_id)
            if anketa is None:
                await update.message.reply_text(
                    f"❌ Анкета {anketa_id} не найдена."
                )
                return
            if anketa['telegram_id'] != user_id:
                await update.message.reply_text(
                    f"❌ Анкета {anketa_id} не принадлежит вам."
                )
                return

        logger.info(f"[GRANT] Using anketa_id: {anketa_id}")

        # Проверить есть ли уже готовый грант для этой анкеты
        existing_grant = self.db.get_grant_by_anketa_id(anketa_id)
        if existing_grant and existing_grant['status'] == 'completed':
            await update.message.reply_text(
                f"✅ Для анкеты {anketa_id} уже есть готовая грантовая заявка!\n\n"
                f"📊 Статистика:\n"
                f"• Символов: {existing_grant.get('character_count', 'N/A')}\n"
                f"• Слов: {existing_grant.get('word_count', 'N/A')}\n"
                f"• Секций: {existing_grant.get('sections_generated', 'N/A')}\n"
                f"• Создана: {existing_grant.get('created_at', 'N/A')}\n\n"
                f"Используйте /get_grant {anketa_id} для получения заявки."
            )
            return

        # Отправить уведомление о начале генерации
        status_message = await update.message.reply_text(
            f"🚀 Начинаю генерацию грантовой заявки...\n\n"
            f"📋 Анкета: {anketa_id}\n"
            f"⏱ Это займет ~2-3 минуты\n\n"
            f"Я пришлю уведомление когда заявка будет готова!"
        )

        # Зарегистрировать активную генерацию
        self.active_generations[user_id] = {
            'anketa_id': anketa_id,
            'start_time': datetime.now(),
            'status': 'running',
            'status_message_id': status_message.message_id
        }

        # Запустить генерацию в фоне
        try:
            # Импортируем ProductionWriter
            from agents.production_writer import ProductionWriter
            import os

            # Получить предпочитаемый LLM провайдер пользователя
            llm_provider = self.db.get_user_llm_preference(user_id)
            logger.info(f"User {user_id} preferred LLM: {llm_provider}")

            # Создать ProductionWriter
            writer = ProductionWriter(
                llm_provider=llm_provider,
                qdrant_host=os.getenv('QDRANT_HOST', '5.35.88.251'),
                qdrant_port=int(os.getenv('QDRANT_PORT', '6333')),
                postgres_host=os.getenv('PGHOST', 'localhost'),
                postgres_port=int(os.getenv('PGPORT', '5434')),
                postgres_user=os.getenv('PGUSER', 'grantservice'),
                postgres_password=os.getenv('PGPASSWORD'),
                postgres_db=os.getenv('PGDATABASE', 'grantservice'),
                db=self.db
            )

            logger.info(f"[GRANT] ProductionWriter initialized for anketa {anketa_id}")

            # Генерируем грант
            result = await asyncio.to_thread(
                writer.generate_grant,
                anketa_id=anketa_id
            )

            # Проверяем результат
            if result['success']:
                grant_id = result['grant_id']
                grant = self.db.get_grant_by_id(grant_id)

                # Обновить статус генерации
                self.active_generations[user_id]['status'] = 'completed'
                self.active_generations[user_id]['grant_id'] = grant_id

                # Отправить уведомление пользователю
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text=f"✅ Грантовая заявка готова!\n\n"
                         f"📋 Анкета: {anketa_id}\n"
                         f"🆔 Grant ID: {grant_id}\n\n"
                         f"📊 Статистика:\n"
                         f"• Символов: {grant.get('character_count', 'N/A'):,}\n"
                         f"• Слов: {grant.get('word_count', 'N/A'):,}\n"
                         f"• Секций: {grant.get('sections_generated', 'N/A')}\n"
                         f"• Время генерации: {grant.get('duration_seconds', 'N/A'):.1f}s\n\n"
                         f"Используйте /get_grant {anketa_id} для получения заявки."
                )

                # Уведомить администратора
                if self.admin_chat_id:
                    await context.bot.send_message(
                        chat_id=self.admin_chat_id,
                        text=f"✅ Новая грантовая заявка сгенерирована!\n\n"
                             f"👤 User: {update.effective_user.username or update.effective_user.first_name} (ID: {user_id})\n"
                             f"📋 Anketa: {anketa_id}\n"
                             f"🆔 Grant: {grant_id}\n"
                             f"📊 Символов: {grant.get('character_count', 0):,}\n"
                             f"⏱ Время: {grant.get('duration_seconds', 0):.1f}s"
                    )

                logger.info(f"[GRANT] Successfully generated grant {grant_id} for anketa {anketa_id}")

            else:
                # Ошибка генерации
                error_msg = result.get('error', 'Unknown error')

                self.active_generations[user_id]['status'] = 'failed'
                self.active_generations[user_id]['error'] = error_msg

                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text=f"❌ Ошибка при генерации грантовой заявки\n\n"
                         f"📋 Анкета: {anketa_id}\n"
                         f"❗️ Ошибка: {error_msg}\n\n"
                         f"Пожалуйста, попробуйте еще раз или обратитесь к администратору."
                )

                logger.error(f"[GRANT] Failed to generate grant for anketa {anketa_id}: {error_msg}")

        except Exception as e:
            logger.error(f"[GRANT] Exception during grant generation: {e}", exc_info=True)

            self.active_generations[user_id]['status'] = 'error'
            self.active_generations[user_id]['error'] = str(e)

            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text=f"❌ Произошла ошибка при генерации\n\n"
                     f"📋 Анкета: {anketa_id}\n"
                     f"❗️ {str(e)}\n\n"
                     f"Администратор уведомлен о проблеме."
            )

            # Уведомить администратора об ошибке
            if self.admin_chat_id:
                await context.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=f"❌ Ошибка генерации гранта!\n\n"
                         f"👤 User: {update.effective_user.username or update.effective_user.first_name} (ID: {user_id})\n"
                         f"📋 Anketa: {anketa_id}\n"
                         f"❗️ Error: {str(e)}"
                )

        finally:
            # Удалить из активных генераций
            if user_id in self.active_generations:
                del self.active_generations[user_id]

    async def get_grant(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        anketa_id: str = None
    ):
        """
        Получить готовую грантовую заявку

        Args:
            update: Telegram Update
            context: Telegram Context
            anketa_id: ID анкеты (опционально)
        """
        user_id = update.effective_user.id

        # Получить anketa_id если не указан
        if anketa_id is None:
            # Получить последнюю завершенную анкету с грантом
            grant = self.db.get_latest_grant_for_user(user_id)
            if grant is None:
                await update.message.reply_text(
                    "❌ У вас нет готовых грантовых заявок.\n"
                    "Используйте /generate_grant для создания заявки."
                )
                return
            anketa_id = grant['anketa_id']

        # Получить грант по anketa_id
        grant = self.db.get_grant_by_anketa_id(anketa_id)

        if grant is None:
            await update.message.reply_text(
                f"❌ Грантовая заявка для анкеты {anketa_id} не найдена.\n"
                f"Используйте /generate_grant {anketa_id} для создания."
            )
            return

        # Проверить права доступа
        if grant['user_id'] != user_id:
            await update.message.reply_text(
                f"❌ У вас нет доступа к этой грантовой заявке."
            )
            return

        # Проверить статус
        if grant['status'] != 'completed':
            await update.message.reply_text(
                f"⏳ Грантовая заявка еще генерируется.\n"
                f"Статус: {grant['status']}\n\n"
                f"Пожалуйста, подождите немного."
            )
            return

        # Отправить грант пользователю
        grant_content = grant.get('grant_content', '')

        if not grant_content:
            await update.message.reply_text(
                f"❌ Содержимое грантовой заявки отсутствует."
            )
            return

        # Отправляем грант частями, если он слишком большой (лимит Telegram: 4096 символов)
        max_length = 4000

        if len(grant_content) <= max_length:
            await update.message.reply_text(grant_content)
        else:
            # Разбиваем на части
            parts = []
            current_part = ""

            for line in grant_content.split('\n'):
                if len(current_part) + len(line) + 1 <= max_length:
                    current_part += line + '\n'
                else:
                    parts.append(current_part)
                    current_part = line + '\n'

            if current_part:
                parts.append(current_part)

            # Отправляем части
            await update.message.reply_text(
                f"📄 Грантовая заявка (разбита на {len(parts)} частей):\n"
                f"📋 Анкета: {anketa_id}\n"
                f"🆔 Grant ID: {grant['grant_id']}"
            )

            for i, part in enumerate(parts, 1):
                await update.message.reply_text(
                    f"Часть {i}/{len(parts)}:\n\n{part}"
                )
                await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями

        # Обновить статус отправки пользователю
        self.db.mark_grant_sent_to_user(grant['grant_id'])

        logger.info(f"[GRANT] Sent grant {grant['grant_id']} to user {user_id}")

    async def list_grants(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Показать список грантовых заявок пользователя

        Args:
            update: Telegram Update
            context: Telegram Context
        """
        user_id = update.effective_user.id

        # Получить все гранты пользователя
        grants = self.db.get_user_grants(user_id)

        if not grants:
            await update.message.reply_text(
                "📋 У вас пока нет грантовых заявок.\n"
                "Используйте /generate_grant для создания."
            )
            return

        # Формируем список
        message = f"📋 Ваши грантовые заявки ({len(grants)}):\n\n"

        for i, grant in enumerate(grants, 1):
            status_emoji = {
                'draft': '📝',
                'pending': '⏳',
                'completed': '✅',
                'sent_to_user': '📤',
                'approved': '🎉',
                'rejected': '❌'
            }.get(grant['status'], '❓')

            message += (
                f"{i}. {status_emoji} {grant['grant_id'][:8]}...\n"
                f"   📋 Анкета: {grant['anketa_id']}\n"
                f"   📊 Символов: {grant.get('character_count', 'N/A'):,}\n"
                f"   📅 Создана: {grant['created_at']}\n"
                f"   🔖 Статус: {grant['status']}\n\n"
            )

        message += (
            f"Для получения заявки используйте:\n"
            f"/get_grant <anketa_id>"
        )

        await update.message.reply_text(message)
