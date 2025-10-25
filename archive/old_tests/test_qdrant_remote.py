#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test connection to remote Qdrant on production server
"""
import requests
import json

QDRANT_HOST = "5.35.88.251"
QDRANT_PORT = 6333

print("=" * 80)
print(f"TESTING QDRANT CONNECTION: {QDRANT_HOST}:{QDRANT_PORT}")
print("=" * 80)

try:
    # 1. Check Qdrant is running
    print(f"\n1. Checking Qdrant health...")
    response = requests.get(f"http://{QDRANT_HOST}:{QDRANT_PORT}/", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")

    # 2. List collections
    print(f"\n2. Listing collections...")
    response = requests.get(f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections", timeout=5)
    if response.status_code == 200:
        data = response.json()
        collections = data.get('result', {}).get('collections', [])
        print(f"   Found {len(collections)} collection(s):")
        for coll in collections:
            print(f"     - {coll['name']}")
    else:
        print(f"   Error: {response.status_code}")

    # 3. Check knowledge_sections collection
    print(f"\n3. Checking 'knowledge_sections' collection...")
    response = requests.get(
        f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/knowledge_sections",
        timeout=5
    )
    if response.status_code == 200:
        data = response.json()
        result = data.get('result', {})
        print(f"   Points count: {result.get('points_count', 0)}")
        print(f"   Vectors count: {result.get('vectors_count', 0)}")
        print(f"   Status: {result.get('status', 'unknown')}")
    else:
        print(f"   Collection not found or error: {response.status_code}")

    print("\n" + "=" * 80)
    print("SUCCESS: Remote Qdrant is accessible!")
    print("=" * 80)
    print("\nThis means:")
    print("  - We can use production Qdrant from local development")
    print("  - No need for local Docker/Qdrant")
    print("  - Single source of truth for knowledge base")

except requests.exceptions.ConnectionError as e:
    print(f"\nERROR: Cannot connect to Qdrant")
    print(f"  Host: {QDRANT_HOST}:{QDRANT_PORT}")
    print(f"  Error: {e}")
    print("\nPossible reasons:")
    print("  - Qdrant not running on server")
    print("  - Firewall blocking port 6333")
    print("  - Wrong host/port")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
