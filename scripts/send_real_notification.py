#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отправка реального уведомления в админскую группу Telegram
Тест для test-engineer GrantService
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

ADMIN_GROUP_ID = -4930683040

def load_bot_token():
    """Загрузить токен бота из config/.env"""
    config_path = r"C:\SnowWhiteAI\GrantService\config\.env"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    return token
    return os.getenv('TELEGRAM_BOT_TOKEN')

def get_latest_application():
    """Получить данные последней заявки из БД"""
    db_path = r"C:\SnowWhiteAI\GrantService\data\grantservice.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

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
        conn.close()

        if not row:
            return None, None

        # Формируем данные заявки
        app_data = {
            'application_number': row[0],
            'title': row[1] or 'Без названия',
            'grant_fund': row[2] or 'Фонд не указан',
            'requested_amount': row[3] or 0,
            'project_duration': row[4] or 12,
            'created_at': row[5],
            'summary': row[6] or 'Краткое описание отсутствует'
        }

        # Извлекаем user_info
        user_data = None
        if row[7]:
            try:
                content = json.loads(row[7])
                user_data = content.get('user_info', {})
            except json.JSONDecodeError:
                user_data = {}

        return app_data, user_data

    except Exception as e:
        print(f"Ошибка БД: {e}")
        return None, None

def format_notification_message(app_data, user_data):
    """Форматировать сообщение для админов"""

    # Информация о пользователе
    user_name = "Неизвестный пользователь"
    if user_data:
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        username = user_data.get('username', '')
        telegram_id = user_data.get('telegram_id', '')

        if first_name or last_name:
            user_name = f"{first_name} {last_name}".strip()
        elif username:
            user_name = f"@{username}"
        elif telegram_id:
            user_name = f"ID: {telegram_id}"

    # Формируем красивое сообщение
    message = f"""
🆕 <b>НОВАЯ ЗАЯВКА НА ГРАНТ</b>

📋 <b>Заявка №{app_data['application_number']}</b>
🎯 <b>Название проекта:</b> {app_data['title']}
🏛 <b>Фонд:</b> {app_data['grant_fund']}
💰 <b>Запрашиваемая сумма:</b> {app_data['requested_amount']:,.0f} ₽
⏱ <b>Длительность проекта:</b> {app_data['project_duration']} мес.
📅 <b>Дата подачи:</b> {app_data['created_at']}

👤 <b>Заявитель:</b> {user_name}

📝 <b>Краткое описание:</b>
{app_data['summary'][:200]}{"..." if len(app_data['summary']) > 200 else ""}

⚡️ <b>Требуется проверка администратора</b>

#новая_заявка #грант #{app_data['grant_fund'].replace(' ', '_').lower()}
""".strip()

    return message

async def send_real_notification():
    """Отправить РЕАЛЬНОЕ уведомление в админскую группу"""

    print("🚀 ОТПРАВКА РЕАЛЬНОГО УВЕДОМЛЕНИЯ В АДМИНСКУЮ ГРУППУ")
    print("=" * 60)
    print(f"🎯 Целевая группа: {ADMIN_GROUP_ID}")
    print()

    # 1. Загружаем токен
    print("1️⃣ Загрузка токена бота...")
    bot_token = load_bot_token()
    if not bot_token:
        print("❌ ОШИБКА: Токен не найден в config/.env")
        return False

    print(f"✅ Токен загружен: ...{bot_token[-10:]}")

    # 2. Проверяем бота
    print("\n2️⃣ Проверка бота...")
    try:
        from telegram import Bot
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        print(f"✅ Бот активен: @{me.username} (ID: {me.id})")
    except Exception as e:
        print(f"❌ ОШИБКА бота: {e}")
        return False

    # 3. Загружаем данные заявки
    print("\n3️⃣ Загрузка данных последней заявки...")
    app_data, user_data = get_latest_application()

    if not app_data:
        print("❌ ОШИБКА: Заявки в БД не найдены")
        return False

    print(f"✅ Заявка загружена: №{app_data['application_number']}")
    print(f"   Название: {app_data['title']}")
    print(f"   Фонд: {app_data['grant_fund']}")
    print(f"   Сумма: {app_data['requested_amount']:,.0f} ₽")

    # 4. Форматируем сообщение
    print("\n4️⃣ Форматирование сообщения...")
    message = format_notification_message(app_data, user_data)
    print(f"✅ Сообщение готово ({len(message)} символов)")

    # 5. Отправляем в группу
    print("\n5️⃣ ОТПРАВКА В АДМИНСКУЮ ГРУППУ...")
    print(f"🎯 Отправляю в группу: {ADMIN_GROUP_ID}")

    try:
        from telegram.constants import ParseMode

        result = await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

        print("🎉 УСПЕХ! Уведомление отправлено в админскую группу!")
        print(f"✅ ID сообщения: {result.message_id}")
        print(f"✅ Дата отправки: {result.date}")
        print(f"✅ В группу: {result.chat.id}")

        if hasattr(result.chat, 'title'):
            print(f"✅ Название группы: {result.chat.title}")

        return True

    except Exception as e:
        print(f"❌ ОШИБКА ОТПРАВКИ: {e}")
        print("\nВозможные причины:")
        print("- Бот не добавлен в группу")
        print("- У бота нет прав на отправку сообщений")
        print("- Неверный ID группы")
        print("- Группа заблокировала бота")
        return False

async def main():
    """Главная функция"""
    print("🧪 TEST ENGINEER - ОТПРАВКА РЕАЛЬНОГО УВЕДОМЛЕНИЯ")
    print("=" * 60)
    print("ВНИМАНИЕ! Это реальная отправка в Telegram группу!")
    print("Группа -4930683040 получит уведомление прямо сейчас!")
    print("=" * 60)
    print()

    success = await send_real_notification()

    print("\n" + "=" * 60)
    if success:
        print("🎉 ТЕСТ УСПЕШНО ЗАВЕРШЕН!")
        print("✅ Уведомление доставлено в админскую группу")
        print("✅ Система уведомлений работает корректно")
    else:
        print("❌ ТЕСТ НЕУДАЧЕН")
        print("❌ Уведомление не было отправлено")
        print("❌ Требуется исправление ошибок")

    print("=" * 60)
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Отправка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)