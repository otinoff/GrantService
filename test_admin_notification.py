#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки уведомлений администраторам
"""

import os
import sys
from datetime import datetime

# Добавляем пути к модулям
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'telegram-bot', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'data'))

def test_notification():
    """Тестировать отправку уведомления в группу администраторов"""

    print("=" * 60)
    print("ТЕСТ ОТПРАВКИ УВЕДОМЛЕНИЙ В ГРУППУ АДМИНИСТРАТОРОВ")
    print("=" * 60)

    # Проверяем наличие токена бота
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        # Пробуем загрузить из конфига
        config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
        if os.path.exists(config_path):
            print(f"📁 Загружаю токен из {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('TELEGRAM_BOT_TOKEN='):
                        bot_token = line.split('=', 1)[1].strip().strip('"\'')
                        os.environ['TELEGRAM_BOT_TOKEN'] = bot_token
                        break

    if not bot_token:
        print("❌ ОШИБКА: Не найден TELEGRAM_BOT_TOKEN")
        print("Укажите токен в переменной окружения или в config/.env")
        return False

    print(f"✅ Токен бота найден: ...{bot_token[-10:]}")
    print()

    # Импортируем модуль уведомлений
    try:
        from admin_notifications import AdminNotifier
        print("✅ Модуль admin_notifications успешно импортирован")
    except ImportError as e:
        print(f"❌ Ошибка импорта модуля admin_notifications: {e}")
        return False

    # Создаем тестовые данные заявки
    test_application = {
        'application_number': f'TEST-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
        'title': 'Тестовый проект: Система автоматизации грантовых заявок',
        'grant_fund': 'Фонд президентских грантов',
        'requested_amount': 1500000,
        'project_duration': 12,
        'created_at': datetime.now().isoformat(),
        'summary': 'Это тестовая заявка для проверки системы уведомлений администраторов.'
    }

    # Создаем тестовые данные пользователя
    test_user = {
        'telegram_id': 123456789,
        'username': 'test_user',
        'first_name': 'Тестовый',
        'last_name': 'Пользователь'
    }

    print("📋 Тестовые данные заявки:")
    print(f"   Номер: {test_application['application_number']}")
    print(f"   Название: {test_application['title']}")
    print(f"   Фонд: {test_application['grant_fund']}")
    print(f"   Сумма: {test_application['requested_amount']:,} ₽")
    print()

    print("👤 Тестовые данные пользователя:")
    print(f"   Имя: {test_user['first_name']} {test_user['last_name']}")
    print(f"   Username: @{test_user['username']}")
    print(f"   Telegram ID: {test_user['telegram_id']}")
    print()

    # Создаем экземпляр нотификатора
    try:
        notifier = AdminNotifier(bot_token)
        print("✅ AdminNotifier создан успешно")
        print(f"📢 Целевая группа: {notifier.admin_group_id}")
        print()
    except Exception as e:
        print(f"❌ Ошибка создания AdminNotifier: {e}")
        return False

    # Отправляем тестовое уведомление
    print("📤 Отправляю уведомление...")
    try:
        # Используем синхронную версию
        success = notifier.send_notification_sync(test_application, test_user)

        if success:
            print("✅ УСПЕХ: Уведомление отправлено в группу администраторов!")
            print()
            print("Проверьте группу администраторов для подтверждения получения.")
            return True
        else:
            print("❌ ОШИБКА: Не удалось отправить уведомление")
            print("Проверьте:")
            print("1. Правильность ID группы: -4930683040")
            print("2. Добавлен ли бот в группу как администратор")
            print("3. Есть ли у бота права на отправку сообщений")
            return False

    except Exception as e:
        print(f"❌ Исключение при отправке: {e}")
        print()
        print("Возможные причины:")
        print("1. Неверный токен бота")
        print("2. Бот не добавлен в группу")
        print("3. Неправильный ID группы")
        print("4. Проблемы с сетевым подключением")
        return False


def test_database_integration():
    """Тестировать интеграцию с базой данных"""

    print("\n" + "=" * 60)
    print("ТЕСТ ИНТЕГРАЦИИ С БАЗОЙ ДАННЫХ")
    print("=" * 60)

    try:
        from database.models import Database
        db = Database()
        print("✅ База данных подключена")

        # Создаем тестовую заявку
        test_data = {
            'title': f'Тест уведомлений {datetime.now().strftime("%H:%M:%S")}',
            'grant_fund': 'Тестовый фонд',
            'requested_amount': 100000,
            'project_duration': 6,
            'summary': 'Тестовая заявка для проверки уведомлений',
            'admin_user': 'test_script'
        }

        print("💾 Сохраняю тестовую заявку в БД...")
        app_number = db.save_grant_application(test_data)

        if app_number:
            print(f"✅ Заявка сохранена: {app_number}")
            print("✅ Уведомление должно быть отправлено автоматически")
            return True
        else:
            print("❌ Не удалось сохранить заявку")
            return False

    except Exception as e:
        print(f"❌ Ошибка работы с БД: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 Запуск тестирования системы уведомлений\n")

    # Тест 1: Прямая отправка уведомления
    test1_result = test_notification()

    # Тест 2: Интеграция с БД
    test2_result = test_database_integration()

    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print(f"Прямая отправка: {'✅ Успех' if test1_result else '❌ Ошибка'}")
    print(f"Интеграция с БД: {'✅ Успех' if test2_result else '❌ Ошибка'}")
    print()

    if test1_result and test2_result:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("Система уведомлений готова к работе.")
    else:
        print("⚠️ Есть проблемы, требующие внимания.")
        print("Проверьте сообщения об ошибках выше.")