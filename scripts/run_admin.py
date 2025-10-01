#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный файл запуска админки GrantService
Обеспечивает корректную настройку путей для всех импортов
"""

import sys
import os
from pathlib import Path

# Устанавливаем базовые пути
BASE_DIR = Path(__file__).parent.absolute()
WEB_ADMIN_DIR = BASE_DIR / "web-admin"
DATA_DIR = BASE_DIR / "data"
TELEGRAM_BOT_DIR = BASE_DIR / "telegram-bot"
CONFIG_DIR = BASE_DIR / "config"

# Добавляем все необходимые пути в sys.path
paths_to_add = [
    str(BASE_DIR),           # GrantService
    str(WEB_ADMIN_DIR),      # web-admin (для импорта utils)
    str(DATA_DIR),           # data
    str(TELEGRAM_BOT_DIR),   # telegram-bot
    str(CONFIG_DIR),         # config
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

print("=" * 60)
print("ЗАПУСК АДМИНКИ GRANTSERVICE")
print("=" * 60)
print(f"Базовая директория: {BASE_DIR}")
print(f"Web-admin директория: {WEB_ADMIN_DIR}")
print(f"Python путь настроен")
print("=" * 60)

# Импортируем streamlit после настройки путей
import streamlit.web.cli as stcli

# Определяем главную страницу админки
main_page = str(WEB_ADMIN_DIR / "pages" / "🏠_Главная.py")

if __name__ == "__main__":
    # Запускаем Streamlit с правильными параметрами
    sys.argv = [
        "streamlit",
        "run",
        main_page,
        "--server.port", "8501",
        "--server.headless", "true",
        "--browser.serverAddress", "localhost",
        "--theme.base", "light"
    ]
    
    # Устанавливаем переменные окружения
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    
    print(f"\nЗапуск админки...")
    print(f"Откройте браузер: http://localhost:8501")
    print("\nДля остановки нажмите Ctrl+C")
    print("=" * 60)
    
    # Запускаем Streamlit
    sys.exit(stcli.main())