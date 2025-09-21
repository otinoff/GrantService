#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для автоматического создания грантовых заявок после завершения интервью
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def create_grant_application_from_session(session_id: int, user_data: Dict[str, Any], answers: Dict[str, Any]) -> Optional[str]:
    """
    Создает грантовую заявку из завершенной сессии интервью
    
    Args:
        session_id: ID сессии в БД
        user_data: Данные пользователя (telegram_id, username, first_name, last_name)
        answers: Ответы пользователя на вопросы интервью
        
    Returns:
        application_number: Номер созданной заявки или None при ошибке
    """
    try:
        # Импортируем БД
        from data.database import save_grant_application
        
        # Генерируем номер заявки
        date_str = datetime.now().strftime('%Y%m%d')
        app_number = f"GA-{date_str}-{str(uuid.uuid4())[:8].upper()}"
        
        # Определяем название проекта из ответов
        title = "Автоматически созданная заявка"
        
        # Ищем название проекта в ответах
        for key, value in answers.items():
            if key in ['project_name', 'название_проекта', '1', 'project_title']:
                if value and len(str(value).strip()) > 0:
                    title = str(value).strip()
                    break
        
        # Подготавливаем содержимое заявки
        content_data = {
            "user_info": user_data,
            "interview_answers": answers,
            "session_id": session_id,
            "_auto_created": {
                "created_at": datetime.now().isoformat(),
                "source": "telegram_bot_auto",
                "version": "1.0"
            }
        }
        
        # Подготавливаем краткое описание
        summary = f"Заявка автоматически создана из интервью. Пользователь: {user_data.get('first_name', '')} {user_data.get('last_name', '')}"
        
        # Данные для сохранения в БД
        application_data = {
            "application_number": app_number,
            "title": title,
            "content_json": json.dumps(content_data, ensure_ascii=False, indent=2),
            "summary": summary,
            "status": "draft",
            "user_id": None,  # Пока не связываем с user_id
            "session_id": session_id,
            "admin_user": "telegram_bot_auto",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Сохраняем заявку
        result = save_grant_application(application_data)
        
        if result:
            logger.info(f"✅ Автоматически создана грантовая заявка: {app_number}")
            logger.info(f"   Сессия: {session_id}")
            logger.info(f"   Пользователь: {user_data.get('telegram_id')}")
            logger.info(f"   Название: {title}")
            return app_number
        else:
            logger.error(f"❌ Не удалось сохранить заявку {app_number}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания грантовой заявки: {e}")
        import traceback
        traceback.print_exc()
        return None

def update_session_completion_status(session_id: int, app_number: Optional[str] = None):
    """
    Обновляет статус завершения сессии и связывает с созданной заявкой
    
    Args:
        session_id: ID сессии
        app_number: Номер созданной заявки (если есть)
    """
    try:
        from data.database import db
        
        # Обновляем статус сессии
        with db.connect() as conn:
            cursor = conn.cursor()
            
            update_data = {
                'status': 'completed',
                'completed_at': datetime.now().isoformat()
            }
            
            # Если создана заявка, добавляем ссылку
            if app_number:
                update_data['application_number'] = app_number
            
            # Формируем SQL запрос
            set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
            values = list(update_data.values()) + [session_id]
            
            cursor.execute(f"""
                UPDATE sessions 
                SET {set_clause}
                WHERE id = ?
            """, values)
            
            conn.commit()
            
            logger.info(f"✅ Обновлен статус сессии {session_id}: completed")
            if app_number:
                logger.info(f"   Связана с заявкой: {app_number}")
                
    except Exception as e:
        logger.error(f"❌ Ошибка обновления статуса сессии {session_id}: {e}")