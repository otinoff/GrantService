#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование импортов для диагностики проблем с админкой
"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("ТЕСТИРОВАНИЕ ИМПОРТОВ АДМИНКИ")
print("=" * 60)

# Определяем базовые пути
script_dir = Path(__file__).parent.absolute()
web_admin_dir = script_dir / "web-admin"
pages_dir = web_admin_dir / "pages"
utils_dir = web_admin_dir / "utils"

print(f"\nТекущая директория: {script_dir}")
print(f"Директория web-admin: {web_admin_dir}")
print(f"Директория pages: {pages_dir}")
print(f"Директория utils: {utils_dir}")

# Проверяем существование директорий
print("\n[ПРОВЕРКА ДИРЕКТОРИЙ]")
for dir_path, name in [(web_admin_dir, "web-admin"), (pages_dir, "pages"), (utils_dir, "utils")]:
    if dir_path.exists():
        print(f"✓ {name} существует")
    else:
        print(f"✗ {name} НЕ существует")

# Проверяем файлы в utils
print("\n[ФАЙЛЫ В UTILS]")
if utils_dir.exists():
    for file in utils_dir.glob("*.py"):
        print(f"  - {file.name}")

# Пытаемся импортировать из разных контекстов
print("\n[ТЕСТ ИМПОРТОВ]")

# Сохраняем оригинальный sys.path
original_path = sys.path.copy()

# Тест 1: Добавляем пути как в pages файлах
print("\n1. Имитация импорта из pages/")
current_dir = pages_dir  # имитируем, что мы в pages
parent_dir = current_dir.parent  # web-admin
grandparent_dir = parent_dir.parent  # GrantService

sys.path = original_path.copy()
sys.path.insert(0, str(grandparent_dir))
sys.path.insert(0, str(parent_dir))

try:
    from utils.auth import is_user_authorized
    print("  ✓ Импорт utils.auth успешен")
except ImportError as e:
    print(f"  ✗ Ошибка импорта utils.auth: {e}")

# Тест 2: Прямой импорт с указанием полного пути
print("\n2. Прямой импорт с полным путем")
sys.path = original_path.copy()
sys.path.insert(0, str(web_admin_dir))

try:
    from utils.auth import is_user_authorized
    print("  ✓ Импорт utils.auth успешен")
except ImportError as e:
    print(f"  ✗ Ошибка импорта utils.auth: {e}")

# Тест 3: Импорт через __init__.py
print("\n3. Импорт через __init__.py")
sys.path = original_path.copy()
sys.path.insert(0, str(web_admin_dir))

try:
    import utils
    print(f"  ✓ Модуль utils импортирован")
    
    # Проверяем доступные атрибуты
    attrs = [attr for attr in dir(utils) if not attr.startswith('_')]
    print(f"  Доступные функции: {', '.join(attrs[:5])}...")
    
    # Пытаемся вызвать функцию
    if hasattr(utils, 'is_user_authorized'):
        print(f"  ✓ Функция is_user_authorized доступна")
    else:
        print(f"  ✗ Функция is_user_authorized НЕ доступна")
        
except ImportError as e:
    print(f"  ✗ Ошибка импорта utils: {e}")

# Тест 4: Проверка зависимостей auth.py
print("\n4. Проверка зависимостей auth.py")
sys.path = original_path.copy()
sys.path.insert(0, str(script_dir))  # GrantService
sys.path.insert(0, str(web_admin_dir))  # web-admin

# Проверяем config.paths
try:
    from config import paths
    print("  ✓ config.paths импортирован")
except ImportError as e:
    print(f"  ✗ Ошибка импорта config.paths: {e}")

# Проверяем data.database
try:
    from data.database import GrantServiceDatabase
    print("  ✓ data.database импортирован")
except ImportError as e:
    print(f"  ✗ Ошибка импорта data.database: {e}")

print("\n[АНАЛИЗ ПРОБЛЕМЫ]")
print("Если импорты не работают, проверьте:")
print("1. Наличие файлов __init__.py во всех директориях")
print("2. Правильность путей в sys.path")
print("3. Отсутствие циклических импортов")
print("4. Корректность зависимостей в auth.py")

print("\n[SYS.PATH ПОСЛЕ ТЕСТОВ]")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i}: {path}")

print("\n" + "=" * 60)
print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
print("=" * 60)