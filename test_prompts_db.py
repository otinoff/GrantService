#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование работы с промптами агентов в БД
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

from data.database import db

def test_prompts_database():
    """Тестирование функций работы с промптами"""
    print("🧪 Тестирование БД промптов агентов")
    print("=" * 50)
    
    # Тест 1: Получение промптов для каждого агента
    agents = ['researcher', 'writer', 'auditor']
    
    for agent in agents:
        print(f"\n📋 Промпты для агента: {agent}")
        prompts = db.get_agent_prompts(agent)
        
        if prompts:
            for prompt in prompts:
                print(f"  • {prompt['prompt_name']} (ID: {prompt['id']})")
                print(f"    Тип: {prompt['prompt_type']}")
                print(f"    Порядок: {prompt['order_num']}")
                print(f"    Активен: {'✅' if prompt['is_active'] else '❌'}")
                print(f"    Модель: {prompt['model_name']}")
                print(f"    Temperature: {prompt['temperature']}")
                print(f"    Max tokens: {prompt['max_tokens']}")
                print(f"    Содержимое: {prompt['prompt_content'][:100]}...")
                print()
        else:
            print(f"  ❌ Промпты для агента {agent} не найдены")
    
    # Тест 2: Создание нового промпта
    print("\n➕ Тест создания нового промпта")
    new_prompt_data = {
        'agent_type': 'researcher',
        'prompt_name': 'Тестовый промпт',
        'prompt_content': 'Это тестовый промпт для проверки функциональности БД',
        'prompt_type': 'task',
        'order_num': 3,
        'temperature': 0.8,
        'max_tokens': 1500,
        'model_name': 'GigaChat-Max',
        'is_active': True
    }
    
    prompt_id = db.create_agent_prompt(new_prompt_data)
    if prompt_id:
        print(f"  ✅ Создан промпт с ID: {prompt_id}")
        
        # Тест 3: Получение промпта по ID
        print(f"\n🔍 Тест получения промпта по ID: {prompt_id}")
        prompt = db.get_prompt_by_id(prompt_id)
        if prompt:
            print(f"  ✅ Найден промпт: {prompt['prompt_name']}")
            
            # Тест 4: Обновление промпта
            print(f"\n✏️ Тест обновления промпта ID: {prompt_id}")
            update_data = {
                'agent_type': 'researcher',
                'prompt_name': 'Обновленный тестовый промпт',
                'prompt_content': 'Это обновленный тестовый промпт',
                'prompt_type': 'system',
                'order_num': 4,
                'temperature': 0.9,
                'max_tokens': 2000,
                'model_name': 'GigaChat-Pro',
                'is_active': True
            }
            
            if db.update_agent_prompt(prompt_id, update_data):
                print(f"  ✅ Промпт {prompt_id} обновлен")
                
                # Проверяем обновление
                updated_prompt = db.get_prompt_by_id(prompt_id)
                if updated_prompt:
                    print(f"  📝 Новое название: {updated_prompt['prompt_name']}")
                    print(f"  📝 Новый тип: {updated_prompt['prompt_type']}")
                    print(f"  📝 Новый порядок: {updated_prompt['order_num']}")
            
            # Тест 5: Удаление промпта
            print(f"\n🗑️ Тест удаления промпта ID: {prompt_id}")
            if db.delete_agent_prompt(prompt_id):
                print(f"  ✅ Промпт {prompt_id} удален")
                
                # Проверяем удаление
                deleted_prompt = db.get_prompt_by_id(prompt_id)
                if not deleted_prompt:
                    print(f"  ✅ Промпт {prompt_id} действительно удален из БД")
                else:
                    print(f"  ❌ Промпт {prompt_id} все еще существует")
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    test_prompts_database() 