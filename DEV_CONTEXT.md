# 🔴 ВАЖНО: КОНТЕКСТ РАЗРАБОТКИ

## Окружения и боты

### 🛠️ DEV (Разработка)
- **Платформа**: Windows 10
- **Путь**: C:\SnowWhiteAI\GrantService
- **Бот**: @Grafana_SnowWhite_bot
- **Токен**: Используется из config/.env
- **База данных**: Локальная SQLite

### 🚀 PROD (Продакшн)
- **Платформа**: Linux VPS
- **Путь**: /var/GrantService
- **Бот**: @GrantServiceHelperBot
- **База данных**: Продакшн SQLite

## ⚠️ ВНИМАНИЕ ПРИ ТЕСТИРОВАНИИ

**НЕ ПУТАЙТЕ БОТОВ!**

### Для тестирования изменений на Windows:
✅ ПРАВИЛЬНАЯ ссылка для DEV:
```
https://t.me/Grafana_SnowWhite_bot?start=get_access
```

❌ НЕПРАВИЛЬНАЯ ссылка (это PROD):
```
https://t.me/GrantServiceHelperBot?start=get_access
```

## Команды для тестирования в DEV боте

1. **Запустите DEV бота на Windows:**
   ```bash
   cd C:\SnowWhiteAI\GrantService
   python telegram-bot\main.py
   ```

2. **Откройте DEV бота в Telegram:**
   @Grafana_SnowWhite_bot

3. **Проверьте команды:**
   - `/start` - главное меню
   - `/get_access` - получить токен
   - `/my_access` - информация о доступе
   - `/revoke_access` - отозвать токен

4. **Проверьте deep link:**
   ```
   https://t.me/Grafana_SnowWhite_bot?start=get_access
   ```

## Структура проекта

```
GrantService/
├── telegram-bot/
│   └── main.py          # Основной файл бота
├── data/
│   └── database/        # Модули БД
├── config/
│   └── .env            # Переменные окружения
├── logs/
│   └── telegram_bot.log # Логи
└── scripts/            # Вспомогательные скрипты
```

## Деплой на продакшн

**ВАЖНО**: Перед деплоем на продакшн:
1. Протестируйте все изменения на DEV боте
2. Убедитесь что используете правильный токен в .env
3. Проверьте совместимость с Linux окружением

## Частые ошибки

### Ошибка: "Deep link не работает"
**Причина**: Тестируете на PROD боте вместо DEV
**Решение**: Используйте @Grafana_SnowWhite_bot

### Ошибка: "Токен не генерируется"
**Причина**: БД не инициализирована или нет прав
**Решение**: Проверьте наличие файла grant_service.db

## Контакты

- **Разработка**: Тестируйте на @Grafana_SnowWhite_bot
- **Продакшн**: @GrantServiceHelperBot
- **Поддержка**: @otinoff_support