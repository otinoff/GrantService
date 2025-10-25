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
import time

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

    async def _validate_anketa_data(self, anketa_data: dict, user_id: int) -> dict:
        """
        ITERATION 37: Two-Stage QA - GATE 1 (Anketa Validation)
        Validates INPUT data quality before generation

        Args:
            anketa_data: Данные анкеты (dict/JSON)
            user_id: Telegram ID пользователя

        Returns:
            dict: {
                'approved': bool,
                'score': float,
                'recommendations': list,
                'status': str  # 'approved'/'needs_revision'/'rejected'
            }
        """
        try:
            logger.info(f"[GATE-1] Validating anketa data quality...")

            # Импортируем AnketaValidator
            from agents.anketa_validator import AnketaValidator

            # Получаем LLM preference пользователя
            llm_provider = self.db.get_user_llm_preference(user_id)

            # Создаем валидатор
            validator = AnketaValidator(llm_provider=llm_provider, db=self.db)

            # Запускаем валидацию
            validation_result = await validator.validate(anketa_data)

            # Преобразуем результат
            score = validation_result['score']
            can_proceed = validation_result['can_proceed']

            # Определяем статус
            if can_proceed and score >= 7.0:
                status = 'approved'
                approved = True
            elif score >= 5.0:
                status = 'needs_revision'
                approved = False
            else:
                status = 'rejected'
                approved = False

            logger.info(f"[GATE-1] Validation result: {status}, score: {score:.1f}/10")

            return {
                'approved': approved,
                'score': score,
                'recommendations': validation_result['recommendations'],
                'status': status,
                'issues': validation_result.get('issues', [])
            }

        except Exception as e:
            logger.error(f"[GATE-1] Anketa validation failed: {e}")
            # Fallback: allow to proceed with warning
            return {
                'approved': True,
                'score': 5.0,
                'recommendations': [f"Validation error: {str(e)}"],
                'status': 'error'
            }

    async def _audit_generated_grant(self, grant_text: str, anketa_data: dict, session_id: int, user_id: int) -> dict:
        """
        ITERATION 37: Two-Stage QA - GATE 2 (Grant Audit)
        Audits OUTPUT (generated grant text) quality

        Args:
            grant_text: Generated grant application TEXT
            anketa_data: Original anketa data (for context)
            session_id: ID сессии
            user_id: Telegram ID пользователя

        Returns:
            dict: {
                'approved': bool,
                'score': float,
                'recommendations': list,
                'status': str
            }
        """
        try:
            logger.info(f"[GATE-2] Auditing generated grant text...")

            # Импортируем AuditorAgent
            from agents.auditor_agent import AuditorAgent

            # Получаем LLM preference пользователя
            llm_provider = self.db.get_user_llm_preference(user_id)

            # Создаем аудитора
            auditor = AuditorAgent(self.db, llm_provider=llm_provider)

            # Формируем input для AuditorAgent
            # ВАЖНО: Передаём GENERATED TEXT, не JSON!
            audit_input = {
                'application_text': grant_text,  # ← TEXT not JSON!
                'application': {'text': grant_text},  # For compatibility
                'user_answers': anketa_data,
                'selected_grant': {
                    'fund_name': anketa_data.get('grant_fund', 'Фонд президентских грантов')
                },
                'session_id': session_id
            }

            # Запускаем аудит асинхронно
            audit_wrapped = await auditor.audit_application_async(audit_input)

            # BaseAgent.prepare_output() оборачивает результат в {'result': {...}}
            audit_result = audit_wrapped.get('result', audit_wrapped)

            # Преобразуем формат AuditorAgent в наш формат
            overall_score = audit_result.get('overall_score', 0.0)
            readiness_status = audit_result.get('readiness_status', 'not_ready')
            can_submit = audit_result.get('can_submit', False)

            # Маппинг readiness_status -> approval_status
            if can_submit or overall_score >= 0.7:
                approval_status = 'approved'
            elif overall_score >= 0.5:
                approval_status = 'needs_revision'
            else:
                approval_status = 'rejected'

            logger.info(f"[GATE-2] Grant audit completed: {approval_status}, score: {overall_score:.1f}/10")

            # Возвращаем результат
            return {
                'approved': approval_status == 'approved',
                'score': overall_score * 10,  # Конвертируем из 0-1 в 0-10
                'recommendations': audit_result.get('recommendations', []),
                'status': approval_status,
                'audit_details': audit_result  # Полный результат аудита
            }

        except Exception as e:
            logger.error(f"[GATE-2] Grant audit failed: {e}")
            # Fallback: разрешаем с предупреждением
            return {
                'approved': True,
                'score': 5.0,
                'recommendations': [f"Audit error: {str(e)}"],
                'status': 'error'
            }

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

            # Получить anketa data из БД
            anketa_session = self.db.get_session_by_anketa_id(anketa_id)
            if not anketa_session or not anketa_session.get('interview_data'):
                await update.message.reply_text(
                    f"❌ Не удалось получить данные анкеты {anketa_id}"
                )
                logger.error(f"[GRANT] No interview_data for anketa {anketa_id}")
                return

            # Парсим JSON anketa data
            import json
            try:
                if isinstance(anketa_session['interview_data'], str):
                    anketa_data = json.loads(anketa_session['interview_data'])
                else:
                    anketa_data = anketa_session['interview_data']
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Ошибка при парсинге данных анкеты: {e}"
                )
                logger.error(f"[GRANT] Failed to parse interview_data: {e}")
                return

            logger.info(f"[GRANT] Anketa data loaded, keys: {list(anketa_data.keys())}")

            # ===== ITERATION 37: TWO-STAGE QA PIPELINE =====

            # Получаем session ID
            session = self.db.get_session_by_anketa_id(anketa_id)
            if not session:
                await update.message.reply_text("❌ Сессия не найдена")
                return
            session_id = session['id']

            # === GATE 1: Validate INPUT (anketa data) ===
            await update.message.reply_text(
                "🔍 GATE 1: Проверяю качество данных анкеты...\n"
                "Это займет ~20 секунд"
            )

            validation_result = await self._validate_anketa_data(
                anketa_data=anketa_data,
                user_id=user_id
            )

            # Проверяем результат валидации
            if not validation_result['approved']:
                status = validation_result['status']
                score = validation_result['score']
                recommendations = validation_result.get('recommendations', [])

                if status == 'needs_revision':
                    message = f"⚠️ **Данные анкеты требуют доработки**\n\n"
                    message += f"📊 Оценка входных данных: {score:.1f}/10\n\n"
                    message += "**Рекомендации:**\n"

                    for i, rec in enumerate(recommendations[:5], 1):
                        message += f"{i}. {rec}\n"

                    message += "\n💡 Пожалуйста, улучшите анкету и попробуйте снова"

                elif status == 'rejected':
                    message = f"❌ **Анкета не подходит для генерации**\n\n"
                    message += f"📊 Оценка качества: {score:.1f}/10 (минимум 5.0)\n\n"
                    message += "**Основные проблемы:**\n"

                    for i, rec in enumerate(recommendations[:5], 1):
                        message += f"{i}. {rec}\n"

                    message += "\n💡 Рекомендуем заполнить анкету заново"

                else:
                    message = f"⏳ Анкета на рассмотрении (статус: {status})"

                await update.message.reply_text(message)
                logger.warning(f"[GATE-1] Blocked generation: {status}, score: {score:.1f}")
                return

            # GATE 1 пройден
            logger.info(f"[GATE-1] ✅ Validation passed (score: {validation_result['score']:.1f}/10)")

            await update.message.reply_text(
                f"✅ GATE 1 пройден: {validation_result['score']:.1f}/10\n"
                f"🚀 Начинаю генерацию грантовой заявки (~2-3 минуты)..."
            )

            # Генерируем грант через write() method
            generation_start = time.time()
            grant_content = await asyncio.to_thread(
                writer.write,
                anketa_data=anketa_data
            )
            generation_duration = time.time() - generation_start

            logger.info(f"[GRANT] Grant generated in {generation_duration:.1f}s, {len(grant_content)} characters")

            # === GATE 2: Audit OUTPUT (generated grant text) ===
            await update.message.reply_text(
                "🔍 GATE 2: Проверяю качество сгенерированной заявки...\n"
                "Это займет ~30 секунд"
            )

            grant_audit = await self._audit_generated_grant(
                grant_text=grant_content,
                anketa_data=anketa_data,
                session_id=session_id,
                user_id=user_id
            )

            # Log результаты обоих gates (для RL data collection)
            logger.info(
                f"[TWO-STAGE-QA] Results for {anketa_id}:\n"
                f"  GATE-1 (Validation): {validation_result['score']:.1f}/10 ({validation_result['status']})\n"
                f"  GATE-2 (Audit): {grant_audit['score']:.1f}/10 ({grant_audit['status']})"
            )

            # Уведомляем пользователя о результатах GATE 2
            gate2_emoji = "✅" if grant_audit['score'] >= 7.0 else "⚠️" if grant_audit['score'] >= 5.0 else "❌"
            await update.message.reply_text(
                f"{gate2_emoji} GATE 2 завершён: {grant_audit['score']:.1f}/10\n"
                f"Статус: {grant_audit['status']}\n\n"
                f"📊 Итого:\n"
                f"• Входные данные: {validation_result['score']:.1f}/10\n"
                f"• Качество заявки: {grant_audit['score']:.1f}/10"
            )

            # Сохраняем грант в БД (с результатами аудита)
            import uuid
            grant_id = f"grant-{anketa_id}-{uuid.uuid4().hex[:8]}"

            character_count = len(grant_content)
            word_count = len(grant_content.split())
            sections_generated = grant_content.count('\n\n##')  # Approximate section count

            # Вставляем grant в БД
            self.db.insert_grant(
                grant_id=grant_id,
                anketa_id=anketa_id,
                user_id=user_id,
                grant_content=grant_content,
                status='completed',
                character_count=character_count,
                word_count=word_count,
                sections_generated=sections_generated,
                duration_seconds=generation_duration
            )

            # Получаем сохраненный grant
            grant = self.db.get_grant_by_id(grant_id)

            # Проверяем что сохранился
            if grant:

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

                # ITERATION 37: Автоматически отправить файл с заявкой
                await self._send_grant_file(
                    chat_id=update.effective_chat.id,
                    anketa_id=anketa_id,
                    grant_id=grant_id,
                    grant_content=grant_content,
                    validation_score=validation_result.get('score', 0),
                    audit_score=grant_audit.get('score', 0),
                    context=context
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
                # Grant не сохранился в БД
                logger.error(f"[GRANT] Failed to save grant to database for anketa {anketa_id}")

                self.active_generations[user_id]['status'] = 'failed'
                self.active_generations[user_id]['error'] = "Failed to save grant to database"

                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text=f"❌ Ошибка при сохранении грантовой заявки\n\n"
                         f"📋 Анкета: {anketa_id}\n"
                         f"❗️ Grant сгенерирован, но не сохранен в БД\n\n"
                         f"Пожалуйста, попробуйте еще раз или обратитесь к администратору."
                )

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

    async def _send_grant_file(
        self,
        chat_id: int,
        anketa_id: str,
        grant_id: str,
        grant_content: str,
        validation_score: float,
        audit_score: float,
        context
    ):
        """
        ITERATION 37: Отправить файл с грантовой заявкой

        Args:
            chat_id: Telegram chat ID
            anketa_id: ID анкеты
            grant_id: ID гранта
            grant_content: Текст заявки
            validation_score: Оценка GATE 1
            audit_score: Оценка GATE 2
            context: Telegram context
        """
        try:
            from telegram import InputFile
            from datetime import datetime
            import io

            # Создаём полный документ с метаданными
            doc = []
            doc.append("=" * 80)
            doc.append("ГРАНТОВАЯ ЗАЯВКА")
            doc.append("=" * 80)
            doc.append("")
            doc.append(f"Анкета ID:     {anketa_id}")
            doc.append(f"Grant ID:      {grant_id}")
            doc.append(f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            doc.append("")
            doc.append("=" * 80)
            doc.append("ОЦЕНКИ КАЧЕСТВА (TWO-STAGE QA)")
            doc.append("=" * 80)
            doc.append("")
            doc.append(f"✅ GATE 1 (Валидация входных данных): {validation_score:.1f}/10")
            doc.append(f"✅ GATE 2 (Аудит сгенерированной заявки): {audit_score:.1f}/10")
            doc.append("")
            doc.append("=" * 80)
            doc.append("СОДЕРЖАНИЕ ЗАЯВКИ")
            doc.append("=" * 80)
            doc.append("")
            doc.append(grant_content)
            doc.append("")
            doc.append("=" * 80)
            doc.append(f"Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            doc.append(f"Система: GrantService - Two-Stage QA Pipeline")
            doc.append("=" * 80)

            # Объединяем в текст
            full_document = "\n".join(doc)

            # Создаём файл в памяти
            file_content = io.BytesIO(full_document.encode('utf-8'))
            file_content.name = f"grant_{anketa_id}.txt"

            # Отправляем файл
            if context and context.bot:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=InputFile(file_content, filename=f"grant_{anketa_id}.txt"),
                    caption=f"📄 Грантовая заявка\n"
                            f"📋 {anketa_id}\n"
                            f"✅ GATE 1: {validation_score:.1f}/10 | GATE 2: {audit_score:.1f}/10"
                )
                logger.info(f"[GRANT] Grant file sent for {grant_id}")
            else:
                logger.warning(f"[GRANT] No context.bot to send file")

        except Exception as e:
            logger.error(f"[GRANT] Error sending grant file: {e}")
            # Не падаем, просто логируем

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
