#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ГрантСервис - Telegram Bot для создания грантовых заявок
Архитектура: Telegram Bot + n8n + ГигаЧат API
Агенты: Интервьюер → Аудитор → Планировщик → Писатель
"""

import logging
import os
import sys
from typing import Dict, Any
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

class GrantServiceBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.n8n_webhook_url = os.getenv('N8N_WEBHOOK_URL', 'http://localhost:5678/webhook/grant-service')
        self.gigachat_api_key = os.getenv('GIGACHAT_API_KEY')
        
        # Состояния пользователей
        self.user_sessions = {}
        
        # Этапы работы с заявкой
        self.stages = {
            'interview': 'Интервью',
            'audit': 'Аудит',
            'planning': 'Планирование', 
            'writing': 'Написание'
        }
        
        # Инициализация БД и загрузка вопросов
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            # Создаем таблицы и добавляем вопросы по умолчанию
            db.insert_default_questions()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def get_current_question(self, user_id: int) -> Dict[str, Any]:
        """Получить текущий вопрос для пользователя"""
        if user_id not in self.user_sessions:
            return None
        
        session = self.user_sessions[user_id]
        current_question_number = session.get('current_question', 1)
        
        return db.get_question_by_number(current_question_number)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Стартовая команда - приветствие и инструкции"""
        user = update.effective_user
        
        welcome_text = f"""
🤖 *Добро пожаловать в ГрантСервис!*

Привет, {user.first_name}! Я помогу тебе создать профессиональную грантовую заявку за 15-20 минут.

*Как это работает:*
1️⃣ *Интервью* - соберу информацию о твоем проекте
2️⃣ *Аудит* - проанализирую и дам рекомендации  
3️⃣ *Планирование* - создам структуру заявки
4️⃣ *Написание* - сформирую финальный документ

*Команды:*
/start - это сообщение
/interview - начать интервью о проекте
/status - посмотреть статус заявки
/help - помощь

Готов начать? Жми /interview 👇
        """
        
        keyboard = [
            [InlineKeyboardButton("🎤 Начать интервью", callback_data='start_interview')],
            [InlineKeyboardButton("📊 Мой статус", callback_data='check_status')],
            [InlineKeyboardButton("❓ Помощь", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def interview_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск интервью с пользователем"""
        # Поддержка как обычных сообщений, так и callback запросов
        if hasattr(update, 'effective_user') and update.effective_user:
            user_id = update.effective_user.id
        else:
            user_id = update.from_user.id
        
        # Инициализация сессии пользователя
        self.user_sessions[user_id] = {
            'stage': 'interview',
            'current_question': 1,
            'answers': {},
            'started_at': datetime.now().isoformat()
        }
        
        first_question = """
🎤 *Интервью началось!*

Давайте соберем информацию о вашем проекте. Я задам несколько вопросов, отвечайте подробно.

*Вопрос 1 из 7:*
📝 Как называется ваш проект и в чем его суть? Опишите основную идею в 2-3 предложениях.
        """
        
        await update.message.reply_text(first_question, parse_mode='Markdown')

    async def start_interview_callback(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Запуск интервью через callback кнопку"""
        user_id = query.from_user.id
        
        # Инициализация сессии пользователя
        self.user_sessions[user_id] = {
            'stage': 'interview',
            'current_question': 1,
            'answers': {},
            'started_at': datetime.now().isoformat()
        }
        
        # Получаем первый вопрос из БД
        question = self.get_current_question(user_id)
        if not question:
            await query.answer("❌ Ошибка загрузки вопросов")
            return
        
        # Формируем сообщение с вопросом
        question_text = f"""
🎤 *Интервью началось!*

Давайте соберем информацию о вашем проекте. Я задам несколько вопросов, отвечайте подробно.

*Вопрос {question['question_number']}:*
{question['question_text']}
        """
        
        if question['hint_text']:
            question_text += f"\n\n💡 *Подсказка:* {question['hint_text']}"
        
        await query.edit_message_text(question_text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений от пользователя"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Проверяем, есть ли активная сессия
        if user_id not in self.user_sessions:
            await update.message.reply_text(
                "Для начала работы используйте команду /start"
            )
            return
            
        session = self.user_sessions[user_id]
        stage = session['stage']
        
        if stage == 'interview':
            await self.process_interview_answer(update, context)
        elif stage == 'audit':
            await update.message.reply_text(
                "Заявка на этапе аудита. Пожалуйста, подождите..."
            )
        else:
            await update.message.reply_text(
                f"Заявка на этапе: {self.stages.get(stage, 'неизвестно')}"
            )

    async def process_interview_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ответов пользователя в интервью"""
        user_id = update.effective_user.id
        message_text = update.message.text
        session = self.user_sessions[user_id]
        
        current_q = session['current_question']
        
        # Валидация ответа через БД
        current_question = self.get_current_question(user_id)
        if current_question:
            validation_result = db.validate_answer(current_question['id'], message_text)
            if not validation_result['is_valid']:
                await update.message.reply_text(
                    f"❌ {validation_result['message']}\n\nПопробуйте еще раз:",
                    parse_mode='Markdown'
                )
                return
        
        # Сохраняем ответ
        session['answers'][f'question_{current_q}'] = message_text
        
        # Получаем следующий вопрос
        next_question_number = current_q + 1
        next_question = db.get_question_by_number(next_question_number)
        
        if next_question:
            # Обновляем номер текущего вопроса
            session['current_question'] = next_question_number
            
            # Формируем следующий вопрос
            question_text = f"""
✅ *Ответ принят!*

*Вопрос {next_question['question_number']}:*
{next_question['question_text']}
            """
            
            if next_question['hint_text']:
                question_text += f"\n\n💡 *Подсказка:* {next_question['hint_text']}"
            
            await update.message.reply_text(question_text, parse_mode='Markdown')
        else:
            # Интервью завершено
            await self.complete_interview(update, context)

    async def complete_interview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Завершение интервью и переход к аудиту"""
        user_id = update.effective_user.id
        session = self.user_sessions[user_id]
        
        completion_text = """
🎉 *Интервью завершено!*

Отличная работа! Я собрал всю необходимую информацию о вашем проекте.

*Что дальше:*
🔍 Сейчас агент-аудитор проанализирует информацию
📊 Даст оценку и рекомендации по улучшению
📋 После этого создадим структуру заявки

⏱️ Анализ займет 1-2 минуты...
        """
        
        keyboard = [
            [InlineKeyboardButton("🔍 Запустить аудит", callback_data='start_audit')],
            [InlineKeyboardButton("📝 Посмотреть ответы", callback_data='view_answers')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        session['stage'] = 'ready_for_audit'
        
        await update.message.reply_text(
            completion_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на inline кнопки"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        user_id = query.from_user.id
        
        if callback_data == 'start_interview':
            await self.start_interview_callback(query, context)
        elif callback_data == 'start_audit':
            await self.start_audit_process(query, context)
        elif callback_data == 'check_status':
            await self.show_status(query, context)
        elif callback_data == 'help':
            await self.show_help(query, context)
        elif callback_data == 'view_answers':
            await self.show_answers(query, context)

    async def start_audit_process(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Запуск процесса аудита через n8n"""
        user_id = query.from_user.id
        session = self.user_sessions.get(user_id, {})
        
        audit_text = """
🔍 *Запускаю аудит заявки...*

Агент-аудитор анализирует:
✅ Инновационность проекта
✅ Реалистичность планов
✅ Компетенции команды  
✅ Потенциальное воздействие
✅ Устойчивость проекта

⏱️ Пожалуйста, подождите...
        """
        
        await query.edit_message_text(audit_text, parse_mode='Markdown')
        
        # Здесь будет вызов n8n webhook для обработки через ГигаЧат
        try:
            audit_result = await self.call_n8n_webhook('audit', session['answers'])
            
            # Показываем результат аудита
            await self.show_audit_results(query, context, audit_result)
            
        except Exception as e:
            logger.error(f"Ошибка при вызове аудита: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при аудите. Попробуйте позже."
            )

    async def call_n8n_webhook(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Вызов n8n webhook для обработки через ГигаЧат"""
        payload = {
            'action': action,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # TODO: Реализовать после настройки n8n
        # response = requests.post(self.n8n_webhook_url, json=payload)
        # return response.json()
        
        # Заглушка для тестирования
        return {
            'success': True,
            'result': 'Аудит выполнен успешно',
            'scores': {
                'innovation': 8,
                'realism': 7,
                'team': 9,
                'impact': 8,
                'sustainability': 6
            }
        }

    async def show_audit_results(self, query, context: ContextTypes.DEFAULT_TYPE, audit_result: Dict[str, Any]):
        """Показ результатов аудита"""
        scores = audit_result.get('scores', {})
        
        result_text = f"""
📊 *Результаты аудита заявки*

*Оценки по критериям (1-10):*
🚀 Инновационность: {scores.get('innovation', 0)}/10
✅ Реалистичность: {scores.get('realism', 0)}/10  
👥 Команда: {scores.get('team', 0)}/10
🎯 Воздействие: {scores.get('impact', 0)}/10
🔄 Устойчивость: {scores.get('sustainability', 0)}/10

*Общая оценка: {sum(scores.values())//len(scores)}/10*

*Рекомендации агента-аудитора:*
• Укрепите команду экспертом по устойчивости
• Добавьте больше конкретных метрик успеха
• Проработайте план продолжения после гранта

Готовы перейти к планированию структуры заявки?
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 Создать план заявки", callback_data='start_planning')],
            [InlineKeyboardButton("🔙 К началу", callback_data='back_to_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            result_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def show_status(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Показ текущего статуса заявки пользователя"""
        user_id = query.from_user.id
        session = self.user_sessions.get(user_id)
        
        if not session:
            status_text = "У вас пока нет активных заявок. Начните с команды /start"
        else:
            stage = session.get('stage', 'unknown')
            status_text = f"""
📋 *Статус вашей заявки*

Текущий этап: {self.stages.get(stage, stage)}
Начато: {session.get('started_at', 'неизвестно')}

*Прогресс:*
{'✅' if stage != 'interview' else '🔄'} Интервью
{'✅' if stage in ['audit', 'planning', 'writing'] else '⏳'} Аудит  
{'✅' if stage in ['planning', 'writing'] else '⏳'} Планирование
{'✅' if stage == 'writing' else '⏳'} Написание
            """
        
        await query.edit_message_text(status_text, parse_mode='Markdown')

    async def show_help(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Показ справки"""
        help_text = """
❓ *Справка по ГрантСервису*

*Команды бота:*
/start - начать работу
/interview - запустить интервью
/status - статус заявки
/help - эта справка

*Этапы работы:*
1️⃣ *Интервью* - 7 вопросов о проекте
2️⃣ *Аудит* - анализ и оценка (ИИ)
3️⃣ *Планирование* - структура заявки (ИИ) 
4️⃣ *Написание* - готовый документ (ИИ)

*Время работы:* 15-20 минут
*Результат:* Готовая грантовая заявка

По вопросам: @support_bot
        """
        
        await query.edit_message_text(help_text, parse_mode='Markdown')

    async def show_answers(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Показ ответов пользователя из интервью"""
        user_id = query.from_user.id
        session = self.user_sessions.get(user_id, {})
        answers = session.get('answers', {})
        
        if not answers:
            await query.edit_message_text("Интервью еще не проводилось.")
            return
            
        answers_text = "📝 *Ваши ответы из интервью:*\n\n"
        
        questions = [
            "Название и суть проекта",
            "Грант и фонд", 
            "Целевая аудитория",
            "Бюджет и сроки",
            "Команда и компетенции", 
            "Уникальность проекта",
            "Измерение результатов"
        ]
        
        for i, (key, answer) in enumerate(answers.items(), 1):
            if i <= len(questions):
                answers_text += f"*{i}. {questions[i-1]}:*\n{answer}\n\n"
        
        await query.edit_message_text(answers_text, parse_mode='Markdown')

    def run(self):
        """Запуск бота"""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN не установлен!")
            return
            
        application = Application.builder().token(self.token).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("interview", self.interview_command))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("ГрантСервис бот запущен!")
        application.run_polling()

if __name__ == '__main__':
    bot = GrantServiceBot()
    bot.run() 