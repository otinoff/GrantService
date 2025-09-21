@echo off
echo ========================================
echo    Перезапуск Telegram бота GrantService
echo ========================================
echo.

REM Переходим в директорию бота
cd /d C:\SnowWhiteAI\GrantService

REM Проверяем наличие виртуального окружения
if not exist "telegram-bot\venv" (
    echo [ERROR] Виртуальное окружение не найдено!
    echo Создаем виртуальное окружение...
    python -m venv telegram-bot\venv
    echo Виртуальное окружение создано.
    echo.
)

echo [1] Активируем виртуальное окружение...
call telegram-bot\venv\Scripts\activate.bat

echo.
echo [2] Обновляем зависимости...
pip install --upgrade pip >nul 2>&1
pip install python-telegram-bot requests python-dotenv >nul 2>&1

echo.
echo [3] Проверяем переменные окружения...
if not exist "config\.env" (
    echo [WARNING] Файл config\.env не найден!
    echo Используйте config\.env.example как шаблон
    pause
    exit /b 1
)

echo.
echo [4] Останавливаем старый процесс бота (если запущен)...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq GrantService Bot*" >nul 2>&1

echo.
echo [5] Запускаем бота...
echo ========================================
echo.

REM Запускаем бота
python telegram-bot\main.py

echo.
echo ========================================
echo Бот остановлен.
pause