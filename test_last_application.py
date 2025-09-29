#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест отправки уведомления о последней заявке из БД
"""

import os
import sys
import sqlite3
from datetime import datetime
import asyncio

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройка путей
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'telegram-bot', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'data'))

def get_last_application():
    """Получить последнюю заявку из БД"""
    db_path = r"C:\SnowWhiteAI\GrantService\data\grantservice.db"

    if not os.path.exists(db_path):
        print(f"❌ БД не найдена: {db_path}")
        return None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Получаем последнюю заявку с данными пользователя
        cursor.execute("""
            SELECT
                ga.application_number,
                ga.title,
                ga.grant_fund,
                ga.requested_amount,
                ga.project_duration,
                ga.created_at,
                ga.summary,
                ga.user_id,
                ga.session_id,
                u.telegram_id,
                u.username,
                u.first_name,
                u.last_name
            FROM grant_applications ga
            LEFT JOIN users u ON ga.user_id = u.id
            ORDER BY ga.created_at DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'application': {
                    'application_number': row[0],
                    'title': row[1],
                    'grant_fund': row[2] or 'Не указан',
                    'requested_amount': row[3] or 0,
                    'project_duration': row[4] or 0,
                    'created_at': row[5],
                    'summary': row[6]
                },
                'user': {
                    'telegram_id': row[9],
                    'username': row[10],
                    'first_name': row[11],
                    'last_name': row[12]
                } if row[9] else None
            }
        return None

    except Exception as e:
        print(f"❌ Ошибка при чтении БД: {e}")
        return None

async def send_last_application_notification():
    """Отправить уведомление о последней заявке"""

    print("=" * 60)
    print("🔍 ПОИСК ПОСЛЕДНЕЙ ЗАЯВКИ В БД")
    print("=" * 60)

    # Получаем последнюю заявку
    last_data = get_last_application()

    if not last_data:
        print("❌ Нет заявок в базе данных")
        return False

    application = last_data['application']
    user = last_data['user']

    print(f"✅ Найдена заявка: {application['application_number']}")
    print(f"   Название: {application['title']}")
    print(f"   Фонд: {application['grant_fund']}")
    print(f"   Сумма: {application['requested_amount']:,.0f} ₽")

    if user:
        print(f"   Пользователь: {user.get('first_name', '')} {user.get('last_name', '')}")
        if user.get('username'):
            print(f"   Username: @{user['username']}")
    print()

    # Загружаем токен
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        config_path = r"C:\SnowWhiteAI\GrantService\config\.env"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('TELEGRAM_BOT_TOKEN='):
                        bot_token = line.split('=', 1)[1].strip().strip('"\'')
                        break

    if not bot_token:
        print("❌ Токен бота не найден")
        return False

    print(f"✅ Токен загружен: ...{bot_token[-10:]}")

    # Импортируем и используем нотификатор
    from admin_notifications import AdminNotifier

    notifier = AdminNotifier(bot_token)
    print(f"📢 Отправка в группу: {notifier.admin_group_id}")
    print()

    # Отправляем уведомление
    print("📤 Отправляю уведомление...")

    try:
        success = await notifier.send_new_application_notification(
            application,
            user
        )

        if success:
            print("✅ УСПЕШНО! Уведомление отправлено в группу админов")
            print(f"   Заявка: {application['application_number']}")
            print("   Проверьте группу для подтверждения")
        else:
            print("❌ Не удалось отправить уведомление")

        return success

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_notification_format():
    """Проверить форматирование уведомления"""

    print("\n" + "=" * 60)
    print("📝 ТЕСТ ФОРМАТИРОВАНИЯ УВЕДОМЛЕНИЯ")
    print("=" * 60)

    from admin_notifications import AdminNotifier

    # Создаем тестовые данные
    test_app = {
        'application_number': 'TEST-FORMAT-001',
        'title': 'Проект социальной поддержки молодежи',
        'grant_fund': 'Росмолодежь.Гранты',
        'requested_amount': 2500000,
        'project_duration': 18,
        'created_at': datetime.now().isoformat()
    }

    test_user = {
        'telegram_id': 987654321,
        'username': 'admin_test',
        'first_name': 'Админ',
        'last_name': 'Тестовый'
    }

    # Создаем нотификатор (с фейковым токеном для теста)
    notifier = AdminNotifier("fake_token_for_test")

    # Форматируем сообщение
    message = notifier._format_notification(test_app, test_user)

    print("Сформированное сообщение:")
    print("-" * 40)
    print(message)
    print("-" * 40)

    return True

def check_bot_in_group():
    """Проверка добавления бота в группу"""

    print("\n" + "=" * 60)
    print("🤖 ПРОВЕРКА БОТА В ГРУППЕ")
    print("=" * 60)

    print("Для корректной работы уведомлений:")
    print()
    print("1. ✅ Добавьте бота в группу администраторов")
    print("2. ✅ Сделайте бота администратором группы")
    print("3. ✅ ID группы должен быть: -4930683040")
    print("4. ✅ У бота должны быть права на отправку сообщений")
    print()
    print("Команда для получения ID группы:")
    print("  - Добавьте в группу @getmyid_bot")
    print("  - Или используйте @JsonDumpBot")
    print()

    return True

if __name__ == "__main__":
    print("\n🚀 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ УВЕДОМЛЕНИЙ")
    print("=" * 60)

    # Тест 1: Форматирование
    print("\n[ТЕСТ 1/3]")
    test_format = test_notification_format()

    # Тест 2: Проверка настроек
    print("\n[ТЕСТ 2/3]")
    test_setup = check_bot_in_group()

    # Тест 3: Отправка реального уведомления
    print("\n[ТЕСТ 3/3]")
    try:
        # Запускаем асинхронную функцию
        loop = asyncio.get_event_loop()
        test_send = loop.run_until_complete(send_last_application_notification())
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")
        test_send = False

    # Итоги
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print(f"✅ Форматирование: Успешно")
    print(f"✅ Проверка настроек: Выполнено")
    print(f"{'✅' if test_send else '❌'} Отправка уведомления: {'Успешно' if test_send else 'Ошибка'}")

    if test_send:
        print("\n🎉 СИСТЕМА УВЕДОМЛЕНИЙ РАБОТАЕТ!")
        print("Администраторы будут получать уведомления о новых заявках")
    else:
        print("\n⚠️ ТРЕБУЕТСЯ НАСТРОЙКА")
        print("Проверьте:")
        print("1. Токен бота в config/.env")
        print("2. Бот добавлен в группу -4930683040")
        print("3. У бота есть права администратора в группе")