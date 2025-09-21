#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для восстановления пропущенных грантовых заявок из завершенных сессий
"""

import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime

db_path = Path(__file__).parent.parent / 'data' / 'grantservice.db'

print("=" * 60)
print("ВОССТАНОВЛЕНИЕ ПРОПУЩЕННЫХ ГРАНТОВЫХ ЗАЯВОК")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Находим завершенные сессии без заявок
cursor.execute("""
    SELECT s.id, s.telegram_id, s.anketa_id, s.answers_data, s.project_name,
           s.completed_at, u.username, u.first_name, u.last_name
    FROM sessions s
    LEFT JOIN users u ON s.telegram_id = u.telegram_id
    LEFT JOIN grant_applications ga ON s.id = ga.session_id
    WHERE s.status = 'completed' 
          AND s.completed_at IS NOT NULL
          AND ga.id IS NULL
    ORDER BY s.completed_at DESC
""")

orphan_sessions = cursor.fetchall()

if not orphan_sessions:
    print("\n✅ Нет завершенных сессий без заявок")
    conn.close()
    exit()

print(f"\n🔍 Найдено {len(orphan_sessions)} завершенных сессий без заявок:")

restored_count = 0

for session in orphan_sessions:
    session_id, telegram_id, anketa_id, answers_data, project_name, completed_at, username, first_name, last_name = session
    
    user_info = f"{first_name} {last_name}" if first_name else f"@{username}" if username else f"ID{telegram_id}"
    print(f"\n📋 Сессия {session_id}: {user_info}")
    print(f"   Анкета: {anketa_id}")
    print(f"   Завершена: {completed_at}")
    
    # Генерируем номер заявки
    date_str = datetime.now().strftime('%Y%m%d')
    app_number = f"GA-{date_str}-{str(uuid.uuid4())[:8].upper()}"
    
    # Определяем название проекта
    title = project_name if project_name else "Восстановленная заявка"
    
    # Парсим ответы
    content_data = {}
    if answers_data:
        try:
            answers = json.loads(answers_data)
            content_data = answers
        except:
            content_data = {"raw_answers": answers_data}
    
    # Добавляем информацию о восстановлении
    content_data["_restored"] = {
        "from_session": session_id,
        "anketa_id": anketa_id,
        "restored_at": datetime.now().isoformat(),
        "original_completion": completed_at
    }
    
    content_json = json.dumps(content_data, ensure_ascii=False, indent=2)
    
    # Создаем заявку
    cursor.execute("""
        INSERT INTO grant_applications (
            application_number, title, content_json, summary, 
            status, user_id, session_id, admin_user, 
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        app_number,
        title,
        content_json,
        f"Заявка восстановлена из сессии {session_id}",
        "draft",
        None,  # user_id будет NULL
        session_id,
        "system_restore",
        completed_at,  # Используем время завершения сессии
        datetime.now().isoformat()
    ))
    
    print(f"   ✅ Создана заявка: {app_number}")
    restored_count += 1

# Сохраняем изменения
conn.commit()

# Проверяем результат
cursor.execute("SELECT COUNT(*) FROM grant_applications")
total_apps = cursor.fetchone()[0]

print(f"\n{'='*60}")
print(f"✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!")
print(f"   Восстановлено заявок: {restored_count}")
print(f"   Всего заявок в БД: {total_apps}")
print(f"{'='*60}")

# Показываем последние заявки
print(f"\n📋 Последние 5 заявок:")
cursor.execute("""
    SELECT id, application_number, title, admin_user, created_at 
    FROM grant_applications 
    ORDER BY created_at DESC 
    LIMIT 5
""")

for app in cursor.fetchall():
    admin = f"({app[3]})" if app[3] else ""
    print(f"  ID {app[0]}: {app[1]} {admin}")
    print(f"       {app[2][:50]}...")

conn.close()