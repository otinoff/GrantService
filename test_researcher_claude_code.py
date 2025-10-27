#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test: Researcher Agent with Claude Code WebSearch
Tests if Claude Code WebSearch works in ResearcherAgent
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(__file__))

from shared.llm.websearch_router import WebSearchRouter


async def test_claude_code_websearch():
    """Test Claude Code WebSearch directly"""

    print("=" * 80)
    print("QUICK TEST: Claude Code WebSearch")
    print("=" * 80)
    print()

    # Mock DB
    class MockDB:
        pass

    db = MockDB()

    try:
        print("[1/3] Initializing WebSearchRouter (Claude Code ONLY)...")
        async with WebSearchRouter(db) as router:
            print(f"[OK] Provider: {router.get_current_provider()}")
            print()

            # Health check
            print("[2/3] Running health check...")
            healthy = await router.check_health()
            if healthy:
                print("[OK] Claude Code WebSearch service is HEALTHY")
            else:
                print("[FAIL] Claude Code WebSearch service is DOWN")
                return False
            print()

            # Test search
            print("[3/3] Testing WebSearch query...")
            query = "статистика инвалидов России 2024"
            print(f"Query: {query}")
            print()

            result = await router.websearch(
                query=query,
                allowed_domains=['gov.ru', 'rosstat.gov.ru'],
                max_results=3
            )

            # Check results
            status = result.get('status')
            provider = result.get('provider')
            total_results = result.get('total_results', 0)
            sources = result.get('sources', [])

            print(f"[RESULT] Status: {status}")
            print(f"[RESULT] Provider: {provider}")
            print(f"[RESULT] Total results: {total_results}")
            print(f"[RESULT] Sources found: {len(sources)}")

            if status == 'success' and total_results > 0:
                print()
                print("[OK] Claude Code WebSearch WORKS!")
                print()
                print("Sample results:")
                for i, res in enumerate(result['results'][:2], 1):
                    print(f"\n  {i}. {res.get('title', 'N/A')[:60]}...")
                    print(f"     URL: {res.get('url', 'N/A')}")
                    print(f"     Source: {res.get('source', 'N/A')}")

                print()
                print("=" * 80)
                print("[SUCCESS] Claude Code WebSearch is WORKING!")
                print("=" * 80)
                return True
            else:
                print()
                print("[FAIL] No results returned")
                print("=" * 80)
                print("[FAILED] Claude Code WebSearch returned no results")
                print("=" * 80)
                return False

    except Exception as e:
        print()
        print("=" * 80)
        print("[ERROR] Claude Code WebSearch FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()

        import traceback
        traceback.print_exc()
        print()
        print("Possible issues:")
        print("  1. Wrapper server down (178.236.17.55:8000)")
        print("  2. OAuth token expired")
        print("  3. Network connectivity issue")
        print()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_claude_code_websearch())
    sys.exit(0 if success else 1)
