#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Валидация данных для Telegram Bot
"""

import re
from typing import Dict, Any, Tuple, Optional

class Validators:
    """Класс для валидации данных"""
    
    @staticmethod
    def validate_answer(question_data: Dict[str, Any], answer: str) -> Tuple[bool, str]:
        """Валидация ответа на вопрос"""
        if not answer or not answer.strip():
            if question_data.get('is_required', False):
                return False, "Это обязательный вопрос. Пожалуйста, дайте ответ."
            return True, ""
        
        answer = answer.strip()
        
        # Проверка длины
        min_length = question_data.get('validation_rules', {}).get('min_length', 0)
        max_length = question_data.get('validation_rules', {}).get('max_length', 2000)
        
        if len(answer) < min_length:
            return False, f"Ответ слишком короткий. Минимальная длина: {min_length} символов."
        
        if len(answer) > max_length:
            return False, f"Ответ слишком длинный. Максимальная длина: {max_length} символов."
        
        # Проверка типа вопроса
        question_type = question_data.get('question_type', 'text')
        
        if question_type == 'number':
            if not Validators._is_valid_number(answer):
                return False, "Пожалуйста, введите число."
            
            # Проверка диапазона для чисел
            min_value = question_data.get('validation_rules', {}).get('min_value')
            max_value = question_data.get('validation_rules', {}).get('max_value')
            
            try:
                num_value = float(answer)
                if min_value is not None and num_value < min_value:
                    return False, f"Значение должно быть не меньше {min_value}."
                if max_value is not None and num_value > max_value:
                    return False, f"Значение должно быть не больше {max_value}."
            except ValueError:
                return False, "Пожалуйста, введите корректное число."
        
        elif question_type == 'date':
            if not Validators._is_valid_date(answer):
                return False, "Пожалуйста, введите корректную дату в формате ДД.ММ.ГГГГ."
        
        elif question_type == 'select':
            options = question_data.get('validation_rules', {}).get('options', [])
            if options and answer not in options:
                return False, f"Пожалуйста, выберите один из вариантов: {', '.join(options)}."
        
        return True, ""
    
    @staticmethod
    def _is_valid_number(value: str) -> bool:
        """Проверка, является ли значение числом"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _is_valid_date(value: str) -> bool:
        """Проверка, является ли значение корректной датой"""
        # Простая проверка формата ДД.ММ.ГГГГ
        pattern = r'^\d{2}\.\d{2}\.\d{4}$'
        if not re.match(pattern, value):
            return False
        
        try:
            day, month, year = map(int, value.split('.'))
            if year < 1900 or year > 2100:
                return False
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            return True
        except ValueError:
            return False
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Очистка текста от потенциально опасных символов"""
        if not text:
            return ""
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Удаляем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Обрезаем пробелы в начале и конце
        text = text.strip()
        
        return text 