"""
Модуль для отправки уведомлений администраторам о новых заявках
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

# ID группы администраторов
ADMIN_GROUP_ID = -4930683040  # Отрицательный ID для группы

class AdminNotifier:
    """Класс для отправки уведомлений администраторам"""

    def __init__(self, bot_token: str):
        """
        Инициализация нотификатора

        Args:
            bot_token: Токен Telegram бота
        """
        self.bot = Bot(token=bot_token)
        self.admin_group_id = ADMIN_GROUP_ID

    async def send_new_application_notification(
        self,
        application_data: Dict[str, Any],
        user_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Отправить уведомление о новой заявке в группу администраторов

        Args:
            application_data: Данные заявки
            user_data: Данные пользователя

        Returns:
            True если уведомление отправлено успешно
        """
        try:
            # Формируем текст уведомления
            message = self._format_notification(application_data, user_data)

            # Отправляем сообщение в группу
            await self.bot.send_message(
                chat_id=self.admin_group_id,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            logger.info(f"✅ Уведомление о заявке {application_data.get('application_number')} отправлено в группу админов")
            return True

        except TelegramError as e:
            logger.error(f"❌ Ошибка отправки уведомления в Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при отправке уведомления: {e}")
            return False

    def _format_notification(
        self,
        application_data: Dict[str, Any],
        user_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Форматировать текст уведомления

        Args:
            application_data: Данные заявки
            user_data: Данные пользователя

        Returns:
            Отформатированный текст уведомления
        """
        # Извлекаем основные данные
        app_number = application_data.get('application_number', 'Не указан')
        title = application_data.get('title') or 'Без названия'
        created_at = application_data.get('created_at') or datetime.now().isoformat()

        # Пробуем получить дополнительную информацию
        grant_fund = application_data.get('grant_fund') or 'Не указан'
        requested_amount = application_data.get('requested_amount') or 0
        project_duration = application_data.get('project_duration') or 0

        # Информация о пользователе
        user_info = "Неизвестный пользователь"
        if user_data:
            username = user_data.get('username', '')
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            telegram_id = user_data.get('telegram_id', '')

            user_parts = []
            if first_name:
                user_parts.append(first_name)
            if last_name:
                user_parts.append(last_name)
            if username:
                user_parts.append(f"@{username}")
            if telegram_id:
                user_parts.append(f"ID: {telegram_id}")

            if user_parts:
                user_info = " ".join(user_parts)

        # Форматируем сумму
        if requested_amount > 0:
            amount_str = f"{requested_amount:,.0f}".replace(',', ' ') + " ₽"
        else:
            amount_str = "Не указана"

        # Формируем сообщение
        message_lines = [
            "🎯 <b>НОВАЯ ЗАЯВКА НА ГРАНТ</b>",
            "",
            f"📋 <b>Номер заявки:</b> <code>{app_number}</code>",
            f"📝 <b>Название проекта:</b> {title}",
            f"👤 <b>Пользователь:</b> {user_info}",
            "",
            f"🏛 <b>Фонд:</b> {grant_fund}",
            f"💰 <b>Запрашиваемая сумма:</b> {amount_str}",
            f"📅 <b>Срок реализации:</b> {project_duration} мес.",
            "",
            f"🕐 <b>Время создания:</b> {created_at}",
            "",
            "➡️ <b>Действия:</b>",
            "• Откройте админ-панель для просмотра полной заявки",
            "• Проверьте качество заполнения",
            "• При необходимости свяжитесь с пользователем",
            "",
            "#новая_заявка #грант"
        ]

        return "\n".join(message_lines)

    def send_notification_sync(
        self,
        application_data: Dict[str, Any],
        user_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Синхронная обертка для отправки уведомления

        Args:
            application_data: Данные заявки
            user_data: Данные пользователя

        Returns:
            True если уведомление отправлено успешно
        """
        try:
            # Создаем новый event loop если его нет
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Запускаем асинхронную функцию
            if loop.is_running():
                # Если loop уже запущен, создаем задачу
                task = asyncio.create_task(
                    self.send_new_application_notification(application_data, user_data)
                )
                return True  # Возвращаем True, т.к. задача создана
            else:
                # Если loop не запущен, запускаем синхронно
                return loop.run_until_complete(
                    self.send_new_application_notification(application_data, user_data)
                )

        except Exception as e:
            logger.error(f"❌ Ошибка в синхронной обертке: {e}")
            return False


def get_notifier(bot_token: str = None) -> Optional[AdminNotifier]:
    """
    Получить экземпляр нотификатора

    Args:
        bot_token: Токен бота (если не указан, берется из переменной окружения)

    Returns:
        Экземпляр AdminNotifier или None
    """
    if not bot_token:
        import os
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not bot_token:
        logger.error("❌ Не найден токен бота для отправки уведомлений")
        return None

    return AdminNotifier(bot_token)