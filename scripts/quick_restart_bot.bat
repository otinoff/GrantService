@echo off
title GrantService Bot
echo ========================================
echo    Быстрый запуск Telegram бота
echo ========================================
echo.

cd /d C:\SnowWhiteAI\GrantService

echo Останавливаем старый процесс...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq GrantService Bot*" >nul 2>&1

echo Запускаем бота...
echo.
python telegram-bot\main.py

pause