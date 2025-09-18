#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест UnifiedLLMClient для GrantService
Проверяет работу с GigaChat, Perplexity и Ollama
"""

import asyncio
import sys
import os

# Добавляем пути к модулям
sys.path.append('/var/GrantService/shared')

try:
    from llm.unified_llm_client import UnifiedLLMClient
    from llm.config import AGENT_CONFIGS
    print("✅ UnifiedLLMClient импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта UnifiedLLMClient: {e}")
    sys.exit(1)

async def test_gigachat():
    """Тест GigaChat"""
    print("\n🚀 Тестируем GigaChat...")
    
    try:
        async with UnifiedLLMClient(
            provider="gigachat",
            model="GigaChat",
            temperature=0.7
        ) as client:
            
            # Проверяем подключение
            is_connected = await client.check_connection_async()
            print(f"📡 Подключение к GigaChat: {'✅' if is_connected else '❌'}")
            
            if is_connected:
                # Тестируем генерацию
                prompt = "Привет! Как дела?"
                result = await client.generate_text(prompt, max_tokens=100)
                print(f"🤖 Ответ GigaChat: {result[:200]}...")
                return True
            else:
                print("❌ GigaChat недоступен")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка GigaChat: {e}")
        return False

async def test_perplexity():
    """Тест Perplexity"""
    print("\n🚀 Тестируем Perplexity...")
    
    try:
        async with UnifiedLLMClient(
            provider="perplexity",
            model="sonar",
            temperature=0.3
        ) as client:
            
            # Проверяем подключение
            is_connected = await client.check_connection_async()
            print(f"📡 Подключение к Perplexity: {'✅' if is_connected else '❌'}")
            
            if is_connected:
                # Тестируем генерацию
                prompt = "Что такое грант?"
                result = await client.generate_text(prompt, max_tokens=150)
                print(f"🤖 Ответ Perplexity: {result[:200]}...")
                return True
            else:
                print("❌ Perplexity недоступен")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка Perplexity: {e}")
        return False

async def test_ollama():
    """Тест Ollama (если доступен)"""
    print("\n🚀 Тестируем Ollama...")
    
    try:
        async with UnifiedLLMClient(
            provider="ollama",
            model="qwen2.5:3b",
            temperature=0.7
        ) as client:
            
            # Проверяем подключение
            is_connected = await client.check_connection_async()
            print(f"📡 Подключение к Ollama: {'✅' if is_connected else '❌'}")
            
            if is_connected:
                # Тестируем генерацию
                prompt = "Привет! Как дела?"
                result = await client.generate_text(prompt, max_tokens=100)
                print(f"🤖 Ответ Ollama: {result[:200]}...")
                return True
            else:
                print("❌ Ollama недоступен (возможно, не запущен)")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка Ollama: {e}")
        return False

async def test_agent_configs():
    """Тест конфигураций агентов"""
    print("\n🔧 Тестируем конфигурации агентов...")
    
    for agent_type, config in AGENT_CONFIGS.items():
        print(f"📋 {agent_type}: {config['provider']} - {config['model']}")
    
    return True

async def test_grant_service_prompt():
    """Тест промпта для грантовой заявки"""
    print("\n📝 Тестируем промпт для грантовой заявки...")
    
    try:
        async with UnifiedLLMClient(
            provider="gigachat",
            model="GigaChat",
            temperature=0.7
        ) as client:
            
            prompt = """
            Проанализируй следующую грантовую заявку и дай рекомендации по улучшению:
            
            Название проекта: "Цифровизация сельской библиотеки"
            Описание: Проект направлен на создание современного информационного центра в сельской библиотеке с доступом к электронным ресурсам и обучением населения цифровым навыкам.
            Бюджет: 500,000 рублей
            Срок реализации: 12 месяцев
            
            Дай краткий анализ и 3-5 рекомендаций по улучшению заявки.
            """
            
            result = await client.generate_text(prompt, max_tokens=500)
            print(f"🤖 Анализ грантовой заявки:\n{result}")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка анализа заявки: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ UNIFIED LLM CLIENT ДЛЯ GRANTSERVICE")
    print("=" * 60)
    
    # Тестируем конфигурации
    await test_agent_configs()
    
    # Тестируем провайдеры
    results = {}
    results['gigachat'] = await test_gigachat()
    results['perplexity'] = await test_perplexity()
    results['ollama'] = await test_ollama()
    
    # Тестируем промпт для грантовой заявки
    results['grant_prompt'] = await test_grant_service_prompt()
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ РАБОТАЕТ" if result else "❌ НЕ РАБОТАЕТ"
        print(f"{test_name:15} : {status}")
    
    working_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 Результат: {working_count}/{total_count} тестов прошли успешно")
    
    if working_count >= 2:  # GigaChat + хотя бы один другой
        print("✅ UnifiedLLMClient готов к использованию в GrantService!")
    else:
        print("⚠️ UnifiedLLMClient требует доработки")

if __name__ == "__main__":
    asyncio.run(main())
