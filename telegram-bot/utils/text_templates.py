#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Шаблоны текстов для Telegram Bot
"""

from typing import Dict, Any, List

class TextTemplates:
    """Класс для шаблонов текстов"""
    
    @staticmethod
    def welcome_message(user_name: str = None) -> str:
        """Шаблон приветственного сообщения"""
        if user_name:
            return f"""Привет, {user_name}! 

Добро пожаловать в ГрантСервис - ваш помощник в создании профессиональных грантовых заявок.

Что мы делаем:
• Проводим детальное интервью о вашем проекте
• Исследуем контекст и находим похожие проекты
• Создаем профессиональную заявку на грант
• Проводим аудит качества и даем рекомендации

Готовы начать? Выберите действие в меню ниже."""
        else:
            return """Добро пожаловать в ГрантСервис!

Ваш помощник в создании профессиональных грантовых заявок.

Что мы делаем:
• Проводим детальное интервью о вашем проекте
• Исследуем контекст и находим похожие проекты
• Создаем профессиональную заявку на грант
• Проводим аудит качества и даем рекомендации

Готовы начать? Выберите действие в меню ниже."""
    
    @staticmethod
    def question_text(question_number: int, total_questions: int, question_text: str, hint_text: str = None) -> str:
        """Шаблон текста вопроса"""
        text = f"""Вопрос {question_number} из {total_questions}

{question_text}"""
        
        if hint_text:
            text += f"\n\n💡 Подсказка: {hint_text}"
        
        return text
    
    @staticmethod
    def review_screen(filled_questions: int, total_questions: int, answers: Dict[str, Any]) -> str:
        """Шаблон экрана проверки"""
        progress_percent = int((filled_questions / total_questions) * 100)
        
        text = f"""📋 Проверка заполнения анкеты

Прогресс: {filled_questions}/{total_questions} ({progress_percent}%)

Ваши ответы:"""
        
        # Добавляем краткую сводку ответов
        for field_name, answer in answers.items():
            if answer:
                # Обрезаем длинные ответы
                short_answer = answer[:50] + "..." if len(answer) > 50 else answer
                text += f"\n• {field_name}: {short_answer}"
        
        text += "\n\nПроверьте правильность ответов и нажмите 'Отправить на проверку' для создания заявки."
        
        return text
    
    @staticmethod
    def application_status(status: str, details: str = None) -> str:
        """Шаблон статуса заявки"""
        status_emojis = {
            'pending': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'rejected': '❌',
            'review': '👀'
        }
        
        emoji = status_emojis.get(status, '📋')
        
        text = f"{emoji} Статус вашей заявки: {status.title()}"
        
        if details:
            text += f"\n\n{details}"
        
        return text
    
    @staticmethod
    def payment_info(amount: float, description: str) -> str:
        """Шаблон информации об оплате"""
        return f"""💳 Оплата услуг

Сумма: {amount} ₽
Описание: {description}

Выберите способ оплаты:"""
    
    @staticmethod
    def about_service() -> str:
        """Шаблон информации о сервисе"""
        return """ℹ️ О ГрантСервисе

Мы помогаем создавать профессиональные грантовые заявки с использованием искусственного интеллекта.

Наши преимущества:
• Детальное интервью о вашем проекте
• Исследование контекста и похожих проектов
• Создание структурированной заявки
• Аудит качества и рекомендации
• Поддержка на всех этапах

Выберите раздел для получения подробной информации:"""
    
    @staticmethod
    def error_message(error_type: str, details: str = None) -> str:
        """Шаблон сообщения об ошибке"""
        error_templates = {
            'database': '❌ Ошибка базы данных',
            'network': '🌐 Ошибка сети',
            'validation': '⚠️ Ошибка валидации',
            'unknown': '❓ Неизвестная ошибка'
        }
        
        text = error_templates.get(error_type, '❌ Ошибка')
        
        if details:
            text += f"\n\n{details}"
        
        text += "\n\nПопробуйте еще раз или обратитесь в поддержку."
        
        return text
    
    @staticmethod
    def success_message(action: str) -> str:
        """Шаблон сообщения об успехе"""
        success_templates = {
            'answer_saved': '✅ Ответ сохранен!',
            'application_submitted': '✅ Заявка отправлена на проверку!',
            'payment_successful': '✅ Оплата прошла успешно!',
            'status_updated': '✅ Статус обновлен!'
        }
        
        return success_templates.get(action, '✅ Операция выполнена успешно!') 