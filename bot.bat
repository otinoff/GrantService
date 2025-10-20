@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cls
echo.
echo ========================================
echo   GrantService Telegram Bot
echo   PostgreSQL 18
echo ========================================
echo.

cd telegram-bot
python main.py

pause
