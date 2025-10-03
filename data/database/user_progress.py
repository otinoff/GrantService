#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Функции для работы с прогрессом пользователей в анкете
"""

import sqlite3
import json
import os
from typing import Dict, List, Optional, Tuple
from .models import GrantServiceDatabase

# Определяем путь к базе данных в зависимости от платформы
if os.name == 'nt':  # Windows
    DB_PATH = "C:/SnowWhiteAI/GrantService/data/grantservice.db"
else:  # Linux/Unix
    DB_PATH = "/var/GrantService/data/grantservice.db"

def get_user_progress(telegram_id: int) -> Dict:
    """
    Получить прогресс пользователя по анкете
    Возвращает: {
        'total_questions': int,
        'answered_questions': int,
        'progress_percent': float,
        'current_question': int,
        'status': str
    }
    """
    db = GrantServiceDatabase(DB_PATH)
    
    with db.connect() as conn:
        cursor = conn.cursor()
        
        # Получаем все сессии пользователя
        cursor.execute("""
            SELECT interview_data, collected_data, status 
            FROM sessions 
            WHERE telegram_id = ? 
            ORDER BY started_at DESC
        """, (telegram_id,))
        
        sessions = cursor.fetchall()
        
        # Получаем общее количество вопросов
        cursor.execute("SELECT COUNT(*) FROM interview_questions WHERE is_active = 1")
        total_questions = cursor.fetchone()[0]
        
        if not sessions:
            return {
                'total_questions': total_questions,
                'answered_questions': 0,
                'progress_percent': 0.0,
                'current_question': 1,
                'status': 'not_started'
            }
        
        # Собираем все ответы из всех сессий
        all_answers = {}
        latest_status = sessions[0][2]  # Статус последней сессии
        
        for interview_data, collected_data, status in sessions:
            # Парсим interview_data
            if interview_data:
                try:
                    interview_json = json.loads(interview_data)
                    if isinstance(interview_json, dict):
                        all_answers.update(interview_json)
                except json.JSONDecodeError:
                    pass
            
            # Парсим collected_data
            if collected_data:
                try:
                    collected_json = json.loads(collected_data)
                    if isinstance(collected_json, dict):
                        all_answers.update(collected_json)
                except json.JSONDecodeError:
                    pass
        
        # Подсчитываем прогресс
        answered_questions = len([v for v in all_answers.values() if v and str(v).strip()])
        progress_percent = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        # Определяем текущий вопрос (следующий неотвеченный)
        cursor.execute("""
            SELECT question_number, field_name 
            FROM interview_questions 
            WHERE is_active = 1 
            ORDER BY question_number
        """)
        questions = cursor.fetchall()
        
        current_question = 1
        for question_number, field_name in questions:
            if field_name not in all_answers or not all_answers[field_name]:
                current_question = question_number
                break
        else:
            # Все вопросы отвечены
            current_question = total_questions
        
        # Определяем статус
        if answered_questions == 0:
            status = 'not_started'
        elif answered_questions == total_questions:
            status = 'completed'
        else:
            status = 'in_progress'
        
        return {
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'progress_percent': round(progress_percent, 1),
            'current_question': current_question,
            'status': status,
            'latest_session_status': latest_status
        }

def get_user_answers(telegram_id: int) -> Dict:
    """
    Получить все ответы пользователя на вопросы анкеты
    Возвращает: {field_name: answer, ...}
    """
    db = GrantServiceDatabase(DB_PATH)
    
    with db.connect() as conn:
        cursor = conn.cursor()
        
        # Получаем все сессии пользователя
        cursor.execute("""
            SELECT interview_data, collected_data 
            FROM sessions 
            WHERE telegram_id = ? 
            ORDER BY started_at DESC
        """, (telegram_id,))
        
        sessions = cursor.fetchall()
        
        # Собираем все ответы
        all_answers = {}
        
        for interview_data, collected_data in sessions:
            # Парсим interview_data
            if interview_data:
                try:
                    interview_json = json.loads(interview_data)
                    if isinstance(interview_json, dict):
                        all_answers.update(interview_json)
                except json.JSONDecodeError:
                    pass
            
            # Парсим collected_data
            if collected_data:
                try:
                    collected_json = json.loads(collected_data)
                    if isinstance(collected_json, dict):
                        all_answers.update(collected_json)
                except json.JSONDecodeError:
                    pass
        
        return all_answers

def get_current_question_info(telegram_id: int) -> Dict:
    """
    Получить информацию о текущем вопросе пользователя
    """
    progress = get_user_progress(telegram_id)
    current_question_number = progress['current_question']
    
    db = GrantServiceDatabase(DB_PATH)
    
    with db.connect() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT question_text, field_name, question_type, hint_text
            FROM interview_questions 
            WHERE question_number = ? AND is_active = 1
        """, (current_question_number,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'question_number': current_question_number,
                'question_text': result[0],
                'field_name': result[1],
                'question_type': result[2],
                'hint_text': result[3]
            }
        else:
            return {
                'question_number': current_question_number,
                'question_text': 'Анкета завершена',
                'field_name': None,
                'question_type': None,
                'hint_text': None
            }

