#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Дебаггинг скрипт для проверки всех импортов в GrantService
Находит все проблемные импорты и предлагает исправления
"""

import os
import sys
import re
from pathlib import Path
from collections import defaultdict

# Цвета для консоли
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

def find_python_files(directory):
    """Найти все Python файлы в проекте"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Пропускаем виртуальные окружения
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def extract_imports(file_path):
    """Извлечь все импорты из файла"""
    imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Регулярные выражения для поиска импортов
        import_patterns = [
            r'^import\s+(.+)',
            r'^from\s+(.+?)\s+import\s+.+'
        ]
        
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if line.startswith('#'):
                continue
                
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module = match.group(1).split(' as ')[0].strip()
                    imports.append({
                        'line': line_num,
                        'statement': line,
                        'module': module,
                        'type': 'import' if line.startswith('import') else 'from'
                    })
                    break
    
    except Exception as e:
        print(f"{Colors.RED}Error reading {file_path}: {e}{Colors.RESET}")
    
    return imports

def check_import(file_path, import_info):
    """Проверить, работает ли импорт"""
    file_dir = os.path.dirname(file_path)
    module_name = import_info['module']
    
    # Определяем тип импорта
    problems = []
    
    # Проблемные паттерны для web-admin
    if 'web-admin' in file_path:
        # Проверка на utils.logger и другие локальные модули
        if module_name == 'utils.logger':
            problems.append({
                'type': 'path_issue',
                'message': 'Модуль utils.logger нужно импортировать с добавлением пути',
                'solution': 'Добавить sys.path к web-admin или использовать относительный импорт'
            })
        
        # Проверка на config без правильного пути
        if module_name == 'config' and 'sys.path' not in open(file_path, 'r', encoding='utf-8').read()[:500]:
            problems.append({
                'type': 'missing_path',
                'message': 'Импорт config требует добавления пути к корню проекта',
                'solution': 'Добавить parent_dir в sys.path перед импортом'
            })
        
        # Проверка на web_admin (неправильное имя)
        if 'web_admin' in module_name:
            problems.append({
                'type': 'wrong_name',
                'message': 'Модуль называется web-admin, а не web_admin',
                'solution': 'Использовать относительный импорт или исправить имя'
            })
    
    # Проверка на абсолютные Linux пути в Windows
    if sys.platform == 'win32':
        if '/var/GrantService' in import_info['statement']:
            problems.append({
                'type': 'hardcoded_path',
                'message': 'Хардкод Linux пути в Windows окружении',
                'solution': 'Использовать config.paths для кроссплатформенности'
            })
    
    return problems

