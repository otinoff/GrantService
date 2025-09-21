@echo off
chcp 65001 >nul
echo ========================================
echo GrantService Telegram Bot - Windows
echo ========================================
echo.

REM Переход в директорию проекта
cd /d C:\SnowWhiteAI\GrantService

REM Проверка наличия файла конфигурации
if not exist "config\.env" (
    if exist "config\config.env" (
        echo Используется файл config\config.env
        copy "config\config.env" "config\.env" >nul
    ) else (
        echo [ERROR] Файл конфигурации не найден!
        echo Создайте файл config\.env с параметрами:
        echo   TELEGRAM_BOT_TOKEN=ваш_токен_бота
        echo   N8N_WEBHOOK_URL=адрес_webhook
        echo   GIGACHAT_API_KEY=ключ_api
        pause
        exit /b 1
    )
)

REM Создание папки для логов если не существует
if not exist "logs" mkdir logs

REM Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python не найден!
    echo Установите Python 3.8+ и добавьте его в PATH
    pause
    exit /b 1
)

REM Установка зависимостей
echo [1/3] Проверка зависимостей...
pip install -r telegram-bot\requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Не удалось установить все зависимости
    echo Попытка продолжить...
)

REM Остановка старого процесса бота (если запущен)
echo [2/3] Остановка старых процессов...
REM Останавливаем все процессы Python чтобы избежать конфликта
taskkill /IM python.exe /F >nul 2>&1
timeout /t 2 >nul

REM Запуск бота
echo [3/3] Запуск бота...
echo ========================================
echo.
python telegram-bot\main.py
echo.
echo ========================================
echo Бот остановлен.
pause