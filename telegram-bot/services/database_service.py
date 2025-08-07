#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервис для работы с базой данных
"""

import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Добавляем путь к модулю БД
sys.path.append('/var/GrantService/data')
from database import db

logger = logging.getLogger(__name__)

class DatabaseService:
    """Сервис для работы с базой данных"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            db.insert_default_questions()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def get_total_questions(self) -> int:
        """Получить общее количество вопросов"""
        try:
            # Простой способ подсчета вопросов - получаем максимальный номер
            max_question = 0
            for i in range(1, 100):  # Проверяем до 100 вопросов
                question = db.get_question_by_number(i)
                if question:
                    max_question = i
                else:
                    break
            return max_question
        except Exception as e:
            logger.error(f"Ошибка подсчета вопросов: {e}")
            return 24  # Возвращаем примерное количество по умолчанию
    
    def get_question_by_number(self, question_number: int) -> Optional[Dict[str, Any]]:
        """Получить вопрос по номеру"""
        try:
            return db.get_question_by_number(question_number)
        except Exception as e:
            logger.error(f"Ошибка получения вопроса {question_number}: {e}")
            return None
    
    def get_active_questions(self) -> List[Dict[str, Any]]:
        """Получить все активные вопросы"""
        try:
            return db.get_active_questions()
        except Exception as e:
            logger.error(f"Ошибка получения активных вопросов: {e}")
            return []
    
    def validate_answer(self, question_id: int, answer: str) -> Dict[str, Any]:
        """Валидация ответа"""
        try:
            return db.validate_answer(question_id, answer)
        except Exception as e:
            logger.error(f"Ошибка валидации ответа: {e}")
            return {"is_valid": False, "message": "Ошибка валидации"}
    
    def save_user_answer(self, session_id: int, question_id: int, answer_text: str) -> bool:
        """Сохранить ответ пользователя"""
        try:
            return db.save_user_answer(session_id, question_id, answer_text)
        except Exception as e:
            logger.error(f"Ошибка сохранения ответа: {e}")
            return False
    
    def create_user_session(self, telegram_id: int) -> int:
        """Создать сессию пользователя"""
        try:
            return db.create_session(telegram_id)
        except Exception as e:
            logger.error(f"Ошибка создания сессии: {e}")
            return 0
    
    def get_user_session(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить сессию пользователя"""
        try:
            sessions = db.get_user_sessions(telegram_id)
            if sessions:
                return sessions[0]  # Возвращаем последнюю активную сессию
            return None
        except Exception as e:
            logger.error(f"Ошибка получения сессии пользователя {telegram_id}: {e}")
            return None
    
    def get_session_progress(self, session_id: int) -> Dict[str, Any]:
        """Получить прогресс сессии"""
        try:
            return db.get_session_progress(session_id)
        except Exception as e:
            logger.error(f"Ошибка получения прогресса сессии {session_id}: {e}")
            return {}
    
    def get_user_answers(self, session_id: int) -> List[Dict[str, Any]]:
        """Получить ответы пользователя"""
        try:
            return db.get_user_answers(session_id)
        except Exception as e:
            logger.error(f"Ошибка получения ответов пользователя: {e}")
            return []
    
    def register_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Зарегистрировать пользователя"""
        try:
            return db.register_user(telegram_id, username, first_name, last_name)
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя {telegram_id}: {e}")
            return False
    
    def get_users_statistics(self) -> Dict[str, Any]:
        """Получить статистику пользователей"""
        try:
            return db.get_users_statistics()
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Получить активные сессии"""
        try:
            return db.get_active_sessions()
        except Exception as e:
            logger.error(f"Ошибка получения активных сессий: {e}")
            return []
    
    def get_completed_sessions(self) -> List[Dict[str, Any]]:
        """Получить завершенные сессии"""
        try:
            return db.get_completed_sessions()
        except Exception as e:
            logger.error(f"Ошибка получения завершенных сессий: {e}")
            return []
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получить всех пользователей"""
        try:
            return db.get_all_users()
        except Exception as e:
            logger.error(f"Ошибка получения пользователей: {e}")
            return [] 