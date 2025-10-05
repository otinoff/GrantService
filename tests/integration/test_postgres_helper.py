#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интеграционные тесты для postgres_helper - проверка типов данных
Эти тесты ловят ошибки типа: AttributeError: 'tuple' object has no attribute 'get'
"""

import pytest
import sys
from pathlib import Path

tests_dir = Path(__file__).parent.parent
project_root = tests_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'web-admin'))

# Import from web-admin/utils
from utils.postgres_helper import (
    execute_query,
    execute_query_df,
    execute_scalar,
    execute_update
)


@pytest.mark.integration
class TestPostgresHelperReturnTypes:
    """Тесты типов возвращаемых данных из postgres_helper"""

    def test_execute_query_returns_list_of_dicts(self):
        """
        КРИТИЧНО: execute_query должен возвращать список словарей, НЕ кортежей

        Эта ошибка вызвала: AttributeError: 'tuple' object has no attribute 'get'
        в коде типа: stats.get('total', 0)
        """
        result = execute_query("SELECT 1 as test_value, 'hello' as test_text")

        # Проверяем что результат - список
        assert isinstance(result, list), "execute_query должен возвращать список"
        assert len(result) > 0, "Результат не должен быть пустым"

        # КРИТИЧНО: каждый элемент должен быть dict, НЕ tuple
        first_row = result[0]
        assert not isinstance(first_row, tuple), \
            "execute_query НЕ должен возвращать tuple! Должен быть dict (RealDict)"

        # Проверяем что это dict-like объект с методом get()
        assert hasattr(first_row, 'get'), \
            "Результат должен иметь метод .get() (быть dict-like объектом)"

        # Проверяем доступ по ключу
        assert first_row['test_value'] == 1
        assert first_row['test_text'] == 'hello'

        # Проверяем метод .get() (этот метод использовался в коде и падал)
        assert first_row.get('test_value') == 1
        assert first_row.get('nonexistent', 'default') == 'default'

    def test_execute_query_with_real_database(self):
        """Проверка на реальных данных из БД"""
        result = execute_query("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN role = 'admin' THEN 1 END) as admins
            FROM users
        """)

        assert len(result) == 1, "Должна быть одна строка результата"

        row = result[0]

        # Проверяем что это dict-like объект
        assert hasattr(row, 'get'), "Результат должен иметь метод .get()"

        # Проверяем доступ через .get() (этот код падал раньше)
        total = row.get('total', 0)
        admins = row.get('admins', 0)

        assert isinstance(total, int), "total должен быть числом"
        assert isinstance(admins, int), "admins должен быть числом"
        assert total >= 4, "Должно быть минимум 4 пользователя после миграции"

    def test_execute_query_df_returns_dataframe(self):
        """Проверка что execute_query_df возвращает DataFrame"""
        import pandas as pd

        df = execute_query_df("SELECT * FROM users LIMIT 5")

        assert isinstance(df, pd.DataFrame), "Должен возвращать pandas DataFrame"
        assert len(df) > 0, "DataFrame не должен быть пустым"
        assert 'telegram_id' in df.columns, "Должна быть колонка telegram_id"

    def test_execute_scalar_returns_single_value(self):
        """Проверка что execute_scalar возвращает одно значение"""
        count = execute_scalar("SELECT COUNT(*) FROM users")

        assert isinstance(count, int), "execute_scalar должен возвращать одно значение"
        assert count >= 4, "Должно быть минимум 4 пользователя"

    def test_execute_query_empty_result(self):
        """Проверка что пустой результат тоже возвращает список dict"""
        result = execute_query("SELECT * FROM users WHERE telegram_id = -999999")

        assert isinstance(result, list), "Должен возвращать список даже если пусто"
        assert len(result) == 0, "Результат должен быть пустым списком"


