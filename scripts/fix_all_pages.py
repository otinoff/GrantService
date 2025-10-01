#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для автоматического исправления всех файлов в web-admin/pages
Делает их кроссплатформенными (Windows/Linux)
"""

import os
import re
import sys
import io
from pathlib import Path

# Устанавливаем UTF-8 для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_file(filepath):
    """Исправляет импорты и пути в файле"""
    
    # Используем repr для безопасного вывода имени файла с emoji
    safe_name = filepath.name.encode('ascii', 'replace').decode('ascii')
    print(f"Processing: {safe_name}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  [ERROR] Read error: {e}")
        return False
    
    # Сохраняем оригинал для сравнения
    original_content = content
    
    # Паттерн для поиска блока с добавлением путей и импортом авторизации
    pattern = r'(import os\s*\n)(?:.*?)sys\.path\.append\([\'\"]/var/GrantService[\'\"]?\)(?:.*?)from web_admin\.utils\.auth import is_user_authorized(?:.*?)st\.stop\(\)'
    
    replacement = r'''import os

# Добавляем пути кроссплатформенно
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService
sys.path.insert(0, grandparent_dir)  # Для импорта config и data
sys.path.insert(0, parent_dir)  # Для импорта utils

# Проверка авторизации
from utils.auth import is_user_authorized

if not is_user_authorized():
    # Импортируем страницу входа
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "login_page", 
        os.path.join(current_dir, "🔐_Вход.py")
    )
    login_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(login_module)
    login_module.show_login_page()
    st.stop()'''
    
    # Применяем замену
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Заменяем все hardcoded пути
    content = content.replace("'/var/GrantService'", "grandparent_dir")
    content = content.replace('"/var/GrantService"', "grandparent_dir")
    content = content.replace("'/var/GrantService/telegram-bot'", "os.path.join(grandparent_dir, 'telegram-bot')")
    content = content.replace('"/var/GrantService/telegram-bot"', "os.path.join(grandparent_dir, 'telegram-bot')")
    content = content.replace("'/var/GrantService/data'", "os.path.join(grandparent_dir, 'data')")
    content = content.replace('"/var/GrantService/data"', "os.path.join(grandparent_dir, 'data')")
    content = content.replace("'/var/GrantService/agents'", "os.path.join(grandparent_dir, 'agents')")
    content = content.replace('"/var/GrantService/agents"', "os.path.join(grandparent_dir, 'agents')")
    content = content.replace('"/var/GrantService/web-admin/pages/🔐_Вход.py"', 'os.path.join(current_dir, "🔐_Вход.py")')
    content = content.replace("'/var/GrantService/web-admin/pages/🔐_Вход.py'", 'os.path.join(current_dir, "🔐_Вход.py")')
    
    # Заменяем импорты из web_admin на utils
    content = content.replace("from web_admin.utils.", "from utils.")
    content = content.replace("import web_admin.utils.", "import utils.")
    
    # Если ничего не изменилось, возможно файл уже исправлен или имеет другую структуру
    if content == original_content:
        print(f"  [SKIP] File already fixed or doesn't need changes")
        return True
    
    # Сохраняем исправленный файл
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] File successfully fixed")
        return True
    except Exception as e:
        print(f"  [ERROR] Write error: {e}")
        return False

def main():
    """Основная функция"""
    
    # Определяем путь к директории pages
    pages_dir = Path(__file__).parent / "web-admin" / "pages"
    
    if not pages_dir.exists():
        print(f"ERROR: Directory not found: {pages_dir}")
        return 1
    
    print(f"Processing files in: {pages_dir}\n")
    
    # Список файлов для обработки
    files_to_process = [
        "📋_Готовые_гранты.py",
        "📋_Мониторинг_логов.py",
        "🤖_AI_Agents.py",
        "🤖_AI_Agents_Main.py",
        "🔬_Аналитика_исследователя.py",
        "🔬_Исследования_исследователя.py",
        "🧑‍💼_Analyst_Prompts.py",
        "🧪_Test_Prompts.py",
        "📄_Просмотр_заявки.py",
        "👥_Пользователи.py",
        "🔐_Вход.py"
    ]
    
    success_count = 0
    error_count = 0
    
    for filename in files_to_process:
        filepath = pages_dir / filename
        
        if not filepath.exists():
            print(f"[WARNING] File not found: {filename}")
            continue
            
        if fix_file(filepath):
            success_count += 1
        else:
            error_count += 1
    
    print("\n" + "="*50)
    print(f"[SUCCESS] Processed: {success_count} files")
    if error_count > 0:
        print(f"[ERRORS] Failed: {error_count} files")
    else:
        print("[DONE] All files processed successfully!")
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())