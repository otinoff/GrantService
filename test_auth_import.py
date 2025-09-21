#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест импорта модуля auth для диагностики
"""

import sys
import os
from pathlib import Path

# Добавляем пути
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "web-admin"))

print("Текущая директория:", current_dir)
print("Python paths:")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i}: {path}")

print("\nПроверяем существование файлов:")
files_to_check = [
    "core.py",
    "web-admin/utils/auth.py",
    "web-admin/utils/__init__.py",
    "telegram-bot/config/constants.py"
]

for file_path in files_to_check:
    full_path = current_dir / file_path
    exists = full_path.exists()
    print(f"  {file_path}: {'✅' if exists else '❌'}")

print("\nПытаемся импортировать модули:")

try:
    import core
    print("✅ core импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта core: {e}")

try:
    from web_admin.utils import auth
    print("✅ web_admin.utils.auth импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта web_admin.utils.auth: {e}")

try:
    from utils import auth
    print("✅ utils.auth импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта utils.auth: {e}")

print("\nТест завершен")