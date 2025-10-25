#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick GigaChat API Status Test
Tests if API is available and check rate limits
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio
from datetime import datetime
from shared.llm_providers.gigachat_provider import GigaChatProvider


async def test_gigachat_status():
    """Test GigaChat API current status"""

    print("=" * 80)
    print("GIGACHAT API STATUS TEST")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Initialize provider
        print("[1/3] Initializing GigaChat provider...")
        provider = GigaChatProvider()
        print("✅ Provider initialized")
        print()

        # Test 1: Simple request
        print("[2/3] Testing simple API request...")
        print("Sending: 'Привет! Это тест.'")

        start_time = datetime.now()
        response = await provider.generate(
            prompt="Привет! Это тест.",
            max_tokens=50,
            temperature=0.7
        )
        end_time = datetime.now()

        processing_time = (end_time - start_time).total_seconds()

        print(f"✅ Response received in {processing_time:.2f}s")
        print(f"Response: {response[:200]}...")
        print()

        # Test 2: Check if we can make another request
        print("[3/3] Testing second request (checking rate limit)...")

        start_time = datetime.now()
        response2 = await provider.generate(
            prompt="Скажи 'OK'",
            max_tokens=10,
            temperature=0.7
        )
        end_time = datetime.now()

        processing_time2 = (end_time - start_time).total_seconds()

        print(f"✅ Second response received in {processing_time2:.2f}s")
        print(f"Response: {response2}")
        print()

        # Summary
        print("=" * 80)
        print("API STATUS: ✅ WORKING")
        print("=" * 80)
        print(f"Request 1: {processing_time:.2f}s")
        print(f"Request 2: {processing_time2:.2f}s")
        print("No rate limit errors detected")
        print()
        print("Conclusion: API is available, quota refreshed")
        print("=" * 80)

        return True

    except Exception as e:
        print("=" * 80)
        print("API STATUS: ❌ ERROR")
        print("=" * 80)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()

        # Check if it's a rate limit error
        if "429" in str(e) or "Too Many Requests" in str(e):
            print("⚠️ RATE LIMIT ERROR")
            print("Причина: Превышен лимит запросов")
            print()
            print("Возможные решения:")
            print("1. Подождать 24 часа (сброс daily quota)")
            print("2. Проверить concurrent streams (max 1 для физ. лиц)")
            print("3. Добавить throttling между запросами")
        elif "quota" in str(e).lower():
            print("⚠️ QUOTA EXCEEDED")
            print("Причина: Превышена квота токенов")
            print()
            print("Решение: Подождать до следующего периода биллинга")
        else:
            print("⚠️ UNKNOWN ERROR")
            print("Рекомендация: Проверить логи и credentials")

        print("=" * 80)

        return False


if __name__ == "__main__":
    success = asyncio.run(test_gigachat_status())
    sys.exit(0 if success else 1)
