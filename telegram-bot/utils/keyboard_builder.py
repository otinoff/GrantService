#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для создания клавиатур Telegram Bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.constants import CALLBACK_DATA

class KeyboardBuilder:
    """Класс для создания клавиатур"""
    
    @staticmethod
    def create_main_menu() -> InlineKeyboardMarkup:
        """Создание главного меню"""
        keyboard = [
            [
                InlineKeyboardButton("Начать интервью", callback_data=CALLBACK_DATA['START_INTERVIEW']),
                InlineKeyboardButton("Оплата", callback_data=CALLBACK_DATA['PAYMENT'])
            ],
            [
                InlineKeyboardButton("Статус заявки", callback_data=CALLBACK_DATA['STATUS']),
                InlineKeyboardButton("О сервисе", callback_data=CALLBACK_DATA['ABOUT'])
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_question_navigation(current_question: int, total_questions: int, has_prev: bool = True, has_next: bool = True) -> InlineKeyboardMarkup:
        """Создание навигации по вопросам"""
        keyboard = []
        
        # Навигационные кнопки
        nav_row = []
        if has_prev and current_question > 1:
            nav_row.append(InlineKeyboardButton("← Назад", callback_data=f"{CALLBACK_DATA['PREV_QUESTION']}_{current_question-1}"))
        
        nav_row.append(InlineKeyboardButton(f"{current_question}/{total_questions}", callback_data="question_number"))
        
        if has_next and current_question < total_questions:
            nav_row.append(InlineKeyboardButton("Далее →", callback_data=f"{CALLBACK_DATA['NEXT_QUESTION']}_{current_question+1}"))
        
        if nav_row:
            keyboard.append(nav_row)
        
        # Кнопки управления
        control_row = [
            InlineKeyboardButton("Главное меню", callback_data=CALLBACK_DATA['BACK_TO_MENU']),
            InlineKeyboardButton("Проверить", callback_data=CALLBACK_DATA['SUBMIT_APPLICATION'])
        ]
        keyboard.append(control_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_review_screen() -> InlineKeyboardMarkup:
        """Создание клавиатуры экрана проверки"""
        keyboard = [
            [
                InlineKeyboardButton("Отправить на проверку", callback_data=CALLBACK_DATA['SUBMIT_APPLICATION']),
                InlineKeyboardButton("Редактировать", callback_data="edit_answers")
            ],
            [
                InlineKeyboardButton("Главное меню", callback_data=CALLBACK_DATA['BACK_TO_MENU'])
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_status_menu() -> InlineKeyboardMarkup:
        """Создание меню статуса"""
        keyboard = [
            [
                InlineKeyboardButton("Обновить статус", callback_data="refresh_status"),
                InlineKeyboardButton("Связаться с поддержкой", callback_data="contact_support")
            ],
            [
                InlineKeyboardButton("Главное меню", callback_data=CALLBACK_DATA['BACK_TO_MENU'])
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_payment_menu() -> InlineKeyboardMarkup:
        """Создание меню оплаты"""
        keyboard = [
            [
                InlineKeyboardButton("Оплатить картой", callback_data="pay_card"),
                InlineKeyboardButton("Оплатить СБП", callback_data="pay_sbp")
            ],
            [
                InlineKeyboardButton("Проверить оплату", callback_data="check_payment"),
                InlineKeyboardButton("Главное меню", callback_data=CALLBACK_DATA['BACK_TO_MENU'])
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_about_menu() -> InlineKeyboardMarkup:
        """Создание меню 'О сервисе'"""
        keyboard = [
            [
                InlineKeyboardButton("Как это работает", callback_data="how_it_works"),
                InlineKeyboardButton("Примеры заявок", callback_data="examples")
            ],
            [
                InlineKeyboardButton("Отзывы клиентов", callback_data="reviews"),
                InlineKeyboardButton("Контакты", callback_data="contacts")
            ],
            [
                InlineKeyboardButton("Главное меню", callback_data=CALLBACK_DATA['BACK_TO_MENU'])
            ]
        ]
        return InlineKeyboardMarkup(keyboard) 