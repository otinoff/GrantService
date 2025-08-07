#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с промптами агентов
"""

import json
import sqlite3
from typing import List, Dict, Any, Optional
from .models import GrantServiceDatabase, get_kuzbass_time

class AgentPromptManager:
    def __init__(self, db: GrantServiceDatabase):
        self.db = db
    
    def get_agent_prompts(self, agent_type: str) -> List[Dict[str, Any]]:
        """Получить все активные промпты для агента"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM agent_prompts 
                    WHERE agent_type = ? AND is_active = 1
                    ORDER BY order_num, id
                """, (agent_type,))
                
                columns = [description[0] for description in cursor.description]
                prompts = []
                for row in cursor.fetchall():
                    prompt = dict(zip(columns, row))
                    prompts.append(prompt)
                
                return prompts
        except Exception as e:
            print(f"❌ Ошибка получения промптов агента {agent_type}: {e}")
            return []
    
    def get_prompt_by_id(self, prompt_id: int) -> Optional[Dict[str, Any]]:
        """Получить промпт по ID"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM agent_prompts WHERE id = ?", (prompt_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"❌ Ошибка получения промпта {prompt_id}: {e}")
            return None
    
    def create_agent_prompt(self, data: Dict[str, Any]) -> int:
        """Создать новый промпт для агента"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO agent_prompts (
                        agent_type, prompt_name, prompt_content, prompt_type,
                        order_num, temperature, max_tokens, model_name, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('agent_type'),
                    data.get('prompt_name'),
                    data.get('prompt_content'),
                    data.get('prompt_type', 'system'),
                    data.get('order_num', 1),
                    data.get('temperature', 0.7),
                    data.get('max_tokens', 2000),
                    data.get('model_name', 'GigaChat-Pro'),
                    data.get('is_active', True)
                ))
                
                prompt_id = cursor.lastrowid
                conn.commit()
                print(f"✅ Создан промпт {prompt_id} для агента {data.get('agent_type')}")
                return prompt_id
        except Exception as e:
            print(f"❌ Ошибка создания промпта: {e}")
            return 0
    
    def update_agent_prompt(self, prompt_id: int, data: Dict[str, Any]) -> bool:
        """Обновить промпт агента"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE agent_prompts SET
                        agent_type = ?, prompt_name = ?, prompt_content = ?,
                        prompt_type = ?, order_num = ?, temperature = ?,
                        max_tokens = ?, model_name = ?, is_active = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    data.get('agent_type'),
                    data.get('prompt_name'),
                    data.get('prompt_content'),
                    data.get('prompt_type', 'system'),
                    data.get('order_num', 1),
                    data.get('temperature', 0.7),
                    data.get('max_tokens', 2000),
                    data.get('model_name', 'GigaChat-Pro'),
                    data.get('is_active', True),
                    get_kuzbass_time(),
                    prompt_id
                ))
                
                conn.commit()
                print(f"✅ Обновлен промпт {prompt_id}")
                return True
        except Exception as e:
            print(f"❌ Ошибка обновления промпта {prompt_id}: {e}")
            return False
    
    def delete_agent_prompt(self, prompt_id: int) -> bool:
        """Удалить промпт агента"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM agent_prompts WHERE id = ?", (prompt_id,))
                conn.commit()
                print(f"✅ Удален промпт {prompt_id}")
                return True
        except Exception as e:
            print(f"❌ Ошибка удаления промпта {prompt_id}: {e}")
            return False
    
    def insert_default_prompts(self):
        """Вставить промпты по умолчанию для всех агентов"""
        default_prompts = [
            # Промпты для исследователя
            {
                'agent_type': 'researcher',
                'prompt_name': 'Системный промпт',
                'prompt_content': 'Ты - эксперт-исследователь в области грантов и проектов. Твоя задача - анализировать информацию о проектах и находить релевантные данные для создания качественных заявок.',
                'prompt_type': 'system',
                'order_num': 1
            },
            {
                'agent_type': 'researcher',
                'prompt_name': 'Поиск контекста',
                'prompt_content': 'Проанализируй описание проекта и найди актуальную информацию о: 1) Подобных проектах в этой области 2) Требованиях грантодателей 3) Ключевых трендах в отрасли 4) Успешных примерах реализации',
                'prompt_type': 'task',
                'order_num': 2
            },
            # Промпты для писателя
            {
                'agent_type': 'writer',
                'prompt_name': 'Системный промпт',
                'prompt_content': 'Ты - профессиональный писатель грантовых заявок с 10+ летним опытом. Твоя задача - создавать убедительные, структурированные и профессиональные заявки на гранты.',
                'prompt_type': 'system',
                'order_num': 1
            },
            {
                'agent_type': 'writer',
                'prompt_name': 'Создание заявки',
                'prompt_content': 'На основе собранной информации создай профессиональную грантовую заявку. Структура: 1) Краткое резюме проекта 2) Описание проблемы и решения 3) Цели и задачи 4) Методология 5) Ожидаемые результаты 6) Бюджет и временные рамки',
                'prompt_type': 'task',
                'order_num': 2
            },
            # Промпты для аналитика
            {
                'agent_type': 'auditor',
                'prompt_name': 'Системный промпт',
                'prompt_content': 'Ты - эксперт-аналитик по оценке качества грантовых заявок. Твоя задача - критически анализировать заявки и давать конструктивные рекомендации по улучшению.',
                'prompt_type': 'system',
                'order_num': 1
            },
            {
                'agent_type': 'auditor',
                'prompt_name': 'Анализ качества',
                'prompt_content': 'Проанализируй грантовую заявку по критериям: 1) Соответствие требованиям грантодателя 2) Логичность и структурированность 3) Убедительность аргументации 4) Реалистичность целей и бюджета 5) Инновационность подхода. Дай конкретные рекомендации по улучшению.',
                'prompt_type': 'task',
                'order_num': 2
            }
        ]
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем, есть ли уже промпты
                cursor.execute("SELECT COUNT(*) FROM agent_prompts")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    for prompt_data in default_prompts:
                        cursor.execute("""
                            INSERT INTO agent_prompts (
                                agent_type, prompt_name, prompt_content, prompt_type,
                                order_num, temperature, max_tokens, model_name, is_active
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            prompt_data['agent_type'],
                            prompt_data['prompt_name'],
                            prompt_data['prompt_content'],
                            prompt_data['prompt_type'],
                            prompt_data['order_num'],
                            0.7,  # temperature
                            2000,  # max_tokens
                            'GigaChat-Pro',  # model_name
                            True  # is_active
                        ))
                    
                    conn.commit()
                    print(f"✅ Добавлено {len(default_prompts)} промптов по умолчанию")
                else:
                    print("ℹ️ Промпты уже существуют, пропускаем вставку по умолчанию")
        except Exception as e:
            print(f"❌ Ошибка вставки промптов по умолчанию: {e}")

