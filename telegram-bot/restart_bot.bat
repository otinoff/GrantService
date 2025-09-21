@echo off
echo =====================================
echo   GrantService Telegram Bot Restart
echo =====================================
echo.

:: Переходим в директорию telegram-bot
cd /d "C:\SnowWhiteAI\GrantService\telegram-bot"

:: Останавливаем существующие процессы Python (бота)
echo [1/4] Stopping existing bot processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq GrantService Bot*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *main.py*" 2>nul
timeout /t 2 /nobreak >nul

:: Активируем виртуальное окружение
echo [2/4] Activating virtual environment...
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate
    echo Virtual environment activated: ..\venv
) else if exist "..\.venv\Scripts\activate.bat" (
    call ..\.venv\Scripts\activate
    echo Virtual environment activated: ..\.venv
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
    echo Virtual environment activated: venv
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate
    echo Virtual environment activated: .venv
) else (
    echo WARNING: Virtual environment not found!
    echo Continuing with system Python...
)

:: Проверяем версию Python
echo.
echo [3/4] Checking Python version...
python --version

:: Запускаем бота
echo.
echo [4/4] Starting Telegram bot...
echo =====================================
echo Bot is starting...
echo Press Ctrl+C to stop the bot
echo =====================================
echo.

:: Запускаем main.py
python main.py

:: Если бот остановлен
echo.
echo =====================================
echo Bot has been stopped.
echo =====================================
pause