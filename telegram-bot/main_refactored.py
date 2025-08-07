#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ГрантСервис - Telegram Bot (Рефакторенная версия)
Архитектура: Модульная структура с сервисами
"""

import logging
import os
import sys
from typing import Dict, Any
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Добавляем путь к модулям
sys.path.append('/var/GrantService/telegram-bot')

# Импорты конфигурации
from config.settings import BOT_TOKEN, LOG_LEVEL, LOG_FILE
from config.constants import USER_STATES, CALLBACK_DATA

# Импорты сервисов
from services.database_service import DatabaseService

# Импорты утилит
from utils.keyboard_builder import KeyboardBuilder
from utils.text_templates import TextTemplates
from utils.validators import Validators

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=LOG_LEVEL,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GrantServiceBot:
    """Главный класс бота с модульной архитектурой"""
    
    def __init__(self):
        """Инициализация бота"""
        self.token = BOT_TOKEN
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
        
        # Инициализация сервисов
        self.database_service = DatabaseService()
        
        # Инициализация утилит
        self.keyboard_builder = KeyboardBuilder()
        self.text_templates = TextTemplates()
        self.validators = Validators()
        
        # Состояния пользователей (временное хранилище)
        self.user_sessions = {}
        
        logger.info("✅ Бот инициализирован")
    
    def get_user_session(self, user_id: int) -> Dict[str, Any]:
        """Получить или создать сессию пользователя"""
        if user_id not in self.user_sessions:
            total_questions = self.database_service.get_total_questions()
            self.user_sessions[user_id] = {
                'state': USER_STATES['MAIN_MENU'],
                'current_question': 1,
                'total_questions': total_questions,
                'answers': {},
                'session_id': None
            }
        return self.user_sessions[user_id]
    
    def update_user_session(self, user_id: int, **kwargs):
        """Обновить сессию пользователя"""
        session = self.get_user_session(user_id)
        session.update(kwargs)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        try:
            user = update.effective_user
            user_id = user.id
            
            # Регистрируем пользователя в БД
            self.database_service.register_user(
                user_id, 
                user.username, 
                user.first_name, 
                user.last_name
            )
            
            # Создаем сессию в БД
            session_id = self.database_service.create_user_session(user_id)
            self.update_user_session(user_id, session_id=session_id)
            
            # Отправляем приветственное сообщение
            welcome_text = self.text_templates.welcome_message(user.first_name)
            keyboard = self.keyboard_builder.create_main_menu()
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=keyboard
            )
            
            logger.info(f"Пользователь {user_id} запустил бота")
            
        except Exception as e:
            logger.error(f"Ошибка в start_command: {e}")
            await self.show_error(update, context, "Ошибка запуска бота")
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        try:
            keyboard = self.keyboard_builder.create_main_menu()
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "Выберите действие:",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text(
                    "Выберите действие:",
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Ошибка в show_main_menu: {e}")
            await self.show_error(update, context, "Ошибка отображения меню")
    
    async def show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_number: int = 1):
        """Показать вопрос"""
        try:
            user_id = update.effective_user.id
            session = self.get_user_session(user_id)
            
            # Получаем вопрос из БД
            question = self.database_service.get_question_by_number(question_number)
            if not question:
                await self.show_error(update, context, "Вопрос не найден")
                return
            
            # Формируем текст вопроса
            question_text = self.text_templates.question_text(
                question_number,
                session['total_questions'],
                question['question_text'],
                question.get('hint_text')
            )
            
            # Создаем клавиатуру навигации
            keyboard = self.keyboard_builder.create_question_navigation(
                question_number,
                session['total_questions'],
                has_prev=question_number > 1,
                has_next=question_number < session['total_questions']
            )
            
            # Обновляем состояние пользователя
            self.update_user_session(user_id, 
                                   state=USER_STATES['INTERVIEWING'],
                                   current_question=question_number)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    question_text,
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text(
                    question_text,
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Ошибка в show_question: {e}")
            await self.show_error(update, context, "Ошибка отображения вопроса")
    
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать ответ пользователя"""
        try:
            user_id = update.effective_user.id
            session = self.get_user_session(user_id)
            answer_text = update.message.text.strip()
            
            if not answer_text:
                await update.message.reply_text("Пожалуйста, введите ответ на вопрос.")
                return
            
            # Получаем текущий вопрос
            question = self.database_service.get_question_by_number(session['current_question'])
            if not question:
                await self.show_error(update, context, "Вопрос не найден")
                return
            
            # Валидируем ответ
            is_valid, error_message = self.validators.validate_answer(question, answer_text)
            if not is_valid:
                await update.message.reply_text(error_message)
                return
            
            # Сохраняем ответ в БД
            if session.get('session_id'):
                success = self.database_service.save_user_answer(
                    session['session_id'],
                    question['id'],
                    answer_text
                )
                if not success:
                    logger.error(f"Ошибка сохранения ответа для пользователя {user_id}")
            
            # Сохраняем в локальную сессию
            session['answers'][question['field_name']] = answer_text
            
            # Показываем следующий вопрос или экран проверки
            next_question = session['current_question'] + 1
            if next_question <= session['total_questions']:
                await self.show_question(update, context, next_question)
            else:
                await self.show_review_screen(update, context)
                
        except Exception as e:
            logger.error(f"Ошибка в handle_answer: {e}")
            await self.show_error(update, context, "Ошибка обработки ответа")
    
    async def show_review_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать экран проверки"""
        try:
            user_id = update.effective_user.id
            session = self.get_user_session(user_id)
            
            # Формируем текст проверки
            review_text = self.text_templates.review_screen(
                len(session['answers']),
                session['total_questions'],
                session['answers']
            )
            
            # Создаем клавиатуру проверки
            keyboard = self.keyboard_builder.create_review_screen()
            
            # Обновляем состояние
            self.update_user_session(user_id, state=USER_STATES['REVIEW'])
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    review_text,
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text(
                    review_text,
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Ошибка в show_review_screen: {e}")
            await self.show_error(update, context, "Ошибка отображения проверки")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback запросов"""
        try:
            query = update.callback_query
            await query.answer()
            
            callback_data = query.data
            
            if callback_data == CALLBACK_DATA['START_INTERVIEW']:
                await self.show_question(update, context, 1)
                
            elif callback_data == CALLBACK_DATA['BACK_TO_MENU']:
                await self.show_main_menu(update, context)
                
            elif callback_data == CALLBACK_DATA['SUBMIT_APPLICATION']:
                await self.submit_application(update, context)
                
            elif callback_data.startswith(CALLBACK_DATA['NEXT_QUESTION']):
                # Извлекаем номер вопроса из callback_data
                try:
                    question_number = int(callback_data.split('_')[-1])
                    await self.show_question(update, context, question_number)
                except (ValueError, IndexError):
                    await self.show_error(update, context, "Ошибка навигации")
                    
            elif callback_data.startswith(CALLBACK_DATA['PREV_QUESTION']):
                # Извлекаем номер вопроса из callback_data
                try:
                    question_number = int(callback_data.split('_')[-1])
                    await self.show_question(update, context, question_number)
                except (ValueError, IndexError):
                    await self.show_error(update, context, "Ошибка навигации")
                    
            elif callback_data == CALLBACK_DATA['PAYMENT']:
                await self.show_payment_menu(update, context)
                
            elif callback_data == CALLBACK_DATA['STATUS']:
                await self.show_status_menu(update, context)
                
            elif callback_data == CALLBACK_DATA['ABOUT']:
                await self.show_about_menu(update, context)
                
        except Exception as e:
            logger.error(f"Ошибка в handle_callback: {e}")
            await self.show_error(update, context, "Ошибка обработки команды")
    
    async def submit_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправить заявку на проверку"""
        try:
            user_id = update.effective_user.id
            session = self.get_user_session(user_id)
            
            # Здесь будет логика отправки заявки
            success_text = self.text_templates.success_message('application_submitted')
            
            await update.callback_query.edit_message_text(
                success_text,
                reply_markup=self.keyboard_builder.create_main_menu()
            )
            
            # Сбрасываем состояние
            self.update_user_session(user_id, 
                                   state=USER_STATES['MAIN_MENU'],
                                   current_question=1,
                                   answers={})
            
            logger.info(f"Пользователь {user_id} отправил заявку")
            
        except Exception as e:
            logger.error(f"Ошибка в submit_application: {e}")
            await self.show_error(update, context, "Ошибка отправки заявки")
    
    async def show_payment_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню оплаты"""
        try:
            payment_text = self.text_templates.payment_info(5000, "Создание грантовой заявки")
            keyboard = self.keyboard_builder.create_payment_menu()
            
            await update.callback_query.edit_message_text(
                payment_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в show_payment_menu: {e}")
            await self.show_error(update, context, "Ошибка отображения оплаты")
    
    async def show_status_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню статуса"""
        try:
            status_text = self.text_templates.application_status('pending', "Ваша заявка находится в обработке")
            keyboard = self.keyboard_builder.create_status_menu()
            
            await update.callback_query.edit_message_text(
                status_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в show_status_menu: {e}")
            await self.show_error(update, context, "Ошибка отображения статуса")
    
    async def show_about_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню 'О сервисе'"""
        try:
            about_text = self.text_templates.about_service()
            keyboard = self.keyboard_builder.create_about_menu()
            
            await update.callback_query.edit_message_text(
                about_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в show_about_menu: {e}")
            await self.show_error(update, context, "Ошибка отображения информации")
    
    async def show_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: str):
        """Показать сообщение об ошибке"""
        try:
            error_text = self.text_templates.error_message('unknown', error_message)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    error_text,
                    reply_markup=self.keyboard_builder.create_main_menu()
                )
            else:
                await update.message.reply_text(
                    error_text,
                    reply_markup=self.keyboard_builder.create_main_menu()
                )
                
        except Exception as e:
            logger.error(f"Ошибка в show_error: {e}")
    
    def setup_handlers(self, application: Application):
        """Настройка обработчиков"""
        # Команды
        application.add_handler(CommandHandler("start", self.start_command))
        
        # Callback запросы
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Текстовые сообщения
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_answer))
        
        logger.info("✅ Обработчики настроены")
    
    def run(self):
        """Запуск бота"""
        try:
            # Создаем приложение
            application = Application.builder().token(self.token).build()
            
            # Настраиваем обработчики
            self.setup_handlers(application)
            
            # Запускаем бота
            logger.info("🚀 Бот запущен")
            application.run_polling()
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            raise

if __name__ == "__main__":
    bot = GrantServiceBot()
    bot.run() 