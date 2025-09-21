#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест автосохранения анкет после 14 вопроса
"""

import sys
import os

# Добавляем путь к модулям
if os.name == 'nt':  # Windows
    sys.path.append('C:\\SnowWhiteAI\\GrantService')
else:  # Linux/Ubuntu
    sys.path.append('/var/GrantService')

from data.database import db, get_or_create_session
from utils.console_helper import safe_print

def test_anketa_generation():
    """Тест генерации ID анкеты"""
    safe_print("=== Тест генерации ID анкеты ===")
    
    # Тестовые данные пользователя
    test_user_data = {
        "telegram_id": 123456789,
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # Генерируем ID анкеты
    anketa_id = db.generate_anketa_id(test_user_data)
    safe_print(f"Сгенерированный ID анкеты: {anketa_id}")
    
    # Проверяем формат
    assert anketa_id.startswith("#AN-"), "ID должен начинаться с #AN-"
    assert "test_user" in anketa_id, "ID должен содержать username"
    safe_print("[OK] Генерация ID анкеты работает корректно")
    
    return anketa_id

def test_anketa_save():
    """Тест сохранения анкеты"""
    safe_print("\n=== Тест сохранения анкеты ===")
    
    # Тестовые данные
    test_user_data = {
        "telegram_id": 123456789,
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # Создаем тестовую сессию
    session = get_or_create_session(123456789)
    if not session:
        safe_print("[ERROR] Не удалось создать сессию")
        return None
    
    safe_print(f"Создана сессия с ID: {session['id']}")
    
    # Подготавливаем данные анкеты
    anketa_data = {
        "user_data": test_user_data,
        "session_id": session['id'],
        "interview_data": {
            "project_name": "Тестовый проект",
            "description": "Описание тестового проекта",
            "team_size": "5 человек",
            "budget": "1000000 рублей"
        }
    }
    
    # Сохраняем анкету
    anketa_id = db.save_anketa(anketa_data)
    if anketa_id:
        safe_print(f"[OK] Анкета сохранена с ID: {anketa_id}")
    else:
        safe_print("[ERROR] Не удалось сохранить анкету")
    
    return anketa_id

def test_anketa_retrieval(anketa_id):
    """Тест получения анкеты из БД"""
    safe_print(f"\n=== Тест получения анкеты {anketa_id} ===")
    
    # Получаем анкету по ID
    anketa = db.get_session_by_anketa_id(anketa_id)
    
    if anketa:
        safe_print(f"[OK] Анкета найдена:")
        safe_print(f"  - ID сессии: {anketa.get('id')}")
        safe_print(f"  - Telegram ID: {anketa.get('telegram_id')}")
        safe_print(f"  - Username: {anketa.get('username')}")
        safe_print(f"  - Статус: {anketa.get('status')}")
        
        if anketa.get('interview_data'):
            safe_print(f"  - Данные интервью: {len(anketa['interview_data'])} полей")
        
        return True
    else:
        safe_print(f"[ERROR] Анкета {anketa_id} не найдена")
        return False

def test_multiple_anketas():
    """Тест создания нескольких анкет для одного пользователя"""
    safe_print("\n=== Тест множественных анкет ===")
    
    test_user_data = {
        "telegram_id": 987654321,
        "username": "multi_user",
        "first_name": "Multi",
        "last_name": "User"
    }
    
    anketa_ids = []
    
    # Создаем 3 анкеты
    for i in range(3):
        # Создаем новую сессию для каждой анкеты
        session = get_or_create_session(987654321)
        
        if not session:
            safe_print(f"  [WARNING] Не удалось создать сессию #{i+1}")
            continue
            
        anketa_data = {
            "user_data": test_user_data,
            "session_id": session['id'],
            "interview_data": {
                "project_name": f"Проект #{i+1}",
                "iteration": i+1
            }
        }
        
        anketa_id = db.save_anketa(anketa_data)
        if anketa_id:
            anketa_ids.append(anketa_id)
            safe_print(f"  Анкета {i+1}: {anketa_id}")
    
    safe_print(f"[OK] Создано {len(anketa_ids)} анкет для одного пользователя")
    
    # Проверяем, что все ID уникальные
    assert len(anketa_ids) == len(set(anketa_ids)), "Все ID должны быть уникальными"
    safe_print("[OK] Все ID анкет уникальны")
    
    return anketa_ids

def main():
    """Главная функция тестирования"""
    safe_print("=" * 50)
    safe_print("ТЕСТИРОВАНИЕ АВТОСОХРАНЕНИЯ АНКЕТ")
    safe_print("=" * 50)
    
    try:
        # Тест 1: Генерация ID
        anketa_id = test_anketa_generation()
        
        # Тест 2: Сохранение анкеты
        saved_anketa_id = test_anketa_save()
        
        # Тест 3: Получение анкеты
        if saved_anketa_id:
            test_anketa_retrieval(saved_anketa_id)
        
        # Тест 4: Множественные анкеты
        test_multiple_anketas()
        
        safe_print("\n" + "=" * 50)
        safe_print("[OK] ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        safe_print("=" * 50)
        
    except Exception as e:
        safe_print("\n" + "=" * 50)
        safe_print(f"[ERROR] ОШИБКА ПРИ ТЕСТИРОВАНИИ: {e}")
        safe_print("=" * 50)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()