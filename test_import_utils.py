#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый файл для проверки импорта utils.auth
"""

import sys
import os
from pathlib import Path

# Определяем базовый путь
base_path = Path(__file__).parent.resolve()
web_admin_path = base_path / "web-admin"

# Добавляем пути в sys.path
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))
if str(web_admin_path) not in sys.path:
    sys.path.insert(0, str(web_admin_path))

print("=" * 60)
print("TESTING UTILS.AUTH IMPORT")
print("=" * 60)
print(f"Base path: {base_path}")
print(f"Web admin path: {web_admin_path}")
print(f"Web admin exists: {web_admin_path.exists()}")

utils_path = web_admin_path / "utils"
print(f"Utils path: {utils_path}")
print(f"Utils exists: {utils_path.exists()}")

auth_file = utils_path / "auth.py"
print(f"Auth file: {auth_file}")
print(f"Auth file exists: {auth_file.exists()}")

print("\nCurrent sys.path (first 5):")
for i, p in enumerate(sys.path[:5]):
    print(f"  {i}: {p}")

print("\nTrying to import utils.auth...")

try:
    # Попробуем прямой импорт из utils
    from utils.auth import is_user_authorized
    print("SUCCESS: utils.auth imported successfully!")
    print(f"is_user_authorized function: {is_user_authorized}")
except ImportError as e:
    print(f"ERROR: Failed to import utils.auth: {e}")
    
    # Попробуем альтернативный способ
    print("\nTrying alternative import method...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("auth", str(auth_file))
        if spec and spec.loader:
            auth_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(auth_module)
            print("SUCCESS: auth module loaded via importlib!")
            print(f"Module has is_user_authorized: {hasattr(auth_module, 'is_user_authorized')}")
    except Exception as e2:
        print(f"ERROR: Alternative import also failed: {e2}")

print("=" * 60)