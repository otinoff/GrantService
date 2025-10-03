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

echo NOTE: Database will be automatically synced from production
echo.
echo Launching admin panel...
echo URL: http://localhost:8501
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

python launcher.py

pause