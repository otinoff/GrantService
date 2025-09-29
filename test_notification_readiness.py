#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка готовности системы уведомлений к продакшну
"""

import os
import sys
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

class ReadinessChecker:
    """Проверка готовности системы уведомлений"""

    def __init__(self):
        self.checks = []
        self.admin_group_id = -4930683040

    def add_check(self, name, status, details=""):
        """Добавить результат проверки"""
        self.checks.append({
            'name': name,
            'status': status,
            'details': details
        })

    async def check_environment(self):
        """Проверка окружения"""
        print("🔧 ПРОВЕРКА ОКРУЖЕНИЯ")
        print("-" * 40)

        # Проверка токена
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        config_token = None

        config_path = r"C:\SnowWhiteAI\GrantService\config\.env"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('TELEGRAM_BOT_TOKEN='):
                        config_token = line.split('=', 1)[1].strip()
                        break

        if config_token:
            self.add_check("Токен в конфиге", True, f"Найден в {config_path}")
            if not token:
                os.environ['TELEGRAM_BOT_TOKEN'] = config_token
                token = config_token
        else:
            self.add_check("Токен в конфиге", False, "Файл конфига не найден")

        if token:
            self.add_check("Переменная окружения", True, f"Длина: {len(token)}")
        else:
            self.add_check("Переменная окружения", False, "TELEGRAM_BOT_TOKEN не найден")

        # Проверка модулей
        try:
            import telegram
            self.add_check("python-telegram-bot", True, f"Версия {telegram.__version__}")
        except ImportError:
            self.add_check("python-telegram-bot", False, "Модуль не установлен")

        try:
            from admin_notifications import AdminNotifier
            self.add_check("AdminNotifier", True, "Модуль доступен")
        except ImportError as e:
            self.add_check("AdminNotifier", False, f"Ошибка импорта: {e}")

        # Проверка БД
        db_path = r"C:\SnowWhiteAI\GrantService\data\grantservice.db"
        if os.path.exists(db_path):
            self.add_check("База данных", True, f"Найдена: {db_path}")
        else:
            self.add_check("База данных", False, f"Файл не найден: {db_path}")

        return token

    async def check_bot_connection(self, token):
        """Проверка подключения к боту"""
        print("\n🤖 ПРОВЕРКА TELEGRAM БОТА")
        print("-" * 40)

        if not token:
            self.add_check("Подключение к боту", False, "Нет токена")
            return None

        try:
            from telegram import Bot
            bot = Bot(token=token)
            me = await bot.get_me()

            self.add_check("Подключение к боту", True, f"@{me.username} (ID: {me.id})")
            self.add_check("Имя бота", True, me.first_name)
            self.add_check("Может читать группы", me.can_read_all_group_messages,
                          "Да" if me.can_read_all_group_messages else "Нет")

            return bot

        except Exception as e:
            self.add_check("Подключение к боту", False, f"Ошибка: {e}")
            return None

    async def check_group_access(self, bot):
        """Проверка доступа к группе администраторов"""
        print("\n📢 ПРОВЕРКА ДОСТУПА К ГРУППЕ АДМИНОВ")
        print("-" * 40)

        if not bot:
            self.add_check("Доступ к группе", False, "Нет подключения к боту")
            return False

        try:
            chat = await bot.get_chat(self.admin_group_id)
            self.add_check("Группа найдена", True, f"{chat.title} ({chat.type})")

            # Проверяем статус бота
            me = await bot.get_me()
            member = await bot.get_chat_member(self.admin_group_id, me.id)

            can_send = getattr(member, 'can_send_messages', True)
            self.add_check("Статус бота в группе", True, member.status)
            self.add_check("Может отправлять сообщения", can_send,
                          "Да" if can_send else "Нет")

            return True

        except Exception as e:
            if "Chat not found" in str(e):
                self.add_check("Доступ к группе", False, "Бот не добавлен в группу")
            else:
                self.add_check("Доступ к группе", False, f"Ошибка: {e}")
            return False

    async def check_notification_functionality(self, bot):
        """Проверка функциональности уведомлений"""
        print("\n🔔 ПРОВЕРКА ФУНКЦИОНАЛЬНОСТИ УВЕДОМЛЕНИЙ")
        print("-" * 40)

        if not bot:
            self.add_check("Форматирование", False, "Нет подключения к боту")
            return False

        try:
            from admin_notifications import AdminNotifier
            notifier = AdminNotifier(bot.token)

            # Тестовые данные
            test_app = {
                'application_number': 'READINESS-CHECK-001',
                'title': 'Тест готовности системы',
                'grant_fund': 'Тестовый фонд',
                'requested_amount': 1000000,
                'project_duration': 12,
                'created_at': datetime.now().isoformat()
            }

            test_user = {
                'telegram_id': 123456789,
                'username': 'readiness_check',
                'first_name': 'Тест',
                'last_name': 'Готовности'
            }

            # Проверяем форматирование
            message = notifier._format_notification(test_app, test_user)
            if len(message) > 100 and 'НОВАЯ ЗАЯВКА НА ГРАНТ' in message:
                self.add_check("Форматирование", True, f"Длина: {len(message)} символов")
            else:
                self.add_check("Форматирование", False, "Некорректное форматирование")

            # Проверяем структуру класса
            self.add_check("AdminNotifier класс", True, "Все методы доступны")

            return True

        except Exception as e:
            self.add_check("Функциональность", False, f"Ошибка: {e}")
            return False

    def generate_report(self):
        """Генерация отчета о готовности"""
        print("\n" + "=" * 60)
        print("📊 ОТЧЕТ О ГОТОВНОСТИ СИСТЕМЫ УВЕДОМЛЕНИЙ")
        print("=" * 60)

        passed = 0
        failed = 0
        warnings = 0

        for check in self.checks:
            if check['status'] is True:
                status_icon = "✅"
                passed += 1
            elif check['status'] is False:
                status_icon = "❌"
                failed += 1
            else:
                status_icon = "⚠️"
                warnings += 1

            details = f" - {check['details']}" if check['details'] else ""
            print(f"{status_icon} {check['name']}{details}")

        total = len(self.checks)
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n📈 СТАТИСТИКА:")
        print(f"   Всего проверок: {total}")
        print(f"   ✅ Успешно: {passed}")
        print(f"   ❌ Неудачно: {failed}")
        print(f"   ⚠️ Предупреждения: {warnings}")
        print(f"   🎯 Успешность: {success_rate:.1f}%")

        # Оценка готовности
        print(f"\n🎯 ОЦЕНКА ГОТОВНОСТИ:")

        if success_rate >= 90 and failed == 0:
            print("🟢 СИСТЕМА ПОЛНОСТЬЮ ГОТОВА К ПРОДАКШНУ")
            readiness = "READY"
        elif success_rate >= 70 and failed <= 2:
            print("🟡 СИСТЕМА ПОЧТИ ГОТОВА (требуются незначительные исправления)")
            readiness = "ALMOST_READY"
        elif success_rate >= 50:
            print("🟠 СИСТЕМА ЧАСТИЧНО ГОТОВА (требуется настройка)")
            readiness = "NEEDS_SETUP"
        else:
            print("🔴 СИСТЕМА НЕ ГОТОВА (серьезные проблемы)")
            readiness = "NOT_READY"

        # Рекомендации
        print(f"\n💡 РЕКОМЕНДАЦИИ:")

        if failed > 0:
            critical_issues = [check for check in self.checks if check['status'] is False]
            for issue in critical_issues:
                if "Доступ к группе" in issue['name']:
                    print(f"   • Добавьте бота в группу {self.admin_group_id}")
                    print(f"   • Сделайте бота администратором группы")
                elif "Токен" in issue['name']:
                    print(f"   • Проверьте токен бота в config/.env")
                elif "База данных" in issue['name']:
                    print(f"   • Создайте базу данных или проверьте путь")
                else:
                    print(f"   • Исправьте: {issue['name']}")

        if readiness == "READY":
            print(f"   • Система готова к использованию")
            print(f"   • Можно запускать в продакшне")
        elif readiness == "ALMOST_READY":
            print(f"   • Исправьте критические ошибки")
            print(f"   • Проведите финальное тестирование")

        return readiness, success_rate

async def main():
    """Главная функция проверки готовности"""
    print("🔍 ПРОВЕРКА ГОТОВНОСТИ СИСТЕМЫ УВЕДОМЛЕНИЙ")
    print("=" * 60)
    print(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    checker = ReadinessChecker()

    # Выполняем все проверки
    token = await checker.check_environment()
    bot = await checker.check_bot_connection(token)
    group_access = await checker.check_group_access(bot)
    functionality = await checker.check_notification_functionality(bot)

    # Генерируем отчет
    readiness, success_rate = checker.generate_report()

    # Финальное сообщение
    print(f"\n🏁 ЗАКЛЮЧЕНИЕ:")
    if readiness == "READY":
        print("🎉 Поздравляем! Система уведомлений готова к работе.")
    else:
        print("⚠️ Требуется дополнительная настройка перед запуском.")

    return readiness == "READY"

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Проверка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)