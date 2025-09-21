#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ГрантСервис - Telegram Bot с интерактивным меню
Архитектура: Telegram Bot + n8n + ГигаЧат API
Меню: Главное → Навигация → Проверка
"""

import logging
import os
import sys
from typing import Dict, Any, Optional
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

# Добавляем путь к модулю БД
sys.path.append('/var/GrantService/data')
from database import db

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/var/GrantService/logs/telegram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GrantServiceBotWithMenu:
    def __init__(self):
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
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            db.insert_default_questions()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def get_user_session(self, user_id: int) -> Dict[str, Any]:
        """Получить или создать сессию пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'state': 'main_menu',
                'current_question': 1,
                'total_questions': len(db.get_active_questions()),
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
        
        # Сброс сессии при /start
        self.user_sessions[user_id] = {
            'state': 'main_menu',
            'current_question': 1,
            'total_questions': len(db.get_active_questions()),
            'answers': {},
            'started_at': datetime.now()
        }
        
        await self.show_main_menu(update, context)
    
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
        
        # Получаем вопрос
        question = db.get_question_by_number(question_number)
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
    
    async def show_application_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статус заявки"""
        user_id = update.effective_user.id
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
        
        # Отправляем в n8n для обработки
        try:
            result = await self.call_n8n_webhook('submit_application', {
                'user_id': user_id,
                'answers': session['answers'],
                'submitted_at': datetime.now().isoformat()
            })
            
            success_text = """
✅ *Заявка отправлена на проверку!*

Ваша заявка успешно отправлена в обработку. 

*Что происходит дальше:*
1️⃣ Наш ИИ-ассистент анализирует ваши ответы
2️⃣ Генерирует структуру заявки
3️⃣ Создает рекомендации по улучшению
4️⃣ При необходимости задаст уточняющие вопросы
5️⃣ Подготовит финальный документ в PDF

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
        session = self.get_user_session(user_id)
        
        if session['state'] != 'interviewing':
            # Если не в режиме интервью, показываем главное меню
            await self.show_main_menu(update, context)
            return
        
        # Сохраняем ответ на текущий вопрос
        current_question = session['current_question']
        answer = update.message.text
        
        # Валидация ответа
        question = db.get_question_by_number(current_question)
        if question:
            validation = db.validate_answer(question['id'], answer)
            if not validation['is_valid']:
                await update.message.reply_text(
                    f"❌ {validation['error_message']}\nПопробуйте еще раз."
                )
                return
        
        # Сохраняем ответ
        session['answers'][current_question] = answer
        
        # Переходим к следующему вопросу или показываем экран проверки
        if current_question < session['total_questions']:
            await self.show_question_navigation(update, context, current_question + 1)
        else:
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
    
    def run(self):
        """Запуск бота"""
        if not self.token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
            return
        
        # Создаем приложение
        application = Application.builder().token(self.token).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CallbackQueryHandler(self.handle_menu_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Запускаем бота
        logger.info("🤖 Бот запущен с интерактивным меню")
        application.run_polling()

if __name__ == "__main__":
    bot = GrantServiceBotWithMenu()
    bot.run() 