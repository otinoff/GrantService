#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления всех импортов в web-admin/pages
"""

import os
import re

def fix_imports_in_file(file_path):
    """Исправить импорты в одном файле"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Сохраняем оригинал для сравнения
    original_content = content
    
    # Заменяем неправильные импорты
    replacements = [
        # Заменяем web_admin на правильный импорт
        (r'from web_admin\.utils\.auth import', 'from utils.auth import'),
        # Заменяем абсолютные Linux пути
        (r"sys\.path\.append\('/var/GrantService'\)", 
         """# Добавляем пути кроссплатформенно
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService
sys.path.insert(0, grandparent_dir)  # Для импорта config и data
sys.path.insert(0, parent_dir)  # Для импорта utils"""),
        # Заменяем хардкод пути к странице входа
        (r'"/var/GrantService/web-admin/pages/🔐_Вход\.py"',
         'os.path.join(current_dir, "🔐_Вход.py")')
    ]
    
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)
    
    # Если файл изменился, сохраняем
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Главная функция"""
    
    pages_dir = "C:\\SnowWhiteAI\\GrantService\\web-admin\\pages"
    
    if not os.path.exists(pages_dir):
        print(f"Директория {pages_dir} не найдена!")
        return
    
    print("=" * 50)
    print("Исправление импортов в web-admin/pages")
    print("=" * 50)
    
    fixed_files = []
    
    # Находим все Python файлы
    for filename in os.listdir(pages_dir):
        if filename.endswith('.py'):
            file_path = os.path.join(pages_dir, filename)
            
            print(f"\nПроверяем: {filename}")
            
            if fix_imports_in_file(file_path):
                fixed_files.append(filename)
                print(f"  [FIXED] Исправлен")
            else:
                print(f"  [OK] Не требует исправлений")
    
    print("\n" + "=" * 50)
    print(f"Итого исправлено файлов: {len(fixed_files)}")
    
    if fixed_files:
        print("\nИсправленные файлы:")
        for file in fixed_files:
            print(f"  - {file}")

if __name__ == "__main__":
    main()