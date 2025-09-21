# Миграция на унифицированный бот

## Обзор

Мы успешно объединили два файла (`main.py` для Linux и `main_windows.py` для Windows) в один унифицированный файл `main_unified.py`, который автоматически определяет платформу и использует соответствующие настройки.

## Что изменилось

### 1. Новая архитектура

```
До миграции:
├── telegram-bot/
│   ├── main.py          (Linux версия)
│   └── main_windows.py  (Windows версия)

После миграции:
├── telegram-bot/
│   ├── main_unified.py  (Универсальная версия)
│   ├── main.py          (устаревшая, будет удалена)
│   └── main_windows.py  (устаревшая, будет удалена)
```

### 2. Автоматическое определение платформы

Новый бот автоматически определяет операционную систему и выбирает соответствующую конфигурацию:

- **Windows** → `WindowsConfig`
- **Linux** → `UnixConfig`
- **macOS** → `UnixConfig`
- **Docker** → `DockerConfig`

### 3. Платформозависимые настройки

| Параметр | Windows | Linux/Unix | Docker |
|----------|---------|------------|--------|
| Базовый путь | `C:\SnowWhiteAI\GrantService` | `/var/GrantService` | `/app` |
| Кодировка логов | UTF-8 | По умолчанию | По умолчанию |
| Emoji в логах | Отключены (можно включить) | Включены | Включены |
| Загрузка .env | Автоматическая | Опциональная | Опциональная |

## Инструкция по миграции

### Шаг 1: Резервное копирование

Перед миграцией создайте резервные копии:

```bash
# Linux/Unix
cp telegram-bot/main.py telegram-bot/main.backup.py

# Windows
copy telegram-bot\main_windows.py telegram-bot\main_windows.backup.py
```

### Шаг 2: Остановка текущего бота

#### Windows
```cmd
taskkill /IM python.exe /F
```

#### Linux
```bash
pkill -f "main.py"
# или
systemctl stop grantservice-bot
```

### Шаг 3: Обновление файлов

1. Убедитесь, что `main_unified.py` находится в директории `telegram-bot/`
2. Проверьте наличие новых скриптов запуска:
   - `start_bot_unified.bat` (Windows)
   - `start_bot_unified.sh` (Linux/Unix)

### Шаг 4: Тестирование

#### Тест определения платформы
```bash
# Windows
python test_platform_detection.py

# Linux
python3 test_platform_detection.py
```

Убедитесь, что система правильно определяет вашу платформу.

### Шаг 5: Запуск унифицированного бота

#### Windows
```cmd
cd C:\SnowWhiteAI\GrantService
start_bot_unified.bat
```

#### Linux
```bash
cd /var/GrantService
chmod +x start_bot_unified.sh
./start_bot_unified.sh
```

### Шаг 6: Проверка работы

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте команду `/start`
4. Убедитесь, что меню отображается корректно

## Переменные окружения

### Обязательные переменные

Создайте файл `config/.env` со следующими параметрами:

```env
# Токен Telegram бота
TELEGRAM_BOT_TOKEN=your_bot_token

# URL webhook для n8n
N8N_WEBHOOK_URL=http://localhost:5678/webhook/grant-service

# API ключ GigaChat
GIGACHAT_API_KEY=your_api_key
```

### Опциональные переменные

```env
# Переопределение базового пути (опционально)
GRANTSERVICE_BASE_PATH=/custom/path/to/GrantService

# Включить emoji в консоли Windows (по умолчанию false)
ENABLE_EMOJI=true

# Путь к приложению в Docker
APP_PATH=/app
```

## Systemd сервис для Linux

Обновите файл сервиса для использования унифицированного бота:

```ini
[Unit]
Description=GrantService Telegram Bot
After=network.target

[Service]
Type=simple
User=grant
WorkingDirectory=/var/GrantService
ExecStart=/usr/bin/python3 /var/GrantService/telegram-bot/main_unified.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Примените изменения:
```bash
sudo systemctl daemon-reload
sudo systemctl restart grantservice-bot
```

## Docker поддержка

### Dockerfile

```dockerfile
FROM python:3.9-slim

# Установка переменной для Docker конфигурации
ENV APP_PATH=/app

WORKDIR /app

# Копирование файлов проекта
COPY . .

# Установка зависимостей
RUN pip install -r telegram-bot/requirements.txt

# Запуск унифицированного бота
CMD ["python", "telegram-bot/main_unified.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  telegram-bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - N8N_WEBHOOK_URL=${N8N_WEBHOOK_URL}
      - GIGACHAT_API_KEY=${GIGACHAT_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
```

## Возможные проблемы и решения

### Проблема 1: ModuleNotFoundError

**Симптом**: Ошибка импорта модулей БД

**Решение**: Убедитесь, что путь к проекту добавлен в PYTHONPATH или запускайте из корневой директории проекта.

### Проблема 2: Emoji не отображаются в Windows

**Симптом**: Вместо emoji отображаются квадраты или вопросительные знаки

**Решение**: 
1. Установите `ENABLE_EMOJI=false` в .env файле
2. Или используйте Windows Terminal вместо cmd.exe

### Проблема 3: Права доступа в Linux

**Симптом**: Permission denied при создании логов

**Решение**:
```bash
sudo chown -R grant:grant /var/GrantService
sudo chmod -R 755 /var/GrantService
```

### Проблема 4: Бот не находит конфигурацию

**Симптом**: TELEGRAM_BOT_TOKEN не установлен

**Решение**: Проверьте наличие и путь к файлу `config/.env`

## Откат изменений

Если необходимо вернуться к старой версии:

### Windows
```cmd
cd C:\SnowWhiteAI\GrantService\telegram-bot
copy main_windows.backup.py main_windows.py
cd ..
start_bot_windows.bat
```

### Linux
```bash
cd /var/GrantService/telegram-bot
cp main.backup.py main.py
cd ..
./start_bot.sh
```

## Удаление старых файлов

После успешного тестирования унифицированного бота в течение нескольких дней, можно удалить старые файлы:

```bash
# Создайте архив перед удалением
tar -czf old_bot_files.tar.gz telegram-bot/main.py telegram-bot/main_windows.py

# Удалите старые файлы
rm telegram-bot/main.py
rm telegram-bot/main_windows.py
rm start_bot_windows.bat
rm start_bot.sh
```

## Преимущества унифицированного подхода

1. **Упрощение поддержки**: Один файл вместо двух
2. **Автоматическое определение платформы**: Не нужно выбирать версию вручную
3. **Гибкость**: Легко добавить поддержку новых платформ
4. **Консистентность**: Все изменения применяются сразу для всех платформ
5. **Переносимость**: Один и тот же код работает везде
6. **Docker-ready**: Встроенная поддержка контейнеризации

## Контрольный чек-лист миграции

- [ ] Создан резервный бэкап старых файлов
- [ ] Остановлен текущий бот
- [ ] Скопирован `main_unified.py` в `telegram-bot/`
- [ ] Обновлены скрипты запуска
- [ ] Проверена конфигурация .env
- [ ] Протестировано определение платформы
- [ ] Запущен унифицированный бот
- [ ] Проверена работа основных функций
- [ ] Обновлен systemd сервис (для Linux)
- [ ] Документирована миграция в логах

## Поддержка

При возникновении проблем:
1. Проверьте логи в `logs/telegram_bot.log`
2. Запустите `test_platform_detection.py`
3. Убедитесь в правильности переменных окружения
4. Обратитесь к резервным копиям при необходимости