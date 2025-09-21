# Руководство по перезапуску Telegram бота GrantService

## Быстрый запуск

### Вариант 1: Простой перезапуск (Windows)
```bash
# Откройте командную строку или проводник
# Перейдите в папку C:\SnowWhiteAI\GrantService
# Запустите один из файлов:

restart_bot.bat         # С виртуальным окружением (рекомендуется)
quick_restart_bot.bat   # Быстрый запуск без venv
restart_bot.ps1         # PowerShell версия (более надежная)
```

### Вариант 2: Ручной запуск
```bash
cd C:\SnowWhiteAI\GrantService
python telegram-bot\main.py
```

### Вариант 3: С виртуальным окружением
```bash
cd C:\SnowWhiteAI\GrantService\telegram-bot

# Активация виртуального окружения
venv\Scripts\activate

# Запуск бота
python main.py
```

## Проверка работы deep linking

После перезапуска бота проверьте работу deep linking:

1. **Запустите тестовый скрипт:**
   ```bash
   cd C:\SnowWhiteAI\GrantService
   python test_deep_link.py
   ```

2. **Перейдите по ссылке:**
   ```
   https://t.me/GrantServiceHelperBot?start=get_access
   ```

3. **Проверьте логи бота:**
   - Должно появиться сообщение: "Deep link /start get_access от пользователя ..."
   - Должен сгенерироваться токен автоматически

## Структура команд бота

### Команды для пользователей:
- `/start` - Главное меню
- `/start get_access` - Deep link для автоматической генерации токена
- `/get_access` - Получить токен доступа к админ-панели
- `/revoke_access` - Отозвать токен доступа
- `/my_access` - Информация о текущем доступе

### Команды для админов:
- `/admin` - Получить админскую ссылку (устаревшая)
- `/login` - Псевдоним для /get_access

## Решение проблем

### Проблема: "Deep link не работает"
**Решение:**
1. Убедитесь, что бот перезапущен после изменений
2. Проверьте логи на наличие ошибок
3. Убедитесь, что используется правильное имя бота: @GrantServiceHelperBot

### Проблема: "Токен не генерируется"
**Решение:**
1. Проверьте подключение к базе данных
2. Убедитесь, что файл config/.env содержит все необходимые переменные
3. Проверьте логи на наличие ошибок импорта модулей

### Проблема: "Виртуальное окружение не активируется"
**Решение:**
1. Создайте новое виртуальное окружение:
   ```bash
   cd C:\SnowWhiteAI\GrantService\telegram-bot
   python -m venv venv
   venv\Scripts\activate
   pip install python-telegram-bot requests python-dotenv
   ```

## Логи бота

Логи сохраняются в файле:
```
C:\SnowWhiteAI\GrantService\logs\telegram_bot.log
```

Для просмотра логов в реальном времени:
```bash
# PowerShell
Get-Content C:\SnowWhiteAI\GrantService\logs\telegram_bot.log -Wait

# Или просто откройте файл в текстовом редакторе
```

## Проверка статуса

1. **Проверить, запущен ли бот:**
   ```bash
   # PowerShell
   Get-Process python | Where-Object {$_.MainWindowTitle -like "*GrantService*"}
   ```

2. **Проверить работу через Telegram:**
   - Откройте @GrantServiceHelperBot
   - Отправьте команду /start
   - Бот должен ответить главным меню

## Автоматический перезапуск

Для автоматического перезапуска при сбоях можно использовать планировщик задач Windows:

1. Откройте Планировщик задач
2. Создайте новую задачу
3. Триггер: При входе в систему или по расписанию
4. Действие: Запустить программу
   - Программа: `C:\SnowWhiteAI\GrantService\restart_bot.bat`
   - Рабочая папка: `C:\SnowWhiteAI\GrantService`

## Контакты поддержки

При возникновении проблем обращайтесь:
- Telegram: @otinoff_support
- Email: otinoff@gmail.com