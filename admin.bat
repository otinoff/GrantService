@echo off
chcp 65001 >nul 2>&1
title GrantService Admin Panel

echo ============================================================
echo                GRANTSERVICE ADMIN PANEL
echo ============================================================
echo.

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Test environment first
echo Testing environment setup...
python launcher.py --test >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Environment test failed. Running detailed test...
    echo.
    python launcher.py --test
    echo.
    echo [!] Fix the issues above before launching
    pause
    exit /b 1
)

echo Environment OK
echo.
echo Launching admin panel...
echo URL: http://localhost:8501
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

python launcher.py

pause