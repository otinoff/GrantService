#!/bin/bash
# Скрипт для настройки токена Telegram бота
# Использование: bash setup_bot_token.sh YOUR_BOT_TOKEN

if [ -z "$1" ]; then
    echo "❌ Ошибка: не указан токен бота"
    echo ""
    echo "Использование:"
    echo "  bash setup_bot_token.sh YOUR_BOT_TOKEN"
    echo ""
    echo "Пример:"
    echo "  bash setup_bot_token.sh 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    echo ""
    exit 1
fi

TOKEN=$1
ENV_FILE="/var/GrantService/config/.env"

echo "========================================"
echo "  Setup Telegram Bot Token"
echo "========================================"
echo ""

# Создаем директорию если не существует
mkdir -p /var/GrantService/config

# Создаем .env файл
cat > $ENV_FILE <<EOF
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=$TOKEN

# n8n Configuration
N8N_WEBHOOK_URL=http://localhost:5678/webhook/grant-service

# GigaChat API Configuration (опционально)
# GIGACHAT_API_KEY=your_key_here
EOF

echo "✅ Файл $ENV_FILE создан"
echo ""

# Устанавливаем права доступа
chmod 600 $ENV_FILE
echo "✅ Права доступа установлены (600)"
echo ""

# Показываем содержимое (маскируем токен)
echo "📄 Содержимое файла:"
cat $ENV_FILE | sed "s/$TOKEN/***HIDDEN***/g"
echo ""

# Проверяем токен
echo "🔍 Проверка токена через Telegram API..."
response=$(curl -s "https://api.telegram.org/bot$TOKEN/getMe")

if echo "$response" | grep -q '"ok":true'; then
    bot_username=$(echo "$response" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Токен валиден! Бот: @$bot_username"
else
    echo "⚠️  Не удалось проверить токен. Проверьте его вручную."
fi
echo ""

# Перезапускаем бота
echo "🔄 Перезапуск бота..."
systemctl restart grantservice-bot

sleep 3

# Проверяем статус
if systemctl is-active --quiet grantservice-bot; then
    echo "✅ Бот успешно запущен!"
    echo ""
    echo "Проверьте логи:"
    echo "  journalctl -u grantservice-bot -n 20 -f"
else
    echo "❌ Бот не запустился. Проверьте логи:"
    echo "  journalctl -u grantservice-bot -n 50"
fi

echo ""
echo "========================================"
echo "  Готово!"
echo "========================================"
