#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для миграции существующих анкет
Генерирует anketa_id для сессий, которые были созданы до внедрения новой системы
"""

import sys
import os
from datetime import datetime
import json

# Добавляем пути к модулям
sys.path.append('/var/GrantService')
sys.path.append('/var/GrantService/data')

from data.database.models import GrantServiceDatabase, get_kuzbass_time

def migrate_existing_anketas():
    """Миграция существующих анкет - генерация anketa_id для сессий без него"""
    print("🔄 Начинаем миграцию существующих анкет")
    print("=" * 50)
    
    # Инициализируем базу данных
    db = GrantServiceDatabase()
    
    try:
        # Получаем все сессии
        all_sessions = db.get_all_sessions(limit=1000)
        print(f"📊 Всего сессий в базе: {len(all_sessions)}")
        
        # Находим сессии без anketa_id
        sessions_without_anketa = [s for s in all_sessions if not s.get('anketa_id')]
        print(f"🔍 Найдено сессий без anketa_id: {len(sessions_without_anketa)}")
        
        if not sessions_without_anketa:
            print("✅ Все сессии уже имеют anketa_id!")
            return
        
        migrated_count = 0
        error_count = 0
        
        for session in sessions_without_anketa:
            try:
                print(f"\n📋 Обрабатываем сессию ID: {session['id']}")
                user_display = session.get('username', f"ID:{session['telegram_id']}")
                print(f"   Пользователь: {user_display}")
                print(f"   Имя: {session.get('first_name', '')} {session.get('last_name', '')}")
                print(f"   Дата создания: {session.get('started_at', 'Unknown')}")
                
                # Проверяем есть ли данные интервью
                has_interview_data = bool(session.get('interview_data'))
                print(f"   Данные интервью: {'✅ Есть' if has_interview_data else '❌ Нет'}")
                
                if not has_interview_data:
                    print("   ⚠️ Пропускаем - нет данных интервью")
                    continue
                
                # Подготавливаем данные пользователя
                user_data = {
                    "telegram_id": session["telegram_id"],
                    "username": session.get("username"),
                    "first_name": session.get("first_name"),
                    "last_name": session.get("last_name")
                }
                
                # Генерируем anketa_id
                anketa_id = db.generate_anketa_id(user_data)
                print(f"   🆔 Сгенерирован anketa_id: {anketa_id}")
                
                # Обновляем сессию с anketa_id
                success = update_session_with_anketa_id(db, session['id'], anketa_id)
                
                if success:
                    print(f"   ✅ Сессия обновлена успешно")
                    migrated_count += 1
                else:
                    print(f"   ❌ Ошибка обновления сессии")
                    error_count += 1
                    
            except Exception as e:
                print(f"   ❌ Ошибка обработки сессии {session['id']}: {e}")
                error_count += 1
        
        print("\n" + "=" * 50)
        print("📊 Результаты миграции:")
        print(f"   ✅ Успешно мигрировано: {migrated_count}")
        print(f"   ❌ Ошибок: {error_count}")
        print(f"   📋 Всего обработано: {migrated_count + error_count}")
        
        if migrated_count > 0:
            print(f"\n🎉 Миграция завершена! Теперь {migrated_count} анкет доступны для ручного исследования.")
        
    except Exception as e:
        print(f"❌ Критическая ошибка миграции: {e}")

def update_session_with_anketa_id(db, session_id, anketa_id):
    """Обновить сессию с anketa_id"""
    try:
        with db.connect() as conn:
            cursor = conn.cursor()
            
            # Обновляем сессию
            cursor.execute("""
                UPDATE sessions 
                SET anketa_id = ?, 
                    status = CASE 
                        WHEN interview_data IS NOT NULL AND interview_data != '' 
                        THEN 'completed' 
                        ELSE status 
                    END,
                    completed_at = CASE 
                        WHEN interview_data IS NOT NULL AND interview_data != '' 
                        THEN ? 
                        ELSE completed_at 
                    END
                WHERE id = ?
            """, (anketa_id, get_kuzbass_time(), session_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                return True
            else:
                print(f"   ⚠️ Сессия {session_id} не найдена для обновления")
                return False
                
    except Exception as e:
        print(f"   ❌ Ошибка обновления сессии {session_id}: {e}")
        return False

def show_migration_preview():
    """Показать превью того, что будет мигрировано"""
    print("🔍 Превью миграции:")
    print("=" * 50)
    
    db = GrantServiceDatabase()
    
    try:
        all_sessions = db.get_all_sessions(limit=1000)
        sessions_without_anketa = [s for s in all_sessions if not s.get('anketa_id')]
        
        print(f"📊 Всего сессий: {len(all_sessions)}")
        print(f"🔍 Без anketa_id: {len(sessions_without_anketa)}")
        
        if sessions_without_anketa:
            print(f"\n📋 Сессии для миграции:")
            for i, session in enumerate(sessions_without_anketa[:5]):  # Показываем первые 5
                user_display = session.get('username', f"ID:{session['telegram_id']}")
                has_data = "✅" if session.get('interview_data') else "❌"
                print(f"   {i+1}. {user_display} - {has_data} данные интервью")
            
            if len(sessions_without_anketa) > 5:
                print(f"   ... и еще {len(sessions_without_anketa) - 5} сессий")
        else:
            print("✅ Все сессии уже имеют anketa_id!")
            
    except Exception as e:
        print(f"❌ Ошибка превью: {e}")

if __name__ == "__main__":
    print("🚀 Скрипт миграции существующих анкет")
    print("=" * 50)
    
    # Показываем превью
    show_migration_preview()
    
    print("\n" + "=" * 50)
    response = input("Продолжить миграцию? (y/N): ").strip().lower()
    
    if response in ['y', 'yes', 'да', 'д']:
        migrate_existing_anketas()
    else:
        print("❌ Миграция отменена")

