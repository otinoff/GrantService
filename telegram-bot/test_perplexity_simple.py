#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест Perplexity API для проверки ключа
"""

import requests
import json

# API ключ из истории
API_KEY = "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"
BASE_URL = "https://api.perplexity.ai"

def test_simple_query():
    """Простой тест запроса"""
    print("🧪 Простой тест Perplexity API")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Очень простой запрос
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "user",
                "content": "Привет! Как дела?"
            }
        ],
        "max_tokens": 50
    }
    
    print(f"📤 Отправляем запрос к {BASE_URL}/chat/completions")
    print(f"🔑 API Key: {API_KEY[:10]}...")
    print(f"📝 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Статус: {response.status_code}")
        print(f"📋 Заголовки: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Успешный ответ!")
            print(f"📄 Ответ: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"📄 Текст ошибки: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_different_models():
    """Тест разных моделей"""
    print("\n🔍 Тест разных моделей")
    print("=" * 50)
    
    models = [
        "sonar",
        "sonar-pro", 
        "llama-3.1-sonar-small-128k-online",
        "llama-3.1-sonar-small-128k",
        "llama-3.1-sonar-medium-128k-online",
        "llama-3.1-sonar-medium-128k"
    ]
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    for model in models:
        print(f"\n🧪 Тестируем модель: {model}")
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": "Скажи привет"
                }
            ],
            "max_tokens": 20
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"✅ {model} - работает")
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    print(f"   Ответ: {content}")
                return True
            else:
                print(f"❌ {model} - ошибка {response.status_code}")
                if response.status_code == 401:
                    print(f"   Ошибка авторизации - ключ недействителен")
                    return False
                elif response.status_code == 400:
                    print(f"   Ошибка модели - {response.text}")
                else:
                    print(f"   {response.text}")
                
        except Exception as e:
            print(f"❌ {model} - исключение: {e}")
    
    return False

def check_api_status():
    """Проверка статуса API"""
    print("\n🔗 Проверка статуса API")
    print("=" * 50)
    
    try:
        # Простой GET запрос
        response = requests.get(BASE_URL, timeout=10)
        print(f"📊 Статус: {response.status_code}")
        print(f"📋 Заголовки: {dict(response.headers)}")
        
        if response.status_code == 404:
            print("ℹ️ API доступен, но корневой путь не существует (это нормально)")
            return True
        else:
            print(f"📄 Ответ: {response.text}")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Тестирование Perplexity API")
    print("=" * 60)
    
    # Проверяем статус API
    if not check_api_status():
        print("❌ API недоступен")
        exit(1)
    
    # Тестируем простой запрос
    if test_simple_query():
        print("\n🎉 API работает!")
    else:
        print("\n🔍 Пробуем разные модели...")
        if test_different_models():
            print("\n🎉 Найдена рабочая модель!")
        else:
            print("\n❌ API не работает с текущим ключом")
            print("\n💡 Возможные причины:")
            print("1. Ключ истек")
            print("2. Изменился формат авторизации")
            print("3. Ограничения по IP/региону")
            print("4. Нужен новый ключ") 