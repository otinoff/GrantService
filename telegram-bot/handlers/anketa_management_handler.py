#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anketa Management Handler - Iteration 38

Управление анкетами пользователя:
- Просмотр списка анкет (/my_anketas)
- Удаление анкет с подтверждением (/delete_anketa)
- Аудит качества анкет (/audit_anketa)

Iteration 38 - Synthetic Corpus Generator:
- Генерация синтетических анкет (/generate_synthetic_anketa)
- Batch аудит анкет (/batch_audit_anketas)
- Статистика корпуса (/corpus_stats)

Author: Grant Service Architect Agent
Created: 2025-10-25
Version: 1.1 (Iteration 38)
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import json

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class AnketaManagementHandler:
    """
    Handler для управления анкетами пользователя

    Команды:
    - /my_anketas - список всех анкет пользователя
    - /delete_anketa - удаление анкеты с подтверждением
    - /audit_anketa - аудит качества анкеты

    Методология: Cradle OS - Immunity (Quality Control)
    """

    def __init__(self, db):
        """
        Инициализация handler

        Args:
            db: Database instance (GrantServiceDatabase)
        """
        self.db = db
        logger.info("[ANKETA] AnketaManagementHandler initialized")

    # ========== КОМАНДА: /my_anketas ==========

    async def my_anketas(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Показать список всех анкет пользователя

        Отображает:
        - Anketa ID
        - Дату создания
        - Статус аудита (если есть)
        - Оценку качества (если есть)
        - Кнопки действий (удалить, аудит)
        """
        user_id = update.effective_user.id

        logger.info(f"[ANKETA] User {user_id} requested anketa list")

        try:
            # Получить анкеты пользователя
            anketas = self.db.get_user_anketas(telegram_id=user_id, limit=10)

            if not anketas or len(anketas) == 0:
                await update.message.reply_text(
                    "📋 У вас пока нет завершенных анкет.\n\n"
                    "Используйте команду /start чтобы создать новую анкету."
                )
                return

            # Формируем сообщение
            message = f"📋 **Ваши анкеты** ({len(anketas)}):\n\n"

            for i, anketa in enumerate(anketas, 1):
                anketa_id = anketa.get('anketa_id', 'Unknown')
                completed_at = anketa.get('completed_at')
                audit_score = anketa.get('audit_score')
                audit_status = anketa.get('audit_status')

                # Форматируем дату
                if completed_at:
                    if isinstance(completed_at, str):
                        date_str = completed_at[:10]
                    else:
                        date_str = completed_at.strftime('%Y-%m-%d')
                else:
                    date_str = "Unknown"

                # Emoji для статуса
                status_emoji = self._get_status_emoji(audit_status)

                message += f"{i}. `{anketa_id}`\n"
                message += f"   📅 Создана: {date_str}\n"

                if audit_score is not None:
                    message += f"   {status_emoji} Аудит: {audit_score:.1f}/10 ({audit_status or 'unknown'})\n"
                else:
                    message += f"   ⏳ Аудит: не проведен\n"

                message += "\n"

            # Кнопки для действий
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Аудит анкеты", callback_data="anketa_audit_select"),
                    InlineKeyboardButton("🗑 Удалить анкету", callback_data="anketa_delete_select")
                ],
                [
                    InlineKeyboardButton("🔄 Обновить", callback_data="anketa_refresh")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

            logger.info(f"[ANKETA] Displayed {len(anketas)} anketas for user {user_id}")

        except Exception as e:
            logger.error(f"[ANKETA] Error getting anketas for user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при получении списка анкет.\n"
                "Пожалуйста, попробуйте позже."
            )

    # ========== КОМАНДА: /delete_anketa ==========

    async def delete_anketa(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Удалить анкету с подтверждением

        Процесс:
        1. Запросить anketa_id (или показать список)
        2. Показать предупреждение
        3. Запросить подтверждение
        4. Выполнить удаление (каскадное)
        """
        user_id = update.effective_user.id

        logger.info(f"[ANKETA] User {user_id} initiated anketa deletion")

        try:
            # Получить anketa_id из аргументов команды
            if context.args and len(context.args) > 0:
                anketa_id = context.args[0]

                # Проверить что анкета существует и принадлежит пользователю
                session = self.db.get_session_by_anketa_id(anketa_id)

                if not session:
                    await update.message.reply_text(
                        f"❌ Анкета `{anketa_id}` не найдена.",
                        parse_mode='Markdown'
                    )
                    return

                if session.get('telegram_id') != user_id:
                    await update.message.reply_text(
                        "❌ Эта анкета вам не принадлежит."
                    )
                    return

                # Показать подтверждение
                await self._confirm_delete(update, anketa_id)

            else:
                # Показать список анкет для выбора
                anketas = self.db.get_user_anketas(telegram_id=user_id, limit=10)

                if not anketas or len(anketas) == 0:
                    await update.message.reply_text(
                        "📋 У вас нет анкет для удаления."
                    )
                    return

                # Формируем кнопки для выбора
                keyboard = []
                for anketa in anketas[:5]:  # Показываем максимум 5
                    anketa_id = anketa.get('anketa_id', 'Unknown')
                    completed_at = anketa.get('completed_at')

                    if completed_at:
                        if isinstance(completed_at, str):
                            date_str = completed_at[:10]
                        else:
                            date_str = completed_at.strftime('%Y-%m-%d')
                    else:
                        date_str = "Unknown"

                    button_text = f"{anketa_id} ({date_str})"
                    callback_data = f"anketa_delete_confirm:{anketa_id}"

                    keyboard.append([
                        InlineKeyboardButton(button_text, callback_data=callback_data)
                    ])

                keyboard.append([
                    InlineKeyboardButton("❌ Отмена", callback_data="anketa_delete_cancel")
                ])

                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    "🗑 **Выберите анкету для удаления:**\n\n"
                    "⚠️ Внимание: Удаление приведет к удалению всех связанных данных "
                    "(аудиты, гранты, review).",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

        except Exception as e:
            logger.error(f"[ANKETA] Error initiating deletion for user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
            )

    async def _confirm_delete(self, update: Update, anketa_id: str):
        """Показать подтверждение удаления"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"anketa_delete_execute:{anketa_id}"),
                InlineKeyboardButton("❌ Отмена", callback_data="anketa_delete_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"⚠️ **Подтвердите удаление анкеты:**\n\n"
            f"`{anketa_id}`\n\n"
            f"Будут удалены:\n"
            f"• Данные анкеты\n"
            f"• Результаты аудита\n"
            f"• Сгенерированные гранты\n"
            f"• Все связанные review\n\n"
            f"**Это действие нельзя отменить!**"
        )

        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _execute_delete(self, query, anketa_id: str, user_id: int):
        """Выполнить удаление анкеты"""
        try:
            logger.info(f"[ANKETA] Executing deletion of {anketa_id} for user {user_id}")

            # Удаляем анкету
            success = self.db.delete_anketa(anketa_id=anketa_id, telegram_id=user_id)

            if success:
                await query.edit_message_text(
                    f"✅ Анкета `{anketa_id}` успешно удалена.\n\n"
                    f"Все связанные данные также удалены.",
                    parse_mode='Markdown'
                )
                logger.info(f"[ANKETA] Successfully deleted {anketa_id}")
            else:
                await query.edit_message_text(
                    f"❌ Не удалось удалить анкету `{anketa_id}`.\n"
                    f"Возможно, она уже удалена или не принадлежит вам.",
                    parse_mode='Markdown'
                )
                logger.warning(f"[ANKETA] Failed to delete {anketa_id}")

        except Exception as e:
            logger.error(f"[ANKETA] Error executing deletion of {anketa_id}: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при удалении анкеты.\n"
                "Пожалуйста, попробуйте позже."
            )

    # ========== КОМАНДА: /audit_anketa ==========

    async def audit_anketa(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Провести аудит качества анкеты

        Процесс:
        1. Выбрать anketa_id (или указать в команде)
        2. Запустить AuditorAgent
        3. Показать результаты аудита
        4. Дать рекомендации
        """
        user_id = update.effective_user.id

        logger.info(f"[ANKETA] User {user_id} initiated anketa audit")

        try:
            # Получить anketa_id из аргументов команды
            if context.args and len(context.args) > 0:
                anketa_id = context.args[0]

                # Проверить что анкета существует и принадлежит пользователю
                session = self.db.get_session_by_anketa_id(anketa_id)

                if not session:
                    await update.message.reply_text(
                        f"❌ Анкета `{anketa_id}` не найдена.",
                        parse_mode='Markdown'
                    )
                    return

                if session.get('telegram_id') != user_id:
                    await update.message.reply_text(
                        "❌ Эта анкета вам не принадлежит."
                    )
                    return

                # Запустить аудит
                await self._run_audit(update, anketa_id, session, context)

            else:
                # Показать список анкет для выбора
                anketas = self.db.get_user_anketas(telegram_id=user_id, limit=10)

                if not anketas or len(anketas) == 0:
                    await update.message.reply_text(
                        "📋 У вас нет анкет для аудита."
                    )
                    return

                # Формируем кнопки для выбора
                keyboard = []
                for anketa in anketas[:5]:  # Показываем максимум 5
                    anketa_id = anketa.get('anketa_id', 'Unknown')
                    audit_score = anketa.get('audit_score')

                    if audit_score is not None:
                        button_text = f"{anketa_id} (⭐ {audit_score:.1f}/10)"
                    else:
                        button_text = f"{anketa_id} (⏳ не проверен)"

                    callback_data = f"anketa_audit_run:{anketa_id}"

                    keyboard.append([
                        InlineKeyboardButton(button_text, callback_data=callback_data)
                    ])

                keyboard.append([
                    InlineKeyboardButton("❌ Отмена", callback_data="anketa_audit_cancel")
                ])

                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    "🔍 **Выберите анкету для аудита:**\n\n"
                    "Аудит проверит качество заполнения анкеты и даст рекомендации.",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

        except Exception as e:
            logger.error(f"[ANKETA] Error initiating audit for user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
            )

    async def _run_audit(self, update_or_query, anketa_id: str, session: Dict, context=None):
        """Запустить аудит анкеты"""
        try:
            # Определяем тип объекта (Update или CallbackQuery)
            is_query = hasattr(update_or_query, 'edit_message_text')

            # Отправляем уведомление о начале аудита
            if is_query:
                await update_or_query.edit_message_text(
                    f"🔍 Запускаю аудит анкеты `{anketa_id}`...\n\n"
                    f"Это займет ~30 секунд.",
                    parse_mode='Markdown'
                )
            else:
                msg = await update_or_query.message.reply_text(
                    f"🔍 Запускаю аудит анкеты `{anketa_id}`...\n\n"
                    f"Это займет ~30 секунд.",
                    parse_mode='Markdown'
                )

            logger.info(f"[ANKETA] Starting audit for {anketa_id}")

            # Проверяем есть ли уже аудит
            session_id = session.get('id')
            existing_audit = self.db.get_audit_by_session_id(session_id)

            if existing_audit:
                logger.info(f"[ANKETA] Found existing audit for {anketa_id}")
                audit_result = existing_audit
            else:
                # ITERATION 37: Two-Stage QA - Stage 1 (Anketa Validation)
                # Запускаем AnketaValidator для проверки качества ВХОДНЫХ ДАННЫХ
                from agents.anketa_validator import AnketaValidator

                # Получаем данные анкеты
                interview_data = session.get('interview_data')
                if isinstance(interview_data, str):
                    interview_data = json.loads(interview_data)

                # Получаем LLM preference
                user_id = session.get('telegram_id')
                llm_provider = self.db.get_user_llm_preference(user_id)

                # Создаем валидатор
                validator = AnketaValidator(llm_provider=llm_provider, db=self.db)

                # Запускаем валидацию (проверяет raw JSON anketa)
                validation_result = await validator.validate(interview_data)

                # Преобразуем формат AnketaValidator → формат для _format_audit_result
                # AnketaValidator возвращает: {score, valid, can_proceed, issues, recommendations}
                # _format_audit_result ожидает: {average_score, approval_status, recommendations}

                score = validation_result['score']

                # Определяем approval_status на основе score и can_proceed
                if validation_result['can_proceed'] and score >= 7.0:
                    approval_status = 'approved'
                elif score >= 5.0:
                    approval_status = 'needs_revision'
                else:
                    approval_status = 'rejected'

                audit_result = {
                    'average_score': score,
                    'approval_status': approval_status,
                    # AnketaValidator не возвращает детальные оценки - упрощаем
                    'completeness_score': int(score),
                    'clarity_score': 0,  # N/A for anketa validation
                    'feasibility_score': 0,  # N/A for anketa validation
                    'innovation_score': 0,  # N/A for anketa validation
                    'quality_score': int(score),
                    'recommendations': validation_result['recommendations'],
                    'issues': validation_result['issues']
                }

                logger.info(f"[ANKETA] Validation completed for {anketa_id}: status={approval_status}, score={score:.1f}/10")

            # Форматируем результаты
            message = self._format_audit_result(anketa_id, audit_result)

            # ITERATION 37: Отправляем результаты + файл
            if is_query:
                await update_or_query.edit_message_text(
                    message,
                    parse_mode='Markdown'
                )

                # Отправляем файл с полным отчётом
                await self._send_audit_report_file(
                    update_or_query.message.chat_id,
                    anketa_id,
                    audit_result,
                    validation_result if 'validation_result' in locals() else None,
                    context.bot if context else None
                )
            else:
                await msg.edit_text(
                    message,
                    parse_mode='Markdown'
                )

                # Отправляем файл с полным отчётом
                await self._send_audit_report_file(
                    msg.chat_id,
                    anketa_id,
                    audit_result,
                    validation_result if 'validation_result' in locals() else None,
                    context.bot if context else None
                )

        except Exception as e:
            logger.error(f"[ANKETA] Error running audit for {anketa_id}: {e}")

            error_msg = (
                f"❌ Произошла ошибка при аудите анкеты `{anketa_id}`.\n\n"
                f"Пожалуйста, попробуйте позже."
            )

            if is_query:
                await update_or_query.edit_message_text(error_msg, parse_mode='Markdown')
            else:
                await update_or_query.message.reply_text(error_msg, parse_mode='Markdown')

    async def _send_audit_report_file(self, chat_id: int, anketa_id: str, audit: Dict, validation_details: Dict = None, bot=None):
        """
        ITERATION 37: Отправить файл с результатами аудита

        Args:
            chat_id: Telegram chat ID
            anketa_id: ID анкеты
            audit: Результаты аудита
            validation_details: Детали валидации (если есть)
        """
        try:
            from telegram import InputFile
            from datetime import datetime
            import io

            # Создаём текстовый отчёт
            report = []
            report.append("=" * 60)
            report.append(f"ОТЧЁТ АУДИТА АНКЕТЫ")
            report.append("=" * 60)
            report.append(f"")
            report.append(f"Анкета ID: {anketa_id}")
            report.append(f"Дата аудита: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"")
            report.append("=" * 60)
            report.append("ОБЩИЕ РЕЗУЛЬТАТЫ")
            report.append("=" * 60)

            score = audit.get('average_score', 0.0)
            status = audit.get('approval_status', 'unknown')

            report.append(f"")
            report.append(f"Общая оценка: {score:.1f}/10")
            report.append(f"Статус: {self._get_status_text(status)}")
            report.append(f"")

            # Детальные оценки
            report.append("=" * 60)
            report.append("ДЕТАЛЬНЫЕ ОЦЕНКИ")
            report.append("=" * 60)
            report.append(f"")
            report.append(f"• Полнота:          {audit.get('completeness_score', 0)}/10")
            report.append(f"• Ясность:          {audit.get('clarity_score', 0)}/10")
            report.append(f"• Выполнимость:     {audit.get('feasibility_score', 0)}/10")
            report.append(f"• Инновационность:  {audit.get('innovation_score', 0)}/10")
            report.append(f"• Качество:         {audit.get('quality_score', 0)}/10")
            report.append(f"")

            # Рекомендации
            recommendations = audit.get('recommendations', [])
            if isinstance(recommendations, str):
                try:
                    recommendations = json.loads(recommendations)
                except:
                    recommendations = [recommendations]

            if recommendations and len(recommendations) > 0:
                report.append("=" * 60)
                report.append("РЕКОМЕНДАЦИИ")
                report.append("=" * 60)
                report.append(f"")
                for i, rec in enumerate(recommendations, 1):
                    report.append(f"{i}. {rec}")
                report.append(f"")

            # Проблемы (если есть)
            issues = audit.get('issues', [])
            if issues and len(issues) > 0:
                report.append("=" * 60)
                report.append("ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ")
                report.append("=" * 60)
                report.append(f"")
                for i, issue in enumerate(issues, 1):
                    report.append(f"{i}. {issue}")
                report.append(f"")

            # Детали валидации (если есть)
            if validation_details:
                report.append("=" * 60)
                report.append("ДЕТАЛИ ВАЛИДАЦИИ (GATE 1)")
                report.append("=" * 60)
                report.append(f"")
                report.append(f"Оценка входных данных: {validation_details.get('score', 0):.1f}/10")
                report.append(f"Можно продолжить: {'Да' if validation_details.get('can_proceed', False) else 'Нет'}")

                llm_assessment = validation_details.get('details', {}).get('llm_assessment', {})
                if llm_assessment:
                    report.append(f"")
                    report.append(f"LLM оценки:")
                    report.append(f"  • Проблема:     {llm_assessment.get('problem_score', 0)}/3")
                    report.append(f"  • Решение:      {llm_assessment.get('solution_score', 0)}/3")
                    report.append(f"  • Цели:         {llm_assessment.get('goals_score', 0)}/2")
                    report.append(f"  • Бюджет:       {llm_assessment.get('budget_score', 0)}/2")
                report.append(f"")

            # Заключение
            report.append("=" * 60)
            report.append("ЗАКЛЮЧЕНИЕ")
            report.append("=" * 60)
            report.append(f"")

            if status == 'approved':
                report.append("✅ Анкета готова для генерации гранта!")
            elif status == 'needs_revision':
                report.append("⚠️  Рекомендуется улучшить анкету перед генерацией гранта.")
            elif status == 'rejected':
                report.append("❌ Анкета не подходит для генерации гранта.")
                report.append("   Требуется серьезная доработка.")

            report.append(f"")
            report.append("=" * 60)
            report.append(f"Отчёт создан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"Система: GrantService - Two-Stage QA Pipeline")
            report.append("=" * 60)

            # Объединяем в текст
            report_text = "\n".join(report)

            # Создаём файл в памяти
            file_content = io.BytesIO(report_text.encode('utf-8'))
            file_content.name = f"audit_{anketa_id}.txt"

            # Отправляем
            if bot:
                await bot.send_document(
                    chat_id=chat_id,
                    document=InputFile(file_content, filename=f"audit_{anketa_id}.txt"),
                    caption=f"📄 Полный отчёт аудита анкеты {anketa_id}"
                )
            else:
                logger.warning(f"[ANKETA] No bot instance to send file")

            logger.info(f"[ANKETA] Audit report file sent for {anketa_id}")

        except Exception as e:
            logger.error(f"[ANKETA] Error sending audit report file: {e}")
            # Не падаем, просто логируем

    def _format_audit_result(self, anketa_id: str, audit: Dict) -> str:
        """Форматировать результаты аудита"""
        avg_score = audit.get('average_score', 0.0)
        status = audit.get('approval_status', 'unknown')

        completeness = audit.get('completeness_score', 0)
        clarity = audit.get('clarity_score', 0)
        feasibility = audit.get('feasibility_score', 0)
        innovation = audit.get('innovation_score', 0)
        quality = audit.get('quality_score', 0)

        recommendations = audit.get('recommendations', [])
        if isinstance(recommendations, str):
            try:
                recommendations = json.loads(recommendations)
            except:
                recommendations = []

        # Emoji для статуса
        status_emoji = self._get_status_emoji(status)

        # Заголовок
        message = f"📊 **Результаты аудита анкеты**\n\n"
        message += f"`{anketa_id}`\n\n"

        # Общая оценка
        message += f"{status_emoji} **Общая оценка:** {avg_score:.1f}/10\n"
        message += f"**Статус:** {self._get_status_text(status)}\n\n"

        # Детальные оценки
        message += f"**Детальные оценки:**\n"
        message += f"• Полнота: {completeness}/10\n"
        message += f"• Ясность: {clarity}/10\n"
        message += f"• Выполнимость: {feasibility}/10\n"
        message += f"• Инновационность: {innovation}/10\n"
        message += f"• Качество: {quality}/10\n\n"

        # Рекомендации
        if recommendations and len(recommendations) > 0:
            message += f"**Рекомендации:**\n"
            for i, rec in enumerate(recommendations[:5], 1):
                message += f"{i}. {rec}\n"
            message += "\n"

        # Заключение
        if status == 'approved':
            message += "✅ Анкета готова для генерации гранта!"
        elif status == 'needs_revision':
            message += "⚠️ Рекомендуется улучшить анкету перед генерацией гранта."
        elif status == 'rejected':
            message += "❌ Анкета не подходит для генерации гранта. Требуется серьезная доработка."
        else:
            message += f"ℹ️ Статус: {status}"

        return message

    # ========== CALLBACK HANDLER ==========

    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик callback кнопок

        Callback patterns:
        - anketa_audit_select - выбор анкеты для аудита
        - anketa_audit_run:<anketa_id> - запуск аудита
        - anketa_audit_cancel - отмена аудита
        - anketa_delete_select - выбор анкеты для удаления
        - anketa_delete_confirm:<anketa_id> - подтверждение удаления
        - anketa_delete_execute:<anketa_id> - выполнение удаления
        - anketa_delete_cancel - отмена удаления
        - anketa_refresh - обновление списка
        """
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        data = query.data

        logger.info(f"[ANKETA] Callback from user {user_id}: {data}")

        try:
            # Аудит
            if data == "anketa_audit_select":
                # Показать список анкет для аудита
                anketas = self.db.get_user_anketas(telegram_id=user_id, limit=10)

                if not anketas or len(anketas) == 0:
                    await query.edit_message_text("📋 У вас нет анкет для аудита.")
                    return

                keyboard = []
                for anketa in anketas[:5]:
                    anketa_id = anketa.get('anketa_id', 'Unknown')
                    audit_score = anketa.get('audit_score')

                    if audit_score is not None:
                        button_text = f"{anketa_id} (⭐ {audit_score:.1f}/10)"
                    else:
                        button_text = f"{anketa_id} (⏳ не проверен)"

                    keyboard.append([
                        InlineKeyboardButton(button_text, callback_data=f"anketa_audit_run:{anketa_id}")
                    ])

                keyboard.append([
                    InlineKeyboardButton("❌ Отмена", callback_data="anketa_audit_cancel")
                ])

                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    "🔍 **Выберите анкету для аудита:**",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

            elif data.startswith("anketa_audit_run:"):
                anketa_id = data.split(":", 1)[1]

                # Получаем сессию
                session = self.db.get_session_by_anketa_id(anketa_id)

                if not session:
                    await query.edit_message_text(
                        f"❌ Анкета `{anketa_id}` не найдена.",
                        parse_mode='Markdown'
                    )
                    return

                if session.get('telegram_id') != user_id:
                    await query.edit_message_text("❌ Эта анкета вам не принадлежит.")
                    return

                # Запускаем аудит
                await self._run_audit(query, anketa_id, session, context)

            elif data == "anketa_audit_cancel":
                await query.edit_message_text("❌ Аудит отменен.")

            # Удаление
            elif data == "anketa_delete_select":
                # Показать список анкет для удаления
                anketas = self.db.get_user_anketas(telegram_id=user_id, limit=10)

                if not anketas or len(anketas) == 0:
                    await query.edit_message_text("📋 У вас нет анкет для удаления.")
                    return

                keyboard = []
                for anketa in anketas[:5]:
                    anketa_id = anketa.get('anketa_id', 'Unknown')
                    completed_at = anketa.get('completed_at')

                    if completed_at:
                        if isinstance(completed_at, str):
                            date_str = completed_at[:10]
                        else:
                            date_str = completed_at.strftime('%Y-%m-%d')
                    else:
                        date_str = "Unknown"

                    button_text = f"{anketa_id} ({date_str})"

                    keyboard.append([
                        InlineKeyboardButton(button_text, callback_data=f"anketa_delete_confirm:{anketa_id}")
                    ])

                keyboard.append([
                    InlineKeyboardButton("❌ Отмена", callback_data="anketa_delete_cancel")
                ])

                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    "🗑 **Выберите анкету для удаления:**\n\n"
                    "⚠️ Внимание: Удаление приведет к удалению всех связанных данных.",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

            elif data.startswith("anketa_delete_confirm:"):
                anketa_id = data.split(":", 1)[1]

                # Показываем подтверждение
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Да, удалить", callback_data=f"anketa_delete_execute:{anketa_id}"),
                        InlineKeyboardButton("❌ Отмена", callback_data="anketa_delete_cancel")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                message = (
                    f"⚠️ **Подтвердите удаление:**\n\n"
                    f"`{anketa_id}`\n\n"
                    f"**Это действие нельзя отменить!**"
                )

                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

            elif data.startswith("anketa_delete_execute:"):
                anketa_id = data.split(":", 1)[1]

                # Выполняем удаление
                await self._execute_delete(query, anketa_id, user_id)

            elif data == "anketa_delete_cancel":
                await query.edit_message_text("❌ Удаление отменено.")

            # Обновление
            elif data == "anketa_refresh":
                # Обновляем список анкет
                anketas = self.db.get_user_anketas(telegram_id=user_id, limit=10)

                if not anketas or len(anketas) == 0:
                    await query.edit_message_text(
                        "📋 У вас пока нет завершенных анкет."
                    )
                    return

                message = f"📋 **Ваши анкеты** ({len(anketas)}):\n\n"

                for i, anketa in enumerate(anketas, 1):
                    anketa_id = anketa.get('anketa_id', 'Unknown')
                    completed_at = anketa.get('completed_at')
                    audit_score = anketa.get('audit_score')
                    audit_status = anketa.get('audit_status')

                    if completed_at:
                        if isinstance(completed_at, str):
                            date_str = completed_at[:10]
                        else:
                            date_str = completed_at.strftime('%Y-%m-%d')
                    else:
                        date_str = "Unknown"

                    status_emoji = self._get_status_emoji(audit_status)

                    message += f"{i}. `{anketa_id}`\n"
                    message += f"   📅 Создана: {date_str}\n"

                    if audit_score is not None:
                        message += f"   {status_emoji} Аудит: {audit_score:.1f}/10 ({audit_status or 'unknown'})\n"
                    else:
                        message += f"   ⏳ Аудит: не проведен\n"

                    message += "\n"

                keyboard = [
                    [
                        InlineKeyboardButton("🔍 Аудит", callback_data="anketa_audit_select"),
                        InlineKeyboardButton("🗑 Удалить", callback_data="anketa_delete_select")
                    ],
                    [
                        InlineKeyboardButton("🔄 Обновить", callback_data="anketa_refresh")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

        except Exception as e:
            logger.error(f"[ANKETA] Error handling callback {data}: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
            )

    # ========== КОМАНДА: /create_test_anketa ==========

    async def create_test_anketa(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Создать тестовую анкету для проверки функционала

        Быстрая команда для тестирования Iteration 35
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name

        logger.info(f"[ANKETA] User {user_id} creating test anketa")

        try:
            await update.message.reply_text("🔧 Создаю тестовую анкету...")

            # Генерируем anketa_id
            user_data = {
                'telegram_id': user_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name
            }

            anketa_id = self.db.generate_anketa_id(user_data)

            # Тестовые данные анкеты (реалистичные)
            test_interview_data = {
                "project_name": "Молодежный образовательный центр 'Цифровое будущее'",
                "organization": "АНО 'Развитие молодежных инициатив'",
                "organization_type": "Автономная некоммерческая организация",
                "region": "Кемеровская область - Кузбасс",
                "city": "Кемерово",
                "target_audience": "Молодежь 14-25 лет, интересующаяся IT-технологиями",
                "target_count": "150 человек в год",

                "problem": "В регионе отсутствуют доступные образовательные программы по современным IT-направлениям для молодежи. Более 70% выпускников школ не имеют базовых навыков программирования, что снижает их конкурентоспособность на рынке труда.",

                "solution": "Создание бесплатного образовательного центра с курсами по программированию, веб-разработке, дизайну и цифровому маркетингу. Занятия будут проводиться опытными специалистами в современно оборудованных классах.",

                "goals": [
                    "Обучить 150 молодых людей основам программирования и IT-технологий",
                    "Создать 5 учебных программ по различным направлениям",
                    "Организовать 30 мастер-классов от ведущих специалистов отрасли",
                    "Помочь 50 выпускникам найти работу или стажировку в IT-компаниях"
                ],

                "activities": [
                    "Разработка образовательных программ и методических материалов",
                    "Набор и обучение преподавателей",
                    "Проведение регулярных курсов и мастер-классов",
                    "Организация хакатонов и конкурсов проектов",
                    "Карьерное консультирование и помощь в трудоустройстве"
                ],

                "results": [
                    "150 обученных молодых специалистов",
                    "5 новых образовательных программ",
                    "30 проведенных мастер-классов",
                    "50 трудоустроенных выпускников",
                    "Создание сообщества IT-специалистов региона"
                ],

                "budget": "850000",
                "budget_breakdown": {
                    "equipment": "300000 руб - компьютеры и оборудование",
                    "rent": "200000 руб - аренда помещения на год",
                    "salaries": "250000 руб - оплата преподавателей",
                    "materials": "100000 руб - учебные материалы"
                },

                "timeline": "12 месяцев",
                "team": "Руководитель проекта, 3 преподавателя, методист, координатор",

                "experience": "Организация имеет 3-летний опыт проведения образовательных программ для молодежи. Ранее успешно реализованы 2 проекта с охватом более 200 участников.",

                "sustainability": "После окончания проекта центр продолжит работу на платной основе для корпоративных клиентов, что позволит сохранить бесплатные программы для молодежи.",

                "innovation": "Использование современных методик обучения, включая проектно-ориентированный подход и менторство от действующих специалистов крупных IT-компаний.",

                "social_impact": "Повышение цифровой грамотности молодежи региона, создание возможностей для карьерного роста, снижение молодежной безработицы."
            }

            # Создаем сессию
            # Проверяем есть ли активная сессия
            existing_sessions = self.db.get_user_sessions(telegram_id=user_id, limit=1)

            if existing_sessions and len(existing_sessions) > 0:
                latest_session = existing_sessions[0]
                if latest_session.get('status') == 'active':
                    # Обновляем существующую активную сессию
                    session_id = latest_session['id']
                else:
                    # Создаем новую сессию
                    session_id = self.db.create_session(telegram_id=user_id)
            else:
                # Создаем новую сессию
                session_id = self.db.create_session(telegram_id=user_id)

            # Сохраняем анкету через save_anketa
            anketa_data = {
                'user_data': user_data,
                'interview_data': test_interview_data,
                'session_id': session_id
            }

            saved_anketa_id = self.db.save_anketa(anketa_data)

            if saved_anketa_id:
                message = (
                    f"✅ **Тестовая анкета создана!**\n\n"
                    f"📋 Anketa ID: `{saved_anketa_id}`\n"
                    f"📊 Проект: {test_interview_data['project_name']}\n"
                    f"💰 Бюджет: {test_interview_data['budget']} руб\n\n"
                    f"**Теперь можно тестировать:**\n"
                    f"• /my\\_anketas - просмотр\n"
                    f"• /audit\\_anketa - аудит качества\n"
                    f"• /generate\\_grant - генерация гранта\n"
                    f"• /delete\\_anketa - удаление"
                )

                await update.message.reply_text(message, parse_mode='Markdown')
                logger.info(f"[ANKETA] Test anketa created: {saved_anketa_id}")
            else:
                await update.message.reply_text(
                    "❌ Ошибка при создании тестовой анкеты.\n"
                    "Проверьте логи для деталей."
                )
                logger.error(f"[ANKETA] Failed to save test anketa")

        except Exception as e:
            logger.error(f"[ANKETA] Error creating test anketa for user {user_id}: {e}")
            await update.message.reply_text(
                f"❌ Произошла ошибка при создании тестовой анкеты:\n{str(e)}"
            )

    # ========== ITERATION 38: SYNTHETIC CORPUS GENERATOR ==========

    async def generate_synthetic_anketa(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        ITERATION 38: Генерация синтетических анкет для корпуса

        Usage: /generate_synthetic_anketa [count] [quality]

        Examples:
        - /generate_synthetic_anketa 10 medium
        - /generate_synthetic_anketa 5 high
        - /generate_synthetic_anketa 1 low

        Args:
            count: 1-100 (default: 10)
            quality: low/medium/high (default: random mix)
        """
        user_id = update.effective_user.id

        # Parse arguments
        args = context.args
        count = 10  # default
        quality_level = None  # random mix

        if len(args) >= 1:
            try:
                count = int(args[0])
                if count < 1 or count > 100:
                    await update.message.reply_text(
                        "❌ Количество должно быть от 1 до 100"
                    )
                    return
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверный формат количества. Используйте число от 1 до 100."
                )
                return

        if len(args) >= 2:
            quality_level = args[1].lower()
            if quality_level not in ['low', 'medium', 'high']:
                await update.message.reply_text(
                    "❌ Качество должно быть: low, medium или high"
                )
                return

        logger.info(f"[SYNTHETIC] User {user_id} requested {count} synthetic anketas (quality: {quality_level or 'mixed'})")

        try:
            # Import generator
            from agents.anketa_synthetic_generator import AnketaSyntheticGenerator

            # Get LLM model (use GigaChat for Lite - token economy)
            llm_model = 'GigaChat'  # Lite model, hardcoded for Iteration 38

            # Initialize generator
            generator = AnketaSyntheticGenerator(
                db=self.db,
                llm_model=llm_model
            )

            # Get template anketas from database
            template_anketas = self.db.get_user_anketas(telegram_id=user_id, limit=5)

            if not template_anketas or len(template_anketas) == 0:
                await update.message.reply_text(
                    "❌ Не найдено реальных анкет для использования как шаблоны.\n\n"
                    "Сначала создайте хотя бы одну анкету через /start"
                )
                return

            # Show progress
            await update.message.reply_text(
                f"🔄 Генерирую {count} синтетических анкет...\n"
                f"💡 Используется: {llm_provider.upper()}\n"
                f"📊 Качество: {quality_level or 'mixed (20% low, 50% medium, 30% high)'}\n\n"
                f"⏱️ Примерное время: ~{count * 15} секунд"
            )

            # Generate batch
            if quality_level:
                # Single quality level
                generated = []
                for i in range(count):
                    anketa = await generator.generate_synthetic_anketa(
                        template_anketas=template_anketas,
                        quality_level=quality_level
                    )
                    generated.append(anketa)

                    # Progress update every 10 anketas
                    if (i + 1) % 10 == 0:
                        await update.message.reply_text(
                            f"⏳ Прогресс: {i + 1}/{count} анкет сгенерировано..."
                        )
            else:
                # Mixed quality distribution
                generated = await generator.generate_batch(
                    template_anketas=template_anketas,
                    count=count
                )

            # Save to database
            saved_count = 0
            for anketa in generated:
                # Create session for each synthetic anketa
                session_id = self.db.create_session(telegram_id=user_id)

                # Prepare anketa data
                anketa_data = {
                    'user_data': {
                        'telegram_id': user_id,
                        'username': update.effective_user.username or 'synthetic_user'
                    },
                    'interview_data': anketa,
                    'session_id': session_id
                }

                # Save
                saved_anketa_id = self.db.save_anketa(anketa_data)
                if saved_anketa_id:
                    saved_count += 1

                    # TODO: Add to Qdrant (Phase 4)
                    # await self._add_to_qdrant(saved_anketa_id, anketa)

            # Calculate token usage estimate
            tokens_used = count * 1500  # ~1500 tokens per anketa (Lite)

            # Success message
            await update.message.reply_text(
                f"✅ **Синтетические анкеты созданы!**\n\n"
                f"📊 Статистика:\n"
                f"• Сгенерировано: {len(generated)} анкет\n"
                f"• Сохранено в БД: {saved_count} анкет\n"
                f"• Использовано токенов: ~{tokens_used:,} (GigaChat Lite)\n\n"
                f"**Качество:**\n"
                f"• Low: {sum(1 for a in generated if a.get('quality_target') == 'low')} анкет\n"
                f"• Medium: {sum(1 for a in generated if a.get('quality_target') == 'medium')} анкет\n"
                f"• High: {sum(1 for a in generated if a.get('quality_target') == 'high')} анкет\n\n"
                f"Используйте /corpus_stats для общей статистики",
                parse_mode='Markdown'
            )

            logger.info(f"[SYNTHETIC] Generated {saved_count} synthetic anketas using ~{tokens_used} Lite tokens")

        except Exception as e:
            logger.error(f"[SYNTHETIC] Error generating synthetic anketas: {e}")
            await update.message.reply_text(
                f"❌ Произошла ошибка при генерации:\n{str(e)}"
            )

    async def batch_audit_anketas(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        ITERATION 38: Batch аудит анкет с использованием GigaChat Max

        Usage: /batch_audit_anketas [count]

        Examples:
        - /batch_audit_anketas 10
        - /batch_audit_anketas 100

        ВАЖНО: Использует GigaChat Max (~2000 tokens/anketa)
        Это критично для демонстрации Sber500!

        Args:
            count: 1-500 (default: 10)
        """
        user_id = update.effective_user.id

        # Parse arguments
        args = context.args
        count = 10  # default

        if len(args) >= 1:
            try:
                count = int(args[0])
                if count < 1 or count > 500:
                    await update.message.reply_text(
                        "❌ Количество должно быть от 1 до 500"
                    )
                    return
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверный формат количества. Используйте число от 1 до 500."
                )
                return

        logger.info(f"[BATCH-AUDIT] User {user_id} requested batch audit of {count} anketas")

        try:
            # Get anketas to audit (prefer synthetic ones without audit)
            from shared.database import GrantServiceDatabase

            # Query: Get anketas without audit_score, prioritize synthetic
            anketas = self.db.get_user_anketas(telegram_id=user_id, limit=count * 2)  # Get more to filter

            # Filter: No audit yet
            unaudited = [a for a in anketas if not a.get('audit_score')]

            if len(unaudited) == 0:
                await update.message.reply_text(
                    "❌ Нет анкет для аудита.\n\n"
                    "Все ваши анкеты уже проверены."
                )
                return

            # Limit to requested count
            to_audit = unaudited[:count]

            # Calculate token estimate
            tokens_estimate = len(to_audit) * 2000  # ~2000 Max tokens per audit

            # Show progress
            await update.message.reply_text(
                f"🔄 Запускаю batch аудит {len(to_audit)} анкет...\n"
                f"💡 Используется: **GigaChat Max** (критично для Sber500!)\n"
                f"📊 Ожидаемое использование: ~{tokens_estimate:,} Max tokens\n\n"
                f"⏱️ Примерное время: ~{len(to_audit) * 30} секунд",
                parse_mode='Markdown'
            )

            # Import validator (GATE 1 - validates JSON)
            from agents.anketa_validator import AnketaValidator

            # Use GigaChat Max for quality assurance
            llm_provider = 'gigachat'  # GigaChat Max

            validator = AnketaValidator(
                llm_provider=llm_provider,
                db=self.db
            )

            # Audit each anketa
            results = []
            audited_count = 0

            for i, anketa in enumerate(to_audit, 1):
                anketa_id = anketa.get('anketa_id')

                try:
                    # Get interview data
                    session = self.db.get_session_by_anketa_id(anketa_id)
                    if not session:
                        logger.warning(f"[BATCH-AUDIT] No session for anketa {anketa_id}")
                        continue

                    interview_data = session.get('interview_data')
                    if isinstance(interview_data, str):
                        interview_data = json.loads(interview_data)

                    # Run validation (GATE 1)
                    validation_result = await validator.validate(interview_data)

                    score = validation_result['score']

                    # Determine status
                    if validation_result['can_proceed'] and score >= 7.0:
                        status = 'approved'
                    elif score >= 5.0:
                        status = 'needs_revision'
                    else:
                        status = 'rejected'

                    # Update database
                    self.db.update_anketa_audit(
                        anketa_id=anketa_id,
                        audit_score=score,
                        audit_status=status,
                        audit_recommendations=validation_result.get('recommendations', [])
                    )

                    results.append({
                        'anketa_id': anketa_id,
                        'score': score,
                        'status': status
                    })

                    audited_count += 1

                    # Progress update every 10 anketas
                    if i % 10 == 0:
                        await update.message.reply_text(
                            f"⏳ Прогресс: {i}/{len(to_audit)} анкет проверено..."
                        )

                except Exception as e:
                    logger.error(f"[BATCH-AUDIT] Error auditing {anketa_id}: {e}")
                    continue

            # Calculate actual token usage
            actual_tokens = audited_count * 2000

            # Statistics
            approved = sum(1 for r in results if r['status'] == 'approved')
            needs_revision = sum(1 for r in results if r['status'] == 'needs_revision')
            rejected = sum(1 for r in results if r['status'] == 'rejected')

            avg_score = sum(r['score'] for r in results) / len(results) if results else 0

            # Success message
            await update.message.reply_text(
                f"✅ **Batch аудит завершён!**\n\n"
                f"📊 Результаты:\n"
                f"• Проверено: {audited_count} анкет\n"
                f"• Средний балл: {avg_score:.1f}/10\n\n"
                f"**Распределение:**\n"
                f"• ✅ Одобрено (≥7.0): {approved}\n"
                f"• ⚠️ Требует доработки (5.0-6.9): {needs_revision}\n"
                f"• ❌ Отклонено (<5.0): {rejected}\n\n"
                f"**Токены:**\n"
                f"• Использовано: ~{actual_tokens:,} Max tokens\n"
                f"• Стоимость: ~{actual_tokens / 1000:.1f} руб (из 1,987,948 доступных)\n\n"
                f"💡 Отлично для демонстрации Sber500!",
                parse_mode='Markdown'
            )

            logger.info(f"[BATCH-AUDIT] Audited {audited_count} anketas using ~{actual_tokens} Max tokens")

        except Exception as e:
            logger.error(f"[BATCH-AUDIT] Error in batch audit: {e}")
            await update.message.reply_text(
                f"❌ Произошла ошибка при batch аудите:\n{str(e)}"
            )

    async def corpus_stats(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        ITERATION 38: Показать статистику корпуса анкет

        Usage: /corpus_stats

        Показывает:
        - Общее количество анкет (реальных и синтетических)
        - Распределение по качеству
        - Распределение по статусам аудита
        - Использование токенов
        """
        user_id = update.effective_user.id

        logger.info(f"[CORPUS] User {user_id} requested corpus statistics")

        try:
            # Get all anketas
            all_anketas = self.db.get_user_anketas(telegram_id=user_id, limit=1000)

            if not all_anketas or len(all_anketas) == 0:
                await update.message.reply_text(
                    "📊 Корпус пуст.\n\n"
                    "Используйте /start для создания реальных анкет\n"
                    "или /generate_synthetic_anketa для синтетических."
                )
                return

            # Count synthetic vs real
            synthetic_count = 0
            real_count = 0

            for anketa in all_anketas:
                anketa_id = anketa.get('anketa_id')
                session = self.db.get_session_by_anketa_id(anketa_id)

                if session:
                    interview_data = session.get('interview_data')
                    if isinstance(interview_data, str):
                        interview_data = json.loads(interview_data)

                    if interview_data and interview_data.get('synthetic'):
                        synthetic_count += 1
                    else:
                        real_count += 1

            # Audit statistics
            audited = [a for a in all_anketas if a.get('audit_score')]
            unaudited = [a for a in all_anketas if not a.get('audit_score')]

            # Quality distribution (for audited)
            approved = sum(1 for a in audited if a.get('audit_status') == 'approved')
            needs_revision = sum(1 for a in audited if a.get('audit_status') == 'needs_revision')
            rejected = sum(1 for a in audited if a.get('audit_status') == 'rejected')

            # Average score
            avg_score = sum(a.get('audit_score', 0) for a in audited) / len(audited) if audited else 0

            # Token estimates
            # Synthetic generation: 1500 Lite tokens each
            # Batch audit: 2000 Max tokens each
            estimated_lite_tokens = synthetic_count * 1500
            estimated_max_tokens = len(audited) * 2000

            # Build message
            message = (
                f"📊 **Статистика корпуса анкет**\n\n"
                f"**Общее количество:** {len(all_anketas)}\n"
                f"• Реальные: {real_count}\n"
                f"• Синтетические: {synthetic_count}\n\n"
                f"**Аудит:**\n"
                f"• Проверено: {len(audited)}\n"
                f"• Не проверено: {len(unaudited)}\n"
                f"• Средний балл: {avg_score:.1f}/10\n\n"
                f"**Качество (проверенные):**\n"
                f"• ✅ Одобрено: {approved}\n"
                f"• ⚠️ Требует доработки: {needs_revision}\n"
                f"• ❌ Отклонено: {rejected}\n\n"
                f"**Использование токенов:**\n"
                f"• GigaChat Lite: ~{estimated_lite_tokens:,}\n"
                f"• GigaChat Max: ~{estimated_max_tokens:,}\n\n"
                f"💡 Используйте:\n"
                f"• /generate_synthetic_anketa [N] - создать ещё\n"
                f"• /batch_audit_anketas [N] - проверить качество"
            )

            await update.message.reply_text(message, parse_mode='Markdown')

            logger.info(
                f"[CORPUS] Stats: {len(all_anketas)} total "
                f"({real_count} real, {synthetic_count} synthetic, "
                f"{len(audited)} audited)"
            )

        except Exception as e:
            logger.error(f"[CORPUS] Error getting corpus stats: {e}")
            await update.message.reply_text(
                f"❌ Произошла ошибка при получении статистики:\n{str(e)}"
            )

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========

    def _get_status_emoji(self, status: Optional[str]) -> str:
        """Получить emoji для статуса аудита"""
        if status == 'approved':
            return "✅"
        elif status == 'needs_revision':
            return "⚠️"
        elif status == 'rejected':
            return "❌"
        elif status == 'pending':
            return "⏳"
        else:
            return "❓"

    def _get_status_text(self, status: Optional[str]) -> str:
        """Получить текстовое описание статуса"""
        if status == 'approved':
            return "Одобрена ✅"
        elif status == 'needs_revision':
            return "Требует доработки ⚠️"
        elif status == 'rejected':
            return "Отклонена ❌"
        elif status == 'pending':
            return "На рассмотрении ⏳"
        else:
            return f"Неизвестно ({status})"
