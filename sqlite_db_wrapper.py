#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite Database Wrapper для локального тестирования
Имитирует интерфейс GrantServiceDatabase для работы с SQLite
"""
import sqlite3
import json
import contextlib
from typing import Optional, Dict, Any, Tuple

class PostgreSQLCompatibleCursor:
    """Cursor wrapper that translates PostgreSQL-style %s to SQLite ?"""

    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=None):
        # Translate %s to ?
        if params:
            sqlite_query = query.replace('%s', '?')
            return self._cursor.execute(sqlite_query, params)
        else:
            return self._cursor.execute(query)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        # Convert Row to dict for compatibility
        return dict(row) if hasattr(row, 'keys') else row

    def fetchall(self):
        rows = self._cursor.fetchall()
        # Convert Rows to dicts for compatibility
        if rows and hasattr(rows[0], 'keys'):
            return [dict(row) for row in rows]
        return rows

    def close(self):
        return self._cursor.close()

    @property
    def description(self):
        return self._cursor.description


class PostgreSQLCompatibleConnection:
    """Connection wrapper that returns PostgreSQL-compatible cursor"""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return PostgreSQLCompatibleCursor(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        self.close()


class SQLiteDBWrapper:
    """Простая обертка для SQLite, совместимая с Writer Agent"""

    def __init__(self, db_path: str = 'C:\\SnowWhiteAI\\GrantService\\data\\grantservice.db'):
        self.db_path = db_path
        print(f"SQLite DB initialized: {db_path}")

    @contextlib.contextmanager
    def connect(self):
        """Создание соединения с SQLite (PostgreSQL-like interface)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Для доступа по именам колонок
        pg_conn = PostgreSQLCompatibleConnection(conn)
        try:
            yield pg_conn
        finally:
            pass  # Connection will be closed by __exit__

    def save_grant_application(self, application_data: Dict[str, Any]) -> str:
        """Сохранить грантовую заявку"""
        with self.connect() as conn:
            cursor = conn.cursor()

            # Генерация номера заявки
            if 'application_number' in application_data:
                application_number = application_data['application_number']
            else:
                import uuid
                from datetime import datetime
                application_number = f"GA-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

            # SQLite не поддерживает RETURNING, поэтому делаем INSERT и возвращаем application_number
            cursor.execute("""
                INSERT INTO grant_applications (
                    application_number, session_id, status, full_text,
                    title, created_at
                )
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (
                application_number,
                application_data.get('session_id', 9),
                application_data.get('status', 'draft'),
                json.dumps(application_data.get('application', {})),
                application_data.get('title', 'Проект'),
            ))

            conn.commit()
            cursor.close()

            print(f"Grant application {application_number} saved to SQLite")
            return application_number
