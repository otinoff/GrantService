#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Claude Code API simple request
"""
import sys
import os
import asyncio
from pathlib import Path

# Setup paths
base_dir = Path(__file__).parent
sys.path.insert(0, str(base_dir / 'shared'))

print("=" * 80)
print("Testing Claude Code API")
print("=" * 80)

# Get API settings from env
API_KEY = "1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732"
BASE_URL = "http://178.236.17.55:8000"

print(f"\n1. API URL: {BASE_URL}")
print(f"2. API Key: {API_KEY[:20]}...{API_KEY[-10:]}")

# Import ClaudeCodeClient
try:
    from llm.claude_code_client import ClaudeCodeClient
    print("\n3. ClaudeCodeClient imported OK")
except ImportError as e:
    print(f"\n3. ERROR: Cannot import ClaudeCodeClient: {e}")
    sys.exit(1)

# Test simple chat
async def test_chat():
    print("\n4. Creating client...")

    async with ClaudeCodeClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        default_model="sonnet",
        default_temperature=0.3
    ) as client:
        print("   Client created OK")

        print("\n5. Sending test message...")
        try:
            response = await client.chat(
                message="Hello, how are you?",
                max_tokens=100
            )

            print(f"\n   SUCCESS!")
            print(f"   Response length: {len(response)} chars")
            print(f"   Response preview: {response[:200]}...")

            return True

        except Exception as e:
            print(f"\n   ERROR: {e}")
            return False

# Run test
print("\n" + "=" * 80)
result = asyncio.run(test_chat())

print("\n" + "=" * 80)
if result:
    print("TEST PASSED: Claude API works!")
else:
    print("TEST FAILED: Claude API error")
print("=" * 80)
