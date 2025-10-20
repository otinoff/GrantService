#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database wrapper для совместимости с Researcher V2
"""
from data.database.models import GrantServiceDatabase
import psycopg2.extras
from typing import List, Dict, Any, Optional


class DatabaseWrapper:
    """Wrapper для GrantServiceDatabase с методами execute_query() и get_session_by_anketa_id()"""

    def __init__(self, db: GrantServiceDatabase):
        self.db = db

    def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False):
        """
        Выполнить SQL запрос

        Args:
            query: SQL запрос
            params: Параметры запроса
            fetch_one: Если True, вернет один результат, иначе список

        Returns:
            Результат запроса (dict или list of dicts)
        """
        with self.db.connect() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            query_upper = query.strip().upper()

            # Если это запрос который возвращает данные
            if query_upper.startswith('SELECT') or 'RETURNING' in query_upper:
                if fetch_one:
                    result = cursor.fetchone()
                    conn.commit()  # На всякий случай коммитим
                    cursor.close()
                    return dict(result) if result else None
                else:
                    results = cursor.fetchall()
                    conn.commit()  # На всякий случай коммитим
                    cursor.close()
                    return [dict(row) for row in results] if results else []
            else:
                # INSERT/UPDATE/DELETE без RETURNING
                conn.commit()
                cursor.close()
                return None

    def get_session_by_anketa_id(self, anketa_id: str) -> Optional[Dict]:
        """Получить сессию по anketa_id"""
        result = self.execute_query(
            "SELECT * FROM sessions WHERE anketa_id = %s LIMIT 1",
            (anketa_id,),
            fetch_one=True
        )
        return result

    def get_session_by_id(self, session_id: int) -> Optional[Dict]:
        """Получить сессию по id"""
        result = self.execute_query(
            "SELECT * FROM sessions WHERE id = %s LIMIT 1",
            (session_id,),
            fetch_one=True
        )
        return result

    def get_user_answers(self, session_id: int) -> List[Dict]:
        """Получить ответы пользователя"""
        return self.execute_query(
            "SELECT * FROM user_answers WHERE session_id = %s ORDER BY answered_at",
            (session_id,)
        )

    def save_research_results(self, research_data: Dict) -> str:
        """
        Сохранить результаты исследования в researcher_research

        Args:
            research_data: Данные исследования с полями:
                - research_id
                - anketa_id
                - status
                - research_results (JSONB)
                - etc.

        Returns:
            research_id
        """
        import json

        # Конвертируем dict в JSON строку для JSONB поля
        research_results = research_data.get('research_results', {})
        if isinstance(research_results, dict):
            research_results = json.dumps(research_results, ensure_ascii=False)

        result = self.execute_query("""
            INSERT INTO researcher_research (
                research_id,
                anketa_id,
                session_id,
                status,
                research_results,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s::jsonb, NOW(), NOW())
            RETURNING research_id
        """, (
            research_data.get('research_id'),
            research_data.get('anketa_id'),
            research_data.get('session_id'),
            research_data.get('status', 'pending'),
            research_results
        ), fetch_one=True)

        return result['research_id'] if result else None

    def connect(self):
        """Прокси метод для совместимости"""
        return self.db.connect()
