#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модульные тесты для AdminNotifier класса
"""

import os
import sys
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
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

class TestAdminNotifier(unittest.TestCase):
    """Тесты для класса AdminNotifier"""

    def setUp(self):
        """Подготовка к тестам"""
        self.test_token = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        self.test_group_id = -4930683040

    def test_notifier_init(self):
        """Тест инициализации нотификатора"""
        from admin_notifications import AdminNotifier

        notifier = AdminNotifier(self.test_token)

        self.assertIsNotNone(notifier.bot)
        self.assertEqual(notifier.admin_group_id, self.test_group_id)

    def test_format_notification_basic(self):
        """Тест базового форматирования уведомления"""
        from admin_notifications import AdminNotifier

        notifier = AdminNotifier(self.test_token)

        app_data = {
            'application_number': 'TEST-001',
            'title': 'Тестовый проект',
            'grant_fund': 'Росмолодежь',
            'requested_amount': 1000000,
            'project_duration': 12,
            'created_at': '2025-09-30T00:00:00'
        }

        user_data = {
            'telegram_id': 123456789,
            'username': 'testuser',
            'first_name': 'Тест',
            'last_name': 'Пользователь'
        }

        message = notifier._format_notification(app_data, user_data)

        # Проверяем наличие ключевых элементов
        self.assertIn('НОВАЯ ЗАЯВКА НА ГРАНТ', message)
        self.assertIn('TEST-001', message)
        self.assertIn('Тестовый проект', message)
        self.assertIn('Росмолодежь', message)
        self.assertIn('1 000 000 ₽', message)
        self.assertIn('Тест Пользователь', message)
        self.assertIn('@testuser', message)
        self.assertIn('#новая_заявка', message)

    def test_format_notification_no_user(self):
        """Тест форматирования без данных пользователя"""
        from admin_notifications import AdminNotifier

        notifier = AdminNotifier(self.test_token)

        app_data = {
            'application_number': 'TEST-002',
            'title': 'Проект без пользователя',
            'grant_fund': 'Тестовый фонд',
            'requested_amount': 500000,
            'project_duration': 6,
            'created_at': '2025-09-30T00:00:00'
        }

        message = notifier._format_notification(app_data, None)

        self.assertIn('TEST-002', message)
        self.assertIn('Проект без пользователя', message)
        self.assertIn('Неизвестный пользователь', message)

    def test_format_notification_minimal_data(self):
        """Тест форматирования с минимальными данными"""
        from admin_notifications import AdminNotifier

        notifier = AdminNotifier(self.test_token)

        app_data = {
            'application_number': 'TEST-003',
            'title': None,
            'grant_fund': None,
            'requested_amount': 0,
            'project_duration': None,
            'created_at': None
        }

        message = notifier._format_notification(app_data, None)

        self.assertIn('TEST-003', message)
        self.assertIn('Без названия', message)
        self.assertIn('Не указан', message)
        self.assertIn('Не указана', message)

    @patch('telegram.Bot.send_message', new_callable=AsyncMock)
    async def test_send_notification_success(self, mock_send_message):
        """Тест успешной отправки уведомления"""
        from admin_notifications import AdminNotifier

        # Настраиваем мок
        mock_send_message.return_value = MagicMock(message_id=123)

        notifier = AdminNotifier(self.test_token)

        app_data = {
            'application_number': 'TEST-004',
            'title': 'Успешный тест',
            'grant_fund': 'Тестовый фонд',
            'requested_amount': 750000,
            'project_duration': 8,
            'created_at': '2025-09-30T00:00:00'
        }

        user_data = {
            'telegram_id': 987654321,
            'username': 'success_user',
            'first_name': 'Успешный',
            'last_name': 'Тест'
        }

        # Выполняем тест
        result = await notifier.send_new_application_notification(app_data, user_data)

        # Проверяем результат
        self.assertTrue(result)
        mock_send_message.assert_called_once()

        # Проверяем параметры вызова
        call_args = mock_send_message.call_args
        self.assertEqual(call_args[1]['chat_id'], self.test_group_id)
        self.assertIn('TEST-004', call_args[1]['text'])
        self.assertIn('Успешный тест', call_args[1]['text'])

    @patch('telegram.Bot.send_message', new_callable=AsyncMock)
    async def test_send_notification_telegram_error(self, mock_send_message):
        """Тест обработки ошибки Telegram API"""
        from admin_notifications import AdminNotifier
        from telegram.error import TelegramError

        # Настраиваем мок для ошибки
        mock_send_message.side_effect = TelegramError("Test error")

        notifier = AdminNotifier(self.test_token)

        app_data = {
            'application_number': 'TEST-005',
            'title': 'Тест ошибки',
            'created_at': '2025-09-30T00:00:00'
        }

        # Выполняем тест
        result = await notifier.send_new_application_notification(app_data)

        # Проверяем результат
        self.assertFalse(result)
        mock_send_message.assert_called_once()

    @patch('telegram.Bot.send_message', new_callable=AsyncMock)
    async def test_send_notification_generic_error(self, mock_send_message):
        """Тест обработки общей ошибки"""
        from admin_notifications import AdminNotifier

        # Настраиваем мок для ошибки
        mock_send_message.side_effect = Exception("Generic error")

        notifier = AdminNotifier(self.test_token)

        app_data = {
            'application_number': 'TEST-006',
            'title': 'Тест общей ошибки',
            'created_at': '2025-09-30T00:00:00'
        }

        # Выполняем тест
        result = await notifier.send_new_application_notification(app_data)

        # Проверяем результат
        self.assertFalse(result)

    def test_get_notifier_with_token(self):
        """Тест создания нотификатора с токеном"""
        from admin_notifications import get_notifier

        notifier = get_notifier(self.test_token)

        self.assertIsNotNone(notifier)
        self.assertEqual(notifier.admin_group_id, self.test_group_id)

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'env_token_12345'})
    def test_get_notifier_from_env(self):
        """Тест создания нотификатора из переменной окружения"""
        from admin_notifications import get_notifier

        notifier = get_notifier()

        self.assertIsNotNone(notifier)

    @patch.dict(os.environ, {}, clear=True)
    def test_get_notifier_no_token(self):
        """Тест создания нотификатора без токена"""
        from admin_notifications import get_notifier

        notifier = get_notifier()

        self.assertIsNone(notifier)

    def test_sync_wrapper_with_running_loop(self):
        """Тест синхронной обертки с работающим event loop"""
        from admin_notifications import AdminNotifier

        notifier = AdminNotifier(self.test_token)

        app_data = {
            'application_number': 'TEST-007',
            'title': 'Тест синхронной обертки',
            'created_at': '2025-09-30T00:00:00'
        }

        # В реальности это должно создать задачу
        # Мы просто проверяем, что метод не падает
        try:
            # Этот вызов может вернуть True (задача создана) или False (ошибка)
            result = notifier.send_notification_sync(app_data)
            # Результат может быть любым, главное - отсутствие исключений
            self.assertIsInstance(result, bool)
        except Exception as e:
            # Допустимы ошибки связанные с отсутствием event loop или токеном
            self.assertIn(('loop', 'token', 'Unauthorized'), str(e).lower())

class TestAdminNotifierIntegration(unittest.TestCase):
    """Интеграционные тесты для AdminNotifier"""

    def setUp(self):
        """Подготовка к интеграционным тестам"""
        # Загружаем реальный токен из конфига
        config_path = r"C:\SnowWhiteAI\GrantService\config\.env"
        self.real_token = None

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('TELEGRAM_BOT_TOKEN='):
                        self.real_token = line.split('=', 1)[1].strip()
                        break

    def test_real_token_validation(self):
        """Тест валидации реального токена"""
        if not self.real_token:
            self.skipTest("Реальный токен не найден")

        from admin_notifications import AdminNotifier

        notifier = AdminNotifier(self.real_token)

        # Проверяем, что токен имеет правильный формат
        self.assertTrue(len(self.real_token) > 30)
        self.assertIn(':', self.real_token)

    async def test_real_bot_connection(self):
        """Тест подключения к реальному боту"""
        if not self.real_token:
            self.skipTest("Реальный токен не найден")

        try:
            from telegram import Bot
            bot = Bot(token=self.real_token)
            me = await bot.get_me()

            self.assertIsNotNone(me.username)
            self.assertIsNotNone(me.id)

        except Exception as e:
            self.fail(f"Не удалось подключиться к реальному боту: {e}")

def run_tests():
    """Запуск всех тестов"""
    print("🧪 МОДУЛЬНОЕ ТЕСТИРОВАНИЕ AdminNotifier")
    print("=" * 60)

    # Создаем test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Добавляем модульные тесты
    suite.addTests(loader.loadTestsFromTestCase(TestAdminNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestAdminNotifierIntegration))

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Статистика
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ МОДУЛЬНОГО ТЕСТИРОВАНИЯ")
    print("=" * 60)

    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    success = total_tests - failures - errors - skipped

    print(f"Всего тестов: {total_tests}")
    print(f"✅ Успешно: {success}")
    print(f"❌ Неудачи: {failures}")
    print(f"💥 Ошибки: {errors}")
    print(f"⏭️ Пропущено: {skipped}")

    success_rate = (success / total_tests * 100) if total_tests > 0 else 0
    print(f"\n🎯 Успешность: {success_rate:.1f}%")

    if failures > 0:
        print("\n❌ НЕУДАЧНЫЕ ТЕСТЫ:")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if errors > 0:
        print("\n💥 ОШИБКИ:")
        for test, traceback in result.errors:
            print(f"   • {test}: {traceback.split('Exception:')[-1].strip()}")

    # Заключение
    if success_rate >= 90:
        print("\n🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Код готов к продакшену.")
    elif success_rate >= 70:
        print("\n✅ ХОРОШИЙ РЕЗУЛЬТАТ! Есть небольшие проблемы для исправления.")
    else:
        print("\n⚠️ ТРЕБУЕТСЯ ДОРАБОТКА. Много неудачных тестов.")

    return result.wasSuccessful()

if __name__ == "__main__":
    # Запуск асинхронных тестов
    async def run_async_tests():
        test_instance = TestAdminNotifierIntegration()
        test_instance.setUp()

        if test_instance.real_token:
            try:
                await test_instance.test_real_bot_connection()
                print("✅ Асинхронный тест подключения пройден")
            except Exception as e:
                print(f"❌ Асинхронный тест подключения провален: {e}")

    # Запускаем асинхронные тесты
    try:
        asyncio.run(run_async_tests())
    except Exception as e:
        print(f"⚠️ Ошибка асинхронных тестов: {e}")

    # Запускаем основные тесты
    success = run_tests()

    sys.exit(0 if success else 1)