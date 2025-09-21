@echo off
chcp 65001 >nul
title GrantService Admin Panel

echo ============================================================
echo           ЗАПУСК АДМИН-ПАНЕЛИ GRANTSERVICE
echo ============================================================
echo.

cd /d "%~dp0"

echo Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден. Установите Python 3.8+
    pause
    exit /b 1
)

echo Проверка Streamlit...
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ПРЕДУПРЕЖДЕНИЕ] Streamlit не установлен. Устанавливаю...
    pip install streamlit
)

echo.
echo Запуск админки...
echo ============================================================
echo.
echo После запуска откройте браузер по адресу:
echo http://localhost:8501
echo.
echo Для остановки нажмите Ctrl+C
echo ============================================================
echo.

python run_admin.py

pause