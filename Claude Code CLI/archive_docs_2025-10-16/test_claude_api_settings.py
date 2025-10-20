#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Claude Code API Settings
Quick verification that API endpoints are working correctly
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
load_dotenv("config/.env.example")

def test_claude_code_api():
    """Test Claude Code API health and models endpoints"""

    api_key = os.getenv('CLAUDE_CODE_API_KEY', '1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732')
    base_url = os.getenv('CLAUDE_CODE_BASE_URL', 'http://178.236.17.55:8000')

    print("=" * 60)
    print("Claude Code API Settings Test")
    print("=" * 60)
    print(f"API URL: {base_url}")
    print(f"API Key: {api_key[:8]}...{api_key[-8:]}")
    print()

    # Test 1: Health check
    print("1. Testing /health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=3)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📊 Data: {health_data}")
        else:
            print(f"   ❌ Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()

    # Test 2: Models check
    print("2. Testing /models endpoint...")
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{base_url}/models", headers=headers, timeout=3)
        if response.status_code == 200:
            models_data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📊 Available models:")

            if "models" in models_data:
                for model in models_data["models"]:
                    print(f"      - {model['name']} ({model['id']})")
                    print(f"        {model.get('description', 'No description')}")
            else:
                print(f"      {models_data}")
        else:
            print(f"   ❌ Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_claude_code_api()
