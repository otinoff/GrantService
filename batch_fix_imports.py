#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Батч-скрипт для исправления всех импортов в pages
Безопасный - работает через простую замену строк
"""

import os
import glob

def fix_file(filepath):
    """Исправить импорты в одном файле"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        new_lines = []
        
        # Флаг для отслеживания добавления путей
        paths_added = False
        
        for i, line in enumerate(lines):
            # Заменяем web_admin на utils
            if 'from web_admin.utils.auth import is_user_authorized' in line:
                new_lines.append('from utils.auth import is_user_authorized\n')
                modified = True
            
            # Заменяем хардкод Linux путей
            elif "sys.path.append('/var/GrantService')" in line:
                if not paths_added:
                    new_lines.append("""# Добавляем пути кроссплатформенно
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService
sys.path.insert(0, grandparent_dir)  # Для импорта config и data
sys.path.insert(0, parent_dir)  # Для импорта utils
""")
                    paths_added = True
                    modified = True
            
            # Заменяем хардкод пути к странице входа
            elif '"/var/GrantService/web-admin/pages/' in line and 'Вход.py' in line:
                new_line = line.replace(
                    '"/var/GrantService/web-admin/pages/🔐_Вход.py"',
                    'os.path.join(current_dir, "🔐_Вход.py")'
                )
                new_lines.append(new_line)
                modified = True
            
            else:
                new_lines.append(line)
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Главная функция"""
    
    pages_dir = "C:\\SnowWhiteAI\\GrantService\\web-admin\\pages"
    
    print("=" * 50)
    print("Batch Import Fixer for web-admin/pages")
    print("=" * 50)
    
    # Получаем все Python файлы
    pattern = os.path.join(pages_dir, "*.py")
    files = glob.glob(pattern)
    
    print(f"\nFound {len(files)} Python files")
    
    fixed_count = 0
    
    for filepath in files:
        filename = os.path.basename(filepath)
        
        # Пропускаем файлы, которые уже исправлены
        if filename in ['__init__.py', '👥_Пользователи.py']:
            print(f"  [SKIP] {filename} - already fixed")
            continue
        
        if fix_file(filepath):
            print(f"  [FIXED] {filename}")
            fixed_count += 1
        else:
            print(f"  [OK] {filename}")
    
    print("\n" + "=" * 50)
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()