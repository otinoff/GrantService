#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый тест agent_router - проверка что возвращает InteractiveInterviewerAgent
"""

import sys
import io
from pathlib import Path

# Fix UTF-8 for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "telegram-bot"))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

print("=" * 80)
print("ТЕСТ: Agent Router - Interviewer Handler")
print("=" * 80)

print("\n📦 Импорт модулей...")
from data.database import GrantServiceDatabase
sys.path.insert(0, str(Path(__file__).parent / "telegram-bot"))
from agent_router import get_interviewer_handler

print("✅ Импорт успешен")

print("\n🗄️  Подключение к БД...")
db = GrantServiceDatabase()
print("✅ БД подключена")

print("\n🎤 Получение Interviewer Handler...")
interviewer = get_interviewer_handler(db)
print(f"✅ Загружен: {type(interviewer).__name__}")

print("\n" + "=" * 80)
print("📋 РЕЗУЛЬТАТ")
print("=" * 80)
print(f"Класс: {type(interviewer).__name__}")
print(f"Модуль: {type(interviewer).__module__}")

expected = "InteractiveInterviewerAgent"
if type(interviewer).__name__ == expected:
    print(f"\n✅ УСПЕШНО! Загружен {expected}")
else:
    print(f"\n❌ ОШИБКА! Ожидался {expected}, получен {type(interviewer).__name__}")

print("=" * 80)
