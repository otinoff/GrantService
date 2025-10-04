# 🎯 Установка Telegram бота с интерактивным меню

## ⚠️ ВАЖНО: Использование systemd сервиса

**ВНИМАНИЕ:** Бот должен запускаться через systemd сервис `grantservice-bot`, а не напрямую через Python!

```bash
# Правильно - через сервис:
sudo systemctl start grantservice-bot
sudo systemctl status grantservice-bot

# Неправильно - напрямую:
python main.py  # Только для тестирования!
```

## 📋 Описание функциональности

Новая версия бота включает интерактивное меню с тремя экранами:

### **Экран 1 - Главное меню:**
- 📝 **Начать заполнение** → переход к вопросам
- 💳 **Оплата** → ссылка на сервис оплаты  
- 📊 **Статус заявки** → прогресс заполнения
- ℹ️ **О Грантсервисе** → информация о сервисе

### **Экран 2 - Навигация по вопросам:**
- ⬅️ **Назад** → предыдущий вопрос
- **Вперёд ➡️** → следующий вопрос
- 🏠 **Вернуться в меню** → главное меню

### **Экран 3 - Проверка и отправка:**
- ✅ **Отправить на проверку** → финальная отправка
- ⬅️ **Назад** → к последнему вопросу
- 🏠 **Вернуться в меню** → главное меню

## 🚀 Установка

### 1. Остановите текущий бот
```bash
cd /var/GrantService/telegram-bot
sudo systemctl stop grantservice-bot
```

### 2. Создайте резервную копию
```bash
cp main.py main_backup.py
```

### 3. Замените основной файл
```bash
cp main_with_menu.py main.py
```

### 4. Проверьте зависимости
```bash
source venv/bin/activate
pip install python-telegram-bot requests
```

### 5. Настройте переменные окружения
```bash
# В файле /var/GrantService/config/config.env
export TELEGRAM_BOT_TOKEN="ваш_токен_бота"
export N8N_WEBHOOK_URL="http://localhost:5678/webhook/grant-service"
export GIGACHAT_API_KEY="ваш_ключ_gigachat"
```

### 6. Запустите бота
```bash
# ВАЖНО: Используйте systemd сервис для запуска!
sudo systemctl start grantservice-bot
sudo systemctl status grantservice-bot

# Для тестирования можно запустить напрямую:
cd /var/GrantService/telegram-bot
source venv/bin/activate
python main.py
```

## 🔧 Настройка

### Переменные окружения
```bash
# Создайте файл .env в папке telegram-bot
TELEGRAM_BOT_TOKEN=ваш_токен_бота
N8N_WEBHOOK_URL=http://localhost:5678/webhook/grant-service
GIGACHAT_API_KEY=ваш_ключ_gigachat
```

### Systemd сервис
```bash
# Обновите файл /etc/systemd/system/grantservice-bot.service
[Unit]
Description=GrantService Telegram Bot with Menu
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/GrantService/telegram-bot
Environment=PATH=/var/GrantService/telegram-bot/venv/bin
ExecStart=/var/GrantService/telegram-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🧪 Тестирование

### 1. Запустите бота
```bash
cd /var/GrantService/telegram-bot
source venv/bin/activate
python main.py
```

### 2. Отправьте команду /start в Telegram
Бот должен показать главное меню с 4 кнопками.

### 3. Протестируйте навигацию
- Нажмите "Начать заполнение"
- Проверьте переходы между вопросами
- Убедитесь, что ответы сохраняются

### 4. Проверьте экран отправки
После заполнения всех вопросов должен появиться экран проверки.

## 📊 Логирование

Логи сохраняются в `/var/GrantService/logs/telegram_bot.log`:

```bash
# Просмотр логов в реальном времени
tail -f /var/GrantService/logs/telegram_bot.log

# Поиск ошибок
grep "ERROR" /var/GrantService/logs/telegram_bot.log
```

## 🔄 Откат к старой версии

Если нужно вернуться к старой версии:

```bash
cd /var/GrantService/telegram-bot
cp main_backup.py main.py
sudo systemctl restart grantservice-bot
```

## 🎯 Ключевые особенности

### Состояния пользователя
- `main_menu` - главное меню
- `interviewing` - заполнение вопросов  
- `review` - проверка и отправка

### Валидация ответов
- Проверка типов данных
- Валидация по правилам из БД
- Подсчет прогресса заполнения

### Интеграция с n8n
- Отправка заявок через webhook
- Обработка результатов ИИ
- Генерация PDF документов

## 🚨 Устранение неполадок

### Бот не отвечает
```bash
# Проверьте статус
sudo systemctl status grantservice-bot

# Проверьте токен
echo $TELEGRAM_BOT_TOKEN

# Перезапустите
sudo systemctl restart grantservice-bot
```

### Ошибки в логах
```bash
# Просмотр последних ошибок
tail -n 50 /var/GrantService/logs/telegram_bot.log | grep ERROR
```

### Проблемы с БД
```bash
# Проверьте подключение к БД
cd /var/GrantService/data
python -c "from database import db; print('БД работает')"
```

## 📈 Мониторинг

### Статистика использования
- Количество активных пользователей
- Процент завершения заявок
- Время обработки запросов

### Метрики производительности
- Время ответа бота
- Количество ошибок
- Использование памяти

---

**Готово!** 🎉 Бот с интерактивным меню готов к работе! 