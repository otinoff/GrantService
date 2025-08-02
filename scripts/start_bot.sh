#!/bin/bash

# ГрантСервис - Скрипт запуска Telegram бота

echo "🚀 Запуск ГрантСервис Telegram Bot..."

# Переход в директорию проекта
cd /var/GrantService

# Проверка существования .env файла
if [ ! -f "config/.env" ]; then
    echo "❌ Файл config/.env не найден!"
    echo "Скопируйте config/config.env.template в config/.env и заполните переменные"
    exit 1
fi

# Загрузка переменных окружения
export $(cat config/.env | grep -v '#' | xargs)

# Проверка обязательных переменных
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не установлен в .env файле!"
    exit 1
fi

# Создание директории логов если не существует
mkdir -p logs

# Установка зависимостей
echo "📦 Проверка зависимостей..."
pip3 install -r telegram-bot/requirements.txt

# Запуск бота
echo "🤖 Запуск бота..."
cd telegram-bot
python3 main.py

echo "✅ Бот запущен!" 