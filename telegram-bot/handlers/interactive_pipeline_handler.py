#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Pipeline Handler - Iteration 52

Обработка пошагового флоу с файлами-чекпоинтами:
- Anketa complete → file + button "Начать аудит"
- Audit → file + button "Начать написание гранта"
- Grant → file + button "Сделать ревью"
- Review → file + "Готово!"

Author: Claude Code (Iteration 52)
Created: 2025-10-26
Version: 1.0.0
"""

import sys
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Import file generators
from shared.telegram.file_generators import (
    generate_anketa_txt,
    generate_audit_txt,
    generate_grant_txt,
    generate_review_txt
)

logger = logging.getLogger(__name__)


class InteractivePipelineHandler:
    """
    Handler для интерактивного pipeline с чекпоинтами

    Methods:
    - on_anketa_complete() - вызывается после завершения анкеты
    - handle_start_audit() - callback для кнопки "Начать аудит"
    - handle_start_grant() - callback для кнопки "Начать написание гранта"
    - handle_start_review() - callback для кнопки "Сделать ревью"
    """

    def __init__(self, db):
        """
        Args:
            db: Database instance (GrantServiceDatabase)
        """
        self.db = db
        logger.info("[PIPELINE] Interactive Pipeline Handler initialized")

    # ========== STEP 1: ANKETA → AUDIT ==========

    async def on_anketa_complete(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        anketa_id: str,
        session_data: Dict[str, Any]
    ):
        """
        Вызывается после завершения анкеты

        Actions:
        1. Генерирует файл anketa.txt
        2. Отправляет файл пользователю
        3. Показывает кнопку "Начать аудит"
        4. Обновляет state → ANKETA_COMPLETED

        Args:
            update: Telegram Update
            context: Telegram Context
            anketa_id: ID анкеты
            session_data: Данные сессии из БД
        """
        user_id = update.effective_user.id

        logger.info(f"[PIPELINE] User {user_id} completed anketa {anketa_id}")

        try:
            # Получить полные данные анкеты из БД
            anketa_data = self.db.get_session_by_anketa_id(anketa_id)

            if not anketa_data:
                logger.error(f"[ERROR] Anketa {anketa_id} not found in database")
                await update.message.reply_text(
                    "❌ Ошибка: анкета не найдена в базе данных"
                )
                return

            # Генерировать файл
            txt_content = generate_anketa_txt(anketa_data)

            # Сохранить во временный файл
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(txt_content)
                temp_file_path = f.name

            # Отправить файл
            with open(temp_file_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"anketa_{anketa_id}.txt",
                    caption="✅ Анкета заполнена!\n\nВсе ваши ответы сохранены."
                )

            # Удалить временный файл
            os.unlink(temp_file_path)

            # Создать кнопку "Начать аудит"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⚡ Начать аудит",
                    callback_data=f"start_audit:anketa:{anketa_id}"
                )]
            ])

            # Отправить сообщение с кнопкой
            await update.message.reply_text(
                text=(
                    "🎯 Анкета готова к аудиту!\n\n"
                    "Аудит проверит:\n"
                    "• Полноту ответов\n"
                    "• Ясность изложения\n"
                    "• Реалистичность проекта\n"
                    "• Инновационность решения\n\n"
                    "Нажмите кнопку когда будете готовы:"
                ),
                reply_markup=keyboard
            )

            # TODO: Update user pipeline state to ANKETA_COMPLETED
            # self.db.update_user_pipeline_state(user_id, "anketa_completed", anketa_id)

            logger.info(f"[OK] Anketa file sent to user {user_id}, button displayed")

        except Exception as e:
            logger.error(f"[ERROR] Failed to process anketa completion: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке анкеты. Попробуйте позже."
            )

    # ========== STEP 2: AUDIT → GRANT ==========

    async def handle_start_audit(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Callback handler для кнопки "Начать аудит"

        Actions:
        1. Запускает AuditorAgent
        2. Генерирует audit.txt
        3. Отправляет файл
        4. Показывает кнопку "Начать написание гранта"
        """
        query = update.callback_query
        user_id = query.from_user.id

        # Parse callback data: "start_audit:anketa:ANK123"
        callback_data = query.data
        parts = callback_data.split(':')

        if len(parts) != 3 or parts[0] != 'start_audit' or parts[1] != 'anketa':
            await query.answer("❌ Неверный формат данных", show_alert=True)
            return

        anketa_id = parts[2]

        logger.info(f"[PIPELINE] User {user_id} clicked 'Start Audit' for anketa {anketa_id}")

        # Acknowledge button click
        await query.answer("⏳ Запускаем аудит...")

        try:
            # TODO: Check pipeline state
            # state = self.db.get_user_pipeline_state(user_id)
            # if state != "anketa_completed":
            #     await query.message.reply_text("❌ Сначала завершите анкету!")
            #     return

            # Отправить сообщение о начале аудита
            await query.message.reply_text(
                "⏳ Запускаю аудит анкеты...\n\n"
                "Это займет около 30 секунд."
            )

            # Запустить AuditorAgent
            from agents.auditor_agent import AuditorAgent

            auditor = AuditorAgent(db=self.db)
            audit_result = await auditor.audit_anketa_async(anketa_id)

            if not audit_result:
                await query.message.reply_text(
                    "❌ Ошибка: не удалось выполнить аудит"
                )
                return

            # Генерировать файл
            txt_content = generate_audit_txt(audit_result)

            # Сохранить во временный файл
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(txt_content)
                temp_file_path = f.name

            # Отправить файл
            score = audit_result.get('average_score', 0)
            status = audit_result.get('approval_status', 'pending')

            status_emoji = {
                'approved': '✅',
                'needs_revision': '⚠️',
                'rejected': '❌',
                'pending': '⏳'
            }.get(status, '⏳')

            with open(temp_file_path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=f"audit_{anketa_id}.txt",
                    caption=f"{status_emoji} Аудит завершен!\n\nОценка: {score}/10"
                )

            # Удалить временный файл
            os.unlink(temp_file_path)

            # Создать кнопку "Начать написание гранта"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "✍️ Начать написание гранта",
                    callback_data=f"start_grant:anketa:{anketa_id}"
                )]
            ])

            # Отправить сообщение с кнопкой
            await query.message.reply_text(
                text=(
                    "📝 Готовы создать грантовую заявку?\n\n"
                    "Генератор создаст полноценную заявку:\n"
                    "• Описание проблемы\n"
                    "• Решение\n"
                    "• Методология\n"
                    "• Бюджет и команда\n\n"
                    "⏱️ Это займет 2-3 минуты.\n\n"
                    "Нажмите кнопку когда будете готовы:"
                ),
                reply_markup=keyboard
            )

            # TODO: Update pipeline state to AUDIT_COMPLETED
            # self.db.update_user_pipeline_state(user_id, "audit_completed", anketa_id)

            logger.info(f"[OK] Audit complete for user {user_id}, button displayed")

        except Exception as e:
            logger.error(f"[ERROR] Failed to run audit: {e}")
            import traceback
            traceback.print_exc()
            await query.message.reply_text(
                "❌ Произошла ошибка при аудите. Попробуйте позже."
            )

    # ========== STEP 3: GRANT → REVIEW ==========

    async def handle_start_grant(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Callback handler для кнопки "Начать написание гранта"

        Actions:
        1. Запускает ProductionWriter
        2. Генерирует grant.txt
        3. Отправляет файл
        4. Показывает кнопку "Сделать ревью"
        """
        query = update.callback_query
        user_id = query.from_user.id

        # Parse callback data: "start_grant:anketa:ANK123"
        callback_data = query.data
        parts = callback_data.split(':')

        if len(parts) != 3 or parts[0] != 'start_grant' or parts[1] != 'anketa':
            await query.answer("❌ Неверный формат данных", show_alert=True)
            return

        anketa_id = parts[2]

        logger.info(f"[PIPELINE] User {user_id} clicked 'Start Grant' for anketa {anketa_id}")

        # Acknowledge button click
        await query.answer("⏳ Запускаем генерацию гранта...")

        try:
            # TODO: Check pipeline state
            # state = self.db.get_user_pipeline_state(user_id)
            # if state != "audit_completed":
            #     await query.message.reply_text("❌ Сначала завершите аудит!")
            #     return

            # Отправить сообщение о начале генерации
            await query.message.reply_text(
                "⏳ Генерирую грантовую заявку...\n\n"
                "Это займет 2-3 минуты. Пожалуйста, подождите."
            )

            # Запустить ProductionWriter
            from agents.production_writer import ProductionWriter

            writer = ProductionWriter(db=self.db)
            grant = await writer.generate_grant_async(anketa_id)

            if not grant:
                await query.message.reply_text(
                    "❌ Ошибка: не удалось создать грант"
                )
                return

            grant_id = grant.get('grant_id') or grant.get('id')

            # Генерировать файл
            txt_content = generate_grant_txt(grant)

            # Сохранить во временный файл
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(txt_content)
                temp_file_path = f.name

            # Отправить файл
            content_length = len(grant.get('grant_content', ''))

            with open(temp_file_path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=f"grant_{grant_id}.txt",
                    caption=f"✅ Грант создан!\n\nРазмер: {content_length:,} символов"
                )

            # Удалить временный файл
            os.unlink(temp_file_path)

            # Создать кнопку "Сделать ревью"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🔍 Сделать ревью",
                    callback_data=f"start_review:grant:{grant_id}"
                )]
            ])

            # Отправить сообщение с кнопкой
            await query.message.reply_text(
                text=(
                    "🎉 Грантовая заявка готова!\n\n"
                    "Хотите проверить качество?\n\n"
                    "Ревью оценит:\n"
                    "• Качество аргументации\n"
                    "• Структуру заявки\n"
                    "• Соответствие требованиям\n\n"
                    "Нажмите кнопку когда будете готовы:"
                ),
                reply_markup=keyboard
            )

            # TODO: Update pipeline state to GRANT_COMPLETED
            # self.db.update_user_pipeline_state(user_id, "grant_completed", grant_id)

            logger.info(f"[OK] Grant created for user {user_id}, button displayed")

        except Exception as e:
            logger.error(f"[ERROR] Failed to generate grant: {e}")
            import traceback
            traceback.print_exc()
            await query.message.reply_text(
                "❌ Произошла ошибка при создании гранта. Попробуйте позже."
            )

    # ========== STEP 4: REVIEW → COMPLETE ==========

    async def handle_start_review(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Callback handler для кнопки "Сделать ревью"

        Actions:
        1. Запускает ReviewerAgent
        2. Генерирует review.txt
        3. Отправляет файл
        4. Показывает финальное сообщение "Готово!"
        """
        query = update.callback_query
        user_id = query.from_user.id

        # Parse callback data: "start_review:grant:GNT456"
        callback_data = query.data
        parts = callback_data.split(':')

        if len(parts) != 3 or parts[0] != 'start_review' or parts[1] != 'grant':
            await query.answer("❌ Неверный формат данных", show_alert=True)
            return

        grant_id = parts[2]

        logger.info(f"[PIPELINE] User {user_id} clicked 'Start Review' for grant {grant_id}")

        # Acknowledge button click
        await query.answer("⏳ Запускаем ревью...")

        try:
            # TODO: Check pipeline state
            # state = self.db.get_user_pipeline_state(user_id)
            # if state != "grant_completed":
            #     await query.message.reply_text("❌ Сначала создайте грант!")
            #     return

            # Отправить сообщение о начале ревью
            await query.message.reply_text(
                "⏳ Анализирую качество гранта...\n\n"
                "Это займет около 30 секунд."
            )

            # Запустить ReviewerAgent
            from agents.reviewer_agent import ReviewerAgent

            reviewer = ReviewerAgent(db=self.db)
            review = await reviewer.review_grant_async(grant_id)

            if not review:
                await query.message.reply_text(
                    "❌ Ошибка: не удалось выполнить ревью"
                )
                return

            # Генерировать файл
            txt_content = generate_review_txt(review)

            # Сохранить во временный файл
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(txt_content)
                temp_file_path = f.name

            # Отправить файл
            score = review.get('review_score', 0)
            status = review.get('final_status', 'pending')

            status_emoji = {
                'approved': '✅',
                'needs_revision': '⚠️',
                'rejected': '❌',
                'pending': '⏳'
            }.get(status, '⏳')

            with open(temp_file_path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=f"review_{grant_id}.txt",
                    caption=f"{status_emoji} Ревью завершено!\n\nОценка: {score}/10"
                )

            # Удалить временный файл
            os.unlink(temp_file_path)

            # Финальное сообщение (БЕЗ кнопок!)
            await query.message.reply_text(
                "🎉 Процесс завершен!\n\n"
                "Все файлы сохранены:\n"
                "✅ Анкета\n"
                "✅ Аудит\n"
                "✅ Грант\n"
                "✅ Ревью\n\n"
                "Вы можете скачать их из истории чата.\n\n"
                "Спасибо за использование GrantService!"
            )

            # TODO: Update pipeline state to PIPELINE_COMPLETE
            # self.db.update_user_pipeline_state(user_id, "pipeline_complete", None)

            logger.info(f"[OK] Pipeline complete for user {user_id}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to run review: {e}")
            import traceback
            traceback.print_exc()
            await query.message.reply_text(
                "❌ Произошла ошибка при ревью. Попробуйте позже."
            )
