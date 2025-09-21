# План объединения main.py и main_windows.py

## Цель
Создать единый файл `main.py`, который будет автоматически определять операционную систему и использовать соответствующие настройки.

## Архитектурное решение

### 1. Определение платформы
```python
import platform
import sys

def get_platform_config():
    """Получить конфигурацию в зависимости от платформы"""
    system = platform.system()
    
    if system == 'Windows':
        return WindowsConfig()
    elif system in ['Linux', 'Darwin']:  # Darwin для macOS
        return UnixConfig()
    else:
        raise NotImplementedError(f"Платформа {system} не поддерживается")
```

### 2. Класс конфигурации
```python
class PlatformConfig:
    """Базовый класс для платформозависимой конфигурации"""
    
    @property
    def base_path(self):
        raise NotImplementedError
    
    @property
    def log_path(self):
        raise NotImplementedError
    
    @property
    def env_path(self):
        raise NotImplementedError
    
    def setup_logging(self):
        raise NotImplementedError
    
    def load_environment(self):
        raise NotImplementedError
```

### 3. Реализация для Windows
```python
class WindowsConfig(PlatformConfig):
    @property
    def base_path(self):
        return 'C:\\SnowWhiteAI\\GrantService'
    
    @property
    def log_path(self):
        return os.path.join(self.base_path, 'logs', 'telegram_bot.log')
    
    @property
    def env_path(self):
        return os.path.join(self.base_path, 'config', '.env')
    
    def setup_logging(self):
        log_dir = os.path.dirname(self.log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO,
            handlers=[
                logging.FileHandler(self.log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
```

### 4. Реализация для Linux/Unix
```python
class UnixConfig(PlatformConfig):
    @property
    def base_path(self):
        return '/var/GrantService'
    
    @property
    def log_path(self):
        return os.path.join(self.base_path, 'logs', 'telegram_bot.log')
    
    @property
    def env_path(self):
        # На Unix системах обычно используются системные переменные
        # Но можем также проверить локальный .env
        local_env = os.path.join(self.base_path, 'config', '.env')
        if os.path.exists(local_env):
            return local_env
        return None
    
    def setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO,
            handlers=[
                logging.FileHandler(self.log_path),
                logging.StreamHandler()
            ]
        )
```

## Преимущества единого файла

### 1. **Упрощение поддержки**
- Один файл вместо двух
- Изменения применяются сразу для всех платформ
- Меньше дублирования кода

### 2. **Гибкость**
- Легко добавить поддержку новых платформ (macOS, Docker)
- Централизованное управление конфигурацией
- Возможность переопределения через переменные окружения

### 3. **Тестирование**
- Проще тестировать один файл
- Можно мокировать платформозависимые части
- CI/CD упрощается

## Этапы реализации

### Этап 1: Создание базовой структуры
1. Создать класс `PlatformConfig`
2. Реализовать `WindowsConfig` и `UnixConfig`
3. Добавить функцию определения платформы

### Этап 2: Интеграция в бота
1. Модифицировать `GrantServiceBotWithMenu.__init__()`
2. Использовать конфигурацию для путей
3. Адаптировать логирование

### Этап 3: Обработка emoji
```python
class PlatformConfig:
    @property
    def use_emoji(self):
        """Использовать ли emoji в логах"""
        return True
    
    def format_log_message(self, message, emoji=None):
        """Форматировать сообщение лога с учетом платформы"""
        if self.use_emoji and emoji:
            return f"{emoji} {message}"
        return message

class WindowsConfig(PlatformConfig):
    @property
    def use_emoji(self):
        # Windows консоль может не поддерживать emoji
        return os.environ.get('ENABLE_EMOJI', 'false').lower() == 'true'
```

### Этап 4: Тестирование
1. Тестирование на Windows 10/11
2. Тестирование на Ubuntu 20.04/22.04
3. Тестирование в Docker контейнере
4. Проверка автозапуска

### Этап 5: Миграция
1. Создать резервные копии существующих файлов
2. Развернуть единый файл
3. Обновить скрипты запуска
4. Обновить документацию

## Дополнительные улучшения

### 1. Переменные окружения для переопределения
```python
# Позволяем переопределить пути через переменные окружения
BASE_PATH = os.environ.get('GRANTSERVICE_BASE_PATH')
LOG_PATH = os.environ.get('GRANTSERVICE_LOG_PATH')
```

### 2. Docker поддержка
```python
class DockerConfig(UnixConfig):
    @property
    def base_path(self):
        return os.environ.get('APP_PATH', '/app')
```

### 3. Автоматическое создание директорий
```python
def ensure_directories(self):
    """Создать необходимые директории если их нет"""
    dirs = [
        os.path.dirname(self.log_path),
        os.path.join(self.base_path, 'data'),
        os.path.join(self.base_path, 'config')
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
```

## Конфигурация запуска

### Единый скрипт запуска (start_bot.py)
```python
#!/usr/bin/env python3
"""Универсальный запуск бота на любой платформе"""

import sys
import os

# Добавляем путь к проекту
if sys.platform == 'win32':
    sys.path.insert(0, 'C:\\SnowWhiteAI\\GrantService')
else:
    sys.path.insert(0, '/var/GrantService')

from telegram_bot.main import GrantServiceBotWithMenu

if __name__ == "__main__":
    bot = GrantServiceBotWithMenu()
    bot.run()
```

### Bash скрипт для Linux (start_bot.sh)
```bash
#!/bin/bash
cd /var/GrantService
source venv/bin/activate 2>/dev/null || true
python3 telegram-bot/main.py
```

### Batch скрипт для Windows (start_bot.bat)
```batch
@echo off
cd /d C:\SnowWhiteAI\GrantService
python telegram-bot\main.py
pause
```

## Риски и их митигация

| Риск | Вероятность | Воздействие | Митигация |
|------|-------------|-------------|-----------|
| Различия в поведении на разных ОС | Средняя | Высокое | Тщательное тестирование |
| Проблемы с путями | Низкая | Среднее | Использование os.path.join |
| Кодировка файлов | Средняя | Низкое | Явное указание UTF-8 |
| Права доступа | Низкая | Высокое | Проверка прав при старте |

## Метрики успеха

1. ✅ Один файл работает на обеих платформах
2. ✅ Сохранена вся функциональность
3. ✅ Упрощена поддержка кода
4. ✅ Улучшена читаемость
5. ✅ Добавлена поддержка новых платформ

## Временная оценка

- Разработка: 2-3 часа
- Тестирование: 2-3 часа
- Документация: 1 час
- Развертывание: 1 час

**Итого: 6-8 часов**

## Следующие шаги

1. Обсудить план с командой
2. Создать ветку `feature/unified-bot`
3. Реализовать единый файл
4. Провести тестирование
5. Слить в основную ветку