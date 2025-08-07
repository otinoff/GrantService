#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модели базы данных GrantService
"""

import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

def get_kuzbass_time():
    """Получить текущее время в часовом поясе Кемерово (GMT+7)"""
    try:
        import pytz
        kuzbass_tz = pytz.timezone('Asia/Novosibirsk')
        return datetime.now(kuzbass_tz).isoformat()
    except ImportError:
        # Fallback без pytz - добавляем 7 часов к UTC
        utc_time = datetime.now(timezone.utc)
        kuzbass_time = utc_time + timedelta(hours=7)
        return kuzbass_time.isoformat()

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
            
            # Таблица логов исследователя
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS researcher_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_id INTEGER,
                    query_text TEXT NOT NULL,
                    perplexity_response TEXT,
                    sources TEXT, -- JSON строка
                    usage_stats TEXT, -- JSON строка
                    cost REAL DEFAULT 0.0,
                    status VARCHAR(20) DEFAULT 'success',
                    error_message TEXT,
                    credit_balance REAL DEFAULT 0.0, -- Новое поле для баланса
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Проверяем, есть ли поле credit_balance в таблице researcher_logs
            cursor.execute("PRAGMA table_info(researcher_logs)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Добавляем поле credit_balance если его нет
            if 'credit_balance' not in columns:
                cursor.execute("ALTER TABLE researcher_logs ADD COLUMN credit_balance REAL DEFAULT 0.0")
                print("✅ Добавлено поле credit_balance в таблицу researcher_logs")
            
            # Таблица промптов агентов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_type VARCHAR(50) NOT NULL,
                    prompt_name VARCHAR(100) NOT NULL,
                    prompt_content TEXT NOT NULL,
                    prompt_type VARCHAR(20) DEFAULT 'system',
                    order_num INTEGER DEFAULT 1,
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER DEFAULT 2000,
                    model_name VARCHAR(50) DEFAULT 'GigaChat-Pro',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("✅ База данных инициализирована")
    
    def get_agent_prompts(self, agent_type: str = None) -> List[Dict[str, Any]]:
        """Получить промпты агентов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if agent_type:
                    cursor.execute("""
                        SELECT * FROM agent_prompts 
                        WHERE agent_type = ? AND is_active = 1
                        ORDER BY order_num, id
                    """, (agent_type,))
                else:
                    cursor.execute("""
                        SELECT * FROM agent_prompts 
                        WHERE is_active = 1
                        ORDER BY agent_type, order_num, id
                    """)
                
                columns = [description[0] for description in cursor.description]
                prompts = []
                for row in cursor.fetchall():
                    prompt = dict(zip(columns, row))
                    prompts.append(prompt)
                
                return prompts
        except Exception as e:
            print(f"❌ Ошибка получения промптов агента {agent_type}: {e}")
            return []

def get_connection():
    """Получить соединение с БД (для внутреннего использования)"""
    from . import db
    return sqlite3.connect(db.db_path) 