@pytest.mark.integration
class TestAgentsPageQueries:
    """
    Тесты SQL-запросов из страницы Агенты
    Эти запросы вызывали ошибку: AttributeError: 'tuple' object has no attribute 'get'
    """

    def test_interviewer_stats_query(self):
        """Тест запроса статистики интервьюера (был источником ошибки)"""
        result = execute_query("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed,
                ROUND(AVG(progress_percentage), 1) as avg_progress,
                ROUND(AVG(session_duration_minutes), 1) as avg_duration_min
            FROM sessions
            WHERE started_at >= NOW() - INTERVAL '30 days'
        """)

        assert len(result) > 0, "Результат не должен быть пустым"

        stats = result[0]

        # КРИТИЧНО: проверяем что можем вызвать .get() без ошибки
        total = stats.get('total', 0)
        completed = stats.get('completed', 0)
        avg_progress = stats.get('avg_progress', 0)

        assert isinstance(total, int), "total должен быть числом"
        assert isinstance(completed, int), "completed должен быть числом"

    def test_auditor_stats_query(self):
        """Тест запроса статистики аудитора"""
        result = execute_query("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved,
                COUNT(CASE WHEN approval_status = 'needs_revision' THEN 1 END) as needs_revision,
                ROUND(AVG(average_score), 2) as avg_score
            FROM auditor_results
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)

        assert isinstance(result, list), "Должен возвращать список"

        if len(result) > 0:
            stats = result[0]
            # Проверяем что .get() работает
            total = stats.get('total', 0)
            assert isinstance(total, int)

    def test_planner_stats_query(self):
        """Тест запроса статистики планера (включая boolean сравнение)"""
        result = execute_query("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN data_mapping_complete = TRUE THEN 1 END) as complete_mappings,
                ROUND(AVG(sections_count), 1) as avg_sections
            FROM planner_structures
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)

        assert isinstance(result, list), "Должен возвращать список"

        if len(result) > 0:
            stats = result[0]
            # Проверяем что .get() работает
            total = stats.get('total', 0)
            assert isinstance(total, int)

    def test_writer_stats_query(self):
        """Тест запроса статистики писателя"""
        result = execute_query("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft,
                ROUND(AVG(quality_score), 2) as avg_quality_score
            FROM grants
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)

        assert isinstance(result, list), "Должен возвращать список"

        if len(result) > 0:
            stats = result[0]
            # Проверяем что .get() работает
            total = stats.get('total', 0)
            completed = stats.get('completed', 0)
            assert isinstance(total, int)


@pytest.mark.integration
class TestSQLiteTupleVsPostgreSQLDict:
    """
    Регрессионный тест: ловим ошибку миграции SQLite → PostgreSQL

    В SQLite cursor.fetchall() мог возвращать tuple,
    В PostgreSQL с обычным cursor тоже возвращает tuple,
    НО с RealDictCursor возвращает RealDictRow (dict-like)
    """

    def test_no_tuple_in_results(self):
        """Проверка что результаты НЕ содержат tuple"""
        result = execute_query("SELECT telegram_id, username FROM users LIMIT 1")

        assert len(result) > 0, "Должен быть минимум один пользователь"

        row = result[0]

        # КРИТИЧНО: НЕ должно быть tuple
        assert not isinstance(row, tuple), \
            f"ОШИБКА: execute_query возвращает tuple вместо dict! Тип: {type(row)}"

        # Должен быть dict-like объект
        assert hasattr(row, 'keys'), "Должны быть доступны ключи (.keys())"
        assert hasattr(row, 'get'), "Должен быть метод .get()"
        assert hasattr(row, '__getitem__'), "Должен поддерживать row['key']"

    def test_can_use_get_method_on_results(self):
        """
        Регрессионный тест: проверка что код stats.get('total', 0) работает

        Этот код падал с ошибкой: AttributeError: 'tuple' object has no attribute 'get'
        """
        result = execute_query("SELECT COUNT(*) as total FROM users")

        stats = result[0]

        # Этот вызов падал до исправления
        try:
            total = stats.get('total', 0)
            assert total >= 4, "Должно быть минимум 4 пользователя"
        except AttributeError as e:
            pytest.fail(f"РЕГРЕССИЯ: stats.get() вызвал ошибку: {e}")

    def test_can_iterate_over_dict_keys(self):
        """Проверка что можем итерировать по ключам как в dict"""
        result = execute_query("SELECT telegram_id, username, role FROM users LIMIT 1")

        row = result[0]

        # Проверяем что можем получить ключи
        keys = list(row.keys())
        assert 'telegram_id' in keys
        assert 'username' in keys
        assert 'role' in keys
