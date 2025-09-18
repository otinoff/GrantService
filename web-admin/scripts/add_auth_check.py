#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления проверки авторизации во все страницы админки
"""

import os
import sys
import re

# Путь к папке с страницами
PAGES_DIR = '/var/GrantService/web-admin/pages'

# Шаблон проверки авторизации
AUTH_CHECK_TEMPLATE = '''import streamlit as st
import sys
import os

# Добавляем путь к проекту
sys.path.append('/var/GrantService')

# Проверка авторизации
from web_admin.utils.auth import is_user_authorized

if not is_user_authorized():
    # Импортируем страницу входа
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "login_page", 
        "/var/GrantService/web-admin/pages/🔐_Вход.py"
    )
    login_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(login_module)
    login_module.show_login_page()
    st.stop()

'''

def add_auth_check_to_file(file_path):
    """
    Добавляет проверку авторизации в файл страницы
    
    Args:
        file_path (str): Путь к файлу страницы
    """
    # Читаем содержимое файла
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, есть ли уже проверка авторизации
    if 'from web_admin.utils.auth import is_user_authorized' in content:
        print(f"✅ Проверка авторизации уже существует в {file_path}")
        return
    
    # Ищем место для вставки проверки авторизации
    # Обычно это после импортов и до основного кода страницы
    lines = content.split('\n')
    
    # Находим конец импортов
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.strip() == '' and i > 0:
            # Проверяем, был ли предыдущий непустой строкой импорт
            prev_line = lines[i-1].strip()
            if prev_line.startswith(('import ', 'from ')):
                insert_pos = i + 1
                break
        elif line.startswith(('st.', '#', '"""', "'''")) and i > 5:
            # Если встретили основной код страницы, вставляем перед ним
            insert_pos = i
            break
    
    # Если не нашли подходящее место, вставляем после первых строк
    if insert_pos == 0:
        insert_pos = min(10, len(lines))
    
    # Вставляем проверку авторизации
    lines.insert(insert_pos, AUTH_CHECK_TEMPLATE.rstrip())
    
    # Записываем обновленное содержимое
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Добавлена проверка авторизации в {file_path}")

def process_pages_directory():
    """
    Обрабатывает все страницы в директории
    """
    print("🔍 Начинаем обработку страниц админки...")
    
    # Получаем список файлов страниц
    page_files = [f for f in os.listdir(PAGES_DIR) if f.endswith('.py') and f != '🔐_Вход.py']
    
    print(f"📄 Найдено {len(page_files)} страниц для обработки")
    
    for page_file in page_files:
        file_path = os.path.join(PAGES_DIR, page_file)
        try:
            add_auth_check_to_file(file_path)
        except Exception as e:
            print(f"❌ Ошибка обработки {file_path}: {e}")
    
    print("✅ Обработка страниц завершена")

if __name__ == "__main__":
    process_pages_directory()