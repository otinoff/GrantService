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
                    is_active BOOLEAN DEFAULT 1,
                    login_token VARCHAR(255)  -- Токен для авторизации в админке
                )
            """)
            
            # Таблица сессий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id BIGINT NOT NULL,
                    anketa_id VARCHAR(20) UNIQUE, -- ID анкеты в формате #AN-YYYYMMDD-username-001
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
                print("Добавлено поле credit_balance в таблицу researcher_logs")
            
            # Проверяем, есть ли поле anketa_id в таблице sessions
            cursor.execute("PRAGMA table_info(sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Добавляем поле anketa_id если его нет
            if 'anketa_id' not in columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN anketa_id VARCHAR(20)")
                print("Добавлено поле anketa_id в таблицу sessions")
            
            # Проверяем, есть ли поле login_token в таблице users
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Добавляем поле login_token если его нет
            if 'login_token' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN login_token VARCHAR(255)")
                print("Добавлено поле login_token в таблицу users")
            
            # Таблица исследований Researcher Agent
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS researcher_research (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    research_id VARCHAR(50) UNIQUE NOT NULL, -- ID исследования в формате #RS-YYYYMMDD-username-001-AN-anketa_id
                    anketa_id VARCHAR(20) NOT NULL, -- ID анкеты в формате #AN-YYYYMMDD-username-001
                    user_id BIGINT NOT NULL, -- Telegram ID пользователя
                    username VARCHAR(100), -- Username пользователя
                    first_name VARCHAR(100), -- Имя пользователя
                    last_name VARCHAR(100), -- Фамилия пользователя
                    session_id INTEGER, -- ID сессии из таблицы sessions
                    research_type VARCHAR(50) DEFAULT 'comprehensive', -- Тип исследования
                    llm_provider VARCHAR(50) NOT NULL, -- Использованный LLM провайдер
                    model VARCHAR(50), -- Использованная модель
                    status VARCHAR(30) DEFAULT 'pending', -- Статус: pending, processing, completed, error
                    research_results TEXT, -- JSON с результатами исследования
                    metadata TEXT, -- JSON с метаданными (токены, время, стоимость)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # Таблица готовых грантов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grant_id VARCHAR(50) UNIQUE NOT NULL, -- ID гранта в формате #GR-YYYYMMDD-username-001-AN-anketa_id
                    anketa_id VARCHAR(20) NOT NULL, -- ID анкеты в формате #AN-YYYYMMDD-username-001
                    research_id VARCHAR(50) NOT NULL, -- ID исследования в формате #RS-YYYYMMDD-username-001-AN-anketa_id
                    user_id BIGINT NOT NULL, -- Telegram ID пользователя
                    username VARCHAR(100), -- Username пользователя
                    first_name VARCHAR(100), -- Имя пользователя
                    last_name VARCHAR(100), -- Фамилия пользователя
                    grant_title VARCHAR(200), -- Название гранта
                    grant_content TEXT, -- Полное содержание гранта
                    grant_sections TEXT, -- JSON с разделами гранта
                    metadata TEXT, -- JSON с метаданными (токены, время, стоимость)
                    llm_provider VARCHAR(50) NOT NULL, -- Использованный LLM провайдер
                    model VARCHAR(50), -- Использованная модель
                    status VARCHAR(30) DEFAULT 'draft', -- Статус: draft, completed, submitted, approved, rejected
                    quality_score INTEGER DEFAULT 0, -- Оценка качества (0-10)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    submitted_at TIMESTAMP, -- Дата отправки
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                    FOREIGN KEY (anketa_id) REFERENCES sessions(anketa_id),
                    FOREIGN KEY (research_id) REFERENCES researcher_research(research_id)
                )
            """)
            
            # Таблица грантовых заявок
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grant_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_number VARCHAR(50) UNIQUE NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    content_json TEXT NOT NULL, -- JSON строка с полным содержанием заявки
                    summary TEXT, -- Краткое описание заявки
                    status VARCHAR(30) DEFAULT 'draft', -- draft, submitted, approved, rejected
                    user_id INTEGER, -- Связь с пользователем (если из Telegram)
                    session_id INTEGER, -- Связь с сессией (если из Telegram)
                    admin_user VARCHAR(100), -- Имя администратора (если из веб-админки)
                    quality_score REAL DEFAULT 0.0, -- Оценка качества заявки
                    llm_provider VARCHAR(50), -- Какой LLM использовался
                    model_used VARCHAR(100), -- Какая модель использовалась
                    processing_time REAL DEFAULT 0.0, -- Время создания в секундах
                    tokens_used INTEGER DEFAULT 0, -- Количество использованных токенов
                    grant_fund VARCHAR(200), -- Грантодатель
                    requested_amount DECIMAL(15,2), -- Запрашиваемая сумма
                    project_duration INTEGER, -- Длительность проекта в месяцах
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # Таблица промптов агентов (удалена - теперь используется prompts.py)
            # cursor.execute("""
            #     CREATE TABLE IF NOT EXISTS agent_prompts (
            #         id INTEGER PRIMARY KEY AUTOINCREMENT,
            #         agent_type VARCHAR(50) NOT NULL,
            #         prompt_name VARCHAR(100) NOT NULL,
            #         prompt_content TEXT NOT NULL,
            #         prompt_type VARCHAR(20) DEFAULT 'system',
            #         order_num INTEGER DEFAULT 1,
            #         temperature REAL DEFAULT 0.7,
            #         max_tokens INTEGER DEFAULT 2000,
            #         model_name VARCHAR(50) DEFAULT 'GigaChat-Pro',
            #         is_active BOOLEAN DEFAULT 1,
            #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            #     )
            # """)
            
            # Создаем индексы для быстрого поиска
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_anketa_id ON sessions(anketa_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_telegram_id ON sessions(telegram_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_research_id ON researcher_research(research_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_anketa_id ON researcher_research(anketa_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_user_id ON researcher_research(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_date ON researcher_research(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_status ON researcher_research(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_provider ON researcher_research(llm_provider)")
            
            # Индексы для таблицы grants
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_grants_grant_id ON grants(grant_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_grants_anketa_id ON grants(anketa_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_grants_research_id ON grants(research_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_grants_user_id ON grants(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_grants_date ON grants(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_grants_status ON grants(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_grants_provider ON grants(llm_provider)")
            
            conn.commit()
            print("База данных инициализирована")
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С ТОКЕНАМИ АВТОРИЗАЦИИ =====
    
    def generate_login_token(self) -> str:
        """Генерирует новый токен для входа в панель"""
        import secrets
        import time
        
        # Формат: tokenTIMESTAMPRANDOM_HEX (без подчеркиваний, 47 символов)
        # token(5) + timestamp(10) + random_hex(32) = 47 символов
        timestamp = int(time.time())
        random_hex = secrets.token_hex(16)  # 32 символа hex
        return f"token{timestamp}{random_hex}"
    
    def get_or_create_login_token(self, telegram_id: int) -> Optional[str]:
        """Получает существующий токен пользователя или создает новый (по telegram_id)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем, есть ли уже токен у пользователя (по telegram_id)
                cursor.execute("""
                    SELECT login_token FROM users WHERE telegram_id = ?
                """, (telegram_id,))
                
                result = cursor.fetchone()
                print(f"Проверка токена для пользователя с telegram_id {telegram_id}: {result}")
                
                if result and result[0]:
                    token = result[0]
                    print(f"Найден токен: {token[:20]}...")
                    # Проверяем срок действия токена (24 часа)
                    try:
                        import time
                        token_timestamp = None
                        
                        # Проверяем формат с подчеркиваниями
                        if '_' in token:
                            parts = token.split('_')
                            if len(parts) >= 3:
                                token_timestamp = int(parts[1])
                        # Проверяем формат без подчеркиваний
                        elif token.startswith('token') and len(token) == 47:
                            try:
                                timestamp_str = token[5:15]  # позиции 5-14 (10 цифр)
                                if timestamp_str.isdigit():
                                    token_timestamp = int(timestamp_str)
                            except (ValueError, IndexError):
                                pass
                        
                        if token_timestamp:
                            current_time = int(time.time())
                            # Токен действителен 24 часа (86400 секунд)
                            if current_time - token_timestamp < 86400:
                                print(f"Токен действителен для пользователя с telegram_id {telegram_id}")
                                return token
                            else:
                                print(f"Токен истек для пользователя с telegram_id {telegram_id}")
                    except (ValueError, IndexError) as e:
                        print(f"Невалидный формат токена для пользователя с telegram_id {telegram_id}: {e}")
                        pass  # Невалидный формат токена
                
                # Генерируем новый токен
                new_token = self.generate_login_token()
                print(f"Генерируем новый токен для пользователя с telegram_id {telegram_id}: {new_token[:20]}...")
                
                # Обновляем токен в БД (по telegram_id)
                cursor.execute("""
                    UPDATE users SET login_token = ? WHERE telegram_id = ?
                """, (new_token, telegram_id))
                
                conn.commit()
                print(f"Токен обновлен для пользователя с telegram_id {telegram_id}")
                return new_token
                
        except Exception as e:
            print(f"Ошибка получения/создания токена для пользователя {telegram_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def validate_login_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверяет токен и возвращает данные пользователя если токен валиден"""
        import time
        
        try:
            print("="*60)
            print("ДЕТАЛЬНАЯ ПРОВЕРКА ТОКЕНА")
            print("-"*60)
            
            if not token:
                print("❌ ОШИБКА: Пустой токен")
                print("="*60)
                return None
            
            # Выводим полную информацию о токене
            print(f"📍 Полный токен (длина {len(token)}): {token}")
            
            # Проверяем два возможных формата токена
            token_timestamp = None
            token_hash = None
            
            # Формат 1: token_timestamp_hash (с подчеркиваниями)
            if '_' in token:
                parts = token.split('_')
                print(f"📍 Обнаружен формат с подчеркиваниями, частей: {len(parts)}")
                if len(parts) >= 3:
                    print(f"✅ Формат токена с подчеркиваниями (token_timestamp_hash)")
                    try:
                        token_timestamp = int(parts[1])
                        token_hash = parts[2]
                    except (ValueError, IndexError):
                        pass
            
            # Формат 2: tokenTIMESTAMPHASH (без подчеркиваний, фиксированные позиции)
            if not token_timestamp and token.startswith('token') and len(token) == 47:
                print(f"📍 Обнаружен формат без подчеркиваний (длина 47)")
                try:
                    # Позиции: token(5) + timestamp(10) + hash(32) = 47
                    timestamp_str = token[5:15]  # позиции 5-14 (10 цифр)
                    token_hash = token[15:47]    # позиции 15-46 (32 символа)
                    
                    # Проверяем, что timestamp состоит из цифр
                    if timestamp_str.isdigit():
                        token_timestamp = int(timestamp_str)
                        print(f"✅ Успешно извлечен timestamp: {token_timestamp}")
                        print(f"✅ Успешно извлечен hash: {token_hash[:16]}...")
                except (ValueError, IndexError) as e:
                    print(f"❌ Ошибка парсинга формата без подчеркиваний: {e}")
            
            # Проверяем, удалось ли извлечь timestamp
            if not token_timestamp:
                print(f"❌ ОШИБКА: Не удалось извлечь timestamp из токена!")
                print(f"   Токен не соответствует ни одному из форматов:")
                print(f"   1. token_timestamp_hash (с подчеркиваниями)")
                print(f"   2. tokenTIMESTAMPHASH (без подчеркиваний, 47 символов)")
                print("="*60)
                return None
            
            # Проверяем срок действия токена
            current_time = int(time.time())
            time_diff = current_time - token_timestamp
            print(f"📍 Timestamp токена: {token_timestamp}")
            print(f"📍 Текущее время: {current_time}")
            print(f"📍 Разница: {time_diff} секунд ({time_diff//3600} часов)")
            
            # Токен действителен 24 часа (86400 секунд)
            if time_diff >= 86400:
                print(f"❌ Токен истек! Прошло {time_diff//3600} часов (лимит 24 часа)")
                print("="*60)
                return None
            
            print("✅ Токен не истек (действителен 24 часа)")
            
            # Ищем пользователя с таким токеном
            print("🔍 Поиск пользователя в базе данных...")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Сначала проверим, есть ли вообще пользователи с токенами
                cursor.execute("SELECT COUNT(*) FROM users WHERE login_token IS NOT NULL")
                total_with_tokens = cursor.fetchone()[0]
                print(f"📍 Всего пользователей с токенами: {total_with_tokens}")
                
                # Теперь ищем конкретный токен
                cursor.execute("""
                    SELECT id, telegram_id, username, first_name, last_name, is_active
                    FROM users WHERE login_token = ?
                """, (token,))
                
                result = cursor.fetchone()
                
                if result:
                    columns = [description[0] for description in cursor.description]
                    user_data = dict(zip(columns, result))
                    # ВАЖНО: Добавляем telegram_id как user_id для совместимости с auth.py
                    user_data['user_id'] = user_data['telegram_id']
                    print(f"✅ УСПЕХ! Найден пользователь:")
                    print(f"   ID: {user_data['id']}")
                    print(f"   Telegram ID: {user_data['telegram_id']}")
                    print(f"   Username: {user_data['username']}")
                    print(f"   Имя: {user_data['first_name']} {user_data['last_name']}")
                    print(f"   Активен: {user_data['is_active']}")
                    print("="*60)
                    return user_data
                else:
                    print("❌ Пользователь с таким токеном НЕ найден в БД")
                    
                    # Для отладки покажем первые несколько токенов из БД
                    cursor.execute("SELECT id, SUBSTR(login_token, 1, 40) FROM users WHERE login_token IS NOT NULL LIMIT 3")
                    existing = cursor.fetchall()
                    if existing:
                        print("📍 Примеры токенов в БД (первые 40 символов):")
                        for uid, token_part in existing:
                            print(f"   User {uid}: {token_part}...")
                    print("="*60)
                    return None
                    
        except Exception as e:
            print(f"❌ Ошибка проверки токена: {e}")
            import traceback
            traceback.print_exc()
            print("="*60)
            return None
    
    def refresh_login_token(self, telegram_id: int) -> Optional[str]:
        """Принудительно обновляет токен пользователя (по telegram_id)"""
        try:
            new_token = self.generate_login_token()
            print(f"Обновление токена для пользователя с telegram_id {telegram_id}: {new_token[:20]}...")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET login_token = ? WHERE telegram_id = ?
                """, (new_token, telegram_id))
                
                conn.commit()
                print(f"Токен обновлен для пользователя с telegram_id {telegram_id}")
                return new_token
                
        except Exception as e:
            print(f"Ошибка обновления токена для пользователя {telegram_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # Метод get_agent_prompts удален - теперь используется prompts.py
    # def get_agent_prompts(self, agent_type: str = None) -> List[Dict[str, Any]]:
    #     """Получить промпты агентов"""
    #     try:
    #         with sqlite3.connect(self.db_path) as conn:
    #             cursor = conn.cursor()
    #             
    #             if agent_type:
    #                 cursor.execute("""
    #                     SELECT * FROM agent_prompts 
    #                     WHERE agent_type = ? AND is_active = 1
    #                     ORDER BY order_num, id
    #                 """, (agent_type,))
    #                 else:
    #                     cursor.execute("""
    #                         SELECT * FROM agent_prompts 
    #                         WHERE is_active = 1
    #                         ORDER BY agent_type, order_num, id
    #                     """)
    #                 
    #                 columns = [description[0] for description in cursor.description]
    #                 prompts = []
    #                 for row in cursor.fetchall():
    #                     prompt = dict(zip(columns, row))
    #                     prompts.append(prompt)
    #                 
    #                 return prompts
    #         except Exception as e:
    #             print(f"❌ Ошибка получения промптов агента {agent_type}: {e}")
    #             return []

    def save_grant_application(self, application_data: Dict[str, Any]) -> str:
        """Сохранить грантовую заявку в базу данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Используем переданный номер заявки или генерируем новый
                if 'application_number' in application_data and application_data['application_number']:
                    application_number = application_data['application_number']
                else:
                    import uuid
                    application_number = f"GA-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
                
                # Извлекаем данные из application_data
                title = application_data.get('title', 'Без названия')
                
                # Попробуем разные варианты содержимого заявки
                if 'content_json' in application_data:
                    content_json = application_data['content_json']
                elif 'application' in application_data:
                    content_json = json.dumps(application_data.get('application', {}), ensure_ascii=False, indent=2)
                else:
                    # Если ни того, ни другого нет, сохраняем все данные как есть
                    content_json = json.dumps(application_data, ensure_ascii=False, indent=2)
                
                summary = application_data.get('summary', '')[:500]  # Ограничиваем длину
                admin_user = application_data.get('admin_user', 'system')
                quality_score = application_data.get('quality_score', 0.0)
                llm_provider = application_data.get('provider_used', application_data.get('provider', 'unknown'))
                model_used = application_data.get('model_used', 'unknown')
                processing_time = application_data.get('processing_time', 0.0)
                tokens_used = application_data.get('tokens_used', 0)
                
                # Извлекаем дополнительную информацию из содержания заявки
                application_content = application_data.get('application', {})
                grant_fund = application_data.get('grant_fund', '')
                requested_amount = application_data.get('requested_amount', 0.0)
                project_duration = application_data.get('project_duration', 12)
                
                # Добавляем session_id и user_id из application_data
                session_id = application_data.get('session_id')
                user_id = application_data.get('user_id')
                
                cursor.execute("""
                    INSERT INTO grant_applications (
                        application_number, title, content_json, summary,
                        admin_user, quality_score, llm_provider, model_used,
                        processing_time, tokens_used, grant_fund, requested_amount,
                        project_duration, user_id, session_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    application_number, title, content_json, summary,
                    admin_user, quality_score, llm_provider, model_used,
                    processing_time, tokens_used, grant_fund, requested_amount,
                    project_duration, user_id, session_id, get_kuzbass_time()
                ))
                
                conn.commit()
                print(f"Заявка сохранена с номером: {application_number}")
                return application_number
                
        except Exception as e:
            print(f"Ошибка сохранения заявки: {e}")
            return ""
    
    def get_all_applications(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получить список всех заявок"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, application_number, title, summary, status,
                           admin_user, quality_score, llm_provider, model_used,
                           grant_fund, requested_amount, project_duration,
                           created_at, updated_at
                    FROM grant_applications 
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                columns = [desc[0] for desc in cursor.description]
                applications = []
                
                for row in cursor.fetchall():
                    app_dict = dict(zip(columns, row))
                    applications.append(app_dict)
                
                return applications
                
        except Exception as e:
            print(f"Ошибка получения заявок: {e}")
            return []
    
    def get_application_by_number(self, application_number: str) -> Optional[Dict[str, Any]]:
        """Получить заявку по номеру"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM grant_applications 
                    WHERE application_number = ?
                """, (application_number,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    app_dict = dict(zip(columns, row))
                    
                    # Десериализуем JSON содержимое
                    try:
                        app_dict['content'] = json.loads(app_dict['content_json'])
                    except:
                        app_dict['content'] = {}
                    
                    return app_dict
                
                return None
                
        except Exception as e:
            print(f"Ошибка получения заявки {application_number}: {e}")
            return None
    
    def update_application_status(self, application_number: str, status: str) -> bool:
        """Обновить статус заявки"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE grant_applications 
                    SET status = ?, updated_at = ?
                    WHERE application_number = ?
                """, (status, get_kuzbass_time(), application_number))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Ошибка обновления статуса заявки {application_number}: {e}")
            return False
    
    def get_applications_statistics(self) -> Dict[str, Any]:
        """Получить статистику по заявкам"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Общее количество
                cursor.execute("SELECT COUNT(*) FROM grant_applications")
                total_count = cursor.fetchone()[0]
                
                # По статусам
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM grant_applications 
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
                
                # По провайдерам LLM
                cursor.execute("""
                    SELECT llm_provider, COUNT(*) 
                    FROM grant_applications 
                    GROUP BY llm_provider
                """)
                provider_counts = dict(cursor.fetchall())
                
                # Средняя оценка качества
                cursor.execute("SELECT AVG(quality_score) FROM grant_applications")
                avg_quality = cursor.fetchone()[0] or 0.0
                
                return {
                    'total_applications': total_count,
                    'status_distribution': status_counts,
                    'provider_distribution': provider_counts,
                    'average_quality_score': round(avg_quality, 2)
                }
                
        except Exception as e:
            print(f"Ошибка получения статистики заявок: {e}")
            return {}
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С АНКЕТАМИ =====
    
    def generate_anketa_id(self, user_data: Dict[str, Any]) -> str:
        """Генерация ID анкеты в формате #AN-YYYYMMDD-username-001"""
        from datetime import datetime
        
        date_str = datetime.now().strftime("%Y%m%d")
        user_identifier = self._get_user_identifier(user_data)
        
        # Получаем следующий номер анкеты для пользователя за сегодня
        next_number = self._get_next_anketa_number(user_identifier, date_str)
        
        return f"#AN-{date_str}-{user_identifier}-{next_number:03d}"
    
    def _get_user_identifier(self, user_data: Dict[str, Any]) -> str:
        """Получить идентификатор пользователя (username или telegram_id)"""
        if user_data.get('username'):
            return user_data['username']  # Без @
        else:
            return str(user_data['telegram_id'])
    
    def _get_next_anketa_number(self, user_identifier: str, date_str: str) -> int:
        """Получить следующий номер анкеты для пользователя за день"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Ищем максимальный номер анкет для пользователя за сегодня
                cursor.execute("""
                    SELECT MAX(CAST(SUBSTR(anketa_id, -3) AS INTEGER))
                    FROM sessions 
                    WHERE anketa_id LIKE ?
                """, (f"#AN-{date_str}-{user_identifier}-%",))
                
                result = cursor.fetchone()
                max_number = result[0] if result[0] else 0
                
                return max_number + 1
        except Exception as e:
            print(f"Ошибка получения следующего номера анкеты: {e}")
            return 1
    
    def save_anketa(self, anketa_data: Dict[str, Any]) -> str:
        """Сохранить анкету и вернуть anketa_id"""
        try:
            anketa_id = self.generate_anketa_id(anketa_data['user_data'])
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE sessions 
                    SET anketa_id = ?, 
                        interview_data = ?,
                        status = ?,
                        completed_at = ?
                    WHERE id = ?
                """, (
                    anketa_id,
                    json.dumps(anketa_data['interview_data']),
                    'completed',
                    get_kuzbass_time(),
                    anketa_data['session_id']
                ))
                
                conn.commit()
                print(f"Анкета сохранена: {anketa_id}")
                return anketa_id
                
        except Exception as e:
            print(f"Ошибка сохранения анкеты: {e}")
            return None
    
    def get_session_by_anketa_id(self, anketa_id: str) -> Optional[Dict[str, Any]]:
        """Получить сессию по ID анкеты"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT s.*, u.username, u.first_name, u.last_name
                    FROM sessions s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    WHERE s.anketa_id = ?
                """, (anketa_id,))
                
                result = cursor.fetchone()
                if result:
                    columns = [description[0] for description in cursor.description]
                    session_data = dict(zip(columns, result))
                    
                    # Парсим JSON поля
                    if session_data.get('interview_data'):
                        session_data['interview_data'] = json.loads(session_data['interview_data'])
                    
                    return session_data
                return None
                
        except Exception as e:
            print(f"Ошибка получения сессии по anketa_id {anketa_id}: {e}")
            return None
    
    def get_all_sessions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получить все сессии с пагинацией"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT s.*, u.username, u.first_name, u.last_name
                    FROM sessions s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    ORDER BY s.started_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                sessions = []
                for result in results:
                    session_data = dict(zip(columns, result))
                    
                    # Парсим JSON поля
                    for json_field in ['conversation_history', 'collected_data', 'interview_data', 'audit_result', 'plan_structure']:
                        if session_data.get(json_field):
                            try:
                                session_data[json_field] = json.loads(session_data[json_field])
                            except:
                                pass  # Оставляем как строку если не JSON
                    
                    sessions.append(session_data)
                
                return sessions
                
        except Exception as e:
            print(f"Ошибка получения всех сессий: {e}")
            return []
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С ИССЛЕДОВАНИЯМИ =====
    
    def generate_research_id(self, user_data: Dict[str, Any], anketa_id: str) -> str:
        """Генерация ID исследования в формате #RS-YYYYMMDD-username-001-AN-anketa_id"""
        from datetime import datetime
        
        date_str = datetime.now().strftime("%Y%m%d")
        user_identifier = self._get_user_identifier(user_data)
        
        # Получаем следующий номер исследования для пользователя за сегодня
        next_number = self._get_next_research_number(user_identifier, date_str)
        
        return f"#RS-{date_str}-{user_identifier}-{next_number:03d}-AN-{anketa_id}"
    
    def _get_next_research_number(self, user_identifier: str, date_str: str) -> int:
        """Получить следующий номер исследования для пользователя за день"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Ищем максимальный номер исследований для пользователя за сегодня
                cursor.execute("""
                    SELECT MAX(CAST(SUBSTR(research_id, -3) AS INTEGER))
                    FROM researcher_research 
                    WHERE research_id LIKE ?
                """, (f"#RS-{date_str}-{user_identifier}-%",))
                
                result = cursor.fetchone()
                max_number = result[0] if result[0] else 0
                
                return max_number + 1
        except Exception as e:
            print(f"Ошибка получения следующего номера исследования: {e}")
            return 1
    
    def save_research_results(self, research_data: Dict[str, Any]) -> str:
        """Сохранить результаты исследования и вернуть research_id"""
        try:
            research_id = self.generate_research_id(
                research_data['user_data'], 
                research_data['anketa_id']
            )
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO researcher_research 
                    (research_id, anketa_id, user_id, username, first_name, last_name, 
                     session_id, research_type, llm_provider, model, status, 
                     research_results, metadata, created_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    research_id,
                    research_data['anketa_id'],
                    research_data['user_data']['telegram_id'],
                    research_data['user_data'].get('username'),
                    research_data['user_data'].get('first_name'),
                    research_data['user_data'].get('last_name'),
                    research_data.get('session_id'),
                    research_data.get('research_type', 'comprehensive'),
                    research_data['llm_provider'],
                    research_data.get('model'),
                    'completed',
                    json.dumps(research_data['research_results']),
                    json.dumps(research_data.get('metadata', {})),
                    get_kuzbass_time(),
                    get_kuzbass_time()
                ))
                
                conn.commit()
                print(f"Исследование сохранено: {research_id}")
                return research_id
                
        except Exception as e:
            print(f"Ошибка сохранения исследования: {e}")
            return None
    
    def get_research_by_id(self, research_id: str) -> Optional[Dict[str, Any]]:
        """Получить исследование по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM researcher_research WHERE research_id = ?
                """, (research_id,))
                
                result = cursor.fetchone()
                if result:
                    columns = [description[0] for description in cursor.description]
                    research_data = dict(zip(columns, result))
                    
                    # Парсим JSON поля
                    if research_data.get('research_results'):
                        research_data['research_results'] = json.loads(research_data['research_results'])
                    if research_data.get('metadata'):
                        research_data['metadata'] = json.loads(research_data['metadata'])
                    
                    return research_data
                return None
                
        except Exception as e:
            print(f"Ошибка получения исследования {research_id}: {e}")
            return None
    
    def get_research_by_anketa_id(self, anketa_id: str) -> List[Dict[str, Any]]:
        """Получить все исследования по ID анкеты"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM researcher_research 
                    WHERE anketa_id = ? 
                    ORDER BY created_at DESC
                """, (anketa_id,))
                
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                research_list = []
                for row in results:
                    research_data = dict(zip(columns, row))
                    
                    # Парсим JSON поля
                    if research_data.get('research_results'):
                        research_data['research_results'] = json.loads(research_data['research_results'])
                    if research_data.get('metadata'):
                        research_data['metadata'] = json.loads(research_data['metadata'])
                    
                    research_list.append(research_data)
                
                return research_list
                
        except Exception as e:
            print(f"Ошибка получения исследований для анкеты {anketa_id}: {e}")
            return []
    
    def get_all_research(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получить все исследования с пагинацией"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM researcher_research 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                research_list = []
                for row in results:
                    research_data = dict(zip(columns, row))
                    
                    # Парсим JSON поля
                    if research_data.get('research_results'):
                        research_data['research_results'] = json.loads(research_data['research_results'])
                    if research_data.get('metadata'):
                        research_data['metadata'] = json.loads(research_data['metadata'])
                    
                    research_list.append(research_data)
                
                return research_list
                
        except Exception as e:
            print(f"Ошибка получения списка исследований: {e}")
            return []
    
    def get_research_statistics(self) -> Dict[str, Any]:
        """Получить статистику по исследованиям"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Общее количество
                cursor.execute("SELECT COUNT(*) FROM researcher_research")
                total_count = cursor.fetchone()[0]
                
                # По статусам
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM researcher_research 
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
                
                # По провайдерам LLM
                cursor.execute("""
                    SELECT llm_provider, COUNT(*) 
                    FROM researcher_research 
                    GROUP BY llm_provider
                """)
                provider_counts = dict(cursor.fetchall())
                
                # По пользователям
                cursor.execute("""
                    SELECT username, COUNT(*) 
                    FROM researcher_research 
                    WHERE username IS NOT NULL
                    GROUP BY username
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """)
                user_counts = dict(cursor.fetchall())
                
                return {
                    'total_research': total_count,
                    'status_distribution': status_counts,
                    'provider_distribution': provider_counts,
                    'top_users': user_counts
                }
                
        except Exception as e:
            print(f"Ошибка получения статистики исследований: {e}")
            return {}

    def generate_grant_id(self, user_data: Dict[str, Any], anketa_id: str) -> str:
        """Генерирует уникальный ID для гранта"""
        user_identifier = self._get_user_identifier(user_data)
        date_str = datetime.now().strftime("%Y%m%d")
        number = self._get_next_grant_number(user_identifier, date_str)
        return f"#GR-{date_str}-{user_identifier}-{number:03d}-AN-{anketa_id}"

    def _get_next_grant_number(self, user_identifier: str, date_str: str) -> int:
        """Получает следующий номер гранта для пользователя и даты"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM grants 
                    WHERE user_id = ? AND grant_id LIKE ?
                """, (user_identifier, f"#GR-{date_str}-{user_identifier}-%"))
                count = cursor.fetchone()[0]
                return count + 1
        except Exception as e:
            print(f"Ошибка получения номера гранта: {e}")
            return 1

    def save_grant(self, grant_data: Dict[str, Any]) -> str:
        """Сохраняет грант в базу данных"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                # Генерируем ID гранта
                grant_id = self.generate_grant_id(grant_data['user_data'], grant_data['anketa_id'])
                
                # Подготавливаем данные для вставки
                grant_record = {
                    'grant_id': grant_id,
                    'anketa_id': grant_data['anketa_id'],
                    'research_id': grant_data['research_id'],
                    'user_id': grant_data['user_data']['telegram_id'],
                    'username': grant_data['user_data'].get('username'),
                    'first_name': grant_data['user_data'].get('first_name'),
                    'last_name': grant_data['user_data'].get('last_name'),
                    'grant_title': grant_data.get('grant_title', ''),
                    'grant_content': grant_data.get('grant_content', ''),
                    'grant_sections': json.dumps(grant_data.get('grant_sections', {}), ensure_ascii=False),
                    'metadata': json.dumps(grant_data.get('metadata', {}), ensure_ascii=False),
                    'llm_provider': grant_data.get('llm_provider', 'gigachat'),
                    'model': grant_data.get('model', ''),
                    'status': grant_data.get('status', 'draft'),
                    'quality_score': grant_data.get('quality_score', 0)
                }
                
                # Вставляем запись
                cursor.execute("""
                    INSERT INTO grants (
                        grant_id, anketa_id, research_id, user_id, username, 
                        first_name, last_name, grant_title, grant_content, 
                        grant_sections, metadata, llm_provider, model, 
                        status, quality_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    grant_record['grant_id'],
                    grant_record['anketa_id'],
                    grant_record['research_id'],
                    grant_record['user_id'],
                    grant_record['username'],
                    grant_record['first_name'],
                    grant_record['last_name'],
                    grant_record['grant_title'],
                    grant_record['grant_content'],
                    grant_record['grant_sections'],
                    grant_record['metadata'],
                    grant_record['llm_provider'],
                    grant_record['model'],
                    grant_record['status'],
                    grant_record['quality_score']
                ))
                
                conn.commit()
                print(f"Грант сохранен: {grant_id}")
                return grant_id
                
        except Exception as e:
            print(f"Ошибка сохранения гранта: {e}")
            return None

    def get_grant_by_id(self, grant_id: str) -> Optional[Dict[str, Any]]:
        """Получить грант по ID"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM grants WHERE grant_id = ?", (grant_id,))
                result = cursor.fetchone()
                
                if result:
                    columns = [description[0] for description in cursor.description]
                    grant_data = dict(zip(columns, result))
                    
                    # Парсим JSON поля
                    if grant_data.get('grant_sections'):
                        try:
                            grant_data['grant_sections'] = json.loads(grant_data['grant_sections'])
                        except:
                            grant_data['grant_sections'] = {}
                    
                    if grant_data.get('metadata'):
                        try:
                            grant_data['metadata'] = json.loads(grant_data['metadata'])
                        except:
                            grant_data['metadata'] = {}
                    
                    return grant_data
                return None
                
        except Exception as e:
            print(f"Ошибка получения гранта: {e}")
            return None

    def get_all_grants(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получить все гранты с пагинацией"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT g.*, s.username, s.first_name, s.last_name
                    FROM grants g
                    LEFT JOIN sessions s ON g.anketa_id = s.anketa_id
                    ORDER BY g.created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                results = cursor.fetchall()
                
                grants = []
                for row in results:
                    columns = [description[0] for description in cursor.description]
                    grant_data = dict(zip(columns, row))
                    
                    # Парсим JSON поля
                    if grant_data.get('grant_sections'):
                        try:
                            grant_data['grant_sections'] = json.loads(grant_data['grant_sections'])
                        except:
                            grant_data['grant_sections'] = {}
                    
                    if grant_data.get('metadata'):
                        try:
                            grant_data['metadata'] = json.loads(grant_data['metadata'])
                        except:
                            grant_data['metadata'] = {}
                    
                    grants.append(grant_data)
                
                return grants
                
        except Exception as e:
            print(f"Ошибка получения всех грантов: {e}")
            return []

def get_connection():
    """Получить соединение с БД (для внутреннего использования)"""
    from . import db
    return sqlite3.connect(db.db_path) 