#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки автоматического создания грантовых заявок
"""

import sys
import os
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "telegram-bot"))

# Импортируем функции
from utils.grant_application_creator import create_grant_application_from_session

def test_auto_grant_creation():
    """Тестируем создание грантовой заявки"""
    
    print("=" * 60)
    print("ТЕСТ АВТОМАТИЧЕСКОГО СОЗДАНИЯ ГРАНТОВЫХ ЗАЯВОК")
    print("=" * 60)
    
    # Тестовые данные
    test_user_data = {
        "telegram_id": 123456789,
        "username": "test_user",
        "first_name": "Тестовый",
        "last_name": "Пользователь"
    }
    
    test_answers = {
        "project_name": "Инновационный IT-проект",
        "project_description": "Описание проекта для тестирования",
        "team_size": "5 человек",
        "budget": "1000000 рублей",
        "duration": "12 месяцев"
    }
    
    # Предполагаем существующую сессию ID
    test_session_id = 1
    
    print(f"Тестируем создание заявки для сессии {test_session_id}")
    print(f"Пользователь: {test_user_data['first_name']} {test_user_data['last_name']}")
    print(f"Проект: {test_answers['project_name']}")
    print()
    
    # Создаем заявку
    try:
        app_number = create_grant_application_from_session(
            session_id=test_session_id,
            user_data=test_user_data,
            answers=test_answers
        )
        
        if app_number:
            print(f"✅ Успешно создана заявка: {app_number}")
            
            # Проверяем в БД
            from data.database import get_application_by_number
            application = get_application_by_number(app_number)
            
            if application:
                print(f"✅ Заявка найдена в БД:")
                print(f"   ID: {application.get('id')}")
                print(f"   Номер: {application.get('application_number')}")
                print(f"   Название: {application.get('title')}")
                print(f"   Статус: {application.get('status')}")
                print(f"   Создана: {application.get('created_at')}")
            else:
                print(f"❌ Заявка {app_number} не найдена в БД")
        else:
            print("❌ Не удалось создать заявку")
            
    except Exception as e:
        print(f"❌ Ошибка при создании заявки: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)

if __name__ == "__main__":
    test_auto_grant_creation()