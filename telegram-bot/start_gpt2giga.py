#!/usr/bin/env python3
"""
Скрипт для запуска gpt2giga прокси
"""
import os
import subprocess
import time
import requests
from gpt2giga import GigaChatProxy

def start_gpt2giga_proxy():
    """Запуск gpt2giga прокси"""
    print("🚀 Запуск gpt2giga прокси...")
    
    # Получаем API ключ
    api_key = os.getenv('GIGACHAT_API_KEY')
    if not api_key:
        print("❌ Ошибка: GIGACHAT_API_KEY не установлен")
        return False
    
    try:
        # Создаем и запускаем прокси
        proxy = GigaChatProxy(
            gigachat_credentials=api_key,
            host="localhost",
            port=8000
        )
        
        print("✅ gpt2giga прокси запущен на http://localhost:8000")
        print("📝 Теперь CrewAI будет использовать GigaChat через OpenAI-совместимый интерфейс")
        
        # Запускаем прокси в отдельном потоке
        proxy.start()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка запуска прокси: {e}")
        return False

def test_proxy():
    """Тест прокси"""
    try:
        response = requests.get("http://localhost:8000/v1/models")
        if response.status_code == 200:
            print("✅ Прокси работает корректно")
            return True
        else:
            print(f"❌ Прокси не отвечает: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка тестирования прокси: {e}")
        return False

if __name__ == "__main__":
    if start_gpt2giga_proxy():
        print("\n🔄 Ожидание запуска прокси...")
        time.sleep(3)
        
        if test_proxy():
            print("\n🎉 gpt2giga прокси готов к работе!")
            print("💡 Теперь можно запускать тест агентов")
        else:
            print("\n⚠️ Прокси запущен, но тест не прошел")
    else:
        print("\n❌ Не удалось запустить прокси") 