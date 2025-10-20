#!/bin/bash
# Скрипт для добавления test_interactive_handler в main.py на production
# Запускать на сервере: bash add_test_handler.sh

MAIN_PY="/var/GrantService/telegram-bot/main.py"

# Backup
cp $MAIN_PY ${MAIN_PY}.backup_$(date +%Y%m%d_%H%M%S)

# Находим строку с "application.add_handler(CommandHandler("admin"" и добавляем после неё
sed -i '/application.add_handler(CommandHandler("admin"/a\        \n        # TEST: Interactive Interviewer handler\n        try:\n            from test_interactive_handler import register_test_handlers\n            register_test_handlers(application)\n            logger.info("✅ Test Interactive handler registered")\n        except Exception as e:\n            logger.warning(f"⚠️ Could not register test handler: {e}")' $MAIN_PY

echo "✅ Handler added to main.py"
echo "📄 Backup saved: ${MAIN_PY}.backup_$(date +%Y%m%d_%H%M%S)"
