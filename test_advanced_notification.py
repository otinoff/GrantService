#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Продвинутый тест системы уведомлений с детальной диагностикой
"""

import os
import sys
import sqlite3
import json
import asyncio
from datetime import datetime

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройка путей
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'telegram-bot', 'utils'))

async def check_bot_token():
    """Проверить токен бота"""

    print("🔑 ПРОВЕРКА ТОКЕНА БОТА")
    print("=" * 50)

    # Загрузка токена
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        config_path = r"C:\SnowWhiteAI\GrantService\config\.env"
        if os.path.exists(config_path):
            print(f"📁 Загружаю токен из {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('TELEGRAM_BOT_TOKEN='):
                        bot_token = line.split('=', 1)[1].strip().strip('"\'')
                        break

    if not bot_token:
        print("❌ Токен не найден")
        return None

    print(f"✅ Токен найден: {bot_token[:8]}...{bot_token[-10:]}")
    print(f"   Длина: {len(bot_token)}")

    # Проверка токена через Telegram API
    try:
        from telegram import Bot
        bot = Bot(token=bot_token)

        print("🔍 Проверяю токен через getMe...")
        me = await bot.get_me()

        print(f"✅ Бот активен: @{me.username}")
        print(f"   ID: {me.id}")
        print(f"   Имя: {me.first_name}")
        print(f"   Может читать группы: {me.can_read_all_group_messages}")

        return bot_token

    except Exception as e:
        print(f"❌ Ошибка проверки токена: {e}")
        return None

async def check_group_access(bot_token, group_id):
    """Проверить доступ к группе"""

    print(f"\n📢 ПРОВЕРКА ДОСТУПА К ГРУППЕ {group_id}")
    print("=" * 50)

    try:
        from telegram import Bot
        bot = Bot(token=bot_token)

        # Получаем информацию о чате
        print("🔍 Получаю информацию о группе...")
        chat = await bot.get_chat(group_id)

        print(f"✅ Группа найдена: {chat.title}")
        print(f"   Тип: {chat.type}")
        print(f"   ID: {chat.id}")
        print(f"   Участников: {chat.get_member_count() if hasattr(chat, 'get_member_count') else 'Неизвестно'}")

        # Проверяем статус бота в группе
        print("🔍 Проверяю статус бота в группе...")
        me = await bot.get_me()
        member = await bot.get_chat_member(group_id, me.id)

        print(f"✅ Статус бота: {member.status}")
        print(f"   Может отправлять сообщения: {member.can_send_messages if hasattr(member, 'can_send_messages') else 'Неизвестно'}")

        return True

    except Exception as e:
        print(f"❌ Ошибка доступа к группе: {e}")
        print(f"   Возможные причины:")
        print(f"   1. Бот не добавлен в группу")
        print(f"   2. Неправильный ID группы")
        print(f"   3. Группа была удалена или заблокирована")
        return False

async def send_test_message(bot_token, group_id):
    """Отправить тестовое сообщение"""

    print(f"\n📤 ОТПРАВКА ТЕСТОВОГО СООБЩЕНИЯ")
    print("=" * 50)

    try:
        from telegram import Bot
        from telegram.constants import ParseMode

        bot = Bot(token=bot_token)

        test_message = f"""
🧪 <b>ТЕСТОВОЕ СООБЩЕНИЕ</b>

Это тест системы уведомлений GrantService.

🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 Отправлено: test-engineer агентом
✅ Если вы видите это сообщение, система работает корректно!

