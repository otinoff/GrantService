#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки новой функциональности анкет и исследований
"""

import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

from data.database import db
from agents.researcher_agent import ResearcherAgent

def test_anketa_creation():
    """Тест создания анкеты"""
    print("🧪 Тестирование создания анкеты...")
    
    # Тестовые данные пользователя
    user_data = {
        "telegram_id": 123456789,
        "username": "test_user",
        "first_name": "Тест",
        "last_name": "Пользователь"
    }
    
    # Тестовые данные анкеты
    anketa_data = {
        "user_data": user_data,
        "session_id": 1,  # Предполагаем, что есть сессия с ID 1
        "interview_data": {
            "question_1": "Название проекта: Тестовая ИИ-платформа",
            "question_2": "Описание: Разрабатываем платформу для автоматизации",
            "question_3": "Бюджет: 1000000 рублей",
            "question_4": "Команда: 5 человек",
            "question_5": "Сроки: 12 месяцев"
        }
    }
    
    try:
        # Создаем анкету
        anketa_id = db.save_anketa(anketa_data)
        
        if anketa_id:
            print(f"✅ Анкета создана: {anketa_id}")
            return anketa_id
        else:
            print("❌ Ошибка создания анкеты")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка создания анкеты: {e}")
        return None

def test_research_creation(anketa_id):
    """Тест создания исследования"""
    print(f"🧪 Тестирование создания исследования для анкеты {anketa_id}...")
    
    try:
        # Создаем Researcher Agent
        researcher = ResearcherAgent(db=db)
        
        # Проводим исследование
        result = researcher.research_anketa(anketa_id)
        
        if result.get('status') == 'success':
            print(f"✅ Исследование создано: {result.get('research_id')}")
            return result.get('research_id')
        else:
            print(f"❌ Ошибка создания исследования: {result.get('message')}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка создания исследования: {e}")
        return None

def test_database_queries():
    """Тест запросов к базе данных"""
    print("🧪 Тестирование запросов к базе данных...")
    
    try:
        # Получаем статистику анкет
        print("📊 Статистика анкет:")
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE anketa_id IS NOT NULL")
            anketa_count = cursor.fetchone()[0]
            print(f"  • Всего анкет: {anketa_count}")
        
        # Получаем статистику исследований
        print("📊 Статистика исследований:")
        research_stats = db.get_research_statistics()
        print(f"  • Всего исследований: {research_stats.get('total_research', 0)}")
        print(f"  • По статусам: {research_stats.get('status_distribution', {})}")
        print(f"  • По провайдерам: {research_stats.get('provider_distribution', {})}")
        
        # Получаем список всех исследований
        all_research = db.get_all_research(limit=10)
        print(f"📋 Последние исследования ({len(all_research)}):")
        for research in all_research:
            print(f"  • {research['research_id']} - {research.get('username', 'N/A')} - {research['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка запросов к БД: {e}")
        return False

def test_id_generation():
    """Тест генерации ID"""
    print("🧪 Тестирование генерации ID...")
    
    # Тестовые данные пользователя
    user_data = {
        "telegram_id": 987654321,
        "username": "another_user",
        "first_name": "Другой",
        "last_name": "Пользователь"
    }
    
    try:
        # Генерируем anketa_id
        anketa_id = db.generate_anketa_id(user_data)
        print(f"✅ Сгенерирован anketa_id: {anketa_id}")
        
        # Генерируем research_id
        research_id = db.generate_research_id(user_data, anketa_id)
        print(f"✅ Сгенерирован research_id: {research_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка генерации ID: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования новой функциональности")
    print("=" * 50)
    
    # Тест 1: Генерация ID
    print("\n1️⃣ Тест генерации ID")
    test_id_generation()
    
    # Тест 2: Создание анкеты
    print("\n2️⃣ Тест создания анкеты")
    anketa_id = test_anketa_creation()
    
    # Тест 3: Создание исследования (если анкета создана)
    if anketa_id:
        print("\n3️⃣ Тест создания исследования")
        research_id = test_research_creation(anketa_id)
    else:
        print("\n3️⃣ Пропуск теста исследования (анкета не создана)")
    
    # Тест 4: Запросы к базе данных
    print("\n4️⃣ Тест запросов к базе данных")
    test_database_queries()
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    main()
