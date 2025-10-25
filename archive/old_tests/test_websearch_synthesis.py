#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест восстановленного синтеза контента для WebSearch
Проверяем что поле 'content' теперь присутствует
"""

import asyncio
import sys
import os

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Добавляем пути
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared'))

from shared.llm.claude_code_websearch_client import ClaudeCodeWebSearchClient

async def test_content_synthesis():
    """Тест синтеза контента"""

    print("=" * 80)
    print("ТЕСТ ВОССТАНОВЛЕНИЯ CONTENT SYNTHESIS")
    print("=" * 80)

    async with ClaudeCodeWebSearchClient(
        base_url="http://178.236.17.55:8000",
        timeout=120
    ) as client:

        # Простой тестовый запрос
        query = "Найди информацию о стрельбе из лука как виде спорта в России"

        print(f"\n🔍 Запрос: {query}")
        print(f"⏱️  Ожидание ответа (до 120 секунд)...\n")

        result = await client.websearch(
            query=query,
            allowed_domains=['rosstat.gov.ru', 'gov.ru', 'minsport.gov.ru'],
            max_results=5
        )

        print("=" * 80)
        print("РЕЗУЛЬТАТ")
        print("=" * 80)

        # Проверка статуса
        status = result.get('status', 'unknown')
        print(f"\n✓ Status: {status}")

        # Проверка results
        results_count = result.get('total_results', 0)
        print(f"✓ Results: {results_count}")

        # Проверка sources
        sources = result.get('sources', [])
        print(f"✓ Sources: {len(sources)}")
        for i, source in enumerate(sources, 1):
            print(f"  {i}. {source}")

        # КРИТИЧЕСКАЯ ПРОВЕРКА: наличие content
        content = result.get('content', '')

        print(f"\n{'=' * 80}")
        print("🎯 КРИТИЧЕСКАЯ ПРОВЕРКА: CONTENT")
        print("=" * 80)

        if content:
            print(f"✅ CONTENT ПРИСУТСТВУЕТ!")
            print(f"✅ Длина: {len(content)} символов")
            print(f"\n📄 Первые 500 символов:\n")
            print("-" * 80)
            print(content[:500])
            print("-" * 80)

            if len(content) >= 500:
                print(f"\n✅ SUCCESS: Content synthesis восстановлен!")
                print(f"✅ Отчёты теперь будут полными как в EKATERINA")
                return True
            else:
                print(f"\n⚠️  WARNING: Content слишком короткий ({len(content)} символов)")
                print(f"⚠️  Ожидалось: 500-1000 слов")
                return False
        else:
            print(f"❌ FAIL: CONTENT ОТСУТСТВУЕТ")
            print(f"❌ Поле 'content' пустое или не существует")
            print(f"\n📋 Доступные поля:")
            for key in result.keys():
                print(f"  - {key}: {type(result[key]).__name__}")
            return False

        # Дополнительная информация
        print(f"\n📊 Дополнительная информация:")
        print(f"  - Search time: {result.get('search_time', 0):.2f}s")
        if 'cost' in result:
            print(f"  - Cost: ${result.get('cost', 0):.4f}")
        if 'usage' in result:
            usage = result.get('usage', {})
            print(f"  - Tokens: {usage.get('total_tokens', 0)}")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ТЕСТИРОВАНИЕ ВОССТАНОВЛЕННОГО CONTENT SYNTHESIS")
    print("=" * 80)
    print("\nЦель: Проверить что wrapper server теперь возвращает поле 'content'")
    print("      с полным синтезированным ответом как в EKATERINA\n")

    try:
        success = asyncio.run(test_content_synthesis())

        print("\n" + "=" * 80)
        if success:
            print("✅ ТЕСТ ПРОЙДЕН: Content synthesis работает!")
            print("=" * 80)
            sys.exit(0)
        else:
            print("⚠️  ТЕСТ НЕ ПРОЙДЕН: Content synthesis требует доработки")
            print("=" * 80)
            sys.exit(1)

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ ОШИБКА: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(2)
