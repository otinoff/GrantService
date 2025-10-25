#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест WebSearch endpoint после фикса

Проверяет что /websearch endpoint работает корректно
"""

import requests
import json

API_URL = "http://178.236.17.55:8000"

def test_websearch_basic():
    """Базовый тест WebSearch"""
    print("1. Базовый WebSearch тест (английский запрос)...")

    response = requests.post(
        f"{API_URL}/websearch",
        json={
            "query": "Find information about Russian presidential grants for culture 2025",
            "max_results": 3
        },
        timeout=120
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Results: {data.get('total_results', 0)}")
        print(f"   Sources: {data.get('sources', [])}")
        print(f"   Cost: ${data.get('cost', 0):.4f}")
        return True
    else:
        print(f"   [ERROR] Error: {response.text}")
        return False


def test_websearch_russian():
    """Тест с русским запросом"""
    print("\n2. WebSearch с русским запросом...")

    response = requests.post(
        f"{API_URL}/websearch",
        json={
            "query": "Найди данные Росстат о доступности спортивных секций для детей в России 2024",
            "max_results": 5
        },
        timeout=120
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Results: {data.get('total_results', 0)}")
        print(f"   Sources: {data.get('sources', [])}")

        # Показать первый результат
        if data.get('results'):
            first = data['results'][0]
            print(f"   First result:")
            print(f"      Title: {first.get('title', 'N/A')[:80]}")
            print(f"      URL: {first.get('url', 'N/A')}")

        return True
    else:
        print(f"   [ERROR] Error: {response.text}")
        return False


def test_websearch_with_domains():
    """Тест с фильтром доменов"""
    print("\n3. WebSearch с фильтром доменов...")

    response = requests.post(
        f"{API_URL}/websearch",
        json={
            "query": "Статистика детского спорта России",
            "max_results": 5,
            "allowed_domains": ["rosstat.gov.ru", "gov.ru", "fedstat.ru"]
        },
        timeout=120
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Results: {data.get('total_results', 0)}")
        print(f"   Sources: {data.get('sources', [])}")

        # Проверить что все результаты из разрешенных доменов
        allowed = ["rosstat.gov.ru", "gov.ru", "fedstat.ru"]
        for result in data.get('results', []):
            source = result.get('source', '')
            if source and not any(domain in source for domain in allowed):
                print(f"   [WARN] Warning: Result from non-allowed domain: {source}")

        return True
    else:
        print(f"   [ERROR] Error: {response.text}")
        return False


def test_health():
    """Проверка здоровья API"""
    print("\n0. Health check...")

    response = requests.get(f"{API_URL}/health", timeout=5)

    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Healthy: {data}")
        return True
    else:
        print(f"   [ERROR] Unhealthy: {response.status_code}")
        return False


if __name__ == "__main__":
    print("=" * 80)
    print("ТЕСТ WEBSEARCH ENDPOINT (ПОСЛЕ ФИКСА)")
    print("=" * 80)

    # Запускаем тесты
    results = []

    results.append(("Health", test_health()))
    results.append(("Basic WebSearch", test_websearch_basic()))
    results.append(("Russian Query", test_websearch_russian()))
    results.append(("Domain Filter", test_websearch_with_domains()))

    # Итоги
    print("\n" + "=" * 80)
    print("ИТОГИ ТЕСТОВ")
    print("=" * 80)

    for name, passed in results:
        status = "[OK] PASSED" if passed else "[ERROR] FAILED"
        print(f"{status}: {name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nВсего: {total_passed}/{len(results)} тестов прошли")

    if total_passed == len(results):
        print("\n[SUCCESS] ВСЕ ТЕСТЫ ПРОШЛИ! WebSearch endpoint работает корректно!")
    else:
        print("\n[WARNING] Некоторые тесты не прошли. Требуется дополнительная отладка.")
