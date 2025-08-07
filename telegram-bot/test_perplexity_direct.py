#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Прямое тестирование Perplexity API
"""

import requests
import json
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Конфигурация
API_KEY = "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"
BASE_URL = "https://api.perplexity.ai"

def test_simple_request():
    """Простой тест запроса"""
    print("🧪 Простой тест Perplexity API")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Простой запрос
    payload = {
        "model": "sonar",  # Используем простую модель
        "messages": [
            {
                "role": "user",
                "content": "Привет! Как дела?"
            }
        ],
        "max_tokens": 100
    }
    
    print(f"📤 Отправляем запрос к {BASE_URL}/chat/completions")
    print(f"🔑 API Key: {API_KEY[:10]}...")
    print(f"📝 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30  # Уменьшаем timeout
        )
        end_time = time.time()
        
        print(f"⏱️ Время ответа: {end_time - start_time:.2f} секунд")
        print(f"📊 Статус: {response.status_code}")
        print(f"📋 Заголовки: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Успешный ответ!")
            print(f"📄 Ответ: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"📄 Текст ошибки: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Таймаут запроса (30 секунд)")
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Ошибка подключения: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

def test_models():
    """Тест доступных моделей"""
    print("\n🔍 Тест доступных моделей")
    print("=" * 50)
    
    models = [
        "sonar",
        "sonar-pro", 
        "sonar-deep-research",
        "sonar-reasoning",
        "sonar-reasoning-pro"
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
            "max_tokens": 50
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
            else:
                print(f"❌ {model} - ошибка {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ {model} - исключение: {e}")

def test_connection():
    """Тест подключения"""
    print("\n🔗 Тест подключения")
    print("=" * 50)
    
    try:
        # Простой GET запрос
        response = requests.get(BASE_URL, timeout=10)
        print(f"📊 Статус: {response.status_code}")
        print(f"📋 Заголовки: {dict(response.headers)}")
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    test_connection()
    test_simple_request()
    test_models() 