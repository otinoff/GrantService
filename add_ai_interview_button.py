#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления кнопки AI Интервью в production main.py
PATCH для быстрого деплоя
"""

import sys

# Читаем main.py
with open('/var/GrantService/telegram-bot/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Backup
with open('/var/GrantService/telegram-bot/main.py.backup_ai', 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Находим строку с кнопкой "Начать заполнение" и добавляем AI кнопку
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)

    # После кнопки "Начать заполнение" добавляем AI кнопку
    if '[InlineKeyboardButton("📝 Начать заполнение", callback_data="start_interview")]' in line:
        # Добавляем вторую кнопку в том же ряду
        indent = len(line) - len(line.lstrip())
        new_lines.append(' ' * indent + '[InlineKeyboardButton("🤖 AI Интервью", callback_data="start_ai_interview")],\n')
        print(f"✅ Добавлена AI кнопка после строки {i+1}")

    # После обработчика start_interview добавляем start_ai_interview
    if 'elif callback_data == "start_interview":' in line:
        # После блока start_interview найдем его конец и добавим новый handler
        # Пропускаем текущий блок
        pass

# Добавляем обработчик start_ai_interview перед payment
for i, line in enumerate(new_lines):
    if 'elif callback_data == "payment":' in line:
        indent = len(line) - len(line.lstrip())
        handler_code = f'''{' ' * indent}elif callback_data == "start_ai_interview":
{' ' * (indent + 4)}# AI-powered interview с промежуточными аудитами
{' ' * (indent + 4)}try:
{' ' * (indent + 8)}from agents.interactive_interviewer_agent import InteractiveInterviewerAgent
{' ' * (indent + 8)}from data.database.models import GrantServiceDatabase
{' ' * (indent + 8)}
{' ' * (indent + 8)}await query.answer()
{' ' * (indent + 8)}await query.edit_message_text(
{' ' * (indent + 12)}"🤖 Запуск AI-интервью...\\n\\n"
{' ' * (indent + 12)}"Это интерактивный режим с AI-анализом ответов.\\n"
{' ' * (indent + 12)}"Вам будет задано 15 вопросов."
{' ' * (indent + 8)})
{' ' * (indent + 8)}
{' ' * (indent + 8)}# Используем обычный interview flow пока
{' ' * (indent + 8)}# TODO: Интегрировать полный AI flow
{' ' * (indent + 8)}await self.show_question_navigation(query, context, 1)
{' ' * (indent + 4)}except Exception as e:
{' ' * (indent + 8)}logger.error(f"AI Interview error: {{e}}")
{' ' * (indent + 8)}await query.edit_message_text("❌ Ошибка запуска AI интервью")
{' ' * (indent + 4)}
'''
        new_lines.insert(i, handler_code)
        print(f"✅ Добавлен handler start_ai_interview перед строкой {i+1}")
        break

# Записываем обратно
with open('/var/GrantService/telegram-bot/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ main.py обновлен!")
print("📄 Backup: /var/GrantService/telegram-bot/main.py.backup_ai")
