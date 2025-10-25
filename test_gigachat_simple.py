#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple GigaChat API Test - Direct API Call
"""

import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import uuid
from datetime import datetime

def get_gigachat_token():
    """Get GigaChat API token"""

    # Try to load from .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

    auth_key = os.getenv('GIGACHAT_API_KEY')
    if not auth_key:
        print("[ERROR] GIGACHAT_API_KEY not found in environment")
        print("Please set GIGACHAT_API_KEY in .env file")
        return None

    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {auth_key}'
    }
    data = {'scope': 'GIGACHAT_API_PERS'}

    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"[ERROR] Token error: {e}")
        return None


def test_gigachat_api():
    """Test GigaChat API status"""

    print("=" * 80)
    print("GIGACHAT API STATUS TEST")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Get token
    print("[1/3] Getting access token...")
    token = get_gigachat_token()
    if not token:
        return False
    print(f"✅ Token received: {token[:20]}...")
    print()

    # Step 2: Test request
    print("[2/3] Testing API request...")

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    data = {
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": "Привет! Это тест. Скажи просто 'OK'."
            }
        ],
        "max_tokens": 10,
        "temperature": 0.7
    }

    try:
        start_time = datetime.now()
        response = requests.post(url, headers=headers, json=data, verify=False)
        end_time = datetime.now()

        processing_time = (end_time - start_time).total_seconds()

        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"[OK] Response received in {processing_time:.2f}s")
            print(f"Response: {answer}")
            print()

            # Step 3: Second request (check rate limit)
            print("[3/3] Testing second request (rate limit check)...")

            start_time = datetime.now()
            response2 = requests.post(url, headers=headers, json=data, verify=False)
            end_time = datetime.now()

            processing_time2 = (end_time - start_time).total_seconds()

            if response2.status_code == 200:
                result2 = response2.json()
                answer2 = result2['choices'][0]['message']['content']
                print(f"✅ Second response received in {processing_time2:.2f}s")
                print(f"Response: {answer2}")
                print()

                # Summary
                print("=" * 80)
                print("API STATUS: ✅ WORKING")
                print("=" * 80)
                print(f"Request 1: {processing_time:.2f}s")
                print(f"Request 2: {processing_time2:.2f}s")
                print("No rate limit errors detected")
                print()
                print("✅ Quota restored - API is ready for testing")
                print("=" * 80)
                return True

            elif response2.status_code == 429:
                print("⚠️ RATE LIMIT ERROR (429)")
                print(f"Response: {response2.text}")
                print()
                print("=" * 80)
                print("API STATUS: ⚠️ RATE LIMITED")
                print("=" * 80)
                print("Первый запрос прошёл успешно")
                print("Второй запрос заблокирован rate limit")
                print()
                print("Возможные причины:")
                print("- Превышен RPM (requests per minute)")
                print("- Concurrent stream limit (1 для физ. лиц)")
                print()
                print("Рекомендация: Добавить задержку между запросами")
                print("=" * 80)
                return False
            else:
                print(f"❌ Second request failed: HTTP {response2.status_code}")
                print(f"Response: {response2.text}")
                return False

        elif response.status_code == 429:
            print("❌ RATE LIMIT ERROR (429)")
            print(f"Response: {response.text}")
            print()
            print("=" * 80)
            print("API STATUS: ❌ RATE LIMITED")
            print("=" * 80)
            print("Quota не восстановилась")
            print()
            print("Рекомендация: Подождать 24 часа")
            print("=" * 80)
            return False
        else:
            print(f"❌ Request failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = test_gigachat_api()
    exit(0 if success else 1)
