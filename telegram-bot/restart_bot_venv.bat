@echo off
echo ========================================
echo   ПЕРЕЗАПУСК TELEGRAM БОТА В VENV
echo ========================================
echo.

REM Переходим в директорию telegram-bot
cd /d C:\SnowWhiteAI\GrantService\telegram-bot

REM Проверяем наличие виртуального окружения
if not exist "venv\" (
    echo [ERROR] Виртуальное окружение не найдено!
    echo.
    echo Создайте виртуальное окружение командой:
    echo python -m venv venv
    echo.
    pause
    exit /b 1
)

echo [1/3] Активируем виртуальное окружение...
call venv\Scripts\activate.bat

echo.
echo [2/3] Обновляем зависимости...
python -m pip install --upgrade pip
pip install python-telegram-bot requests python-dotenv

echo.
echo [3/3] Запускаем бота...
echo ========================================
echo.
python main.py

echo.
echo ========================================
echo Бот остановлен
echo ========================================
pause