def analyze_project(project_dir):
    """Анализировать весь проект"""
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}   GrantService Import Debugger{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}\n")
    
    # Находим все Python файлы
    python_files = find_python_files(project_dir)
    print(f"{Colors.GREEN}[OK] Найдено {len(python_files)} Python файлов{Colors.RESET}\n")
    
    all_problems = defaultdict(list)
    
    # Анализируем каждый файл
    for file_path in python_files:
        rel_path = os.path.relpath(file_path, project_dir)
        imports = extract_imports(file_path)
        
        if imports:
            file_problems = []
            for import_info in imports:
                problems = check_import(file_path, import_info)
                if problems:
                    file_problems.append({
                        'import': import_info,
                        'problems': problems
                    })
            
            if file_problems:
                all_problems[rel_path] = file_problems
    
    # Выводим результаты
    if all_problems:
        print(f"{Colors.RED}[!] Найдены проблемы в {len(all_problems)} файлах:{Colors.RESET}\n")
        
        for file_path, problems in all_problems.items():
            print(f"{Colors.YELLOW}[FILE] {file_path}:{Colors.RESET}")
            
            for problem_info in problems:
                import_info = problem_info['import']
                print(f"  Строка {import_info['line']}: {Colors.CYAN}{import_info['statement']}{Colors.RESET}")
                
                for problem in problem_info['problems']:
                    print(f"    {Colors.RED}[X] {problem['type']}: {problem['message']}{Colors.RESET}")
                    print(f"    {Colors.GREEN}[>] Решение: {problem['solution']}{Colors.RESET}")
            print()
    
    # Специальная проверка для main_admin.py
    main_admin_path = os.path.join(project_dir, 'web-admin', 'main_admin.py')
    if os.path.exists(main_admin_path):
        print(f"\n{Colors.MAGENTA}[CHECK] Специальная проверка main_admin.py:{Colors.RESET}")
        
        with open(main_admin_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверяем наличие правильных импортов
        checks = {
            'sys.path добавление': 'sys.path.insert' in content or 'sys.path.append' in content,
            'config импорт': 'from config import paths' in content,
            'logger импорт': 'logger' in content
        }
        
        for check_name, passed in checks.items():
            status = f"{Colors.GREEN}[OK]{Colors.RESET}" if passed else f"{Colors.RED}[X]{Colors.RESET}"
            print(f"  {status} {check_name}")
    
    # Рекомендации по исправлению
    print(f"\n{Colors.CYAN}[RECOMMENDATIONS] Общие рекомендации:{Colors.RESET}")
    print(f"""
1. Для файлов в web-admin/pages/:
   {Colors.YELLOW}# Добавить в начало файла:
   parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   sys.path.insert(0, parent_dir){Colors.RESET}
   
2. Для файлов в web-admin/utils/:
   {Colors.YELLOW}# Добавить в начало файла:
   parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   sys.path.insert(0, parent_dir){Colors.RESET}
   
3. Для main_admin.py:
   {Colors.YELLOW}# Использовать либо sys.path добавление, либо запускать из корня проекта{Colors.RESET}
   
4. Импорт logger в web-admin:
   {Colors.YELLOW}# Если запуск из web-admin:
   from utils.logger import setup_logger
   # Если запуск из корня:
   from web-admin.utils.logger import setup_logger{Colors.RESET}
""")
    
    return all_problems

def fix_main_admin(project_dir):
    """Предложить исправление для main_admin.py"""
    main_admin_path = os.path.join(project_dir, 'web-admin', 'main_admin.py')
    
    if not os.path.exists(main_admin_path):
        print(f"{Colors.RED}Файл main_admin.py не найден{Colors.RESET}")
        return
    
    print(f"\n{Colors.CYAN}[FIX] Предлагаемое исправление для main_admin.py:{Colors.RESET}")
    print(f"""{Colors.YELLOW}
import streamlit as st
import sys
import os

# Определяем, откуда запущен скрипт
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Добавляем пути для импортов
if 'web-admin' in current_dir:
    # Запуск из web-admin директории
    sys.path.insert(0, parent_dir)  # Для импорта config
    sys.path.insert(0, current_dir)  # Для импорта utils
else:
    # Запуск из корня проекта
    sys.path.insert(0, os.path.join(parent_dir, 'web-admin'))

# Импортируем кроссплатформенные пути
from config import paths

# Инициализация логгера
try:
    # Пробуем импорт для запуска из web-admin
    from utils.logger import setup_logger
except ImportError:
    # Если не получилось, пробуем импорт для запуска из корня
    try:
        from web_admin.utils.logger import setup_logger
    except ImportError:
        # Создаем заглушку если логгер не найден
        def setup_logger(name):
            import logging
            return logging.getLogger(name)

logger = setup_logger('main_admin')
{Colors.RESET}""")

if __name__ == "__main__":
    # Определяем корневую директорию проекта
    if os.path.exists("C:\\SnowWhiteAI\\GrantService"):
        project_root = "C:\\SnowWhiteAI\\GrantService"
    else:
        project_root = os.getcwd()
    
    print(f"[DIR] Анализируем проект: {project_root}\n")
    
    # Запускаем анализ
    problems = analyze_project(project_root)
    
    # Предлагаем исправление для main_admin.py
    fix_main_admin(project_root)
    
    # Итоговая статистика
    total_problems = sum(len(p) for p in problems.values())
    if total_problems > 0:
        print(f"\n{Colors.RED}[X] Всего найдено проблем: {total_problems}{Colors.RESET}")
    else:
        print(f"\n{Colors.GREEN}[OK] Проблем с импортами не найдено!{Colors.RESET}")