#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрая проверка токена Telegram бота
"""

import sys
import os
from pathlib import Path

# Добавляем пути для импортов
current_dir = Path(__file__).parent
web_admin_path = current_dir / "web-admin"
if str(web_admin_path) not in sys.path:
    sys.path.insert(0, str(web_admin_path))

def main():
    """Основная функция проверки токена"""
    print("ПРОВЕРКА ТОКЕНА TELEGRAM БОТА")
    print("=" * 50)
    
    try:
        from utils.telegram_sender import test_telegram_connection
        
        # Запускаем тест соединения с детальным логированием
        success, message = test_telegram_connection()
        
        print("\n" + "=" * 50)
        if success:
            print("[OK] РЕЗУЛЬТАТ: Токен работает корректно!")
            print("[INFO] Бот готов к отправке сообщений")
        else:
            print("[FAIL] РЕЗУЛЬТАТ: Проблема с токеном!")
            print("[INFO] Требуется проверка настроек")
            
            print("\n[HELP] ВОЗМОЖНЫЕ РЕШЕНИЯ:")
            print("   1. Проверьте файл GrantService/config/.env")
            print("   2. Убедитесь, что токен правильный")
            print("   3. Проверьте, что бот создан через @BotFather")
            print("   4. Убедитесь, что бот не заблокирован")
        
        print(f"\n[MSG] Сообщение: {message}")
        
    except Exception as e:
        print(f"[ERROR] КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()