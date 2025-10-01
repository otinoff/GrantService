@echo off
echo 🌐 Простая проверка удаленного сервера...
echo.

REM Установка paramiko если его нет
python -c "import paramiko" 2>nul
if errorlevel 1 (
    echo 📦 Устанавливаем paramiko...
    pip install paramiko
    echo.
)

echo 🔍 Запуск проверки базы данных...
python check_remote_db_windows.py

echo.
echo ✅ Проверка завершена
pause