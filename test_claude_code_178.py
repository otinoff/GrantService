"""
Тестирование Claude Code на удаленном сервере 178.236.17.55:8000
Проверяет работу chat и websearch для задач генерации грантов
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к shared модулям
sys.path.insert(0, str(Path(__file__).parent))

from shared.llm.claude_code_client import ClaudeCodeClient

# API ключ (из config.py)
CLAUDE_CODE_API_KEY = "max_subscription_2025oct"


async def test_health(client: ClaudeCodeClient):
    """Тест 1: Проверка здоровья сервера"""
    print("\n" + "="*70)
    print("TEST 1: Checking /health endpoint")
    print("="*70)

    try:
        result = await client.check_health()
        if result:
            print(f"[OK] Status: healthy")
            print(f"[OK] Server: responding")
            return True
        else:
            print(f"[FAIL] Status: unhealthy")
            return False
    except Exception as e:
        print(f"[FAIL] Health check error: {e}")
        return False


async def test_chat_grant_context(client: ClaudeCodeClient):
    """Тест 2: Chat с контекстом генерации гранта"""
    print("\n" + "="*70)
    print("TEST 2: /chat endpoint - RSF Grant Structure Analysis")
    print("="*70)

    prompt = """You are an expert on RSF grants. Analyze the main requirements for the structure of an application
for the interdisciplinary competition RSF #105 2024.

List the mandatory sections of Part 1 (General Information) and indicate their numbering.
Answer briefly, as a list."""

    print(f"Prompt: {prompt[:150]}...")
    print("\nSending request...")

    try:
        response = await client.chat(
            message=prompt,
            max_tokens=500,
            temperature=0.3
        )

        print("\n[OK] RESPONSE RECEIVED:")
        print("-"*70)
        print(response[:800])
        if len(response) > 800:
            print(f"\n... (total {len(response)} chars)")
        print("-"*70)
        return True

    except Exception as e:
        print(f"\n[FAIL] Chat error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_websearch_grant_research(client: ClaudeCodeClient):
    """Тест 3: WebSearch для исследования по теме гранта"""
    print("\n" + "="*70)
    print("TEST 3: /websearch endpoint - MSC aging publications")
    print("="*70)

    query = "mesenchymal stem cells aging epigenetic changes 2023-2024"

    print(f"Query: {query}")
    print("\nSending websearch request...")

    try:
        # Прямой HTTP запрос к /websearch endpoint
        url = f"{client.base_url}/websearch"
        payload = {
            "query": query,
            "max_results": 5
        }

        async with client.session.post(url, json=payload, timeout=120) as response:
            if response.status == 200:
                data = await response.json()

                print("\n[OK] SEARCH RESULTS:")
                print("-"*70)

                if 'results' in data and data['results']:
                    for i, result in enumerate(data['results'][:3], 1):
                        print(f"\n{i}. {result.get('title', 'N/A')}")
                        print(f"   URL: {result.get('url', 'N/A')}")
                        snippet = result.get('snippet', 'N/A')
                        if len(snippet) > 120:
                            snippet = snippet[:120] + "..."
                        print(f"   Snippet: {snippet}")

                    print(f"\nTotal results: {data.get('total_results', len(data['results']))}")
                    print(f"Cost: ${data.get('cost', 0):.4f}")

                elif 'raw_text' in data:
                    print("\n[WARN] Results returned as text (not JSON):")
                    print(data['raw_text'][:500])
                else:
                    print("\n[WARN] No results found")

                print("-"*70)
                return True

            else:
                error_text = await response.text()
                print(f"\n[FAIL] HTTP {response.status}: {error_text}")
                return False

    except Exception as e:
        print(f"\n[FAIL] Websearch error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Основная функция тестирования"""
    print("\n" + "="*70)
    print("TESTING CLAUDE CODE ON SERVER 178.236.17.55:8000")
    print("="*70)
    print(f"API Key: {CLAUDE_CODE_API_KEY[:20]}...")

    # Инициализация клиента
    client = ClaudeCodeClient(
        api_key=CLAUDE_CODE_API_KEY,
        base_url="http://178.236.17.55:8000"
    )

    results = {
        "health": False,
        "chat": False,
        "websearch": False
    }

    try:
        # Создаем сессию
        await client.__aenter__()

        # Запускаем тесты последовательно
        results["health"] = await test_health(client)

        if results["health"]:
            results["chat"] = await test_chat_grant_context(client)
            results["websearch"] = await test_websearch_grant_research(client)
        else:
            print("\n[WARN] Health check failed - skipping other tests")

    except Exception as e:
        print(f"\n[FAIL] Critical error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Закрываем сессию
        await client.__aexit__(None, None, None)

    # Итоговый отчет
    print("\n" + "="*70)
    print("FINAL REPORT")
    print("="*70)

    total = sum(results.values())

    print(f"\n{'[OK]' if results['health'] else '[FAIL]'} Health Check: {'PASSED' if results['health'] else 'FAILED'}")
    print(f"{'[OK]' if results['chat'] else '[FAIL]'} Chat (Grant Analysis): {'PASSED' if results['chat'] else 'FAILED'}")
    print(f"{'[OK]' if results['websearch'] else '[FAIL]'} WebSearch (Research): {'PASSED' if results['websearch'] else 'FAILED'}")

    print(f"\nSuccess: {total}/3 tests")

    if total == 3:
        print("\n[OK] ALL TESTS PASSED - Claude Code on 178 ready for grant work!")
    elif total > 0:
        print(f"\n[WARN] PARTIAL SUCCESS - {total} out of 3 tests working")
    else:
        print("\n[FAIL] TESTS FAILED - server diagnostics needed")

    print("="*70 + "\n")

    return total == 3


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