# Глобальные функции для совместимости
def get_agent_prompts(agent_type: str = None) -> List[Dict]:
    """Получить промпты агентов"""
    try:
        from . import db
        manager = AgentPromptManager(db)
        return manager.get_agent_prompts(agent_type) if agent_type else []
    except Exception as e:
        print(f"Ошибка получения промптов агентов: {e}")
        return []

def insert_agent_prompt(agent_type: str, prompt_name: str, prompt_content: str,
                       prompt_type: str = 'system', order_num: int = 1,
                       temperature: float = 0.7, max_tokens: int = 2000,
                       model_name: str = 'GigaChat-Pro', is_active: bool = True):
    """Создание промпта агента (совместимость с новыми страницами)"""
    try:
        from . import db
        manager = AgentPromptManager(db)
        data = {
            'agent_type': agent_type,
            'prompt_name': prompt_name,
            'prompt_content': prompt_content,
            'prompt_type': prompt_type,
            'order_num': order_num,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'model_name': model_name,
            'is_active': is_active
        }
        return manager.create_agent_prompt(data)
    except Exception as e:
        print(f"Ошибка создания промпта: {e}")
        return 0

def update_agent_prompt(prompt_id: int, **kwargs):
    """Обновление промпта агента (совместимость с новыми страницами)"""
    try:
        from . import db
        manager = AgentPromptManager(db)
        return manager.update_agent_prompt(prompt_id, kwargs)
    except Exception as e:
        print(f"Ошибка обновления промпта: {e}")
        return False

def delete_agent_prompt(prompt_id: int):
    """Удаление промпта агента (совместимость с новыми страницами)"""
    try:
        from . import db
        manager = AgentPromptManager(db)
        return manager.delete_agent_prompt(prompt_id)
    except Exception as e:
        print(f"Ошибка удаления промпта: {e}")
        return False 