def get_all_users_progress() -> List[Dict]:
    """
    Получить прогресс всех пользователей
    """
    db = GrantServiceDatabase(DB_PATH)

    with db.connect() as conn:
        cursor = conn.cursor()

        # Получаем всех пользователей
        cursor.execute("""
            SELECT DISTINCT telegram_id, username, first_name, last_name,
                   registration_date, last_active
            FROM users
            WHERE is_active = 1
            ORDER BY last_active DESC
        """)

        users = cursor.fetchall()

        result = []
        for user in users:
            telegram_id = user[0]
            progress = get_user_progress(telegram_id)
            current_question = get_current_question_info(telegram_id)
            
            # Получаем последнюю активность
            cursor.execute("""
                SELECT MAX(last_activity) 
                FROM sessions 
                WHERE telegram_id = ?
            """, (telegram_id,))
            
            last_activity = cursor.fetchone()[0]
            
            result.append({
                'telegram_id': telegram_id,
                'username': user[1],
                'first_name': user[2],
                'last_name': user[3],
                'registration_date': user[4],
                'last_activity': last_activity or user[5],
                'progress': progress,
                'current_question_info': current_question
            })

        return result

def get_questions_with_answers(telegram_id: int) -> List[Dict]:
    """
    Получить все вопросы с ответами пользователя
    """
    answers = get_user_answers(telegram_id)
    
    db = GrantServiceDatabase(DB_PATH)
    
    with db.connect() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT question_number, question_text, field_name, question_type, hint_text
            FROM interview_questions 
            WHERE is_active = 1
            ORDER BY question_number
        """)
        
        questions = cursor.fetchall()
        
        result = []
        for question in questions:
            question_number, question_text, field_name, question_type, hint_text = question
            # Ищем ответ по field_name
            answer = answers.get(field_name, '')
            
            result.append({
                'question_number': question_number,
                'question_text': question_text,
                'field_name': field_name,
                'question_type': question_type,
                'hint_text': hint_text,
                'answer': answer,
                'answered': bool(answer and str(answer).strip())
            })
        
        return result

def export_user_form(telegram_id: int) -> str:
    """
    Экспорт анкеты пользователя в текстовом формате
    """
    from datetime import datetime
    
    # Получаем информацию о пользователе
    db = GrantServiceDatabase(DB_PATH)
    
    with db.connect() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, first_name, last_name, registration_date
            FROM users 
            WHERE telegram_id = ?
        """, (telegram_id,))
        
        user_info = cursor.fetchone()
    
    # Получаем прогресс
    progress = get_user_progress(telegram_id)
    
    # Получаем все вопросы с ответами
    questions_with_answers = get_questions_with_answers(telegram_id)
    
    # Формируем текст
    export_text = "АНКЕТА ГРАНТОВОГО КОНКУРСА\n"
    export_text += "=" * 50 + "\n\n"
    
    if user_info:
        export_text += f"Пользователь: {user_info[1] or ''} {user_info[2] or ''}".strip() + "\n"
        if user_info[0]:
            export_text += f"Telegram: @{user_info[0]}\n"
        export_text += f"ID: {telegram_id}\n"
        export_text += f"Дата регистрации: {user_info[3]}\n"
    else:
        export_text += f"Telegram ID: {telegram_id}\n"
    
    export_text += f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    export_text += f"Прогресс: {progress['answered_questions']}/{progress['total_questions']} ({progress['progress_percent']}%)\n"
    export_text += f"Статус: {progress['status']}\n\n"
    
    export_text += "ОТВЕТЫ НА ВОПРОСЫ:\n"
    export_text += "-" * 30 + "\n\n"
    
    for qa in questions_with_answers:
        export_text += f"Вопрос {qa['question_number']}: {qa['question_text']}\n"
        
        if qa['answered']:
            export_text += f"Ответ: {qa['answer']}\n"
        else:
            export_text += "Ответ: (не заполнено)\n"
        
        export_text += "\n"
    
    return export_text