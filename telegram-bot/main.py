#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ГрантСервис - Универсальный Telegram Bot
Автоматически определяет платформу и использует соответствующие настройки
Архитектура: Telegram Bot + n8n + ГигаЧат API
"""

import logging
import os
import sys
import platform
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import requests
import json
from datetime import datetime


# ============================================================================
# ПЛАТФОРМОЗАВИСИМАЯ КОНФИГУРАЦИЯ
# ============================================================================

class PlatformConfig(ABC):
    """Базовый класс для платформозависимой конфигурации"""
    
    @property
    @abstractmethod
    def base_path(self) -> str:
        """Базовый путь к проекту"""
        pass
    
    @property
    def log_path(self) -> str:
        """Путь к файлу логов"""
        return os.path.join(self.base_path, 'logs', 'telegram_bot.log')
    
    @property
    def env_path(self) -> str:
        """Путь к файлу с переменными окружения"""
        return os.path.join(self.base_path, 'config', '.env')
    
    @property
    def use_emoji(self) -> bool:
        """Использовать ли emoji в логах"""
        return True
    
    def format_log_message(self, message: str, emoji: str = None) -> str:
        """Форматировать сообщение лога с учетом платформы"""
        if self.use_emoji and emoji:
            return f"{emoji} {message}"
        return message
    
    def ensure_directories(self):
        """Создать необходимые директории если их нет"""
        dirs = [
            os.path.dirname(self.log_path),
            os.path.join(self.base_path, 'data'),
            os.path.join(self.base_path, 'config')
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    @abstractmethod
    def setup_logging(self) -> logging.Logger:
        """Настроить логирование для платформы"""
        pass
    
    def load_environment(self):
        """Загрузить переменные окружения"""
        if os.path.exists(self.env_path):
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            # Убираем кавычки если есть
                            value = value.strip('"\'')
                            os.environ[key] = value
            return True
        return False


class WindowsConfig(PlatformConfig):
    """Конфигурация для Windows"""
    
    @property
    def base_path(self) -> str:
        # Позволяем переопределить через переменную окружения
        return os.environ.get('GRANTSERVICE_BASE_PATH', 'C:\\SnowWhiteAI\\GrantService')
    
    @property
    def use_emoji(self) -> bool:
        # Windows консоль может не поддерживать emoji
        return os.environ.get('ENABLE_EMOJI', 'false').lower() == 'true'
    
    def setup_logging(self) -> logging.Logger:
        """Настроить логирование для Windows"""
        self.ensure_directories()
        
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO,
            handlers=[
                logging.FileHandler(self.log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)


class UnixConfig(PlatformConfig):
    """Конфигурация для Linux/Unix"""
    
    @property
    def base_path(self) -> str:
        # Позволяем переопределить через переменную окружения
        return os.environ.get('GRANTSERVICE_BASE_PATH', '/var/GrantService')
    
    def setup_logging(self) -> logging.Logger:
        """Настроить логирование для Unix"""
        self.ensure_directories()
        
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO,
            handlers=[
                logging.FileHandler(self.log_path),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)


class DockerConfig(UnixConfig):
    """Конфигурация для Docker контейнера"""
    
    @property
    def base_path(self) -> str:
        return os.environ.get('APP_PATH', '/app')


def get_platform_config() -> PlatformConfig:
    """Получить конфигурацию в зависимости от платформы"""
    # Проверяем, запущены ли мы в Docker
    if os.path.exists('/.dockerenv'):
        return DockerConfig()
    
    # Определяем операционную систему
    system = platform.system()
    
    if system == 'Windows':
        return WindowsConfig()
    elif system in ['Linux', 'Darwin']:  # Darwin для macOS
        return UnixConfig()
    else:
        # Фоллбек на Unix конфигурацию
        logging.warning(f"Неизвестная платформа {system}, используется Unix конфигурация")
        return UnixConfig()


# ============================================================================
# ОСНОВНОЙ КОД БОТА
# ============================================================================

# Инициализируем конфигурацию платформы
config = get_platform_config()

# Добавляем пути к модулям БД и utils
sys.path.insert(0, config.base_path)
# Добавляем текущую папку telegram-bot для импорта utils
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Настраиваем логирование
logger = config.setup_logging()

# Загружаем переменные окружения
if config.load_environment():
    logger.info(config.format_log_message(
        f"Загружены переменные окружения из {config.env_path}", "✅"
    ))

# Импортируем модули БД после добавления пути
from data.database import (
    db, get_or_create_session, update_session_data,
    get_interview_questions, get_total_users
)

from config.constants import ADMIN_USERS, ALLOWED_USERS

# AI Agents
from agents.interactive_interviewer_agent import InteractiveInterviewerAgent

# NEW: Interactive Interview V2 Handler
from handlers.interactive_interview_handler import InteractiveInterviewHandler

# NEW: Grant Handler for ProductionWriter
from handlers.grant_handler import GrantHandler

# ITERATION 35: Anketa Management Handler
from handlers.anketa_management_handler import AnketaManagementHandler

# ITERATION 52: Interactive Pipeline Handler
from handlers.interactive_pipeline_handler import InteractivePipelineHandler


class GrantServiceBotWithMenu:
    def __init__(self):
        self.config = config  # Сохраняем конфигурацию
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.n8n_webhook_url = os.getenv('N8N_WEBHOOK_URL', 'http://localhost:5678/webhook/grant-service')
        self.gigachat_api_key = os.getenv('GIGACHAT_API_KEY')

        # Состояния пользователей
        self.user_sessions = {}

        # Состояния меню
        self.menu_states = {
            'main_menu': 'main_menu',
            'interviewing': 'interviewing',
            'review': 'review'
        }

        # AI Agents - по одному экземпляру на пользователя
        self.ai_interviewers = {}  # {user_id: InteractiveInterviewerAgent}

        # ITERATION 52: Interactive Pipeline Handler (must be before interview_handler!)
        self.pipeline_handler = InteractivePipelineHandler(db=db)

        # NEW: Interactive Interview V2 Handler (with Iteration 52 pipeline integration)
        admin_chat_id = os.getenv('ADMIN_CHAT_ID')
        self.interview_handler = InteractiveInterviewHandler(
            db=db,
            admin_chat_id=int(admin_chat_id) if admin_chat_id else None,
            pipeline_handler=self.pipeline_handler  # ITERATION 52: Pass pipeline handler
        )

        # NEW: Grant Handler for ProductionWriter
        self.grant_handler = GrantHandler(
            db=db,
            admin_chat_id=int(admin_chat_id) if admin_chat_id else None
        )

        # ITERATION 35: Anketa Management Handler
        self.anketa_handler = AnketaManagementHandler(db=db)

        # Инициализация БД
        self.init_database()
    
    def is_user_authorized(self, user_id: int) -> bool:
        """Проверяет, авторизован ли пользователь"""
        # ВСЕГДА разрешаем доступ (авторизация отключена)
        return True
        # Если список разрешенных пользователей пуст, разрешаем всем
        # if not ALLOWED_USERS:
        #     return True
        # return user_id in ALLOWED_USERS
    
    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        # ВСЕГДА разрешаем админские функции (авторизация отключена)
        return True
        # return user_id in ADMIN_USERS
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            # Проверяем, что БД доступна
            total_users = get_total_users()
            logger.info(self.config.format_log_message(
                f"База данных инициализирована, пользователей: {total_users}", "✅"
            ))
        except Exception as e:
            logger.error(self.config.format_log_message(
                f"Ошибка инициализации БД: {e}", "❌"
            ))

    def get_or_create_ai_interviewer(self, user_id: int, user_data: Dict[str, Any]) -> InteractiveInterviewerAgent:
        """Получить или создать AI интервьюера для пользователя"""
        if user_id not in self.ai_interviewers:
            logger.info(f"Создаю нового AI интервьюера для пользователя {user_id}")
            self.ai_interviewers[user_id] = InteractiveInterviewerAgent(
                telegram_id=user_data.get('telegram_id', user_id),
                username=user_data.get('username', ''),
                email=user_data.get('email'),
                phone=user_data.get('phone'),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                grant_fund=user_data.get('grant_fund', 'Фонд президентских грантов')
            )
        return self.ai_interviewers[user_id]

    def get_total_questions(self) -> int:
        """Получить общее количество активных вопросов"""
        try:
            questions = get_interview_questions()  # уже возвращает is_active=1
            return len(questions)
        except Exception as e:
            logger.error(f"Ошибка подсчета вопросов: {e}")
            return 0  # без фолбэка на 24, чтобы избежать рассинхрона
    
    def get_question_by_number(self, question_number: int) -> Dict:
        """Получить вопрос по номеру"""
        try:
            questions = get_interview_questions()
            for question in questions:
                if question.get('question_number') == question_number:
                    return question
            return None
        except Exception as e:
            logger.error(f"Ошибка получения вопроса {question_number}: {e}")
            return None
    
    def get_user_session(self, user_id: int) -> Dict[str, Any]:
        """Получить или создать сессию пользователя"""
        if user_id not in self.user_sessions:
            total_questions = self.get_total_questions()
            self.user_sessions[user_id] = {
                'state': 'main_menu',
                'current_question': 1,
                'total_questions': total_questions,
                'answers': {},
                'started_at': datetime.now()
            }
        return self.user_sessions[user_id]
    
    def update_user_session(self, user_id: int, **kwargs):
        """Обновить сессию пользователя"""
        session = self.get_user_session(user_id)
        session.update(kwargs)
        session['last_activity'] = datetime.now()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Стартовая команда - показывает главное меню или обрабатывает deep link"""
        user = update.effective_user
        user_id = user.id
        
        # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ для отладки deep link
        logger.info("="*60)
        logger.info("ВЫЗОВ КОМАНДЫ /start")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Username: {user.username}")
        logger.info(f"Параметры context.args: {context.args}")
        logger.info(f"Количество параметров: {len(context.args) if context.args else 0}")
        if context.args:
            for i, arg in enumerate(context.args):
                logger.info(f"  Параметр {i}: '{arg}'")
        logger.info(f"Update.message существует: {update.message is not None}")
        logger.info(f"Update.callback_query существует: {update.callback_query is not None}")
        logger.info("="*60)
        
        # Регистрируем пользователя в БД
        try:
            from data.database import db
            db.register_user(
                telegram_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            logger.info(f"✅ Пользователь {user_id} зарегистрирован в БД")
        except Exception as e:
            logger.error(f"❌ Ошибка регистрации пользователя {user_id}: {e}")
        
        # Проверка авторизации
        if not self.is_user_authorized(user_id):
            await update.message.reply_text("❌ Доступ запрещен. Обратитесь к администратору.")
            return
        
        # Проверяем параметры deep linking
        if context.args and len(context.args) > 0:
            command = context.args[0]
            logger.info(f"🔍 Обнаружен deep link параметр: '{command}'")
            
            # Если параметр get_access - автоматически генерируем токен
            if command == "get_access":
                logger.info(self.config.format_log_message(
                    f"✅ Deep link /start get_access от пользователя {user_id}", "🔗"
                ))
                # Используем существующее сообщение или создаем виртуальное
                if update.message:
                    logger.info("📨 Вызываем get_access_command с существующим message")
                    # Вызываем функцию генерации токена с обычным update
                    await self.get_access_command(update, context)
                else:
                    # Если это был callback, создаем новое сообщение
                    logger.warning("⚠️ Deep link вызван без message, создаем виртуальное сообщение")
                    # Отправляем сообщение пользователю и затем вызываем функцию
                    msg = await context.bot.send_message(
                        chat_id=user_id,
                        text="🔐 Генерирую токен доступа..."
                    )
                    # Создаем новый update с этим сообщением
                    update.message = msg
                    await self.get_access_command(update, context)
                logger.info("✅ Обработка deep link завершена")
                return
            else:
                logger.info(f"⚠️ Неизвестный deep link параметр: '{command}'")
        else:
            logger.info("📋 Параметров deep link нет, показываем главное меню")
        
        # Обычная логика старта - сброс сессии и показ главного меню
        total_questions = self.get_total_questions()
        self.user_sessions[user_id] = {
            'state': 'main_menu',
            'current_question': 1,
            'total_questions': total_questions,
            'answers': {},
            'started_at': datetime.now()
        }
        
        await self.show_main_menu(update, context)
    
    async def get_access_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /get_access - генерация токена доступа к админ-панели"""
        user = update.effective_user
        user_id = user.id
        
        logger.info(self.config.format_log_message(
            f"Получена команда /get_access от пользователя {user_id} ({user.username})", "🔐"
        ))
        
        # Проверка авторизации
        if not self.is_user_authorized(user_id):
            logger.warning(self.config.format_log_message(
                f"Доступ запрещен для пользователя {user_id}", "❌"
            ))
            # Обрабатываем и message, и callback_query
            if update.message:
                await update.message.reply_text("❌ Доступ запрещен. Обратитесь к администратору.")
            elif update.callback_query:
                await update.callback_query.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        # Генерируем токен авторизации
        try:
            # Получаем или создаем токен для пользователя
            from data.database import db, auth_manager
            
            # Проверяем роль пользователя
            user_role = auth_manager.get_user_role(user_id)
            if not user_role:
                # Устанавливаем роль по умолчанию
                auth_manager.set_user_role(user_id, 'user')
                user_role = 'user'
            
            token = db.get_or_create_login_token(user_id)
            logger.info(self.config.format_log_message(
                f"Сгенерирован токен для пользователя {user_id} с ролью {user_role}", "🔑"
            ))
            
            if token:
                # Формируем ссылку для входа в админ панель
                # Для локальной разработки используем localhost
                base_url = os.getenv('ADMIN_BASE_URL', 'http://localhost:8501')
                admin_url = f"{base_url}?token={token}"
                
                # Логируем вход в систему
                auth_manager.log_auth_action(
                    user_id=user_id,
                    action='generate_token',
                    success=True
                )
                
                access_text = f"""
🔐 *Доступ к админ-панели*

✅ *Токен успешно сгенерирован!*
📱 *Ваш Telegram ID:* `{user_id}`
👤 *Роль в системе:* `{user_role}`

🔗 *Ссылка для входа:*
{admin_url}

⏰ *Токен действителен:* 24 часа
🔒 *Безопасность:* Не передавайте ссылку третьим лицам!

💡 *Совет:* Ссылка активна - просто нажмите на неё
"""
                
                # Создаем инлайн-клавиатуру с дополнительными опциями
                # НЕ добавляем кнопку с localhost URL - Telegram её не принимает
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [
                    # Убираем кнопку с URL для localhost
                    # [InlineKeyboardButton("🔗 Открыть админ-панель", url=admin_url)],
                    [InlineKeyboardButton("🔄 Обновить токен", callback_data="refresh_token")],
                    [InlineKeyboardButton("❌ Отозвать токен", callback_data="revoke_token")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Отправляем сообщение в зависимости от типа update
                if update.message:
                    await update.message.reply_text(
                        text=access_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                elif update.callback_query:
                    await update.callback_query.edit_message_text(
                        text=access_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                else:
                    # Fallback - отправляем напрямую
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=access_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
            else:
                logger.error(self.config.format_log_message(
                    f"Ошибка генерации токена для пользователя {user_id}", "❌"
                ))
                error_msg = "❌ Ошибка генерации токена. Попробуйте позже."
                if update.message:
                    await update.message.reply_text(error_msg)
                elif update.callback_query:
                    await update.callback_query.answer(error_msg, show_alert=True)
                else:
                    await context.bot.send_message(chat_id=user_id, text=error_msg)
                
        except Exception as e:
            logger.error(self.config.format_log_message(
                f"Ошибка генерации токена доступа для пользователя {user_id}: {e}", "❌"
            ))
            import traceback
            traceback.print_exc()
            error_msg = "❌ Ошибка генерации токена. Попробуйте позже."
            if update.message:
                await update.message.reply_text(error_msg)
            elif update.callback_query:
                await update.callback_query.answer(error_msg, show_alert=True)
            else:
                await context.bot.send_message(chat_id=user_id, text=error_msg)
    
    async def revoke_access_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /revoke_access - отзыв токена доступа"""
        user = update.effective_user
        user_id = user.id
        
        logger.info(self.config.format_log_message(
            f"Получена команда /revoke_access от пользователя {user_id}", "🔓"
        ))
        
        try:
            from data.database import db, auth_manager
            
            # Очищаем токен пользователя
            with db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET login_token = NULL WHERE telegram_id = ?
                """, (user_id,))
                conn.commit()
            
            # Логируем отзыв токена
            auth_manager.log_auth_action(
                user_id=user_id,
                action='revoke_token',
                success=True
            )
            
            logger.info(self.config.format_log_message(
                f"Токен отозван для пользователя {user_id}", "✅"
            ))
            
            revoke_text = """
🔓 *Токен доступа отозван*

✅ Ваш токен доступа к админ-панели был успешно отозван.

Если вам снова понадобится доступ, используйте команду /get_access
"""
            
            await update.message.reply_text(
                text=revoke_text,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(self.config.format_log_message(
                f"Ошибка отзыва токена для пользователя {user_id}: {e}", "❌"
            ))
            await update.message.reply_text("❌ Ошибка отзыва токена. Попробуйте позже.")
    
    async def my_access_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /my_access - информация о текущем доступе"""
        user = update.effective_user
        user_id = user.id
        
        logger.info(self.config.format_log_message(
            f"Получена команда /my_access от пользователя {user_id}", "ℹ️"
        ))
        
        try:
            from data.database import db, auth_manager
            
            # Получаем информацию о пользователе
            user_role = auth_manager.get_user_role(user_id)
            user_permissions = auth_manager.get_user_permissions(user_id)
            
            # Проверяем наличие активного токена
            with db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT login_token FROM users WHERE telegram_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                has_token = bool(result and result[0])
            
            # Формируем текст с информацией
            access_info = f"""
ℹ️ *Информация о вашем доступе*

👤 *Telegram ID:* `{user_id}`
📝 *Имя:* {user.first_name or 'Не указано'}
🏷️ *Username:* @{user.username or 'не указан'}

🎭 *Роль в системе:* `{user_role}`
🔐 *Активный токен:* {'✅ Да' if has_token else '❌ Нет'}
"""
            
            if user_permissions:
                access_info += f"\n🔧 *Дополнительные разрешения:*\n"
                for perm in user_permissions:
                    access_info += f"  • {perm}\n"
            
            # Доступные страницы
            accessible_pages = auth_manager.get_accessible_pages(user_id)
            if accessible_pages:
                access_info += f"\n📄 *Доступные страницы:*\n"
                for page in accessible_pages[:5]:  # Показываем только первые 5
                    access_info += f"  • {page}\n"
                if len(accessible_pages) > 5:
                    access_info += f"  ... и ещё {len(accessible_pages) - 5}\n"
            
            access_info += """
            
💡 *Команды управления доступом:*
/get_access - Получить токен доступа
/revoke_access - Отозвать токен
/my_access - Эта информация
"""
            
            await update.message.reply_text(
                text=access_info,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о доступе: {e}")
            await update.message.reply_text("❌ Ошибка получения информации. Попробуйте позже.")
    
    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /login - псевдоним для /get_access (для обратной совместимости)"""
        await self.get_access_command(update, context)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для получения ссылки авторизации в админ панель (только для админов)"""
        user = update.effective_user
        user_id = user.id
        
        logger.info(self.config.format_log_message(
            f"Получена команда /admin от пользователя {user_id} ({user.username})", "📥"
        ))
        
        # Проверка авторизации
        if not self.is_user_authorized(user_id):
            logger.warning(self.config.format_log_message(
                f"Доступ запрещен для пользователя {user_id}", "❌"
            ))
            await update.message.reply_text("❌ Доступ запрещен. Обратитесь к администратору.")
            return
        
        # Проверка прав администратора
        if not self.is_admin(user_id):
            logger.warning(self.config.format_log_message(
                f"Недостаточно прав для пользователя {user_id}", "❌"
            ))
            await update.message.reply_text("❌ Недостаточно прав. Требуются права администратора.")
            return
        
        # Генерируем токен авторизации
        try:
            # Получаем или создаем токен для пользователя
            from data.database import db
            token = db.get_or_create_login_token(user_id)
            logger.info(self.config.format_log_message(
                f"Получен токен для администратора {user_id}: {token[:20] if token else 'None'}", "🔑"
            ))
            
            if token:
                # Формируем ссылку для входа в админ панель
                admin_url = f"https://admin.grantservice.onff.ru?token={token}"
                logger.info(self.config.format_log_message(
                    f"Сформирована ссылка для администратора {user_id}: {admin_url[:50]}...", "🔗"
                ))
                
                admin_text = f"""
🔐 *Ссылка для входа в админ панель*

⚠️ **Внимание! Ни с кем не делитесь этой ссылкой!**

🔗 Нажмите на ссылку для авторизации:
`{admin_url}`

⚠️ Ссылка действительна 24 часа
🔒 Не передавайте ссылку посторонним

👑 **Вы вошли с правами администратора**
"""
                
                await update.message.reply_text(
                    text=admin_text,
                    parse_mode='Markdown'
                )
            else:
                logger.error(self.config.format_log_message(
                    f"Ошибка генерации токена для администратора {user_id}", "❌"
                ))
                await update.message.reply_text("❌ Ошибка генерации токена. Попробуйте позже.")
                
        except Exception as e:
            logger.error(self.config.format_log_message(
                f"Ошибка генерации админ-ссылки для пользователя {user_id}: {e}", "❌"
            ))
            import traceback
            traceback.print_exc()
            await update.message.reply_text("❌ Ошибка генерации ссылки. Попробуйте позже.")
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню (Экран 1)"""
        user = update.effective_user
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("🆕 Интервью V2 (Adaptive)", callback_data="start_interview_v2")],
            [InlineKeyboardButton("📝 Начать заполнение (Classic)", callback_data="start_interview")],
            [InlineKeyboardButton("💳 Оплата", callback_data="payment")],
            [InlineKeyboardButton("📊 Статус заявки", callback_data="status")],
            [InlineKeyboardButton("ℹ️ О Грантсервисе", url="https://грантсервис.рф")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🤖 *Добро пожаловать в ГрантСервис!*

Привет, {user.first_name}! Я помогу тебе создать профессиональную грантовую заявку.

*Выберите действие:*
"""
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def show_question_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_number: int = 1):
        """Показать навигацию по вопросам (Экран 2)"""
        user_id = update.effective_user.id
        session = self.get_user_session(user_id)
        
        # Актуализируем количество вопросов (на случай динамических изменений)
        session['total_questions'] = self.get_total_questions()
        
        # Получаем вопрос
        question = self.get_question_by_number(question_number)
        if not question:
            await self.show_error(update, context, "Вопрос не найден")
            return
        
        # Обновляем состояние
        self.update_user_session(user_id,
                               state='interviewing',
                               current_question=question_number)
        
        # Создаем клавиатуру навигации
        keyboard = []
        
        # Кнопки навигации
        nav_buttons = []
        if question_number > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_question_{question_number-1}"))
        if question_number < session['total_questions']:
            nav_buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"next_question_{question_number+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Кнопка возврата в меню
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в меню", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Формируем текст вопроса
        question_text = f"""
*Вопрос {question_number} из {session['total_questions']}*

{question['question_text']}
"""
        
        # Если это вопрос типа select, добавляем варианты ответов
        if question.get('question_type') == 'select' and question.get('options'):
            try:
                import json
                # Проверяем, является ли options уже списком или нужно парсить JSON
                if isinstance(question['options'], str):
                    options = json.loads(question['options'])
                elif isinstance(question['options'], list):
                    options = question['options']
                else:
                    # Если это bytes или другой тип, пытаемся декодировать
                    options = json.loads(str(question['options']))
                
                question_text += "\n*Варианты ответов:*\n"
                for i, option in enumerate(options, 1):
                    question_text += f"\n{i}. {option.get('text', option.get('value'))}"
                    if option.get('description'):
                        question_text += f"\n   _{option['description']}_"
                
                question_text += "\n\n📝 *Введите номер выбранного варианта (от 1 до " + str(len(options)) + ")*"
            except Exception as e:
                logger.error(f"Ошибка парсинга вариантов ответа: {e}")
                question_text += "\n\n⚠️ Ошибка загрузки вариантов ответа"
        
        # Добавляем подсказку
        if question.get('hint_text'):
            question_text += f"\n\n💡 *Подсказка:* {question['hint_text']}"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=question_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=question_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def show_review_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать экран проверки (Экран 3)"""
        user_id = update.effective_user.id
        session = self.get_user_session(user_id)
        
        # Обновляем состояние
        self.update_user_session(user_id, state='review')
        
        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton("✅ Отправить на проверку", callback_data="submit_for_review")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_question_{session['current_question']-1}")],
            [InlineKeyboardButton("🏠 Вернуться в меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Подсчитываем заполненные вопросы
        filled_questions = len([ans for ans in session['answers'].values() if ans])
        completion_percentage = (filled_questions / session['total_questions']) * 100
        
        review_text = f"""
📋 *Проверка заявки*

*Статистика заполнения:*
• Заполнено вопросов: {filled_questions} из {session['total_questions']}
• Процент заполнения: {completion_percentage:.1f}%

*Важно:* Нажимая кнопку "Отправить на проверку" вы подтверждаете полноту и достоверность ответов на вопросы.

Далее наш сервис:
• Сгенерирует разделы вашей заявки
• Даст рекомендации по улучшению
• При необходимости вернется с уточняющими вопросами
• Готовый текст будет выслан в формате .pdf

*Готовы отправить заявку на проверку?*
"""
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=review_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=review_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий кнопок меню"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Проверка авторизации
        if not self.is_user_authorized(user_id):
            await query.answer("❌ Доступ запрещен. Обратитесь к администратору.", show_alert=True)
            return
        
        callback_data = query.data
        
        # Обработка токен-команд
        if callback_data == "refresh_token":
            # Обновление токена
            try:
                from data.database import db, auth_manager
                new_token = db.refresh_login_token(user_id)
                if new_token:
                    base_url = os.getenv('ADMIN_BASE_URL', 'http://localhost:8501')
                    admin_url = f"{base_url}?token={new_token}"
                    
                    auth_manager.log_auth_action(
                        user_id=user_id,
                        action='refresh_token',
                        success=True
                    )
                    
                    await query.answer("✅ Токен обновлен!", show_alert=True)
                    await query.edit_message_text(
                        text=f"🔐 *Токен обновлен!*\n\n🔗 *Новая ссылка:*\n{admin_url}\n\n⏰ Действителен 24 часа",
                        parse_mode='Markdown'
                    )
                else:
                    await query.answer("❌ Ошибка обновления токена", show_alert=True)
            except Exception as e:
                logger.error(f"Ошибка обновления токена: {e}")
                await query.answer("❌ Ошибка обновления токена", show_alert=True)
            return
            
        elif callback_data == "revoke_token":
            # Отзыв токена
            try:
                from data.database import db, auth_manager
                with db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET login_token = NULL WHERE telegram_id = ?", (user_id,))
                    conn.commit()
                
                auth_manager.log_auth_action(
                    user_id=user_id,
                    action='revoke_token_inline',
                    success=True
                )
                
                await query.answer("✅ Токен отозван!", show_alert=True)
                await query.edit_message_text(
                    text="🔓 *Токен доступа отозван*\n\nДля получения нового токена используйте команду /get_access",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Ошибка отзыва токена: {e}")
                await query.answer("❌ Ошибка отзыва токена", show_alert=True)
            return
        
        elif callback_data == "start_interview_v2":
            # NEW: Начать V2 интервью с Reference Points
            await query.answer()
            # Запустить интервью сразу (без лишних сообщений)
            await self.handle_start_interview_v2_direct(update, context)

        elif callback_data == "start_interview":
            # Начинаем интервью с первого вопроса
            await self.show_question_navigation(update, context, 1)

        elif callback_data == "payment":
            # Переход на сервис оплаты
            payment_text = """
💳 *Оплата услуг*

Для оплаты перейдите по ссылке:
https://grantservice.onff.ru/payment

Или свяжитесь с нами:
📞 +7 (951) 584-10-83
📧 otinoff@gmail.com
"""
            await query.edit_message_text(
                text=payment_text,
                parse_mode='Markdown'
            )
            
        elif callback_data == "status":
            # Показать статус заявки
            await self.show_application_status(update, context)
            
        # Removed: "about" button now opens URL directly (no callback needed)

        elif callback_data == "main_menu":
            # Возврат в главное меню
            await self.show_main_menu(update, context)
            
        elif callback_data.startswith("next_question_"):
            # Переход к следующему вопросу
            next_question = int(callback_data.split("_")[-1])
            await self.show_question_navigation(update, context, next_question)
            
        elif callback_data.startswith("prev_question_"):
            # Переход к предыдущему вопросу
            prev_question = int(callback_data.split("_")[-1])
            await self.show_question_navigation(update, context, prev_question)
            
        elif callback_data == "submit_for_review":
            # Отправка на проверку
            await self.submit_application_for_review(update, context)
            
        elif callback_data == "new_anketa":
            # Начать новую анкету
            await self.start_new_anketa(update, context)
            
        elif callback_data.startswith("send_to_processing_"):
            # Отправить анкету на обработку
            anketa_id = callback_data.replace("send_to_processing_", "")
            await self.send_anketa_to_processing(update, context, anketa_id)
    
    async def show_application_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статус заявки"""
        user_id = update.callback_query.from_user.id
        session = self.get_user_session(user_id)
        
        # Подсчитываем прогресс
        filled_questions = len([ans for ans in session['answers'].values() if ans])
        completion_percentage = (filled_questions / session['total_questions']) * 100
        
        # Определяем статус
        if completion_percentage == 0:
            status = "🟡 Не начато"
        elif completion_percentage < 100:
            status = "🟠 В работе"
        else:
            status = "🟢 Заполнено"
        
        status_text = f"""
📊 *Статус заявки*

*Текущий статус:* {status}
*Заполнено вопросов:* {filled_questions} из {session['total_questions']}
*Процент заполнения:* {completion_percentage:.1f}%

*Время начала:* {session['started_at'].strftime('%d.%m.%Y %H:%M')}
*Последняя активность:* {session.get('last_activity', session['started_at']).strftime('%d.%m.%Y %H:%M')}
"""
        
        # Кнопка возврата в меню
        keyboard = [[InlineKeyboardButton("🏠 Вернуться в меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(
            text=status_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def submit_application_for_review(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправить заявку на проверку"""
        user_id = update.callback_query.from_user.id
        session = self.get_user_session(user_id)
        
        # Проверяем полноту заполнения
        filled_questions = len([ans for ans in session['answers'].values() if ans])
        if filled_questions < session['total_questions']:
            await self.show_error(update, context, 
                                f"Заполнено только {filled_questions} из {session['total_questions']} вопросов. "
                                "Пожалуйста, заполните все вопросы перед отправкой.")
            return
        
        # Генерируем anketa_id и сохраняем анкету
        try:
            # Получаем данные пользователя
            user = update.effective_user
            user_data = {
                "telegram_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            
            # Получаем сессию из БД
            db_session = get_or_create_session(user_id)
            if not db_session:
                await self.show_error(update, context, "Ошибка получения сессии. Попробуйте позже.")
                return
            
            # Подготавливаем данные анкеты
            anketa_data = {
                "user_data": user_data,
                "session_id": db_session['id'],
                "interview_data": session['answers']
            }
            
            # Сохраняем анкету и получаем anketa_id
            anketa_id = db.save_anketa(anketa_data)
            
            if not anketa_id:
                await self.show_error(update, context, "Ошибка сохранения анкеты. Попробуйте позже.")
                return
            
            logger.info(self.config.format_log_message(
                f"Анкета сохранена: {anketa_id} для пользователя {user_id}", "✅"
            ))

            # 📄 ОТПРАВКА PDF АНКЕТЫ В АДМИНСКИЙ ЧАТ
            try:
                await self._send_interview_pdf_to_admin(
                    anketa_id=anketa_id,
                    user_id=user_id,
                    answers=session['answers']
                )
            except Exception as pdf_error:
                logger.error(f"❌ Ошибка отправки interview PDF: {pdf_error}")
                # Не прерываем выполнение - это не критично

        except Exception as e:
            logger.error(self.config.format_log_message(
                f"Ошибка сохранения анкеты: {e}", "❌"
            ))
            await self.show_error(update, context, "Ошибка сохранения анкеты. Попробуйте позже.")
            return
        
        # Отправляем в n8n для обработки
        try:
            result = await self.call_n8n_webhook('submit_application', {
                'user_id': user_id,
                'anketa_id': anketa_id,
                'answers': session['answers'],
                'submitted_at': datetime.now().isoformat()
            })
            
            success_text = f"""
✅ *Анкета отправлена на обработку!*

Ваша анкета успешно сохранена и отправлена в обработку.

*ID анкеты:* `{anketa_id}`

*Что происходит дальше:*
1️⃣ Наш ИИ-исследователь анализирует ваши ответы
2️⃣ Проводит исследование рынка и конкурентов
3️⃣ Находит подходящие грантовые возможности
4️⃣ Создает структуру заявки
5️⃣ Подготавливает финальный документ

⏰ *Ваша заявка в работе!*
📞 *В течение 48 часов мы свяжемся с вами*

Спасибо за использование Грантсервиса! 🚀
"""
            
            keyboard = [[InlineKeyboardButton("🏠 Вернуться в меню", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                text=success_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка отправки заявки: {e}")
            await self.show_error(update, context, "Ошибка отправки заявки. Попробуйте позже.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений (ответы на вопросы)"""
        user_id = update.effective_user.id
        message_text = update.message.text if update.message else "None"

        logger.info(f"[DEBUG MAIN] handle_message called for user {user_id}, message: {message_text[:50]}")

        # Проверка авторизации
        is_authorized = self.is_user_authorized(user_id)
        logger.info(f"[DEBUG MAIN] Authorization check: {is_authorized}")

        if not is_authorized:
            logger.warning(f"[DEBUG MAIN] User {user_id} not authorized, exiting")
            await update.message.reply_text("❌ Доступ запрещен. Обратитесь к администратору.")
            return

        # NEW: Проверить активное V2 интервью
        is_active = self.interview_handler.is_interview_active(user_id)
        logger.info(f"[DEBUG MAIN] Interview active check: {is_active}")

        if is_active:
            logger.info(f"[DEBUG MAIN] Routing to interview_handler.handle_message for user {user_id}")
            await self.interview_handler.handle_message(update, context)
            logger.info(f"[DEBUG MAIN] Returned from interview_handler.handle_message")
            return

        session = self.get_user_session(user_id)
        
        if session['state'] != 'interviewing':
            # Если не в режиме интервью, показываем главное меню
            await self.show_main_menu(update, context)
            return
        
        # Сохраняем ответ на текущий вопрос
        current_question = session['current_question']
        answer = update.message.text
        
        # Получаем информацию о текущем вопросе
        question_info = self.get_question_by_number(current_question)
        if question_info and question_info.get('field_name'):
            field_name = question_info['field_name']
        else:
            # Fallback на номер вопроса, если field_name не найден
            field_name = str(current_question)
        
        # Если это вопрос типа select, обрабатываем выбор по номеру
        if question_info and question_info.get('question_type') == 'select':
            try:
                # Проверяем, что введен номер
                choice_num = int(answer.strip())
                
                # Загружаем варианты ответов
                import json
                options_data = question_info.get('options', '[]')
                
                # Проверяем тип данных options
                if isinstance(options_data, str):
                    options = json.loads(options_data)
                elif isinstance(options_data, list):
                    options = options_data
                else:
                    options = json.loads(str(options_data))
                
                if 1 <= choice_num <= len(options):
                    # Сохраняем ТЕКСТ выбранного варианта для анализа заявки
                    selected_option = options[choice_num - 1]
                    # Берем полный текст варианта, а не value (код)
                    answer = selected_option.get('text', selected_option.get('value', str(choice_num)))
                    
                    # Логируем выбор пользователя
                    answer_value = selected_option.get('value', '')
                    logger.info(f"Пользователь {user_id} выбрал вариант {choice_num}: {answer}")
                    logger.info(f"  -> Текст для БД: {answer}")
                    logger.info(f"  -> Код варианта: {answer_value}")
                else:
                    await update.message.reply_text(
                        f"⚠️ Пожалуйста, введите число от 1 до {len(options)}"
                    )
                    return
                    
            except ValueError:
                await update.message.reply_text(
                    "⚠️ Для вопросов с вариантами ответа введите номер варианта (например: 1)"
                )
                return
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка декодирования JSON: {e}, данные: {type(options_data)}")
                await update.message.reply_text(
                    "⚠️ Ошибка загрузки вариантов ответа. Пожалуйста, введите ваш ответ текстом."
                )
                # Продолжаем обработку как обычного текстового ответа
            except Exception as e:
                logger.error(f"Ошибка обработки select вопроса: {e}")
        
        # Сохраняем ответ в память по field_name
        session['answers'][field_name] = answer
        
        # Сохраняем ответ в БД
        try:
            # Получаем или создаем сессию в БД
            db_session = get_or_create_session(user_id)
            
            # Сохраняем ответ в БД
            if db_session:
                # Обновляем поля interview_data и collected_data
                current_answers = session['answers']
                
                # Сохраняем в interview_data (JSON)
                interview_data = json.dumps(current_answers, ensure_ascii=False)
                
                # Обновляем сессию в БД
                update_session_data(db_session['id'], {
                    'interview_data': interview_data,
                    'collected_data': interview_data,  # Дублируем для совместимости
                    'last_activity': datetime.now().isoformat()
                })
                
                logger.info(self.config.format_log_message(
                    f"Ответ сохранен в БД для пользователя {user_id}, вопрос {current_question}", "✅"
                ))
            else:
                logger.error(self.config.format_log_message(
                    f"Не удалось получить сессию БД для пользователя {user_id}", "❌"
                ))
                
        except Exception as e:
            logger.error(self.config.format_log_message(
                f"Ошибка сохранения ответа в БД: {e}", "❌"
            ))
        
        # Актуализируем количество вопросов перед проверкой
        actual_total_questions = self.get_total_questions()
        session['total_questions'] = actual_total_questions  # Обновляем в сессии
        
        # Логирование для отладки
        logger.info(f"Пользователь {user_id}: вопрос {current_question} из {actual_total_questions} активных")
        
        # Проверяем, ответил ли пользователь на все активные вопросы
        if current_question < actual_total_questions:
            await self.show_question_navigation(update, context, current_question + 1)
        else:
            # Автоматически сохраняем анкету после последнего активного вопроса
            logger.info(f"Пользователь {user_id} ответил на все {actual_total_questions} активных вопросов")
            anketa_id = await self.auto_save_anketa(update, context, user_id)
            if anketa_id:
                # 🤖 AI AUDIT: Оцениваем качество анкеты
                audit_result = await self.run_ai_audit(update, context, user_id, anketa_id)
                if audit_result:
                    session['audit_score'] = audit_result.get('audit_score', 0)
                    session['audit_recommendations'] = audit_result.get('recommendations', [])
                    logger.info(f"✅ AI Audit завершён: {session['audit_score']}/100")

                # ITERATION 52: Use Interactive Pipeline instead of show_completion_screen
                await self.pipeline_handler.on_anketa_complete(update, context, anketa_id, session)
            else:
                # Если не удалось сохранить, показываем экран проверки
                await self.show_review_screen(update, context)
    
    async def call_n8n_webhook(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Вызов n8n webhook"""
        try:
            payload = {
                'action': action,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                self.n8n_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"n8n webhook error: {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            logger.error(f"n8n webhook exception: {e}")
            return {'success': False, 'error': str(e)}
    
    async def show_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: str):
        """Показать сообщение об ошибке"""
        keyboard = [[InlineKeyboardButton("🏠 Вернуться в меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        error_text = f"❌ *Ошибка*\n\n{error_message}"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=error_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=error_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def auto_save_anketa(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> Optional[str]:
        """Автоматически сохранить анкету после последнего вопроса"""
        try:
            session = self.get_user_session(user_id)
            
            # Логирование для отладки
            logger.info(f"Автосохранение: пользователь {user_id} заполнил {len(session['answers'])} из {session['total_questions']} вопросов")
            
            # Получаем данные пользователя
            user = update.effective_user
            user_data = {
                "telegram_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            
            # Получаем сессию из БД
            db_session = get_or_create_session(user_id)
            if not db_session:
                logger.error(f"Не удалось получить сессию для пользователя {user_id}")
                return None
            
            # Подготавливаем данные анкеты
            anketa_data = {
                "user_data": user_data,
                "session_id": db_session['id'],
                "interview_data": session['answers']
            }
            
            # Сохраняем анкету и получаем anketa_id
            from data.database import db
            anketa_id = db.save_anketa(anketa_data)
            
            if anketa_id:
                logger.info(f"Анкета автоматически сохранена: {anketa_id} для пользователя {user_id}")
                # Сохраняем anketa_id в сессии для дальнейшего использования
                session['anketa_id'] = anketa_id

                # 📄 ОТПРАВКА PDF АНКЕТЫ В АДМИНСКИЙ ЧАТ
                try:
                    await self._send_interview_pdf_to_admin(
                        anketa_id=anketa_id,
                        user_id=user_id,
                        answers=session['answers']
                    )
                except Exception as pdf_error:
                    logger.error(f"❌ Ошибка отправки interview PDF: {pdf_error}")
                    # Не прерываем выполнение - это не критично

                # НОВОЕ: Автоматически создаем грантовую заявку
                try:
                    from utils.grant_application_creator import create_grant_application_from_session, update_session_completion_status
                    
                    # Создаем грантовую заявку
                    app_number = create_grant_application_from_session(
                        session_id=db_session['id'],
                        user_data=user_data,
                        answers=session['answers']
                    )
                    
                    if app_number:
                        logger.info(f"✅ Автоматически создана грантовая заявка: {app_number} для пользователя {user_id}")
                        
                        # Обновляем статус сессии
                        update_session_completion_status(db_session['id'], app_number)
                        
                        # Сохраняем номер заявки в сессии
                        session['application_number'] = app_number
                        
                        # Логируем успешное создание заявки (уведомление отправим через show_completion_screen)
                        logger.info(f"✅ Грантовая заявка {app_number} будет показана в финальном экране")
                    
                    else:
                        logger.warning(f"⚠️ Не удалось создать грантовую заявку для пользователя {user_id}, но анкета сохранена")
                        
                except Exception as grant_error:
                    logger.error(f"❌ Ошибка создания грантовой заявки: {grant_error}")
                    # Не прерываем выполнение - анкета уже сохранена
                
                return anketa_id
            else:
                logger.error(f"Не удалось сохранить анкету для пользователя {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка автосохранения анкеты: {e}")
            return None

    async def run_ai_audit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, anketa_id: str) -> Optional[Dict[str, Any]]:
        """Запустить AI аудит анкеты через InteractiveInterviewerAgent"""
        try:
            logger.info(f"🤖 Запуск AI audit для пользователя {user_id}, анкета {anketa_id}")

            session = self.get_user_session(user_id)
            user = update.effective_user

            # Подготовка данных для агента
            user_data = {
                'telegram_id': user.id,
                'username': user.username or '',
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'email': session.get('email'),
                'phone': session.get('phone'),
                'grant_fund': 'Фонд президентских грантов'
            }

            # Получаем или создаём AI агента
            ai_agent = self.get_or_create_ai_interviewer(user_id, user_data)

            # Вызываем аудит (синхронный метод в отдельном потоке)
            import asyncio
            loop = asyncio.get_event_loop()
            audit_result = await loop.run_in_executor(
                None,
                ai_agent.process,
                {'user_data': user_data, 'answers': session['answers']}
            )

            logger.info(f"✅ AI Audit completed: score={audit_result.get('audit_score', 0)}/100")
            return audit_result

        except Exception as e:
            logger.error(f"❌ Ошибка AI audit: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def show_completion_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, anketa_id: str):
        """Показать экран успешного завершения анкеты с AI оценкой"""
        user_id = update.effective_user.id
        session = self.get_user_session(user_id)

        # Проверяем, создана ли грантовая заявка
        app_number = session.get('application_number')

        # Получаем AI audit результаты
        audit_score = session.get('audit_score', 0)
        audit_recommendations = session.get('audit_recommendations', [])

        # Формируем сообщение с AI оценкой
        audit_section = ""
        if audit_score > 0:
            # Определяем эмодзи по уровню оценки
            if audit_score >= 70:
                score_emoji = "🟢"
                readiness = "Отличное качество!"
            elif audit_score >= 50:
                score_emoji = "🟡"
                readiness = "Хорошее качество"
            else:
                score_emoji = "🟠"
                readiness = "Требует доработки"

            audit_section = f"""
🤖 *AI Оценка качества анкеты:*
{score_emoji} *{audit_score}/100* — {readiness}
"""
            # Добавляем топ-3 рекомендации
            if audit_recommendations and len(audit_recommendations) > 0:
                audit_section += "\n📝 *Рекомендации по улучшению:*\n"
                for i, rec in enumerate(audit_recommendations[:3], 1):
                    audit_section += f"{i}. {rec}\n"

        if app_number:
            # Если заявка создана - показываем упрощенное меню
            keyboard = [
                [InlineKeyboardButton("📝 Заполнить новую анкету", callback_data="new_anketa")],
                [InlineKeyboardButton("🏠 Вернуться в меню", callback_data="main_menu")]
            ]

            completion_text = f"""
🎉 *Поздравляем! Интервью завершено!*

✅ *Анкета сохранена:* `{anketa_id}`
📋 *Грантовая заявка создана:* `{app_number}`
{audit_section}
🚀 *Ваша заявка автоматически создана и находится в обработке!*

📞 *Что дальше:*
• Наши эксперты проверят заявку
• При необходимости мы свяжемся с вами
• Готовый документ будет выслан в течение 48 часов

*Спасибо за использование ГрантСервиса!*
"""
        else:
            # Если заявка не создана - оставляем старое меню с возможностью отправки
            keyboard = [
                [InlineKeyboardButton("📝 Заполнить новую анкету", callback_data="new_anketa")],
                [InlineKeyboardButton("📤 Отправить на обработку", callback_data=f"send_to_processing_{anketa_id}")],
                [InlineKeyboardButton("🏠 Вернуться в меню", callback_data="main_menu")]
            ]

            completion_text = f"""
✅ *Анкета успешно сохранена!*

📋 *Номер вашей анкеты:* `{anketa_id}`
{audit_section}
Все ваши ответы сохранены в базе данных.
Вы можете скопировать номер анкеты для дальнейшего использования.

⏰ *Ваша заявка в работе!*
📞 *В течение 48 часов мы свяжемся с вами*

*Что вы хотите сделать дальше?*
"""
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text=completion_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_new_anketa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать заполнение новой анкеты"""
        user = update.effective_user
        user_id = user.id
        
        # Сбрасываем сессию
        total_questions = self.get_total_questions()
        self.user_sessions[user_id] = {
            'state': 'interviewing',
            'current_question': 1,
            'total_questions': total_questions,
            'answers': {},
            'started_at': datetime.now()
        }
        
        # Показываем первый вопрос
        await self.show_question_navigation(update, context, 1)
    
    async def send_anketa_to_processing(self, update: Update, context: ContextTypes.DEFAULT_TYPE, anketa_id: str):
        """Отправить анкету на обработку в n8n"""
        user_id = update.effective_user.id

        try:
            # Отправляем в n8n для обработки
            result = await self.call_n8n_webhook('submit_application', {
                'user_id': user_id,
                'anketa_id': anketa_id,
                'submitted_at': datetime.now().isoformat()
            })

            success_text = f"""
✅ *Анкета отправлена на обработку!*

*ID анкеты:* `{anketa_id}`

*Что происходит дальше:*
1️⃣ Наш ИИ-исследователь анализирует ваши ответы
2️⃣ Проводит исследование рынка и конкурентов
3️⃣ Находит подходящие грантовые возможности
4️⃣ Создает структуру заявки
5️⃣ Подготавливает финальный документ

⏰ *Ваша заявка в работе!*
📞 *В течение 48 часов мы свяжемся с вами*

Спасибо за использование Грантсервиса! 🚀
"""

            keyboard = [[InlineKeyboardButton("🏠 Вернуться в меню", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                text=success_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Ошибка отправки анкеты на обработку: {e}")
            await self.show_error(update, context, f"Ошибка отправки анкеты {anketa_id} на обработку")

    async def _send_interview_pdf_to_admin(self, anketa_id: str, user_id: int, answers: Dict[str, str]):
        """
        Отправить PDF анкеты в админский чат после завершения интервью

        Process:
        1. Загрузить все вопросы из таблицы interview_questions
        2. Сопоставить вопросы с ответами пользователя
        3. Сгенерировать PDF через stage_report_generator
        4. Отправить PDF в админский чат через AdminNotifier

        Args:
            anketa_id: ID анкеты (#AN-YYYYMMDD-username-NNN)
            user_id: Telegram ID пользователя
            answers: Словарь ответов {field_name: answer}
        """
        try:
            logger.info(f"📄 Начинаем генерацию interview PDF для анкеты {anketa_id}")

            # 1. Получаем все вопросы из БД
            questions = get_interview_questions()
            if not questions:
                logger.warning(f"⚠️ Не найдено вопросов для анкеты {anketa_id}")
                return

            # 2. Получаем данные пользователя из БД
            user_info = {'username': 'Unknown', 'first_name': '', 'last_name': ''}
            try:
                with db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT username, first_name, last_name
                        FROM users
                        WHERE telegram_id = %s
                    """, (user_id,))
                    user_row = cursor.fetchone()
                    if user_row:
                        if isinstance(user_row, tuple):
                            user_info = {
                                'username': user_row[0] or 'Unknown',
                                'first_name': user_row[1] or '',
                                'last_name': user_row[2] or ''
                            }
                        else:
                            user_info = {
                                'username': user_row.get('username', 'Unknown'),
                                'first_name': user_row.get('first_name', ''),
                                'last_name': user_row.get('last_name', '')
                            }
                    cursor.close()
            except Exception as e:
                logger.warning(f"⚠️ Не удалось загрузить данные пользователя: {e}")

            # 3. Формируем структурированные Q&A (ПРАВИЛЬНЫЙ ФОРМАТ)
            questions_answers = []
            for question in questions:
                field_name = question.get('field_name', str(question['question_number']))
                answer = answers.get(field_name, "Нет ответа")

                questions_answers.append({
                    'question_id': question['question_number'],  # ИЗМЕНЕНО: question_id вместо question_number
                    'question_text': question['question_text'],
                    'answer': answer
                })

            logger.info(f"✅ Собрано {len(questions_answers)} Q&A для PDF")

            # 4. Подготовка данных для PDF generator (ПРАВИЛЬНЫЙ ФОРМАТ)
            interview_data = {
                'anketa_id': anketa_id,
                'telegram_id': user_id,  # ИЗМЕНЕНО: telegram_id вместо user_id
                'username': user_info['username'],  # ДОБАВЛЕНО
                'first_name': user_info['first_name'],  # ДОБАВЛЕНО
                'last_name': user_info['last_name'],  # ДОБАВЛЕНО
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # ИЗМЕНЕНО: created_at вместо completed_at
                'questions_answers': questions_answers  # ИЗМЕНЕНО: questions_answers вместо qa_list
            }

            # 4. Генерация PDF
            from utils.stage_report_generator import generate_stage_pdf
            pdf_bytes = generate_stage_pdf('interview', interview_data)
            logger.info(f"✅ PDF сгенерирован: {len(pdf_bytes)} bytes")

            # 5. Отправка в админский чат
            from utils.admin_notifications import AdminNotifier
            import os

            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                logger.error("❌ TELEGRAM_BOT_TOKEN не установлен, пропускаем отправку PDF")
                return

            notifier = AdminNotifier(bot_token)

            # Формируем полное имя пользователя
            full_name = f"{user_info['first_name']} {user_info['last_name']}".strip() or user_info['username']
            if not full_name:
                full_name = "Unknown"

            # Формируем caption (лаконичный формат)
            caption = f"""📝 ИНТЕРВЬЮ ЗАВЕРШЕНО

📋 Анкета: {anketa_id}
👤 Пользователь: {full_name} (@{user_info['username']})
🆔 Telegram ID: {user_id}
📅 Дата: {interview_data['created_at']}
✅ Вопросов: {len(questions_answers)}/{len(questions)}

PDF документ с полной анкетой прикреплен

#interview #completed"""

            await notifier.send_stage_completion_pdf(
                stage='interview',
                pdf_bytes=pdf_bytes,
                filename=f"{anketa_id.replace('#', '')}.pdf",
                caption=caption,
                anketa_id=anketa_id
            )

            logger.info(f"✅ Interview PDF успешно отправлен в админский чат: {anketa_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка отправки interview PDF для анкеты {anketa_id}: {e}")
            import traceback
            traceback.print_exc()
            # Не падаем если отправка не удалась - это не критично для workflow

    # ========================================================================
    # NEW: Interactive Interview V2 Methods
    # ========================================================================

    async def handle_start_interview_v2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать интервью V2 с Reference Points"""
        user_id = update.effective_user.id

        # Подготовить user_data
        user_data = {
            'telegram_id': user_id,
            'username': update.effective_user.username or 'unknown',
            'first_name': update.effective_user.first_name or '',
            'last_name': update.effective_user.last_name or '',
            'grant_fund': 'fpg'  # По умолчанию ФПГ
        }

        # Запустить интервью
        await self.interview_handler.start_interview(update, context, user_data)

    async def handle_start_interview_v2_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Начать интервью V2 с мгновенной реакцией

        Отправляет хардкодный первый вопрос сразу (без delay),
        затем инициализирует агента параллельно пока пользователь набирает ответ.
        """
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # 1. МГНОВЕННО отправить хардкодный вопрос про имя (без ожидания инициализации)
        await context.bot.send_message(
            chat_id=chat_id,
            text="Скажите, как Ваше имя, как я могу к Вам обращаться?"
        )
        logger.info(f"[INSTANT] Sent name question to user {user_id}")

        # 2. Создать очередь для ответов
        import asyncio
        answer_queue = asyncio.Queue()

        # 3. Создать минимальную запись в active_interviews
        # (чтобы handle_message мог принимать ответы пока агент инициализируется)
        self.interview_handler.active_interviews[user_id] = {
            'answer_queue': answer_queue,
            'initializing': True
        }

        # 4. Подготовить user_data
        user_data = {
            'telegram_id': user_id,
            'username': update.effective_user.username or 'unknown',
            'first_name': update.effective_user.first_name or '',
            'last_name': update.effective_user.last_name or '',
            'grant_fund': 'fpg'
        }

        # 5. Запустить инициализацию агента и продолжение интервью в фоне
        # Пока пользователь набирает имя, агент инициализируется параллельно
        asyncio.create_task(
            self._init_and_continue_interview(user_id, update, context, user_data, answer_queue)
        )
        logger.info(f"[BACKGROUND] Started agent initialization for user {user_id}")

    async def _init_and_continue_interview(
        self,
        user_id: int,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict[str, Any],
        answer_queue
    ):
        """
        Инициализировать агента и продолжить интервью в фоне

        Параллельно:
        - Пользователь набирает имя
        - Агент инициализируется

        После получения имени и завершения инициализации продолжает интервью.
        """
        import asyncio
        from datetime import datetime

        try:
            # Запустить инициализацию агента параллельно
            logger.info(f"[INIT] Starting agent initialization for user {user_id}")
            init_task = asyncio.create_task(
                self._init_agent_for_user(user_id, user_data)
            )

            # Ждать ответа на вопрос про имя (пока агент инициализируется)
            logger.info(f"[WAITING] Waiting for name from user {user_id}")
            name = await answer_queue.get()
            logger.info(f"[NAME] Received name from user {user_id}: {name}")

            # Сохранить имя в user_data
            user_data['applicant_name'] = name

            # ✅ ITERATION 24: Отметить что имя УЖЕ СОБРАНО
            # Чтобы LLM не спрашивал имя повторно
            user_data['collected_fields'] = {'applicant_name'}
            user_data['covered_topics'] = ['applicant_name', 'greeting']
            logger.info(f"[CONTEXT] Marked 'applicant_name' as collected for user {user_id}")

            # ✅ ITERATION 26: Отправить hardcoded вопрос #2 про суть проекта (INSTANT!)
            # Экономим ~9 секунд на LLM generation
            essence_question = (
                f"{name}, расскажите, пожалуйста, в чем суть вашего проекта? "
                f"Что вы планируете делать и какую главную цель хотите достичь?"
            )

            await context.bot.send_message(
                chat_id=user_id,
                text=essence_question
            )
            logger.info(f"[INSTANT] Sent hardcoded essence question to user {user_id}")

            # Отметить что rp_001_project_essence уже задан
            user_data['covered_topics'].append('project_essence_asked')
            user_data['hardcoded_rps'] = ['rp_001_project_essence']  # Какие RP захардкожены
            logger.info(f"[HARDCODED] Marked rp_001_project_essence as already asked")

            # Дождаться завершения инициализации агента
            logger.info(f"[INIT] Waiting for agent initialization to complete for user {user_id}")
            agent = await init_task
            logger.info(f"[INIT] Agent initialized for user {user_id}")

            # Обновить запись в active_interviews с полными данными
            self.interview_handler.active_interviews[user_id] = {
                'agent': agent,
                'update': update,
                'context': context,
                'user_data': user_data,
                'started_at': datetime.now(),
                'answer_queue': answer_queue
            }

            # Продолжить интервью (второй вопрос)
            logger.info(f"[CONTINUE] Starting interview for user {user_id}")
            await self.interview_handler.continue_interview(update, context)

        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize interview for user {user_id}: {e}")
            import traceback
            traceback.print_exc()

            # Очистить active_interviews
            if user_id in self.interview_handler.active_interviews:
                del self.interview_handler.active_interviews[user_id]

            # Сообщить пользователю
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Произошла ошибка при инициализации интервью: {e}"
            )

    async def _init_agent_for_user(self, user_id: int, user_data: Dict[str, Any]):
        """
        Инициализировать агента для пользователя

        Это долгая операция (~6 секунд):
        - Загрузка embedding модели
        - Подключение к Qdrant
        - Инициализация LLM клиента
        """
        from agents.interactive_interviewer_agent_v2 import InteractiveInterviewerAgentV2

        # Получить LLM провайдер пользователя
        llm_provider = self.interview_handler.db.get_user_llm_preference(user_id)
        logger.info(f"[INIT] User {user_id} LLM provider: {llm_provider}")

        # Создать агента (ДОЛГО - ~6 сек для загрузки embedding модели)
        agent = InteractiveInterviewerAgentV2(
            db=self.interview_handler.db,
            llm_provider=llm_provider,
            qdrant_host="5.35.88.251",
            qdrant_port=6333
        )

        return agent

    async def handle_continue_interview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Продолжить интервью - получить следующий вопрос"""
        await self.interview_handler.continue_interview(update, context)

    async def handle_stop_interview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Остановить интервью"""
        await self.interview_handler.stop_interview(update, context)

    async def handle_show_progress(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать прогресс интервью"""
        await self.interview_handler.show_progress(update, context)

    # ========================================================================
    # GRANT COMMANDS - ProductionWriter Integration
    # ========================================================================

    async def handle_generate_grant(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Генерировать грантовую заявку"""
        # Получить anketa_id из аргументов команды
        anketa_id = None
        if context.args and len(context.args) > 0:
            anketa_id = context.args[0]

        await self.grant_handler.generate_grant(update, context, anketa_id)

    async def handle_get_grant(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить готовую грантовую заявку"""
        # Получить anketa_id из аргументов команды
        anketa_id = None
        if context.args and len(context.args) > 0:
            anketa_id = context.args[0]

        await self.grant_handler.get_grant(update, context, anketa_id)

    async def handle_list_grants(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список грантовых заявок"""
        await self.grant_handler.list_grants(update, context)

    # ========================================================================
    # ITERATION 35: ANKETA MANAGEMENT COMMANDS
    # ========================================================================

    async def handle_my_anketas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список анкет пользователя"""
        await self.anketa_handler.my_anketas(update, context)

    async def handle_delete_anketa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить анкету с подтверждением"""
        await self.anketa_handler.delete_anketa(update, context)

    async def handle_audit_anketa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Провести аудит анкеты"""
        await self.anketa_handler.audit_anketa(update, context)

    async def handle_create_test_anketa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создать тестовую анкету для проверки"""
        await self.anketa_handler.create_test_anketa(update, context)

    async def handle_anketa_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback кнопок для anketa management"""
        await self.anketa_handler.callback_handler(update, context)

    # ========================================================================
    # ITERATION 38: SYNTHETIC CORPUS GENERATOR COMMANDS
    # ========================================================================

    async def handle_generate_synthetic_anketa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Генерация синтетических анкет для корпуса"""
        await self.anketa_handler.generate_synthetic_anketa(update, context)

    async def handle_batch_audit_anketas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Batch аудит анкет с использованием GigaChat Max"""
        await self.anketa_handler.batch_audit_anketas(update, context)

    async def handle_corpus_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику корпуса анкет"""
        await self.anketa_handler.corpus_stats(update, context)

    # ========================================================================

    def run(self):
        """Запуск бота"""
        if not self.token:
            logger.error(self.config.format_log_message(
                "TELEGRAM_BOT_TOKEN не установлен", "❌"
            ))
            logger.error("Пожалуйста, установите переменную окружения TELEGRAM_BOT_TOKEN")
            logger.error(f"Или добавьте её в файл {self.config.env_path}")
            return
        
        # Создаем приложение
        application = Application.builder().token(self.token).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", self.start_command))
        
        # Команды управления токенами
        application.add_handler(CommandHandler("get_access", self.get_access_command))
        application.add_handler(CommandHandler("revoke_access", self.revoke_access_command))
        application.add_handler(CommandHandler("my_access", self.my_access_command))
        
        # Старые команды для совместимости
        application.add_handler(CommandHandler("login", self.login_command))
        application.add_handler(CommandHandler("admin", self.admin_command))

        # NEW: Interactive Interview V2 Commands
        application.add_handler(CommandHandler("start_interview_v2", self.handle_start_interview_v2))
        application.add_handler(CommandHandler("continue", self.handle_continue_interview))
        application.add_handler(CommandHandler("stop_interview", self.handle_stop_interview))
        application.add_handler(CommandHandler("progress", self.handle_show_progress))

        # NEW: Grant Commands - ProductionWriter Integration
        application.add_handler(CommandHandler("generate_grant", self.handle_generate_grant))
        application.add_handler(CommandHandler("get_grant", self.handle_get_grant))
        application.add_handler(CommandHandler("list_grants", self.handle_list_grants))

        # ITERATION 35: Anketa Management Commands
        application.add_handler(CommandHandler("my_anketas", self.handle_my_anketas))
        application.add_handler(CommandHandler("delete_anketa", self.handle_delete_anketa))
        application.add_handler(CommandHandler("audit_anketa", self.handle_audit_anketa))
        application.add_handler(CommandHandler("create_test_anketa", self.handle_create_test_anketa))

        # ITERATION 38: Synthetic Corpus Generator Commands
        application.add_handler(CommandHandler("generate_synthetic_anketa", self.handle_generate_synthetic_anketa))
        application.add_handler(CommandHandler("batch_audit_anketas", self.handle_batch_audit_anketas))
        application.add_handler(CommandHandler("corpus_stats", self.handle_corpus_stats))

        # Обработчики коллбэков и сообщений
        # Anketa management callbacks (проверяем первыми)
        application.add_handler(CallbackQueryHandler(
            self.handle_anketa_callback,
            pattern="^anketa_"
        ))

        # ITERATION 52: Interactive Pipeline callbacks
        application.add_handler(CallbackQueryHandler(
            self.pipeline_handler.handle_start_audit,
            pattern=r"^start_audit:anketa:\w+$"
        ))
        application.add_handler(CallbackQueryHandler(
            self.pipeline_handler.handle_start_grant,
            pattern=r"^start_grant:anketa:\w+$"
        ))
        application.add_handler(CallbackQueryHandler(
            self.pipeline_handler.handle_start_review,
            pattern=r"^start_review:grant:\w+$"
        ))

        # Остальные callbacks
        application.add_handler(CallbackQueryHandler(self.handle_menu_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Запускаем бота
        logger.info(self.config.format_log_message(
            f"Бот запущен на платформе {platform.system()}", "🤖"
        ))
        logger.info("Для остановки нажмите Ctrl+C")
        
        try:
            application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(self.config.format_log_message(
                f"Ошибка при запуске бота: {e}", "❌"
            ))


if __name__ == "__main__":
    bot = GrantServiceBotWithMenu()
    bot.run()