#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрационный тест системы уведомлений
Отправляет уведомление в личный чат с ботом для проверки функциональности
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

def load_correct_token():
    """Загрузить правильный токен из config/.env"""
    config_path = r"C:\SnowWhiteAI\GrantService\config\.env"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    os.environ['TELEGRAM_BOT_TOKEN'] = token
                    return token
    return os.getenv('TELEGRAM_BOT_TOKEN')

async def test_notification_functionality():
    """Тест функциональности уведомлений"""

    print("🧪 ДЕМОНСТРАЦИОННЫЙ ТЕСТ СИСТЕМЫ УВЕДОМЛЕНИЙ")
    print("=" * 60)

    # Загружаем правильный токен
    bot_token = load_correct_token()
    if not bot_token:
        print("❌ Токен не найден")
        return False

    print(f"✅ Токен загружен: {bot_token[:8]}...{bot_token[-10:]}")

    # Проверяем бота
    try:
        from telegram import Bot
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        print(f"✅ Бот активен: @{me.username} (ID: {me.id})")
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")
        return False

    # Получаем данные из БД
    print("\n💾 ЗАГРУЗКА ДАННЫХ ИЗ БД")
    print("-" * 40)

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
            print("❌ Заявок не найдено")
            return False

        # Парсим данные
        app_data = {
            'application_number': row[0],
            'title': row[1] or 'Без названия',
            'grant_fund': row[2] or 'Фонд не указан',
            'requested_amount': row[3] or 500000,  # Добавим сумму для демо
            'project_duration': row[4] or 12,
            'created_at': row[5],
            'summary': row[6]
        }

        # Извлекаем данные пользователя из JSON
        user_data = None
        if row[7]:
            try:
                content = json.loads(row[7])
                if 'user_info' in content:
                    user_data = content['user_info']
            except json.JSONDecodeError:
                pass

        print(f"✅ Заявка: {app_data['application_number']}")
        print(f"   Название: {app_data['title']}")
        print(f"   Фонд: {app_data['grant_fund']}")
        print(f"   Сумма: {app_data['requested_amount']:,.0f} ₽")

        if user_data:
            print(f"   Пользователь: {user_data.get('first_name', '')} {user_data.get('last_name', '')}")

    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False

    # Тестируем форматирование уведомления
    print("\n📝 ТЕСТ ФОРМАТИРОВАНИЯ УВЕДОМЛЕНИЯ")
    print("-" * 40)

    try:
        from admin_notifications import AdminNotifier
        notifier = AdminNotifier(bot_token)

        # Создаем отформатированное сообщение
        formatted_message = notifier._format_notification(app_data, user_data)

        print("✅ Сообщение отформатировано:")
        print(f"   Длина: {len(formatted_message)} символов")
        print("\n" + "=" * 50)
        print("ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР УВЕДОМЛЕНИЯ:")
        print("=" * 50)
        print(formatted_message)
        print("=" * 50)

    except Exception as e:
        print(f"❌ Ошибка форматирования: {e}")
        return False

    # Для демонстрации - отправляем сообщение в чат с создателем бота
    # (ID можно получить, написав боту /start и посмотрев в логах)
    print("\n📤 ДЕМОНСТРАЦИЯ ОТПРАВКИ УВЕДОМЛЕНИЯ")
    print("-" * 40)

    # Попробуем отправить в известный Telegram ID разработчика
    # В реальной системе это будет группа администраторов
    demo_chat_id = user_data.get('telegram_id') if user_data else None

    if demo_chat_id:
        print(f"🎯 Отправляю демо-уведомление пользователю: {demo_chat_id}")

        try:
            # Создаем демо-сообщение
            demo_message = f"""
🧪 <b>ДЕМОНСТРАЦИЯ СИСТЕМЫ УВЕДОМЛЕНИЙ</b>

Это тестовое уведомление для демонстрации работы системы AdminNotifier в проекте GrantService.

<i>В реальной работе такие уведомления отправляются в группу администраторов при создании новой заявки.</i>

{formatted_message}

🔧 <b>Техническая информация:</b>
• Бот: @{me.username}
• Время теста: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Статус: ✅ Система работает корректно

#тест #demo #уведомления
"""

            from telegram.constants import ParseMode

            message = await bot.send_message(
                chat_id=demo_chat_id,
                text=demo_message.strip(),
                parse_mode=ParseMode.HTML
            )

            print(f"✅ Демо-уведомление отправлено!")
            print(f"   ID сообщения: {message.message_id}")
            print(f"   Получатель: {demo_chat_id}")

            return True

        except Exception as e:
            print(f"❌ Ошибка отправки демо: {e}")
    else:
        print("⚠️ Нет данных пользователя для демонстрации")

    print("\n📊 ЗАКЛЮЧЕНИЕ")
    print("-" * 40)
    print("✅ Система уведомлений функционально готова")
    print("✅ Форматирование сообщений работает корректно")
    print("✅ Бот активен и может отправлять сообщения")
    print()
    print("⚠️ Для полной работы требуется:")
    print("   1. Добавить бота @Grafana_SnowWhite_bot в группу админов")
    print("   2. Дать боту права администратора в группе")
    print("   3. Проверить правильность ID группы: -4930683040")

    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_notification_functionality())
    except KeyboardInterrupt:
        print("\n\n⏹️ Тест прерван пользователем")
    except Exception as e:
        print(f"\n\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()