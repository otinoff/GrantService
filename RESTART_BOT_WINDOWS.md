# Инструкция по перезапуску Telegram бота в Windows

## Быстрый запуск (рекомендуется)

### Способ 1: Через батник (самый простой)
```cmd
cd C:\SnowWhiteAI\GrantService
start_bot_windows.bat
```

Батник автоматически:
- Остановит старый процесс бота
- Проверит конфигурацию
- Установит зависимости
- Запустит новый процесс

### Способ 2: Напрямую через Python
```cmd
cd C:\SnowWhiteAI\GrantService
python telegram-bot\main_windows.py
```

## Пошаговая инструкция

### 1. Остановка текущего бота

**Вариант А: Найти и завершить процесс**
```cmd
# Посмотреть запущенные процессы Python
tasklist | findstr python

# Завершить процесс по PID (замените 6672 на ваш PID)
taskkill /PID 6672 /F
```

**Вариант Б: Завершить все процессы Python**
```cmd
taskkill /IM python.exe /F
```
⚠️ Осторожно: это завершит ВСЕ Python процессы!

### 2. Проверка конфигурации

Убедитесь, что файл `config\.env` или `config\config.env` содержит:
```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
N8N_WEBHOOK_URL=http://localhost:5678/webhook/grant-service
GIGACHAT_API_KEY=ваш_ключ_api
```

### 3. Запуск бота

**С виртуальным окружением (если есть):**
```cmd
cd C:\SnowWhiteAI
.venv\Scripts\activate
cd GrantService
python telegram-bot\main_windows.py
```

**Без виртуального окружения:**
```cmd
cd C:\SnowWhiteAI\GrantService
python telegram-bot\main_windows.py
```

## Различия между версиями

### main.py (Linux/Ubuntu)
- Использует пути Linux: `/var/GrantService`
- Логи в `/var/GrantService/logs/`
- Предназначен для production сервера

### main_windows.py (Windows)
- Использует Windows пути: `C:\SnowWhiteAI\GrantService`
- Логи в `C:\SnowWhiteAI\GrantService\logs\`
- Автоматически загружает переменные из .env файла
- Адаптирован для локальной разработки

## Проверка работы бота

### 1. Проверка логов
```cmd
type C:\SnowWhiteAI\GrantService\logs\telegram_bot.log
```

### 2. Проверка в Telegram
- Откройте вашего бота в Telegram
- Отправьте команду `/start`
- Должно появиться главное меню

### 3. Проверка процесса
```cmd
tasklist | findstr python
```

## Возможные проблемы

### Ошибка: "No module named 'telegram'"
**Решение:** Установите зависимости
```cmd
cd C:\SnowWhiteAI\GrantService
pip install -r telegram-bot\requirements.txt
```

### Ошибка: "TELEGRAM_BOT_TOKEN не установлен"
**Решение:** Создайте файл `config\.env` с токеном

### Ошибка: "No module named 'data.database'"
**Решение:** Запускайте из корня проекта GrantService

### Ошибка: "FileNotFoundError: logs"
**Решение:** Создайте папку logs
```cmd
mkdir C:\SnowWhiteAI\GrantService\logs
```

## Автозапуск при старте Windows

Создайте ярлык `start_bot_windows.bat` и поместите в:
```
C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

## Команды бота

- `/start` - Главное меню
- `/login` - Получить ссылку для входа в админ панель
- `/admin` - Админская ссылка (для администраторов)

## Мониторинг

Для постоянного мониторинга работы бота используйте PowerShell:
```powershell
Get-Content C:\SnowWhiteAI\GrantService\logs\telegram_bot.log -Wait
```

## Контакты поддержки

При возникновении проблем обращайтесь:
- Telegram: @otinoff_support
- Email: otinoff@gmail.com