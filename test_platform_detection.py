#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест определения платформы для унифицированного бота
"""

import platform
import os
import sys

# Добавляем путь к проекту для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_platform_detection():
    """Тестирование определения платформы"""
    
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ОПРЕДЕЛЕНИЯ ПЛАТФОРМЫ")
    print("=" * 60)
    
    # Системная информация
    print("\n1. СИСТЕМНАЯ ИНФОРМАЦИЯ:")
    print(f"   - Операционная система: {platform.system()}")
    print(f"   - Версия: {platform.version()}")
    print(f"   - Платформа: {platform.platform()}")
    print(f"   - Архитектура: {platform.machine()}")
    print(f"   - Python версия: {platform.python_version()}")
    
    # Проверка Docker
    print("\n2. ПРОВЕРКА DOCKER:")
    is_docker = os.path.exists('/.dockerenv')
    print(f"   - Docker контейнер: {'Да' if is_docker else 'Нет'}")
    
    # Импортируем конфигурации из унифицированного файла
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'telegram-bot'))
    from main_unified import get_platform_config, WindowsConfig, UnixConfig, DockerConfig
    
    # Получаем конфигурацию
    print("\n3. АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ:")
    config = get_platform_config()
    config_type = type(config).__name__
    print(f"   - Выбрана конфигурация: {config_type}")
    
    # Детали конфигурации
    print("\n4. ПАРАМЕТРЫ КОНФИГУРАЦИИ:")
    print(f"   - Базовый путь: {config.base_path}")
    print(f"   - Путь к логам: {config.log_path}")
    print(f"   - Путь к .env: {config.env_path}")
    print(f"   - Использовать emoji: {config.use_emoji}")
    
    # Проверка существования путей
    print("\n5. ПРОВЕРКА ПУТЕЙ:")
    print(f"   - Базовый путь существует: {os.path.exists(config.base_path)}")
    print(f"   - Файл .env существует: {os.path.exists(config.env_path)}")
    
    # Проверка создания директорий
    print("\n6. СОЗДАНИЕ ДИРЕКТОРИЙ:")
    try:
        config.ensure_directories()
        print("   - Директории созданы/проверены успешно")
        
        log_dir = os.path.dirname(config.log_path)
        print(f"   - Директория логов: {log_dir}")
        print(f"   - Директория логов существует: {os.path.exists(log_dir)}")
    except Exception as e:
        print(f"   - Ошибка создания директорий: {e}")
    
    # Проверка переменных окружения
    print("\n7. ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    env_vars = [
        'GRANTSERVICE_BASE_PATH',
        'TELEGRAM_BOT_TOKEN',
        'N8N_WEBHOOK_URL',
        'GIGACHAT_API_KEY',
        'ENABLE_EMOJI'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Скрываем часть токенов для безопасности
            if 'TOKEN' in var or 'KEY' in var:
                display_value = value[:10] + '...' if len(value) > 10 else value
            else:
                display_value = value
            print(f"   - {var}: {display_value}")
        else:
            print(f"   - {var}: не установлена")
    
    # Тест загрузки переменных окружения
    print("\n8. ЗАГРУЗКА .ENV ФАЙЛА:")
    if config.load_environment():
        print("   - Переменные окружения загружены успешно")
        # Проверяем загруженные переменные
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if token:
            print(f"   - TELEGRAM_BOT_TOKEN загружен: {token[:10]}...")
    else:
        print("   - Файл .env не найден или не загружен")
    
    # Тест форматирования сообщений
    print("\n9. ФОРМАТИРОВАНИЕ СООБЩЕНИЙ:")
    test_messages = [
        ("Успешно", "✅"),
        ("Ошибка", "❌"),
        ("Информация", "ℹ️"),
        ("Предупреждение", "⚠️")
    ]
    
    for msg, emoji in test_messages:
        formatted = config.format_log_message(msg, emoji)
        print(f"   - {formatted}")
    
    # Рекомендации
    print("\n10. РЕКОМЕНДАЦИИ:")
    system = platform.system()
    
    if system == 'Windows':
        print("   - Система: Windows")
        print("   - Используйте start_bot_windows.bat для запуска")
        print("   - Убедитесь, что путь C:\\SnowWhiteAI\\GrantService существует")
        print("   - Для emoji в консоли установите ENABLE_EMOJI=true")
        
    elif system == 'Linux':
        print("   - Система: Linux")
        print("   - Используйте systemctl или start_bot.sh для запуска")
        print("   - Убедитесь, что путь /var/GrantService существует")
        print("   - Проверьте права доступа к директориям")
        
    elif system == 'Darwin':
        print("   - Система: macOS")
        print("   - Используйте start_bot.sh для запуска")
        print("   - Убедитесь, что путь /var/GrantService существует")
        
    else:
        print(f"   - Неизвестная система: {system}")
        print("   - Используется конфигурация Unix по умолчанию")
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)

if __name__ == "__main__":
    test_platform_detection()