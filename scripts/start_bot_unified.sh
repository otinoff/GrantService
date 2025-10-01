#!/bin/bash

echo "========================================"
echo "GrantService Telegram Bot - Unified"
echo "========================================"
echo ""

# Определение базового пути в зависимости от системы
if [ -d "/var/GrantService" ]; then
    BASE_PATH="/var/GrantService"
elif [ -d "$HOME/GrantService" ]; then
    BASE_PATH="$HOME/GrantService"
else
    BASE_PATH="$(dirname "$(readlink -f "$0")")"
fi

echo "Using base path: $BASE_PATH"
cd "$BASE_PATH" || exit 1

# Проверка наличия файла конфигурации
if [ ! -f "config/.env" ]; then
    if [ -f "config/config.env" ]; then
        echo "Using config/config.env"
        cp config/config.env config/.env
    else
        echo "[ERROR] Configuration file not found!"
        echo "Create config/.env file with parameters:"
        echo "  TELEGRAM_BOT_TOKEN=your_bot_token"
        echo "  N8N_WEBHOOK_URL=webhook_url"
        echo "  GIGACHAT_API_KEY=api_key"
        exit 1
    fi
fi

# Создание директории для логов если не существует
if [ ! -d "logs" ]; then
    mkdir -p logs
fi

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found!"
    echo "Install Python 3.8+ and add it to PATH"
    exit 1
fi

# Активация виртуального окружения если существует
if [ -f "venv/bin/activate" ]; then
    echo "[1/3] Activating virtual environment..."
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    echo "[1/3] Activating virtual environment..."
    source .venv/bin/activate
else
    echo "[1/3] No virtual environment found, using system Python"
fi

# Установка зависимостей
echo "[2/3] Checking dependencies..."
pip3 install -q -r telegram-bot/requirements.txt 2>/dev/null || {
    echo "[WARNING] Failed to install all dependencies"
    echo "Trying to continue..."
}

# Остановка старого процесса бота (если запущен)
echo "[3/3] Stopping old processes..."
pkill -f "main_unified.py" 2>/dev/null || true
pkill -f "main.py" 2>/dev/null || true
sleep 2

# Запуск единого бота
echo "[3/3] Starting unified bot..."
echo "========================================"
echo "Platform will be detected automatically"
echo "========================================"
echo ""

# Запуск с обработкой сигналов для корректной остановки
python3 telegram-bot/main.py

echo ""
echo "========================================"
echo "Bot stopped."