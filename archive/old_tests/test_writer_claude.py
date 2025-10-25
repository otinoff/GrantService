#!/usr/bin/env python3
"""
Тест Writer Agent с Claude Opus 4
Генерирует короткий раздел гранта для проверки интеграции
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.llm.unified_llm_client import UnifiedLLMClient
from shared.llm.config import AGENT_CONFIGS


async def test_writer_agent():
    """Тест генерации текста через Writer Agent с Claude Opus"""

    print("=" * 80)
    print("🧪 Тест Writer Agent с Claude Opus 4")
    print("=" * 80)

    # Получаем конфигурацию Writer Agent
    writer_config = AGENT_CONFIGS["writer"]
    print(f"\n📋 Конфигурация Writer Agent:")
    print(f"   Provider: {writer_config['provider']}")
    print(f"   Model: {writer_config['model']}")
    print(f"   Temperature: {writer_config['temperature']}")
    print(f"   Max Tokens: {writer_config['max_tokens']}")

    # Создаем LLM клиент
    print(f"\n🔧 Инициализация UnifiedLLMClient...")

    async with UnifiedLLMClient(
        provider=writer_config["provider"],
        model=writer_config["model"],
        temperature=writer_config["temperature"]
    ) as client:

        # Тестовый промпт - генерация раздела "Актуальность"
        prompt = """You are a professional grant writer. Write a brief "Relevance" section for a grant application about youth mental health support program.

Requirements:
- Write in formal academic English
- 2-3 paragraphs
- Focus on current challenges in youth mental health
- Explain why this program is timely and important

Return ONLY the text of the "Relevance" section."""

        print(f"\n📝 Промпт готов ({len(prompt)} символов)")
        print("\n⏳ Генерация текста через Claude Opus 4...")

        start_time = datetime.now()

        try:
            # Генерируем текст
            result = await client.generate_async(
                prompt=prompt,
                max_tokens=500
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print(f"\n✅ Генерация завершена за {duration:.2f} сек")
            print("\n" + "=" * 80)
            print("📄 РЕЗУЛЬТАТ:")
            print("=" * 80)
            print(result)
            print("=" * 80)

            # Статистика
            print(f"\n📊 Статистика:")
            print(f"   Длина ответа: {len(result)} символов")
            print(f"   Время генерации: {duration:.2f} сек")
            print(f"   Скорость: {len(result)/duration:.0f} символов/сек")

            # Debug log
            debug_log = client.get_debug_log()
            if debug_log:
                print(f"\n🔍 Debug Log:")
                for log_entry in debug_log:
                    print(f"   {log_entry}")

            return True

        except Exception as e:
            print(f"\n❌ ОШИБКА: {e}")
            print(f"\n🔍 Debug Log:")
            for log_entry in client.get_debug_log():
                print(f"   {log_entry}")
            return False


async def main():
    """Главная функция"""
    success = await test_writer_agent()

    print("\n" + "=" * 80)
    if success:
        print("✅ ТЕСТ ПРОЙДЕН")
        print("\nWriter Agent успешно использует Claude Opus 4 для генерации грантов!")
        sys.exit(0)
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН")
        print("\nНеобходимо проверить:")
        print("1. Доступность Claude Code API на 178.236.17.55:8000")
        print("2. Валидность API ключа")
        print("3. Логи telegram-bot сервиса")
        sys.exit(1)
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
