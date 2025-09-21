#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для очистки невалидных токенов в БД
Удаляет все токены без правильного формата (token_timestamp_hash)
"""

import sys
import os
import sqlite3

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def clear_invalid_tokens():
    """Очищает все токены с невалидным форматом"""
    
    # Путь к БД в зависимости от ОС
    import os
    if os.name == 'nt':  # Windows
        db_path = "C:/SnowWhiteAI/GrantService/data/grantservice.db"
    else:  # Linux/Unix
        db_path = "/var/GrantService/data/grantservice.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Получаем все токены
            cursor.execute("SELECT telegram_id, login_token FROM users WHERE login_token IS NOT NULL")
            users = cursor.fetchall()
            
            invalid_count = 0
            valid_count = 0
            
            print("="*60)
            print("ПРОВЕРКА ТОКЕНОВ В БАЗЕ ДАННЫХ")
            print("-"*60)
            
            for telegram_id, token in users:
                if token:
                    parts = token.split('_')
                    if len(parts) < 3:
                        # Невалидный токен - очищаем
                        print(f"❌ Невалидный токен для пользователя {telegram_id}")
                        print(f"   Токен: {token[:20]}... (частей: {len(parts)})")
                        
                        cursor.execute(
                            "UPDATE users SET login_token = NULL WHERE telegram_id = ?",
                            (telegram_id,)
                        )
                        invalid_count += 1
                    else:
                        print(f"✅ Валидный токен для пользователя {telegram_id}")
                        print(f"   Токен: {token[:30]}...")
                        valid_count += 1
            
            conn.commit()
            
            print("-"*60)
            print(f"РЕЗУЛЬТАТ:")
            print(f"  Валидных токенов: {valid_count}")
            print(f"  Очищено невалидных: {invalid_count}")
            print("="*60)
            
            if invalid_count > 0:
                print("\n✅ Невалидные токены успешно очищены!")
                print("Теперь пользователи получат новые токены в правильном формате.")
            else:
                print("\n✅ Все токены в базе данных валидны!")
                
    except Exception as e:
        print(f"❌ Ошибка работы с БД: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clear_invalid_tokens()