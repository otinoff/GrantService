#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL Helper for Streamlit Pages
======================================
Universal helper to replace SQLite get_db_connection() with PostgreSQL

Author: Database Manager Agent
Created: 2025-10-04
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# Import PostgreSQL database
import sys
from pathlib import Path

# Add project root to path
web_admin_dir = Path(__file__).parent.parent
if str(web_admin_dir.parent) not in sys.path:
    sys.path.insert(0, str(web_admin_dir.parent))

from data.database import GrantServiceDatabase


@st.cache_resource
def get_postgres_db():
    """
    Get cached PostgreSQL database instance

    Returns:
        GrantServiceDatabase: PostgreSQL database instance
    """
    return GrantServiceDatabase()


@contextmanager
def get_postgres_connection():
    """
    Context manager for PostgreSQL connection

    Usage:
        with get_postgres_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT...")
            results = cursor.fetchall()
            cursor.close()

    Yields:
        psycopg2.connection: PostgreSQL connection
    """
    db = get_postgres_db()
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: Optional[tuple] = None) -> List[tuple]:
    """
    Execute SELECT query and return results

    Args:
        query: SQL SELECT query (use %s for parameters)
        params: Query parameters tuple

    Returns:
        List of tuples with results

    Example:
        results = execute_query("SELECT * FROM users WHERE id = %s", (user_id,))
    """
    db = get_postgres_db()

    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()

    return results


def execute_query_df(query: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """
    Execute SELECT query and return DataFrame

    Args:
        query: SQL SELECT query (use %s for parameters)
        params: Query parameters tuple

    Returns:
        pandas.DataFrame with results

    Example:
        df = execute_query_df("SELECT * FROM grant_applications LIMIT 10")
    """
    db = get_postgres_db()

    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)

        # Fetch all rows
        rows = cursor.fetchall()

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        cursor.close()

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=columns)
    return df


def execute_scalar(query: str, params: Optional[tuple] = None) -> Any:
    """
    Execute query and return single value (first column of first row)

    Args:
        query: SQL query (typically SELECT COUNT(*) or similar)
        params: Query parameters tuple

    Returns:
        Single value (int, str, etc.)

    Example:
        count = execute_scalar("SELECT COUNT(*) FROM users")
    """
    db = get_postgres_db()

    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()[0]
        cursor.close()

    return result


def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """
    Execute INSERT/UPDATE/DELETE query

    Args:
        query: SQL query (INSERT, UPDATE, DELETE)
        params: Query parameters tuple

    Returns:
        Number of affected rows

    Example:
        rows_updated = execute_update(
            "UPDATE grant_applications SET status = %s WHERE id = %s",
            ('completed', app_id)
        )
    """
    db = get_postgres_db()

    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        rowcount = cursor.rowcount
        cursor.close()

    return rowcount


# Backward compatibility aliases
get_db_connection_postgres = get_postgres_connection
get_postgres_cursor = get_postgres_connection


__all__ = [
    'get_postgres_db',
    'get_postgres_connection',
    'execute_query',
    'execute_query_df',
    'execute_scalar',
    'execute_update',
]
