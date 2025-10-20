#!/usr/bin/env python3
"""
Простой скрипт для поиска писем от Михаила Арбатского
"""

import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime

def load_credentials():
    """Загрузка OAuth credentials из MCP сервера"""
    creds_file = 'C:/SnowWhiteAI/MCP_servers/mcp-gsuite/.oauth.otinoff@gmail.com.json'

    if not os.path.exists(creds_file):
        print(f"❌ Файл credentials не найден: {creds_file}")
        print("Нужно сначала авторизоваться через MCP сервер")
        return None

    with open(creds_file, 'r') as f:
        creds_data = json.load(f)

    creds = Credentials(
        token=creds_data.get('access_token'),
        refresh_token=creds_data.get('refresh_token'),
        token_uri=creds_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=creds_data.get('client_id'),
        client_secret=creds_data.get('client_secret')
    )

    return creds

def search_emails(service, query):
    """Поиск писем по запросу"""
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=20
        ).execute()

        messages = results.get('messages', [])
        return messages
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return []

def get_email_details(service, msg_id):
    """Получение деталей письма"""
    try:
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()

        headers = message['payload']['headers']

        # Извлекаем заголовки
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Без темы')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Неизвестно')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Неизвестно')

        # Получаем snippet
        snippet = message.get('snippet', '')

        return {
            'id': msg_id,
            'subject': subject,
            'from': from_email,
            'date': date,
            'snippet': snippet
        }
    except Exception as e:
        print(f"Ошибка получения письма {msg_id}: {e}")
        return None

def main():
    print("🔍 Поиск писем от Михаила Арбатского...\n")

    # Загружаем credentials
    creds = load_credentials()
    if not creds:
        return

    # Создаем Gmail API сервис
    try:
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail API подключен\n")
    except Exception as e:
        print(f"❌ Ошибка подключения к Gmail API: {e}")
        return

    # Ищем письма с разными вариантами
    queries = [
        "from:Арбатский",
        "from:Arbatsky",
        "from:Михаил",
        "Арбатский",
        "Arbatsky"
    ]

    all_emails = {}

    for query in queries:
        print(f"Поиск: {query}")
        messages = search_emails(service, query)
        print(f"  Найдено: {len(messages)}\n")

        for msg in messages:
            if msg['id'] not in all_emails:
                all_emails[msg['id']] = msg

    if not all_emails:
        print("\n❌ Письма не найдены")
        return

    print(f"\n📧 Всего уникальных писем: {len(all_emails)}")
    print("=" * 80)

    # Получаем детали каждого письма
    for i, msg_id in enumerate(all_emails.keys(), 1):
        details = get_email_details(service, msg_id)
        if details:
            print(f"\n{i}. {details['subject']}")
            print(f"   От: {details['from']}")
            print(f"   Дата: {details['date']}")
            print(f"   ID: {details['id']}")
            if details['snippet']:
                print(f"   Превью: {details['snippet'][:150]}...")

    # Сохраняем результаты
    output_file = 'C:/SnowWhiteAI/GrantService/arbatsky_emails_result.json'

    detailed_results = []
    for msg_id in all_emails.keys():
        details = get_email_details(service, msg_id)
        if details:
            detailed_results.append(details)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, ensure_ascii=False, indent=2)

    print(f"\n\n💾 Результаты сохранены: {output_file}")

if __name__ == "__main__":
    main()
