#!/usr/bin/env python3
"""
Скрипт для поиска писем от Михаила Арбатского через Gmail API
Использует OAuth конфигурацию из MCP сервера gsuite
"""

import sys
import os

# Добавляем путь к MCP серверу
sys.path.insert(0, 'C:/SnowWhiteAI/MCP_servers/mcp-gsuite/src')

from mcp_gsuite import gauth, gmail
import json

def search_emails_from_arbatsky():
    """Поиск писем от Михаила Арбатского"""

    # Настраиваем пути к конфигурации
    gauth_file = 'C:/SnowWhiteAI/MCP_servers/mcp-gsuite/.gauth.json'
    accounts_file = 'C:/SnowWhiteAI/MCP_servers/mcp-gsuite/.accounts.json'
    credentials_dir = 'C:/SnowWhiteAI/MCP_servers/mcp-gsuite'

    # Устанавливаем переменные окружения для gauth
    os.environ['GAUTH_FILE'] = gauth_file
    os.environ['ACCOUNTS_FILE'] = accounts_file
    os.environ['CREDENTIALS_DIR'] = credentials_dir

    # Получаем email из конфигурации
    with open(accounts_file, 'r', encoding='utf-8') as f:
        accounts = json.load(f)
        user_email = accounts['accounts'][0]['email']

    print(f"Используем аккаунт: {user_email}")

    # Получаем credentials
    try:
        credentials = gauth.get_stored_credentials(user_id=user_email)
        if not credentials:
            print("❌ Не найдены сохраненные credentials")
            print("Нужно запустить авторизацию через MCP сервер")
            return

        # Обновляем токен если нужно
        if credentials.access_token_expired:
            print("🔄 Обновляем access token...")
            user_info = gauth.get_user_info(credentials=credentials)
            gauth.store_credentials(credentials=credentials, user_id=user_email)

        print("✅ Авторизация успешна")

        # Создаем Gmail сервис
        gmail_service = gmail.GmailService(credentials=credentials)

        # Поиск писем от Арбатского
        print("\n🔍 Ищу письма от Михаила Арбатского...")

        # Пробуем разные варианты поиска
        queries = [
            "from:Арбатский",
            "from:Arbatsky",
            "from:Михаил",
            "from:arbatsky"
        ]

        all_emails = []
        for query in queries:
            print(f"\nПоиск по запросу: {query}")
            try:
                emails = gmail_service.query_emails(
                    query=query,
                    max_results=20
                )

                if emails:
                    print(f"  Найдено писем: {len(emails)}")
                    all_emails.extend(emails)
            except Exception as e:
                print(f"  Ошибка: {e}")

        # Убираем дубликаты
        unique_emails = {email['id']: email for email in all_emails}.values()

        print(f"\n📧 Всего уникальных писем: {len(unique_emails)}")
        print("\n" + "="*80)

        # Выводим результаты
        for i, email in enumerate(unique_emails, 1):
            print(f"\n{i}. ID: {email['id']}")
            print(f"   От: {email.get('from', 'N/A')}")
            print(f"   Тема: {email.get('subject', 'N/A')}")
            print(f"   Дата: {email.get('date', 'N/A')}")

            # Краткое содержание
            snippet = email.get('snippet', '')
            if snippet:
                print(f"   Превью: {snippet[:100]}...")

        # Сохраняем результаты в файл
        output_file = 'C:/SnowWhiteAI/GrantService/arbatsky_emails.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(list(unique_emails), f, ensure_ascii=False, indent=2)

        print(f"\n\n💾 Результаты сохранены в: {output_file}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    search_emails_from_arbatsky()
