#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agent Router
===============
Маршрутизация между GigaChat и Claude Code на основе настроек из ai_agent_settings

Author: Grant Service Architect Agent
Created: 2025-10-06
"""

import sys
import logging
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.database import GrantServiceDatabase

logger = logging.getLogger(__name__)


def get_interviewer_handler(db: GrantServiceDatabase):
    """
    Получить обработчик интервью в зависимости от настроек

    Проверяет таблицу ai_agent_settings и возвращает:
    - InteractiveInterviewerAgent если mode = 'interactive' (по умолчанию, рекомендуется)
    - InterviewerAgent если mode = 'structured' (hardcoded вопросы без AI анализа)

    Args:
        db: Database instance

    Returns:
        InterviewerAgent: Interactive или Structured агент

    Example:
        >>> from data.database import GrantServiceDatabase
        >>> db = GrantServiceDatabase()
        >>> interviewer = get_interviewer_handler(db)
        >>> print(type(interviewer).__name__)
        'InteractiveInterviewerAgent'
    """
    try:
        # Query settings from database
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT mode FROM ai_agent_settings WHERE agent_name = 'interviewer'"
            )
            result = cursor.fetchone()
            cursor.close()

        mode = result[0] if result else 'interactive'

        logger.info(f"🎤 Interviewer mode from database: {mode}")

        # Route to appropriate handler
        if mode == 'structured':
            # Hardcoded interviewer без AI анализа
            from agents.interviewer_agent import InterviewerAgent
            logger.info("Loading InterviewerAgent (structured mode - hardcoded)")
            return InterviewerAgent(db)
        else:  # interactive (default)
            # Interactive interviewer с промежуточными аудитами
            try:
                from agents.interactive_interviewer_agent import InteractiveInterviewerAgent
                logger.info("✅ Loading InteractiveInterviewerAgent (AI-powered with interim audits)")
                return InteractiveInterviewerAgent(db, llm_provider="claude_code")
            except ImportError as e:
                logger.error(f"Cannot import InteractiveInterviewerAgent: {e}")
                logger.warning("Falling back to structured InterviewerAgent")
                from agents.interviewer_agent import InterviewerAgent
                return InterviewerAgent(db)

    except Exception as e:
        logger.error(f"Error getting interviewer handler: {e}")
        logger.warning("Falling back to default InteractiveInterviewerAgent")
        try:
            from agents.interactive_interviewer_agent import InteractiveInterviewerAgent
            return InteractiveInterviewerAgent(db, llm_provider="claude_code")
        except ImportError:
            from agents.interviewer_agent import InterviewerAgent
            return InterviewerAgent(db)


def get_agent_llm_client(agent_name: str, db: GrantServiceDatabase) -> Any:
    """
    Получить LLM клиента для агента (GigaChat или Claude Code)

    Проверяет таблицу ai_agent_settings и возвращает соответствующий клиент

    Args:
        agent_name: Имя агента (writer, auditor, planner, researcher)
        db: Database instance

    Returns:
        LLM client instance (GigaChatClient или ClaudeCodeClient)

    Example:
        >>> from data.database import GrantServiceDatabase
        >>> db = GrantServiceDatabase()
        >>> client = get_agent_llm_client('writer', db)
        >>> response = client.generate("Write something")
    """
    try:
        # Query settings from database
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT provider, config FROM ai_agent_settings WHERE agent_name = %s",
                (agent_name,)
            )
            result = cursor.fetchone()
            cursor.close()

        if result:
            provider = result[0]
            config = result[1] if result[1] else {}
        else:
            # Default to GigaChat
            provider = 'gigachat'
            config = {}

        logger.info(f"Agent '{agent_name}' using provider: {provider}")

        # Route to appropriate LLM client
        if provider == 'claude_code':
            try:
                from shared.llm.claude_code_client import ClaudeCodeClient
                logger.info(f"Loading ClaudeCodeClient for agent '{agent_name}'")
                return ClaudeCodeClient()
            except ImportError as e:
                logger.error(f"Cannot import ClaudeCodeClient: {e}")
                logger.warning(f"Falling back to GigaChatService for agent '{agent_name}'")
                from services.gigachat_service import GigaChatService
                return GigaChatService()
        else:
            # GigaChat (default)
            try:
                from services.gigachat_service import GigaChatService
                logger.info(f"Loading GigaChatService for agent '{agent_name}'")
                return GigaChatService()
            except ImportError as e:
                logger.error(f"Cannot import GigaChatService: {e}")
                raise ImportError(f"No LLM client available for agent '{agent_name}'")

    except Exception as e:
        logger.error(f"Error getting LLM client for agent '{agent_name}': {e}")
        logger.warning(f"Falling back to default GigaChatService")
        try:
            from services.gigachat_service import GigaChatService
            return GigaChatService()
        except ImportError:
            raise ImportError(f"Cannot initialize fallback LLM client for agent '{agent_name}'")


__all__ = [
    'get_interviewer_handler',
    'get_agent_llm_client',
]
