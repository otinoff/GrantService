#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция ответов в sessions.interview_data/collected_data с ключей по номеру вопроса
на стабильные ключи по field_name. Повторный запуск безопасен (идемпотентен).
"""

import os
import json
import sqlite3
from datetime import datetime

DB_PATH = "/var/GrantService/data/grantservice.db"


def fetch_question_number_to_field_map(conn: sqlite3.Connection) -> dict:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT question_number, field_name
        FROM interview_questions
        WHERE is_active = 1
        ORDER BY question_number
        """
    )
    mapping: dict[int, str] = {}
    for qn, field in cursor.fetchall():
        if field:
            mapping[int(qn)] = str(field)
    return mapping


def migrate_sessions(conn: sqlite3.Connection, qn_to_field: dict) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, interview_data, collected_data
        FROM sessions
        ORDER BY id
        """
    )
    rows = cursor.fetchall()

    updated_count = 0
    now_iso = datetime.now().isoformat()

    for session_id, interview_data, collected_data in rows:
        changed = False

        def migrate_payload(payload_str: str) -> tuple[str, bool]:
            nonlocal changed
            if not payload_str:
                return payload_str, changed
            try:
                data = json.loads(payload_str)
                if not isinstance(data, dict):
                    return payload_str, changed
            except Exception:
                return payload_str, changed

            new_data: dict[str, str] = {}
            # Сначала копируем все field_name как есть
            for key, value in data.items():
                if isinstance(key, str) and not key.isdigit():
                    new_data[key] = value

            # Перекладываем числовые ключи → field_name
            for key, value in data.items():
                qn = None
                if isinstance(key, int):
                    qn = key
                elif isinstance(key, str) and key.isdigit():
                    try:
                        qn = int(key)
                    except Exception:
                        qn = None

                if qn is not None and qn in qn_to_field:
                    field_name = qn_to_field[qn]
                    # Не перезаписываем уже существующие содержательные ответы по field_name
                    if field_name not in new_data or (not new_data[field_name] and value):
                        new_data[field_name] = value

            # Обнаруживаем изменения
            # Если в исходных ключах были только field_name, изменений может не быть
            if new_data != data:
                changed = True
            return json.dumps(new_data, ensure_ascii=False), changed

        new_interview, changed = migrate_payload(interview_data)
        new_collected, changed = migrate_payload(collected_data)

        if changed:
            cursor.execute(
                """
                UPDATE sessions
                SET interview_data = ?, collected_data = ?, last_activity = ?
                WHERE id = ?
                """,
                (new_interview, new_collected, now_iso, session_id),
            )
            updated_count += 1

    conn.commit()
    return updated_count


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"❌ Не найдена БД: {DB_PATH}")
        return 1

    try:
        with sqlite3.connect(DB_PATH) as conn:
            print("🔍 Загружаю карту вопрос → field_name...")
            qn_to_field = fetch_question_number_to_field_map(conn)
            if not qn_to_field:
                print("⚠️ Не найдено активных вопросов. Миграция пропущена.")
                return 0

            print(f"📋 Активных вопросов: {len(qn_to_field)}")
            print("🔁 Выполняю миграцию сессий...")
            updated = migrate_sessions(conn, qn_to_field)
            print(f"✅ Миграция завершена. Обновлено сессий: {updated}")
            return 0
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

