#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для замены всех эмодзи в файлах проекта на текстовые маркеры
"""

import sys
import os

# Добавляем путь к модулям
if os.name == 'nt':  # Windows
    sys.path.append('C:\\SnowWhiteAI\\GrantService')
    PROJECT_ROOT = 'C:\\SnowWhiteAI\\GrantService'
else:  # Linux/Ubuntu
    sys.path.append('/var/GrantService')
    PROJECT_ROOT = '/var/GrantService'

from utils.console_helper import process_directory, safe_print

def main():
    """Главная функция"""
    safe_print("[START] Начинаем замену эмодзи в файлах проекта")
    safe_print("=" * 50)
    
    # Директории для обработки
    directories = [
        os.path.join(PROJECT_ROOT, 'data'),
        os.path.join(PROJECT_ROOT, 'telegram-bot'),
        os.path.join(PROJECT_ROOT, 'web-admin'),
        os.path.join(PROJECT_ROOT, 'scripts')
    ]
    
    total_processed = 0
    
    for directory in directories:
        if os.path.exists(directory):
            safe_print(f"\n[INFO] Обработка директории: {directory}")
            processed = process_directory(
                directory, 
                extensions=['.py'],  # Только Python файлы
                backup=True  # Создавать резервные копии
            )
            total_processed += processed
        else:
            safe_print(f"[WARNING] Директория не найдена: {directory}")
    
    safe_print("\n" + "=" * 50)
    safe_print(f"[SUCCESS] Всего обработано файлов: {total_processed}")
    safe_print("[INFO] Резервные копии сохранены с расширением .backup")
    
    # Предложение восстановить из резервных копий
    safe_print("\n[NOTE] Для восстановления оригинальных файлов используйте:")
    safe_print("       python scripts/restore_from_backup.py")

if __name__ == "__main__":
    main()