#тест #уведомления
"""

        print("📨 Отправляю тестовое сообщение...")
        message = await bot.send_message(
            chat_id=group_id,
            text=test_message.strip(),
            parse_mode=ParseMode.HTML
        )

        print(f"✅ Сообщение отправлено!")
        print(f"   ID сообщения: {message.message_id}")
        print(f"   Дата: {message.date}")

        return True

    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

def get_last_application():
    """Получить последнюю заявку из БД"""

    print(f"\n💾 ЗАГРУЗКА ПОСЛЕДНЕЙ ЗАЯВКИ ИЗ БД")
    print("=" * 50)

    db_path = r"C:\SnowWhiteAI\GrantService\data\grantservice.db"

    if not os.path.exists(db_path):
        print(f"❌ БД не найдена: {db_path}")
        return None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Получаем последнюю заявку
        cursor.execute("""
            SELECT
                application_number,
                title,
                grant_fund,
                requested_amount,
                project_duration,
                created_at,
                summary,
                content_json
            FROM grant_applications
            ORDER BY created_at DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

        if not row:
            print("❌ Заявок не найдено")
            conn.close()
            return None

        # Парсим данные
        app_data = {
            'application_number': row[0],
            'title': row[1],
            'grant_fund': row[2] or 'Не указан',
            'requested_amount': row[3] or 0,
            'project_duration': row[4] or 0,
            'created_at': row[5],
            'summary': row[6]
        }

        # Извлекаем данные пользователя из JSON
        user_data = None
        if row[7]:  # content_json
            try:
                content = json.loads(row[7])
                if 'user_info' in content:
                    user_data = content['user_info']
            except json.JSONDecodeError:
                print("⚠️ Не удалось распарсить JSON с данными пользователя")

        conn.close()

        print(f"✅ Заявка загружена: {app_data['application_number']}")
        print(f"   Название: {app_data['title']}")
        print(f"   Фонд: {app_data['grant_fund']}")
        print(f"   Сумма: {app_data['requested_amount']:,.0f} ₽")

        if user_data:
            print(f"   Пользователь: {user_data.get('first_name', '')} {user_data.get('last_name', '')}")
            if user_data.get('username'):
                print(f"   Username: @{user_data['username']}")

        return {'application': app_data, 'user': user_data}

    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return None

async def test_notification_with_real_data(bot_token, group_id):
    """Тест уведомления с реальными данными"""

    print(f"\n🎯 ТЕСТ УВЕДОМЛЕНИЯ С РЕАЛЬНЫМИ ДАННЫМИ")
    print("=" * 50)

    # Получаем данные
    data = get_last_application()
    if not data:
        return False

    # Создаем нотификатор
    try:
        from admin_notifications import AdminNotifier
        notifier = AdminNotifier(bot_token)

        print("📤 Отправляю уведомление о реальной заявке...")
        success = await notifier.send_new_application_notification(
            data['application'],
            data['user']
        )

        if success:
            print("✅ Уведомление отправлено успешно!")
        else:
            print("❌ Не удалось отправить уведомление")

        return success

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def main():
    """Главная функция тестирования"""

    print("🧪 ПРОДВИНУТОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ УВЕДОМЛЕНИЙ")
    print("=" * 60)
    print(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    group_id = -4930683040

    # Тест 1: Проверка токена
    bot_token = await check_bot_token()
    if not bot_token:
        print("\n❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Проблемы с токеном")
        return

    # Тест 2: Проверка доступа к группе
    group_access = await check_group_access(bot_token, group_id)

    # Тест 3: Отправка тестового сообщения
    if group_access:
        test_send = await send_test_message(bot_token, group_id)
    else:
        print("\n⚠️ Пропускаю отправку из-за проблем с доступом к группе")
        test_send = False

    # Тест 4: Отправка уведомления с реальными данными
    if test_send:
        real_notification = await test_notification_with_real_data(bot_token, group_id)
    else:
        print("\n⚠️ Пропускаю уведомление с реальными данными")
        real_notification = False

    # Итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)

    results = [
        ("Проверка токена", bot_token is not None),
        ("Доступ к группе", group_access),
        ("Тестовое сообщение", test_send),
        ("Уведомление с данными", real_notification)
    ]

    for test_name, result in results:
        status = "✅ Успешно" if result else "❌ Ошибка"
        print(f"{status.ljust(12)} {test_name}")

    success_count = sum(1 for _, result in results if result)
    total_count = len(results)

    print(f"\nРезультат: {success_count}/{total_count} тестов пройдено")

    if success_count == total_count:
        print("🎉 СИСТЕМА УВЕДОМЛЕНИЙ ПОЛНОСТЬЮ РАБОТОСПОСОБНА!")
    elif success_count >= 2:
        print("⚠️ Система частично работоспособна, требуется доработка")
    else:
        print("❌ СИСТЕМА НЕ РАБОТАЕТ, требуется серьезная настройка")

    print("\n📝 Рекомендации для улучшения:")
    if not group_access:
        print("1. Добавьте бота в группу -4930683040")
        print("2. Сделайте бота администратором группы")
        print("3. Дайте боту права на отправку сообщений")

    if bot_token and group_access and not test_send:
        print("1. Проверьте интернет-соединение")
        print("2. Убедитесь что Telegram API доступен")
        print("3. Проверьте лимиты отправки сообщений")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()