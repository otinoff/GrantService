@echo off
REM Автономный тест InteractiveInterviewer на ПРОДАКШН БД
REM Подключается к продакшн БД и запускает полный тест

echo ========================================
echo АВТОНОМНЫЙ ТЕСТ НА ПРОДАКШН БД
echo ========================================
echo.

REM Установить переменные окружения для ПРОДАКШН БД
set DB_HOST=5.35.88.251
set DB_PORT=5432
set DB_NAME=grantservice
set DB_USER=postgres
set DB_PASSWORD=Snowwhite2024!

echo [INFO] Подключение к продакшн БД:
echo        Host: %DB_HOST%:%DB_PORT%
echo        DB: %DB_NAME%
echo.

REM Запустить тест
python test_agent_local_autonomous.py

echo.
echo ========================================
pause
