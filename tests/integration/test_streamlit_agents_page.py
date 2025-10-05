#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интеграционные тесты для страницы Агенты (🤖_Агенты.py)
Проверяют что данные корректно загружаются и отображаются
"""

import pytest
import sys
from pathlib import Path

tests_dir = Path(__file__).parent.parent
project_root = tests_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'web-admin'))

# Import from web-admin/utils
from utils.postgres_helper import execute_query


@pytest.mark.integration
class TestAgentsPageDataLoading:
    """
    Тесты загрузки данных для страницы Агенты

    Эти тесты предотвращают регрессию ошибки:
    AttributeError: 'tuple' object has no attribute 'get'
    """

    def test_get_agent_statistics_interviewer(self):
        """
        Тест функции get_agent_statistics для интервьюера

        Эта функция вызывала ошибку до исправления postgres_helper
        """
        # Симулируем вызов из get_agent_statistics('interviewer')
        result = execute_query("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed,
                ROUND(AVG(progress_percentage), 1) as avg_progress,
                ROUND(AVG(session_duration_minutes), 1) as avg_duration_min
            FROM sessions
            WHERE started_at >= NOW() - INTERVAL '30 days'
        """)

        # Проверка что результат не пустой
        assert len(result) > 0, "Должна быть хотя бы одна строка результата"

        stats = result[0]

        # КРИТИЧНО: проверяем что можем использовать .get() как в реальном коде
        # Этот код падал с: AttributeError: 'tuple' object has no attribute 'get'
        total = stats.get('total', 0)
        completed = stats.get('completed', 0)
        avg_progress = stats.get('avg_progress', 0)
        avg_duration = stats.get('avg_duration_min', 0)

        # Проверка типов
        assert isinstance(total, int), f"total должен быть int, получен {type(total)}"
        assert isinstance(completed, int), f"completed должен быть int, получен {type(completed)}"

        # Проверка логики
        assert total >= 0, "total не может быть отрицательным"
        assert completed >= 0, "completed не может быть отрицательным"
        assert completed <= total, "completed не может быть больше total"

    def test_agent_stats_use_dict_access_pattern(self):
        """
        Проверка паттернов доступа к данным из страницы Агенты

        Код на странице использует:
        - stats.get('total', 0)
        - st.metric("Всего интервью", stats.get('total', 0))

        Этот паттерн должен работать без ошибок
        """
        queries = [
            # Interviewer
            """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed
            FROM sessions
            WHERE started_at >= NOW() - INTERVAL '30 days'
            """,

            # Auditor
            """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved
            FROM auditor_results
            WHERE created_at >= NOW() - INTERVAL '30 days'
            """,

            # Writer
            """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
            FROM grants
            WHERE created_at >= NOW() - INTERVAL '30 days'
            """
        ]

        for query in queries:
            result = execute_query(query)

            assert isinstance(result, list), "execute_query должен возвращать список"

            if len(result) > 0:
                stats = result[0]

                # Проверяем что это dict-like объект
                assert hasattr(stats, 'get'), \
                    f"Результат должен иметь метод .get(), получен тип {type(stats)}"

                # Проверяем что .get() работает с default значением
                total = stats.get('total', 0)
                assert total >= 0, "total должен быть >= 0"

    def test_postgres_interval_syntax(self):
        """
        Проверка что PostgreSQL синтаксис NOW() - INTERVAL работает

        Раньше использовался SQLite синтаксис: datetime('now', '-30 days')
        Теперь PostgreSQL: NOW() - INTERVAL '30 days'
        """
        # Проверяем что запрос с INTERVAL не падает
        result = execute_query("""
            SELECT
                COUNT(*) as total
            FROM sessions
            WHERE started_at >= NOW() - INTERVAL '30 days'
        """)

        assert len(result) > 0, "Запрос с INTERVAL должен работать"

        stats = result[0]
        total = stats.get('total', 0)
        assert isinstance(total, int), "Должен вернуть число"

    def test_boolean_comparison_in_queries(self):
        """
        Проверка что PostgreSQL boolean сравнения работают

        Раньше: data_mapping_complete = 1 (SQLite)
        Теперь: data_mapping_complete = TRUE (PostgreSQL)
        """
        result = execute_query("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN data_mapping_complete = TRUE THEN 1 END) as complete_mappings
            FROM planner_structures
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)

        assert isinstance(result, list), "Запрос с boolean должен работать"

        if len(result) > 0:
            stats = result[0]
            total = stats.get('total', 0)
            complete = stats.get('complete_mappings', 0)

            assert isinstance(total, int)
            assert isinstance(complete, int)
            assert complete <= total, "complete не может быть больше total"


@pytest.mark.integration
class TestAgentsPageRegressionTests:
    """
    Регрессионные тесты - предотвращают возврат старых ошибок
    """

    def test_no_sqlite_datetime_syntax(self):
        """
        Проверка что не используется SQLite синтаксис datetime()

        Это вызывало ошибку в PostgreSQL:
        function datetime(unknown, unknown) does not exist
        """
        # Если бы мы попытались использовать SQLite синтаксис, запрос упал бы
        with pytest.raises(Exception) as exc_info:
            execute_query("""
                SELECT COUNT(*) as total
                FROM sessions
                WHERE started_at >= datetime('now', '-30 days')
            """)

        # Проверяем что ошибка связана с функцией datetime
        error_msg = str(exc_info.value).lower()
        assert 'datetime' in error_msg or 'function' in error_msg, \
            "Должна быть ошибка о несуществующей функции datetime"

    def test_streamlit_metric_pattern_works(self):
        """
        Проверка паттерна st.metric() из Streamlit

        Код: st.metric("Всего интервью", stats.get('total', 0))
        Не должен падать с AttributeError
        """
        result = execute_query("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed
            FROM sessions
            WHERE started_at >= NOW() - INTERVAL '7 days'
        """)

        stats = result[0] if result else {}

        # Симулируем код из Streamlit страницы
        total = stats.get('total', 0)
        completed = stats.get('completed', 0)
        avg_progress = stats.get('avg_progress', 0)

        # Проверяем что значения могут быть использованы в st.metric
        assert isinstance(total, (int, type(None))), \
            f"total должен быть int для st.metric, получен {type(total)}"
        assert isinstance(completed, (int, type(None))), \
            f"completed должен быть int для st.metric, получен {type(completed)}"

    def test_all_agent_types_queries_work(self):
        """
        Проверка что запросы для всех типов агентов работают

        Типы агентов: interviewer, auditor, planner, writer, researcher
        """
        agent_queries = {
            'interviewer': "SELECT COUNT(*) as total FROM sessions",
            'auditor': "SELECT COUNT(*) as total FROM auditor_results",
            'planner': "SELECT COUNT(*) as total FROM planner_structures",
            'writer': "SELECT COUNT(*) as total FROM grants",
            'researcher': "SELECT COUNT(*) as total FROM researcher_research"
        }

        for agent_type, query in agent_queries.items():
            result = execute_query(query)

            assert isinstance(result, list), \
                f"Запрос для {agent_type} должен возвращать список"

            if len(result) > 0:
                stats = result[0]
                assert hasattr(stats, 'get'), \
                    f"Результат для {agent_type} должен иметь метод .get()"

                total = stats.get('total', 0)
                assert isinstance(total, int), \
                    f"total для {agent_type} должен быть int, получен {type(total)}"
