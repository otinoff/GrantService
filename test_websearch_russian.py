#!/usr/bin/env python3
"""Test WebSearch endpoint with Russian query"""

import requests
import json

url = "http://178.236.17.55:8000/websearch"

payload = {
    "query": "Президентские гранты 2025 культура требования",
    "max_results": 2
}

print("Sending request...")
print(f"Query: {payload['query']}")

try:
    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()

    data = response.json()

    print("\n" + "="*80)
    print("WEBSEARCH RESPONSE (RUSSIAN QUERY)")
    print("="*80)
    print(f"\nQuery: {data['query']}")
    print(f"Content length: {len(data.get('content', ''))} chars")
    print(f"Total results: {data['total_results']}")
    print(f"Sources: {', '.join(data['sources'])}")
    print(f"Cost: ${data['cost']:.4f}")
    print(f"Search time: {data['search_time']}s")

    if data.get('content'):
        print(f"\nContent preview (first 500 chars):")
        print("-" * 80)
        print(data['content'][:500])
        print("-" * 80)

    print("\n✅ TEST PASSED: Russian query works!")

except requests.exceptions.RequestException as e:
    print(f"\n❌ TEST FAILED: {e}")
    exit(1)
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
    exit(1)
