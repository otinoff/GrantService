#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
База данных GrantService
Управление вопросами интервью и пользовательскими данными
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class GrantServiceDatabase:
    def __init__(self, db_path: str = "/var/GrantService/data/grantservice.db"):
        self.db_path = db_path
        self.init_database()
    
    def connect(self):
        """Создание соединения с БД"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица вопросов интервью
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interview_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_number INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    field_name VARCHAR(100) NOT NULL,
                    question_type VARCHAR(50) DEFAULT 'text',
                    options TEXT, -- JSON строка для вариантов ответов
                    hint_text TEXT,
                    is_required BOOLEAN DEFAULT 1,
                    follow_up_question TEXT,
                    validation_rules TEXT, -- JSON строка для правил валидации
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(100),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_sessions INTEGER DEFAULT 0,
                    completed_applications INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Таблица сессий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id BIGINT NOT NULL,
                    current_step VARCHAR(50),
                    status VARCHAR(30) DEFAULT 'active',
                    conversation_history TEXT, -- JSON строка
                    collected_data TEXT, -- JSON строка
                    interview_data TEXT, -- JSON строка
                    audit_result TEXT, -- JSON строка
                    plan_structure TEXT, -- JSON строка
                    final_document TEXT,
                    project_name VARCHAR(300),
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER DEFAULT 0,
                    ai_requests_count INTEGER DEFAULT 0,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
                )
            """)
            
            # Индексы для быстрого поиска
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_number ON interview_questions(question_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_active ON interview_questions(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_telegram_id ON sessions(telegram_id)")
            
            conn.commit()
    
    def insert_default_questions(self):
        """Вставка вопросов по умолчанию из qwestions.md"""
        default_questions = [
            {
                'question_number': 1,
                'question_text': 'Как называется ваш проект в 3-7 словах?',
                'field_name': 'project_name',
                'question_type': 'text',
                'hint_text': 'Пример: Мобильная библиотека для людей с ОВЗ',
                'is_required': True,
                'validation_rules': json.dumps({'min_length': 3, 'max_length': 50})
            },
            {
                'question_number': 2,
                'question_text': 'Кратко опишите суть проекта (что хотите сделать)',
                'field_name': 'project_description',
                'question_type': 'textarea',
                'hint_text': 'Пример: создадим выездную библиотеку и аудиокниги, чтобы жители сел Новокузнецкого района с ограничениями в здоровье могли бесплатно получить литературу на дом, образовываться и устраиваться на работу',
                'is_required': True,
                'validation_rules': json.dumps({'min_length': 20, 'max_length': 500})
            },
            {
                'question_number': 3,
                'question_text': 'В каком городе, регионе вы хотите реализовать проект?',
                'field_name': 'region',
                'question_type': 'text',
                'hint_text': 'Пример: Кемеровская область, новокузнецкий район, пгт…',
                'is_required': True,
                'validation_rules': json.dumps({'min_length': 5})
            },
            {
                'question_number': 4,
                'question_text': 'Опишите, какую проблему решает ваш проект и почему он важен?',
                'field_name': 'problem_description',
                'question_type': 'textarea',
                'hint_text': 'Пример: Сельские жители с ОВЗ Новокузнецкого района не имеют доступа к библиотекам, из-за этого страдает культура и развитие, что приводит к пьянству и невозможности устроиться на работу (по отчету минкультуры 2024)',
                'is_required': True,
                'validation_rules': json.dumps({'min_length': 30})
            },
            {
                'question_number': 5,
                'question_text': 'Кто будет основной целевой группой вашего проекта? (участники вашего проекта)',
                'field_name': 'target_audience',
                'question_type': 'textarea',
                'hint_text': 'Пример: Охватим 300 взрослых людей с ОВЗ, проживающих по 3 поселкам Новокузнецкого района',
                'is_required': True,
                'validation_rules': json.dumps({'min_length': 20})
            },
            {
                'question_number': 6,
                'question_text': 'Какова главная цель проекта?',
                'field_name': 'main_goal',
                'question_type': 'text',
                'hint_text': 'Пример: Повысить доступность чтения для людей с ОВЗ в сельской местности',
                'is_required': True,
                'validation_rules': json.dumps({'min_length': 10})
            },
            {
                'question_number': 7,
                'question_text': 'Перечислите конкретные задачи, которые нужно будет решить, чтобы запустить проект?',
                'field_name': 'project_tasks',
                'question_type': 'textarea',
                'hint_text': 'Пример: 1. Оснастить автобус книжным фондом на 1000 экземпляров 2. Провести информационную компанию, чтобы оповестить людей 3.Провести 20 выездных библиотечных сессий с целевой аудиторией',
                'is_required': True,
                'validation_rules': json.dumps({'min_length': 30})
            }
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже вопросы
            cursor.execute("SELECT COUNT(*) FROM interview_questions")
            count = cursor.fetchone()[0]
            
            if count == 0:
                for question in default_questions:
                    cursor.execute("""
                        INSERT INTO interview_questions 
                        (question_number, question_text, field_name, question_type, hint_text, is_required, validation_rules)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        question['question_number'],
                        question['question_text'],
                        question['field_name'],
                        question['question_type'],
                        question['hint_text'],
                        question['is_required'],
                        question['validation_rules']
                    ))
                
                conn.commit()
                print(f"✅ Добавлено {len(default_questions)} вопросов по умолчанию")
            else:
                print(f"ℹ️ В базе уже есть {count} вопросов")
    
    def get_active_questions(self) -> List[Dict[str, Any]]:
        """Получить все активные вопросы, отсортированные по номеру"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM interview_questions 
                WHERE is_active = 1 
                ORDER BY question_number
            """)
            
            questions = []
            for row in cursor.fetchall():
                question = dict(row)
                # Парсим JSON поля
                if question['options']:
                    question['options'] = json.loads(question['options'])
                if question['validation_rules']:
                    question['validation_rules'] = json.loads(question['validation_rules'])
                
                questions.append(question)
            
            return questions
    
    def get_question_by_number(self, question_number: int) -> Optional[Dict[str, Any]]:
        """Получить вопрос по номеру"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM interview_questions 
                WHERE question_number = ? AND is_active = 1
            """, (question_number,))
            
            row = cursor.fetchone()
            if row:
                question = dict(row)
                if question['options']:
                    question['options'] = json.loads(question['options'])
                if question['validation_rules']:
                    question['validation_rules'] = json.loads(question['validation_rules'])
                return question
            
            return None
    
    def validate_answer(self, question_id: int, answer: str) -> Dict[str, Any]:
        """Валидация ответа по правилам из БД"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM interview_questions WHERE id = ?
            """, (question_id,))
            
            row = cursor.fetchone()
            if not row:
                return {"is_valid": False, "message": "Вопрос не найден"}
            
            question = {
                'id': row[0],
                'question_number': row[1],
                'question_text': row[2],
                'field_name': row[3],
                'question_type': row[4],
                'options': json.loads(row[5]) if row[5] else None,
                'hint_text': row[6],
                'is_required': bool(row[7]),
                'follow_up_question': row[8],
                'validation_rules': json.loads(row[9]) if row[9] else {},
                'is_active': bool(row[10])
            }
            
            # Проверка обязательности
            if question['is_required'] and not answer.strip():
                return {"is_valid": False, "message": "Это обязательный вопрос"}
            
            # Проверка длины
            validation_rules = question['validation_rules']
            if 'min_length' in validation_rules and len(answer) < validation_rules['min_length']:
                return {"is_valid": False, "message": f"Минимальная длина: {validation_rules['min_length']} символов"}
            
            if 'max_length' in validation_rules and len(answer) > validation_rules['max_length']:
                return {"is_valid": False, "message": f"Максимальная длина: {validation_rules['max_length']} символов"}
            
            # Проверка вариантов
            if question['question_type'] == 'select' and question['options']:
                if answer not in question['options']:
                    return {"is_valid": False, "message": "Выберите один из предложенных вариантов"}
            
            # Проверка числовых значений
            if question['question_type'] == 'number':
                try:
                    value = float(answer.strip())
                    if 'min_value' in validation_rules and value < validation_rules['min_value']:
                        return {
                            "is_valid": False,
                            "message": f"Значение должно быть не менее {validation_rules['min_value']}"
                        }
                    if 'max_value' in validation_rules and value > validation_rules['max_value']:
                        return {
                            "is_valid": False,
                            "message": f"Значение должно быть не более {validation_rules['max_value']}"
                        }
                except ValueError:
                    return {
                        "is_valid": False,
                        "message": "Введите числовое значение"
                    }
            
            return {"is_valid": True, "message": "Ответ корректен"}
    
    def update_question(self, question_id: int, data: Dict[str, Any]) -> bool:
        """Обновить вопрос"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Подготавливаем данные
                update_data = {
                    'question_number': data.get('question_number'),
                    'question_text': data.get('question_text'),
                    'field_name': data.get('field_name'),
                    'question_type': data.get('question_type'),
                    'options': json.dumps(data.get('options')) if data.get('options') else None,
                    'hint_text': data.get('hint_text'),
                    'is_required': data.get('is_required', True),
                    'follow_up_question': data.get('follow_up_question'),
                    'validation_rules': json.dumps(data.get('validation_rules', {})),
                    'is_active': data.get('is_active', True),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Строим SQL запрос
                set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
                sql = f"UPDATE interview_questions SET {set_clause} WHERE id = ?"
                
                cursor.execute(sql, list(update_data.values()) + [question_id])
                conn.commit()
                
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка обновления вопроса: {e}")
            return False
    
    def create_question(self, data: Dict[str, Any]) -> int:
        """Создать новый вопрос"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO interview_questions 
                    (question_number, question_text, field_name, question_type, options, hint_text, 
                     is_required, follow_up_question, validation_rules, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('question_number'),
                    data.get('question_text'),
                    data.get('field_name'),
                    data.get('question_type', 'text'),
                    json.dumps(data.get('options')) if data.get('options') else None,
                    data.get('hint_text'),
                    data.get('is_required', True),
                    data.get('follow_up_question'),
                    json.dumps(data.get('validation_rules', {})),
                    data.get('is_active', True)
                ))
                
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"❌ Ошибка создания вопроса: {e}")
            return 0
    
    def delete_question(self, question_id: int) -> bool:
        """Удалить вопрос (мягкое удаление)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE interview_questions 
                    SET is_active = 0, updated_at = ? 
                    WHERE id = ?
                """, (datetime.now().isoformat(), question_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка удаления вопроса: {e}")
            return False

# Глобальный экземпляр БД
db = GrantServiceDatabase() 