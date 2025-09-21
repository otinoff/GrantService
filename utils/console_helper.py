#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для корректного вывода текста с эмодзи в консоль Windows
"""

import sys
import os
import io

# Словарь замены эмодзи на текстовые маркеры
EMOJI_REPLACEMENTS = {
    '✅': '[OK]',
    '❌': '[ERROR]',
    '⚠️': '[WARNING]',
    '📊': '[STATS]',
    '📈': '[CHART]',
    '📋': '[LIST]',
    '📝': '[NOTE]',
    '🔄': '[SYNC]',
    '🚀': '[START]',
    '🎉': '[SUCCESS]',
    '💾': '[SAVE]',
    '📁': '[FOLDER]',
    '📂': '[FOLDER_OPEN]',
    '📄': '[FILE]',
    '🔍': '[SEARCH]',
    '⏰': '[TIME]',
    '🔔': '[BELL]',
    '💬': '[CHAT]',
    '👤': '[USER]',
    '🔐': '[LOCK]',
    '🔓': '[UNLOCK]',
    '⭐': '[STAR]',
    '📍': '[PIN]',
    '🏆': '[TROPHY]',
    '💡': '[IDEA]',
    '⚡': '[FLASH]',
    '🔧': '[TOOL]',
    '⚙️': '[SETTINGS]',
    '📱': '[PHONE]',
    '💻': '[COMPUTER]',
    '🌐': '[WEB]',
    '📧': '[EMAIL]',
    '📞': '[CALL]',
    '📅': '[CALENDAR]',
    '📌': '[PUSHPIN]',
    '🔗': '[LINK]',
    '✨': '[SPARKLES]',
    '🎯': '[TARGET]',
    '🔥': '[FIRE]',
    '💰': '[MONEY]',
    '📊': '[GRAPH]',
    '📉': '[GRAPH_DOWN]',
    '📈': '[GRAPH_UP]',
    '✏️': '[PENCIL]',
    '🗑️': '[TRASH]',
    '📮': '[MAILBOX]',
    '📨': '[INCOMING]',
    '📤': '[OUTGOING]',
    '🔖': '[BOOKMARK]',
    '🏷️': '[TAG]',
    '📛': '[BADGE]',
    '🆔': '[ID]',
    '🔑': '[KEY]',
    '🗝️': '[OLD_KEY]',
    '🔒': '[LOCKED]',
    '🔓': '[UNLOCKED]',
    '🔐': '[LOCKED_KEY]',
    '🔏': '[LOCKED_PEN]'
}

def setup_console():
    """Настройка консоли для корректной работы с Unicode"""
    if os.name == 'nt':  # Windows
        # Пытаемся установить UTF-8 кодировку
        try:
            # Устанавливаем кодировку для stdout
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, 
                encoding='utf-8',
                errors='replace'
            )
            # Устанавливаем кодировку для stderr
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding='utf-8', 
                errors='replace'
            )
        except:
            # Если не получилось, используем замену эмодзи
            pass

def safe_print(text, use_emoji=None):
    """
    Безопасный вывод текста с автоматической заменой эмодзи при необходимости
    
    Args:
        text: Текст для вывода
        use_emoji: True - всегда использовать эмодзи, 
                   False - всегда заменять на текст,
                   None - автоматическое определение
    """
    if use_emoji is None:
        # Автоматическое определение
        use_emoji = can_use_emoji()
    
    if not use_emoji:
        # Заменяем все эмодзи на текстовые маркеры
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            text = text.replace(emoji, replacement)
    
    try:
        print(text)
    except UnicodeEncodeError:
        # Если всё равно ошибка, заменяем эмодзи
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            text = text.replace(emoji, replacement)
        print(text)

def can_use_emoji():
    """Проверка возможности использования эмодзи в консоли"""
    if os.name != 'nt':
        # На Linux/Mac обычно работает
        return True
    
    # На Windows проверяем кодировку
    try:
        # Пытаемся вывести тестовый эмодзи
        test_emoji = '✅'
        test_emoji.encode(sys.stdout.encoding)
        return True
    except (UnicodeEncodeError, AttributeError):
        return False

def replace_emojis_in_file(filepath, backup=True):
    """
    Заменить все эмодзи в файле на текстовые маркеры
    
    Args:
        filepath: Путь к файлу
        backup: Создавать ли резервную копию
    """
    import shutil
    
    # Создаем резервную копию
    if backup:
        backup_path = filepath + '.backup'
        shutil.copy2(filepath, backup_path)
        print(f"[INFO] Создана резервная копия: {backup_path}")
    
    # Читаем файл
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем эмодзи
    original_content = content
    for emoji, replacement in EMOJI_REPLACEMENTS.items():
        content = content.replace(emoji, replacement)
    
    # Если были изменения, сохраняем
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Файл обновлен: {filepath}")
        return True
    else:
        print(f"[INFO] Эмодзи не найдены в файле: {filepath}")
        return False

def process_directory(directory, extensions=None, backup=True):
    """
    Обработать все файлы в директории
    
    Args:
        directory: Путь к директории
        extensions: Список расширений файлов для обработки (например, ['.py', '.md'])
        backup: Создавать ли резервные копии
    """
    import glob
    
    if extensions is None:
        extensions = ['.py']
    
    processed = 0
    for ext in extensions:
        pattern = os.path.join(directory, '**', f'*{ext}')
        files = glob.glob(pattern, recursive=True)
        
        for filepath in files:
            if '.backup' not in filepath:
                if replace_emojis_in_file(filepath, backup):
                    processed += 1
    
    print(f"[SUCCESS] Обработано файлов: {processed}")
    return processed

# Инициализация при импорте модуля
setup_console()

if __name__ == "__main__":
    # Тестирование
    print("Тестирование вывода эмодзи:")
    print("-" * 40)
    
    # Прямой вывод (может не работать в Windows)
    try:
        print("Прямой вывод: ✅ Успех, ❌ Ошибка, ⚠️ Предупреждение")
    except:
        print("Прямой вывод не работает")
    
    # Безопасный вывод
    safe_print("Безопасный вывод: ✅ Успех, ❌ Ошибка, ⚠️ Предупреждение")
    
    # Принудительно без эмодзи
    safe_print("Без эмодзи: ✅ Успех, ❌ Ошибка, ⚠️ Предупреждение", use_emoji=False)