#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для расширения базы данных GrantService (Windows версия)
Добавляет поля для отслеживания прогресса пользователей
"""

import sqlite3
import os
import sys
from datetime import datetime

def upgrade_database():
    """Обновление структуры базы данных"""
    # Windows путь - используем правильное имя файла
    db_path = "C:\\SnowWhiteAI\\GrantService\\data\\grantservice.db"
    
    if not os.path.exists(db_path):
        print(f"[ERROR] База данных не найдена: {db_path}")
        print("[INFO] Создаем новую базу данных...")
        # Создадим директорию если не существует
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("[INFO] Начинаем обновление базы данных...")
        
        # Создаем таблицу sessions если её нет
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                current_step VARCHAR(50),
                status VARCHAR(20) DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                interview_data TEXT,
                current_question INTEGER DEFAULT 1,
                anketa_id VARCHAR(100),
                total_questions INTEGER DEFAULT 14,
                progress_percentage INTEGER DEFAULT 0,
                questions_answered INTEGER DEFAULT 0,
                last_question_number INTEGER DEFAULT 1,
                answers_data TEXT,
                session_duration_minutes INTEGER DEFAULT 0,
                completion_status VARCHAR(20) DEFAULT 'in_progress'
            )
        """)
        print("[OK] Таблица sessions создана/проверена")
        
        # Проверяем существующие поля в таблице sessions
        cursor.execute("PRAGMA table_info(sessions)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Добавляем новые поля в таблицу sessions если их нет
        new_columns = [
            ('progress_percentage', 'INTEGER DEFAULT 0'),
            ('questions_answered', 'INTEGER DEFAULT 0'),
            ('total_questions', 'INTEGER DEFAULT 14'),
            ('last_question_number', 'INTEGER DEFAULT 1'),
            ('answers_data', 'TEXT'),
            ('session_duration_minutes', 'INTEGER DEFAULT 0'),
            ('completion_status', 'VARCHAR(20) DEFAULT "in_progress"'),
            ('anketa_id', 'VARCHAR(100)')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE sessions ADD COLUMN {column_name} {column_type}")
                    print(f"[OK] Добавлено поле: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"[WARNING] Поле {column_name} уже существует или ошибка: {e}")
        
        # Создаем таблицу user_answers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                answer_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validation_status VARCHAR(20) DEFAULT 'valid',
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (question_id) REFERENCES interview_questions(id)
            )
        """)
        print("[OK] Таблица user_answers создана/проверена")
        
        # Создаем таблицу users если её нет
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username VARCHAR(100),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                phone VARCHAR(20),
                email VARCHAR(100),
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Таблица users создана/проверена")
        
        # Создаем таблицу interview_questions если её нет
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interview_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_number INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                field_name VARCHAR(50),
                answer_type VARCHAR(20),
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Таблица interview_questions создана/проверена")
        
        # Создаем индексы для быстрой работы
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_answers_session ON user_answers(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_answers_question ON user_answers(question_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_progress ON sessions(progress_percentage)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(completion_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_telegram ON sessions(telegram_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_anketa ON sessions(anketa_id)")
        print("[OK] Индексы созданы")
        
        # Обновляем существующие сессии
        cursor.execute("""
            UPDATE sessions 
            SET completion_status = CASE 
                WHEN status = 'completed' THEN 'completed'
                ELSE 'in_progress'
            END
            WHERE completion_status IS NULL
        """)
        
        # Подсчитываем прогресс для существующих сессий
        cursor.execute("""
            UPDATE sessions 
            SET questions_answered = (
                SELECT COUNT(*) 
                FROM user_answers ua 
                WHERE ua.session_id = sessions.id
            )
            WHERE EXISTS (
                SELECT 1 FROM user_answers WHERE session_id = sessions.id
            )
        """)
        
        cursor.execute("""
            UPDATE sessions 
            SET progress_percentage = CASE 
                WHEN total_questions > 0 THEN (questions_answered * 100) / total_questions
                ELSE 0
            END
        """)
        
        print("[OK] Существующие данные обновлены")
        
        conn.commit()
        conn.close()
        
        print("[SUCCESS] Обновление базы данных завершено успешно!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка обновления базы данных: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_database_info():
    """Показать информацию о структуре базы данных"""
    # Windows путь - используем правильное имя файла
    db_path = "C:\\SnowWhiteAI\\GrantService\\data\\grantservice.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n[DATABASE INFO]")
        print("=" * 50)
        
        # Информация о таблице sessions
        cursor.execute("PRAGMA table_info(sessions)")
        columns = cursor.fetchall()
        print(f"\nТаблица 'sessions' ({len(columns)} полей):")
        for column in columns:
            print(f"  - {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else 'NULL'}")
        
        # Информация о таблице user_answers
        cursor.execute("PRAGMA table_info(user_answers)")
        columns = cursor.fetchall()
        print(f"\nТаблица 'user_answers' ({len(columns)} полей):")
        for column in columns:
            print(f"  - {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else 'NULL'}")
        
        # Статистика
        cursor.execute("SELECT COUNT(*) FROM sessions")
        sessions_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_answers")
        answers_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM interview_questions")
        questions_count = cursor.fetchone()[0]
        
        print(f"\n[STATISTICS]:")
        print(f"  - Пользователей: {users_count}")
        print(f"  - Сессий: {sessions_count}")
        print(f"  - Ответов: {answers_count}")
        print(f"  - Вопросов: {questions_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Ошибка получения информации: {e}")

if __name__ == "__main__":
    print("[START] Обновление базы данных GrantService")
    print("=" * 50)
    
    if upgrade_database():
        show_database_info()
    else:
        print("[ERROR] Обновление не выполнено")