"""
Система управления промптами агентов в базе данных
"""
import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

def init_prompts_tables(db_path: str = "/var/GrantService/data/grantservice.db"):
    """Инициализация таблиц для промптов"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Таблица категорий промптов
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prompt_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        agent_type VARCHAR(50) NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Таблица промптов
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        prompt_template TEXT NOT NULL,
        variables TEXT, -- JSON список переменных
        default_values TEXT, -- JSON с дефолтными значениями
        is_active BOOLEAN DEFAULT 1,
        priority INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES prompt_categories(id)
    )
    """)
    
    # Таблица версий промптов (для истории изменений)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prompt_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_id INTEGER NOT NULL,
        prompt_template TEXT NOT NULL,
        variables TEXT,
        default_values TEXT,
        version_number INTEGER NOT NULL,
        created_by VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (prompt_id) REFERENCES agent_prompts(id)
    )
    """)
    
    conn.commit()
    conn.close()

def insert_default_prompts(db_path: str = "/var/GrantService/data/grantservice.db"):
    """Вставка дефолтных промптов"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Категории промптов
    categories = [
        ("researcher_market", "Анализ рынка", "researcher"),
        ("researcher_competitors", "Анализ конкурентов", "researcher"),
        ("researcher_grants", "Поиск грантов", "researcher"),
        ("researcher_success", "Факторы успеха", "researcher"),
        ("writer_summary", "Резюме проекта", "writer"),
        ("writer_description", "Описание проекта", "writer"),
        ("writer_methodology", "Методология", "writer"),
        ("writer_budget", "Бюджет", "writer"),
        ("writer_timeline", "План реализации", "writer"),
        ("auditor_completeness", "Проверка полноты", "auditor"),
        ("auditor_quality", "Оценка качества", "auditor"),
        ("auditor_compliance", "Соответствие требованиям", "auditor"),
        ("interviewer_questions", "Создание вопросов", "interviewer"),
        ("interviewer_followup", "Дополнительные вопросы", "interviewer")
    ]
    
    for category_name, description, agent_type in categories:
        cursor.execute("""
        INSERT OR IGNORE INTO prompt_categories (name, description, agent_type)
        VALUES (?, ?, ?)
        """, (category_name, description, agent_type))
    
    # Дефолтные промпты
    default_prompts = [
        # Researcher - Анализ рынка
        ("researcher_market", "Анализ рынка", 
         "Проведи анализ рынка для следующего проекта:\n\n{project_description}\n\nПроанализируй:\n1. Размер рынка и потенциал роста\n2. Ключевые тренды в отрасли\n3. Целевая аудитория\n4. Рыночные возможности\n5. Потенциальные риски\n\nДай конкретные цифры и факты.",
         ["project_description"]),
        
        # Researcher - Анализ конкурентов
        ("researcher_competitors", "Анализ конкурентов",
         "Найди и проанализируй конкурентов для следующего проекта:\n\n{project_description}\n\nДля каждого конкурента укажи:\n1. Название компании\n2. Основные продукты/услуги\n3. Сильные стороны\n4. Слабые стороны\n5. Доля рынка (если известна)\n6. Конкурентные преимущества проекта",
         ["project_description"]),
        
        # Researcher - Поиск грантов
        ("researcher_grants", "Поиск грантов",
         "Найди подходящие гранты для следующего проекта:\n\n{project_description}\n\nДля каждого гранта укажи:\n1. Название фонда/программы\n2. Размер финансирования\n3. Сроки подачи заявок\n4. Основные требования\n5. Процент соответствия проекту\n6. Вероятность получения\n7. Контакты для подачи",
         ["project_description"]),
        
        # Writer - Резюме проекта
        ("writer_summary", "Резюме проекта",
         "Создай краткое резюме проекта на основе следующих данных:\n\n{research_data}\n\nРезюме должно включать:\n1. Название проекта\n2. Основную идею\n3. Цели и задачи\n4. Ожидаемые результаты\n5. Запрашиваемую сумму\n\nМаксимум 200 слов.",
         ["research_data"]),
        
        # Writer - Описание проекта
        ("writer_description", "Описание проекта",
         "Создай подробное описание проекта:\n\n{research_data}\n\nВключи:\n1. Проблему, которую решает проект\n2. Предлагаемое решение\n3. Уникальность подхода\n4. Технологические аспекты\n5. Ожидаемое влияние\n\nИспользуй профессиональный, но понятный язык.",
         ["research_data"]),
        
        # Auditor - Проверка полноты
        ("auditor_completeness", "Проверка полноты",
         "Проверь полноту заявки:\n\n{application_text}\n\nПроверь наличие:\n1. Четкого описания проекта\n2. Обоснования бюджета\n3. Плана реализации\n4. Информации о команде\n5. Ожидаемых результатов\n\nДай оценку по шкале 1-10 и рекомендации.",
         ["application_text"]),
        
        # Interviewer - Создание вопросов
        ("interviewer_questions", "Создание вопросов",
         "Создай вопросы для интервью на основе:\n\n{user_profile}\n\nСоздай 10-15 вопросов:\n1. О проекте и команде\n2. О бюджете и финансах\n3. О планах реализации\n4. О рисках и вызовах\n5. О ожидаемых результатах\n\nВопросы должны быть открытыми и направляющими.",
         ["user_profile"])
    ]
    
    for category_name, name, template, variables in default_prompts:
        # Получаем ID категории
        cursor.execute("SELECT id FROM prompt_categories WHERE name = ?", (category_name,))
        category_id = cursor.fetchone()[0]
        
        # Вставляем промпт
        cursor.execute("""
        INSERT OR IGNORE INTO agent_prompts 
        (category_id, name, description, prompt_template, variables, priority)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (category_id, name, name, template, json.dumps(variables), 0))
    
    conn.commit()
    conn.close()

def get_prompt_by_name(prompt_name: str, db_path: str = "/var/GrantService/data/grantservice.db") -> Optional[Dict]:
    """Получить промпт по названию"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT p.id, p.name, p.description, p.prompt_template, p.variables, p.default_values,
           c.name as category_name, c.agent_type
    FROM agent_prompts p
    JOIN prompt_categories c ON p.category_id = c.id
    WHERE p.name = ? AND p.is_active = 1
    """, (prompt_name,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'name': result[1],
            'description': result[2],
            'prompt_template': result[3],
            'variables': json.loads(result[4]) if result[4] else [],
            'default_values': json.loads(result[5]) if result[5] else {},
            'category_name': result[6],
            'agent_type': result[7]
        }
    return None

def get_prompts_by_agent(agent_type: str, db_path: str = "/var/GrantService/data/grantservice.db") -> List[Dict]:
    """Получить все промпты для конкретного агента"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT p.id, p.name, p.description, p.prompt_template, p.variables, p.default_values,
           c.name as category_name, c.agent_type, p.priority
    FROM agent_prompts p
    JOIN prompt_categories c ON p.category_id = c.id
    WHERE c.agent_type = ? AND p.is_active = 1
    ORDER BY p.priority DESC, p.name
    """, (agent_type,))
    
    results = cursor.fetchall()
    conn.close()
    
    prompts = []
    for result in results:
        prompts.append({
            'id': result[0],
            'name': result[1],
            'description': result[2],
            'prompt_template': result[3],
            'variables': json.loads(result[4]) if result[4] else [],
            'default_values': json.loads(result[5]) if result[5] else {},
            'category_name': result[6],
            'agent_type': result[7],
            'priority': result[8]
        })
    
    return prompts

def get_prompts_by_category(category_name: str, db_path: str = "/var/GrantService/data/grantservice.db") -> List[Dict]:
    """Получить промпты по категории"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT p.id, p.name, p.description, p.prompt_template, p.variables, p.default_values,
           c.name as category_name, c.agent_type, p.priority
    FROM agent_prompts p
    JOIN prompt_categories c ON p.category_id = c.id
    WHERE c.name = ? AND p.is_active = 1
    ORDER BY p.priority DESC, p.name
    """, (category_name,))
    
    results = cursor.fetchall()
    conn.close()
    
    prompts = []
    for result in results:
        prompts.append({
            'id': result[0],
            'name': result[1],
            'description': result[2],
            'prompt_template': result[3],
            'variables': json.loads(result[4]) if result[4] else [],
            'default_values': json.loads(result[5]) if result[5] else {},
            'category_name': result[6],
            'agent_type': result[7],
            'priority': result[8]
        })
    
    return prompts

def create_prompt(category_name: str, name: str, description: str, prompt_template: str, 
                 variables: List[str] = None, default_values: Dict = None, 
                 priority: int = 0, db_path: str = "/var/GrantService/data/grantservice.db") -> bool:
    """Создать новый промпт"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем ID категории
        cursor.execute("SELECT id FROM prompt_categories WHERE name = ?", (category_name,))
        category_result = cursor.fetchone()
        
        if not category_result:
            conn.close()
            return False
        
        category_id = category_result[0]
        
        # Вставляем промпт
        cursor.execute("""
        INSERT INTO agent_prompts 
        (category_id, name, description, prompt_template, variables, default_values, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (category_id, name, description, prompt_template, 
              json.dumps(variables or []), json.dumps(default_values or {}), priority))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка создания промпта: {e}")
        return False

def update_prompt(prompt_id: int, name: str = None, description: str = None, 
                 prompt_template: str = None, variables: List[str] = None, 
                 default_values: Dict = None, priority: int = None,
                 db_path: str = "/var/GrantService/data/grantservice.db") -> bool:
    """Обновить промпт"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Сначала сохраняем версию
        cursor.execute("""
        SELECT prompt_template, variables, default_values FROM agent_prompts WHERE id = ?
        """, (prompt_id,))
        
        current = cursor.fetchone()
        if current:
            # Получаем номер следующей версии
            cursor.execute("""
            SELECT MAX(version_number) FROM prompt_versions WHERE prompt_id = ?
            """, (prompt_id,))
            
            version_result = cursor.fetchone()
            next_version = (version_result[0] or 0) + 1
            
            # Сохраняем версию
            cursor.execute("""
            INSERT INTO prompt_versions 
            (prompt_id, prompt_template, variables, default_values, version_number)
            VALUES (?, ?, ?, ?, ?)
            """, (prompt_id, current[0], current[1], current[2], next_version))
        
        # Обновляем промпт
        update_fields = []
        update_values = []
        
        if name is not None:
            update_fields.append("name = ?")
            update_values.append(name)
        
        if description is not None:
            update_fields.append("description = ?")
            update_values.append(description)
        
        if prompt_template is not None:
            update_fields.append("prompt_template = ?")
            update_values.append(prompt_template)
        
        if variables is not None:
            update_fields.append("variables = ?")
            update_values.append(json.dumps(variables))
        
        if default_values is not None:
            update_fields.append("default_values = ?")
            update_values.append(json.dumps(default_values))
        
        if priority is not None:
            update_fields.append("priority = ?")
            update_values.append(priority)
        
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(prompt_id)
            
            query = f"UPDATE agent_prompts SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка обновления промпта: {e}")
        return False

def delete_prompt(prompt_id: int, db_path: str = "/var/GrantService/data/grantservice.db") -> bool:
    """Удалить промпт (мягкое удаление)"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE agent_prompts SET is_active = 0 WHERE id = ?", (prompt_id,))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка удаления промпта: {e}")
        return False

def format_prompt(prompt_template: str, variables: Dict[str, Any]) -> str:
    """Форматировать промпт с переменными"""
    try:
        return prompt_template.format(**variables)
    except KeyError as e:
        # Если не хватает переменной, заменяем на пустую строку
        missing_var = str(e).strip("'")
        variables[missing_var] = ""
        return prompt_template.format(**variables)
    except Exception as e:
        print(f"Ошибка форматирования промпта: {e}")
        return prompt_template

def get_all_categories(db_path: str = "/var/GrantService/data/grantservice.db") -> List[Dict]:
    """Получить все категории промптов"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, name, description, agent_type, is_active, created_at
    FROM prompt_categories
    ORDER BY agent_type, name
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    categories = []
    for result in results:
        categories.append({
            'id': result[0],
            'name': result[1],
            'description': result[2],
            'agent_type': result[3],
            'is_active': bool(result[4]),
            'created_at': result[5]
        })
    
    return categories
