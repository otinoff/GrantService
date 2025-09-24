
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

# Добавляем путь к модулю БД
sys.path.insert(0, config.base_path)

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
        """Стартовая команда - показывает главное меню"""
        user = update.effective_user
        user_id = user.id
        
        # Проверка авторизации
        if not self.is_user_authorized(user_id):
            await update.message.reply_text("❌ Доступ запрещен. Обратитесь к администратору.")
            return
        
        # Сброс сессии при /start
        total_questions = self.get_total_questions()
        self.user_sessions[user_id] = {
            'state': 'main_menu',
            'current_question': 1,
            'total_questions': total_questions,
            'answers': {},
            'started_at': datetime.now()
        }
        
        await self.show_main_menu(update, context)
    
    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для получения ссылки авторизации в админ панель"""
        user = update.effective_user
        user_id = user.id
        
        logger.info(self.config.format_log_message(
            f"Получена команда /login от пользователя {user_id} ({user.username})", "📥"
        ))
        
        # Проверка авторизации
        if not self.is_user_authorized(user_id):
            logger.warning(self.config.format_log_message(
                f"Доступ запрещен для пользователя {user_id}", "❌"
            ))
            await update.message.reply_text("❌ Доступ запрещен. Обратитесь к администратору.")
            return
        
        # Генерируем токен авторизации
        try:
            # Получаем или создаем токен для пользователя
            from data.database import db
            token = db.get_or_create_login_token(user_id)
            logger.info(self.config.format_log_message(
                f"Получен токен для пользователя {user_id}: {token[:20] if token else 'None'}", "🔑"
            ))
            
            if token:
                # Формируем ссылку для входа в админ панель
                admin_url = f"https://admin.grantservice.onff.ru?token={token}"
                logger.info(self.config.format_log_message(
                    f"Сформирована ссылка для пользователя {user_id}: {admin_url[:50]}...", "🔗"
                ))
                
                login_text = f"""
🔐 *Ссылка для входа в админ панель*

⚠️ **Внимание! Ни с кем не делитесь этой ссылкой!**

🔗 Нажмите на ссылку для авторизации:
`{admin_url}`

⚠️ Ссылка действительна 24 часа
🔒 Не передавайте ссылку посторонним
"""
                
                await update.message.reply_text(
                    text=login_text,
                    parse_mode='Markdown'
                )
            else:
                logger.error(self.config.format_log_message(
                    f"Ошибка генерации токена для пользователя {user_id}", "❌"
                ))
                await update.message.reply_text("❌ Ошибка генерации токена. Попробуйте позже.")
                
        except Exception as e:
            logger.error(self.config.format_log_message(
                f"Ошибка генерации ссылки авторизации для пользователя {user_id}: {e}", "❌"
            ))
            import traceback
            traceback.print_exc()
            await update.message.reply_text("❌ Ошибка генерации ссылки. Попробуйте позже.")
    
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
        
        # Создаем клавиатуру с 4 кнопками
        keyboard = [
            [InlineKeyboardButton("📝 Начать заполнение", callback_data="start_interview")],
            [InlineKeyboardButton("💳 Оплата", callback_data="payment")],
            [InlineKeyboardButton("📊 Статус заявки", callback_data="status")],
            [InlineKeyboardButton("ℹ️ О Грантсервисе", callback_data="about")]
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

{f"💡 *Подсказка:* {question['hint_text']}" if question.get('hint_text') else ""}
"""
        
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
        
        if callback_data == "start_interview":
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
            
        elif callback_data == "about":
            # Информация о сервисе
            about_text = """
ℹ️ *О Грантсервисе*

*Грантсервис* - это интеллектуальная система создания грантовых заявок с использованием ИИ.

*Наши преимущества:*
• 🤖 ИИ-ассистент для анализа проектов
• ⚡ Быстрое создание заявок (15-20 минут)
• 📊 Профессиональная структура документов
• 💡 Персональные рекомендации
• 📄 Готовые документы в PDF

*Веб-сайт:* https://grantservice.onff.ru
*Поддержка:* @otinoff_support
"""
            await query.edit_message_text(
                text=about_text,
                parse_mode='Markdown'
            )
            
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

*Время обработки:* 2-4 часа
*Уведомления:* Вы получите сообщение о готовности

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
        
        # Проверка авторизации
        if not self.is_user_authorized(user_id):
            await update.message.reply_text("❌ Доступ запрещен. Обратитесь к администратору.")
            return
        
        session = self.get_user_session(user_id)
        
        if session['state'] != 'interviewing':
            # Если не в режиме интервью, показываем главное меню
            await self.show_main_menu(update, context)
            return
        
        # Сохраняем ответ на текущий вопрос
        current_question = session['current_question']
        answer = update.message.text
        
        # Получаем field_name для текущего вопроса
        question_info = self.get_question_by_number(current_question)
        if question_info and question_info.get('field_name'):
            field_name = question_info['field_name']
        else:
            # Fallback на номер вопроса, если field_name не найден
            field_name = str(current_question)
        
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
                await self.show_completion_screen(update, context, anketa_id)
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
                return anketa_id
            else:
                logger.error(f"Не удалось сохранить анкету для пользователя {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка автосохранения анкеты: {e}")
            return None
    
    async def show_completion_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, anketa_id: str):
        """Показать экран успешного завершения анкеты"""
        user_id = update.effective_user.id
        session = self.get_user_session(user_id)
        
        # Создаем клавиатуру с опциями
        keyboard = [
            [InlineKeyboardButton("📝 Заполнить новую анкету", callback_data="new_anketa")],
            [InlineKeyboardButton("📤 Отправить на обработку", callback_data=f"send_to_processing_{anketa_id}")],
            [InlineKeyboardButton("🏠 Вернуться в меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        completion_text = f"""
✅ *Анкета успешно сохранена!*

📋 *Номер вашей анкеты:*
`{anketa_id}`

Все ваши ответы сохранены в базе данных.
Вы можете скопировать номер анкеты для дальнейшего использования.

*Что вы хотите сделать дальше?*
"""
        
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

*Время обработки:* 2-4 часа
*Уведомления:* Вы получите сообщение о готовности

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
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("login", self.login_command))
        application.add_handler(CommandHandler("admin", self.admin_command))
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