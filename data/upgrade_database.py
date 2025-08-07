#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для расширения базы данных GrantService
Добавляет поля для отслеживания прогресса пользователей
"""

import sqlite3
import os
import sys
from datetime import datetime

def upgrade_database():
    """Обновление структуры базы данных"""
    db_path = "/var/GrantService/data/grantservice.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Начинаем обновление базы данных...")
        
        # Проверяем существующие поля в таблице sessions
        cursor.execute("PRAGMA table_info(sessions)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Добавляем новые поля в таблицу sessions
        new_columns = [
            ('progress_percentage', 'INTEGER DEFAULT 0'),
            ('questions_answered', 'INTEGER DEFAULT 0'),
            ('total_questions', 'INTEGER DEFAULT 24'),
            ('last_question_number', 'INTEGER DEFAULT 1'),
            ('answers_data', 'TEXT'),
            ('session_duration_minutes', 'INTEGER DEFAULT 0'),
            ('completion_status', 'VARCHAR(20) DEFAULT "in_progress"')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE sessions ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Добавлено поле: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ Поле {column_name} уже существует: {e}")
        
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
        print("✅ Таблица user_answers создана/проверена")
        
        # Создаем индексы для быстрой работы
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_answers_session ON user_answers(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_answers_question ON user_answers(question_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_progress ON sessions(progress_percentage)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(completion_status)")
        print("✅ Индексы созданы")
        
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
        """)
        
        cursor.execute("""
            UPDATE sessions 
            SET progress_percentage = CASE 
                WHEN total_questions > 0 THEN (questions_answered * 100) / total_questions
                ELSE 0
            END
        """)
        
        print("✅ Существующие данные обновлены")
        
        conn.commit()
        conn.close()
        
        print("🎉 Обновление базы данных завершено успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления базы данных: {e}")
        return False

def show_database_info():
    """Показать информацию о структуре базы данных"""
    db_path = "/var/GrantService/data/grantservice.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ:")
        print("=" * 50)
        
        # Информация о таблице sessions
        cursor.execute("PRAGMA table_info(sessions)")
        columns = cursor.fetchall()
        print(f"\n📋 Таблица 'sessions' ({len(columns)} полей):")
        for column in columns:
            print(f"  • {column[1]} ({column[2]}) - {column[3]}")
        
        # Информация о таблице user_answers
        cursor.execute("PRAGMA table_info(user_answers)")
        columns = cursor.fetchall()
        print(f"\n📝 Таблица 'user_answers' ({len(columns)} полей):")
        for column in columns:
            print(f"  • {column[1]} ({column[2]}) - {column[3]}")
        
        # Статистика
        cursor.execute("SELECT COUNT(*) FROM sessions")
        sessions_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_answers")
        answers_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        
        print(f"\n📈 СТАТИСТИКА:")
        print(f"  • Пользователей: {users_count}")
        print(f"  • Сессий: {sessions_count}")
        print(f"  • Ответов: {answers_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка получения информации: {e}")

if __name__ == "__main__":
    print("🚀 Обновление базы данных GrantService")
    print("=" * 50)
    
    if upgrade_database():
        show_database_info()
    else:
        print("❌ Обновление не выполнено") 