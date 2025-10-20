#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Патч main.py для добавления AI аудита при отправке анкеты
Минимальные изменения - только send_anketa_to_processing
"""

import sys

MAIN_PY = '/var/GrantService/telegram-bot/main.py'

print("Reading main.py...")
with open(MAIN_PY, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(MAIN_PY + '.backup_ai_audit', 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✅ Backup: {MAIN_PY}.backup_ai_audit")

# Находим функцию send_anketa_to_processing и добавляем AI audit ПЕРЕД вызовом n8n
old_code = """    async def send_anketa_to_processing(self, update: Update, context: ContextTypes.DEFAULT_TYPE, anketa_id: str):
        \"\"\"Отправить анкету на обработку в n8n\"\"\"
        user_id = update.effective_user.id

        try:
            # Отправляем в n8n для обработки"""

new_code = """    async def send_anketa_to_processing(self, update: Update, context: ContextTypes.DEFAULT_TYPE, anketa_id: str):
        \"\"\"Отправить анкету на обработку в n8n\"\"\"
        user_id = update.effective_user.id

        # AI Audit (опционально)
        ai_audit_message = ""
        try:
            from ai_interview_wrapper import run_ai_audit_for_anketa, format_ai_audit_message
            logger.info(f"Running AI audit for {anketa_id}...")
            audit_result = await run_ai_audit_for_anketa(anketa_id, self.db)
            ai_audit_message = format_ai_audit_message(audit_result)
            logger.info(f"AI audit complete: score={audit_result.get('audit_score', 0)}")
        except Exception as e:
            logger.warning(f"AI audit skipped: {e}")

        try:
            # Отправляем в n8n для обработки"""

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Добавлен AI audit в send_anketa_to_processing")
else:
    print("❌ Не найден код для замены!")
    sys.exit(1)

# Также обновим success_text чтобы включить AI audit результат
old_success = """            success_text = f\"\"\"
✅ *Анкета отправлена на обработку!*

*ID анкеты:* `{anketa_id}`"""

new_success = """            success_text = f\"\"\"
✅ *Анкета отправлена на обработку!*

*ID анкеты:* `{anketa_id}`

{ai_audit_message if ai_audit_message else ''}"""

if old_success in content:
    content = content.replace(old_success, new_success)
    print("✅ Обновлен success_text с AI audit результатом")
else:
    print("⚠️ success_text не обновлен (не критично)")

# Записываем
with open(MAIN_PY, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ main.py обновлен с AI audit интеграцией!")
