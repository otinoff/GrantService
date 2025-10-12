#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Queue Calculator
======================
Calculates queue sizes for each agent based on database state

Author: Grant Service Architect Agent
Created: 2025-10-09
"""

from typing import Dict
import logging
from .postgres_helper import execute_query

logger = logging.getLogger(__name__)


def get_interviewer_queue_size() -> int:
    """
    Получить размер очереди для Interviewer

    Interviewer обрабатывает:
    - Сессии со статусом 'in_progress' и current_stage = 'interviewer'
    - Сессии со статусом 'completed' и completion_status = 'completed' (новый workflow)

    Returns:
        Количество сессий в очереди
    """
    try:
        result = execute_query("""
            SELECT COUNT(*) as count
            FROM sessions
            WHERE (
                (status = 'in_progress' AND current_stage = 'interviewer')
                OR (status != 'archived' AND completion_status = 'completed' AND current_stage = 'interviewer')
            )
            AND anketa_id IS NOT NULL
        """)
        return result[0]['count'] if result else 0
    except Exception as e:
        logger.error(f"Error calculating interviewer queue: {e}")
        return 0


def get_auditor_queue_size() -> int:
    """
    Получить размер очереди для Auditor

    Auditor обрабатывает:
    - Сессии с completed interview (current_stage прошел interviewer)
    - У которых НЕТ записи в auditor_results

    Returns:
        Количество сессий в очереди
    """
    try:
        result = execute_query("""
            SELECT COUNT(*) as count
            FROM sessions s
            WHERE s.anketa_id IS NOT NULL
              AND s.status != 'archived'
              AND s.current_stage != 'interviewer'
              AND NOT EXISTS (
                  SELECT 1 FROM auditor_results ar
                  WHERE ar.session_id = s.id
              )
        """)
        return result[0]['count'] if result else 0
    except Exception as e:
        logger.error(f"Error calculating auditor queue: {e}")
        return 0


def get_researcher_queue_size() -> int:
    """
    Получить размер очереди для Researcher

    Researcher обрабатывает:
    - Сессии с completed audit (есть auditor_results)
    - У которых НЕТ completed research в researcher_research

    Returns:
        Количество сессий в очереди
    """
    try:
        result = execute_query("""
            SELECT COUNT(*) as count
            FROM sessions s
            WHERE s.anketa_id IS NOT NULL
              AND s.status != 'archived'
              AND EXISTS (
                  SELECT 1 FROM auditor_results ar
                  WHERE ar.session_id = s.id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM researcher_research rr
                  WHERE rr.session_id = s.id
                    AND rr.status = 'completed'
              )
        """)
        return result[0]['count'] if result else 0
    except Exception as e:
        logger.error(f"Error calculating researcher queue: {e}")
        return 0


def get_writer_queue_size() -> int:
    """
    Получить размер очереди для Writer

    Writer обрабатывает:
    - Сессии с completed research (есть researcher_research со status='completed')
    - У которых НЕТ grant

    Returns:
        Количество сессий в очереди
    """
    try:
        result = execute_query("""
            SELECT COUNT(*) as count
            FROM sessions s
            WHERE s.anketa_id IS NOT NULL
              AND s.status != 'archived'
              AND EXISTS (
                  SELECT 1 FROM researcher_research rr
                  WHERE rr.session_id = s.id
                    AND rr.status = 'completed'
              )
              AND NOT EXISTS (
                  SELECT 1 FROM grants g
                  WHERE g.anketa_id = s.anketa_id
              )
        """)
        return result[0]['count'] if result else 0
    except Exception as e:
        logger.error(f"Error calculating writer queue: {e}")
        return 0


def get_reviewer_queue_size() -> int:
    """
    Получить размер очереди для Reviewer

    Reviewer обрабатывает:
    - Grants которые созданы (есть в таблице grants)
    - У которых НЕТ review (review_score IS NULL)

    Returns:
        Количество грантов в очереди
    """
    try:
        result = execute_query("""
            SELECT COUNT(*) as count
            FROM grants
            WHERE review_score IS NULL
              AND status != 'archived'
        """)
        return result[0]['count'] if result else 0
    except Exception as e:
        logger.error(f"Error calculating reviewer queue: {e}")
        return 0


def get_all_queue_sizes() -> Dict[str, int]:
    """
    Получить размеры очередей для всех агентов

    Returns:
        Dict с ключами: interviewer, auditor, researcher, writer, reviewer
        и значениями - количество элементов в очереди

    Example:
        >>> queues = get_all_queue_sizes()
        >>> print(f"Writer queue: {queues['writer']}")
    """
    return {
        'interviewer': get_interviewer_queue_size(),
        'auditor': get_auditor_queue_size(),
        'researcher': get_researcher_queue_size(),
        'writer': get_writer_queue_size(),
        'reviewer': get_reviewer_queue_size(),
    }


__all__ = [
    'get_interviewer_queue_size',
    'get_auditor_queue_size',
    'get_researcher_queue_size',
    'get_writer_queue_size',
    'get_reviewer_queue_size',
    'get_all_queue_sizes',
]
