#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test /test_interactive command in production bot
"""
import requests
import time
import json
import sys

# Set UTF-8 output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BOT_TOKEN = "7685915842:AAGcW0kgtljyIob8enM3zvFSLuZ-BZzcPOo"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_latest_chat_id():
    """Get chat_id from recent messages"""
    response = requests.get(f"{BASE_URL}/getUpdates")
    data = response.json()

    if data['ok'] and data['result']:
        last_update = data['result'][-1]
        if 'message' in last_update:
            chat_id = last_update['message']['chat']['id']
            username = last_update['message']['chat'].get('username', 'Unknown')
            return chat_id, username
    return None, None

def send_message(chat_id, text):
    """Send message to chat"""
    response = requests.post(f"{BASE_URL}/sendMessage", json={
        'chat_id': chat_id,
        'text': text
    })
    return response.json()

def get_updates_after_offset(offset=None):
    """Get new messages"""
    params = {'timeout': 10}
    if offset:
        params['offset'] = offset

    response = requests.get(f"{BASE_URL}/getUpdates", params=params)
    return response.json()

def main():
    print("=" * 80)
    print("TEST: /test_interactive command in production bot")
    print("=" * 80)

    # Get chat_id from history
    print("\nStep 1: Getting chat_id from history...")
    chat_id, username = get_latest_chat_id()

    if not chat_id:
        print("ERROR: No messages found in bot history.")
        print("Send any message to bot (e.g. /start) and run script again.")
        return

    print(f"OK Chat ID: {chat_id}")
    print(f"OK Username: @{username}")

    # Get current offset
    updates = get_updates_after_offset()
    if updates['ok'] and updates['result']:
        current_offset = updates['result'][-1]['update_id'] + 1
    else:
        current_offset = 0

    # Send command
    print(f"\nStep 2: Sending /test_interactive to chat {chat_id}...")
    result = send_message(chat_id, "/test_interactive")

    if result['ok']:
        print("OK Command sent successfully!")
    else:
        print(f"ERROR sending command: {result}")
        return

    # Wait for response
    print("\nStep 3: Waiting for bot response (15 seconds)...")
    time.sleep(5)

    # Get new messages
    updates = get_updates_after_offset(current_offset)

    print("\nStep 4: Bot responses:")
    print("=" * 80)

    if updates['ok'] and updates['result']:
        bot_messages = []
        for update in updates['result']:
            if 'message' in update:
                msg = update['message']
                # Only bot messages
                if msg.get('from', {}).get('is_bot'):
                    text = msg.get('text', '')
                    bot_messages.append(text)
                    print(f"\nBOT:\n{text}")
                    print("-" * 80)

        if not bot_messages:
            print("WARNING: No new messages from bot. Check Telegram manually.")
        else:
            print(f"\nOK Received {len(bot_messages)} messages from bot")

            # Analyze response
            full_response = '\n'.join(bot_messages)

            if 'InteractiveInterviewerAgent' in full_response:
                print("\nSUCCESS: InteractiveInterviewerAgent mentioned!")

            if 'DatabasePromptManager' in full_response:
                print("SUCCESS: DatabasePromptManager connected!")

            if 'claude_code' in full_response.lower():
                print("SUCCESS: LLM Provider set!")

            if 'Ошибка' in full_response or 'ImportError' in full_response or 'Error' in full_response:
                print("ERROR: Errors found in bot response")
    else:
        print("WARNING: No updates. Check Telegram manually.")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print(f"\nCheck Telegram chat with bot manually")
    print(f"Chat ID: {chat_id}")

if __name__ == "__main__":
    main()
