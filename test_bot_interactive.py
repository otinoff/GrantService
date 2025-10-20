#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест /test_interactive команды в production боте
"""
import requests
import time
import json

BOT_TOKEN = "7685915842:AAGcW0kgtljyIob8enM3zvFSLuZ-BZzcPOo"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_latest_chat_id():
    """Получить chat_id из последних обновлений"""
    response = requests.get(f"{BASE_URL}/getUpdates")
    data = response.json()

    if data['ok'] and data['result']:
        # Берем последнее сообщение
        last_update = data['result'][-1]
        if 'message' in last_update:
            chat_id = last_update['message']['chat']['id']
            username = last_update['message']['chat'].get('username', 'Unknown')
            return chat_id, username
    return None, None

def send_message(chat_id, text):
    """Отправить сообщение в чат"""
    response = requests.post(f"{BASE_URL}/sendMessage", json={
        'chat_id': chat_id,
        'text': text
    })
    return response.json()

def get_updates_after_offset(offset=None):
    """Получить новые сообщения"""
    params = {'timeout': 10}
    if offset:
        params['offset'] = offset

    response = requests.get(f"{BASE_URL}/getUpdates", params=params)
    return response.json()

def main():
    print("=" * 80)
    print("🧪 ТЕСТ: /test_interactive команда в production боте")
    print("=" * 80)

    # Получаем chat_id из последних сообщений
    print("\n📱 Шаг 1: Получение chat_id из истории...")
    chat_id, username = get_latest_chat_id()

    if not chat_id:
        print("❌ Не найдено ни одного сообщения в истории бота.")
        print("Отправьте боту любое сообщение (например /start) и запустите скрипт снова.")
        return

    print(f"✅ Chat ID: {chat_id}")
    print(f"✅ Username: @{username}")

    # Получаем текущий offset
    updates = get_updates_after_offset()
    if updates['ok'] and updates['result']:
        current_offset = updates['result'][-1]['update_id'] + 1
    else:
        current_offset = 0

    # Отправляем команду
    print(f"\n📤 Шаг 2: Отправка /test_interactive в чат {chat_id}...")
    result = send_message(chat_id, "/test_interactive")

    if result['ok']:
        print("✅ Команда отправлена успешно!")
    else:
        print(f"❌ Ошибка отправки: {result}")
        return

    # Ждем ответ от бота
    print("\n⏳ Шаг 3: Ожидание ответа от бота (15 секунд)...")
    time.sleep(5)

    # Получаем новые сообщения
    updates = get_updates_after_offset(current_offset)

    print("\n📥 Шаг 4: Ответы от бота:")
    print("=" * 80)

    if updates['ok'] and updates['result']:
        bot_messages = []
        for update in updates['result']:
            if 'message' in update:
                msg = update['message']
                # Только сообщения от бота
                if msg.get('from', {}).get('is_bot'):
                    text = msg.get('text', '')
                    bot_messages.append(text)
                    print(f"\n🤖 БОТ:\n{text}")
                    print("-" * 80)

        if not bot_messages:
            print("⚠️ Нет новых сообщений от бота. Возможно бот не ответил или нужно подождать.")
            print("Проверьте Telegram вручную.")
        else:
            print(f"\n✅ Получено {len(bot_messages)} сообщений от бота")

            # Анализируем ответ
            full_response = '\n'.join(bot_messages)

            if 'InteractiveInterviewerAgent' in full_response:
                print("\n✅ SUCCESS: InteractiveInterviewerAgent упомянут в ответе!")

            if 'DatabasePromptManager' in full_response:
                print("✅ SUCCESS: DatabasePromptManager подключен!")

            if 'claude_code' in full_response.lower():
                print("✅ SUCCESS: LLM Provider установлен!")

            if 'Ошибка' in full_response or 'ImportError' in full_response:
                print("❌ ERROR: Обнаружены ошибки в ответе бота")
    else:
        print("⚠️ Нет обновлений. Проверьте Telegram вручную.")

    print("\n" + "=" * 80)
    print("✅ ТЕСТ ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\n💡 Для проверки откройте Telegram и посмотрите чат с ботом")
    print(f"   Chat ID: {chat_id}")

if __name__ == "__main__":
    main()
